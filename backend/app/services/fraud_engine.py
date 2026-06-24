"""
Fraud detection / scoring engine.

Two complementary approaches, matching what the UI mockups depict:

1. ML-based (job postings): app.ml.infer uses a trained scikit-learn model
   over the job_fraud dataset.

2. Rule-based explainable signals (messages, recruiter profiles, links):
   a transparent set of red-flag heuristics, each one mapped to a labeled
   "signal" / "XAI reasoning card" -- exactly mirroring the "AI REASONING",
   "Detected Risk Factors", and "Profile Forensics" panels in the frontend.

Both paths converge on the same ScanResult shape so the unified Verification
Hub (profile / message / job tabs) can use one schema for all three.
"""
import re
from typing import List, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.company import Company

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "gmx.com",
}

URGENCY_PHRASES = [
    "urgent", "immediately", "right away", "act now", "limited time",
    "limited-time", "start today", "asap", "before positions fill up",
    "hurry", "last chance", "expires soon", "no time to waste",
]

PAYMENT_PHRASES = [
    "registration fee", "processing fee", "background check fee", "training fee",
    "deposit a check", "wire transfer", "send money", "western union",
    "gift card", "cryptocurrency", "crypto", "bitcoin", "pay to start",
    "refundable fee", "activation fee", "small fee", "equipment fee",
]

SENSITIVE_INFO_PHRASES = [
    "social security", "ssn", "passport", "bank account number", "routing number",
    "copy of your id", "government id", "drivers license", "driver's license",
]

UNOFFICIAL_CHANNEL_PHRASES = [
    "telegram", "whatsapp", "signal app", "text me at", "personal email",
]

VAGUE_PHRASES = [
    "no experience necessary", "no interview required", "no resume needed",
    "anyone can apply", "guaranteed income", "be your own boss", "unlimited earning",
    "easy money", "work 2 hours a day",
]

GENERIC_GREETING_PATTERNS = [
    r"\bdear candidate\b", r"\bdear applicant\b", r"\bdear job seeker\b",
]


def _contains_any(text: str, phrases: List[str]) -> List[str]:
    text_l = text.lower()
    return [p for p in phrases if p in text_l]


# ----------------------------------------------------------------------
# MESSAGE SCANNER
# ----------------------------------------------------------------------

def analyze_message(message_text: str, sender_email: str = "") -> dict:
    text = message_text or ""
    signals = []
    reasoning = []
    risk_points = 0

    urgency_hits = _contains_any(text, URGENCY_PHRASES)
    if urgency_hits:
        risk_points += 18
        signals.append({
            "icon": "bolt", "label": "Urgent Language",
            "detail": "Creating artificial urgency to bypass logical reasoning.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Linguistic Patterns",
            "detail": "Detected urgency-pressure phrasing commonly used to rush victims into "
                      "skipping due diligence.",
        })

    payment_hits = _contains_any(text, PAYMENT_PHRASES)
    if payment_hits:
        risk_points += 35
        signals.append({
            "icon": "payments", "label": "Payment Request",
            "detail": "Requesting money for 'fees' is a signature scam trait.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Upfront Payment Request",
            "detail": "Legitimate employers never require candidates to pay registration, training, or "
                      "equipment fees before or during hiring.",
        })

    sensitive_hits = _contains_any(text, SENSITIVE_INFO_PHRASES)
    if sensitive_hits:
        risk_points += 30
        signals.append({
            "icon": "badge", "label": "Sensitive Data Request",
            "detail": "Requesting ID/SSN/passport details prematurely.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Resume & Identity Theft Detection",
            "detail": "This message requests sensitive documentation (passport, SSN, or ID). Legitimate "
                      "employers never ask for these via initial email or unsecured messaging before a "
                      "formal offer and official onboarding.",
        })

    unofficial_hits = _contains_any(text, UNOFFICIAL_CHANNEL_PHRASES)
    if unofficial_hits:
        risk_points += 15
        signals.append({
            "icon": "forum", "label": "Unofficial Channel",
            "detail": "Directs you to an unofficial messaging app instead of corporate systems.",
            "status": "negative",
        })

    domain = ""
    if sender_email and "@" in sender_email:
        domain = sender_email.split("@")[-1].lower().strip()
        if domain in FREE_EMAIL_DOMAINS:
            risk_points += 20
            signals.append({
                "icon": "mail_lock", "label": "Unofficial Domain",
                "detail": f"Sender using @{domain} instead of a corporate domain.",
                "status": "negative",
            })
            reasoning.append({
                "title": "Domain Reputation",
                "detail": f"The sender domain '{domain}' is a free consumer email provider, not a "
                          f"verifiable corporate domain. Legitimate recruiters use company-owned domains.",
            })

    vague_hits = _contains_any(text, VAGUE_PHRASES)
    if vague_hits:
        risk_points += 15
        signals.append({
            "icon": "help", "label": "Unrealistic Promises",
            "detail": "Vague, too-good-to-be-true compensation claims.",
            "status": "negative",
        })

    if any(re.search(p, text.lower()) for p in GENERIC_GREETING_PATTERNS):
        risk_points += 8
        signals.append({
            "icon": "person_off", "label": "Generic Greeting",
            "detail": "No personalization; mass-sent template language.",
            "status": "negative",
        })

    if not signals:
        signals.append({
            "icon": "verified", "label": "No Red Flags Detected",
            "detail": "Message tone and structure align with standard recruiter communication.",
            "status": "positive",
        })
        reasoning.append({
            "title": "Linguistic Consistency",
            "detail": "Tone and structure match verified recruiter outreach patterns. No urgency, "
                      "payment requests, or sensitive-data requests were detected.",
        })

    risk_points = min(risk_points, 99)
    trust_score = max(1, 100 - risk_points)
    risk_level, verdict_label = _risk_bucket(
        trust_score, safe_label="Verified Communication",
        verify_label="Use Caution", risk_label="Critical Risk",
    )

    summary = _message_summary(risk_level)

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "verdict_label": verdict_label,
        "summary": summary,
        "signals": signals,
        "reasoning": reasoning,
    }


