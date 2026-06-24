# SafeConnect AI — Recruitment Guardian

A full-stack fraud-detection platform for job seekers: verifies recruiter
profiles, scans messages for phishing/scam patterns, checks job listing
authenticity with a trained ML model, and maintains a community scam ledger.

```
safeconnect/
├── backend/      FastAPI + PostgreSQL (or SQLite) API + ML model
└── frontend/     Static HTML/Tailwind/vanilla JS frontend
```

---

## 1. Backend setup

### Requirements
- Python 3.10+
- PostgreSQL 13+ (optional — see "Quick start without Postgres" below)

### Option A — Full setup with PostgreSQL (recommended)

```bash
cd backend

# 1. Create the database (run once)
createdb safeconnect
#    If `createdb` isn't on your PATH, use psql:
#    psql -U postgres -c "CREATE DATABASE safeconnect;"

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL to match your Postgres credentials, e.g.:
# DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@localhost:5432/safeconnect

# 4. Datasets are already included (real Indian job postings + verified
#    company registry — see section 3 below for details). No generation
#    step needed unless you want to regenerate the fully-synthetic version.

# 5. Train the ML fraud-detection model
python3 -m app.ml.train_model

# 6. Run the API
uvicorn app.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**. Interactive docs (Swagger
UI) are at **http://localhost:8000/docs**.

On first startup, the app automatically:
- Creates all database tables
- Seeds the `companies` table from `app/data/companies.csv`
- Seeds a handful of starter community scam reports
- Verifies the ML model is trained (trains it on the spot if missing)

### Option B — Quick start without PostgreSQL

If you just want to try it locally without installing Postgres, skip step 1
and leave `DATABASE_URL` unset (or delete that line from `.env`). The app
automatically falls back to a local SQLite file (`backend/safeconnect.db`)
with zero extra setup. Steps 2–6 are otherwise identical.

### One-shot setup script

`backend/setup.sh` automates steps 2–5 (venv, install, dataset generation,
model training):

```bash
cd backend
bash setup.sh
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

## 2. Frontend setup

The frontend is plain HTML/CSS (Tailwind via CDN)/vanilla JS — no build step.

```bash
cd frontend
python3 serve.py 5500
```

Then open **http://localhost:5500/index.html**.

(You can also just double-click `index.html` to open it via `file://`, but
serving it over `http://` is more reliable for the `fetch()` calls to the
API and avoids browser CORS quirks.)

Make sure the backend (step 1) is running first — the frontend expects it at
`http://localhost:8000`. If you run the backend on a different port/host,
add this line to the `<head>` of each HTML file **before** the
`js/api.js` script tag:

```html
<script>window.SAFECONNECT_API_BASE = "http://localhost:9000";</script>
```

### Pages

| Page | Purpose |
|---|---|
| `index.html` | Landing page |
| `register.html` / `login.html` | Auth |
| `dashboard.html` | Personal safety overview, recent scans, community trends |
| `verification-hub.html` | **Core feature** — scan a recruiter profile, message, or job listing |
| `scam-ledger.html` | Community-reported scammers, submit new reports |
| `history.html` | Full scan history |
| `extension-demo.html` | Static design reference for a browser-extension popup (not a real installable extension — see note in-page) |

---

## 3. How the fraud detection works

- **Job listings** — a scikit-learn `LogisticRegression` model (TF-IDF text
  features + categorical + numeric features) trained on
  `backend/app/data/fake_job_postings.csv`, combined with company-registry
  cross-checks and rule-based red flags (payment requests, urgency language).
- **Recruiter profiles** — cross-references the company name against
  `backend/app/data/companies.csv` (a registry of real well-known companies
  + synthetic legitimate companies + known scam-pattern shell companies),
  plus LinkedIn URL structural heuristics.
- **Messages** — explainable rule-based engine that flags urgency language,
  payment/fee requests, requests for sensitive documents (SSN/passport),
  free-email domains posing as corporate recruiters, and unofficial
  messaging channels (Telegram/WhatsApp).
- **Links** — structural heuristics (HTTPS, suspicious TLDs, URL shorteners,
  lookalike domains).

