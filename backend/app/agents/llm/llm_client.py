"""
Hybrid AI Client — now powered by LangChain
=============================================
This is the heart of the "Hybrid approach" decision:
- Uses LangChain's ChatGoogleGenerativeAI (wrapping Gemini) for reasoning tasks.
- If the API key is missing, times out, errors, or hits a rate limit,
  it automatically falls back to rule-based logic — so the demo NEVER crashes.

Every agent in both modules calls `HybridAIClient.reason()` instead of
calling LangChain/Gemini directly. This keeps the fallback logic in ONE place.
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
        result.used_llm     -> True if the LLM (via LangChain) answered, False if fallback used
    """

    _model = None
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
            from langchain_google_genai import ChatGoogleGenerativeAI
            cls._model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.4,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"LangChain/Gemini configuration failed: {exc}")
            cls._model = None

    @classmethod
    async def reason(cls, prompt: str, fallback_fn) -> "HybridAIClient.Result":
        """
        Try the LangChain-wrapped LLM first, fall back to rule-based fn on
        ANY failure. `fallback_fn` must be a zero-arg callable returning a string.
        """
        cls._configure()

        if FORCE_SIMULATED_FAILURE or cls._model is None:
            return cls.Result(text=fallback_fn(), used_llm=False)

        try:
            response = await asyncio.wait_for(
                cls._model.ainvoke(prompt),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
            text = (response.content or "").strip()
            if not text:
                raise ValueError("Empty response from LLM")
            return cls.Result(text=text, used_llm=True)
        except Exception as exc:
            logger.warning(f"LLM call failed, using rule-based fallback: {exc}")
            return cls.Result(text=fallback_fn(), used_llm=False, error=str(exc))


def set_simulated_failure(enabled: bool):
    """Used by the demo 'Simulate API Failure' toggle button in the UI."""
    global FORCE_SIMULATED_FAILURE
    FORCE_SIMULATED_FAILURE = enabled


def get_simulated_failure() -> bool:
    return FORCE_SIMULATED_FAILURE
