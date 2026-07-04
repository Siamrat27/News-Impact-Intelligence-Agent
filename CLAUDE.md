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
- The MSYS2 `python` on PATH produces a broken venv (installs to `.venv/bin`
  instead of `.venv/Scripts`, wrong site-packages). Use the official Windows
  Python instead: `C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe`.
- RSS feed URLs rot. Reuters public RSS is dead; MarketWatch is the
  stand-in. CoinDesk's feed 308-redirects if the URL has a trailing slash —
  use `https://www.coindesk.com/arc/outboundfeeds/rss` (no trailing `/`).
  Re-verify all `RSS_FEEDS` entries in `ingest/fetch_news.py` before
  trusting ingest results.
- `ingest/.fetch_state.json` (gitignored) enforces a 10-min cooldown
  between fetch passes; use `--force` during development.

## Database

- Supabase free tier caps at 2 projects per org, and both slots on this
  account are already used — this project's tables live in the existing
  `pocketflow` project (`vzuwdsigburzwyutzhtg`, ap-south-1), NOT a
  dedicated project. A `news_agent` Postgres role owns all 7 news-agent
  tables and has RLS enabled with no policies + revoked anon/authenticated
  grants, so it's isolated from pocketflow's own tables and inaccessible
  via the Supabase auto-generated REST API.
- The direct host (`db.<ref>.supabase.co:5432`) is IPv6-only and doesn't
  resolve from this network. `DATABASE_URL` must use the **session
  pooler** instead: `aws-1-ap-south-1.pooler.supabase.com:5432` with
  username `news_agent.<project-ref>` (note the project ref suffix on the
  username — required by the pooler, not needed on the direct host).
