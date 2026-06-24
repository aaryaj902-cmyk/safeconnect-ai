from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import (
    ProfileScanRequest, MessageScanRequest, JobScanRequest, LinkScanRequest,
    ScanResult, ScanHistoryItem,
)
from app.security import get_current_user
from app.services import fraud_engine

router = APIRouter(prefix="/api/scan", tags=["scan"])


def _persist_scan(
    db: Session,
    user: Optional[User],
    scan_type: str,
    subject_name: Optional[str],
    subject_company: Optional[str],
    input_summary: str,
    raw_input: dict,
    result: dict,
) -> Scan:
    scan = Scan(
        user_id=user.id if user else None,
        scan_type=scan_type,
        subject_name=subject_name,
        subject_company=subject_company,
        input_summary=input_summary[:500] if input_summary else None,
        raw_input=raw_input,
        trust_score=result["trust_score"],
        risk_level=result["risk_level"],
        verdict_label=result["verdict_label"],
        summary=result["summary"],
        signals=result["signals"],
        reasoning=result["reasoning"],
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.post("/profile", response_model=ScanResult)
def scan_profile(
    payload: ProfileScanRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    result = fraud_engine.analyze_profile(
        db, payload.full_name, payload.company_name, payload.linkedin_url or ""
    )
    scan = _persist_scan(
        db, current_user, "profile",
        subject_name=payload.full_name, subject_company=payload.company_name,
        input_summary=f"{payload.full_name} @ {payload.company_name}",
        raw_input=payload.model_dump(), result=result,
    )
    return scan


@router.post("/message", response_model=ScanResult)
def scan_message(
    payload: MessageScanRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    result = fraud_engine.analyze_message(payload.message_text, payload.sender_email or "")
    scan = _persist_scan(
        db, current_user, "message",
        subject_name=payload.sender_email or "Unknown Sender", subject_company=None,
        input_summary=payload.message_text,
        raw_input=payload.model_dump(), result=result,
    )
    return scan


@router.post("/job", response_model=ScanResult)
def scan_job(
    payload: JobScanRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    result = fraud_engine.analyze_job(
        db, payload.job_title, payload.company_name, payload.description or "",
        payload.salary_range or "", payload.location or "",
    )
    scan = _persist_scan(
        db, current_user, "job",
        subject_name=payload.job_title, subject_company=payload.company_name,
        input_summary=f"{payload.job_title} @ {payload.company_name}",
        raw_input=payload.model_dump(), result=result,
    )
    return scan


@router.post("/link", response_model=ScanResult)
def scan_link(
    payload: LinkScanRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    result = fraud_engine.analyze_link(payload.url)
    scan = _persist_scan(
        db, current_user, "link",
        subject_name=payload.url, subject_company=None,
        input_summary=payload.url,
        raw_input=payload.model_dump(), result=result,
    )
    return scan


@router.get("/history", response_model=List[ScanHistoryItem])
def scan_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    query = db.query(Scan)
    if current_user:
        query = query.filter(Scan.user_id == current_user.id)
    return query.order_by(Scan.created_at.desc()).limit(limit).all()


@router.get("/{scan_id}", response_model=ScanResult)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return scan
