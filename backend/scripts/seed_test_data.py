"""
Seeds a small, known dataset into the database for CI integration tests
(retrieval, rag-llm, e2e-smoke jobs). Safe to run multiple times against
a fresh CI database — it creates the schema if missing.

Usage: python scripts/seed_test_data.py
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.user import User
from app.services.auth import get_password_hash
from app.services.embedding import generate_embeddings

# A small set of representative documents covering distinct topics,
# used by CI tests and the ~8-10 representative question set (NFR-12).
SEED_DOCUMENTS = [
    {
        "filename": "vacation_policy.txt",
        "content": "Employees receive 15 days of paid vacation per year, "
        "accrued monthly starting on their hire date.",
    },
    {
        "filename": "onboarding_checklist.txt",
        "content": "New hires complete a checklist that includes laptop "
        "setup, badge issuance, and benefits enrollment within the first week.",
    },
    {
        "filename": "budget_review.txt",
        "content": "The quarterly budget review takes place every March, "
        "June, September, and December, led by the finance team.",
    },
]


def seed():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        admin = User(
            username="ci_admin",
            hashed_password=get_password_hash("ci-test-password"),
            role="admin",
            disabled=False,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        for doc_data in SEED_DOCUMENTS:
            document = Document(
                filename=doc_data["filename"],
                content=doc_data["content"],
                owner_id=admin.id,
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            embedding = generate_embeddings([doc_data["content"]])[0]
            chunk = DocumentChunk(
                document_id=document.id,
                content=doc_data["content"],
                embedding=embedding,
            )
            db.add(chunk)
            db.commit()

        print(f"Seeded {len(SEED_DOCUMENTS)} documents for CI testing.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
