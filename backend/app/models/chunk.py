from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer, Text

from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
