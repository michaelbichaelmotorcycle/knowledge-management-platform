from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.user import User
from app.services.embedding import generate_embeddings

MAX_DISTANCE = 0.70


def semantic_search(
    question: str,
    db: Session,
    current_user: User,
    limit: int = 5,
) -> list[DocumentChunk]:
    query_embedding = generate_embeddings([question])[0]

    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    )

    query = (
        db.query(DocumentChunk)
        .join(
            Document,
            DocumentChunk.document_id == Document.id,
        )
        .filter(DocumentChunk.embedding.isnot(None))
        .filter(distance <= MAX_DISTANCE)
    )

    # Admins can search all documents.
    # Regular users can only search their own documents.
    if current_user.role != "admin":
        query = query.filter(
            Document.owner_id == current_user.id
        )

    return (
        query
        .order_by(distance)
        .limit(limit)
        .all()
    )
