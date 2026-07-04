"""FastAPI app (SPEC §10.1).

Run:  uvicorn api.main:app --reload --port 8000
The dashboard dev server proxies /api/* here (see dashboard/vite.config.js).
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI                          # noqa: E402
from fastapi.middleware.cors import CORSMiddleware   # noqa: E402

from api.routes import analytics, decisions, news    # noqa: E402

app = FastAPI(
    title="News Impact Intelligence Agent",
    description="Educational demo — not investment advice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router)
app.include_router(decisions.router)
app.include_router(analytics.router)


@app.on_event("startup")
def warm_pool() -> None:
    from api.db import _pool
    _pool()  # open DB connections now, not on the first request


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
