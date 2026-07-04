"""LangGraph graph definition (SPEC §8.2): Monitor → Sentiment → Impact → Log.

The Impact node binds the rag_retrieve / sql_query tools to the model and
loops on tool calls — the model decides whether and how many times to
consult the knowledge base before committing to an assessment (§8.3).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analytics.loader import load_queries            # noqa: E402
from agents.db import get_conn                       # noqa: E402
from agents.llm import get_chat_model, model_name    # noqa: E402
from agents.state import AgentState                  # noqa: E402
from agents.tools import rag_retrieve, sql_query     # noqa: E402

MAX_TOOL_ROUNDS = 4


# --------------------------------------------------------------------------
# Monitor node — find a spike-flagged entity with an unprocessed news item
# --------------------------------------------------------------------------
def monitor(state: AgentState) -> AgentState:
    queries = load_queries()
    with get_conn() as conn:
        if state.get("news_item_id"):
            # manual trigger (--news-id / POST /agent/run): skip spike scan
            row = conn.execute(
                """
                select n.id, n.headline, n.raw_summary, e.id, e.name
                from news_items n
                left join news_entities ne on ne.news_item_id = n.id
                left join entities e       on e.id = ne.entity_id
                where n.id = %s
                limit 1
                """,
                (state["news_item_id"],),
            ).fetchone()
            if not row:
                return {"news_item_id": None}
            nid, headline, summary, eid, ename = row
            return {"news_item_id": nid, "headline": headline,
                    "raw_summary": summary, "focus_entity_id": eid,
                    "focus_entity_name": ename}

        spikes = conn.execute(queries["volume_spikes"], {
            "as_of": datetime.now(timezone.utc),
            "spike_factor": 2.0,
            "include_synthetic": True,
        }).fetchall()
        flagged = [r for r in spikes if r[5]]  # is_spike column
        for entity_id, entity_name, *_ in flagged:
            row = conn.execute(
                """
                select n.id, n.headline, n.raw_summary
                from news_items n
                join news_entities ne on ne.news_item_id = n.id
                where ne.entity_id = %s and not n.processed
                order by n.published_at desc
                limit 1
                """,
                (entity_id,),
            ).fetchone()
            if row:
                return {"news_item_id": row[0], "headline": row[1],
                        "raw_summary": row[2], "focus_entity_id": entity_id,
                        "focus_entity_name": entity_name}
    return {"news_item_id": None}  # nothing to do -> graph ends


def has_work(state: AgentState) -> str:
    return "sentiment" if state.get("news_item_id") else END


# --------------------------------------------------------------------------
# Sentiment node — score sentiment + extract/confirm entities, write to DB
# --------------------------------------------------------------------------
class SentimentResult(BaseModel):
    sentiment: float = Field(ge=-1, le=1,
                             description="overall market sentiment of the news")
    sentiment_label: str = Field(description="negative, neutral, or positive")
    entities: list[str] = Field(
        description="market entities the news is about (companies, coins, "
                    "institutions, indexes) — canonical short names")


def sentiment(state: AgentState) -> AgentState:
    llm = get_chat_model().with_structured_output(SentimentResult)
    result: SentimentResult = llm.invoke([
        SystemMessage(
            "You score financial news sentiment from -1 (very bearish) to 1 "
            "(very bullish) and extract the market entities involved."),
        HumanMessage(
            f"Headline: {state['headline']}\n"
            f"Summary: {state.get('raw_summary') or '(none)'}"),
    ])
    label = result.sentiment_label.lower()
    if label not in ("negative", "neutral", "positive"):
        label = "neutral"

    entity_ids = []
    with get_conn() as conn:
        conn.execute(
            """
            insert into sentiment_scores
                (news_item_id, sentiment, sentiment_label, model)
            values (%s, %s, %s, %s)
            on conflict (news_item_id) do update set
                sentiment = excluded.sentiment,
                sentiment_label = excluded.sentiment_label,
                model = excluded.model,
                scored_at = now()
            """,
            (state["news_item_id"], round(result.sentiment, 3), label,
             model_name()),
        )
        for name in result.entities[:5]:
            row = conn.execute(
                """
                insert into entities (name, entity_type)
                values (%s, 'other')
                on conflict (name) do update set name = excluded.name
                returning id
                """,
                (name.strip(),),
            ).fetchone()
            conn.execute(
                """
                insert into news_entities (news_item_id, entity_id)
                values (%s, %s) on conflict do nothing
                """,
                (state["news_item_id"], row[0]),
            )
            entity_ids.append(row[0])
        conn.commit()

    return {"sentiment": round(result.sentiment, 3),
            "sentiment_label": label,
            "entity_ids": entity_ids}


# --------------------------------------------------------------------------
# Impact node — agentic loop: model calls tools, then commits an assessment
# --------------------------------------------------------------------------
class ImpactAssessment(BaseModel):
    impact_score: float = Field(
        ge=-1, le=1, description="expected market impact direction/size")
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(
        description="2-5 sentences; MUST cite at least one retrieved "
                    "historical case by its title")


def impact(state: AgentState) -> AgentState:
    tools = {"rag_retrieve": rag_retrieve, "sql_query": sql_query}
    llm = get_chat_model().bind_tools(list(tools.values()))

    messages = [
        SystemMessage(
            "You are a market-impact analyst. Assess the likely market "
            "impact of a news item on the focus entity. Ground your "
            "assessment in historical precedent: use rag_retrieve to find "
            "similar past cases (you may search more than once with "
            "different phrasings), and optionally sql_query for recent "
            "data context. Then give impact_score (-1..1), confidence "
            "(0..1), and reasoning that cites retrieved case titles."),
        HumanMessage(
            f"Focus entity: {state.get('focus_entity_name') or 'unknown'}\n"
            f"Headline: {state['headline']}\n"
            f"Summary: {state.get('raw_summary') or '(none)'}\n"
            f"Sentiment: {state.get('sentiment')} "
            f"({state.get('sentiment_label')})"),
    ]

    retrieved: dict[int, dict] = {}
    for _ in range(MAX_TOOL_ROUNDS):
        response = llm.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            break
        for call in response.tool_calls:
            fn = tools.get(call["name"])
            result = (fn.invoke(call["args"]) if fn
                      else [{"error": f"unknown tool {call['name']}"}])
            if call["name"] == "rag_retrieve":
                for case in result:
                    if "id" in case:
                        retrieved[case["id"]] = {
                            "id": case["id"], "title": case["title"],
                            "similarity": case["similarity"]}
            messages.append(ToolMessage(content=str(result),
                                        tool_call_id=call["id"]))

    final = get_chat_model().with_structured_output(ImpactAssessment).invoke(
        messages + [HumanMessage(
            "Commit your final assessment now as structured output.")])

    return {"retrieved_cases": list(retrieved.values()),
            "impact_score": round(final.impact_score, 3),
            "confidence": round(final.confidence, 3),
            "reasoning": final.reasoning}


# --------------------------------------------------------------------------
# Log node — persist the decision with its RAG audit trail
# --------------------------------------------------------------------------
def log(state: AgentState) -> AgentState:
    case_ids = [c["id"] for c in state.get("retrieved_cases", [])]
    with get_conn() as conn:
        row = conn.execute(
            """
            insert into agent_decisions
                (news_item_id, entity_id, impact_score, confidence,
                 reasoning, retrieved_case_ids)
            values (%s, %s, %s, %s, %s, %s)
            returning id
            """,
            (state["news_item_id"],
             state.get("focus_entity_id") or state["entity_ids"][0],
             state["impact_score"], state["confidence"],
             state["reasoning"], case_ids),
        ).fetchone()
        conn.execute("update news_items set processed = true where id = %s",
                     (state["news_item_id"],))
        conn.commit()
    return {"decision_id": row[0]}


# --------------------------------------------------------------------------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("monitor", monitor)
    g.add_node("sentiment", sentiment)
    g.add_node("impact", impact)
    g.add_node("log", log)
    g.set_entry_point("monitor")
    g.add_conditional_edges("monitor", has_work,
                            {"sentiment": "sentiment", END: END})
    g.add_edge("sentiment", "impact")
    g.add_edge("impact", "log")
    g.add_edge("log", END)
    return g.compile()
