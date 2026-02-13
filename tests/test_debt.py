from __future__ import annotations

import datetime as dt

import pytest

from src.underwriting.debt import build_debt_schedule
from src.underwriting.models import FinancingAssumptions


def test_amortizing_schedule_fully_repaid_at_term() -> None:
    financing = FinancingAssumptions(
        ltv=0.7,
        annual_interest_rate=0.06,
        amortizing=True,
        term_years=2,
        financing_fee_pct=0.0,
    )
    schedule = build_debt_schedule(
        loan_amount=120_000,
        financing=financing,
        months=24,
        start_date=dt.date(2025, 1, 1),
    )

    assert len(schedule) == 24
    assert schedule["payment"].iloc[0] == pytest.approx(schedule["payment"].iloc[1], rel=1e-6)
    assert schedule["closing_balance"].iloc[-1] == pytest.approx(0.0, abs=1e-2)


def test_interest_only_has_balloon_payment() -> None:
    financing = FinancingAssumptions(
        ltv=0.75,
        annual_interest_rate=0.05,
        amortizing=False,
        term_years=1,
        financing_fee_pct=0.0,
    )
    schedule = build_debt_schedule(
        loan_amount=100_000,
        financing=financing,
        months=12,
        start_date=dt.date(2025, 1, 1),
    )

    # Month 1 should be interest-only.
    assert schedule.loc[0, "principal"] == pytest.approx(0.0)
    # Final month carries the balloon principal payoff.
    assert schedule.loc[11, "principal"] == pytest.approx(100_000, rel=1e-6)
    assert schedule.loc[11, "closing_balance"] == pytest.approx(0.0, abs=1e-6)
