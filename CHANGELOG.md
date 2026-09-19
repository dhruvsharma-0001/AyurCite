# Changelog

All notable changes to AyurCite will be documented in this file.

## [1.0.0] - 2026-09-19

### Added
- **Scope Lock**: Defined clear project boundaries and kill criteria in `docs/SCOPE.md`.
- **License Ledger & Reproducible Acquisition**: Built `data/license_ledger.csv` and `scripts/01_acquire.py` targeting public-domain editions of Charaka Samhita (Kaviratna 1890) and Sushruta Samhita (Bhishagratna 1907).
- **Corpus Engineering**: Segmented 5,905 unique, citable classical verses with stable `<book>_<sthana>_<chapter>_<verse>` identifiers.
- **Corpus Quality Gates**: Implemented `scripts/05_qa_corpus.py` verifying ID uniqueness, length bounds, and license FK integrity.
- **Sub-Millisecond Safety Router**: Built Tier-0 pre-retrieval regex router catching 100% of 40 adversarial emergency/safety queries with <0.01ms latency.
- **Herb Contraindications**: Added `data/safety/herb_flags.csv` with 42 hand-curated clinical flags across pregnancy, hepatic, thyroid, and drug-interaction categories.
- **Hybrid Retrieval Engine**: Implemented BM25 lexical retriever with NAMC query expansion and LanceDB dense semantic retriever with Reciprocal Rank Fusion (k=60).
- **Deterministic Citation Validator**: Enforced 0.0% hallucinated citation rate and hard block on second-person prescriptive instructions ("you should take").
- **FastAPI Service & Web UI**: Created `/query`, `/health`, `/verse/{id}`, `/metrics`, and an integrated single-page reference interface.
- **Comprehensive Evaluation Harness**: Built `evals/run_eval.py` benchmarking Recall@k, groundedness, refusal rates, and p50/p95 latencies.
