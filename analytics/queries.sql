-- analytics/queries.sql — the 5 required analytics queries (SPEC §6.1).
--
-- Convention: each query starts with a `-- name: <query_name>` marker and
-- uses psycopg named placeholders (%(param)s). `analytics/loader.py` parses
-- this file, and `api/routes/analytics.py` reuses the same queries — never
-- fork divergent copies into Python strings (CLAUDE.md).
--
-- All queries exclude nothing by default: pass %(include_synthetic)s = false
-- to filter out synthetic dev data where the parameter appears.


-- name: rolling_sentiment
-- §6.1.1 Rolling sentiment average per entity: 24h and 7d moving averages
-- of sentiment, time-ordered, for one entity.
-- params: entity_id (int), since (timestamptz), include_synthetic (bool)
select
    n.published_at,
    s.sentiment,
    avg(s.sentiment) over (
        order by n.published_at
        range between interval '24 hours' preceding and current row
    ) as avg_24h,
    avg(s.sentiment) over (
        order by n.published_at
        range between interval '7 days' preceding and current row
    ) as avg_7d
from news_items n
join news_entities ne   on ne.news_item_id = n.id
join sentiment_scores s on s.news_item_id = n.id
where ne.entity_id = %(entity_id)s
  and n.published_at >= %(since)s
  and (%(include_synthetic)s or n.source <> 'synthetic')
order by n.published_at;


-- name: volume_spikes
-- §6.1.2 News volume spike detection: for each entity, compare the count in
-- the trailing 6h against that entity's average 6h-bucket count over the
-- trailing 7 days. Spike if current > %(spike_factor)s x baseline.
-- params: as_of (timestamptz), spike_factor (float), include_synthetic (bool)
with buckets as (
    select
        ne.entity_id,
        -- bucket index 0..27: 6h windows counting back from as_of
        floor(extract(epoch from (%(as_of)s::timestamptz - n.published_at))
              / (6 * 3600))::int as bucket
    from news_items n
    join news_entities ne on ne.news_item_id = n.id
    where n.published_at >  %(as_of)s::timestamptz - interval '7 days'
      and n.published_at <= %(as_of)s::timestamptz
      and (%(include_synthetic)s or n.source <> 'synthetic')
),
per_bucket as (
    select entity_id, bucket, count(*) as cnt
    from buckets
    group by entity_id, bucket
),
stats as (
    select
        entity_id,
        coalesce(sum(cnt) filter (where bucket = 0), 0)      as current_6h,
        -- average over the 27 fully-elapsed baseline buckets; entities with
        -- no news in a bucket contribute 0 via the fixed divisor
        coalesce(sum(cnt) filter (where bucket > 0), 0) / 27.0 as baseline_6h
    from per_bucket
    group by entity_id
)
select
    e.id as entity_id,
    e.name,
    st.current_6h,
    round(st.baseline_6h, 2) as baseline_6h,
    round(st.current_6h / nullif(st.baseline_6h, 0), 2) as ratio,
    (st.current_6h > %(spike_factor)s * st.baseline_6h
     and st.current_6h >= 3) as is_spike
from stats st
join entities e on e.id = st.entity_id
order by ratio desc nulls last;


-- name: negative_momentum
-- §6.1.3 Entities where sentiment is negative AND trending more negative
-- over the last %(window_hours)s hours (second half vs first half).
-- params: as_of (timestamptz), window_hours (int), include_synthetic (bool)
with windowed as (
    select
        ne.entity_id,
        s.sentiment,
        n.published_at >= %(as_of)s::timestamptz
            - make_interval(hours => %(window_hours)s / 2) as second_half
    from news_items n
    join news_entities ne   on ne.news_item_id = n.id
    join sentiment_scores s on s.news_item_id = n.id
    where n.published_at >  %(as_of)s::timestamptz
                            - make_interval(hours => %(window_hours)s)
      and n.published_at <= %(as_of)s::timestamptz
      and (%(include_synthetic)s or n.source <> 'synthetic')
),
halves as (
    select
        entity_id,
        avg(sentiment)                             as avg_full,
        avg(sentiment) filter (where not second_half) as avg_first_half,
        avg(sentiment) filter (where second_half)     as avg_second_half,
        count(*)                                   as n_items
    from windowed
    group by entity_id
    having count(*) filter (where second_half) > 0
       and count(*) filter (where not second_half) > 0
)
select
    e.id as entity_id,
    e.name,
    round(h.avg_full, 3)                          as avg_sentiment,
    round(h.avg_first_half, 3)                    as first_half,
    round(h.avg_second_half, 3)                   as second_half,
    round(h.avg_second_half - h.avg_first_half, 3) as momentum,
    h.n_items
from halves h
join entities e on e.id = h.entity_id
where h.avg_full < 0
  and h.avg_second_half < h.avg_first_half
order by momentum asc;


-- name: decision_follow_up
-- §6.1.4 Agent self-evaluation: for each decision, the average sentiment of
-- same-entity news published in the %(horizon_hours)s after the decision,
-- and whether its sign agrees with the predicted impact direction.
-- params: horizon_hours (int), limit (int)
select
    d.id as decision_id,
    e.name as entity,
    d.impact_score,
    d.confidence,
    d.created_at,
    round(avg(s.sentiment), 3) as subsequent_sentiment,
    count(s.*)                 as follow_up_items,
    sign(avg(s.sentiment)) = sign(d.impact_score) as direction_match
from agent_decisions d
join entities e on e.id = d.entity_id
left join news_entities ne on ne.entity_id = d.entity_id
left join news_items n
       on n.id = ne.news_item_id
      and n.published_at >  d.created_at
      and n.published_at <= d.created_at
                            + make_interval(hours => %(horizon_hours)s)
left join sentiment_scores s on s.news_item_id = n.id
group by d.id, e.name, d.impact_score, d.confidence, d.created_at
order by d.created_at desc
limit %(limit)s;


-- name: win_rate
-- §6.1.5 Win-rate summary: accuracy percentage overall and per entity.
-- The overall row appears with entity = 'ALL' via grouping sets.
-- params: (none required)
select
    coalesce(e.name, 'ALL')                            as entity,
    count(*) filter (where ev.accuracy_flag is not null) as evaluated,
    count(*) filter (where ev.accuracy_flag)             as wins,
    round(100.0 * count(*) filter (where ev.accuracy_flag)
        / nullif(count(*) filter (where ev.accuracy_flag is not null), 0),
        1)                                             as win_rate_pct
from decision_evaluations ev
join agent_decisions d on d.id = ev.decision_id
join entities e        on e.id = d.entity_id
group by grouping sets ((e.name), ())
order by grouping(e.name) desc, win_rate_pct desc nulls last;