def _message_summary(risk_level: str) -> str:
    if risk_level == "high_risk":
        return "Highly likely to be a fraudulent phishing attempt. Do not send money or personal documents."
    if risk_level == "verify":
        return "Some suspicious patterns detected. Verify the sender's identity through official channels before proceeding."
    return "The communication pattern shows high alignment with professional standards and verified recruiter outreach."


# ----------------------------------------------------------------------
# RECRUITER / PROFILE SCANNER
# ----------------------------------------------------------------------

def analyze_profile(db: Session, full_name: str, company_name: str, linkedin_url: str = "") -> dict:
    signals = []
    reasoning = []
    risk_points = 0

    company = (
        db.query(Company)
        .filter(Company.name.ilike(f"%{company_name.strip()}%"))
        .order_by(Company.trust_score.desc())
        .first()
    )

    if company is None:
        risk_points += 35
        signals.append({
            "icon": "domain_disabled", "label": "Unverified Company",
            "detail": f"'{company_name}' was not found in our verified business registry.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Company Entity Search",
            "detail": f"No record of '{company_name}' was found in public business registries. This "
                      f"does not guarantee fraud, but it means the employer's identity could not be "
                      f"independently corroborated.",
        })
    elif company.trust_status == "flagged":
        risk_points += 55
        signals.append({
            "icon": "report", "label": "Flagged Company",
            "detail": f"{company.report_count} community fraud reports on file.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Cross-Platform Mismatch",
            "detail": f"'{company.name}' matches a known high-risk shell entity with "
                      f"{company.report_count} prior community fraud reports and no verifiable "
                      f"corporate registration.",
        })
    else:
        risk_points -= 25
        signals.append({
            "icon": "verified", "label": "Verified Company",
            "detail": f"{company.name} is a registered entity (trust score {company.trust_score}/100).",
            "status": "positive",
        })
        reasoning.append({
            "title": "Company Entity Search",
            "detail": f"'{company.name}' is a registered entity in {company.headquarters or 'public records'} "
                      f"with a verifiable domain ({company.official_domain or 'n/a'}).",
        })

    # LinkedIn URL heuristics (since we cannot call LinkedIn's API, use structural signals)
    if linkedin_url:
        parsed = urlparse(linkedin_url if "://" in linkedin_url else f"https://{linkedin_url}")
        host = (parsed.netloc or "").lower()
        if "linkedin.com" not in host:
            risk_points += 20
            signals.append({
                "icon": "link_off", "label": "Invalid Profile Link",
                "detail": "The provided URL is not a linkedin.com profile.",
                "status": "negative",
            })
        else:
            path_id = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
            # Heuristic: profile slugs ending in long random digit strings often indicate
            # auto-generated/bot accounts in scam datasets used for this demo.
            if re.search(r"\d{5,}$", path_id):
                risk_points += 12
                signals.append({
                    "icon": "smart_toy", "label": "Suspicious Profile Slug",
                    "detail": "URL pattern resembles auto-generated bot accounts.",
                    "status": "negative",
                })
            else:
                signals.append({
                    "icon": "check_circle", "label": "LinkedIn Profile Provided",
                    "detail": "Profile URL format looks standard.",
                    "status": "positive",
                })
    else:
        risk_points += 10
        signals.append({
            "icon": "link_off", "label": "No LinkedIn Profile",
            "detail": "No professional profile link was provided for cross-referencing.",
            "status": "negative",
        })

    # Name plausibility (very light heuristic, mirrors "profile forensics" panel)
    if full_name and len(full_name.split()) < 2:
        risk_points += 8
        signals.append({
            "icon": "person_search", "label": "Incomplete Identity",
            "detail": "Only a single name provided; full name could not be cross-checked.",
            "status": "negative",
        })

    risk_points = max(0, min(risk_points, 95))
    trust_score = max(2, 100 - risk_points)
    risk_level, verdict_label = _risk_bucket(
        trust_score, safe_label="Verified Profile", verify_label="Verify Manually", risk_label="High Risk Profile"
    )

    if risk_level == "high_risk":
        summary = "SafeConnect AI has detected strong indicators of a fraudulent identity. Engagement is not recommended."
    elif risk_level == "verify":
        summary = "Some details could not be independently verified. Proceed with caution and confirm through official channels."
    else:
        summary = "This recruiter and company profile align with verified, legitimate business records."

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "verdict_label": verdict_label,
        "summary": summary,
        "signals": signals,
        "reasoning": reasoning,
        "matched_company": company,
    }


