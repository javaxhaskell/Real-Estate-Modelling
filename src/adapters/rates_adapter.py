"""Rates adapter for local CSV ingestion with fallback curves."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd


class RatesSeriesAdapter:
    """Load historical rates from CSV or return a default curve."""

    FALLBACK_CURVE = [
        {"date": "2023-01-01", "rate_name": "policy_proxy", "value": 0.0350},
        {"date": "2023-07-01", "rate_name": "policy_proxy", "value": 0.0450},
        {"date": "2024-01-01", "rate_name": "policy_proxy", "value": 0.0525},
        {"date": "2024-07-01", "rate_name": "policy_proxy", "value": 0.0500},
        {"date": "2025-01-01", "rate_name": "policy_proxy", "value": 0.0475},
        {"date": "2025-07-01", "rate_name": "policy_proxy", "value": 0.0450},
    ]

    def load(self, csv_path: str | Path | None = None) -> list[dict]:
        if csv_path is None:
            return self._fallback_records()

        path = Path(csv_path)
        if not path.exists():
            return self._fallback_records()

        df = pd.read_csv(path)
        lowered = {col.lower().strip(): col for col in df.columns}
        required = {"date", "rate_name", "value"}
        if not required.issubset(lowered):
            raise ValueError("Rates CSV must include columns: date, rate_name, value")

        work = df.rename(columns={lowered[k]: k for k in required}).copy()
        work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
        work["value"] = pd.to_numeric(work["value"], errors="coerce")
        work = work.dropna(subset=["date", "rate_name", "value"])

        records: list[dict] = []
        for _, row in work.iterrows():
            date_value = row["date"]
            if not isinstance(date_value, dt.date):
                continue
            records.append(
                {
                    "date": date_value,
                    "rate_name": str(row["rate_name"]).strip(),
                    "value": float(row["value"]),
                }
            )
        return records if records else self._fallback_records()

    def _fallback_records(self) -> list[dict]:
        return [
            {
                "date": dt.datetime.strptime(point["date"], "%Y-%m-%d").date(),
                "rate_name": point["rate_name"],
                "value": float(point["value"]),
            }
            for point in self.FALLBACK_CURVE
        ]
