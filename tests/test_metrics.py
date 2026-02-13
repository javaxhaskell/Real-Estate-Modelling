from __future__ import annotations

import pytest

from src.underwriting.metrics import compute_irr, compute_npv


def test_npv_known_toy_example() -> None:
    cash_flows = [-100.0, 60.0, 60.0]
    npv = compute_npv(cash_flows, annual_discount_rate=0.10, periods_per_year=1)
    assert npv == pytest.approx(4.1322314, rel=1e-6)


def test_irr_known_toy_example() -> None:
    cash_flows = [-100.0, 60.0, 60.0]
    irr = compute_irr(cash_flows, periods_per_year=1)
    assert irr is not None
    assert irr == pytest.approx(0.130662, rel=1e-4)