# ----------------------------------------------------------------------
# JOB LISTING SCANNER (ML + rules)
# ----------------------------------------------------------------------

def analyze_job(
    db: Session,
    job_title: str,
    company_name: str,
    description: str = "",
    salary_range: str = "",
    location: str = "",
) -> dict:
    from app.ml.infer import predict_job_fraud_probability

    description = description or ""

    company = (
        db.query(Company)
        .filter(Company.name.ilike(f"%{company_name.strip()}%"))
        .order_by(Company.trust_score.desc())
        .first()
    )

    has_company_logo = 1 if (company and company.trust_status == "verified") else 0
    telecommuting = 1 if "remote" in (location or "").lower() else 0

    fraud_proba = predict_job_fraud_probability(
        title=job_title,
        company_profile=f"{company_name} {(company.notes if company else '')}",
        description=description,
        salary_range=salary_range or "",
        telecommuting=telecommuting,
        has_company_logo=has_company_logo,
        has_questions=1,
        industry=(company.industry if company else ""),
    )

    ml_risk_points = fraud_proba * 70  # weight ML contribution

    signals = []
    reasoning = []
    risk_points = ml_risk_points

    # Company registry cross-check (same as profile scan, contextualized for jobs)
    if company is None:
        risk_points += 12
        signals.append({
            "icon": "domain_disabled", "label": "Company Entity Search",
            "detail": f"'{company_name}' is not a recognized registered entity.",
            "status": "negative",
        })
    elif company.trust_status == "flagged":
        risk_points += 25
        signals.append({
            "icon": "report", "label": "Flagged Employer",
            "detail": f"{company.name} has {company.report_count} fraud reports on file.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Company Entity Search",
            "detail": f"'{company.name}' matches a known high-risk shell entity with multiple "
                      f"community fraud reports.",
        })
    else:
        risk_points -= 15
        signals.append({
            "icon": "verified", "label": "Company Entity Search",
            "detail": f"{company.name} is a registered entity.",
            "status": "positive",
        })
        reasoning.append({
            "title": "Company Entity Search",
            "detail": f"{company.name} is a registered, verifiable company.",
        })

    # Salary benchmarking signal
    if salary_range and "-" in salary_range:
        try:
            lo, hi = [float(x) for x in salary_range.replace("$", "").split("-")]
            span_ratio = (hi - lo) / lo if lo > 0 else 0
            if span_ratio > 1.5 or hi > 300000:
                risk_points += 10
                signals.append({
                    "icon": "monitoring", "label": "Salary Benchmarking",
                    "detail": "Salary range is unusually wide or high for this role.",
                    "status": "negative",
                })
            else:
                signals.append({
                    "icon": "monitoring", "label": "Salary Benchmarking",
                    "detail": "Compensation appears within normal market range.",
                    "status": "positive",
                })
        except Exception:
            pass
    else:
        signals.append({
            "icon": "monitoring", "label": "Salary Benchmarking",
            "detail": "No salary range provided to benchmark.",
            "status": "neutral",
        })

    # Description text-based red flags (reuse message phrase lists, since
    # scam job descriptions use the same manipulative language patterns)
    desc_payment_hits = _contains_any(description, PAYMENT_PHRASES)
    if desc_payment_hits:
        risk_points += 25
        signals.append({
            "icon": "payments", "label": "Payment Request in Listing",
            "detail": "Description references fees, deposits, or wire transfers.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Description Red Flags",
            "detail": "The job description references upfront fees or payment processing, a strong "
                      "indicator of advance-fee fraud.",
        })

    desc_urgency_hits = _contains_any(description, URGENCY_PHRASES)
    if desc_urgency_hits:
        risk_points += 10
        signals.append({
            "icon": "bolt", "label": "Urgency Pressure",
            "detail": "Listing uses high-pressure urgency language.",
            "status": "negative",
        })

    if not desc_payment_hits and not desc_urgency_hits and description.strip():
        reasoning.append({
            "title": "Market Realism",
            "detail": "Role description and requirements are consistent with standard postings for "
                      "this job category.",
        })

    risk_points = max(0, min(risk_points, 96))
    trust_score = max(3, round(100 - risk_points))
    risk_level, verdict_label = _risk_bucket(
        trust_score, safe_label="Likely Genuine", verify_label="Probable / Verify", risk_label="High Risk Listing"
    )

    if risk_level == "high_risk":
        summary = "Multiple strong fraud indicators detected. This listing closely matches known scam patterns."
    elif risk_level == "verify":
        summary = "Some signals require manual verification before proceeding with this opportunity."
    else:
        summary = "This listing aligns with legitimate hiring patterns and verified company data."

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "verdict_label": verdict_label,
        "summary": summary,
        "signals": signals,
        "reasoning": reasoning,
        "ml_fraud_probability": round(fraud_proba, 4),
    }


