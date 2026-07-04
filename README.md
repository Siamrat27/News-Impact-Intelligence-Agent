# News Impact Intelligence Agent

An autonomous multi-agent system that monitors financial/crypto news,
extracts sentiment and entities via NLP (Claude API), retrieves similar
historical cases via RAG (pgvector), and produces confidence-scored
market-impact assessments through a LangGraph agent graph. Every decision
is logged with its full RAG trace and is queryable via SQL for
backtesting.

> **⚠️ Disclaimer: educational demo — not investment advice.**
> This is a portfolio project. Nothing it produces should be used to make
> trading or investment decisions.

## Architecture

```text
RSS feeds ──► ingest/fetch_news.py ──► Postgres (Supabase + pgvector)
                                            │
              LangGraph agent graph ◄───────┤
              Monitor ► Sentiment ► Impact ► Log
              (Impact node calls rag_retrieve over kb_cases)
                                            │
              FastAPI ◄─────────────────────┘
                 │
              React dashboard (Vite + Ant Design + Recharts)
```

See [SPEC.md](SPEC.md) for the full engineering spec and phase plan.

## Tech stack

Postgres (Supabase, pgvector) · Python (feedparser, psycopg) · Claude API ·
LangGraph · FastAPI · React + Vite + Ant Design + Recharts

## Setup

1. **Database** — create a Supabase project, then apply the schema:

   ```bash
   psql "$DATABASE_URL" -f db/schema.sql
   ```

   (or paste `db/schema.sql` into the Supabase SQL editor)

2. **Environment** — copy `.env.example` to `.env` and fill in
   `DATABASE_URL` and `ANTHROPIC_API_KEY`.

3. **Python deps**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows (source .venv/bin/activate on unix)
   pip install -r requirements.txt
   ```

4. **Ingest news**

   ```bash
   python ingest/fetch_news.py
   ```

   Re-running within 10 minutes is skipped (RSS etiquette); duplicate URLs
   are never inserted twice.

5. **Synthetic dev data + analytics** — real RSS volume is too thin to
   exercise the analytics windows, so seed ~5,000 marked-synthetic rows:

   ```bash
   python ingest/generate_synthetic_news.py           # seed
   python analytics/benchmark.py                      # time the 5 queries (<500ms each)
   python ingest/generate_synthetic_news.py --purge   # remove synthetic rows
   ```

   The 5 analytics queries (rolling sentiment, volume-spike detection,
   negative momentum, decision follow-up, win-rate) live in
   [analytics/queries.sql](analytics/queries.sql) and are parsed by
   [analytics/loader.py](analytics/loader.py) — the API reuses these same
   queries.

### Scheduling options

- **Simple loop (local dev):** `python ingest/fetch_news.py --loop`
  fetches every 15 minutes until stopped.
- **Cron (unix):** `*/15 * * * * cd /path/to/repo && python ingest/fetch_news.py`
- **Task Scheduler (Windows):** create a task running
  `python ingest\fetch_news.py` every 15 minutes.

## Project status

- [x] Phase 1-2 — schema + RSS ingest (verified: 5/5 feeds live, dedup works)
- [x] Phase 3-4 — SQL analytics layer (`analytics/queries.sql`, all 5 queries <500ms)
- [x] Phase 5-6 — knowledge base + RAG (`kb/`, 18 cases, local fastembed embeddings)
- [ ] Phase 7-9 — LangGraph multi-agent graph (`agents/`)
- [ ] Phase 10-11 — FastAPI + React dashboard
- [ ] Phase 12 — architecture diagram, screenshots, wrap-up

## Resume bullet drafts (refine after the project is functional)

- **Shopee-leaning:** Built a news-intelligence pipeline in Python +
  Postgres that ingests multi-source RSS data, classifies sentiment with
  an LLM, and surfaces entity-level trends, volume-spike detection, and
  decision win-rates through parameterized SQL analytics and a React
  dashboard.
- **CyberPay-leaning:** Designed a LangGraph multi-agent system
  (Monitor → Sentiment → Impact → Log) with real tool-calling and
  pgvector RAG over hand-curated historical cases, producing
  confidence-scored market-impact assessments with a fully auditable
  reasoning trace.
