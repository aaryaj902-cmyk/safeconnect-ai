from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scan import Scan
from app.models.user import User
from app.schemas.dashboard import DashboardOut, CommunityTrend
from app.schemas.scan import ScanHistoryItem
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

STATIC_COMMUNITY_TRENDS = [
    CommunityTrend(
        title="Fake 'Upwork' Payments",
        detail="Scammers sending PDF 'contracts' with malware-embedded macros.",
        change_pct=12.0,
    ),
    CommunityTrend(
        title="LinkedIn Ghosting Phish",
        detail="Requests for 'Identity Verification' using external non-secure links.",
        change_pct=8.0,
    ),
    CommunityTrend(
        title="Remote Setup Scams",
        detail="Fraudulent tech equipment reimbursement checks via crypto.",
        change_pct=2.0,
    ),
]


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    query = db.query(Scan)
    if current_user:
        query = query.filter(Scan.user_id == current_user.id)
    recent_scans = query.order_by(Scan.created_at.desc()).limit(5).all()

    threats_neutralized = query.filter(Scan.risk_level == "high_risk").count()

    safety_score = current_user.safety_score if current_user else 82
    if safety_score >= 70:
        health = "Excellent"
    elif safety_score >= 40:
        health = "Fair"
    else:
        health = "At Risk"

    return DashboardOut(
        overall_safety_score=safety_score,
        threats_neutralized_week=threats_neutralized,
        system_health=health,
        recent_scans=[ScanHistoryItem.model_validate(s) for s in recent_scans],
        community_trends=STATIC_COMMUNITY_TRENDS,
    )
