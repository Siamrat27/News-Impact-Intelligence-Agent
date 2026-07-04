"""Shared LangGraph state schema (SPEC §8.1)."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    # set by the Monitor node
    news_item_id: int | None
    headline: str
    raw_summary: str | None
    focus_entity_id: int | None      # the spike-flagged entity under analysis
    focus_entity_name: str | None

    # set by the Sentiment node
    entity_ids: list[int]            # entities extracted/confirmed for the item
    sentiment: float | None          # -1 .. 1
    sentiment_label: str | None      # negative / neutral / positive

    # set by the Impact node
    retrieved_cases: list[dict]      # RAG trace: id, title, similarity per call
    impact_score: float | None       # -1 .. 1
    confidence: float | None         # 0 .. 1
    reasoning: str | None            # must cite retrieved case(s) by name

    # set by the Log node
    decision_id: int | None
