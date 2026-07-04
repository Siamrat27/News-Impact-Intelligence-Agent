"""Seed the DB with ~5,000 synthetic news rows for Phase 3-4 development.

All rows are marked source='synthetic' (news), model='synthetic' (sentiment)
or a '[synthetic]' reasoning prefix (decisions) so they can be filtered out
or purged once real data volume grows (SPEC §9).

The data is engineered so the analytics queries have patterns to find:
  - Bitcoin gets a news-volume burst in the trailing 6h  -> spike detection
  - Binance and Tesla sentiment drifts sharply negative
    over the last 48h                                    -> negative momentum

Usage:
    python ingest/generate_synthetic_news.py            # seed (idempotent-ish)
    python ingest/generate_synthetic_news.py --purge    # delete all synthetic rows
"""

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv

random.seed(42)

DAYS_OF_HISTORY = 30
BASE_ROW_TARGET = 4800
SPIKE_ROWS = 120          # extra BTC rows crammed into the trailing 6h
DECISION_ROWS = 150

# name, entity_type, ticker, volume weight, baseline sentiment mean
ENTITIES = [
    ("Bitcoin",       "crypto",      "BTC",  3.0,  0.10),
    ("Ethereum",      "crypto",      "ETH",  2.0,  0.05),
    ("Binance",       "company",     None,   1.5,  0.10),
    ("Coinbase",      "company",     "COIN", 1.0,  0.00),
    ("Federal Reserve", "institution", None, 1.5,  0.00),
    ("Tesla",         "company",     "TSLA", 1.5,  0.15),
    ("Apple",         "company",     "AAPL", 1.2,  0.20),
    ("S&P 500",       "index",       "SPX",  1.3,  0.05),
    ("US Dollar",     "currency",    "USD",  0.8,  0.00),
    ("Gold",          "commodity",   "XAU",  0.7,  0.10),
]

# entities whose sentiment collapses over the final 48h (negative momentum)
DRIFT_DOWN = {"Binance": -0.65, "Tesla": -0.55}

POSITIVE_TEMPLATES = [
    "{e} surges as institutional inflows hit record highs",
    "{e} rallies after stronger-than-expected results",
    "Analysts raise targets for {e} on robust demand",
    "{e} climbs amid renewed investor optimism",
    "{e} gains as adoption metrics beat forecasts",
]
NEUTRAL_TEMPLATES = [
    "{e} steady as markets await economic data",
    "What traders are watching in {e} this week",
    "{e} unchanged in quiet trading session",
    "Explainer: how recent policy shifts affect {e}",
    "{e} consolidates after last week's moves",
]
NEGATIVE_TEMPLATES = [
    "{e} slides amid regulatory scrutiny concerns",
    "{e} drops as investors flee risk assets",
    "Sell-off deepens in {e} after disappointing guidance",
    "{e} under pressure following security incident reports",
    "{e} tumbles as outflows accelerate",
]


def pick_headline(entity: str, sentiment: float) -> str:
    if sentiment > 0.15:
        pool = POSITIVE_TEMPLATES
    elif sentiment < -0.15:
        pool = NEGATIVE_TEMPLATES
    else:
        pool = NEUTRAL_TEMPLATES
    return random.choice(pool).format(e=entity)


def label_for(sentiment: float) -> str:
    if sentiment > 0.15:
        return "positive"
    if sentiment < -0.15:
        return "negative"
    return "neutral"


def clamp(x: float, lo: float = -0.999, hi: float = 0.999) -> float:
    return max(lo, min(hi, x))


def sample_sentiment(entity: str, base_mean: float, published_at: datetime,
                     now: datetime) -> float:
    """Baseline noise around the entity mean, plus a late collapse for
    the DRIFT_DOWN entities so negative-momentum queries have a signal."""
    mean = base_mean
    hours_ago = (now - published_at).total_seconds() / 3600
    if entity in DRIFT_DOWN and hours_ago <= 48:
        # linear slide toward the drift target as we approach `now`
        progress = 1 - hours_ago / 48
        mean = base_mean + (DRIFT_DOWN[entity] - base_mean) * progress
    return clamp(random.gauss(mean, 0.30))


def generate_rows(now: datetime) -> list[dict]:
    rows = []
    weights = [e[3] for e in ENTITIES]

    def make_row(entity_tuple, published_at):
        name, etype, ticker, _w, base_mean = entity_tuple
        sentiment = sample_sentiment(name, base_mean, published_at, now)
        headline = pick_headline(name, sentiment)
        return {
            "entity": name,
            "headline": headline,
            "url": f"synthetic://news/{uuid.uuid4().hex}",
            "published_at": published_at,
            "raw_summary": f"Synthetic development item about {name}. "
                           f"Generated for analytics testing; not real news.",
            "sentiment": round(sentiment, 3),
        }

    for _ in range(BASE_ROW_TARGET):
        entity_tuple = random.choices(ENTITIES, weights=weights, k=1)[0]
        published_at = now - timedelta(
            minutes=random.uniform(0, DAYS_OF_HISTORY * 24 * 60))
        rows.append(make_row(entity_tuple, published_at))

    btc = ENTITIES[0]
    for _ in range(SPIKE_ROWS):  # volume burst inside the trailing 6h
        published_at = now - timedelta(minutes=random.uniform(0, 6 * 60))
        rows.append(make_row(btc, published_at))

    return rows


