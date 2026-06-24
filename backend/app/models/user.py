import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(String, default="free")  # free | pro
    safety_score = Column(Integer, default=82)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    scans = relationship("Scan", back_populates="owner", cascade="all, delete-orphan")
    reports = relationship("ScamReport", back_populates="reporter", cascade="all, delete-orphan")
