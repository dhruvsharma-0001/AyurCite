import re
import time
from typing import List, Optional
from pydantic import BaseModel
from src.ayurcite.config import settings
from src.ayurcite.safety.patterns import SAFETY_PATTERNS, REFUSAL_MESSAGES, COMMON_PHARMA_DRUGS
from src.ayurcite.safety.herb_flags import HerbFlagRegistry, HerbFlagRecord

class SafetyDecision(BaseModel):
    allowed: bool
    tier: int
    category: Optional[str] = None
    refusal_message: Optional[str] = None
    warning_banner: Optional[str] = None
    pharma_flags: List[str] = []
    herb_flags: List[HerbFlagRecord] = []
    latency_ms: float = 0.0

class SafetyRouter:
    def __init__(self, herb_flags_registry: Optional[HerbFlagRegistry] = None):
        self.herb_flags = herb_flags_registry or HerbFlagRegistry(settings.herb_flags_path)

    def route(self, query: str) -> SafetyDecision:
        t0 = time.perf_counter()
        q_clean = query.strip()

        # Tier 0: Hard block (<5ms latency budget)
        for category, patterns in SAFETY_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(q_clean):
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    return SafetyDecision(
                        allowed=False,
                        tier=0,
                        category=category,
                        refusal_message=REFUSAL_MESSAGES[category],
                        latency_ms=latency_ms
                    )

        # Tier 1: Check modern pharma drugs and herb contraindications
        q_words = set(re.findall(r"\b[a-zA-Z]+\b", q_clean.lower()))
        detected_pharma = sorted(list(q_words.intersection(COMMON_PHARMA_DRUGS)))
        matched_herb_flags = self.herb_flags.scan_query(q_clean)

        if detected_pharma or matched_herb_flags:
            banner_parts = []
            if detected_pharma:
                banner_parts.append(
                    f"PHARMACEUTICAL INTERACTION CAUTION: Query mentions modern prescription medication(s): {', '.join(detected_pharma)}. "
                    "Herbal compounds can alter CYP enzyme metabolism and bioavailability."
                )
            if matched_herb_flags:
                categories = {f.flag_category for f in matched_herb_flags}
                banner_parts.append(
                    f"HERB SAFETY CAUTION: Mentions herbs with active clinical contraindications ({', '.join(categories)}). "
                    "Review referenced flags below."
                )

            latency_ms = (time.perf_counter() - t0) * 1000.0
            return SafetyDecision(
                allowed=True,
                tier=1,
                warning_banner=" | ".join(banner_parts),
                pharma_flags=detected_pharma,
                herb_flags=matched_herb_flags,
                latency_ms=latency_ms
            )

        # Tier 2: Normal path
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return SafetyDecision(
            allowed=True,
            tier=2,
            latency_ms=latency_ms
        )
