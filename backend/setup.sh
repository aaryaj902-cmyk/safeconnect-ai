#!/usr/bin/env bash
# One-shot local setup for the SafeConnect AI backend.
# Usage: bash setup.sh
set -e

cd "$(dirname "$0")"

echo "==> Creating virtual environment (.venv)..."
python3 -m venv .venv

echo "==> Activating virtual environment..."
source .venv/bin/activate

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing dependencies..."
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example..."
  cp .env.example .env
  echo "    Edit backend/.env if you want to point at your own PostgreSQL instance."
fi

echo "==> Checking datasets..."
if [ -f app/data/fake_job_postings.csv ] && [ -f app/data/companies.csv ]; then
  echo "    Datasets already present (app/data/fake_job_postings.csv, app/data/companies.csv) -- skipping generation."
  echo "    Delete them first if you want to regenerate the fully-synthetic versions."
else
  echo "==> Generating datasets (job postings + companies)..."
  python3 app/data/generate_job_dataset.py
  python3 app/data/generate_company_dataset.py
fi

echo "==> Training the fraud-detection ML model..."
python3 -m app.ml.train_model

echo ""
echo "Setup complete. Start the server with:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
