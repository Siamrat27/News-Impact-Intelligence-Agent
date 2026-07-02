# SPEC.md — News Impact Intelligence Agent

Full engineering spec for implementation in Claude Code. This is the
authoritative reference — read this before writing any code. Treat each
"Phase" as a milestone with its own acceptance criteria; don't start a
phase until the previous one's criteria are met.

---

## 1. Project Summary

An autonomous multi-agent system that monitors financial/crypto news,
extracts sentiment and entities via NLP, retrieves similar historical
cases via RAG, and produces confidence-scored market-impact assessments.
Every decision is logged and queryable via SQL for backtesting/evaluation.

**Purpose:** portfolio project targeting two internship applications:
- Shopee Operations Analytics & AI (needs: SQL, Python, data dashboards,
  AI classification)
- CyberPay AI Engineer (needs: agentic AI, LangChain/LangGraph, RAG, NLP)

**Explicit non-goal:** this is not a real trading/investment tool. No
part of the system should be framed as investment advice. A disclaimer
must appear in the README and in the dashboard UI itself.

**Explicit domain constraint:** news content stored is limited to
headline, source, URL, publish timestamp, and short RSS-provided summary
snippets (≤500 chars). Full article bodies are never scraped or stored,
for copyright reasons.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Database | Postgres via Supabase | pgvector extension for RAG |
| Ingest | Python + `feedparser` | RSS only, no paid API keys required |
| NLP / reasoning | Claude API (Anthropic SDK) | sentiment scoring, entity extraction, agent reasoning |
| Embeddings | Claude/Voyage or OpenAI embeddings (pick one, see §6.2) | stored in `kb_cases.embedding` |
| Agent orchestration | LangGraph | multi-node graph, see §7 |
| Backend API | FastAPI | serves dashboard, triggers agent runs |
| Frontend | React + Vite + Ant Design + Recharts | consistent with Siamrat's existing stack (AquaDat2, PocketFlow) |
| Deployment | Vercel (frontend) + Supabase (db) + Railway/Render (FastAPI, if needed) | keep free-tier where possible |

---

## 3. Repository Layout

