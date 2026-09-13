import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("USE_MOCK_LLM", "true")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def mock_llm_response():
    """Canned LLM response used whenever USE_MOCK_LLM=true."""
    return {
        "answer": "This is a mocked answer for testing purposes.",
        "sources": [{"chunk_id": "test-chunk-1", "score": 0.92}],
    }


@pytest.fixture
def mock_embedding():
    """Deterministic fake embedding vector (match your pgvector column dim)."""
    return [0.01] * 1536