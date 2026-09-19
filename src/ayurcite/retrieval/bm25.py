import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rank_bm25 import BM25Okapi
from pydantic import BaseModel

from src.ayurcite.config import settings, DATA_DIR
from src.ayurcite.ingest.normalise import strip_accents_iast, expand_query_terms

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

def tokenize(text: str) -> List[str]:
    clean = strip_accents_iast(text.lower())
    tokens = re.findall(r"\b[a-z0-9]+\b", clean)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

class BM25Hit(BaseModel):
    verse_id: str
    score: float
    rank: int
    book: str
    sthana: str
    chapter: int
    verse: int
    chapter_title: str
    english: str
    prev_verse_id: Optional[str] = None
    next_verse_id: Optional[str] = None

class BM25Retriever:
    def __init__(self, verses_path: Optional[Path] = None):
        self.verses_path = verses_path or (DATA_DIR / "processed" / "verses.jsonl")
        self.records: List[dict] = []
        self.verse_id_to_record: Dict[str, dict] = {}
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._load_and_index()

    def _load_and_index(self):
        if not self.verses_path.exists():
            raise FileNotFoundError(f"Verses corpus not found at {self.verses_path}")

        self.records = []
        self.corpus_tokens = []
        with open(self.verses_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    self.records.append(r)
                    self.verse_id_to_record[r["verse_id"]] = r
                    
                    # Tokenize combined title + english + topics + entities
                    searchable_text = f"{r.get('chapter_title', '')} {r.get('english', '')} {' '.join(r.get('topics', []))}"
                    self.corpus_tokens.append(tokenize(searchable_text))

        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query: str, top_k: int = 10, expand_query: bool = True) -> List[BM25Hit]:
        if not self.bm25:
            return []

        tokens = tokenize(query)
        if expand_query:
            expanded = expand_query_terms(query)
            for term in expanded:
                tokens.extend(tokenize(term))

        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        hits = []
        for rank, idx in enumerate(top_indices, 1):
            if scores[idx] <= 0.0:
                break
            r = self.records[idx]
            hits.append(BM25Hit(
                verse_id=r["verse_id"],
                score=float(scores[idx]),
                rank=rank,
                book=r["book"],
                sthana=r["sthana"],
                chapter=r["chapter"],
                verse=r["verse"],
                chapter_title=r.get("chapter_title", ""),
                english=r["english"],
                prev_verse_id=r.get("prev_verse_id"),
                next_verse_id=r.get("next_verse_id")
            ))
        return hits
