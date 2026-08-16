from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from backend.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class Notice(Base):

    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False
    )

    title = Column(String)

    notice_type = Column(String)

    deadline = Column(String)

    location = Column(String)

    summary = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )