"""Database initialization helpers."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from src.db.models import Base


def init_db(engine: Engine) -> None:
    """Auto-create all tables if they do not yet exist."""

    Base.metadata.create_all(bind=engine)
