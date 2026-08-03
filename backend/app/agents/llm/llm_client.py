"""
Hybrid AI Client — Google GenAI SDK (supports AIza + AQ auth keys)
==================================================================
Hybrid approach:
- Uses the official `google-genai` SDK (Gemini Developer API, including AQ auth keys).
- If the API key is missing, times out, errors, or hits a rate limit,
  it automatically falls back to rule-based logic — so the demo NEVER crashes.

Every "thinking" agent calls `HybridAIClient.reason()` instead of calling
Gemini directly. Fallback logic lives in ONE place.
"""
import asyncio
import logging
from typing import Optional

from app.core.config import settings, is_llm_key_valid

logger = logging.getLogger("hybrid_ai_client")

# Simulate-failure switch used for live demos to PROVE the fallback works.
# Toggle via the /api/system/toggle-llm-failure endpoint.
FORCE_SIMULATED_FAILURE = False


class HybridAIClient:
    """
    Usage:
        result = await HybridAIClient.reason(
            prompt="...",
            fallback_fn=lambda: "rule based answer"
        )
        result.text        -> the answer text
        result.used_llm     -> True if Gemini answered, False if fallback used
    """

    _client = None
    _configured = False

    class Result:
        def __init__(self, text: str, used_llm: bool, error: Optional[str] = None):
            self.text = text
            self.used_llm = used_llm
            self.error = error

    @classmethod
    def _configure(cls):
        if cls._configured:
            return
        cls._configured = True
        if not settings.LLM_ENABLED or not is_llm_key_valid():
            logger.info("LLM disabled or no valid API key — running in rule-based-only mode.")
            return
        try:
            from google import genai

            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
            logger.info(
                "Google GenAI client ready (model=%s, key_type=%s).",
                settings.LLM_MODEL,
                "AQ-auth" if settings.GEMINI_API_KEY.strip().startswith("AQ.") else "standard",
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Google GenAI configuration failed: %s", exc)
            cls._client = None

    @classmethod
    async def reason(cls, prompt: str, fallback_fn) -> "HybridAIClient.Result":
        """
        Try Gemini first, fall back to rule-based fn on ANY failure.
        `fallback_fn` must be a zero-arg callable returning a string.
        """
        cls._configure()

        if FORCE_SIMULATED_FAILURE or cls._client is None:
            return cls.Result(text=fallback_fn(), used_llm=False)

        try:
            from google.genai import types

            response = await asyncio.wait_for(
                cls._client.aio.models.generate_content(
                    model=settings.LLM_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.4),
                ),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Empty response from LLM")
            return cls.Result(text=text, used_llm=True)
        except Exception as exc:
            logger.warning("LLM call failed, using rule-based fallback: %s", exc)
            return cls.Result(text=fallback_fn(), used_llm=False, error=str(exc))


def set_simulated_failure(enabled: bool):
    """Used by the demo 'Simulate API Failure' toggle button in the UI."""
    global FORCE_SIMULATED_FAILURE
    FORCE_SIMULATED_FAILURE = enabled


def get_simulated_failure() -> bool:
    return FORCE_SIMULATED_FAILURE
