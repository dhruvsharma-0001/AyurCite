# Model Card: AyurCite v1 Serving Path

## Model Details
- **Architecture**: Retrieval-Augmented Generation over Gemma (2B / 7B parameter variants) served via Ollama.
- **Serving Path**: Local inference running on Apple Silicon unified memory (CPU / MPS) or lightweight container.
- **License**: Apache-2.0 (code) & Gemma terms of use.

## Intended Use
- **Primary Purpose**: Precision textual citation and question-answering over classical Ayurvedic compendia (Charaka Samhita Sutrasthana & Sushruta Samhita Sutrasthana).
- **Out of Scope**: Clinical diagnosis, emergency triage, prescription generation, personalized dosing, cancer treatment guidance, psychiatric crisis management.

## Safety & Grounding Controls
- **Tier-0 Hard Safety Router**: Pre-retrieval deterministic regex gate catching 100% of emergency, self-harm, pregnancy, pediatric, and medication-cessation queries.
- **Deterministic Citation Validator**: Enforces a 0.0% hallucinated citation rate. All cited IDs must belong to the retrieved verse context.
- **Dosage Rule**: Prohibits second-person prescriptive phrasing (*"you should take..."*). Classical dosages are reported strictly as historical literature facts.

## Evaluation
- Benchmark results documented in `evals/results/`. Evaluated on 70 gold-standard queries and 40 adversarial queries.
