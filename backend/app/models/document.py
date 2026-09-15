from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
