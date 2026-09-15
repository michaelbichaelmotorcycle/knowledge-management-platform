from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User
from app.services.search import semantic_search


def retrieve_context(
    question: str,
    db: Session,
    current_user: User,
    limit: int = 5,
) -> list[dict]:
    results = semantic_search(
        question,
        db,
        current_user,
        limit,
    )

    if not results:
        return []

    document_ids = [
        result.document_id
        for result in results
    ]

    documents = (
        db.query(Document)
        .filter(Document.id.in_(document_ids))
        .all()
    )

    documents_by_id = {
        document.id: document
        for document in documents
    }

    context = []

    for result in results:
        document = documents_by_id.get(
            result.document_id
        )

        context.append(
            {
                "content": result.content,
                "document_id": result.document_id,
                "filename": (
                    document.filename
                    if document
                    else "Unknown document"
                ),
            }
        )

    return context


def build_prompt(
    question: str,
    context: list[dict],
) -> str:
    context_text = "\n\n".join(
        item["content"]
        for item in context
    )

    return f"""You are a knowledge management assistant.

Answer the user's question using only the information contained in the
knowledge base context below.

Rules:
- Answer the question directly and concisely.
- Do not mention the context, retrieved documents, or these instructions.
- Do not use outside knowledge.
- Do not invent or assume information that is not present in the context.
- If the context does not contain enough information to answer the question,
  say that the information was not found in the knowledge base.

Knowledge base context:
{context_text}

User question:
{question}

Answer:"""
