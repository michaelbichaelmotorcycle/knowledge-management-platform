"""
Integration tests for the RAG pipeline (backlog IDs 11, 13).

The LLM call (generate_answer) is MOCKED here — Gemini's free tier has a
strict daily request limit, and CI can run many times per day. Mocking
keeps these tests fast, free, and deterministic, while still exercising
real prompt assembly and context retrieval logic.

Real-API verification is a separate manual step before the Alpha demo
(see USE_MOCK_LLM in ci.yml).
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.user import User
from app.services.auth import get_password_hash
from app.services.embedding import generate_embeddings
from app.services.llm import generate_answer
from app.services.rag import build_prompt, retrieve_context


@pytest.fixture(scope="module")
def engine():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def make_user(db, username, role="user"):
    user = User(
        username=username,
        hashed_password=get_password_hash("test-password"),
        role=role,
        disabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_document_with_chunk(db, owner, filename, content):
    document = Document(
        filename=filename,
        content=content,
        owner_id=owner.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    embedding = generate_embeddings([content])[0]
    chunk = DocumentChunk(
        document_id=document.id,
        content=content,
        embedding=embedding,
    )
    db.add(chunk)
    db.commit()

    return document, chunk


# ---------------------------------------------------------------------
# build_prompt — pure function, no external calls, no mocking needed
# ---------------------------------------------------------------------

def test_build_prompt_includes_context_and_question():
    context = [
        {
            "content": "Employees get 15 vacation days per year.",
            "document_id": 1,
            "filename": "vacation_policy.txt",
        }
    ]

    prompt = build_prompt("How many vacation days do I get?", context)

    assert "Employees get 15 vacation days per year." in prompt
    assert "How many vacation days do I get?" in prompt
    assert "only the information contained in the" in prompt


def test_build_prompt_handles_empty_context():
    prompt = build_prompt("Any question?", [])

    assert "Any question?" in prompt
    # Should still produce a valid prompt string, not crash, even with
    # nothing retrieved.
    assert isinstance(prompt, str)
    assert len(prompt) > 0


# ---------------------------------------------------------------------
# retrieve_context — real DB, real embeddings, no LLM call involved
# ---------------------------------------------------------------------

def test_retrieve_context_attaches_filename(db):
    user = make_user(db, "rag_test_user")
    _, chunk = make_document_with_chunk(
        db,
        user,
        "remote_work_policy.txt",
        "Employees may work remotely up to three days per week.",
    )

    context = retrieve_context(
        "How many remote work days are allowed?",
        db,
        user,
        limit=5,
    )

    assert len(context) > 0
    matching = [c for c in context if c["document_id"] == chunk.document_id]
    assert matching
    assert matching[0]["filename"] == "remote_work_policy.txt"


def test_retrieve_context_returns_empty_list_when_no_match(db):
    user = make_user(db, "rag_test_user_2")

    # No documents created for this user at all.
    context = retrieve_context(
        "What is the meaning of life?",
        db,
        user,
        limit=5,
    )

    assert context == []


# ---------------------------------------------------------------------
# generate_answer — LLM call is mocked to avoid real API usage in CI
# ---------------------------------------------------------------------

@patch("app.services.llm.client")
def test_generate_answer_returns_mocked_text(mock_client):
    mock_response = MagicMock()
    mock_response.text = "Employees get 15 vacation days per year."
    mock_client.models.generate_content.return_value = mock_response

    result = generate_answer("Some prompt text")

    assert result == "Employees get 15 vacation days per year."
    mock_client.models.generate_content.assert_called_once()


@patch("app.services.llm.client")
def test_generate_answer_passes_prompt_to_model(mock_client):
    mock_response = MagicMock()
    mock_response.text = "Mocked answer"
    mock_client.models.generate_content.return_value = mock_response

    generate_answer("What is the vacation policy?")

    _, call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs["contents"] == "What is the vacation policy?"


# ---------------------------------------------------------------------
# Full pipeline — retrieval + prompt assembly + mocked LLM together
# ---------------------------------------------------------------------

@patch("app.services.llm.client")
def test_full_rag_pipeline_with_mocked_llm(mock_client, db):
    mock_response = MagicMock()
    mock_response.text = (
        "Employees may work remotely up to three days per week."
    )
    mock_client.models.generate_content.return_value = mock_response

    user = make_user(db, "rag_pipeline_user")
    make_document_with_chunk(
        db,
        user,
        "remote_work_policy.txt",
        "Employees may work remotely up to three days per week.",
    )

    context = retrieve_context(
        "How many remote work days are allowed?",
        db,
        user,
        limit=5,
    )
    assert context

    prompt = build_prompt("How many remote work days are allowed?", context)
    answer = generate_answer(prompt)

    assert answer == "Employees may work remotely up to three days per week."
