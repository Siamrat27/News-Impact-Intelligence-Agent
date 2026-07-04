"""News + entity endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from analytics.loader import load_queries
from api.db import fetch_all

router = APIRouter(tags=["news"])
QUERIES = load_queries()


@router.get("/news/recent")
def recent_news(page: int = Query(1, ge=1),
                page_size: int = Query(25, ge=1, le=100),
                include_synthetic: bool = True) -> dict:
    rows = fetch_all(
        """
        select n.id, n.headline, n.source, n.url, n.published_at,
               s.sentiment, s.sentiment_label,
               coalesce(array_agg(e.name) filter (where e.name is not null),
                        '{}') as entities
        from news_items n
        left join sentiment_scores s on s.news_item_id = n.id
        left join news_entities ne   on ne.news_item_id = n.id
        left join entities e         on e.id = ne.entity_id
        where (%(include_synthetic)s or n.source <> 'synthetic')
        group by n.id, s.sentiment, s.sentiment_label
        order by n.published_at desc
        limit %(limit)s offset %(offset)s
        """,
        {"include_synthetic": include_synthetic, "limit": page_size,
         "offset": (page - 1) * page_size},
    )
    return {"page": page, "page_size": page_size, "items": rows}


@router.get("/entities")
def list_entities() -> list[dict]:
    return fetch_all(
        """
        select e.id, e.name, e.entity_type, e.ticker,
               count(ne.news_item_id) as news_count
        from entities e
        left join news_entities ne on ne.entity_id = e.id
        group by e.id
        order by news_count desc
        """
    )


@router.get("/entities/{entity_id}/trend")
def entity_trend(entity_id: int, hours: int = Query(168, ge=6, le=720),
                 include_synthetic: bool = True) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    params = {"entity_id": entity_id, "since": since,
              "include_synthetic": include_synthetic}
    sentiment = fetch_all(QUERIES["rolling_sentiment"], params)
    volume = fetch_all(QUERIES["entity_volume"], params)
    if not sentiment and not volume:
        raise HTTPException(404, "no data for this entity in the window")
    return {"entity_id": entity_id, "sentiment": sentiment, "volume": volume}
