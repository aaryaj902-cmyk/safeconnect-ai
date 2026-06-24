import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    reporter_id = Column(String, ForeignKey("users.id"), nullable=True)

    scammer_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    violation_type = Column(String, nullable=False)  # e.g. Resume Theft, Advance Fee, Phishing
    risk_level = Column(String, nullable=False, default="suspicious")  # suspicious | high_risk
    description = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    ai_reasoning = Column(Text, nullable=True)

    confirmations = Column(Integer, default=1)  # "Reported by N users" counter
    status = Column(String, default="active")    # active | resolved

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reporter = relationship("User", back_populates="reports")
