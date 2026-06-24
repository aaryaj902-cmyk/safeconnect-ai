from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Request payloads ----------

class ProfileScanRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    linkedin_url: Optional[str] = None


class MessageScanRequest(BaseModel):
    message_text: str = Field(..., min_length=1)
    sender_email: Optional[str] = None


class JobScanRequest(BaseModel):
    job_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    salary_range: Optional[str] = None
    location: Optional[str] = None


class LinkScanRequest(BaseModel):
    url: str = Field(..., min_length=3)


# ---------- Response payloads ----------

class Signal(BaseModel):
    icon: str
    label: str
    detail: str
    status: str  # 'positive' | 'negative' | 'neutral'


class ReasoningCard(BaseModel):
    title: str
    detail: str


class ScanResult(BaseModel):
    id: str
    scan_type: str
    subject_name: Optional[str] = None
    subject_company: Optional[str] = None
    trust_score: int
    risk_level: str          # safe | verify | high_risk
    verdict_label: str
    summary: str
    signals: List[Signal] = []
    reasoning: List[ReasoningCard] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ScanHistoryItem(BaseModel):
    id: str
    scan_type: str
    subject_name: Optional[str] = None
    subject_company: Optional[str] = None
    trust_score: int
    risk_level: str
    verdict_label: str
    created_at: datetime

    class Config:
        from_attributes = True
