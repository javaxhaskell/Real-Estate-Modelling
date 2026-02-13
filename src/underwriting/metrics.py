"""Investment return metrics."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def compute_npv(cash_flows: Iterable[float], annual_discount_rate: float, periods_per_year: int = 12) -> float:
    """Compute NPV with a user-defined annual discount rate."""

    cfs = list(cash_flows)
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    periodic_rate = (1 + annual_discount_rate) ** (1 / periods_per_year) - 1
    return float(sum(cf / ((1 + periodic_rate) ** t) for t, cf in enumerate(cfs)))


def _npv_at_rate(cash_flows: list[float], rate: float) -> float:
    return float(sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cash_flows)))


def compute_irr(
    cash_flows: Iterable[float],
    periods_per_year: int = 12,
    tol: float = 1e-7,
    max_iter: int = 200,
) -> float | None:
    """Compute IRR robustly using bounded bisection.

    Returns ``None`` when cash flows do not bracket a valid root or when the
    solver cannot converge within the specified iterations.
    """

    cfs = [float(cf) for cf in cash_flows]
    if not cfs or periods_per_year <= 0:
        return None
    if all(cf >= 0 for cf in cfs) or all(cf <= 0 for cf in cfs):
        return None

    low = -0.9999
    high = 1.0
    f_low = _npv_at_rate(cfs, low)
    f_high = _npv_at_rate(cfs, high)

    # Expand the upper bound until the sign flips or the bound is implausibly high.
    expansion_count = 0
    while f_low * f_high > 0 and high < 100 and expansion_count < 25:
        high *= 2
        f_high = _npv_at_rate(cfs, high)
        expansion_count += 1

    if f_low * f_high > 0:
        return None

    for _ in range(max_iter):
        mid = (low + high) / 2
        f_mid = _npv_at_rate(cfs, mid)
        if abs(f_mid) < tol:
            return float((1 + mid) ** periods_per_year - 1)
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    return None


def equity_multiple(cash_flows: Iterable[float]) -> float | None:
    cfs = [float(cf) for cf in cash_flows]
    invested = -sum(cf for cf in cfs if cf < 0)
    returned = sum(cf for cf in cfs if cf > 0)
    if invested <= 0:
        return None
    return returned / invested


def cash_on_cash(year_one_cash_flow: float, initial_equity: float) -> float | None:
    if initial_equity <= 0:
        return None
    return year_one_cash_flow / initial_equity


def summarize_metrics(
    monthly_cash_flows: pd.DataFrame,
    annual_cash_flows: pd.DataFrame,
    annual_discount_rate: float,
) -> dict[str, float | None]:
    cfs = monthly_cash_flows["levered_cf"].tolist()
    irr = compute_irr(cfs, periods_per_year=12)
    npv = compute_npv(cfs, annual_discount_rate=annual_discount_rate, periods_per_year=12)
    em = equity_multiple(cfs)

    initial_equity = abs(float(monthly_cash_flows.loc[monthly_cash_flows["month"] == 0, "levered_cf"].sum()))
    year_one_cf = float(
        annual_cash_flows.loc[annual_cash_flows["year"] == 1, "levered_cf"].sum()
        if 1 in annual_cash_flows["year"].values
        else 0.0
    )
    coc = cash_on_cash(year_one_cf, initial_equity)

    dscr_series = monthly_cash_flows["dscr"].dropna()
    min_dscr = float(dscr_series.min()) if not dscr_series.empty else None

    ltv_series = monthly_cash_flows["ltv"].dropna()
    max_ltv = float(ltv_series.max()) if not ltv_series.empty else None

    return {
        "irr": irr,
        "npv": npv,
        "equity_multiple": em,
        "cash_on_cash": coc,
        "min_dscr": min_dscr,
        "max_ltv": max_ltv,
    }
