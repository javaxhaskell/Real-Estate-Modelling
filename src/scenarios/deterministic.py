"""Deterministic scenario analysis."""

from __future__ import annotations

import copy

import pandas as pd

from src.underwriting.engine import UnderwritingEngine
from src.underwriting.models import UnderwritingInputs


RATE_SHOCK_BPS = [50, 100, 200]
RENT_COMPRESSION_PCT = [0.05, 0.10, 0.15]
EXIT_YIELD_EXPANSION_BPS = [25, 50, 100]


def run_standard_scenarios(
    base_inputs: UnderwritingInputs,
    engine: UnderwritingEngine | None = None,
) -> pd.DataFrame:
    """Run requested deterministic stress scenarios and return metric deltas."""

    model = engine or UnderwritingEngine()
    base_result = model.run(base_inputs)
    base_metrics = base_result.metrics

    rows: list[dict] = []

    for bps in RATE_SHOCK_BPS:
        shocked = copy.deepcopy(base_inputs)
        shocked.financing.annual_interest_rate += bps / 10_000
        result = model.run(shocked)
        rows.append(_row_from_result(f"Rate shock +{bps}bp", result.metrics, base_metrics))

    for pct in RENT_COMPRESSION_PCT:
        shocked = copy.deepcopy(base_inputs)
        shocked.rental.market_rent_monthly *= 1 - pct
        result = model.run(shocked)
        rows.append(_row_from_result(f"Rent compression -{int(pct * 100)}%", result.metrics, base_metrics))

    for bps in EXIT_YIELD_EXPANSION_BPS:
        shocked = copy.deepcopy(base_inputs)
        shocked.exit.exit_cap_rate += bps / 10_000
        result = model.run(shocked)
        rows.append(_row_from_result(f"Exit yield expansion +{bps}bp", result.metrics, base_metrics))

    return pd.DataFrame(rows)


def _row_from_result(name: str, metrics: dict, base_metrics: dict) -> dict:
    irr = metrics.get("irr")
    npv = metrics.get("npv")
    base_irr = base_metrics.get("irr")
    base_npv = base_metrics.get("npv")

    irr_delta = None if irr is None or base_irr is None else irr - base_irr
    npv_delta = None if npv is None or base_npv is None else npv - base_npv

    return {
        "scenario": name,
        "irr": irr,
        "npv": npv,
        "equity_multiple": metrics.get("equity_multiple"),
        "irr_delta": irr_delta,
        "npv_delta": npv_delta,
    }
