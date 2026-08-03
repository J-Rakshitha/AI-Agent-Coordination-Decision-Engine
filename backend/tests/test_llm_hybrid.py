"""Hybrid AI client — Google GenAI SDK path and fallback behaviour."""
import pytest


@pytest.fixture
def reset_hybrid_client():
    from app.agents.llm import llm_client

    llm_client.HybridAIClient._client = None
    llm_client.HybridAIClient._configured = False
    llm_client.FORCE_SIMULATED_FAILURE = False
    yield
    llm_client.HybridAIClient._client = None
    llm_client.HybridAIClient._configured = False
    llm_client.FORCE_SIMULATED_FAILURE = False


async def test_hybrid_client_uses_llm_when_genai_succeeds(monkeypatch, reset_hybrid_client):
    from app.core.config import settings
    from app.agents.llm.llm_client import HybridAIClient

    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AQ.test-auth-key-for-unit-test")
    monkeypatch.setattr(settings, "LLM_MODEL", "gemini-2.0-flash")

    class FakeResponse:
        text = "LLM generated insight"

    class FakeAioModels:
        async def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeAio:
        models = FakeAioModels()

    class FakeClient:
        aio = FakeAio()

    monkeypatch.setattr(
        "google.genai.Client",
        lambda **kwargs: FakeClient(),
    )

    result = await HybridAIClient.reason(
        prompt="test prompt",
        fallback_fn=lambda: "rule based answer",
    )

    assert result.used_llm is True
    assert result.text == "LLM generated insight"


async def test_hybrid_client_falls_back_on_simulated_failure(monkeypatch, reset_hybrid_client):
    from app.core.config import settings
    from app.agents.llm import llm_client
    from app.agents.llm.llm_client import HybridAIClient

    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AQ.test-auth-key-for-unit-test")
    llm_client.FORCE_SIMULATED_FAILURE = True

    result = await HybridAIClient.reason(
        prompt="test prompt",
        fallback_fn=lambda: "rule based answer",
    )

    assert result.used_llm is False
    assert result.text == "rule based answer"


async def test_hybrid_client_falls_back_when_genai_raises(monkeypatch, reset_hybrid_client):
    from app.core.config import settings
    from app.agents.llm.llm_client import HybridAIClient

    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AQ.test-auth-key-for-unit-test")

    class FakeAioModels:
        async def generate_content(self, **kwargs):
            raise RuntimeError("401 UNAUTHENTICATED")

    class FakeAio:
        models = FakeAioModels()

    class FakeClient:
        aio = FakeAio()

    monkeypatch.setattr(
        "google.genai.Client",
        lambda **kwargs: FakeClient(),
    )

    result = await HybridAIClient.reason(
        prompt="test prompt",
        fallback_fn=lambda: "rule based answer",
    )

    assert result.used_llm is False
    assert result.text == "rule based answer"
    assert result.error is not None
