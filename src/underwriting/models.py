"""Domain model for underwriting assumptions and outputs."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.tax import compute_residential_stamp_duty


@dataclass(slots=True)
class AcquisitionCosts:
    """Acquisition cost assumptions.

    ``stamp_duty`` can be omitted; if so, a simplified stamp duty estimate is
    derived from purchase price.
    """

    stamp_duty: float | None = None
    legal_fees: float = 1_500.0
    broker_fees: float = 0.0
    other_costs: float = 0.0

    def total(self, purchase_price: float) -> float:
        stamp = self.stamp_duty
        if stamp is None:
            stamp = compute_residential_stamp_duty(purchase_price)
        components = [stamp, self.legal_fees, self.broker_fees, self.other_costs]
        if any(value < 0 for value in components):
            raise ValueError("Acquisition cost components must be non-negative")
        return float(sum(components))


@dataclass(slots=True)
class RentalAssumptions:
    market_rent_monthly: float
    annual_rent_growth: float = 0.02
    vacancy_rate: float = 0.05
    operating_expense_ratio: float = 0.30

    def __post_init__(self) -> None:
        if self.market_rent_monthly <= 0:
            raise ValueError("market_rent_monthly must be > 0")
        if not -0.25 <= self.annual_rent_growth <= 0.25:
            raise ValueError("annual_rent_growth outside reasonable bounds")
        if not 0 <= self.vacancy_rate <= 0.95:
            raise ValueError("vacancy_rate must be between 0 and 0.95")
        if not 0 <= self.operating_expense_ratio <= 0.95:
            raise ValueError("operating_expense_ratio must be between 0 and 0.95")


@dataclass(slots=True)
class FinancingAssumptions:
    ltv: float = 0.75
    annual_interest_rate: float = 0.05
    amortizing: bool = False
    term_years: int = 25
    financing_fee_pct: float = 0.01

    def __post_init__(self) -> None:
        if not 0 <= self.ltv <= 0.95:
            raise ValueError("ltv must be between 0 and 0.95")
        if not 0 <= self.annual_interest_rate <= 0.25:
            raise ValueError("annual_interest_rate out of bounds")
        if self.term_years <= 0:
            raise ValueError("term_years must be positive")
        if not 0 <= self.financing_fee_pct <= 0.10:
            raise ValueError("financing_fee_pct must be between 0 and 0.10")


@dataclass(slots=True)
class ExitAssumptions:
    hold_years: int = 5
    exit_cap_rate: float = 0.06
    exit_multiple: float | None = None
    sales_cost_pct: float = 0.02

    def __post_init__(self) -> None:
        if self.hold_years <= 0:
            raise ValueError("hold_years must be positive")
        if self.exit_multiple is None and self.exit_cap_rate <= 0:
            raise ValueError("exit_cap_rate must be > 0 when exit_multiple is unset")
        if self.exit_multiple is not None and self.exit_multiple <= 0:
            raise ValueError("exit_multiple must be > 0")
        if not 0 <= self.sales_cost_pct <= 0.20:
            raise ValueError("sales_cost_pct must be between 0 and 0.20")


@dataclass(slots=True)
class UnderwritingInputs:
    purchase_price: float
    acquisition_costs: AcquisitionCosts = field(default_factory=AcquisitionCosts)
    rental: RentalAssumptions = field(default_factory=lambda: RentalAssumptions(market_rent_monthly=1_500.0))
    financing: FinancingAssumptions = field(default_factory=FinancingAssumptions)
    exit: ExitAssumptions = field(default_factory=ExitAssumptions)
    discount_rate: float = 0.08
    target_hurdle_irr: float = 0.12

    def __post_init__(self) -> None:
        if self.purchase_price <= 0:
            raise ValueError("purchase_price must be > 0")
        if not -0.50 <= self.discount_rate <= 0.50:
            raise ValueError("discount_rate out of bounds")
        if not -0.50 <= self.target_hurdle_irr <= 1.0:
            raise ValueError("target_hurdle_irr out of bounds")
