"""
Merges the real Indeed India job-postings dataset (genuine listings) with
SafeConnect AI's synthetic scam examples (fraudulent listings) into a single
fake_job_postings.csv with the schema the ML pipeline expects.

WHY THIS APPROACH
------------------
The real Indeed India dataset (PromptCloud / Kaggle:
promptcloud/indeed-india-job-dataset) contains ~5,000 REAL job postings
scraped from indeed.co.in, but it has NO fraud/scam labels -- every row is
a genuine listing. There is no well-established, large, India-specific
LABELED fraud dataset equivalent to the global EMSCAD dataset.

So this script:
  1. Loads all real Indeed India postings -> labels them fraudulent=0
     (they are genuine, real, Indian job postings -- company names,
     locations, descriptions are all real).
  2. Loads a sample of SafeConnect AI's synthetic scam postings (the
     procedurally-generated fraud examples from generate_job_dataset.py)
     -> keeps them labeled fraudulent=1, so the model still has fraud
     examples to learn from. These follow documented real-world scam
     patterns (advance-fee requests, urgency language, vague pay claims)
     even though the specific company names are synthetic.
  3. Combines both into data/fake_job_postings.csv, ready for
     `python -m app.ml.train_model`.

Usage (from backend/ directory, with the Indeed India .ldjson file placed
at backend/app/data/indeed_india_raw.ldjson):

    python3 app/data/merge_indian_dataset.py
"""
import csv
import json
import os
import random

random.seed(11)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LDJSON_PATH = os.path.join(THIS_DIR, "indeed_india_raw.ldjson")
SYNTHETIC_CSV_PATH = os.path.join(THIS_DIR, "fake_job_postings.csv")
OUTPUT_CSV_PATH = os.path.join(THIS_DIR, "fake_job_postings.csv")
BACKUP_SYNTHETIC_PATH = os.path.join(THIS_DIR, "fake_job_postings_synthetic_backup.csv")

FIELDNAMES = [
    "job_id", "title", "location", "department", "salary_range",
    "company_profile", "description", "requirements", "benefits",
    "telecommuting", "has_company_logo", "has_questions", "employment_type",
    "required_experience", "required_education", "industry", "function",
    "fraudulent",
]

# Map Indeed's free-text job_type strings to the EMSCAD-style categories
# our schema/model expects.
EMPLOYMENT_TYPE_MAP = {
    "full-time": "Full-time",
    "part time": "Part-time",
    "part-time": "Part-time",
    "contract": "Contract",
    "internship": "Other",
    "fresher": "Other",
    "commission": "Other",
    "walk-in": "Other",
    "volunteer": "Other",
}


def normalize_employment_type(job_type: str) -> str:
    if not job_type:
        return "Full-time"
    first = job_type.split("|")[0].strip().lower()
    return EMPLOYMENT_TYPE_MAP.get(first, "Full-time")


def normalize_experience(job_type: str) -> str:
    jt = (job_type or "").lower()
    if "fresher" in jt or "internship" in jt:
        return "Entry level"
    return "Not Applicable"


def load_indian_rows(path: str, limit: int = None) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            title = (rec.get("job_title") or "").strip()
            company = (rec.get("company_name") or "").strip()
            description = (rec.get("job_description") or "").strip()
            if not title or not company or not description:
                continue  # skip incomplete records

            city = rec.get("inferred_city") or rec.get("city") or ""
            state = rec.get("inferred_state") or rec.get("state") or ""
            country = rec.get("inferred_country") or "India"
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts)

            company_description = (rec.get("company_description") or "").strip()
            company_profile = company_description or f"{company} is hiring via Indeed India."

            job_type = rec.get("job_type") or ""
            employment_type = normalize_employment_type(job_type)
            required_experience = normalize_experience(job_type)
            is_remote = str(rec.get("is_remote", "false")).lower() == "true"
            category = (rec.get("category") or "").strip()

            rows.append({
                "job_id": rec.get("uniq_id", f"in_{i}"),
                "title": title,
                "location": location or "India",
                "department": category,
                "salary_range": "",  # not reliably present in this dataset
                "company_profile": company_profile,
                "description": description,
                "requirements": "",  # not provided as a separate field in this dataset
                "benefits": "",       # not provided as a separate field in this dataset
                "telecommuting": 1 if is_remote else 0,
                "has_company_logo": 1,  # real Indeed postings display a company profile
                "has_questions": 0,
                "employment_type": employment_type,
                "required_experience": required_experience,
                "required_education": "Unspecified",
                "industry": category or "Other",
                "function": category or "Other",
                "fraudulent": 0,
            })
    return rows


def load_synthetic_fraud_rows(path: str) -> list:
    """Keep only the fraudulent=1 rows from the existing synthetic dataset,
    so the model still has fraud examples (the Indian dataset has none)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("fraudulent", "0")) == "1":
                rows.append(row)
    return rows


def main():
    if not os.path.exists(LDJSON_PATH):
        print(f"ERROR: Could not find {LDJSON_PATH}")
        print("Place the Indeed India .ldjson file there first, named exactly "
              "'indeed_india_raw.ldjson', then re-run this script.")
        return

    # Back up the original fully-synthetic dataset before overwriting it,
    # in case you want to revert later.
    if os.path.exists(SYNTHETIC_CSV_PATH) and not os.path.exists(BACKUP_SYNTHETIC_PATH):
        with open(SYNTHETIC_CSV_PATH, encoding="utf-8") as src, \
             open(BACKUP_SYNTHETIC_PATH, "w", encoding="utf-8", newline="") as dst:
            dst.write(src.read())
        print(f"Backed up original synthetic dataset to {BACKUP_SYNTHETIC_PATH}")

    fraud_rows = load_synthetic_fraud_rows(BACKUP_SYNTHETIC_PATH if os.path.exists(BACKUP_SYNTHETIC_PATH) else SYNTHETIC_CSV_PATH)
    print(f"Loaded {len(fraud_rows)} synthetic fraudulent rows")

    indian_rows = load_indian_rows(LDJSON_PATH)
    print(f"Loaded {len(indian_rows)} real Indeed India job postings")

    all_rows = indian_rows + fraud_rows
    random.shuffle(all_rows)

    # Re-number job_id sequentially for cleanliness
    for idx, row in enumerate(all_rows, start=1):
        row["job_id"] = idx
        # Ensure every fieldname is present (defensive, in case of schema drift)
        for fn in FIELDNAMES:
            if fn not in row:
                row[fn] = ""

    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    n_fraud = sum(1 for r in all_rows if str(r["fraudulent"]) == "1")
    print(f"\nWrote {len(all_rows)} total rows to {OUTPUT_CSV_PATH}")
    print(f"  Genuine (real Indeed India): {len(all_rows) - n_fraud}")
    print(f"  Fraudulent (synthetic):      {n_fraud}")
    print(f"  Fraud rate: {100 * n_fraud / len(all_rows):.2f}%")
    print("\nNext step: retrain the model with:")
    print("  python3 -m app.ml.train_model")


if __name__ == "__main__":
    main()
