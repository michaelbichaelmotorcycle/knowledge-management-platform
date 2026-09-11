from sqlalchemy import Column, Integer, String, Boolean
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
        default="user",
    )

    disabled = Column(
        Boolean,
        nullable=False,
        default=False,
    )
