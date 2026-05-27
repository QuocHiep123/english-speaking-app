# =============================================================================
# LLM Evaluation Service — IELTS Speaking Assessment via Groq Cloud
# =============================================================================

import json
from typing import Any, Dict

from groq import AsyncGroq

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# System prompt enforcing strict JSON-only output
_SYSTEM_PROMPT = (
    "You are an expert IELTS examiner. "
    "You will receive a noisy transcript from a Vietnamese speaker. "
    "1) Correct any STT mishearings to form what the user likely meant. "
    "2) Provide a Lexical Resource score (0-9) and Grammar score (0-9). "
    "3) Give brief feedback. "
    "You MUST return the response ONLY as a valid JSON object with keys: "
    "'corrected_text', 'lexical_score', 'grammar_score', 'feedback'."
)

# Expected keys in the LLM JSON response
_EXPECTED_KEYS = {"corrected_text", "lexical_score", "grammar_score", "feedback"}


class IELTSEvaluatorService:
    """Evaluates IELTS speaking transcripts using Groq's LLM API.

    Sends the raw STT transcript to Groq Cloud and parses the structured
    JSON assessment returned by the model.
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile") -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model = model
        logger.info("llm_service_init", model=self._model, backend="groq")

    async def evaluate_transcript(self, transcript: str) -> Dict[str, Any]:
        """Send a transcript to Groq for IELTS evaluation.

        Args:
            transcript: Raw STT transcript text.

        Returns:
            Dict with keys: corrected_text, lexical_score, grammar_score,
            feedback. Falls back to an error dict if parsing fails.
        """
        user_prompt = (
            f"Evaluate the following IELTS Speaking transcript:\n\n"
            f"\"{transcript}\""
        )

        logger.info("llm_request_start", model=self._model, transcript_len=len(transcript))

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=512,
        )

        raw_text: str = response.choices[0].message.content or ""

        logger.debug("llm_raw_response", raw_text=raw_text[:500])

        return self._parse_evaluation(raw_text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_evaluation(raw_text: str) -> Dict[str, Any]:
        """Safely parse the LLM response into a structured dict.

        If the LLM returns invalid JSON or is missing expected keys,
        this returns a best-effort result with an ``llm_parse_error`` flag
        so the caller can decide how to handle it.
        """
        try:
            result = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("llm_json_parse_error", error=str(exc), raw=raw_text[:300])
            return {
                "corrected_text": None,
                "lexical_score": None,
                "grammar_score": None,
                "feedback": None,
                "llm_parse_error": f"Failed to parse LLM response as JSON: {exc}",
                "raw_llm_response": raw_text[:1000],
            }

        # Validate expected keys are present
        missing = _EXPECTED_KEYS - set(result.keys())
        if missing:
            logger.warning("llm_missing_keys", missing=list(missing))
            for key in missing:
                result[key] = None
            result["llm_parse_error"] = f"Missing keys in LLM response: {sorted(missing)}"

        # Clamp scores to 0-9 range when they are numeric
        for score_key in ("lexical_score", "grammar_score"):
            val = result.get(score_key)
            if isinstance(val, (int, float)):
                result[score_key] = max(0, min(9, val))

        return result