### ⚠️ About the datasets — please read

This environment had no internet access while building the initial version
of this project, so the real Kaggle "Fake Job Postings" dataset (EMSCAD,
~17,880 rows) could not be downloaded at that time. The shipped dataset has
since been upgraded to include **real Indian job postings**:

- **Genuine listings (5,000 rows)** — real job postings scraped from
  Indeed India (PromptCloud's `indeed-india-job-dataset` on Kaggle),
  covering real Indian companies, cities, and job descriptions.
- **Fraudulent listings (150 rows)** — procedurally generated synthetic
  scam postings, since no large, labeled, India-specific fraud dataset
  exists publicly. These follow documented real-world scam patterns
  (advance-fee requests, urgency language, vague/unrealistic pay claims)
  even though the specific company names are synthetic.

This mirrors how the original EMSCAD dataset itself is structured — mostly
real postings with a small minority of labeled fraud examples (~5%; here
~2.9%). The company verification registry (`companies.csv`) was similarly
enriched with **127 real companies** (JPMorgan Chase, Genpact, Cognizant,
EY, Standard Chartered, and more) extracted directly from the same Indian
job-postings source, in addition to the original global companies
(Google, Microsoft, Infosys, TCS, Wipro, HCLTech, etc.) and known
scam-pattern shell companies.

If you'd like to regenerate this merge yourself (e.g. with a fresher Indeed
India export, or to add more rows):

1. Download the Indeed India dataset from
   https://www.kaggle.com/datasets/promptcloud/indeed-india-job-dataset
   (or a similar PromptCloud Indeed-India export — line-delimited JSON)
2. Save it as `backend/app/data/indeed_india_raw.ldjson`
3. Run:
   ```bash
   cd backend
   python3 app/data/merge_indian_dataset.py
   python3 app/data/enrich_companies_with_indian_data.py
   ```
4. Delete the old model and retrain:
   ```bash
   rm app/ml/job_fraud_model.joblib   # Windows: del app\ml\job_fraud_model.joblib
   python3 -m app.ml.train_model
   ```

The original fully-synthetic dataset is preserved at
`backend/app/data/fake_job_postings_synthetic_backup.csv` if you ever want
to revert (just copy it over `fake_job_postings.csv` and retrain).

If you want the literal global Kaggle EMSCAD dataset instead of either of
the above, download it from
https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction,
save as `backend/app/data/fake_job_postings.csv` (same column names, drop-in
replacement), delete the model file, and retrain.

---

## 4. API reference (quick glance)

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in |
| GET | `/api/auth/me` | Current user |
| POST | `/api/scan/profile` | Scan a recruiter profile |
| POST | `/api/scan/message` | Scan a message for phishing patterns |
| POST | `/api/scan/job` | Scan a job listing (ML + rules) |
| POST | `/api/scan/link` | Scan a URL |
| GET | `/api/scan/history` | List past scans |
| GET | `/api/companies?q=` | Search the company registry |
| GET | `/api/reports` | List community scam reports |
| POST | `/api/reports` | Submit a scam report |
| GET | `/api/reports/stats` | Ledger stats (total blocked, etc.) |
| GET | `/api/dashboard` | Aggregate dashboard data |

Full interactive docs: **http://localhost:8000/docs**

---

## 5. Troubleshooting

- **"Could not reach the SafeConnect AI backend"** in the browser — make
  sure `uvicorn app.main:app --reload --port 8000` is running.
- **CORS errors** — the backend allows all origins by default
  (`CORS_ALLOW_ORIGINS=*` in `.env`). If you changed this, make sure your
  frontend's origin is included.
- **`psycopg2` install fails** — on some systems you may need PostgreSQL's
  dev headers (`sudo apt install libpq-dev` on Debian/Ubuntu) or just rely
  on the bundled `psycopg2-binary` wheel already in `requirements.txt`.
- **Model training is slow on first request** — the first `uvicorn` startup
  trains the ML model (a few seconds on 3,000 rows). Subsequent starts load
  the cached `.joblib` file instantly.
