import time
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.ayurcite.config import settings, DATA_DIR
from src.ayurcite.safety.scrub import scrub_pii
from src.ayurcite.safety.router import SafetyRouter
from src.ayurcite.retrieval.bm25 import BM25Retriever
from src.ayurcite.retrieval.dense import DenseRetriever
from src.ayurcite.retrieval.hybrid import HybridRetriever
from src.ayurcite.generate.llm import LLMGenerator
from src.ayurcite.api.schemas import (
    QueryRequest, QueryResponse, SourceVerse, HealthResponse, MetricsResponse
)

app = FastAPI(
    title="AyurCite API",
    description="Precision, citation-grounded Q&A over public-domain classical Ayurvedic literature",
    version=settings.corpus_version
)

# Global instances (initialized on startup)
safety_router: Optional[SafetyRouter] = None
hybrid_retriever: Optional[HybridRetriever] = None
llm_generator: Optional[LLMGenerator] = None

# In-memory metrics
metrics_data = {
    "total_queries": 0,
    "safety_blocks": 0,
    "herb_flags_triggered": 0,
    "refusals": 0,
    "grounded_answers": 0
}

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
def startup_event():
    global safety_router, hybrid_retriever, llm_generator
    print("[API] Initializing AyurCite service...")
    safety_router = SafetyRouter()
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    hybrid_retriever = HybridRetriever(bm25_retriever=bm25, dense_retriever=dense, tau=settings.grounding_tau)
    llm_generator = LLMGenerator()
    print("[API] All engines initialized.")

@app.get("/health", response_model=HealthResponse)
def health():
    total_verses = len(hybrid_retriever.bm25.records) if hybrid_retriever else 0
    return HealthResponse(
        status="healthy",
        corpus_version=settings.corpus_version,
        model_version=settings.model_version,
        adapter_version=settings.adapter_version,
        total_verses_indexed=total_verses
    )

@app.get("/metrics", response_model=MetricsResponse)
def metrics():
    return MetricsResponse(**metrics_data)

@app.get("/verse/{verse_id}")
def get_verse(verse_id: str):
    if not hybrid_retriever or verse_id not in hybrid_retriever.verse_id_to_record:
        raise HTTPException(status_code=404, detail=f"Verse {verse_id} not found in corpus.")
    return hybrid_retriever.verse_id_to_record[verse_id]

@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    t0 = time.perf_counter()
    metrics_data["total_queries"] += 1

    # 1. PII Scrubbing
    scrubbed_query, had_pii = scrub_pii(req.question)

    # 2. Safety Router Check (Pre-retrieval)
    safety_decision = safety_router.route(scrubbed_query)
    if not safety_decision.allowed:
        metrics_data["safety_blocks"] += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return QueryResponse(
            question=scrubbed_query,
            answer=safety_decision.refusal_message or "Query blocked by Tier-0 safety policy.",
            confidence="refused",
            citations=[],
            safety_tier=0,
            safety_category=safety_decision.category,
            warning_banner=None,
            sources=[],
            corpus_version=settings.corpus_version,
            model_version=settings.model_version,
            adapter_version=settings.adapter_version,
            latency_ms=round(elapsed_ms, 2),
            scrubbed_pii=had_pii
        )

    warning_banner = safety_decision.warning_banner
    if safety_decision.tier == 1:
        metrics_data["herb_flags_triggered"] += 1

    # 3. Hybrid Retrieval
    retrieval_result = hybrid_retriever.search(scrubbed_query, top_k=req.top_k)

    if retrieval_result.is_refusal:
        metrics_data["refusals"] += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return QueryResponse(
            question=scrubbed_query,
            answer=(
                "The classical compendia (Charaka & Sushruta Samhitas) in the corpus do not contain "
                "sufficiently grounded verses to answer this query. AyurCite strictly refuses ungrounded extrapolation."
            ),
            confidence="refused",
            citations=[],
            safety_tier=safety_decision.tier,
            safety_category=safety_decision.category,
            warning_banner=warning_banner,
            sources=[],
            corpus_version=settings.corpus_version,
            model_version=settings.model_version,
            adapter_version=settings.adapter_version,
            latency_ms=round(elapsed_ms, 2),
            scrubbed_pii=had_pii
        )

    # 4. Context Preparation & Generation
    verse_dicts = [h.model_dump() for h in retrieval_result.hits]
    gen_result = llm_generator.generate(scrubbed_query, verse_dicts)

    if gen_result.confidence == "grounded":
        metrics_data["grounded_answers"] += 1
    elif gen_result.confidence == "refused":
        metrics_data["refusals"] += 1

    # 5. Format Sources
    sources = [
        SourceVerse(
            verse_id=h.verse_id,
            book=h.book,
            sthana=h.sthana,
            chapter=h.chapter,
            verse=h.verse,
            chapter_title=h.chapter_title,
            english=h.english,
            rrf_score=round(h.rrf_score, 4)
        )
        for h in retrieval_result.hits
    ]

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return QueryResponse(
        question=scrubbed_query,
        answer=gen_result.answer,
        confidence=gen_result.confidence,
        citations=gen_result.extracted_citations,
        safety_tier=safety_decision.tier,
        safety_category=safety_decision.category,
        warning_banner=warning_banner,
        sources=sources,
        corpus_version=settings.corpus_version,
        model_version=settings.model_version,
        adapter_version=settings.adapter_version,
        latency_ms=round(elapsed_ms, 2),
        scrubbed_pii=had_pii
    )

# Mount static files and root UI
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "AyurCite v1 Service Running. UI index.html not yet installed."}
