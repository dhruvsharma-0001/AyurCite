AyurCite v1 — Full Build Plan
A fully-local, citation-grounded question-answering system over public-domain Ayurvedic classical texts, with a hard safety router and a real eval harness.

From zero data to a tagged v1.0.0 release on GitHub. Written against your private-data roadmap — this project exercises methods #0, #1, #2, #3, #5, #6, #7 from it in one coherent build.

0. Read this before you write a line of code
The three constraints that define the project
Constraint 1 — This is a health domain. Scope is the product.

You are not building a system that tells people what to take. You are building a system that answers "what does the classical literature say about X, and exactly where does it say it" — with verse-level citations and a refusal when it can't ground the answer.

This isn't timidity. It's the only version that is:

legally defensible
technically evaluable (groundedness is measurable; "was this good health advice" is not)
actually sellable — the same architecture drops straight onto legal docs, insurance policy corpora, and compliance manuals
If you find yourself adding a "personalised recommendation" feature, you've left the project.

Constraint 2 — Licensing is the bottleneck, not availability.

Vast amounts of Ayurvedic text are digitised. Most of it is under live copyright (modern translations, commentaries, publisher editions). A 1907 Bhishagratna translation is public domain; a 1998 Chaukhamba edition is not. You will spend real time on a license ledger. Build it as a first-class artifact — it's a portfolio asset in itself and it's what separates you from every scraper repo.

Constraint 3 — Mac, no GPU.

Everything in the serving path must run on Apple Silicon CPU/MPS. Fine-tuning has two viable routes (MLX locally, or a free Colab T4 with the adapter brought back). Both are covered in Phase 6.

Prior art you should read before starting, not after
Thing	Why
AyurParam paper (arXiv 2511.02374)	Bilingual Ayurveda LLM. Their §3.2 corpus-collection + license-ledger methodology is the single best reference for your Phase 1. Copy the ledger schema.
Charaka-AI (github.com/Madhu-204/Charaka-AI)	Existing agentic RAG over Charaka Samhita with verse-traceable IDs and emergency short-circuiting. Read it to see what's already solved, then beat it on evaluation.
AyurKOSH (IEEE DataPort)	Machine-readable Ayurvedic knowledge graph — diseases, symptoms, formulations, and pharmacological properties (Rasa, Guna, Virya, Vipaka, Karma). Potential structured supplement to your text corpus.
IMPPAT 2.0 (cb.imsc.res.in/imppat)	Your herb-properties backbone. Check its reuse terms before ingesting.
Spend one evening on these. Write a docs/prior-art.md with what each does and what yours does differently. That file goes in the repo and it will get you taken seriously.

1. Product spec — what v1 is and is not
Is
A local FastAPI service + minimal web UI where a user asks a natural-language question and gets back:

ANSWER (3-6 sentences, every claim traceable)
  ├─ inline citations → [cs_su_01_015]
  ├─ SOURCES panel: verse ID, Sanskrit/IAST, English, book/sthana/chapter/verse
  ├─ CONFIDENCE: grounded | partial | refused
  └─ SAFETY BANNER (when triggered)
Four query classes it handles:

Conceptual — "What are the three doshas and where are they defined?"
Textual/locational — "Which chapter covers dinacharya?"
Herb properties — "What rasa and virya does Haritaki have according to the texts?"
Comparative — "How do Charaka and Sushruta differ on the definition of health?"
Is not
Not a diagnostic tool
Not a prescribing tool
No personalised dosage, ever
No pregnancy, pediatric, oncology, psychiatric, or emergency handling — hard-refused
No Rasa Shastra / bhasma (heavy-metal preparation) content — hard-refused, entirely
No "replace your medication" reasoning — hard-refused
The one non-negotiable output rule
Every factual sentence in an answer must either (a) carry a citation to a verse present in the current retrieval set, or (b) be a hedge/framing sentence that makes no factual claim. Hallucinated citation rate must be exactly 0%.

This is deterministically checkable. Make it a CI gate. It is the most impressive line in your README.

