from __future__ import annotations

import pytest

from src.underwriting.cashflows import project_cash_flows
from src.underwriting.models import (
    AcquisitionCosts,
    ExitAssumptions,
    FinancingAssumptions,
    RentalAssumptions,
    UnderwritingInputs,
)


def test_monthly_noi_calculation_without_debt() -> None:
    inputs = UnderwritingInputs(
        purchase_price=200_000,
        acquisition_costs=AcquisitionCosts(stamp_duty=0, legal_fees=0, broker_fees=0, other_costs=0),
        rental=RentalAssumptions(
            market_rent_monthly=1_000,
            annual_rent_growth=0.0,
            vacancy_rate=0.10,
            operating_expense_ratio=0.20,
        ),
        financing=FinancingAssumptions(
            ltv=0.0,
            annual_interest_rate=0.0,
            amortizing=False,
            term_years=25,
            financing_fee_pct=0.0,
        ),
        exit=ExitAssumptions(
            hold_years=1,
            exit_cap_rate=0.06,
            sales_cost_pct=0.0,
        ),
    )

    monthly, annual, _, initial_equity = project_cash_flows(inputs)
    month1 = monthly.loc[monthly["month"] == 1].iloc[0]

    expected_noi = 1_000 * (1 - 0.10) * (1 - 0.20)
    assert month1["noi"] == pytest.approx(expected_noi, rel=1e-6)
    assert month1["debt_service"] == pytest.approx(0.0)
    assert monthly.loc[monthly["month"] == 0, "levered_cf"].iloc[0] == pytest.approx(-initial_equity)

    year1_noi = annual.loc[annual["year"] == 1, "noi"].iloc[0]
    assert year1_noi == pytest.approx(expected_noi * 12, rel=1e-6)
