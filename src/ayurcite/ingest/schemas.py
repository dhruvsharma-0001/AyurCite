from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class VerseRecord(BaseModel):
    verse_id: str = Field(..., description="Unique ID: <book>_<sthana>_<chapter>_<verse>, e.g. cs_su_01_015")
    book: str = Field(..., description="Compendium name, e.g. Charaka Samhita")
    sthana: str = Field(..., description="Section name, e.g. Sutrasthana")
    chapter: int = Field(..., description="Chapter number")
    chapter_title: str = Field("", description="Title of chapter")
    verse: int = Field(..., description="Verse number within chapter")
    sanskrit_iast: str = Field("", description="Romanized Sanskrit transliteration in IAST")
    sanskrit_devanagari: Optional[str] = Field(None, description="Devanagari script if available")
    english: str = Field(..., description="English translation")
    translator: str = Field(..., description="Translator or edition editor")
    edition_year: int = Field(..., description="Year published")
    doc_id: str = Field(..., description="Foreign key to license_ledger.csv")
    topics: List[str] = Field(default_factory=list, description="Normalized NAMC topic tags")
    entities: Dict[str, List[str]] = Field(
        default_factory=lambda: {"herbs": [], "conditions": []},
        description="Extracted herbs and conditions"
    )
    prev_verse_id: Optional[str] = Field(None, description="Previous verse ID for context window expansion")
    next_verse_id: Optional[str] = Field(None, description="Next verse ID for context window expansion")
