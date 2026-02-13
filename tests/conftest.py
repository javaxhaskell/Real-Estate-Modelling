"""Shared fixtures for underwriting tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.underwriting.models import (
    AcquisitionCosts,
    ExitAssumptions,
    FinancingAssumptions,
    RentalAssumptions,
    UnderwritingInputs,
)


def make_base_inputs() -> UnderwritingInputs:
    return UnderwritingInputs(
        purchase_price=250_000,
        acquisition_costs=AcquisitionCosts(stamp_duty=2_500, legal_fees=1_000, broker_fees=500, other_costs=0),
        rental=RentalAssumptions(
            market_rent_monthly=1_450,
            annual_rent_growth=0.02,
            vacancy_rate=0.05,
            operating_expense_ratio=0.30,
        ),
        financing=FinancingAssumptions(
            ltv=0.70,
            annual_interest_rate=0.05,
            amortizing=False,
            term_years=25,
            financing_fee_pct=0.01,
        ),
        exit=ExitAssumptions(
            hold_years=5,
            exit_cap_rate=0.06,
            exit_multiple=None,
            sales_cost_pct=0.02,
        ),
        discount_rate=0.08,
        target_hurdle_irr=0.12,
    )


@pytest.fixture
def base_inputs() -> UnderwritingInputs:
    return make_base_inputs()
