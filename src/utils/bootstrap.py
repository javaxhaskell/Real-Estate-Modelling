"""Bootstrap helpers to initialize DB and ingest sample data."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine

from src.adapters.land_registry import LandRegistryCSVIngestor
from src.adapters.listings_mock import MockListingsAdapter
from src.adapters.rates_adapter import RatesSeriesAdapter
from src.adapters.rent_comps_adapter import RentCompsCSVIngestor
from src.db.base import get_session_factory, session_scope
from src.db.init_db import init_db
from src.db.repository import add_listings, add_rates, counts
from src.utils.config import (
    SAMPLE_LISTINGS_PATH,
    SAMPLE_RATES_PATH,
    SAMPLE_RENT_COMPS_PATH,
    SAMPLE_TRANSACTIONS_PATH,
)


def bootstrap_database(
    engine: Engine,
    listings_path: str | Path | None = None,
    transactions_path: str | Path | None = None,
    rates_path: str | Path | None = None,
    rent_comps_path: str | Path | None = None,
) -> dict[str, int]:
    """Create tables and load sample datasets if tables are empty."""

    init_db(engine)
    session_factory = get_session_factory(engine)

    resolved_paths = {
        "listings": Path(listings_path) if listings_path else SAMPLE_LISTINGS_PATH,
        "transactions": Path(transactions_path) if transactions_path else SAMPLE_TRANSACTIONS_PATH,
        "rates": Path(rates_path) if rates_path else SAMPLE_RATES_PATH,
        "rent_comps": Path(rent_comps_path) if rent_comps_path else SAMPLE_RENT_COMPS_PATH,
    }

    inserted = {"listings": 0, "transactions": 0, "rates": 0, "rent_comps": 0}

    with session_scope(session_factory) as session:
        table_counts = counts(session)

        if table_counts["listings"] == 0 and resolved_paths["listings"].exists():
            listings = MockListingsAdapter(resolved_paths["listings"]).fetch_listings()
            inserted["listings"] = add_listings(session, listings)

        if table_counts["transactions"] == 0 and resolved_paths["transactions"].exists():
            inserted["transactions"] = LandRegistryCSVIngestor().ingest(session, resolved_paths["transactions"])

        if table_counts["rates"] == 0:
            rates = RatesSeriesAdapter().load(
                resolved_paths["rates"] if resolved_paths["rates"].exists() else None
            )
            inserted["rates"] = add_rates(session, rates)

        if table_counts["rent_comps"] == 0 and resolved_paths["rent_comps"].exists():
            inserted["rent_comps"] = RentCompsCSVIngestor().ingest(session, resolved_paths["rent_comps"])

    return inserted
