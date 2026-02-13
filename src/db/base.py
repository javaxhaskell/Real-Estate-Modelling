"""Database engine and session helpers for the underwriting project."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "underwriting.db"


def get_engine(db_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine.

    The default database lives in ``data/underwriting.db`` to keep the whole
    project self-contained and offline friendly.
    """

    if db_url is None:
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    return create_engine(db_url, future=True)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a reusable session factory bound to ``engine``."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
