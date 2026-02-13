"""SQLAlchemy ORM models used by the underwriting engine."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    postcode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    asking_price: Mapped[float] = mapped_column(Float, nullable=False)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    floor_area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    listing_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    postcode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    price_paid: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_build: Mapped[str | None] = mapped_column(String(5), nullable=True)
    tenure: Mapped[str | None] = mapped_column(String(20), nullable=True)


class RentComp(Base):
    __tablename__ = "rent_comps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    postcode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)


class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    rate_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
