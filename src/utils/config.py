"""Project configuration constants."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "underwriting.db"
DEFAULT_DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

SAMPLE_LISTINGS_PATH = DATA_DIR / "listings_sample.json"
SAMPLE_TRANSACTIONS_PATH = DATA_DIR / "land_registry_sample.csv"
SAMPLE_RATES_PATH = DATA_DIR / "rates_sample.csv"
SAMPLE_RENT_COMPS_PATH = DATA_DIR / "rent_comps_sample.csv"
