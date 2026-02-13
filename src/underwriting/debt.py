"""Debt schedule modelling."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from src.underwriting.models import FinancingAssumptions


def build_debt_schedule(
    loan_amount: float,
    financing: FinancingAssumptions,
    months: int,
    start_date: dt.date,
) -> pd.DataFrame:
    """Construct a monthly debt schedule.

    Supports amortizing and interest-only structures. For interest-only loans,
    principal is repaid in a balloon payment at term maturity (or at sale if
    hold period ends earlier).
    """

    if loan_amount < 0:
        raise ValueError("loan_amount must be non-negative")
    if months <= 0:
        raise ValueError("months must be positive")

    term_months = financing.term_years * 12
    monthly_rate = financing.annual_interest_rate / 12.0
    balance = float(loan_amount)

    if financing.amortizing and term_months > 0:
        if monthly_rate == 0:
            scheduled_payment = balance / term_months
        else:
            scheduled_payment = balance * monthly_rate / (1 - (1 + monthly_rate) ** (-term_months))
    else:
        scheduled_payment = 0.0

    rows: list[dict] = []
    for month in range(1, months + 1):
        payment_date = (pd.Timestamp(start_date) + pd.DateOffset(months=month)).date()
        opening_balance = balance

        interest = 0.0
        principal = 0.0
        payment = 0.0

        if month <= term_months and opening_balance > 0:
            interest = opening_balance * monthly_rate
            if financing.amortizing:
                principal = min(scheduled_payment - interest, opening_balance)
                payment = interest + principal
            else:
                # Interest-only coupon, with balloon at contractual maturity.
                principal = opening_balance if month == term_months else 0.0
                payment = interest + principal

        closing_balance = max(opening_balance - principal, 0.0)
        balance = closing_balance

        rows.append(
            {
                "month": month,
                "date": payment_date,
                "opening_balance": opening_balance,
                "interest": interest,
                "principal": principal,
                "payment": payment,
                "closing_balance": closing_balance,
            }
        )

    return pd.DataFrame(rows)
