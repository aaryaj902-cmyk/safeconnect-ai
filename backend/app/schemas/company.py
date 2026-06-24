from typing import Optional

from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    official_domain: Optional[str] = None
    founded_year: Optional[int] = None
    trust_status: str
    trust_score: int
    employee_count: Optional[int] = None
    report_count: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True
