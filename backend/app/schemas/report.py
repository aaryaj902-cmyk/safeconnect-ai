from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScamReportCreate(BaseModel):
    scammer_name: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    violation_type: str = Field(..., min_length=1)
    risk_level: str = "suspicious"  # suspicious | high_risk
    description: Optional[str] = None
    evidence: Optional[str] = None


class ScamReportOut(BaseModel):
    id: str
    scammer_name: str
    company_name: Optional[str] = None
    violation_type: str
    risk_level: str
    description: Optional[str] = None
    ai_reasoning: Optional[str] = None
    confirmations: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerStats(BaseModel):
    total_scams_blocked: int
    active_reports: int
    trust_protector_score: float
    monthly_growth_pct: float
