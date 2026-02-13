"""High-level orchestration for full underwriting runs."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.underwriting.cashflows import project_cash_flows
from src.underwriting.metrics import summarize_metrics
from src.underwriting.models import UnderwritingInputs


@dataclass(slots=True)
class UnderwritingResult:
    monthly_cash_flows: pd.DataFrame
    annual_cash_flows: pd.DataFrame
    debt_schedule: pd.DataFrame
    metrics: dict[str, float | None]
    assumptions: UnderwritingInputs

    def to_dict(self) -> dict[str, Any]:
        """Serialize result into a JSON-friendly structure."""

        def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
            payload: list[dict[str, Any]] = []
            for row in df.to_dict(orient="records"):
                converted: dict[str, Any] = {}
                for key, value in row.items():
                    if isinstance(value, dt.date):
                        converted[key] = value.isoformat()
                    elif pd.isna(value):
                        converted[key] = None
                    else:
                        converted[key] = value
                payload.append(converted)
            return payload

        return {
            "metrics": self.metrics,
            "monthly_cash_flows": _records(self.monthly_cash_flows),
            "annual_cash_flows": _records(self.annual_cash_flows),
            "debt_schedule": _records(self.debt_schedule),
        }


class UnderwritingEngine:
    """Runs cash flow projection + metric computation."""

    def run(self, inputs: UnderwritingInputs, start_date: dt.date | None = None) -> UnderwritingResult:
        monthly_df, annual_df, debt_df, _ = project_cash_flows(inputs, start_date=start_date)
        metrics = summarize_metrics(
            monthly_cash_flows=monthly_df,
            annual_cash_flows=annual_df,
            annual_discount_rate=inputs.discount_rate,
        )
        return UnderwritingResult(
            monthly_cash_flows=monthly_df,
            annual_cash_flows=annual_df,
            debt_schedule=debt_df,
            metrics=metrics,
            assumptions=inputs,
        )
