"""Query helpers and persistence utilities."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, is_dataclass
from typing import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Listing, Rate, RentComp, Transaction


def _normalize_item(item: object) -> dict:
    if is_dataclass(item):
        return asdict(item)
    if isinstance(item, dict):
        return item
    raise TypeError(f"Unsupported item type: {type(item)!r}")


def add_listings(session: Session, listings: Iterable[dict | object]) -> int:
    payload = [_normalize_item(item) for item in listings]
    if not payload:
        return 0
    session.add_all([Listing(**row) for row in payload])
    return len(payload)


def add_transactions(session: Session, transactions: Iterable[dict | object]) -> int:
    payload = [_normalize_item(item) for item in transactions]
    if not payload:
        return 0
    session.add_all([Transaction(**row) for row in payload])
    return len(payload)


def add_rent_comps(session: Session, comps: Iterable[dict | object]) -> int:
    payload = [_normalize_item(item) for item in comps]
    if not payload:
        return 0
    session.add_all([RentComp(**row) for row in payload])
    return len(payload)


def add_rates(session: Session, rates: Iterable[dict | object]) -> int:
    payload = [_normalize_item(item) for item in rates]
    if not payload:
        return 0
    session.add_all([Rate(**row) for row in payload])
    return len(payload)


def list_listings(session: Session) -> list[Listing]:
    stmt = select(Listing).order_by(Listing.listing_date.desc(), Listing.id.asc())
    return list(session.scalars(stmt).all())


def get_listing_by_id(session: Session, listing_id: int) -> Listing | None:
    stmt = select(Listing).where(Listing.id == listing_id)
    return session.scalars(stmt).first()


def list_rates(session: Session, rate_name: str | None = None) -> list[Rate]:
    stmt = select(Rate)
    if rate_name:
        stmt = stmt.where(Rate.rate_name == rate_name)
    stmt = stmt.order_by(Rate.date.asc())
    return list(session.scalars(stmt).all())


def latest_rate_value(session: Session, rate_name: str) -> float | None:
    stmt = (
        select(Rate.value)
        .where(Rate.rate_name == rate_name)
        .order_by(Rate.date.desc())
        .limit(1)
    )
    value = session.scalar(stmt)
    return float(value) if value is not None else None


def average_rent_for_postcode(session: Session, postcode: str) -> float | None:
    stmt = select(func.avg(RentComp.monthly_rent)).where(RentComp.postcode == postcode)
    value = session.scalar(stmt)
    return float(value) if value is not None else None


def transactions_for_postcode(session: Session, postcode: str) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.postcode == postcode).order_by(Transaction.date.asc())
    return list(session.scalars(stmt).all())


def counts(session: Session) -> dict[str, int]:
    tables: Sequence[tuple[str, type]] = (
        ("listings", Listing),
        ("transactions", Transaction),
        ("rent_comps", RentComp),
        ("rates", Rate),
    )
    return {name: int(session.scalar(select(func.count()).select_from(model)) or 0) for name, model in tables}


def delete_all(session: Session) -> None:
    """Delete all records from all tables (useful for tests)."""

    session.query(Listing).delete()
    session.query(Transaction).delete()
    session.query(RentComp).delete()
    session.query(Rate).delete()


def coerce_date(value: dt.date | str) -> dt.date:
    if isinstance(value, dt.date):
        return value
    return dt.datetime.strptime(value, "%Y-%m-%d").date()
