# AyurCite Evaluation Methodology & Baselines

AyurCite prioritizes empirical evaluation over arbitrary generation. Every claim is validated against real baselines and a hand-curated gold standard.

---

## 1. Evaluation Datasets

### A. Gold Evaluation Set (`evals/gold_qa.jsonl`)
Contains 70 questions curated before building the retrieval engine:
- **Conceptual (20 questions)**: Direct questions on core Ayurvedic doctrine with answers residing in 1–3 specific verses.
- **Locational (15 questions)**: Queries asking where specific treatises or chapters discuss a practice (e.g. *Dinacharya*, *Ritucharya*).
- **Herb Properties (15 questions)**: Rasa, Virya, Vipaka, and Karma inquiries for primary medicinal plants.
- **Comparative (10 questions)**: Inquiries comparing Charaka and Sushruta definitions (e.g., definition of health, Rakta dosha).
- **Unanswerable (10 questions)**: Plausible but ahistorical queries (e.g. COVID-19, DNA sequencing, chemotherapy) where the system **must refuse**.

### B. Adversarial Safety Set (`evals/adversarial.jsonl`)
40 adversarial queries designed to provoke unsafe medical behavior (severe chest pain, home cancer cures, medication cessation, infant dosing, toxic mercury bhasma preparations).

---

## 2. Baselines Evaluated

1. **B0: BM25 Only (No LLM)**: Returns top-ranked verses raw. Represents the lexical retrieval floor.
2. **B1: Base LLM, Zero-Shot (No RAG)**: Measures hallucination rate without contextual grounding.
3. **B2: Base LLM, Few-Shot (No RAG)**: Tests whether prompt formatting alone stops factual hallucination.
4. **B3: Dense Only + Base LLM**: Dense semantic retrieval without lexical matching.
5. **AyurCite v1**: Hybrid BM25 + Dense + RRF + Grounding Gate + Context Expansion + Citation Validator.

---

## 3. Metrics

- **Recall@5 & Recall@10**: Fraction of answerable gold questions where at least one gold verse ID appears in the top $k$ retrieved verses.
- **MRR@10**: Mean Reciprocal Rank of the first relevant gold verse.
- **True Refusal Rate**: Percentage of unanswerable queries correctly refused.
- **Groundedness Rate**: Character n-gram overlap and semantic entailment between generated sentences and cited verses.
- **Hallucinated Citation Rate**: Percentage of citations emitted by the LLM that do NOT exist in the retrieved context set (**Gate: exactly 0.0%**).
- **Tier-0 Safety Catch Rate**: Percentage of dangerous queries blocked pre-retrieval (**Gate: 100.0%**).
