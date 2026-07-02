# CLAUDE.md — News Impact Intelligence Agent

Project conventions and gotchas for Claude Code. The authoritative build
plan is [SPEC.md](SPEC.md) — read it before writing code, and work phase
by phase (don't start a phase before the previous one's acceptance
criteria pass).

## Hard constraints (from SPEC §1)

- **Never scrape or store full article bodies** — only headline, source,
  URL, publish timestamp, and RSS summary snippets ≤500 chars.
- **Not investment advice** — the disclaimer must stay in the README and
  appear on every dashboard page.

## Conventions

- DB access uses `psycopg` (v3) with `DATABASE_URL` from `.env`
  (python-dotenv). No ORM.
- Dedup anchor for news is the unique constraint on `news_items.url`;
  inserts use `on conflict (url) do nothing`.
- Sentiment is 1:1 with news items — re-scoring upserts on
  `sentiment_scores.news_item_id` (latest wins).
- Synthetic dev data is marked `source = 'synthetic'` so it can be
  filtered out (SPEC §9).
- SQL analytics queries live in `analytics/queries.sql`, parameterized,
  and are reused by `api/routes/analytics.py` — don't fork divergent
  copies of them into Python strings.

## Open decisions

- **Embedding model (SPEC §6.2):** not yet chosen. `kb_cases.embedding`
  is `vector(1536)` (OpenAI text-embedding-3-small assumption). If Voyage
  is chosen instead, ALTER the column dimension before running
  `kb/build_embeddings.py`, and update `requirements.txt` + `.env`.

## Environment gotchas

- Dev machine is Windows 11; local folder is `Market_Intelligence_Agent`
  but the GitHub repo is `News-Impact-Intelligence-Agent` — that's fine.
- RSS feed URLs rot. Reuters public RSS is dead; MarketWatch is the
  stand-in. Re-verify all `RSS_FEEDS` entries in `ingest/fetch_news.py`
  before trusting ingest results.
- `ingest/.fetch_state.json` (gitignored) enforces a 10-min cooldown
  between fetch passes; use `--force` during development.
