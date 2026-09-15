"""
End-to-end smoke test (backlog IDs 12, 15).

Exercises the real HTTP flow: login -> ask a question -> receive a
grounded answer with source attribution. Relies on the dataset already
seeded by scripts/seed_test_data.py (run as a prior CI step), rather
than creating its own data.

The LLM call is mocked (same reasoning as test_rag_integration.py) —
this test is verifying the PIPELINE wiring end-to-end, not Gemini's
actual output quality, and it protects the team's limited free-tier
API quota.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from google.genai.errors import APIError

from app.main import app

client = TestClient(app)

SEED_USERNAME = "ci_admin"
SEED_PASSWORD = "ci-test-password"


@pytest.fixture(scope="module")
def auth_headers():
    response = client.post(
        "/auth/token",
        data={
            "username": SEED_USERNAME,
            "password": SEED_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Representative questions (NFR-12), each mapped to one of the three
# documents created by seed_test_data.py.
REPRESENTATIVE_QUESTIONS = [
    {
        "question": "How many vacation days do employees get per year?",
        "expected_title": "vacation_policy.txt",
        "mocked_answer": "Employees receive 15 days of paid vacation per year.",
    },
    {
        "question": "What does the onboarding checklist include?",
        "expected_title": "onboarding_checklist.txt",
        "mocked_answer": (
            "The onboarding checklist includes laptop setup, badge "
            "issuance, and benefits enrollment."
        ),
    },
    {
        "question": "When does the quarterly budget review happen?",
        "expected_title": "budget_review.txt",
        "mocked_answer": (
            "The quarterly budget review happens every March, June, "
            "September, and December."
        ),
    },
]


@pytest.mark.parametrize("case", REPRESENTATIVE_QUESTIONS)
@patch("app.services.llm.client")
def test_representative_question_returns_grounded_answer_with_source(
    mock_client, case, auth_headers
):
    mock_response = MagicMock()
    mock_response.text = case["mocked_answer"]
    mock_client.models.generate_content.return_value = mock_response

    response = client.get(
        "/documents/ask",
        params={"question": case["question"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["answer"] == case["mocked_answer"]
    assert len(data["sources"]) > 0

    source_titles = [s["title"] for s in data["sources"]]
    assert case["expected_title"] in source_titles


@patch("app.services.llm.client")
def test_unrelated_question_returns_not_found_without_calling_llm(
    mock_client, auth_headers
):
    response = client.get(
        "/documents/ask",
        params={"question": "What is the recipe for a chocolate souffle?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["sources"] == []
    assert "not found" in data["answer"].lower()
    # No context was retrieved, so the LLM should never have been called
    # (matches the "no relevant information found" behavior, NFR-16).
    mock_client.models.generate_content.assert_not_called()


def test_ask_without_auth_is_rejected():
    response = client.get(
        "/documents/ask",
        params={"question": "How many vacation days do I get?"},
    )

    assert response.status_code in (401, 403)

@patch("app.api.documents.generate_answer")
def test_llm_failure_returns_service_unavailable(
    mock_generate_answer,
    auth_headers,
):
    mock_generate_answer.side_effect = APIError(
        503,
        {"message": "LLM service unavailable"},
    )

    response = client.get(
        "/documents/ask",
        params={
            "question": "How many vacation days do employees get?"
        },
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The AI service is temporarily unavailable. "
        "Please try again later."
    )

def test_empty_question_is_rejected(auth_headers):
    response = client.get(
        "/documents/ask",
        params={"question": ""},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_whitespace_question_is_rejected(auth_headers):
    response = client.get(
        "/documents/ask",
        params={"question": "   "},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."

def test_question_over_max_length_is_rejected(auth_headers):
    response = client.get(
        "/documents/ask",
        params={"question": "a" * 2001},
        headers=auth_headers,
    )

    assert response.status_code == 422