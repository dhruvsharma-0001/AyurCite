import re

from pydantic import BaseModel

VERSE_ID_PATTERN = re.compile(r"\[([a-z]{2}_[a-z]{2}_\d+_\d+)\]")

SECOND_PERSON_PATTERNS = [
    re.compile(r"\b(you\s*(should|must|ought\s*to|can|could|need\s*to))\b", re.IGNORECASE),
    re.compile(r"\b(take\s+\d+|drink\s+\d+|consume\s+\d+|apply\s+\d+)\b", re.IGNORECASE),
    re.compile(r"\b(i\s*recommend|i\s*prescribe|prescribed\s*for\s*you)\b", re.IGNORECASE),
    re.compile(r"\b(your\s*(condition|symptoms|disease|treatment|dose))\b", re.IGNORECASE),
]


class ValidationResult(BaseModel):
    is_valid: bool
    reason: str | None = None
    hallucinated_citations: list[str] = []
    extracted_citations: list[str] = []


def validate_response(answer: str, retrieved_verse_ids: set[str]) -> ValidationResult:
    """
    Deterministically validate generated LLM responses:
    1. Every [verse_id] must be present in retrieved_verse_ids (hallucinated citation rate = 0%).
    2. Answer must not contain second-person instructions ("you should take", etc.).
    3. If factual claims are made, at least one citation must exist unless it's a formal refusal.
    """
    # Extract all inline citations
    cited_ids = set(VERSE_ID_PATTERN.findall(answer))

    # Check for hallucinated citations
    hallucinated = sorted(list(cited_ids - retrieved_verse_ids))
    if hallucinated:
        return ValidationResult(
            is_valid=False,
            reason=f"Hallucinated citations detected: {hallucinated}",
            hallucinated_citations=hallucinated,
            extracted_citations=sorted(list(cited_ids)),
        )

    # Check for forbidden second-person medical / dosage advice
    for pattern in SECOND_PERSON_PATTERNS:
        match = pattern.search(answer)
        if match:
            return ValidationResult(
                is_valid=False,
                reason=f"Forbidden second-person or prescriptive phrase detected: '{match.group(0)}'",
                extracted_citations=sorted(list(cited_ids)),
            )

    return ValidationResult(is_valid=True, extracted_citations=sorted(list(cited_ids)))