```
news-impact-agent/
├── db/
│   └── schema.sql
├── ingest/
│   └── fetch_news.py
├── analytics/
│   └── queries.sql          # Phase 3 — reference SQL, also used by API
├── kb/
│   ├── cases.md              # human-written source of the 15-20 cases (Phase 5)
│   └── build_embeddings.py   # embeds cases.md entries into kb_cases
├── agents/
│   ├── state.py               # shared LangGraph state schema
│   ├── tools.py                # tool functions: sql_query, rag_retrieve, sentiment_score
│   ├── graph.py                 # LangGraph graph definition (Monitor -> Sentiment -> Impact)
│   └── run.py                    # entrypoint to run one agent cycle
├── api/
│   ├── main.py                    # FastAPI app
│   └── routes/
│       ├── news.py
│       ├── decisions.py
│       └── analytics.py
├── dashboard/
│   └── (Vite React app)
├── docs/
│   └── architecture.png / .excalidraw
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Data Model (see `db/schema.sql` for DDL — already generated)

Tables: `news_items`, `entities`, `news_entities`, `sentiment_scores`,
`kb_cases`, `agent_decisions`, `decision_evaluations`.

Key relationships:
- One `news_item` → many `entities` (via `news_entities`)
- One `news_item` → one `sentiment_scores` row (1:1, latest wins if re-scored)
- One `agent_decision` references one `news_item` + one `entity`, and an
  array of `kb_cases.id` it retrieved during reasoning (RAG trace —
  critical for demoing "agent explains itself")

**Open decision for Claude Code to resolve in Phase 1:** confirm
`kb_cases.embedding` vector dimension matches whichever embedding model
gets used (1536 assumed for OpenAI `text-embedding-3-small`; adjust if
using Voyage or another model).

---

## 5. Phase 1-2 — Ingest + Schema (STATUS: scaffolded, needs testing)

Already generated: `db/schema.sql`, `ingest/fetch_news.py`,
`requirements.txt`, `.env.example`.

**Remaining work:**
- Verify each RSS feed URL in `RSS_FEEDS` is still live (RSS URLs rot —
  check each one manually before relying on it)
- Add at least 5 feeds total, mixing crypto + traditional markets, e.g.:
  CoinDesk, CoinTelegraph, Reuters Business, CNBC Markets, Yahoo Finance
- Add a simple dedup/backoff so re-running `fetch_news.py` on a cron
  doesn't hammer feeds (RSS etiquette: no more than once every 10-15 min)
- Wire up a scheduler: for local dev, cron or a simple `while True: sleep`
  loop is fine; document both options in README

**Acceptance criteria:**
- Running `python ingest/fetch_news.py` twice in a row inserts 0 duplicate
  rows the second time (unique constraint on `url` handles this — verify)
- At least 3 of 5 configured feeds return >0 entries

---

## 6. Phase 3-4 — SQL Analytics Layer

This is the layer that must look substantial for the Shopee application —
don't under-invest here.

### 6.1 Required queries (put in `analytics/queries.sql`, each as a named,
reusable query; these get exposed via `api/routes/analytics.py`)

1. **Rolling sentiment average per entity** — 24h and 7d moving average of
   `sentiment_scores.sentiment`, grouped by entity. Use window functions
   (`avg(...) over (partition by entity_id order by published_at rows
   between ...)`).
2. **News volume spike detection** — for each entity, compare count of
   news items in the trailing 6h window vs. that entity's trailing 7-day
   average 6h-window count. Flag as "spike" if current > 2x baseline.
   Implement with a CTE that buckets time into 6h windows.
3. **Entity ranking by negative sentiment momentum** — entities where
   sentiment is both negative AND trending more negative over the last
   48h (compare first-half vs second-half average within the window).
4. **Agent self-evaluation query** — join `agent_decisions` to
   `news_items` published *after* the decision for the same entity, to
   see whether subsequent sentiment moved in the direction the agent
   predicted. This powers the backtest view.
5. **Win-rate summary** — aggregate `decision_evaluations.accuracy_flag`
   into a percentage, overall and per-entity.

### 6.2 Embeddings decision

Pick ONE:
- **Option A (simpler):** Use OpenAI `text-embedding-3-small` (1536 dim)
  — cheap, well-documented, works fine with pgvector.
- **Option B (fits stack better):** Use Voyage AI embeddings (Anthropic's
  recommended embedding partner) — check current recommended model via
  Anthropic docs at build time since this may have changed.

Claude Code should check current docs (`docs.claude.com`) before locking
this in, since embedding model recommendations change.

**Acceptance criteria:**
- Each of the 5 queries above runs in <500ms against a seeded dataset of
  ~5,000 synthetic news rows (see §9 for synthetic data generation)
- Queries are parameterized (entity_id, time window) — not hardcoded

---

## 7. Phase 5-6 — Knowledge Base + RAG

- Write 15-20 short case studies by hand in `kb/cases.md` — format:
  title, 2-4 sentence description of what happened, what market impact
  followed, and entity_type tag. Mix crypto and traditional market
  examples (e.g. exchange hack, rate decision, earnings surprise,
  regulatory announcement, major partnership).
- `kb/build_embeddings.py` parses `cases.md`, embeds each case, upserts
  into `kb_cases`.
- Retrieval: cosine similarity search (pgvector `<=>` operator), top-k=3,
  exposed as a tool function `rag_retrieve(query_text, k=3)` for the agent.

**Acceptance criteria:**
- Querying with a synthetic headline like "Major exchange halts
  withdrawals amid solvency concerns" retrieves the most topically
  relevant case(s) from the hand-written set, not a random unrelated one
  (spot-check manually, no formal eval needed for a portfolio project)

---

## 8. Phase 7-9 — LangGraph Multi-Agent Graph (core of the project — spend
the most time here)

### 8.1 Shared state (`agents/state.py`)

```python
class AgentState(TypedDict):
    news_item_id: int
    headline: str
    entity_ids: list[int]
    sentiment: float | None
    sentiment_label: str | None
    retrieved_cases: list[dict]      # from RAG, each with id + description
    impact_score: float | None
    confidence: float | None
    reasoning: str | None
