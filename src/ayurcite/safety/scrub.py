import re

# Regex-based PII scrubber (fast, offline, deterministic)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
AADHAAR_PATTERN = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


def scrub_pii(text: str) -> tuple[str, bool]:
    """
    Scrub PII (email, phone, national IDs) from user query and logs before storage.
    Returns: (scrubbed_text, had_pii)
    """
    scrubbed = text
    had_pii = False

    if EMAIL_PATTERN.search(scrubbed):
        scrubbed = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", scrubbed)
        had_pii = True

    if PHONE_PATTERN.search(scrubbed):
        scrubbed = PHONE_PATTERN.sub("[REDACTED_PHONE]", scrubbed)
        had_pii = True

    if AADHAAR_PATTERN.search(scrubbed):
        scrubbed = AADHAAR_PATTERN.sub("[REDACTED_ID]", scrubbed)
        had_pii = True

    if CREDIT_CARD_PATTERN.search(scrubbed):
        scrubbed = CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", scrubbed)
        had_pii = True

    return scrubbed, had_pii
