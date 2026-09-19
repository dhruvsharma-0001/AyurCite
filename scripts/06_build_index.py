import json
import time

import lancedb
from tqdm import tqdm

from src.ayurcite.config import DATA_DIR, PROJECT_ROOT
from src.ayurcite.retrieval.dense import DenseRetriever
from src.ayurcite.retrieval.embed import Embedder

VERSES_PATH = DATA_DIR / "processed" / "verses.jsonl"
LANCEDB_DIR = DATA_DIR / "processed" / "lancedb"


def build_dense_index():
    print("=======================================================")
    print("       AyurCite v1 — Building Dense Vector Index       ")
    print("=======================================================")

    if not VERSES_PATH.exists():
        raise FileNotFoundError(f"Verses file not found at {VERSES_PATH}")

    LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
    embedder = Embedder.get_instance()

    records = []
    with open(VERSES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    total = len(records)
    print(f"[Index] Loaded {total:,} verses to embed.")

    # Prepare texts for embedding
    texts_to_embed = [
        f"{r.get('chapter_title', '')}: {r['english']} {' '.join(r.get('topics', []))}"
        for r in records
    ]

    print("[Index] Computing dense embeddings (batch size 128)...")
    t0 = time.perf_counter()
    batch_size = 128
    all_vectors = []
    for i in tqdm(range(0, total, batch_size), desc="Embedding"):
        batch_texts = texts_to_embed[i : i + batch_size]
        vecs = embedder.embed_texts(batch_texts, batch_size=len(batch_texts))
        all_vectors.extend(vecs)
    dur = time.perf_counter() - t0
    print(f"[Index] Embedding completed in {dur:.2f}s ({total / dur:.1f} verses/sec).")

    # Connect to LanceDB
    db = lancedb.connect(str(LANCEDB_DIR))

    # Format data records
    data_rows = []
    for r, vec in zip(records, all_vectors):
        data_rows.append(
            {
                "verse_id": r["verse_id"],
                "vector": vec,
                "book": r["book"],
                "sthana": r["sthana"],
                "chapter": r["chapter"],
                "verse": r["verse"],
                "chapter_title": r.get("chapter_title", ""),
                "english": r["english"],
                "prev_verse_id": r.get("prev_verse_id") or "",
                "next_verse_id": r.get("next_verse_id") or "",
            }
        )

    print(f"[Index] Writing LanceDB table '{DenseRetriever.TABLE_NAME}'...")
    db.create_table(
        DenseRetriever.TABLE_NAME,
        data=data_rows,
        mode="overwrite",
    )
    print(f"✅ Dense vector index built successfully at {LANCEDB_DIR.relative_to(PROJECT_ROOT)}!")


if __name__ == "__main__":
    build_dense_index()
