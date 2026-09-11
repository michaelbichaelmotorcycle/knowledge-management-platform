from sqlalchemy import Column, Integer, Text, String, ForeignKey
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    filename = Column(
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
