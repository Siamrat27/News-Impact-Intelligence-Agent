"""Analytics endpoints — thin wrappers over analytics/queries.sql
(single source of truth for the SQL; CLAUDE.md convention)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Query

from analytics.loader import load_queries
from api.db import fetch_all

router = APIRouter(prefix="/analytics", tags=["analytics"])
QUERIES = load_queries()


@router.get("/winrate")
def winrate() -> list[dict]:
    return fetch_all(QUERIES["win_rate"], {})


@router.get("/spikes")
def spikes(spike_factor: float = Query(2.0, ge=1.0),
           include_synthetic: bool = True) -> list[dict]:
    return fetch_all(QUERIES["volume_spikes"], {
        "as_of": datetime.now(timezone.utc),
        "spike_factor": spike_factor,
        "include_synthetic": include_synthetic,
    })


@router.get("/negative-momentum")
def negative_momentum(window_hours: int = Query(48, ge=6, le=336),
                      include_synthetic: bool = True) -> list[dict]:
    return fetch_all(QUERIES["negative_momentum"], {
        "as_of": datetime.now(timezone.utc),
        "window_hours": window_hours,
        "include_synthetic": include_synthetic,
    })


@router.get("/follow-up")
def follow_up(horizon_hours: int = Query(24, ge=1, le=168),
              limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    return fetch_all(QUERIES["decision_follow_up"], {
        "horizon_hours": horizon_hours, "limit": limit,
    })
