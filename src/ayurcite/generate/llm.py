import json
import logging
from typing import Dict, List, Optional, Set
import httpx
from pydantic import BaseModel

from src.ayurcite.config import settings
from src.ayurcite.generate.prompt import build_prompt
from src.ayurcite.generate.validator import validate_response, ValidationResult

logger = logging.getLogger("ayurcite.generator")

class GenerationResult(BaseModel):
    answer: str
    confidence: str  # grounded, partial, refused
    extracted_citations: List[str] = []
    is_valid: bool = True
    retries_used: int = 0
    validation_reason: Optional[str] = None
    model_used: str

class LLMGenerator:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        use_mock: bool = False
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model_name = model_name or settings.model_name
        self.use_mock = use_mock

    def _call_ollama(self, prompt: str, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 250,
            }
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()

    def _generate_mock_answer(self, question: str, retrieved_verses: List[Dict]) -> str:
        """Deterministic fallback when Ollama is offline or in CI smoke tests."""
        if not retrieved_verses:
            return "The classical verses in the corpus do not contain sufficient information to answer this question."
        top_verse = retrieved_verses[0]
        vid = top_verse["verse_id"]
        book = top_verse.get("book", "The classical text")
        text = top_verse.get("english", "").strip()
        # Create a clean, cited summary sentence
        first_sent = text.split(".")[0] if "." in text else text[:120]
        return f"According to {book}, {first_sent.strip()} [{vid}]."

    def generate(
        self,
        question: str,
        retrieved_verses: List[Dict]
    ) -> GenerationResult:
        retrieved_ids: Set[str] = {v["verse_id"] for v in retrieved_verses}

        if not retrieved_verses:
            return GenerationResult(
                answer="The classical verses in the corpus do not contain sufficient information to answer this question.",
                confidence="refused",
                extracted_citations=[],
                is_valid=True,
                model_used="rule_refusal"
            )

        prompt = build_prompt(question, retrieved_verses)

        # Attempt 1
        raw_answer = ""
        retries = 0
        if self.use_mock:
            raw_answer = self._generate_mock_answer(question, retrieved_verses)
        else:
            try:
                raw_answer = self._call_ollama(prompt, temperature=0.2)
            except Exception as e:
                logger.warning(f"Ollama call failed ({e}). Falling back to deterministic cited generator.")
                raw_answer = self._generate_mock_answer(question, retrieved_verses)

        # Validate Attempt 1
        val = validate_response(raw_answer, retrieved_ids)

        # Retry once at temperature 0 if invalid
        if not val.is_valid and not self.use_mock:
            retries += 1
            logger.info(f"Attempt 1 invalid ({val.reason}). Retrying once at temperature 0...")
            try:
                raw_answer = self._call_ollama(prompt, temperature=0.0)
                val = validate_response(raw_answer, retrieved_ids)
            except Exception:
                pass

        # If still invalid after retry, refuse plainly rather than outputting ungrounded text
        if not val.is_valid:
            logger.warning(f"Response validation failed after retry: {val.reason}. Forcing refusal.")
            return GenerationResult(
                answer="The classical verses in the corpus do not contain verified grounded information to address this query.",
                confidence="refused",
                extracted_citations=[],
                is_valid=False,
                retries_used=retries,
                validation_reason=val.reason,
                model_used=self.model_name
            )

        confidence = "grounded" if len(val.extracted_citations) > 0 else "partial"

        return GenerationResult(
            answer=raw_answer,
            confidence=confidence,
            extracted_citations=val.extracted_citations,
            is_valid=True,
            retries_used=retries,
            model_used=self.model_name
        )
