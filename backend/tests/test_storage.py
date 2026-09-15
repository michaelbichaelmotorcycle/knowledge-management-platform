from app.db.database import SessionLocal
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.user import User


def test_document_chunk_stores_and_retrieves_embedding():
    db = SessionLocal()

    try:
        user = User(
            username="storage-test-user",
            hashed_password="test-hash",
            role="user",
            disabled=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        document = Document(
            title="storage-test.txt",
            content="Test document content.",
            owner_id=user.id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        embedding = [0.1] * 384

        chunk = DocumentChunk(
            doc_id=document.doc_id,
            content="Test chunk content.",
            embedding=embedding,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        stored_chunk = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.chunk_id == chunk.chunk_id)
            .first()
        )

        assert stored_chunk is not None
        assert stored_chunk.content == "Test chunk content."
        assert stored_chunk.doc_id == document.doc_id
        assert len(stored_chunk.embedding) == 384

        for actual, expected in zip(
            stored_chunk.embedding,
            embedding,
        ):
            assert abs(actual - expected) < 0.000001

    finally:
        db.query(DocumentChunk).delete(
            synchronize_session=False
        )
        db.query(Document).delete(
            synchronize_session=False
        )
        db.query(User).filter(
            User.username == "storage-test-user"
        ).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()
