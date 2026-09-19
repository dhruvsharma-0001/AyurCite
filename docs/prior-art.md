# Prior Art Analysis: Ayurvedic NLP & Domain-Specific AI

Before writing code for AyurCite, we reviewed existing projects and literature in the Ayurvedic informatics space to identify solved problems and key gaps.

---

## 1. AyurParam (arXiv: 2511.02374)

- **What it is**: A bilingual foundational language model fine-tuned for Ayurveda in Hindi and English.
- **Key Contribution**: §3.2 corpus collection and licensing methodology. AyurParam established the rigorous standard of maintaining a license ledger and separating public-domain texts from copyrighted modern editions.
- **How AyurCite differs**: AyurParam focuses on general model pretraining/fine-tuning. AyurCite is an applied, production-ready citation-grounded RAG architecture with sub-millisecond safety routing, zero hallucinated citation enforcement, and offline Apple Silicon execution.

---

## 2. Charaka-AI (github.com/Madhu-204/Charaka-AI)

- **What it is**: An agentic RAG system querying Charaka Samhita using LangChain with verse IDs and emergency short-circuiting.
- **Key Contribution**: Demonstrated the utility of verse-traceable citations over raw page chunks.
- **How AyurCite differs**:
  - Eliminates heavy agentic overhead in the serving path for deterministic sub-second latency.
  - Implements Reciprocal Rank Fusion (RRF) combining dense embeddings with BM25 lexical search (crucial for exact IAST transliteration matches).
  - Hard deterministic validator rejecting 100% of second-person prescriptive instructions and hallucinated citations.
  - Comprehensive empirical eval harness with 70 gold Q&A items, 40 adversarial queries, and documented baselines.

---

## 3. AyurKOSH (IEEE DataPort)

- **What it is**: A structured Ayurvedic knowledge graph linking diseases, symptoms, formulations, and Ayurvedic pharmacological properties (*Rasa*, *Guna*, *Virya*, *Vipaka*, *Karma*).
- **How AyurCite uses it**: Provides reference taxonomies for normalizing classical Ayurvedic concepts in our NAMC translation dictionary.

---

## 4. IMPPAT 2.0 (cb.imsc.res.in/imppat)

- **What it is**: Indian Medicinal Plants, Phytochemistry And Therapeutics — a curated database linking Indian medicinal plants to phytochemicals and therapeutic uses.
- **How AyurCite uses it**: Serves as the botanical taxonomy backbone for resolving common vernacular plant names ("Harad", "Haritaki") to scientific binomials (*Terminalia chebula*).
