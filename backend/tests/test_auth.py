import pytest

pytestmark = pytest.mark.skip(reason="waiting on auth module (track 2) — unskip once /api/auth exists")


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/documents")
    assert response.status_code == 401


def test_login_returns_jwt(client):
    response = client.post("/api/auth/login", json={"username": "test", "password": "test"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_token_rejected(client):
    response = client.get("/api/documents", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401