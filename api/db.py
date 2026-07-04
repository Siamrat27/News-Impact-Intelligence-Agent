"""DB helpers for API routes: run queries, return list-of-dict rows.

Uses a shared connection pool — the Supabase pooler is ~1s away (TLS +
auth per fresh connection), so opening a connection per request made
concurrent dashboard loads stack up multi-second latencies.
"""

import os
from functools import lru_cache

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


@lru_cache(maxsize=1)
def _pool() -> ConnectionPool:
    pool = ConnectionPool(
        os.environ["DATABASE_URL"],
        min_size=3,          # keep a few warm — cold TLS+auth costs ~1s each
        max_size=8,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    pool.wait(timeout=30)    # block until min_size connections are ready
    return pool


def fetch_all(sql: str, params: dict | tuple = ()) -> list[dict]:
    with _pool().connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: dict | tuple = ()) -> dict | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None
