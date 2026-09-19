from pydantic import BaseModel

from src.ayurcite.config import settings
from src.ayurcite.retrieval.bm25 import BM25Hit, BM25Retriever
from src.ayurcite.retrieval.dense import DenseHit, DenseRetriever


class FusedHit(BaseModel):
    verse_id: str
    rrf_score: float
    bm25_rank: int | None = None
    dense_rank: int | None = None
    bm25_score: float | None = None
    dense_score: float | None = None
    book: str
    sthana: str
    chapter: int
    verse: int
    chapter_title: str
    english: str
    prev_verse_id: str | None = None
    next_verse_id: str | None = None
    prev_verse_text: str | None = None
    next_verse_text: str | None = None


class HybridSearchResult(BaseModel):
    query: str
    is_refusal: bool = False
    refusal_reason: str | None = None
    max_score: float = 0.0
    hits: list[FusedHit] = []


def reciprocal_rank_fusion(
    dense_hits: list[DenseHit], bm25_hits: list[BM25Hit], k_rrf: int = 60
) -> list[FusedHit]:
    """
    Compute Reciprocal Rank Fusion:
    score(d) = sum_{m in {dense, bm25}} 1 / (k_rrf + rank_m(d))
    """
    scores: dict[str, float] = {}
    verse_map: dict[str, dict] = {}
    dense_ranks: dict[str, int] = {}
    dense_scores: dict[str, float] = {}
    bm25_ranks: dict[str, int] = {}
    bm25_scores: dict[str, float] = {}

    for hit in dense_hits:
        vid = hit.verse_id
        dense_ranks[vid] = hit.rank
        dense_scores[vid] = hit.score
        verse_map[vid] = hit.model_dump()
        scores[vid] = scores.get(vid, 0.0) + (1.0 / (k_rrf + hit.rank))

    for hit in bm25_hits:
        vid = hit.verse_id
        bm25_ranks[vid] = hit.rank
        bm25_scores[vid] = hit.score
        if vid not in verse_map:
            verse_map[vid] = hit.model_dump()
        scores[vid] = scores.get(vid, 0.0) + (1.0 / (k_rrf + hit.rank))

    sorted_vids = sorted(scores.keys(), key=lambda v: scores[v], reverse=True)

    fused_results = []
    for vid in sorted_vids:
        raw_info = verse_map[vid]
        fused_results.append(
            FusedHit(
                verse_id=vid,
                rrf_score=scores[vid],
                bm25_rank=bm25_ranks.get(vid),
                dense_rank=dense_ranks.get(vid),
                bm25_score=bm25_scores.get(vid),
                dense_score=dense_scores.get(vid),
                book=raw_info["book"],
                sthana=raw_info["sthana"],
                chapter=raw_info["chapter"],
                verse=raw_info["verse"],
                chapter_title=raw_info.get("chapter_title", ""),
                english=raw_info["english"],
                prev_verse_id=raw_info.get("prev_verse_id"),
                next_verse_id=raw_info.get("next_verse_id"),
            )
        )

    return fused_results


class HybridRetriever:
    def __init__(
        self,
        bm25_retriever: BM25Retriever | None = None,
        dense_retriever: DenseRetriever | None = None,
        tau: float = 0.012,
    ):
        self.bm25 = bm25_retriever or BM25Retriever()
        self.dense = dense_retriever or DenseRetriever()
        self.tau = tau
        self.verse_id_to_record: dict[str, dict] = self.bm25.verse_id_to_record

    def expand_context(self, hits: list[FusedHit]) -> list[FusedHit]:
        """Attach text of prev_verse and next_verse for context expansion."""
        for hit in hits:
            if hit.prev_verse_id and hit.prev_verse_id in self.verse_id_to_record:
                hit.prev_verse_text = self.verse_id_to_record[hit.prev_verse_id]["english"]
            if hit.next_verse_id and hit.next_verse_id in self.verse_id_to_record:
                hit.next_verse_text = self.verse_id_to_record[hit.next_verse_id]["english"]
        return hits

    def search(self, query: str, top_k: int = 5) -> HybridSearchResult:
        candidates_k = top_k * 3
        bm25_hits = self.bm25.search(query, top_k=candidates_k, expand_query=True)

        dense_hits = []
        if self.dense.is_indexed():
            dense_hits = self.dense.search(query, top_k=candidates_k)

        fused = reciprocal_rank_fusion(dense_hits, bm25_hits, k_rrf=settings.rrf_k)

        if not fused:
            return HybridSearchResult(
                query=query,
                is_refusal=True,
                refusal_reason="not_found_in_corpus",
                max_score=0.0,
                hits=[],
            )

        max_score = fused[0].rrf_score

        # Grounding gate threshold
        if max_score < self.tau:
            return HybridSearchResult(
                query=query,
                is_refusal=True,
                refusal_reason=f"Grounding score {max_score:.4f} is below refusal threshold tau={self.tau:.4f}",
                max_score=max_score,
                hits=self.expand_context(fused[:top_k]),
            )

        return HybridSearchResult(
            query=query,
            is_refusal=False,
            max_score=max_score,
            hits=self.expand_context(fused[:top_k]),
        )
