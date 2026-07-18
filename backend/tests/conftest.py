"""
Shared pytest fixtures.

Sets a DEDICATED test database and disables the LLM before the app is
imported, so the test suite is fast, deterministic, and never depends on
network access or an API key — every test exercises the rule-based path,
which is exactly what should run in CI anyway.
"""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_coordination_engine.db"
os.environ["LLM_ENABLED"] = "False"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import engine, Base

# Import all models so Base.metadata knows about every table.
from app.models import dev_collab, incident, memory, tool_execution  # noqa: F401


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    """Fresh schema before every test — tests never leak state into each other."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def _stub_external_lookup(monkeypatch):
    """Tests must never depend on live network access to GitHub's API."""
    from app.agents.aiops import external_lookup_agent

    async def _fake_find_related_issues(query, timeout=4.0, max_results=3):
        return []

    monkeypatch.setattr(
        external_lookup_agent.ExternalLookupAgent,
        "find_related_issues",
        staticmethod(_fake_find_related_issues),
    )


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
