-- News Impact Intelligence Agent — database schema
-- Target: Postgres (Supabase) with the pgvector extension.
-- Apply with: psql "$DATABASE_URL" -f db/schema.sql
-- or paste into the Supabase SQL editor.

create extension if not exists vector;

-- ---------------------------------------------------------------------------
-- Core news storage. Only headline/source/url/timestamp/summary snippet are
-- stored — full article bodies are never scraped (SPEC §1, copyright).
-- ---------------------------------------------------------------------------
create table if not exists news_items (
    id            bigint generated always as identity primary key,
    headline      text        not null,
    source        text        not null,           -- feed key, or 'synthetic'
    url           text        not null unique,    -- dedup anchor (SPEC §5)
    published_at  timestamptz not null,
    raw_summary   varchar(500),                   -- RSS snippet, <=500 chars
    fetched_at    timestamptz not null default now(),
    processed     boolean     not null default false  -- picked up by Monitor node yet?
);

create index if not exists idx_news_items_published_at
    on news_items (published_at desc);
create index if not exists idx_news_items_unprocessed
    on news_items (processed) where processed = false;

-- ---------------------------------------------------------------------------
-- Entities mentioned in the news (BTC, Fed, individual companies, ...).
-- ---------------------------------------------------------------------------
create table if not exists entities (
    id           bigint generated always as identity primary key,
    name         text not null unique,
    entity_type  text not null check (entity_type in
                     ('crypto', 'company', 'currency', 'commodity',
                      'index', 'institution', 'other')),
    ticker       text
);

create table if not exists news_entities (
    news_item_id bigint not null references news_items(id) on delete cascade,
    entity_id    bigint not null references entities(id)   on delete cascade,
    primary key (news_item_id, entity_id)
);

create index if not exists idx_news_entities_entity
    on news_entities (entity_id);

-- ---------------------------------------------------------------------------
-- Sentiment: 1:1 with news_items, latest score wins if re-scored (SPEC §4).
-- Upsert with: insert ... on conflict (news_item_id) do update set ...
-- ---------------------------------------------------------------------------
create table if not exists sentiment_scores (
    id              bigint generated always as identity primary key,
    news_item_id    bigint not null unique references news_items(id) on delete cascade,
    sentiment       numeric(4,3) not null check (sentiment between -1 and 1),
    sentiment_label text         not null check (sentiment_label in
                        ('negative', 'neutral', 'positive')),
    model           text         not null,   -- e.g. 'claude-sonnet-5'
    scored_at       timestamptz  not null default now()
);

-- ---------------------------------------------------------------------------
-- RAG knowledge base: hand-written historical cases (kb/cases.md).
-- NOTE (open decision, SPEC §4/§6.2): vector(1536) assumes OpenAI
-- text-embedding-3-small. If Voyage or another model is chosen in Phase 5-6,
-- ALTER this column's dimension before building embeddings.
-- ---------------------------------------------------------------------------
create table if not exists kb_cases (
    id            bigint generated always as identity primary key,
    title         text not null unique,
    description   text not null,          -- 2-4 sentences: what happened
    market_impact text not null,          -- what followed in the market
    entity_type   text not null,          -- tag: crypto / company / ...
    embedding     vector(1536)
);

-- ivfflat needs data before it helps; fine to create up front with few lists.
create index if not exists idx_kb_cases_embedding
    on kb_cases using ivfflat (embedding vector_cosine_ops) with (lists = 10);

-- ---------------------------------------------------------------------------
-- Agent output: one row per Impact-node assessment, with the RAG audit trail.
-- ---------------------------------------------------------------------------
create table if not exists agent_decisions (
    id                 bigint generated always as identity primary key,
    news_item_id       bigint not null references news_items(id) on delete cascade,
    entity_id          bigint not null references entities(id)   on delete cascade,
    impact_score       numeric(4,3) not null check (impact_score between -1 and 1),
    confidence         numeric(4,3) not null check (confidence between 0 and 1),
    reasoning          text         not null,
    retrieved_case_ids bigint[]     not null default '{}',  -- RAG trace (SPEC §4)
    created_at         timestamptz  not null default now()
);

create index if not exists idx_agent_decisions_entity
    on agent_decisions (entity_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Backtest results: did subsequent sentiment move the way the agent predicted?
-- Populated by the self-evaluation query (SPEC §6.1.4-6.1.5).
-- ---------------------------------------------------------------------------
create table if not exists decision_evaluations (
    id                   bigint generated always as identity primary key,
    decision_id          bigint not null unique references agent_decisions(id) on delete cascade,
    evaluated_at         timestamptz not null default now(),
    subsequent_sentiment numeric(4,3) check (subsequent_sentiment between -1 and 1),
    accuracy_flag        boolean,     -- null = not enough follow-up news yet
    notes                text
);
