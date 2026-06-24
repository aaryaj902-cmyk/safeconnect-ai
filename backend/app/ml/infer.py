"""
Loads the trained job-fraud-detection model bundle (TF-IDF + OHE + scaler +
LogisticRegression) produced by train_model.py. If the model file doesn't
exist yet (first run), it trains it automatically so the API works out of
the box with no manual ML steps required.
"""
import os
import threading

import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(THIS_DIR, "job_fraud_model.joblib")

_lock = threading.Lock()
_bundle = None


def _ensure_trained():
    global _bundle
    if _bundle is not None:
        return _bundle
    with _lock:
        if _bundle is not None:
            return _bundle
        if not os.path.exists(MODEL_PATH):
            # Train on the fly using the same logic as train_model.py
            from app.ml.train_model import main as train_main
            train_main()
        _bundle = joblib.load(MODEL_PATH)
        return _bundle


def _salary_span_ratio(salary_range: str) -> float:
    if not salary_range or "-" not in salary_range:
        return 0.0
    try:
        lo, hi = salary_range.split("-")
        lo, hi = float(lo), float(hi)
        if lo <= 0:
            return 0.0
        return (hi - lo) / lo
    except Exception:
        return 0.0


def predict_job_fraud_probability(
    title: str,
    company_profile: str,
    description: str,
    requirements: str = "",
    benefits: str = "",
    employment_type: str = "Full-time",
    required_experience: str = "Not Applicable",
    required_education: str = "Unspecified",
    industry: str = "",
    function: str = "",
    telecommuting: int = 0,
    has_company_logo: int = 0,
    has_questions: int = 0,
    salary_range: str = "",
) -> float:
    """Returns probability (0.0-1.0) that this job posting is fraudulent."""
    bundle = _ensure_trained()
    tfidf, ohe, scaler, clf = bundle["tfidf"], bundle["ohe"], bundle["scaler"], bundle["clf"]

    text = " ".join([title, company_profile, description, requirements, benefits])
    X_text = tfidf.transform([text])

    cats = np.array([[employment_type, required_experience, required_education, industry, function]], dtype=object)
    X_cat = ohe.transform(cats)

    text_len = len(text)
    nums = np.array([[
        float(telecommuting), float(has_company_logo), float(has_questions),
        _salary_span_ratio(salary_range), text_len,
    ]])
    X_num = scaler.transform(nums)

    X = hstack([X_text, X_cat, csr_matrix(X_num)]).tocsr()
    proba = clf.predict_proba(X)[0, 1]
    return float(proba)
