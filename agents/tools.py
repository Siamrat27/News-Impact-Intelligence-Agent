"""LangChain tool definitions for the agent graph (SPEC §8.3).

These are real tool-calling constructs bound to the model — the Impact
node's model decides whether and how many times to call them.

`sql_query` deliberately runs only the named, parameterized queries from
analytics/queries.sql rather than arbitrary SQL (prompt-injection safety).
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from langchain_core.tools import tool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analytics.loader import load_queries          # noqa: E402
from kb.retrieve import rag_retrieve as _rag       # noqa: E402
from agents.db import get_conn                     # noqa: E402


@tool
def rag_retrieve(query_text: str, k: int = 3) -> list[dict]:
    """Retrieve the k most similar historical market-impact cases from the
    knowledge base for a query (e.g. a news headline). Each case includes
    what happened and what market impact followed. Use this to ground your
    impact assessment in historical precedent."""
    return _rag(query_text, k)


@tool
def sql_query(query_name: str, entity_id: int | None = None) -> list[dict]:
    """Run a named analytics query against the news database. Available:
    'rolling_sentiment' (recent sentiment trend for entity_id, last 7 days),
    'volume_spikes' (which entities have unusual news volume right now),
    'negative_momentum' (entities trending negative over the last 48h).
    Use this to check the recent data context around an entity."""
    queries = load_queries()
    if query_name not in ("rolling_sentiment", "volume_spikes",
                          "negative_momentum"):
        return [{"error": f"unknown query_name {query_name!r}"}]
    now = datetime.now(timezone.utc)
    params = {
        "rolling_sentiment": {"entity_id": entity_id,
                              "since": now - timedelta(days=7),
                              "include_synthetic": True},
        "volume_spikes": {"as_of": now, "spike_factor": 2.0,
                          "include_synthetic": True},
        "negative_momentum": {"as_of": now, "window_hours": 48,
                              "include_synthetic": True},
    }[query_name]
    with get_conn() as conn:
        cur = conn.execute(queries[query_name], params)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    # keep tool output small for the model
    return [dict(zip(cols, map(str, r))) for r in rows[:20]]