def seed(conn: psycopg.Connection) -> None:
    now = datetime.now(timezone.utc)
    rows = generate_rows(now)

    with conn.cursor() as cur:
        # entities (idempotent)
        entity_ids: dict[str, int] = {}
        for name, etype, ticker, _w, _m in ENTITIES:
            cur.execute(
                """
                insert into entities (name, entity_type, ticker)
                values (%s, %s, %s)
                on conflict (name) do update set entity_type = excluded.entity_type
                returning id
                """,
                (name, etype, ticker),
            )
            entity_ids[name] = cur.fetchone()[0]

        # news_items via COPY (fast over the pooler)
        with cur.copy(
            "copy news_items (headline, source, url, published_at, raw_summary) "
            "from stdin"
        ) as copy:
            for r in rows:
                copy.write_row((r["headline"], "synthetic", r["url"],
                                r["published_at"], r["raw_summary"]))

        # map urls back to generated ids
        cur.execute(
            "select id, url from news_items where source = 'synthetic'")
        id_by_url = {url: nid for nid, url in cur.fetchall()}

        # links + sentiment via COPY
        with cur.copy(
            "copy news_entities (news_item_id, entity_id) from stdin"
        ) as copy:
            for r in rows:
                if r["url"] in id_by_url:
                    copy.write_row((id_by_url[r["url"]],
                                    entity_ids[r["entity"]]))

        with cur.copy(
            "copy sentiment_scores (news_item_id, sentiment, sentiment_label, model) "
            "from stdin"
        ) as copy:
            for r in rows:
                if r["url"] in id_by_url:
                    copy.write_row((id_by_url[r["url"]], r["sentiment"],
                                    label_for(r["sentiment"]), "synthetic"))

        # synthetic agent decisions on older items (>48h) so the backtest
        # queries (SPEC §6.1.4-6.1.5) have follow-up news to evaluate against
        candidates = [r for r in rows
                      if (now - r["published_at"]).total_seconds() > 48 * 3600
                      and r["url"] in id_by_url]
        for r in random.sample(candidates, min(DECISION_ROWS, len(candidates))):
            impact = clamp(r["sentiment"] * 0.8 + random.gauss(0, 0.25))
            cur.execute(
                """
                insert into agent_decisions
                    (news_item_id, entity_id, impact_score, confidence,
                     reasoning, created_at)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (id_by_url[r["url"]], entity_ids[r["entity"]],
                 round(impact, 3), round(random.uniform(0.55, 0.95), 3),
                 "[synthetic] placeholder decision generated for backtest "
                 "development; not produced by the agent graph.",
                 r["published_at"]),
            )

        # evaluate each synthetic decision against the avg sentiment of
        # same-entity news in the 24h after the decision (sign agreement)
        cur.execute(
            """
            insert into decision_evaluations
                (decision_id, subsequent_sentiment, accuracy_flag, notes)
            select d.id,
                   round(avg(s.sentiment), 3),
                   sign(avg(s.sentiment)) = sign(d.impact_score),
                   '[synthetic] auto-evaluated at seed time'
            from agent_decisions d
            join news_entities ne on ne.entity_id = d.entity_id
            join news_items n     on n.id = ne.news_item_id
                                 and n.published_at > d.created_at
                                 and n.published_at <= d.created_at + interval '24 hours'
            join sentiment_scores s on s.news_item_id = n.id
            where d.reasoning like '[synthetic]%'
            group by d.id, d.impact_score
            on conflict (decision_id) do nothing
            """
        )

    conn.commit()

    with conn.cursor() as cur:
        cur.execute("select count(*) from news_items where source='synthetic'")
        n_news = cur.fetchone()[0]
        cur.execute("select count(*) from agent_decisions where reasoning like '[synthetic]%'")
        n_dec = cur.fetchone()[0]
        cur.execute("select count(*) from decision_evaluations where notes like '[synthetic]%'")
        n_eval = cur.fetchone()[0]
    print(f"Seeded: {n_news} synthetic news rows, {n_dec} decisions, "
          f"{n_eval} evaluations.")


def purge(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        # cascades clean up news_entities, sentiment_scores, agent_decisions
        # (and their decision_evaluations) that hang off synthetic news items
        cur.execute("delete from news_items where source = 'synthetic'")
        deleted = cur.rowcount
    conn.commit()
    print(f"Purged {deleted} synthetic news rows (children cascaded).")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--purge", action="store_true",
                        help="delete all synthetic rows instead of seeding")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("DATABASE_URL is not set — copy .env.example to .env first.")

    with psycopg.connect(database_url) as conn:
        if args.purge:
            purge(conn)
        else:
            seed(conn)


if __name__ == "__main__":
    main()
