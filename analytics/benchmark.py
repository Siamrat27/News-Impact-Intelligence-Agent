"""Run every query in queries.sql with sample params and time it.

Acceptance criterion (SPEC §6.1): each query < 500ms against ~5,000 rows.

Usage:
    python analytics/benchmark.py
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analytics.loader import load_queries  # noqa: E402

NOW = datetime.now(timezone.utc)

SAMPLE_PARAMS = {
    "rolling_sentiment": {
        "entity_id": None,  # resolved to Bitcoin's id at runtime
        "since": NOW - timedelta(days=7),
        "include_synthetic": True,
    },
    "volume_spikes": {
        "as_of": NOW,
        "spike_factor": 2.0,
        "include_synthetic": True,
    },
    "negative_momentum": {
        "as_of": NOW,
        "window_hours": 48,
        "include_synthetic": True,
    },
    "decision_follow_up": {
        "horizon_hours": 24,
        "limit": 50,
    },
    "win_rate": {},
}


def main() -> None:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set.")

    queries = load_queries()
    failures = 0

    with psycopg.connect(url) as conn:
        btc_id = conn.execute(
            "select id from entities where name = 'Bitcoin'").fetchone()
        if btc_id:
            SAMPLE_PARAMS["rolling_sentiment"]["entity_id"] = btc_id[0]

        # warm the connection so TLS/auth setup isn't billed to query 1
        conn.execute("select 1")

        for name, sql in queries.items():
            params = SAMPLE_PARAMS.get(name, {})
            # best of 2: the second run reflects warm (API-serving) latency
            timings = []
            for _ in range(2):
                start = time.perf_counter()
                rows = conn.execute(sql, params).fetchall()
                timings.append((time.perf_counter() - start) * 1000)
            ms = min(timings)
            status = "OK  " if ms < 500 else "SLOW"
            if ms >= 500:
                failures += 1
            print(f"{status} {name:<22} {ms:7.1f} ms  {len(rows):>5} rows")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
