import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403  -- ensures all models are registered with Base
from app.routers import auth, scan, companies, reports, dashboard
from app.services.seed import run_all_seeds

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safeconnect")

app = FastAPI(
    title="SafeConnect AI API",
    description="Backend for SafeConnect AI Recruitment Guardian — job, recruiter, "
                "message, and link fraud detection.",
    version="1.0.0",
)

# CORS: must use explicit origins (not "*") because allow_credentials=True.
# Browsers reject the combination of wildcard origins + credentials, so a
# bare "*" here would silently break every authenticated request from the
# browser. Default to common local-dev ports plus the deployed frontend
# domain; override via CORS_ALLOW_ORIGINS (comma-separated) if needed.
default_origins = (
    "http://localhost:5500,http://127.0.0.1:5500,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "https://safeconnect-frontend.onrender.com"
)
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", default_origins)
if allowed_origins.strip() == "*":
    # Wildcard requested explicitly: keep credentials support working by
    # reflecting any origin instead of using the literal "*" the browser
    # would reject when credentials are involved.
    origins = ["*"]
    allow_credentials = False
else:
    origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(companies.router)
app.include_router(reports.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables (if not already present)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        result = run_all_seeds(db)
        logger.info(f"Seed result: {result}")
    finally:
        db.close()

    # Warm up / auto-train the ML model on startup so the first user request
    # isn't slowed down by on-demand training.
    try:
        from app.ml.infer import _ensure_trained
        _ensure_trained()
        logger.info("ML fraud-detection model is ready.")
    except Exception as e:
        logger.warning(f"ML model warmup failed (will retry on first request): {e}")


@app.get("/")
def root():
    return {
        "service": "SafeConnect AI API",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
