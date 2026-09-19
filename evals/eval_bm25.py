import json
from pathlib import Path
from src.ayurcite.config import settings, DATA_DIR, EVALS_DIR, PROJECT_ROOT
from src.ayurcite.retrieval.bm25 import BM25Retriever

GOLD_PATH = EVALS_DIR / "gold_qa.jsonl"
RESULTS_DIR = EVALS_DIR / "results"
BASELINES_FILE = RESULTS_DIR / "baselines.json"

def evaluate_b0():
    print("=======================================================")
    print("        AyurCite v1 — Baseline B0 Evaluation (BM25)    ")
    print("=======================================================")

    retriever = BM25Retriever()
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f if line.strip()]

    answerable = [q for q in queries if q["answerable"]]
    unanswerable = [q for q in queries if not q["answerable"]]

    print(f"Total Gold Queries: {len(queries)} (Answerable: {len(answerable)}, Unanswerable: {len(unanswerable)})")

    hits_at_5 = 0
    hits_at_10 = 0
    reciprocal_ranks = []
    category_scores = {}

    for q in answerable:
        qid = q["qid"]
        question = q["question"]
        gold_ids = set(q["gold_verse_ids"])
        cat = q["category"]

        if cat not in category_scores:
            category_scores[cat] = {"total": 0, "r5": 0, "r10": 0}
        category_scores[cat]["total"] += 1

        hits = retriever.search(question, top_k=10, expand_query=True)
        retrieved_ids = [h.verse_id for h in hits]

        # Recall@5
        if any(gid in retrieved_ids[:5] for gid in gold_ids):
            hits_at_5 += 1
            category_scores[cat]["r5"] += 1

        # Recall@10
        if any(gid in retrieved_ids[:10] for gid in gold_ids):
            hits_at_10 += 1
            category_scores[cat]["r10"] += 1

        # MRR@10
        rr = 0.0
        for rank, rid in enumerate(retrieved_ids[:10], 1):
            if rid in gold_ids:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    recall_5 = hits_at_5 / len(answerable)
    recall_10 = hits_at_10 / len(answerable)
    mrr_10 = sum(reciprocal_ranks) / len(answerable)

    print(f"\n--- Baseline B0 (BM25 Only) Results ---")
    print(f"Recall@5:  {recall_5:.4f} ({hits_at_5}/{len(answerable)})")
    print(f"Recall@10: {recall_10:.4f} ({hits_at_10}/{len(answerable)})")
    print(f"MRR@10:    {mrr_10:.4f}")

    print("\n--- Per-Category Recall Breakdown ---")
    for cat, data in category_scores.items():
        tot = data["total"]
        r10 = data["r10"] / tot if tot else 0
        print(f"{cat.capitalize():15s}: Recall@10 = {r10:.2f} ({data['r10']}/{tot})")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    baselines = {}
    if BASELINES_FILE.exists():
        with open(BASELINES_FILE, "r", encoding="utf-8") as f:
            try:
                baselines = json.load(f)
            except Exception:
                baselines = {}

    baselines["B0_BM25_only"] = {
        "description": "BM25 lexical retrieval only with NAMC query expansion, no LLM",
        "num_answerable": len(answerable),
        "recall_at_5": round(recall_5, 4),
        "recall_at_10": round(recall_10, 4),
        "mrr_at_10": round(mrr_10, 4),
        "category_breakdown": {
            cat: {
                "recall_at_10": round(d["r10"] / d["total"], 4) if d["total"] else 0,
                "hits_at_10": d["r10"],
                "total": d["total"]
            }
            for cat, d in category_scores.items()
        }
    }

    with open(BASELINES_FILE, "w", encoding="utf-8") as f:
        json.dump(baselines, f, indent=2)

    print(f"\n✅ Results saved to {BASELINES_FILE.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    evaluate_b0()
