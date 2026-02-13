"""Land Registry CSV ingestion."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from src.db.repository import add_transactions


class LandRegistryCSVIngestor:
    """Ingest UK transaction records from a local CSV file.

    Expected columns (case-insensitive):
    - postcode
    - price_paid
    - date
    - property_type
    - new_build
    - tenure
    """

    REQUIRED_COLUMNS = {
        "postcode": "postcode",
        "price_paid": "price_paid",
        "date": "date",
        "property_type": "property_type",
        "new_build": "new_build",
        "tenure": "tenure",
    }

    def ingest(self, session: Session, csv_path: str | Path) -> int:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Land Registry CSV not found: {path}")

        df = pd.read_csv(path)
        lowered = {col.lower().strip(): col for col in df.columns}
        missing = [col for col in self.REQUIRED_COLUMNS if col not in lowered]
        if missing:
            raise ValueError(f"Land Registry CSV missing columns: {', '.join(missing)}")

        renamed = {
            lowered[src]: dst
            for src, dst in self.REQUIRED_COLUMNS.items()
            if src in lowered
        }
        work = df.rename(columns=renamed).copy()
        work = work[list(self.REQUIRED_COLUMNS.values())]
        work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
        work["price_paid"] = pd.to_numeric(work["price_paid"], errors="coerce")

        work = work.dropna(subset=["postcode", "price_paid", "date"])
        if work.empty:
            return 0

        records = []
        for _, row in work.iterrows():
            date_value = row["date"]
            if not isinstance(date_value, dt.date):
                continue
            records.append(
                {
                    "postcode": str(row["postcode"]).upper().strip(),
                    "price_paid": float(row["price_paid"]),
                    "date": date_value,
                    "property_type": str(row.get("property_type", "")).strip() or None,
                    "new_build": str(row.get("new_build", "")).strip() or None,
                    "tenure": str(row.get("tenure", "")).strip() or None,
                }
            )

        return add_transactions(session, records)