2. Architecture
                        USER QUERY
                             │
                   ┌─────────▼─────────┐
                   │  PII SCRUB (#7)   │  presidio / spaCy NER
                   │  on query + logs  │  strip names, phones, emails
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │  SAFETY ROUTER    │  Tier 0: regex + fine-tuned classifier
                   │  (pre-retrieval)  │  → hard block, canned referral, NO LLM CALL
                   └─────────┬─────────┘
                        pass │
                   ┌─────────▼─────────┐
                   │ HYBRID RETRIEVAL  │  BM25 (rank_bm25)  ─┐
                   │      (#2)         │                     ├─ RRF fusion → top-k
                   │                   │  Dense (bge-m3) ────┘
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │  GROUNDING GATE   │  max_score < τ → refuse
                   │                   │  "not found in corpus"
                   └─────────┬─────────┘
                        pass │
                   ┌─────────▼─────────┐
                   │  GENERATION       │  Local Gemma via Ollama (#1)
                   │  LoRA-tuned (#5)  │  + LoRA adapter for citation format
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │ CITATION VALIDATOR │  every [id] ∈ retrieved set?
                   │  (deterministic)   │  no → regenerate once → refuse
                   └─────────┬─────────┘
                             │
                          RESPONSE
Stack (all pinned):

Layer	Choice	Why
Generation	Gemma (same model you already have) via Ollama	Already your stack; local; GGUF
Embeddings	BAAI/bge-m3 via sentence-transformers	Multilingual, handles IAST transliteration + English, runs on MPS
Vector store	LanceDB (or Chroma)	Fully offline, single-file, no server
Lexical	rank_bm25	Sanskrit/IAST terms are exact-match-heavy; dense alone will fail you
Fusion	Reciprocal Rank Fusion (k=60)	Two lines of code, big win
Fine-tune	MLX-LM on Mac, or Colab T4 + adapter	See Phase 6
Synthetic data	Groq (#6)	Same setup as your vocab app
API	FastAPI	
PII	presidio-analyzer + spaCy en_core_web_sm	#7
Packaging	uv + Docker (multi-stage)	
CI	GitHub Actions	
3. Phase 0 — Scope lock and kill criteria (Day 1, 2 hours)
Before any code. Create docs/SCOPE.md containing:

The in-scope / out-of-scope lists from §1, verbatim
Your kill criteria — write these now, honestly:
If after Phase 4, hybrid retrieval Recall@10 on your gold set is below 0.70, the corpus segmentation is wrong — stop and fix Phase 2, don't proceed to fine-tuning
If plain BM25 alone gets within 5 points of your full pipeline, ship BM25 and write that up. That's a more honest result than a worse-but-fancier system.
Your v1 definition of done (copy from §16)
Commit this first. It's the file that stops the project sprawling.

4. Phase 1 — Data elicitation (Week 1)
This is your "no data" problem, solved. Four independent tracks — run them in parallel.

Track A — Classical text corpus (public domain only)
Target: 2 compendia, 4-6 sthanas, ~3000-6000 verses. Do not try to ingest all of Ayurveda. Depth over breadth for v1.

Recommended v1 corpus:

Charaka Samhita — Sutrasthana + Nidanasthana
Sushruta Samhita — Sutrasthana
Sources to evaluate, in priority order:

Source	URL	Notes
NIIMH e-Samhita	niimh.nic.in/ebooks/ecaraka/	Government (Ministry of Ayush / CCRAS) digitisation. Check terms of use. Best structural quality.
Archive.org	archive.org	Bhishagratna's Sushruta translation (1907–1916) and Kaviratna's Charaka are old enough to be clearly public domain. Verify publication dates per volume.
Wisdomlib	wisdomlib.org	English Charaka Samhita, chapter-structured. Check their reuse terms explicitly.
Charak Samhita Online Edition	(published project)	Modern structured edition — likely restrictive, but worth checking
CCRAS APTA / AMAR	Ministry of Ayush	Authoritative textbooks + manuscript repository
Rule: if the license is ambiguous, it goes in the ledger as a shadow entry — metadata recorded, text excluded. This is exactly the AyurParam approach and it's the correct one.

Track B — Structured herb data
IMPPAT 2.0 (cb.imsc.res.in/imppat) — plant → part → phytochemical and plant → part → therapeutic-use associations. Check download/reuse terms.
Cross-reference plant names against botanical binomials so "Haritaki" / "Harad" / Terminalia chebula all resolve to one entity.
Track C — Controlled vocabulary
NAMASTE portal (namaste.ayush.gov.in) — National Ayurveda Morbidity Codes and standardized terminologies, dual-coded against ICD-10/11.
Use this as your term normalisation layer: the biggest retrieval failure in this domain is the same concept appearing as Sanskrit, IAST, Devanagari, and three different English glosses. NAMC gives you a canonical spine.
This alone will lift your retrieval numbers more than any model swap.
Track D — Safety reference data (hand-curated, small)
Reality check: there is no permissively-licensed, machine-readable herb–drug interaction database. Drugs.com, Medscape, MSKCC's integrative-medicine herb database, and NCCIH are all either proprietary or not bulk-reusable. Do not scrape them.

Instead: hand-build a ~40-row flag table (data/safety/herb_flags.csv) covering the most commonly-queried herbs, with columns:

herb_canonical, botanical_name, flag_category, flag_note, source_citation, source_url, date_checked
Flag categories: pregnancy, hepatic, thyroid, autoimmune, cns_depressant_interaction, anticoagulant_interaction, surgery.

Every row must cite a named source (NCCIH, MSKCC, a peer-reviewed review). Forty hand-curated, cited rows beat four thousand scraped ones — and it's honest about what it is.

Deliverable for Phase 1
data/
├── raw/                        # gitignored — never committed
├── license_ledger.csv          # COMMITTED. one row per source document
└── safety/herb_flags.csv       # COMMITTED
scripts/01_acquire.py           # reproducible download, checksums to manifest
license_ledger.csv schema (steal from AyurParam):

doc_id, title, author, translator, edition_year, publisher, language,
script, source_url, declared_license, license_verdict, verdict_reason,
sha256, date_acquired, included_in_corpus (bool)
You do not commit the raw PDFs. You commit the acquisition script, the manifest with checksums, and the ledger. Anyone can reproduce your corpus; you redistribute nothing. Say this explicitly in the README.

5. Phase 2 — Corpus engineering (Week 1–2)
This phase determines your ceiling. Everything downstream inherits these decisions.

5.1 The unit of retrieval is the verse, not the page
Design your ID scheme now and never change it:

<book>_<sthana>_<chapter>_<verse>

cs_su_01_015   → Charaka Samhita, Sutrasthana, ch.1, verse 15
ss_su_15_003   → Sushruta Samhita, Sutrasthana, ch.15, verse 3
Stable, human-readable, sortable, and directly citable. This is the single most important design choice in the project — a citation the user can verify against a physical book is the whole value proposition.

5.2 Record schema
{
  "verse_id": "cs_su_01_015",
  "book": "Charaka Samhita",
  "sthana": "Sutrasthana",
  "chapter": 1,
  "chapter_title": "Deerghanjiviteeya Adhyaya",
  "verse": 15,
  "sanskrit_iast": "...",
  "english": "...",
  "translator": "Kaviratna",
  "edition_year": 1890,
  "doc_id": "...",            // FK to license_ledger
  "topics": ["dosha", "vata"], // NAMC-normalised tags
  "entities": {
    "herbs": ["haritaki"],
    "conditions": ["amlapitta"]
  },
  "prev_verse_id": "cs_su_01_014",
  "next_verse_id": "cs_su_01_016"
}
5.3 Chunking strategy
Index at verse level, retrieve with a context window.

Embed each verse individually (short, precise, citable)
At retrieval time, expand each hit to [prev, hit, next] before sending to the LLM — classical verses are frequently incomplete alone
The citation always anchors to the hit verse, never the window
This gives you precise citations AND sufficient context. Naive 512-token chunking destroys both.

5.4 Pipeline
scripts/02_extract.py     # PDF → raw text (pdfplumber; tesseract only if needed)
scripts/03_segment.py     # raw text → verse records (the hard part)
scripts/04_normalise.py   # NAMC term mapping, transliteration normalisation
scripts/05_qa_corpus.py   # quality gates — MUST PASS before proceeding
Quality gates in 05_qa_corpus.py (fail loudly):

No duplicate verse_id
No verse over 400 words (segmentation failure)
No verse under 5 words (OCR junk)
Every doc_id resolves to a ledger row with included_in_corpus = true
MinHash near-duplicate detection across editions (AyurParam does exactly this — multiple editions of the same compendium is the normal case in this domain)
Random-sample 30 verses and eyeball them against the source. Yes, manually. Budget an hour.
5.5 Build the gold eval set NOW — not later
This is the step everyone skips and it's why their projects don't count.

Hand-write 70 questions before you build any retrieval:

Count	Type
20	Conceptual — answer exists in 1-3 specific verses
15	Locational — "where does the text discuss X"
15	Herb properties
10	Comparative across two texts
10	Unanswerable — plausible but genuinely not in your corpus (the system must refuse)
Plus 40 adversarial safety queries in a separate file: emergencies, pregnancy dosing, pediatric, "can I stop my BP medication", bhasma preparation, self-harm, cancer cures.

Format: evals/gold_qa.jsonl

{"qid":"g001","question":"...","gold_verse_ids":["cs_su_01_015","cs_su_01_016"],
 "answerable":true,"category":"conceptual"}
Writing these is ~6 hours of genuinely tedious work reading your own corpus. Do it anyway. Without it you have opinions; with it you have results.

6. Phase 3 — Baselines before models (Week 2, half a day)
Roadmap method #0. Do not skip.

Run and record, in this order:

Baseline	What it tells you
B0: BM25-only retrieval + no LLM (return top verses raw)	The floor. Sometimes shockingly good.
B1: Base Gemma, no retrieval, zero-shot	Measures how much it hallucinates unaided. Expect it to confidently invent verse numbers — this is your motivating example for the README.
B2: Base Gemma + 4 few-shot examples in prompt, no retrieval	Does prompting alone fix format? (It won't fix facts.)
B3: Dense-only retrieval + base Gemma	Your real comparison point.
Record every number in evals/results/baselines.json. Your final README table compares your system against all four. If your full pipeline doesn't clearly beat B0, you built complexity for nothing — and saying so publicly is a stronger signal than faking a win.

7. Phase 4 — Retrieval (Week 2–3)
7.1 Build hybrid
# retrieval/hybrid.py
def search(query, k=10):
    dense_hits  = lance_table.search(embed(query)).limit(k*3).to_list()
    bm25_hits   = bm25.get_top_n(tokenize(query), corpus, n=k*3)
    fused       = reciprocal_rank_fusion(dense_hits, bm25_hits, k_rrf=60)
    return expand_context(fused[:k])
Why hybrid is mandatory here: dense embeddings handle "what promotes good digestion", BM25 handles "Agnivesha", "Dridhabala", "amlapitta", "vipaka". Neither alone covers this corpus. Expect BM25 to win on ~40% of your gold queries.

7.2 Query normalisation layer
Before retrieval, expand the query using your NAMC map:

"harad" → ["harad", "haritaki", "harītakī", "Terminalia chebula"]
Measure Recall@10 with and without this. In this domain it's usually worth several points — more than any embedding-model upgrade.

7.3 The grounding gate
if fused[0].score < TAU:
    return Refusal(reason="not_found_in_corpus")
Calibrate TAU on your 10 unanswerable gold questions. Target: refuse ≥ 9 of 10 unanswerable, while keeping Recall@10 ≥ 0.75 on answerable. Plot the tradeoff curve — that plot goes in your README.

7.4 Metrics to log
Recall@5, Recall@10, MRR@10, nDCG@10, plus false-refusal rate. Write them to evals/results/retrieval.json. Gate: Recall@10 ≥ 0.70 before proceeding (from your kill criteria).

8. Phase 5 — The safety router (Week 3)
Build this before generation. It sits in front of everything.

Tier 0 — Hard block, pre-retrieval, no LLM call
Deterministic regex + keyword patterns, then a small classifier as backstop. Categories:

Category	Response
Emergency symptoms (chest pain, breathing difficulty, severe bleeding, stroke signs, loss of consciousness)	Immediate emergency referral. Nothing else.
Self-harm / suicidal ideation	Crisis referral. Nothing else.
Pregnancy / lactation dosing	Refuse + refer to registered practitioner
Pediatric dosing	Refuse + refer
Oncology, "cure for cancer"	Refuse + refer
Stopping/replacing prescribed medication	Refuse + refer to prescribing doctor
Rasa Shastra / bhasma / heavy-metal preparation methods	Refuse entirely — no exceptions
Latency budget: <5ms. It short-circuits before retrieval, before the LLM, before anything.

Tier 1 — Flag and annotate
Query mentions a modern drug name (match against a pharma name list) → proceed with retrieval, but prepend a herb–drug-interaction banner and surface any matching row from herb_flags.csv.

Tier 2 — Normal path
Everything else. Proceeds to retrieval.

The dosage rule
Classical texts do state quantities. Your rule:

Classical dosage statements may be reported as textual content with citation, explicitly framed as what the text records. They are never converted into a second-person recommendation. The generation prompt forbids "you should take" constructions entirely, and a post-generation regex checks for them.

Write this rule in docs/SAFETY.md and link it from the README. Reviewers will look for exactly this.

Test it
tests/test_safety_router.py runs all 40 adversarial queries. Hard-block category must be 100% caught. This is a CI gate — merge blocked on failure.

9. Phase 6 — Synthetic data + fine-tune (Week 3–4)
Roadmap methods #6 then #3/#5.

9.1 What you're actually fine-tuning for
Not facts — facts come from retrieval. You're teaching three behaviours:

Citation discipline — emit [verse_id] inline, only for verses in the provided context
Refusal discipline — when context is thin or irrelevant, say so instead of improvising
Format discipline — consistent, concise, structured answers
This is precisely roadmap #5: RAG supplies facts, the fine-tune teaches context-handling behaviour.

9.2 Generating the training set with Groq
For each of 400 sampled verse-clusters from your corpus:
  1. Groq generates a plausible user question answerable from that cluster
  2. Groq generates the ideal answer, given ONLY those verses, with citations
  3. Validate deterministically: every cited ID ∈ the provided cluster. Reject otherwise.
Plus 150 negative examples: question + deliberately irrelevant context → correct refusal. Without these your model will never learn to refuse. This is the most commonly omitted part of RAG fine-tuning and the reason most RAG systems hallucinate under weak retrieval.

Target: ~550 pairs in data/sft/train.jsonl. Hold out 60 for validation. Zero overlap with your gold eval set — check programmatically, it's an easy and fatal mistake.

9.3 Running the LoRA on a Mac with no GPU
Option A — MLX (local, recommended):

pip install mlx-lm
mlx_lm.lora --model <gemma-repo> --train \
  --data data/sft --batch-size 1 --iters 600 \
  --lora-layers 8 --adapter-path adapters/ayurcite-v1
Runs on Apple Silicon unified memory. A ~2-4B model with a small adapter is comfortable. Unsloth will not help you here — it's CUDA-only.

Option B — Colab free T4: run the LoRA there, download the adapter (a few tens of MB), fuse locally. Faster wall-clock, one extra step.

Then: fuse adapter → convert to GGUF → ollama create with a Modelfile. Same path you already used for notes-to-tasks.

9.4 Gate before you accept the fine-tune
Run the full eval suite against base-model-with-RAG vs tuned-model-with-RAG. If groundedness and refusal don't improve, ship the base model and write up the negative result. A documented "fine-tuning didn't help here, and here's the data" is a stronger portfolio artifact than an unverified claim that it did.

10. Phase 7 — Generation + citation enforcement (Week 4)
System prompt skeleton
You answer ONLY from the provided verses. Rules:
1. Every factual sentence must cite a verse ID in square brackets.
2. Only cite IDs present in the CONTEXT below. Never invent an ID.
3. If the context does not answer the question, say so plainly. Do not improvise.
4. Report what the texts state. Never address the user's personal situation.
5. Never use "you should", "take", "apply", or any second-person instruction.
6. Maximum 6 sentences.

CONTEXT:
[cs_su_01_015] <verse text>
[cs_su_01_016] <verse text>
...
The citation validator (deterministic, non-negotiable)
def validate(answer, retrieved_ids):
    cited = set(re.findall(r'\[([a-z]{2}_[a-z]{2}_\d+_\d+)\]', answer))
    if not cited.issubset(retrieved_ids):
        return Invalid(hallucinated=cited - retrieved_ids)
    if re.search(r'\byou should\b|\btake \d', answer, re.I):
        return Invalid(reason="second_person_instruction")
    return Valid()
On invalid: regenerate once at temperature 0. Still invalid → return a refusal. Never return an unvalidated answer. Log every failure to logs/validation_failures.jsonl — that log is your debugging goldmine and a README chart.

11. Phase 8 — The eval harness (Week 4–5) — this is what makes it "not like other projects"
evals/run_eval.py produces one JSON report. Everything below goes in it.

Retrieval
Recall@5, Recall@10, MRR@10, nDCG@10
False-refusal rate on answerable questions
True-refusal rate on unanswerable questions
Groundedness (two methods, report both)
Deterministic: per-sentence character n-gram overlap with its cited verse. Cheap, reproducible, no API dependency.
LLM judge (Groq, temp 0, strict rubric): per-sentence supported / partially_supported / unsupported. Report the agreement rate between the two. Disagreement is itself a finding.
Hard gates (CI-blocking)
Metric	Threshold
Hallucinated citation rate	exactly 0%
Tier-0 safety catch rate	100%
Second-person instruction leakage	0%
Comparison table — the centrepiece of your README
System	Recall@10	Groundedness	Refusal (unanswerable)	Halluc. cites
B0: BM25 only		n/a		n/a
B1: LLM, no RAG	n/a			
B2: LLM + few-shot	n/a			
B3: Dense + base LLM				
AyurCite v1				
Also report
p50 / p95 latency, CPU-only, on your actual Mac
Peak RSS
Cost: ₹0 at inference (fully local) — state it, it's a real selling point
12. Phase 9 — Service layer (Week 5)
API
POST /query      {question, k?}  → {answer, citations[], confidence, safety_flags[]}
GET  /verse/{id}                 → full verse record
GET  /health                     → {status, corpus_version, model_version, adapter_version}
GET  /metrics                    → basic counters
Every response carries corpus_version, model_version, adapter_version. Auditability in a health-adjacent tool is not optional, and it's the kind of detail that reads as professional.

UI
One page. Search box, answer panel, sources panel with expandable verse cards, a persistent scope banner. Plain HTML + a little JS is fine — resist building a React app for v1.

FastAPI serves the static build and the API from one origin. No CORS, one URL, one process.

Request logging with PII scrubbing (#7)
Every logged query passes through Presidio before it hits disk. Even locally. Demonstrating this discipline on a health tool is a hiring signal — and it means you can show the log file to a client without anxiety.

13. Phase 10 — Repo, CI, release (Week 5–6)
Repo structure
ayurcite/
├── README.md                    # the artifact people actually read
├── LICENSE                      # Apache-2.0 (code)
├── CHANGELOG.md
├── pyproject.toml               # uv, pinned
├── .pre-commit-config.yaml      # ruff, ruff-format, nbstripout
├── Dockerfile                   # multi-stage
├── docker-compose.yml           # app + ollama
├── Makefile                     # make ingest / eval / serve / test
│
├── docs/
│   ├── SCOPE.md                 # from Phase 0
│   ├── SAFETY.md                # the router + dosage rule
│   ├── DATA.md                  # provenance + licensing
│   ├── EVAL.md                  # methodology, not just numbers
│   ├── ARCHITECTURE.md
│   ├── prior-art.md
│   ├── MODEL_CARD.md            # HF format
│   └── DATASET_CARD.md          # HF format
│
├── data/
│   ├── license_ledger.csv       # ✅ committed
│   ├── manifest.json            # ✅ committed — checksums
│   ├── safety/herb_flags.csv    # ✅ committed
│   ├── raw/                     # ❌ gitignored
│   ├── processed/               # ❌ gitignored (git-lfs if you must)
│   └── sft/                     # ✅ committed (it's yours — synthetic)
│
├── src/ayurcite/
│   ├── ingest/     extract.py  segment.py  normalise.py  qa.py
│   ├── retrieval/  embed.py  bm25.py  hybrid.py  rerank.py
│   ├── safety/     router.py  patterns.py  herb_flags.py  scrub.py
│   ├── generate/   prompt.py  llm.py  validator.py
│   ├── api/        main.py  schemas.py
│   └── config.py
│
├── evals/
│   ├── gold_qa.jsonl
│   ├── adversarial.jsonl
│   ├── run_eval.py
│   └── results/                 # ✅ committed — every run, versioned
│
├── scripts/        01_acquire.py … 06_build_index.py
├── tests/          test_safety_router.py  test_validator.py  test_retrieval.py …
├── notebooks/      # exploration only, stripped of outputs
└── .github/workflows/ci.yml
CI (.github/workflows/ci.yml)
jobs:
  quality:   ruff check + ruff format --check + pytest
  safety:    pytest tests/test_safety_router.py   # 100% or fail
  eval-smoke: python evals/run_eval.py --subset 20 --mock-llm
             # fails build if hallucinated_citation_rate > 0
Use a mocked/deterministic LLM in CI so it runs without a model or API key. A green badge that actually means something.

Release checklist
 All quality gates green
 evals/results/v1.0.0.json committed
 README comparison table filled with real numbers
 MODEL_CARD + DATASET_CARD complete, including limitations and out-of-scope uses
 docker compose up works from a clean clone
 make ingest reproduces the corpus from scratch on another machine
 No raw copyrighted text in git history (git log --all --diff-filter=A --name-only)
 Demo GIF in README (30 seconds: a good answer, a refusal, a safety block)
 git tag -a v1.0.0 -m "..." → push → GitHub Release with notes
 Optional: deploy to HF Spaces free tier for a live link
README structure (this is the deliverable people judge)
One-sentence description + demo GIF
Scope box — what it does and explicitly does not do, right at the top
Results table (with baselines — never hide them)
Architecture diagram
Data provenance + licensing stance
Safety design
Quickstart
Eval methodology → link to docs/EVAL.md
Limitations — be generous and specific here; it reads as competence, not weakness
Prior art and how this differs
14. Week-by-week
Week	Focus	Done when
1	Phase 0–1: scope lock, license ledger, acquisition	Ledger has ≥15 rows with verdicts; raw corpus downloaded
2	Phase 2–3: segmentation, QA gates, gold set, baselines	70 gold Q + 40 adversarial written; baselines recorded
3	Phase 4–5: hybrid retrieval, safety router	Recall@10 ≥ 0.70; safety tests 100%
4	Phase 6–7: synthetic data, LoRA, citation validator	Hallucinated citations 0% on eval subset
5	Phase 8–9: eval harness, API, UI	Full results table generated
6	Phase 10: docs, Docker, CI, release	v1.0.0 tagged
Realistic at ~12–15 hrs/week alongside college. Week 2 is the one that gets skipped and it's the one that matters most. Protect it.

15. Cut list — what NOT to build in v1
Explicitly deferred. Write them in docs/ROADMAP_V2.md so it's visible you chose, not forgot:

Devanagari / Sanskrit-native retrieval (v1 is English + IAST only)
Cross-encoder reranking (flag it, off by default — CPU cost isn't worth it yet)
Knowledge graph over entities (AyurKOSH-style)
Multi-turn conversation
Agentic multi-hop retrieval
Mobile deployment (roadmap #8)
User accounts / personalisation (and personalisation would break scope anyway)
16. Definition of done for v1.0.0
git clone → docker compose up → working local system, no GPU, no API key
Hallucinated citation rate: 0% on the full gold set
Tier-0 safety catch rate: 100% on the adversarial set
Recall@10 ≥ 0.70, and the pipeline demonstrably beats all four baselines — or the README honestly explains why it doesn't
Corpus fully reproducible from scripts/ + manifest.json; zero redistributed copyrighted text
Green CI, tagged release, complete model + dataset cards
17. Failure modes, and how you'll catch them
Failure	Symptom	Catch
Segmentation garbage	Verses wildly variable in length	05_qa_corpus.py gates
Dense-only retrieval	Sanskrit-term queries fail	BM25 leg + per-query-type recall breakdown
Model ignores context	Confident answers with no citations	Citation validator + negative training examples
Eval-set contamination	Suspiciously high scores	Programmatic overlap check between SFT and gold
Scope creep into advice	"You should take…" appears	Post-gen regex + CI gate
License drift	A restrictive source sneaks in	included_in_corpus FK check in QA gate
Fine-tune didn't help	Metrics flat	You ran baselines, so you'll actually know
18. Why this is worth your time commercially
Strip out "Ayurveda" and this is a cited-answer system over a regulated corpus with an enforced refusal policy and a measured groundedness rate.

That is directly the shape of:

Indian law-firm work: statute and judgment retrieval with paragraph-level citation
Insurance: policy-wording Q&A where a hallucinated clause is a liability event
Manufacturing / pharma compliance: SOP and regulatory-document lookup
Any enterprise RAG pilot where "how do you know it isn't making things up" is the first question asked
You will be able to answer that question with a number and a reproducible eval harness. Almost nobody pitching AAA work can. That — far more than the Ayurveda framing — is what this project buys you.

And the domain choice is good on its own terms: AYUSH is a real, funded, digitising sector in India, which makes it a credible demo for domestic clients and a genuinely distinctive one for US/UK/AU prospects.

Build order is deliberate: data → evaluation → retrieval → safety → generation → model. The temptation is to start at the model. Resist it — that's the ordering that produces projects that demo well and evaluate badly.