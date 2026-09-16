import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("USE_MOCK_LLM", "true")

from app.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


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