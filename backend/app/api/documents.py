from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.user import User
from app.services.auth import (
    get_current_user,
    get_db,
)
from app.services.chunking import chunk_text
from app.services.embedding import generate_embeddings
from app.services.llm import generate_answer
from app.services.rag import (
    build_prompt,
    retrieve_context,
)
from app.services.search import semantic_search

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    content = await file.read()

    if file.filename.lower().endswith(".pdf"):
        from app.services.pdf_extraction import (
            extract_text_from_pdf,
        )

        text_content = extract_text_from_pdf(
            content
        )

    elif file.filename.lower().endswith(".txt"):
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Only UTF-8 text files are supported",
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are supported",
        )

    document = Document(
        title=file.filename,
        content=text_content,
        owner_id=current_user.id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = chunk_text(text_content)
    embeddings = generate_embeddings(chunks)

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        document_chunk = DocumentChunk(
            doc_id=document.doc_id,
            content=chunk,
            embedding=embedding,
        )

        db.add(document_chunk)

    db.commit()

    return {
        "doc_id": document.doc_id,
        "title": document.title,
        "chunks_created": len(chunks),
        "message": "Document uploaded successfully",
    }


@router.get("")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document)

    if current_user.role != "admin":
        query = query.filter(
            Document.owner_id == current_user.id
        )

    documents = (
        query
        .order_by(Document.doc_id.desc())
        .all()
    )

    owner_ids = [document.owner_id for document in documents]
    owners = (
        db.query(User)
        .filter(User.id.in_(owner_ids))
        .all()
    )
    usernames_by_id = {owner.id: owner.username for owner in owners}

    return [
        {
            "doc_id": document.doc_id,
            "title": document.title,
            "owner_id": document.owner_id,
            "owner_username": usernames_by_id.get(
                document.owner_id, "Unknown"
            ),
        }
        for document in documents
    ]

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Document)
        .filter(Document.doc_id == document_id)
    )

    if current_user.role != "admin":
        query = query.filter(
            Document.owner_id == current_user.id
        )

    document = query.first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    db.query(DocumentChunk).filter(
        DocumentChunk.doc_id == document_id
    ).delete(
        synchronize_session=False
    )

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "doc_id": document_id,
    }


@router.get("/search")
def search_documents(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = semantic_search(
        query,
        db,
        current_user,
        limit,
    )

    return [
        {
            "chunk_id": result.chunk_id,
            "doc_id": result.doc_id,
            "content": result.content,
        }
        for result in results
    ]


@router.get("/ask")
def ask_question(
    question: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = retrieve_context(
        question,
        db,
        current_user,
        5,
    )

    if not context:
        return {
            "answer": (
                "The information was not found "
                "in the knowledge base."
            ),
            "sources": [],
        }

    prompt = build_prompt(
        question,
        context,
    )

    answer = generate_answer(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "doc_id": item["doc_id"],
                "title": item["title"],
                "content": item["content"],
            }
            for item in context
        ],
    }
