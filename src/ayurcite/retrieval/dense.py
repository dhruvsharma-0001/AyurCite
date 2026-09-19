from pathlib import Path

try:
    import lancedb
except ImportError:
    lancedb = None

from pydantic import BaseModel

from src.ayurcite.config import DATA_DIR
from src.ayurcite.retrieval.embed import Embedder


class DenseHit(BaseModel):
    verse_id: str
    score: float
    rank: int
    book: str
    sthana: str
    chapter: int
    verse: int
    chapter_title: str
    english: str
    prev_verse_id: str | None = None
    next_verse_id: str | None = None


class DenseRetriever:
    TABLE_NAME = "ayurveda_verses"

    def __init__(self, db_path: Path | None = None, embedder: Embedder | None = None):
        self.db_path = db_path or (DATA_DIR / "processed" / "lancedb")
        self._embedder = embedder
        self.table = None
        self.db = None
        if lancedb is not None:
            self.db = lancedb.connect(str(self.db_path))
            try:
                tables = self.db.table_names()
            except Exception:
                res = self.db.list_tables()
                tables = getattr(res, "tables", list(res))
            if self.TABLE_NAME in tables:
                self.table = self.db.open_table(self.TABLE_NAME)

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder.get_instance()
        return self._embedder

    def is_indexed(self) -> bool:
        return self.table is not None

    def search(self, query: str, top_k: int = 10) -> list[DenseHit]:
        if self.table is None:
            raise RuntimeError("Dense index not found. Run scripts/06_build_index.py first.")

        query_vec = self.embedder.embed_query(query)
        results = self.table.search(query_vec).metric("cosine").limit(top_k).to_pandas()

        hits = []
        for rank, (_, row) in enumerate(results.iterrows(), 1):
            # cosine distance to similarity score
            score = 1.0 - float(row.get("_distance", 0.0))
            hits.append(
                DenseHit(
                    verse_id=str(row["verse_id"]),
                    score=score,
                    rank=rank,
                    book=str(row["book"]),
                    sthana=str(row["sthana"]),
                    chapter=int(row["chapter"]),
                    verse=int(row["verse"]),
                    chapter_title=str(row["chapter_title"]),
                    english=str(row["english"]),
                    prev_verse_id=str(row["prev_verse_id"]) if row.get("prev_verse_id") else None,
                    next_verse_id=str(row["next_verse_id"]) if row.get("next_verse_id") else None,
                )
            )
        return hits
