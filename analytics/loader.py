"""Parse analytics/queries.sql into named queries.

Used by both the benchmark script and api/routes/analytics.py so the SQL
lives in exactly one place (CLAUDE.md convention).
"""

import re
from pathlib import Path

QUERIES_FILE = Path(__file__).parent / "queries.sql"

_NAME_RE = re.compile(r"^-- name:\s*(\w+)\s*$", re.MULTILINE)


def load_queries() -> dict[str, str]:
    """Return {query_name: sql_text} from queries.sql."""
    text = QUERIES_FILE.read_text(encoding="utf-8")
    parts = _NAME_RE.split(text)
    # parts = [preamble, name1, body1, name2, body2, ...]
    return {parts[i]: parts[i + 1].strip().rstrip(";")
            for i in range(1, len(parts), 2)}
