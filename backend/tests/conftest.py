import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("USE_MOCK_LLM", "true")

from app.main import app

TEST_USER = {"username": "testuser", "password": "testpass"}


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Valid JWT for the seeded test user."""
    response = client.post("/auth/token", data=TEST_USER)
    assert response.status_code == 200, f"login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_llm_response():
    return {
        "answer": "This is a mocked answer for testing purposes.",
        "sources": [{"document_id": 1, "document": "test.txt", "content": "..."}],
    }


@pytest.fixture
def mock_embedding():
    """Deterministic fake embedding — matches Vector(384) column."""
    return [0.01] * 384