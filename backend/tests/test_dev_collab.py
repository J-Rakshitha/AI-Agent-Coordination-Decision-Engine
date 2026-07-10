async def test_simulate_conflict_creates_two_sessions_and_a_conflict(client):
    resp = await client.post("/api/dev-collab/simulate-demo-conflict")
    assert resp.status_code == 200
    body = resp.json()
    assert "conflict_id" in body
    assert body["risk_score"] > 0

    sessions = (await client.get("/api/dev-collab/active-sessions")).json()
    assert len(sessions) == 2

    conflicts = (await client.get("/api/dev-collab/conflicts")).json()
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "predicted"


async def test_suggest_resolution_marks_conflict_resolved_and_creates_commit(client):
    sim = await client.post("/api/dev-collab/simulate-demo-conflict")
    conflict_id = sim.json()["conflict_id"]

    resp = await client.post(f"/api/dev-collab/conflicts/{conflict_id}/suggest-resolution")
    assert resp.status_code == 200
    assert resp.json()["suggestion"]

    conflicts = (await client.get("/api/dev-collab/conflicts")).json()
    resolved = next(c for c in conflicts if c["id"] == conflict_id)
    assert resolved["status"] == "resolved"
    assert resolved["ai_suggestion"]

    commits = (await client.get("/api/dev-collab/commits")).json()
    assert len(commits) == 1
    assert commits[0]["had_conflict"] is True


async def test_suggest_resolution_404_for_missing_conflict(client):
    resp = await client.post("/api/dev-collab/conflicts/9999/suggest-resolution")
    assert resp.status_code == 404


async def test_start_and_end_edit_session(client):
    start = await client.post(
        "/api/dev-collab/edit-session/start",
        json={"developer_name": "Test Dev", "file_path": "app.py", "function_name": "main"},
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    active = (await client.get("/api/dev-collab/active-sessions")).json()
    assert len(active) == 1

    end = await client.post(f"/api/dev-collab/edit-session/{session_id}/end")
    assert end.status_code == 200

    active_after = (await client.get("/api/dev-collab/active-sessions")).json()
    assert len(active_after) == 0
