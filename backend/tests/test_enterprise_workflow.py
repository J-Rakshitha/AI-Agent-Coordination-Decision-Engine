async def test_chat_session_and_ask(client):
    create = await client.post("/api/chat/sessions", json={"title": "Test chat"})
    assert create.status_code == 200
    session_id = create.json()["id"]

    ask = await client.post(
        f"/api/chat/sessions/{session_id}/ask",
        json={"question": "How many conflicts are predicted?"},
    )
    assert ask.status_code == 200
    assert "answer" in ask.json()

    messages = (await client.get(f"/api/chat/sessions/{session_id}/messages")).json()
    assert len(messages) >= 2


async def test_hitl_defer_conflict(client):
    sim = await client.post("/api/dev-collab/simulate-demo-conflict")
    conflict_id = sim.json()["conflict_id"]
    await client.post(f"/api/dev-collab/conflicts/{conflict_id}/suggest-resolution")

    defer = await client.post(
        f"/api/dev-collab/conflicts/{conflict_id}/resolve-later",
        json={"note": "Business review scheduled"},
    )
    assert defer.status_code == 200
    assert defer.json()["approval_status"] == "deferred"


async def test_auth_required_without_token():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/dev-collab/conflicts")
        assert resp.status_code == 401
