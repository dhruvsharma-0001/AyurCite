import json
import random
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VERSES_PATH = DATA_DIR / "processed" / "verses.jsonl"
LEDGER_PATH = DATA_DIR / "license_ledger.csv"

def run_qa_gates():
    print("\n=======================================================")
    print("      AyurCite v1 — Corpus Quality Gates (Phase 2)    ")
    print("=======================================================")

    if not VERSES_PATH.exists():
        print(f"❌ FAIL: Processed verses file not found: {VERSES_PATH}")
        sys.exit(1)

    if not LEDGER_PATH.exists():
        print(f"❌ FAIL: License ledger file not found: {LEDGER_PATH}")
        sys.exit(1)

    # 1. Load license ledger
    ledger_df = pd.read_csv(LEDGER_PATH)
    valid_doc_ids = set(ledger_df[ledger_df["included_in_corpus"] == True]["doc_id"])
    print(f"✅ Loaded {len(ledger_df)} ledger entries. Approved corpus doc_ids: {valid_doc_ids}")

    # 2. Read verses
    records = []
    with open(VERSES_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"❌ FAIL: Invalid JSON on line {line_num}: {e}")
                    sys.exit(1)

    total_verses = len(records)
    print(f"✅ Read {total_verses:,} verses from {VERSES_PATH.name}")

    # Gate 1: No duplicate verse_ids
    seen_ids = set()
    duplicates = []
    for r in records:
        vid = r.get("verse_id")
        if vid in seen_ids:
            duplicates.append(vid)
        seen_ids.add(vid)

    if duplicates:
        print(f"❌ FAIL: Gate 1 violated — Found {len(duplicates)} duplicate verse_ids: {duplicates[:10]}")
        sys.exit(1)
    else:
        print(f"✅ Gate 1 PASSED: All {total_verses:,} verse_ids are strictly unique.")

    # Gate 2: Length bounds (5 <= words <= 400)
    under_5 = []
    over_400 = []
    word_counts = []

    for r in records:
        words = len(r.get("english", "").split())
        word_counts.append(words)
        vid = r.get("verse_id")
        if words < 5:
            under_5.append((vid, words))
        if words > 400:
            over_400.append((vid, words))

    if under_5:
        print(f"❌ FAIL: Gate 2 violated — {len(under_5)} verses under 5 words: {under_5[:5]}")
        sys.exit(1)
    if over_400:
        print(f"❌ FAIL: Gate 2 violated — {len(over_400)} verses over 400 words: {over_400[:5]}")
        sys.exit(1)

    avg_words = sum(word_counts) / len(word_counts)
    print(f"✅ Gate 2 PASSED: Length bounds respected (Min: {min(word_counts)}, Max: {max(word_counts)}, Mean: {avg_words:.1f} words).")

    # Gate 3: Foreign Key integrity with license_ledger
    unauthorized_docs = []
    for r in records:
        doc_id = r.get("doc_id")
        if doc_id not in valid_doc_ids:
            unauthorized_docs.append((r.get("verse_id"), doc_id))

    if unauthorized_docs:
        print(f"❌ FAIL: Gate 3 violated — Unauthorized doc_ids found: {unauthorized_docs[:5]}")
        sys.exit(1)
    else:
        print("✅ Gate 3 PASSED: Every verse resolves to an approved public domain license_ledger row.")

    # Gate 4: Near-duplicate check on verse text
    text_hashes = set()
    exact_text_dups = 0
    for r in records:
        t_clean = " ".join(r.get("english", "").lower().split())
        h = hash(t_clean)
        if h in text_hashes:
            exact_text_dups += 1
        text_hashes.add(h)

    dup_rate = (exact_text_dups / total_verses) * 100.0
    if dup_rate > 2.0:
        print(f"❌ FAIL: Gate 4 violated — High text redundancy rate: {dup_rate:.2f}%")
        sys.exit(1)
    else:
        print(f"✅ Gate 4 PASSED: Text redundancy within acceptable bounds ({dup_rate:.2f}% duplicates).")

    # Gate 5: Random sample spot check
    print("\n--- Spot Check: 3 Random Sample Verses ---")
    samples = random.sample(records, 3)
    for s in samples:
        print(f"\nID: {s['verse_id']} | {s['book']} ({s['sthana']} Ch.{s['chapter']})")
        print(f"Title: {s['chapter_title']}")
        print(f"Text snippet: {s['english'][:180]}...")
        print(f"Topics: {s['topics']} | Entities: {s['entities']}")

    print("\n=======================================================")
    print("      🎉 ALL QUALITY GATES PASSED SUCCESSFULLY!       ")
    print("=======================================================\n")

if __name__ == "__main__":
    run_qa_gates()
