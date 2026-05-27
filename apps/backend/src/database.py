# =============================================================================
# SQLAlchemy Database Setup for VietSpeak AI
# =============================================================================
#
# Uses a synchronous engine (psycopg2 / SQLite) for the API and standalone
# scripts. The DATABASE_URL from .env may contain '+asyncpg'; this module
# normalises it to the synchronous driver automatically.
#
# Resilient connection strategy ("support both"):
#   1. Try the configured DATABASE_URL (e.g. Supabase Postgres).
#   2. If it is unreachable (bad host, paused project, network error),
#      automatically fall back to the bundled local SQLite database (dev.db).
# This lets the app keep working offline while still preferring the cloud DB
# when it is available.

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Tuple

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.core.logging import get_logger

logger = get_logger(__name__)

load_dotenv()

# Local SQLite database bundled with the backend (seeded with IELTS prompts).
_SQLITE_PATH = Path(__file__).resolve().parent.parent / "dev.db"
_FALLBACK_SQLITE_URL = f"sqlite:///{_SQLITE_PATH.as_posix()}"

# Seconds to wait when probing the primary (cloud) database before giving up.
_CONNECT_TIMEOUT = 5

Base = declarative_base()


def _normalise_url(url: str) -> str:
    """Strip async driver markers so we always use a synchronous driver."""
    return url.replace("+asyncpg", "")


def _make_sqlite_engine() -> Engine:
    """Create the local SQLite engine (safe for FastAPI's threadpool)."""
    return create_engine(
        _FALLBACK_SQLITE_URL,
        echo=False,
        # FastAPI runs sync endpoints in a threadpool; allow cross-thread use.
        connect_args={"check_same_thread": False},
    )


def _resolve_engine() -> Tuple[Engine, str]:
    """Pick an engine: prefer the configured DB, fall back to SQLite.

    Returns the engine and the URL it ended up using.
    """
    raw_url = os.getenv("DATABASE_URL", _FALLBACK_SQLITE_URL)
    primary_url = _normalise_url(raw_url)

    # If the configured DB is already SQLite, just use it — nothing to probe.
    if primary_url.startswith("sqlite"):
        return _make_sqlite_engine(), _FALLBACK_SQLITE_URL

    # Probe the cloud/primary database with a short timeout.
    try:
        primary_engine = create_engine(
            primary_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": _CONNECT_TIMEOUT},
        )
        with primary_engine.connect():
            pass
        logger.info("db_connected", backend="primary", url=_safe_url(primary_url))
        return primary_engine, primary_url
    except Exception as exc:  # noqa: BLE001 — any failure means fall back
        logger.warning(
            "db_primary_unreachable_falling_back_to_sqlite",
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
            fallback=_FALLBACK_SQLITE_URL,
        )
        return _make_sqlite_engine(), _FALLBACK_SQLITE_URL


def _safe_url(url: str) -> str:
    """Hide the password when logging a database URL."""
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            user = creds.split(":", 1)[0]
            return f"{scheme}://{user}:***@{host}"
    return url


engine, DATABASE_URL = _resolve_engine()
SessionLocal = sessionmaker(bind=engine)


class IELTSPrompt(Base):
    """IELTS Speaking prompt (Part 1 / 2 / 3)."""

    __tablename__ = "ielts_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part = Column(Integer, nullable=False)
    topic = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)


class UserAttempt(Base):
    """User speaking attempt linked to an IELTS prompt."""

    __tablename__ = "user_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, ForeignKey("ielts_prompts.id"), nullable=False)
    transcript = Column(Text)
    lexical_score = Column(Integer)
    grammar_score = Column(Integer)
    feedback = Column(Text)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


def init_db() -> None:
    """Create all tables on the active engine. Idempotent."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and auto-closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
