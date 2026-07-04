"""Agent decision endpoints, including the reasoning-trace detail and the
manual agent trigger (SPEC §10.1)."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.db import fetch_all, fetch_one

router = APIRouter(tags=["decisions"])


@router.get("/decisions/recent")
def recent_decisions(limit: int = Query(25, ge=1, le=100)) -> list[dict]:
    return fetch_all(
        """
        select d.id, d.created_at, d.impact_score, d.confidence,
               d.reasoning, d.retrieved_case_ids,
               e.name as entity, n.headline,
               ev.accuracy_flag, ev.subsequent_sentiment
        from agent_decisions d
        join entities e   on e.id = d.entity_id
        join news_items n on n.id = d.news_item_id
        left join decision_evaluations ev on ev.decision_id = d.id
        order by d.created_at desc
        limit %s
        """,
        (limit,),
    )


@router.get("/decisions/{decision_id}")
def decision_trace(decision_id: int) -> dict:
    """Full reasoning-trace payload: headline -> sentiment -> retrieved
    cases -> impact/confidence/reasoning."""
    decision = fetch_one(
        """
        select d.id, d.created_at, d.impact_score, d.confidence,
               d.reasoning, d.retrieved_case_ids,
               e.id as entity_id, e.name as entity, e.entity_type,
               n.id as news_item_id, n.headline, n.raw_summary, n.source,
               n.url, n.published_at,
               s.sentiment, s.sentiment_label, s.model as sentiment_model,
               ev.accuracy_flag, ev.subsequent_sentiment
        from agent_decisions d
        join entities e   on e.id = d.entity_id
        join news_items n on n.id = d.news_item_id
        left join sentiment_scores s      on s.news_item_id = n.id
        left join decision_evaluations ev on ev.decision_id = d.id
        where d.id = %s
        """,
        (decision_id,),
    )
    if not decision:
        raise HTTPException(404, "decision not found")
    cases = fetch_all(
        """
        select id, title, description, market_impact, entity_type
        from kb_cases
        where id = any(%s)
        """,
        (decision["retrieved_case_ids"],),
    )
    # preserve retrieval order
    order = {cid: i for i, cid in enumerate(decision["retrieved_case_ids"])}
    decision["retrieved_cases"] = sorted(cases,
                                         key=lambda c: order.get(c["id"], 99))
    return decision


class RunRequest(BaseModel):
    news_id: int | None = None


@router.post("/agent/run")
def run_agent(body: RunRequest) -> dict:
    """Manually trigger one agent cycle (demo). Synchronous — an LLM cycle
    takes a few seconds on Groq."""
    from agents.graph import build_graph  # deferred: heavy import

    graph = build_graph()
    initial = {"news_item_id": body.news_id} if body.news_id else {}
    final: dict = {}
    for step in graph.stream(initial, stream_mode="updates"):
        for _node, delta in step.items():
            final.update(delta or {})
    if not final.get("decision_id"):
        return {"ran": False,
                "detail": "no unprocessed news for any spike-flagged entity"}
    return {"ran": True, "decision_id": final["decision_id"],
            "impact_score": final.get("impact_score"),
            "confidence": final.get("confidence")}
