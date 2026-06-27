"""
prelabel.py — TakeMeter AI pre-labeler
Reads raw_data.csv, calls Groq API to suggest labels for unlabeled rows,
and saves progress incrementally.
"""

import csv
import os
import time
import sys
from collections import Counter

from groq import Groq

INPUT_FILE = "raw_data.csv"
MODEL = "llama-3.3-70b-versatile"
BATCH_SAVE_EVERY = 10
API_DELAY = 0.5
MAX_ROWS = 220
VALID_LABELS = {"analysis", "hot_take", "reaction"}

SYSTEM_PROMPT = """You are a soccer discourse classifier. Classify posts into exactly one label.

Labels:
- analysis: structured argument backed by specific stats, tactical observation, or historical comparison. Evidence is specific and verifiable.
- hot_take: bold confident opinion stated without supporting evidence. Asserts rather than argues.
- reaction: immediate emotional response to a specific event. Little to no argument, just expressing a feeling or sharing news.

Rules:
- Output ONLY one word: analysis, hot_take, or reaction
- No explanation, no punctuation, nothing else"""

USER_TEMPLATE = "Post: {text}"


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path: str, rows: list[dict]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)


def classify(client: Groq, text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(text=text)},
        ],
        temperature=0.0,
        max_tokens=10,
    )
    raw = response.choices[0].message.content.strip().lower()
    # Strip any accidental punctuation
    raw = raw.strip(".,!?\"'")
    return raw if raw in VALID_LABELS else "unknown"


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[error] GROQ_API_KEY environment variable not set.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    all_rows = load_csv(INPUT_FILE)
    print(f"Loaded {len(all_rows)} total rows from {INPUT_FILE}")

    # Find first MAX_ROWS rows with empty label
    targets = [i for i, r in enumerate(all_rows) if not r["label"].strip()][:MAX_ROWS]
    print(f"Rows to label: {len(targets)}")
    print("=" * 60)

    labeled = 0
    errors = 0

    for count, idx in enumerate(targets, 1):
        row = all_rows[idx]
        text = row["text"].strip()

        try:
            label = classify(client, text)
            row["label"] = label
            row["notes"] = "AI-prelabeled"
            labeled += 1
        except Exception as e:
            print(f"  [error] row {idx}: {e}")
            row["notes"] = "AI-prelabeled-error"
            errors += 1

        # Progress print + save every BATCH_SAVE_EVERY rows
        if count % BATCH_SAVE_EVERY == 0:
            save_csv(INPUT_FILE, all_rows)
            done_so_far = [all_rows[i] for i in targets[:count]]
            dist = Counter(r["label"] for r in done_so_far if r["label"] in VALID_LABELS)
            print(
                f"[{count}/{len(targets)}] saved — "
                f"analysis={dist.get('analysis', 0)}  "
                f"hot_take={dist.get('hot_take', 0)}  "
                f"reaction={dist.get('reaction', 0)}  "
                f"errors={errors}"
            )

        time.sleep(API_DELAY)

    # Final save
    save_csv(INPUT_FILE, all_rows)

    # Distribution summary
    labeled_rows = [all_rows[i] for i in targets]
    dist = Counter(r["label"] for r in labeled_rows)

    print("\n" + "=" * 60)
    print("LABELING COMPLETE")
    print("=" * 60)
    print(f"  Rows processed : {len(targets)}")
    print(f"  Successfully labeled : {labeled}")
    print(f"  Errors               : {errors}")
    print()
    print("Label distribution:")
    for label in ["analysis", "hot_take", "reaction", "unknown"]:
        count = dist.get(label, 0)
        bar = "█" * (count // 2)
        print(f"  {label:<12} {count:>4}  {bar}")
    print("=" * 60)


if __name__ == "__main__":
    main()
