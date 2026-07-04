"""RAG retrieval over kb_cases (pgvector cosine similarity).

`rag_retrieve` is the core function; agents/tools.py wraps it as a
LangGraph tool in Phase 7-9.

Usage (spot-check):
    python kb/retrieve.py "Major exchange halts withdrawals amid solvency concerns"
"""

import os
import sys
from functools import lru_cache

import psycopg
from dotenv import load_dotenv
from fastembed import TextEmbedding

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(EMBEDDING_MODEL)


def rag_retrieve(query_text: str, k: int = 3) -> list[dict]:
    """Return the k most similar KB cases for a query (e.g. a headline).

    Each result: {id, title, description, market_impact, entity_type,
    similarity} with similarity = 1 - cosine distance.
    """
    # query_embed applies the model's recommended query-side prompt prefix
    query_emb = next(_model().query_embed(query_text))
    vec = "[" + ",".join(map(str, query_emb)) + "]"
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            """
            select id, title, description, market_impact, entity_type,
                   1 - (embedding <=> %(vec)s::vector) as similarity
            from kb_cases
            order by embedding <=> %(vec)s::vector
            limit %(k)s
            """,
            {"vec": vec, "k": k},
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "description": r[2],
         "market_impact": r[3], "entity_type": r[4],
         "similarity": round(float(r[5]), 4)}
        for r in rows
    ]


if __name__ == "__main__":
    load_dotenv()
    query = " ".join(sys.argv[1:]) or \
        "Major exchange halts withdrawals amid solvency concerns"
    print(f"Query: {query}\n")
    for case in rag_retrieve(query):
        print(f"  {case['similarity']:.4f}  [{case['entity_type']}] "
              f"{case['title']}")
