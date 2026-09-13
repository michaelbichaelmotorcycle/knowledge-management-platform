"""
Integration tests for semantic_search (backlog ID 10).

These tests use a real database connection (settings.database_url) and
real embeddings from the local embedding model — no mocking needed here,
since embedding generation is local/free, unlike the LLM call in rag-llm.

Each test creates its own isolated data and cleans up after itself so
tests can run in any order without interfering with each other.
"""

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
from app.services.search import semantic_search


@pytest.fixture(scope="module")
def engine():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield engine

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


def test_relevant_chunk_returned_for_matching_query(db):
    user = make_user(db, "retrieval_user_1")
    _, chunk = make_document_with_chunk(
        db,
        user,
        "vacation_policy.txt",
        "Employees receive 15 days of paid vacation per year.",
    )

    results = semantic_search(
        "How many vacation days do employees get?",
        db,
        user,
        limit=5,
    )

    result_ids = [r.id for r in results]
    assert chunk.id in result_ids


def test_regular_user_only_sees_own_documents(db):
    alice = make_user(db, "retrieval_alice")
    bob = make_user(db, "retrieval_bob")

    _, alice_chunk = make_document_with_chunk(
        db,
        alice,
        "alice_notes.txt",
        "The onboarding checklist includes setting up a laptop and badge.",
    )
    make_document_with_chunk(
        db,
        bob,
        "bob_notes.txt",
        "The onboarding checklist includes setting up a laptop and badge.",
    )

    results = semantic_search(
        "What is on the onboarding checklist?",
        db,
        alice,
        limit=10,
    )

    result_ids = [r.id for r in results]
    assert alice_chunk.id in result_ids
    for result in results:
        owning_document = (
            db.query(Document)
            .filter(Document.id == result.document_id)
            .first()
        )
        assert owning_document.owner_id == alice.id

def test_admin_sees_all_documents(db):
    admin = make_user(db, "retrieval_admin", role="admin")
    other_user = make_user(db, "retrieval_other_user")

    _, other_chunk = make_document_with_chunk(
        db,
        other_user,
        "budget.txt",
        "The quarterly budget review happens every March.",
    )

    results = semantic_search(
        "When is the quarterly budget review?",
        db,
        admin,
        limit=10,
    )

    result_ids = [r.id for r in results]
    assert other_chunk.id in result_ids


def test_unrelated_query_does_not_match_irrelevant_chunk(db):
    user = make_user(db, "retrieval_user_2")
    _, chunk = make_document_with_chunk(
        db,
        user,
        "recipe.txt",
        "This recipe requires flour, sugar, eggs, and butter.",
    )

    results = semantic_search(
        "What is the process for filing a tax extension?",
        db,
        user,
        limit=5,
    )

    result_ids = [r.id for r in results]
    assert chunk.id not in result_ids

def test_semantic_search_respects_result_limit(db):
    user = make_user(db, "retrieval_limit_user_final")

    make_document_with_chunk(
        db,
        user,
        "vacation_policy_1.txt",
        "Employees receive 15 days of paid vacation each year.",
    )
    make_document_with_chunk(
        db,
        user,
        "vacation_policy_2.txt",
        "Employees can request vacation days through the HR portal.",
    )
    make_document_with_chunk(
        db,
        user,
        "vacation_policy_3.txt",
        "Unused vacation days may be carried over to the next year.",
    )

    results = semantic_search(
        "What is the company vacation policy?",
        db,
        user,
        limit=2,
    )

    assert len(results) <= 2