"""
Trains a real scikit-learn fraud classifier on data/fake_job_postings.csv
and saves the fitted pipeline to ml/job_fraud_model.joblib

Run:
    python3 -m app.ml.train_model
from the backend/ directory (or just `python3 train_model.py` from this dir
-- path handling below supports both).
"""
import os
import sys
import csv

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(THIS_DIR), "data")
CSV_PATH = os.path.join(DATA_DIR, "fake_job_postings.csv")
MODEL_PATH = os.path.join(THIS_DIR, "job_fraud_model.joblib")

TEXT_COLS = ["title", "company_profile", "description", "requirements", "benefits"]
CAT_COLS = ["employment_type", "required_experience", "required_education", "industry", "function"]
NUM_COLS = ["telecommuting", "has_company_logo", "has_questions", "salary_span_ratio", "text_len"]


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def salary_span_ratio(salary_range: str) -> float:
    """Heuristic numeric feature: ratio of (hi-lo)/lo for salary range strings like '50000-65000'."""
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


def build_features(rows):
    combined_text, cats, nums, labels = [], [], [], []
    for r in rows:
        text = " ".join(r.get(c, "") or "" for c in TEXT_COLS)
        combined_text.append(text)
        cats.append([r.get(c, "") or "" for c in CAT_COLS])
        text_len = len(text)
        nums.append([
            float(r.get("telecommuting", 0) or 0),
            float(r.get("has_company_logo", 0) or 0),
            float(r.get("has_questions", 0) or 0),
            salary_span_ratio(r.get("salary_range", "")),
            text_len,
        ])
        labels.append(int(r.get("fraudulent", 0) or 0))
    return combined_text, np.array(cats, dtype=object), np.array(nums, dtype=float), np.array(labels)


class TextLengthSafeVectorizer(TfidfVectorizer):
    pass


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Dataset not found at {CSV_PATH}. Run generate_job_dataset.py first.")
        sys.exit(1)

    rows = load_rows(CSV_PATH)
    print(f"Loaded {len(rows)} rows")

    text, cats, nums, y = build_features(rows)

    # TF-IDF on combined free text
    tfidf = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words="english", min_df=2)
    X_text = tfidf.fit_transform(text)

    # One-hot categorical
    ohe = OneHotEncoder(handle_unknown="ignore")
    X_cat = ohe.fit_transform(cats)

    # Scale numeric
    scaler = StandardScaler()
    X_num = scaler.fit_transform(nums)

    from scipy.sparse import hstack, csr_matrix
    X = hstack([X_text, X_cat, csr_matrix(X_num)]).tocsr()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred, target_names=["genuine", "fraudulent"]))
    try:
        print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
    except Exception:
        pass

    bundle = {
        "tfidf": tfidf,
        "ohe": ohe,
        "scaler": scaler,
        "clf": clf,
        "text_cols": TEXT_COLS,
        "cat_cols": CAT_COLS,
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nSaved model bundle to {MODEL_PATH}")


if __name__ == "__main__":
    main()
