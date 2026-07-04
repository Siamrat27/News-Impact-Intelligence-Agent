"""Parse kb/cases.md, embed each case locally, upsert into kb_cases.

Embedding model (SPEC §6.2 decision): fastembed's BAAI/bge-small-en-v1.5 —
384-dim ONNX model that runs locally, free, no API key. kb_cases.embedding
is vector(384) to match.

Usage:
    python kb/build_embeddings.py
"""

import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastembed import TextEmbedding

CASES_FILE = Path(__file__).parent / "cases.md"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

_CASE_RE = re.compile(
    r"^## (?P<title>.+?)\n"
    r".*?^type:\s*(?P<entity_type>\w+)\s*$"
    r".*?\*\*What happened:\*\*\s*(?P<description>.+?)"
    r"\*\*Market impact:\*\*\s*(?P<market_impact>.+?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().rstrip("-").strip()


def parse_cases(text: str) -> list[dict]:
    cases = []
    for m in _CASE_RE.finditer(text):
        cases.append({
            "title": m["title"].strip(),
            "entity_type": m["entity_type"].strip(),
            "description": _squash(m["description"]),
            "market_impact": _squash(m["market_impact"]),
        })
    return cases


def main() -> None:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set.")

    cases = parse_cases(CASES_FILE.read_text(encoding="utf-8"))
    if len(cases) < 15:
        sys.exit(f"Parsed only {len(cases)} cases from cases.md — expected "
                 f"15-20; check the file format.")
    print(f"Parsed {len(cases)} cases; embedding with {EMBEDDING_MODEL} ...")

    model = TextEmbedding(EMBEDDING_MODEL)
    passages = [f"{c['title']}. {c['description']} {c['market_impact']}"
                for c in cases]
    embeddings = list(model.embed(passages))

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        for case, emb in zip(cases, embeddings):
            cur.execute(
                """
                insert into kb_cases
                    (title, description, market_impact, entity_type, embedding)
                values (%(title)s, %(description)s, %(market_impact)s,
                        %(entity_type)s, %(embedding)s::vector)
                on conflict (title) do update set
                    description   = excluded.description,
                    market_impact = excluded.market_impact,
                    entity_type   = excluded.entity_type,
                    embedding     = excluded.embedding
                """,
                {**case, "embedding": "[" + ",".join(map(str, emb)) + "]"},
            )
        conn.commit()
        n = cur.execute("select count(*) from kb_cases").fetchone()[0]
    print(f"kb_cases now holds {n} embedded cases.")


if __name__ == "__main__":
    main()