```

### 8.2 Nodes

1. **Monitor node** — runs the volume-spike SQL query (§6.1.2) on a
   schedule/trigger; for each flagged entity, pulls the most recent
   un-processed news_item and initializes `AgentState`.
2. **Sentiment node** — calls Claude to score sentiment (-1 to 1) and
   extract/confirm entities from `headline` + `raw_summary`. Writes to
   `sentiment_scores` table.
3. **Impact node** — calls `rag_retrieve` tool with the headline as query,
   gets top-3 similar cases, then prompts Claude with headline + sentiment
   + retrieved cases to produce `impact_score`, `confidence` (0-1), and
   `reasoning` (must explicitly reference which retrieved case(s)
   informed the assessment — this is what makes the RAG trace visible
   and demoable).
4. **Log node** — writes final state to `agent_decisions`, including
   `retrieved_case_ids` array for the audit trail.

### 8.3 Tool-calling requirement

Tools must be real LangGraph/tool-calling constructs (not just plain
function calls glued together) — this is the difference between "agentic"
and "a pipeline that uses an LLM once." The Impact node in particular
should let the model decide whether/how many times to call
`rag_retrieve` rather than it being a fixed, hardcoded call.

**Acceptance criteria:**
- Running `agents/run.py` end-to-end on one flagged entity produces a
  row in `agent_decisions` with non-null `reasoning` that mentions at
  least one retrieved case by name
- Graph execution trace (LangGraph's built-in state history) can be
  printed/logged for debugging and for the dashboard's "reasoning trace"
  view

---

## 9. Synthetic Data for Development

Real RSS feeds are low-volume for dev/testing. Write a small script
(`ingest/generate_synthetic_news.py`, not yet created) that inserts
~5,000 fake-but-plausible news rows across a handful of entities with
randomized timestamps and sentiment-correlated headlines, so that Phase
3-4 SQL queries and Phase 7-9 agent runs have enough data to look
meaningful in the dashboard. Clearly mark synthetic data as such (e.g.
`source = 'synthetic'`) so it can be filtered out later if real data
volume grows.

---

## 10. Phase 10-11 — API + Dashboard

### 10.1 API endpoints (`api/`)

- `GET /news/recent` — paginated recent news items with sentiment
- `GET /entities/{id}/trend` — rolling sentiment + volume for one entity
- `GET /decisions/recent` — recent agent decisions with reasoning + RAG trace
- `GET /analytics/winrate` — backtest summary (§6.1.5)
- `POST /agent/run` — manually trigger one agent cycle (for demo purposes)

### 10.2 Dashboard pages

- **Live Feed** — stream of incoming news items with sentiment badge
- **Entity Detail** — trend chart (Recharts) + list of agent decisions for
  that entity + which historical cases were cited
- **Agent Reasoning Trace** — for a selected decision, show the full
  chain: headline → sentiment → retrieved cases → final impact/confidence
  (this is the single most important screen for the CyberPay application —
  it's the visual proof of "agentic," not just "ML")
- **Backtest / Win-rate** — table + chart of decision accuracy over time

**Disclaimer banner** must appear on every dashboard page (small footer
or top banner): "Educational demo — not investment advice."

**Acceptance criteria:**
- Dashboard loads real data from the FastAPI backend (not mocked)
- Reasoning Trace page is screenshot-able as a portfolio piece on its own

---

## 11. Phase 12 — Wrap-up

- Architecture diagram (can use Excalidraw or Claude's own diagram tool)
- Update README with final setup instructions + screenshots
- Write two resume bullet variants (Shopee-leaning, CyberPay-leaning) —
  drafts already exist in README, refine after the project is functional
- Push to GitHub with a clean commit history (or at least a clean final
  state) since both applications may ask for a portfolio/GitHub link

---

## 12. Known Risks / Things to Watch

- **RSS feed URLs rot** — verify feeds are alive at the start of the
  project, not just once in Phase 1
- **Embedding model choice** may have changed since this spec was written
  — check `docs.claude.com` / Anthropic's embedding guidance before
  locking in Phase 5-6
- **Rate limits** on Claude API calls if the agent runs frequently on a
  large synthetic dataset — batch or throttle calls during development
- **Time budget is tight (12 days)** — if behind schedule, cut scope in
  this order: (1) drop live RSS scheduling, keep manual trigger; (2) drop
  win-rate backtest UI, keep the table; (3) reduce KB cases from 20 to 10;
  never cut the LangGraph reasoning trace — it's the core differentiator

---

## 13. Handoff Notes for Claude Code

- Phases 1-2 are already scaffolded (see repo). Start by running and
  verifying them (§5 acceptance criteria) before writing new code.
- Work phase by phase; don't jump ahead to the dashboard before the agent
  graph produces real `agent_decisions` rows.
- Prefer a `CLAUDE.md` in the repo root (separate from this SPEC.md)
  capturing any project-specific conventions/gotchas discovered during
  implementation, consistent with how other projects in this workspace
  (e.g. AquaDat2) are documented.
