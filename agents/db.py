"""Shared DB connection helper for the agent modules."""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_conn() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set — copy .env.example to .env")
    return psycopg.connect(url)
