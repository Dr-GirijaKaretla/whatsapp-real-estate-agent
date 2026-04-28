"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./real_estate.db")

# SQLite needs check_same_thread=False for multi-threaded Flask
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a DB session; close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
