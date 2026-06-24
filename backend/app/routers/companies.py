from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=List[CompanyOut])
def search_companies(
    q: Optional[str] = Query(None, description="Search by company name"),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f"%{q}%"))
    if status_filter:
        query = query.filter(Company.trust_status == status_filter)
    return query.order_by(Company.trust_score.desc()).limit(limit).all()


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Company not found.")
    return company
