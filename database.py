import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Check if running in Vercel serverless environment (read-only filesystem except /tmp)
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("NOW_REGION"))
DEFAULT_DB_URL = "sqlite:////tmp/students.db" if IS_VERCEL else "sqlite:///./students.db"

DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# check_same_thread: False is needed for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session and closing it on completion.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Helper function to create all database tables."""
    Base.metadata.create_all(bind=engine)
