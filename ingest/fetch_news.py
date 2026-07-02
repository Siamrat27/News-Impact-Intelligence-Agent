"""Fetch financial/crypto news headlines from RSS feeds into Postgres.

Stores ONLY headline, source, URL, publish timestamp, and a short
RSS-provided summary snippet (<=500 chars). Full article bodies are never
scraped or stored (SPEC §1, copyright constraint).

Usage:
    python ingest/fetch_news.py            # one pass (skipped if run <10 min ago)
    python ingest/fetch_news.py --force    # one pass, ignore the cooldown
    python ingest/fetch_news.py --loop     # run forever, one pass every 15 min

RSS etiquette (SPEC §5): a state file enforces a 10-minute cooldown between
passes so a misconfigured cron can't hammer the feeds.
"""

import argparse
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import psycopg
from dotenv import load_dotenv

# NOTE: RSS URLs rot (SPEC §12) — re-verify these are alive before relying
# on them. Reuters retired its public RSS feeds; MarketWatch stands in as the
# traditional-markets counterpart.
RSS_FEEDS = {
    "coindesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "cnbc_markets":  "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
    "marketwatch":   "https://feeds.content.dowjones.io/public/rss/mw_topstories",
}

SUMMARY_MAX_CHARS = 500
COOLDOWN_MINUTES = 10
LOOP_INTERVAL_MINUTES = 15
STATE_FILE = Path(__file__).parent / ".fetch_state.json"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_summary(raw: str | None) -> str | None:
    """Strip HTML tags/entities from an RSS summary and cap its length."""
    if not raw:
        return None
    text = _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", raw))).strip()
    return text[:SUMMARY_MAX_CHARS] or None


def parse_published(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def cooldown_remaining() -> float:
    """Minutes left on the cooldown, or 0 if a pass may run now."""
    try:
        last_run = json.loads(STATE_FILE.read_text())["last_run"]
    except (FileNotFoundError, KeyError, ValueError):
        return 0.0
    elapsed = (datetime.now(timezone.utc)
               - datetime.fromisoformat(last_run)).total_seconds() / 60
    return max(0.0, COOLDOWN_MINUTES - elapsed)


def mark_run() -> None:
    STATE_FILE.write_text(
        json.dumps({"last_run": datetime.now(timezone.utc).isoformat()})
    )


def fetch_feed(source: str, url: str) -> list[tuple]:
    """Return (headline, source, url, published_at, raw_summary) rows."""
    parsed = feedparser.parse(url)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"feed unreadable: {parsed.bozo_exception!r}")
    rows = []
    for entry in parsed.entries:
        headline = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not headline or not link:
            continue
        rows.append((
            headline,
            source,
            link,
            parse_published(entry),
            clean_summary(entry.get("summary")),
        ))
    return rows


def insert_items(conn: psycopg.Connection, rows: list[tuple]) -> int:
    """Insert rows, deduping on url; returns the number actually inserted."""
    inserted = 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """
                insert into news_items
                    (headline, source, url, published_at, raw_summary)
                values (%s, %s, %s, %s, %s)
                on conflict (url) do nothing
                """,
                row,
            )
            inserted += cur.rowcount
    conn.commit()
    return inserted


def run_once(force: bool = False) -> None:
    remaining = cooldown_remaining()
    if remaining > 0 and not force:
        print(f"Last pass was <{COOLDOWN_MINUTES} min ago "
              f"({remaining:.1f} min cooldown left) — skipping. "
              f"Use --force to override.")
        return
    mark_run()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("DATABASE_URL is not set — copy .env.example to .env first.")

    total_seen = total_inserted = feeds_ok = 0
    with psycopg.connect(database_url) as conn:
        for source, url in RSS_FEEDS.items():
            try:
                rows = fetch_feed(source, url)
            except Exception as exc:  # a dead feed must not kill the pass
                print(f"  {source:<15} FAILED: {exc}")
                continue
            inserted = insert_items(conn, rows)
            feeds_ok += 1 if rows else 0
            total_seen += len(rows)
            total_inserted += inserted
            print(f"  {source:<15} {len(rows):>3} entries, {inserted:>3} new")

    print(f"Done: {feeds_ok}/{len(RSS_FEEDS)} feeds returned entries, "
          f"{total_inserted}/{total_seen} rows inserted.")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="ignore the 10-minute cooldown")
    parser.add_argument("--loop", action="store_true",
                        help=f"run forever, every {LOOP_INTERVAL_MINUTES} min")
    args = parser.parse_args()

    if args.loop:
        while True:
            run_once(force=args.force)
            time.sleep(LOOP_INTERVAL_MINUTES * 60)
    else:
        run_once(force=args.force)


if __name__ == "__main__":
    main()
