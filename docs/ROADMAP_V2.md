# AyurCite v2 Roadmap & Explicit Cut List

To preserve engineering focus and ensure rigorous quality gates for v1.0.0, the following capabilities were deliberately deferred to v2. Documenting them here establishes conscious architectural trade-offs rather than omissions.

---

## 1. Native Devanagari & Bilingual Script Retrieval
- **v1 Status**: English translations + Romanized IAST transliterations with diacritic-folding normalizer.
- **v2 Plan**: Add bilingual embedding support and cross-script alignment between original Devanagari Sanskrit verses and English commentary.

## 2. Cross-Encoder Reranking
- **v1 Status**: Reciprocal Rank Fusion (RRF, $k=60$) combining BM25 lexical and dense cosine ranking.
- **v2 Plan**: Optional cross-encoder reranker (e.g. `bge-reranker-large`). Kept off by default in v1 to preserve the <10ms CPU latency budget.

## 3. Knowledge Graph Integration (AyurKOSH Style)
- **v1 Status**: Entity tagging (herbs, conditions, topics) in `VerseRecord`.
- **v2 Plan**: Full property graph linking herbs to phytochemicals (IMPPAT), doshic qualities (*rasa*, *guna*, *virya*, *vipaka*), and ICD-11/NAMASTE morbidity codes.

## 4. Multi-Turn Conversation
- **v1 Status**: Single-turn, stateless query-response.
- **v2 Plan**: History-aware conversation session with context carryover, while preserving the strict 0% hallucination citation gate across turns.

## 5. Agentic Multi-Hop Retrieval
- **v1 Status**: Single-hop hybrid retrieval with [prev, hit, next] context window expansion.
- **v2 Plan**: Decomposition of complex comparative queries into sub-queries across both compendia.

## 6. User Accounts & Personalization
- **v1 Status**: Explicitly excluded.
- **Rationale**: Personalization in health-adjacent software introduces severe diagnostic and liability risks. AyurCite strictly remains an objective classical literature retrieval tool.
