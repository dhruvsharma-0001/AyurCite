# AyurCite v1 — Scope Lock & Kill Criteria

## 1. Product Scope

### In Scope
A local FastAPI service + minimal web UI where a user asks a natural-language question and gets back:
- **ANSWER** (3–6 sentences, every claim traceable)
  - Inline citations → `[cs_su_01_015]`
  - **SOURCES** panel: verse ID, Sanskrit/IAST, English, book/sthana/chapter/verse
  - **CONFIDENCE**: `grounded` | `partial` | `refused`
  - **SAFETY BANNER** (when triggered)

#### Query Classes Handled:
1. **Conceptual**: e.g., *"What are the three doshas and where are they defined?"*
2. **Textual / Locational**: e.g., *"Which chapter covers dinacharya?"*
3. **Herb Properties**: e.g., *"What rasa and virya does Haritaki have according to the texts?"*
4. **Comparative**: e.g., *"How do Charaka and Sushruta differ on the definition of health?"*

---

### Out of Scope (Hard Non-Negotiables)
- **Not a diagnostic tool**: No symptom check to disease diagnosis.
- **Not a prescribing tool**: No therapeutic claims or recommendations.
- **No personalised dosage, ever**: Classical dosages may only be quoted as descriptive text facts, never as "you should take X".
- **No emergency, pregnancy, pediatric, oncology, or psychiatric handling**: Hard-refused via Tier-0 safety router before any retrieval or LLM call.
- **No Rasa Shastra / bhasma (heavy-metal / mineral preparations)**: Hard-refused completely.
- **No "replace your medication" advice**: Hard-refused.

---

## 2. Non-Negotiable Output Rule
> Every factual sentence in an answer must either:
> 1. Carry a citation `[verse_id]` to a verse present in the current retrieved context set, or
> 2. Be a framing/hedging sentence that makes no factual claim.
> 
> **Hallucinated citation rate must be exactly 0.0%.**

---

## 3. Kill Criteria

1. **Corpus Segmentation & Retrieval Quality**:
   - If after Phase 4, hybrid retrieval **Recall@10** on the gold evaluation set is **below 0.70**, the corpus segmentation is defective.
   - **Action**: Stop immediately. Re-segment and fix Phase 2. Do not proceed to fine-tuning.

2. **Complexity vs Simplicity**:
   - If plain **BM25 alone** scores within 5 points of the full hybrid dense-lexical pipeline, ship BM25 and write that up honestly. A simple, working baseline is better than unnecessary complexity.

---

## 4. Definition of Done (v1.0.0)

- [ ] `git clone` → `docker compose up` works out-of-the-box locally (CPU/MPS, no GPU, no required external API key).
- [ ] Hallucinated citation rate: **0%** on the full gold evaluation set.
- [ ] Tier-0 safety catch rate: **100%** on the adversarial evaluation set.
- [ ] Recall@10 ≥ **0.70**, and pipeline demonstrably outperforms all four baselines (or documents why).
- [ ] Corpus fully reproducible from `scripts/` and `data/manifest.json`; zero redistributed copyrighted text.
- [ ] Green CI gate, tagged release `v1.0.0`, complete `MODEL_CARD.md` and `DATASET_CARD.md`.
