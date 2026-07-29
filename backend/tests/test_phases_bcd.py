"""Tests for Phase B monitoring and Phase C auth."""


async def test_monitoring_status_empty(client):
    resp = await client.get("/api/monitoring/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert len(data["services"]) == 2
    assert data["monitoring_enabled"] is False  # disabled in test conftest


async def test_auth_login_demo_user(client):
    resp = await client.post("/api/auth/login", json={
        "email": "priya@infosys.com",
        "password": "demo123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["full_name"] == "Priya Sharma"


async def test_auth_me_requires_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_auth_me_with_token(client):
    login = await client.post("/api/auth/login", json={
        "email": "admin@infosys.com",
        "password": "admin123",
    })
    token = login.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


async def test_list_demo_users(client):
    resp = await client.get("/api/auth/users")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3
