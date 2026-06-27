"""
scrape_reddit.py — TakeMeter r/soccer scraper
Uses Pushshift/Pullpush public API (no auth, no API key needed).
Collects post titles, selftexts, and top-level comments from r/soccer.
"""

import csv
import time
import random
import re
import json

import requests

OUTPUT_FILE = "raw_data.csv"
SUBREDDIT = "soccer"

# Pullpush — public Pushshift mirror, no auth needed
BASE_URL = "https://api.pullpush.io/reddit/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

MIN_CHARS = 30
MAX_CHARS = 1000
TARGET_ROWS = 250
DELAY_RANGE = (1.5, 2.5)

# How many batches of posts/comments to pull (100 per batch max)
POST_BATCHES = 5        # 5 × 100 = up to 500 posts
COMMENT_BATCHES = 5     # 5 × 100 = up to 500 comments


def delay():
    time.sleep(random.uniform(*DELAY_RANGE))


def get_json(url: str, params: dict) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 20))
            print(f"  [rate limited] waiting {wait}s")
            time.sleep(wait + 2)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  [skip] HTTP {resp.status_code}")
            return []
        data = resp.json()
        return data.get("data", [])
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"  [error] {e}")
        return []


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_valid(text: str) -> bool:
    if not text:
        return False
    lo = text.lower().strip()
    # Reject exact or partial deleted/removed markers and Reddit poll links
    if lo in {"[deleted]", "[removed]", ""}:
        return False
    if lo.startswith("[removed]") or lo.startswith("[deleted]"):
        return False
    if "reddit.com/poll/" in lo:
        return False
    return MIN_CHARS <= len(text) <= MAX_CHARS


def scrape_posts() -> list[dict]:
    """Pull post titles and selftexts via Pullpush submission endpoint."""
    rows: list[dict] = []
    before = None  # epoch timestamp for pagination

    print(f"\n[posts] fetching up to {POST_BATCHES * 100} submissions")

    for batch in range(POST_BATCHES):
        params = {
            "subreddit": SUBREDDIT,
            "size": 100,
            "sort": "desc",
            "sort_type": "score",       # high-scored posts = richer text
            "fields": "title,selftext,permalink,created_utc",
        }
        if before:
            params["before"] = before

        print(f"  batch {batch + 1}/{POST_BATCHES}  before={before}")
        items = get_json(f"{BASE_URL}/submission/", params)
        if not items:
            print("  no more items, stopping")
            break

        for item in items:
            title = clean(item.get("title", ""))
            selftext = clean(item.get("selftext", ""))
            for text in [title, selftext]:
                if is_valid(text):
                    rows.append({"text": text, "label": "", "notes": "post"})

        # Advance pagination cursor
        last_ts = items[-1].get("created_utc")
        if last_ts:
            before = int(last_ts)

        print(f"    got {len(items)} posts — rows so far: {len(rows)}")
        delay()

    return rows


def scrape_comments() -> list[dict]:
    """Pull comments via Pullpush comment endpoint."""
    rows: list[dict] = []
    before = None

    print(f"\n[comments] fetching up to {COMMENT_BATCHES * 100} comments")

    for batch in range(COMMENT_BATCHES):
        params = {
            "subreddit": SUBREDDIT,
            "size": 100,
            "sort": "desc",
            "sort_type": "score",       # high-scored comments = higher quality
            "fields": "body,created_utc",
        }
        if before:
            params["before"] = before

        print(f"  batch {batch + 1}/{COMMENT_BATCHES}  before={before}")
        items = get_json(f"{BASE_URL}/comment/", params)
        if not items:
            print("  no more items, stopping")
            break

        for item in items:
            body = clean(item.get("body", ""))
            if is_valid(body):
                rows.append({"text": body, "label": "", "notes": "comment"})

        last_ts = items[-1].get("created_utc")
        if last_ts:
            before = int(last_ts)

        print(f"    got {len(items)} comments — rows so far: {len(rows)}")
        delay()

    return rows


def deduplicate(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["text"] not in seen:
            seen.add(r["text"])
            out.append(r)
    return out


def main():
    print("=" * 60)
    print("TakeMeter — r/soccer scraper (Pullpush API)")
    print("=" * 60)

    post_rows = scrape_posts()
    comment_rows = scrape_comments()

    all_rows = deduplicate(post_rows + comment_rows)

    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary
    total = len(all_rows)
    avg_len = sum(len(r["text"]) for r in all_rows) / total if total else 0
    post_count = sum(1 for r in all_rows if r["notes"] == "post")
    comment_count = sum(1 for r in all_rows if r["notes"] == "comment")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total rows saved : {total}")
    print(f"  From posts       : {post_count}")
    print(f"  From comments    : {comment_count}")
    print(f"  Avg text length  : {avg_len:.0f} chars")
    print(f"  Output file      : {OUTPUT_FILE}")
    if total < TARGET_ROWS:
        print(f"  [warning] below target of {TARGET_ROWS} rows — increase POST_BATCHES or COMMENT_BATCHES")
    else:
        print(f"  [ok] target of {TARGET_ROWS} rows met")
    print("=" * 60)


if __name__ == "__main__":
    main()
