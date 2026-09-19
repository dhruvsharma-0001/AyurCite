from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., description="User query about classical Ayurvedic literature")
    top_k: int = Field(5, ge=1, le=20, description="Number of verses to retrieve")

class SourceVerse(BaseModel):
    verse_id: str
    book: str
    sthana: str
    chapter: int
    verse: int
    chapter_title: str
    english: str
    rrf_score: float

class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: str  # grounded | partial | refused
    citations: List[str]
    safety_tier: int  # 0, 1, 2
    safety_category: Optional[str] = None
    warning_banner: Optional[str] = None
    sources: List[SourceVerse] = []
    
    # Auditability metadata (plan.md §12)
    corpus_version: str
    model_version: str
    adapter_version: str
    latency_ms: float
    scrubbed_pii: bool = False

class HealthResponse(BaseModel):
    status: str
    corpus_version: str
    model_version: str
    adapter_version: str
    total_verses_indexed: int

class MetricsResponse(BaseModel):
    total_queries: int
    safety_blocks: int
    herb_flags_triggered: int
    refusals: int
    grounded_answers: int
