from typing import List

from pydantic import BaseModel

from app.schemas.scan import ScanHistoryItem


class CommunityTrend(BaseModel):
    title: str
    detail: str
    change_pct: float


class DashboardOut(BaseModel):
    overall_safety_score: int
    threats_neutralized_week: int
    system_health: str
    recent_scans: List[ScanHistoryItem]
    community_trends: List[CommunityTrend]
