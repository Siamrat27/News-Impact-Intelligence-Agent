"""DB helpers for API routes: run queries, return list-of-dict rows."""

import os

import psycopg
from psycopg.rows import dict_row


def fetch_all(sql: str, params: dict | tuple = ()) -> list[dict]:
    with psycopg.connect(os.environ["DATABASE_URL"],
                         row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: dict | tuple = ()) -> dict | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None
