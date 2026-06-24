"""
Database setup.

Reads DATABASE_URL from the environment / .env file. Expected to be a
PostgreSQL URL in production/local-postgres use, e.g.:

    DATABASE_URL=postgresql+psycopg2://safeconnect:safeconnect@localhost:5432/safeconnect

If DATABASE_URL is not set at all, we fall back to a local SQLite file
(./safeconnect.db) so the project runs out of the box with zero database
setup. This fallback is intended for quick local testing only -- for the
"real" local run, set DATABASE_URL to your Postgres instance in .env.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Hosting platforms like Render/Heroku inject DATABASE_URL starting with
# "postgres://", but SQLAlchemy 2.x requires "postgresql://" (or an explicit
# driver like "postgresql+psycopg2://"). Normalize it so deployment works
# without manual edits.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./safeconnect.db"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
