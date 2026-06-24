import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Scan(Base):
    """
    Unified scan record. Covers all three scan types shown across the
    frontend screens: 'profile' (recruiter verification), 'message'
    (AI message/phishing scanner), and 'job' (job authenticity checker).
    """
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # nullable: allow anonymous scans

    scan_type = Column(String, nullable=False)  # 'profile' | 'message' | 'job' | 'link'

    # Common display fields
    subject_name = Column(String, nullable=True)      # recruiter name / job title / sender
    subject_company = Column(String, nullable=True)    # company name
    input_summary = Column(Text, nullable=True)         # short preview of what was scanned

    # Raw inputs (kept for audit / re-analysis)
    raw_input = Column(JSON, nullable=True)

    # Results
    trust_score = Column(Integer, nullable=False)        # 0-100, higher = safer
    risk_level = Column(String, nullable=False)           # 'safe' | 'verify' | 'high_risk'
    verdict_label = Column(String, nullable=False)        # e.g. "Verified Communication"
    summary = Column(Text, nullable=True)
    signals = Column(JSON, nullable=True)                 # list of {icon, label, detail, status}
    reasoning = Column(JSON, nullable=True)                # list of {title, detail} XAI cards

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="scans")
