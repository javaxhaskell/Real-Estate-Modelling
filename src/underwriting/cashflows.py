"""Cash flow projection engine."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from src.underwriting.debt import build_debt_schedule
from src.underwriting.models import UnderwritingInputs


def _monthly_growth_rate(annual_growth: float) -> float:
    return (1 + annual_growth) ** (1 / 12.0) - 1


def project_cash_flows(inputs: UnderwritingInputs, start_date: dt.date | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
    """Project monthly and annual levered cash flows for an investment."""

    if start_date is None:
        start_date = dt.date.today().replace(day=1)

    hold_months = inputs.exit.hold_years * 12
    purchase_price = inputs.purchase_price

    loan_amount = purchase_price * inputs.financing.ltv
    financing_fee = loan_amount * inputs.financing.financing_fee_pct
    acquisition_cost_total = inputs.acquisition_costs.total(purchase_price)

    initial_equity = (purchase_price - loan_amount) + acquisition_cost_total + financing_fee

    debt_schedule = build_debt_schedule(
        loan_amount=loan_amount,
        financing=inputs.financing,
        months=hold_months,
        start_date=start_date,
    )

    growth_m = _monthly_growth_rate(inputs.rental.annual_rent_growth)
    rows: list[dict] = [
        {
            "month": 0,
            "date": start_date,
            "gross_rent": 0.0,
            "vacancy_loss": 0.0,
            "effective_gross_income": 0.0,
            "operating_expenses": 0.0,
            "noi": 0.0,
            "debt_service": 0.0,
            "interest": 0.0,
            "principal": 0.0,
            "levered_cf": -initial_equity,
            "exit_proceeds": 0.0,
            "estimated_value": purchase_price,
            "loan_balance": loan_amount,
            "dscr": np.nan,
            "ltv": loan_amount / purchase_price if purchase_price > 0 else np.nan,
        }
    ]

    for month in range(1, hold_months + 1):
        debt_row = debt_schedule.loc[debt_schedule["month"] == month].iloc[0]
        gross_rent = inputs.rental.market_rent_monthly * ((1 + growth_m) ** (month - 1))
        vacancy_loss = gross_rent * inputs.rental.vacancy_rate
        egi = gross_rent - vacancy_loss
        opex = egi * inputs.rental.operating_expense_ratio
        noi = egi - opex

        debt_service = float(debt_row["payment"])
        interest = float(debt_row["interest"])
        principal = float(debt_row["principal"])
        loan_balance = float(debt_row["closing_balance"])

        annualized_noi = noi * 12
        valuation_cap = inputs.exit.exit_cap_rate if inputs.exit.exit_cap_rate > 0 else 1e-6
        estimated_value = annualized_noi / valuation_cap

        dscr = noi / debt_service if debt_service > 0 else np.nan
        ltv = loan_balance / estimated_value if estimated_value > 0 else np.nan

        levered_cf = noi - debt_service
        exit_proceeds = 0.0

        if month == hold_months:
            if inputs.exit.exit_multiple is not None:
                sale_price = annualized_noi * inputs.exit.exit_multiple
            else:
                sale_price = estimated_value

            net_sale_before_debt = sale_price * (1 - inputs.exit.sales_cost_pct)
            equity_sale_proceeds = net_sale_before_debt - loan_balance
            exit_proceeds = equity_sale_proceeds
            levered_cf += exit_proceeds

        rows.append(
            {
                "month": month,
                "date": (pd.Timestamp(start_date) + pd.DateOffset(months=month)).date(),
                "gross_rent": gross_rent,
                "vacancy_loss": vacancy_loss,
                "effective_gross_income": egi,
                "operating_expenses": opex,
                "noi": noi,
                "debt_service": debt_service,
                "interest": interest,
                "principal": principal,
                "levered_cf": levered_cf,
                "exit_proceeds": exit_proceeds,
                "estimated_value": estimated_value,
                "loan_balance": loan_balance,
                "dscr": dscr,
                "ltv": ltv,
            }
        )

    monthly_df = pd.DataFrame(rows)

    operations = monthly_df.loc[monthly_df["month"] > 0].copy()
    operations["year"] = ((operations["month"] - 1) // 12) + 1
    annual_df = (
        operations.groupby("year", as_index=False)[
            [
                "gross_rent",
                "vacancy_loss",
                "effective_gross_income",
                "operating_expenses",
                "noi",
                "debt_service",
                "interest",
                "principal",
                "levered_cf",
                "exit_proceeds",
            ]
        ]
        .sum()
        .sort_values("year")
    )

    annual_zero = pd.DataFrame(
        [
            {
                "year": 0,
                "gross_rent": 0.0,
                "vacancy_loss": 0.0,
                "effective_gross_income": 0.0,
                "operating_expenses": 0.0,
                "noi": 0.0,
                "debt_service": 0.0,
                "interest": 0.0,
                "principal": 0.0,
                "levered_cf": -initial_equity,
                "exit_proceeds": 0.0,
            }
        ]
    )
    annual_df = pd.concat([annual_zero, annual_df], ignore_index=True)

    return monthly_df, annual_df, debt_schedule, initial_equity
