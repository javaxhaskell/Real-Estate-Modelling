"""Feature engineering for listing and market context."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.db.models import Listing
from src.db.repository import latest_rate_value, transactions_for_postcode


@dataclass(slots=True)
class VacancyHeuristicConfig:
    """Rule-based vacancy heuristics by property type and postcode prefix."""

    base_by_property_type: dict[str, float] = field(
        default_factory=lambda: {
            "flat": 0.06,
            "apartment": 0.06,
            "terraced": 0.05,
            "semi-detached": 0.045,
            "detached": 0.04,
            "house": 0.05,
        }
    )
    postcode_prefix_adjustment: dict[str, float] = field(
        default_factory=lambda: {
            "E": -0.005,
            "EC": -0.01,
            "W": -0.005,
            "SW": -0.005,
            "M": 0.0,
            "B": 0.005,
            "L": 0.0075,
        }
    )
    fallback_rate: float = 0.055


def compute_price_per_sqft(asking_price: float, floor_area_sqft: float | None) -> float | None:
    if floor_area_sqft is None or floor_area_sqft <= 0:
        return None
    return asking_price / floor_area_sqft


def compute_postcode_transaction_stats(session: Session, postcode: str) -> dict[str, float | None]:
    txns = transactions_for_postcode(session, postcode)
    if not txns:
        return {
            "postcode_avg_transaction_price": None,
            "postcode_transaction_trend_annual_pct": None,
            "postcode_transaction_count": 0,
        }

    df = pd.DataFrame(
        {
            "date": [t.date for t in txns],
            "price_paid": [t.price_paid for t in txns],
        }
    ).sort_values("date")

    avg_price = float(df["price_paid"].mean())

    trend_pct = None
    if len(df) >= 3:
        month_index = df["date"].map(lambda d: d.year * 12 + d.month).to_numpy(dtype=float)
        prices = df["price_paid"].to_numpy(dtype=float)
        slope, _ = np.polyfit(month_index, prices, deg=1)
        trend_pct = float((slope * 12) / avg_price) if avg_price != 0 else None

    return {
        "postcode_avg_transaction_price": avg_price,
        "postcode_transaction_trend_annual_pct": trend_pct,
        "postcode_transaction_count": int(len(df)),
    }


def compute_yield_estimate(monthly_rent: float, purchase_price: float) -> float | None:
    if purchase_price <= 0:
        return None
    return (monthly_rent * 12) / purchase_price


def compute_yield_spread(yield_estimate: float | None, reference_rate: float | None) -> float | None:
    if yield_estimate is None or reference_rate is None:
        return None
    return yield_estimate - reference_rate


def estimate_vacancy_rate(
    property_type: str | None,
    postcode: str,
    config: VacancyHeuristicConfig | None = None,
) -> float:
    cfg = config or VacancyHeuristicConfig()
    ptype = (property_type or "").strip().lower()

    base = cfg.base_by_property_type.get(ptype, cfg.fallback_rate)

    postcode_upper = postcode.upper().replace(" ", "")
    adjustment = 0.0
    for prefix, value in cfg.postcode_prefix_adjustment.items():
        if postcode_upper.startswith(prefix):
            adjustment = value
            break

    return float(np.clip(base + adjustment, 0.01, 0.20))


def build_feature_bundle(
    session: Session,
    listing: Listing,
    market_rent_monthly: float,
    purchase_price: float | None = None,
    reference_rate_name: str = "policy_proxy",
) -> dict[str, float | int | None]:
    """Return engineered features used by underwriting and UI defaults."""

    effective_price = purchase_price if purchase_price is not None else listing.asking_price

    ppsf = compute_price_per_sqft(listing.asking_price, listing.floor_area_sqft)
    postcode_stats = compute_postcode_transaction_stats(session, listing.postcode)
    yield_est = compute_yield_estimate(market_rent_monthly, effective_price)
    ref_rate = latest_rate_value(session, reference_rate_name)
    spread = compute_yield_spread(yield_est, ref_rate)
    vacancy = estimate_vacancy_rate(listing.property_type, listing.postcode)

    return {
        "price_per_sqft": ppsf,
        "yield_estimate": yield_est,
        "reference_rate": ref_rate,
        "yield_spread": spread,
        "vacancy_heuristic": vacancy,
        **postcode_stats,
    }
