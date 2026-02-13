"""Rent comparable ingestion utilities."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from src.db.repository import add_rent_comps


class RentCompsCSVIngestor:
    """Load rent comparables from CSV into the local database."""

    REQUIRED_COLUMNS = {
        "postcode": "postcode",
        "monthly_rent": "monthly_rent",
        "bedrooms": "bedrooms",
        "property_type": "property_type",
        "date": "date",
        "source": "source",
    }

    def ingest(self, session: Session, csv_path: str | Path) -> int:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Rent comps CSV not found: {path}")

        df = pd.read_csv(path)
        lowered = {col.lower().strip(): col for col in df.columns}
        missing = [k for k in self.REQUIRED_COLUMNS if k not in lowered]
        if missing:
            raise ValueError(f"Rent comps CSV missing columns: {', '.join(missing)}")

        renamed = {lowered[src]: dst for src, dst in self.REQUIRED_COLUMNS.items()}
        work = df.rename(columns=renamed).copy()
        work = work[list(self.REQUIRED_COLUMNS.values())]

        work["monthly_rent"] = pd.to_numeric(work["monthly_rent"], errors="coerce")
        work["bedrooms"] = pd.to_numeric(work["bedrooms"], errors="coerce").astype("Int64")
        work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
        work = work.dropna(subset=["postcode", "monthly_rent", "date", "source"])

        records: list[dict] = []
        for _, row in work.iterrows():
            date_value = row["date"]
            if not isinstance(date_value, dt.date):
                continue
            bedrooms = row.get("bedrooms")
            bedrooms_int = int(bedrooms) if pd.notna(bedrooms) else None
            records.append(
                {
                    "postcode": str(row["postcode"]).upper().strip(),
                    "monthly_rent": float(row["monthly_rent"]),
                    "bedrooms": bedrooms_int,
                    "property_type": str(row.get("property_type", "")).strip() or None,
                    "date": date_value,
                    "source": str(row.get("source", "")).strip(),
                }
            )

        return add_rent_comps(session, records)