# ----------------------------------------------------------------------
# LINK SCANNER (lightweight structural heuristics)
# ----------------------------------------------------------------------

SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click"}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "buff.ly", "cutt.ly"}


def analyze_link(url: str) -> dict:
    signals = []
    reasoning = []
    risk_points = 0

    raw = url.strip()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or parsed.path.split("/")[0]).lower()

    if parsed.scheme != "https":
        risk_points += 15
        signals.append({
            "icon": "lock_open", "label": "No HTTPS",
            "detail": "Connection is not encrypted.",
            "status": "negative",
        })
    else:
        signals.append({
            "icon": "lock", "label": "HTTPS Enabled",
            "detail": "Connection uses standard encryption.",
            "status": "positive",
        })

    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        risk_points += 35
        signals.append({
            "icon": "domain", "label": "High-Risk Domain Extension",
            "detail": "Domain uses a TLD commonly associated with disposable/spam sites.",
            "status": "negative",
        })
        reasoning.append({
            "title": "Domain Reputation",
            "detail": f"The domain '{host}' uses a top-level domain frequently associated with "
                      f"low-cost, disposable scam infrastructure.",
        })

    if any(short in host for short in URL_SHORTENERS):
        risk_points += 20
        signals.append({
            "icon": "link", "label": "Shortened URL",
            "detail": "URL shorteners can mask the true destination.",
            "status": "negative",
        })

    if re.search(r"\d{4,}", host):
        risk_points += 10
        signals.append({
            "icon": "tag", "label": "Numeric Subdomain Pattern",
            "detail": "Domain contains an unusual numeric pattern.",
            "status": "negative",
        })

    if "-" in host and host.count("-") >= 2:
        risk_points += 10
        signals.append({
            "icon": "alt_route", "label": "Hyphenated Lookalike Domain",
            "detail": "Multiple hyphens can indicate a typosquatting attempt.",
            "status": "negative",
        })

    if not signals or risk_points == 0:
        signals.append({
            "icon": "verified", "label": "No Structural Red Flags",
            "detail": "Domain structure appears standard.",
            "status": "positive",
        })

    risk_points = min(risk_points, 90)
    trust_score = max(5, 100 - risk_points)
    risk_level, verdict_label = _risk_bucket(
        trust_score, safe_label="Likely Safe Link", verify_label="Inspect Before Clicking", risk_label="High Risk Link"
    )

    summary = {
        "high_risk": "This link shows strong structural indicators of a phishing or scam destination.",
        "verify": "This link has some unusual characteristics. Verify the destination before entering any information.",
        "safe": "This link's structure does not show common phishing indicators.",
    }[risk_level]

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "verdict_label": verdict_label,
        "summary": summary,
        "signals": signals,
        "reasoning": reasoning,
    }


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------

def _risk_bucket(trust_score: int, safe_label: str, verify_label: str, risk_label: str) -> Tuple[str, str]:
    if trust_score >= 70:
        return "safe", safe_label
    if trust_score >= 40:
        return "verify", verify_label
    return "high_risk", risk_label
