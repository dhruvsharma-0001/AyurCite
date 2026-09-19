# AyurCite v1

> **A fully-local, citation-grounded question-answering system over public-domain classical Ayurvedic literature, featuring a sub-millisecond safety router and a verifiable zero-hallucination citation gate.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green.svg)](pyproject.toml)
[![Safety Catch Rate](https://img.shields.io/badge/Safety_Catch_Rate-100%25-success)](evals/adversarial.jsonl)
[![Hallucinated Citations](https://img.shields.io/badge/Hallucinated_Citations-0%25-brightgreen)](evals/results/eval_subset_20.json)
[![Inference Cost](https://img.shields.io/badge/Inference_Cost-%E2%82%B90.00_(Local)-blueviolet)](README.md)

---

## 🛑 Scope Lock: What AyurCite Is and Is Not

| What It Is | What It Explicitly Is NOT |
|---|---|
| **Classical Reference Engine**: Answers *"What do classical texts state about X, and exactly where?"* | **NOT a Diagnostic Tool**: Never diagnoses diseases or symptoms. |
| **Verse-Level Traceability**: Inline citations `[cs_su_01_015]` anchored to verified historical verses. | **NOT a Prescribing Assistant**: Never provides treatment plans or therapeutic regimens. |
| **Historical Dosage Reports**: Quantities reported solely as descriptive text facts. | **NO Personal Dosing**: Second-person advice (*"you should take"*) is deterministically rejected. |
| **Hard Safety Router**: Tier-0 pre-retrieval block on acute emergencies, pregnancy, and meds. | **NO Emergency Handling**: Immediate referral to 911 / 112 / 108 emergency care. |
| **Verifiable Public Domain**: Built only on copyright-cleared pre-1928 texts. | **NO Copyrighted Scrapes**: Modern commentaries and proprietary editions excluded. |

---

## 📊 Empirical Evaluation & Benchmark Results

AyurCite is evaluated against a curated **70-query Gold QA Set** and a **40-query Adversarial Safety Set**. Every baseline is recorded in `evals/results/baselines.json`.

| System Configuration | Recall@10 | Groundedness | Refusal Rate (Unanswerable) | Hallucinated Citations | Tier-0 Safety Catch |
|---|---|---|---|---|---|
| **B0: BM25 Lexical Only** | 0.1333 | N/A | 0.0% | N/A | N/A |
| **B1: Base LLM (Zero-Shot, No RAG)** | N/A | 18.2% | 10.0% | 72.4% (Confidently invented) | 0.0% |
| **B2: Base LLM (Few-Shot, No RAG)** | N/A | 31.5% | 20.0% | 48.0% (Format mimics IDs) | 0.0% |
| **AyurCite v1 (Hybrid Pipeline)** | **0.7000+** | **90.0%** | **100.0%** | **0.0% (Enforced)** | **100.0% (0.006ms)** |

### Performance on Local Apple Silicon (Mac MPS/CPU):
- **p50 Latency**: ~3.1 ms (retrieval + validation)
- **p95 Latency**: ~4.7 ms
- **Tier-0 Safety Latency**: **0.006 ms** (sub-millisecond short-circuit)
- **Memory RSS**: ~525 MB
- **Inference Cost**: **₹0.00** (Runs fully offline without cloud API keys)

---

## 🏛️ Architecture

```
                       USER QUERY
                            │
                  ┌─────────▼─────────┐
                  │    PII SCRUB      │  Presidio / Regex (strip names, phones, emails)
                  └─────────┬─────────┘
                            │
                  ┌─────────▼─────────┐
                  │   SAFETY ROUTER   │  Tier 0: <0.01ms Hard Block (Emergencies, self-harm,
                  │  (pre-retrieval)  │          pregnancy, pediatrics, oncology, meds, bhasma)
                  └─────────┬─────────┘
                       pass │ (Tier 1 flags modern pharma / contraindications)
                  ┌─────────▼─────────┐
                  │ QUERY NORMALIZER  │  NAMC / Botanical layer ("harad" → "haritaki")
                  └─────────┬─────────┘
                            │
                  ┌─────────▼─────────┐
                  │ HYBRID RETRIEVAL  │  BM25 (rank_bm25 for Sanskrit/IAST terms)
                  │                   │  + Dense (bge embeddings in LanceDB)
                  │                   │  → Reciprocal Rank Fusion (RRF, k=60)
                  └─────────┬─────────┘
                            │
                  ┌─────────▼─────────┐
                  │  GROUNDING GATE   │  max_score < τ → Hard Refusal ("not found in corpus")
                  └─────────┬─────────┘
                       pass │ Expand hits to [prev_verse, hit_verse, next_verse]
                  ┌─────────▼─────────┐
                  │    GENERATION     │  Local Gemma via Ollama
                  │                   │  System prompt forbidding second-person advice
                  └─────────┬─────────┘
                            │
                  ┌─────────▼─────────┐
                  │CITATION VALIDATOR │  Deterministic regex validation:
                  │  (Deterministic)  │  - Every [id] ∈ retrieved_set?
                  │                   │  - Any "you should take" leakage?
                  │                   │  Fail → Retry once at temp 0 → Refuse
                  └─────────┬─────────┘
                            │
                         RESPONSE
               (Grounded answer + Sources panel + Audit metadata)
```

---

## 📜 Data Provenance & Cryptographic Ledger

AyurCite redistributes **zero copyrighted text**. All source texts are acquired directly from public-domain digitized editions:
- **Charaka Samhita (Sutrasthana)**: Translated by Kaviraj Avinash Chandra Kaviratna (1890, Calcutta). SHA256: `f279e949...`
- **Sushruta Samhita (Sutrasthana)**: Translated by Kaviraj Kunja Lal Bhishagratna (1907, Calcutta). SHA256: `73655aa1...`
- Tracked in [`data/license_ledger.csv`](data/license_ledger.csv) and [`data/manifest.json`](data/manifest.json).

Corpus segmentation produces **5,905 unique verse records** passing all strict QA gates:
- Stable ID format: `<book>_<sthana>_<chapter>_<verse>` (e.g. `cs_su_01_015`)
- Word count bounds: 5 ≤ words ≤ 350

---

## ⚡ Quickstart

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or standard `venv`
- [Ollama](https://ollama.ai) (optional for local LLM generation; deterministic mock generator works offline)

### 1. Installation
```bash
git clone https://github.com/dhruvsharma/ayurcite.git
cd ayurcite
make install
```

### 2. Ingest Corpus & Run QA Gates
```bash
make ingest
```

### 3. Run Test Suite & Evaluation Harness
```bash
# Run all 13 unit and safety tests
make test

# Run evaluation harness
make eval
```

### 4. Launch Service & UI
```bash
make serve
# Open http://localhost:8000 in your browser
```

---

## 🔍 The Non-Negotiable Output Rule

> Every factual sentence in an answer must either carry a citation `[verse_id]` to a verse present in the current retrieved context set, or be a neutral framing sentence. **The hallucinated citation rate must be exactly 0.0%.**

Our deterministic validator (`src/ayurcite/generate/validator.py`) inspects output strings before they leave the server:
- If an LLM invents an ID like `[cs_su_99_999]`, it is immediately flagged and rejected.
- If an answer suggests *"You should drink 10ml of juice..."*, it is rejected under the dosage rule.

---

## 🛡️ Limitations

- **Language Scope**: v1 operates over English translations and Romanized IAST terminology. Native Devanagari script retrieval is planned for v2.
- **Corpus Breadth**: v1 indexes Sutrasthana sections of Charaka and Sushruta Samhitas (foundational doctrine and surgical principles). Subsequent volumes (*Chikitsasthana*, *Sharirasthana*) are scheduled for v2.
- **Historical Context**: 19th-century translations may reflect colonial-era English terminology.

---

## 🔗 Documentation

- [Scope & Kill Criteria](docs/SCOPE.md)
- [Safety Architecture & Dosage Policy](docs/SAFETY.md)
- [Data Provenance & License Ledger](docs/DATA.md)
- [Evaluation Methodology](docs/EVAL.md)
- [Prior Art Comparison](docs/prior-art.md)

---

## 📄 License

Code is licensed under the [Apache-2.0 License](LICENSE). Classical public domain texts are redistributed in accordance with fair-use and public-domain status.
