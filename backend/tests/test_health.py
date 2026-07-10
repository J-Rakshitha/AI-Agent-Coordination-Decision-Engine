async def test_health_check(client):
    resp = await client.get("/api/system/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_root_endpoint(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "modules" in body
    assert "dev-collaboration" in body["modules"]
    assert "aiops-incident-response" in body["modules"]
