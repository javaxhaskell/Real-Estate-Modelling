"""Tax utilities used by underwriting assumptions."""

from __future__ import annotations


def compute_residential_stamp_duty(purchase_price: float) -> float:
    """Estimate UK residential stamp duty from simplified progressive bands.

    Assumption: standard residential rates (England/NI style banding), no
    first-time buyer relief and no additional dwelling surcharge. Keep this
    configurable when adapting to specific transaction cases.
    """

    if purchase_price < 0:
        raise ValueError("Purchase price must be non-negative")

    bands = [
        (250_000, 0.00),
        (925_000, 0.05),
        (1_500_000, 0.10),
        (float("inf"), 0.12),
    ]

    remaining = purchase_price
    lower = 0.0
    duty = 0.0

    for upper, rate in bands:
        taxable = max(min(remaining, upper - lower), 0.0)
        duty += taxable * rate
        remaining -= taxable
        lower = upper
        if remaining <= 0:
            break

    return duty
