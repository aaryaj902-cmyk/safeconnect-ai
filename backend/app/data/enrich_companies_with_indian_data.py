"""
Enriches data/companies.csv with real companies extracted from the Indeed
India job-postings dataset (the same source used in merge_indian_dataset.py).

Only companies that posted multiple times (>= MIN_POSTINGS) are added, as a
simple proxy for "this is an established, ongoing employer" rather than a
one-off or noisy scrape artifact. These are added as `trust_status=verified`
since they are real companies actively posting on Indeed India.

Usage (from backend/ directory, with indeed_india_raw.ldjson present in
app/data/ -- see merge_indian_dataset.py for how to obtain it):

    python3 app/data/enrich_companies_with_indian_data.py
"""
import csv
import json
import os
import random

random.seed(13)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LDJSON_PATH = os.path.join(THIS_DIR, "indeed_india_raw.ldjson")
COMPANIES_CSV_PATH = os.path.join(THIS_DIR, "companies.csv")

MIN_POSTINGS = 5  # only add companies that posted at least this many times
MAX_TO_ADD = 150  # cap how many we add, to keep the registry a manageable size


def main():
    if not os.path.exists(LDJSON_PATH):
        print(f"ERROR: Could not find {LDJSON_PATH}")
        print("Place the Indeed India .ldjson file there first, named exactly "
              "'indeed_india_raw.ldjson', then re-run this script.")
        return

    import collections
    companies = collections.Counter()
    company_meta = {}  # name -> (city, state, category)

    with open(LDJSON_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = (rec.get("company_name") or "").strip()
            if not name:
                continue
            companies[name] += 1
            if name not in company_meta:
                city = rec.get("inferred_city") or rec.get("city") or ""
                state = rec.get("inferred_state") or rec.get("state") or ""
                category = (rec.get("category") or "").strip()
                company_meta[name] = (city, state, category)

    # Load existing companies to avoid duplicates
    existing_names = set()
    existing_rows = []
    if os.path.exists(COMPANIES_CSV_PATH):
        with open(COMPANIES_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            existing_names = {r["name"].strip().lower() for r in existing_rows}

    next_id = max([int(r["company_id"]) for r in existing_rows], default=0) + 1

    candidates = [
        (name, count) for name, count in companies.items()
        if count >= MIN_POSTINGS and name.strip().lower() not in existing_names
    ]
    candidates.sort(key=lambda x: -x[1])
    candidates = candidates[:MAX_TO_ADD]

    new_rows = []
    for name, count in candidates:
        city, state, category = company_meta.get(name, ("", "", ""))
        hq_parts = [p for p in [city, state, "India"] if p]
        headquarters = ", ".join(hq_parts) if hq_parts else "India"
        # More postings -> slightly higher baseline trust score (capped)
        trust_score = min(96, 78 + min(count, 18))
        new_rows.append({
            "company_id": next_id,
            "name": name,
            "industry": category or "Other",
            "headquarters": headquarters,
            "official_domain": "",
            "founded_year": "",
            "trust_status": "verified",
            "trust_score": trust_score,
            "employee_count": "",
            "report_count": 0,
            "notes": f"Active employer on Indeed India ({count} postings observed).",
        })
        next_id += 1

    all_rows = existing_rows + new_rows
    fieldnames = list(existing_rows[0].keys()) if existing_rows else list(new_rows[0].keys())

    with open(COMPANIES_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Added {len(new_rows)} real Indian companies to the registry.")
    print(f"Total companies in registry now: {len(all_rows)}")
    if new_rows:
        print("\nSample of companies added:")
        for r in new_rows[:10]:
            print(f"  - {r['name']} (trust_score={r['trust_score']}, {r['headquarters']})")


if __name__ == "__main__":
    main()
