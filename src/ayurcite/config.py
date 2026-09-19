from pathlib import Path
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
EVALS_DIR = PROJECT_ROOT / "evals"

class Settings(BaseModel):
    # Model & Serving
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "gemma2:2b"
    corpus_version: str = "v1.0.0"
    model_version: str = "gemma2:2b-base"
    adapter_version: str = "none"

    # Retrieval
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 5
    rrf_k: int = 60
    grounding_tau: float = 0.010

    # Paths
    lance_db_path: Path = DATA_DIR / "processed" / "lancedb"
    herb_flags_path: Path = DATA_DIR / "safety" / "herb_flags.csv"
    license_ledger_path: Path = DATA_DIR / "license_ledger.csv"
    gold_qa_path: Path = EVALS_DIR / "gold_qa.jsonl"
    adversarial_path: Path = EVALS_DIR / "adversarial.jsonl"

settings = Settings()
