import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# SQLite database URL (can be overridden via environment variable)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./students.db")

# check_same_thread: False is needed only for SQLite to allow multiple threads per connection
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True if SQL query logging is desired
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session
    and guarantees it is closed after request handling.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Helper function to create all database tables."""
    Base.metadata.create_all(bind=engine)
