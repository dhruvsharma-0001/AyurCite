# AyurCite Safety Architecture & Dosage Enforcement

AyurCite operates under a strict principle: **Scope is the product**. In a health-adjacent domain, answering what classical texts state is valuable; giving medical or dosage advice is unacceptable.

---

## 1. Safety Router Tiers

```
                         Incoming User Query
                                  │
                       ┌──────────▼──────────┐
                       │  PII Redaction      │  Strip emails, phone numbers, IDs
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │  Tier-0 Hard Block  │  Latency < 0.01ms (Regex & Keywords)
                       │  (Pre-Retrieval)    │  Matches emergency, pregnancy, etc.?
                       └──────────┬──────────┘
                            NO   │   YES ────────► IMMEDIATE HARD REFUSAL
                                 │                (No LLM call, no retrieval)
                       ┌──────────▼──────────┐
                       │  Tier-1 Annotation  │  Matches modern prescription drug or
                       │                     │  clinical herb contraindication?
                       └──────────┬──────────┘
                            NO   │   YES ────────► PREPEND SAFETY WARNING BANNER
                                 │
                       ┌──────────▼──────────┐
                       │  Tier-2 Normal Path │  Proceeds to Hybrid Retrieval & LLM
                       └─────────────────────┘
```

### Tier 0 — Hard Refusal Categories (<5ms latency budget)
Matches are evaluated instantaneously before retrieval or language model invocation:
1. **Emergency Symptoms**: Chest pain, cardiac arrest, respiratory distress, stroke signs, massive hemorrhage, loss of consciousness, convulsions.
2. **Self-Harm / Crisis**: Suicidal ideation, self-harm, overdose queries.
3. **Pregnancy & Lactation**: Dosing guidance or abortifacient queries for pregnant or nursing individuals.
4. **Pediatric Dosing**: Treatment or dosages for infants, toddlers, and young children.
5. **Oncology / Malignancy**: Cures or alternative therapies for cancer, tumors, or leukemia.
6. **Medication Replacement**: Discontinuing or replacing prescribed pharmaceuticals (e.g., metformin, lisinopril, statins, insulin, blood thinners).
7. **Rasa Shastra / Heavy Metals**: Home preparation or ingestion of Bhasmas containing mercury, lead, arsenic, or copper.

### Tier 1 — Interaction Flagging
- Matches modern prescription drugs (e.g., warfarin, metformin, statins) and surfaces potential pharmacokinetic/pharmacodynamic interactions.
- Matches herbs with documented clinical contraindications from `data/safety/herb_flags.csv` (citing NCCIH, MSKCC, LiverTox).

---

## 2. The Dosage Rule

Classical Ayurvedic texts (such as Charaka Samhita and Sushruta Samhita) do record measurements and therapeutic quantities (e.g., *palas*, *karshas*, *tolas*).

### Non-Negotiable Protocol:
> Classical dosage statements may only be reported as **objective textual facts with citation**, explicitly framed as historical literature.
> They are **never** converted into a second-person clinical directive.

### Deterministic Validation:
The response validator (`src/ayurcite/generate/validator.py`) deterministically rejects:
- Second-person directives: `\b(you (should|must|ought to|can))\b`
- Prescriptive commands: `\b(take \d+|drink \d+|apply \d+)\b`
- Personal framing: `\b(your condition|for your symptoms)\b`

Any response failing this check is regenerated once at temperature 0. If it fails again, the system returns a refusal.
