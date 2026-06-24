import csv
import os
import random

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.scam_report import ScamReport

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(THIS_DIR), "data")
COMPANIES_CSV = os.path.join(DATA_DIR, "companies.csv")

SEED_REPORTS = [
    {
        "scammer_name": "John Recruiter",
        "company_name": "Global Talent Solutions Inc.",
        "violation_type": "Resume Theft",
        "risk_level": "high_risk",
        "description": "Collected resumes under the guise of a job application, then reused candidate "
                        "personal details across fake LinkedIn outreach campaigns.",
        "ai_reasoning": "Matches signature of automated bulk identity harvesting campaigns detected "
                         "across LinkedIn & Indeed.",
        "confirmations": 43,
    },
    {
        "scammer_name": "Amanda L. Tech",
        "company_name": "Independent Contractor",
        "violation_type": "Advance Fee Fraud",
        "risk_level": "high_risk",
        "description": "Requested an upfront 'equipment deposit' before the first day of work; victims "
                        "never received equipment or further contact.",
        "ai_reasoning": "High correlation with 'Check Scam' patterns; multiple victims report paying for "
                         "equipment before start date.",
        "confirmations": 29,
    },
    {
        "scammer_name": "Staffing Today",
        "company_name": "Agency Profile",
        "violation_type": "Phishing Link Distribution",
        "risk_level": "suspicious",
        "description": "Sent interview invitation links pointing to credential-harvesting pages "
                        "disguised as video-interview platforms.",
        "ai_reasoning": "AI flagged anomalous URL structures in interview invitations. Domains lack SSL "
                         "and registration age < 30 days.",
        "confirmations": 112,
    },
    {
        "scammer_name": "Global Hire Express",
        "company_name": "Global Hire Express",
        "violation_type": "Advance Fee Fraud",
        "risk_level": "high_risk",
        "description": "Requested a $150 'registration fee' via gift card before granting access to a "
                        "'training portal' that never materialized.",
        "ai_reasoning": "Payment-via-gift-card requests are a near-certain indicator of advance fee fraud.",
        "confirmations": 67,
    },
    {
        "scammer_name": "QuickJobs International",
        "company_name": "QuickJobs International",
        "violation_type": "Identity Theft",
        "risk_level": "high_risk",
        "description": "Requested SSN and a copy of a government ID before any formal offer was extended.",
        "ai_reasoning": "Premature sensitive-document requests strongly correlate with identity theft schemes.",
        "confirmations": 38,
    },
    {
        "scammer_name": "EasyHire Worldwide",
        "company_name": "EasyHire Worldwide",
        "violation_type": "Check Fraud",
        "risk_level": "suspicious",
        "description": "Sent an oversized cashier's check and instructed the candidate to deposit it and "
                        "wire back the difference for 'equipment purchase'.",
        "ai_reasoning": "Classic overpayment / fake check scam pattern identified by the AI.",
        "confirmations": 21,
    },
]


def seed_companies(db: Session) -> int:
    existing = db.query(Company).count()
    if existing > 0:
        return 0
    if not os.path.exists(COMPANIES_CSV):
        return 0
    count = 0
    with open(COMPANIES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Company(
                name=row["name"],
                industry=row.get("industry") or None,
                headquarters=row.get("headquarters") or None,
                official_domain=row.get("official_domain") or None,
                founded_year=int(row["founded_year"]) if row.get("founded_year") else None,
                trust_status=row.get("trust_status", "unknown"),
                trust_score=int(row.get("trust_score", 50)),
                employee_count=int(row["employee_count"]) if row.get("employee_count") else None,
                report_count=int(row.get("report_count", 0)),
                notes=row.get("notes") or None,
            ))
            count += 1
    db.commit()
    return count


def seed_scam_reports(db: Session) -> int:
    existing = db.query(ScamReport).count()
    if existing > 0:
        return 0
    count = 0
    for item in SEED_REPORTS:
        db.add(ScamReport(**item))
        count += 1
    db.commit()
    return count


def run_all_seeds(db: Session) -> dict:
    return {
        "companies_seeded": seed_companies(db),
        "reports_seeded": seed_scam_reports(db),
    }
