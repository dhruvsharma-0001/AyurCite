SYSTEM_PROMPT = """You are AyurCite, a precision Ayurvedic classical literature reference assistant.
You answer questions ONLY using the provided classical verses in the CONTEXT below.

STRICT OPERATING RULES:
1. Every factual statement in your answer must cite its supporting verse ID in square brackets, e.g. [cs_su_01_015].
2. You must ONLY cite verse IDs that are explicitly provided in the CONTEXT below. Never invent or hallucinate a verse ID.
3. If the provided context does not contain enough information to answer the question, state plainly: "The classical verses in the corpus do not contain sufficient information to answer this question." Do not improvise or extrapolate.
4. Always frame statements as what the classical texts record (e.g. "Charaka states...", "The verse records..."). Never address the user's personal medical condition.
5. NEVER use second-person medical directives or advice (e.g. "you should", "take", "drink", "apply", "recommended for you").
6. Keep the answer concise: 3 to 6 sentences maximum.

CONTEXT:
{context_str}
"""


def format_context_for_prompt(retrieved_verses: list[dict]) -> str:
    """Format retrieved verses with context window for LLM prompt."""
    lines = []
    for v in retrieved_verses:
        vid = v.get("verse_id")
        book = v.get("book", "")
        ch = v.get("chapter", "")
        vnum = v.get("verse", "")
        text = v.get("english", "").strip()
        lines.append(f"[{vid}] ({book}, Chapter {ch}, Verse {vnum}): {text}")

        # If neighbor verses are included for context expansion
        if v.get("prev_verse_text"):
            pvid = v.get("prev_verse_id")
            lines.append(f"  [Context before - {pvid}]: {v.get('prev_verse_text').strip()}")
        if v.get("next_verse_text"):
            nvid = v.get("next_verse_id")
            lines.append(f"  [Context after - {nvid}]: {v.get('next_verse_text').strip()}")
        lines.append("")

    return "\n".join(lines).strip()


def build_prompt(question: str, retrieved_verses: list[dict]) -> str:
    context_str = format_context_for_prompt(retrieved_verses)
    return (
        SYSTEM_PROMPT.format(context_str=context_str) + f"\n\nUSER QUESTION: {question}\n\nANSWER:"
    )
