# Automated Real Estate Underwriting Engine (UK-focused)

Offline-first Python project that ingests UK property data and produces complete leveraged underwriting outputs in both machine-readable JSON and a human-friendly Streamlit dashboard.

## Highlights

- Modular adapters for ingestion:
  - Land Registry CSV ingestion into SQLite
  - `ListingsAdapter` interface with:
    - `MockListingsAdapter` (local JSON)
    - `PlaceholderListingsAPIAdapter` (explicit integration placeholder)
  - Rates adapter from CSV with hard-coded fallback curve
- SQLAlchemy + SQLite data layer with auto-create tables
- Underwriting engine:
  - Monthly + annual cash flow projections
  - Interest-only and amortizing debt schedules
  - Levered cash flow metrics: IRR, NPV, Equity Multiple, Cash-on-Cash, DSCR, LTV
- Feature engineering:
  - Price per sqft
  - Postcode transaction averages/trend
  - Yield estimate + yield spread versus reference rate
  - Rule-based vacancy heuristics by property type + postcode prefix
- Scenario analysis:
  - Deterministic stresses (rates/rent/exit yield)
  - Monte Carlo simulation (IRR/NPV distributions + downside probabilities)
- Streamlit dashboard with exports:
  - JSON export
  - CSV export for annual cash flow and debt schedule

## Repository Structure

```
.
├── app/
│   └── main.py
├── data/
│   ├── land_registry_sample.csv
│   ├── listings_sample.json
│   ├── rates_sample.csv
│   └── rent_comps_sample.csv
├── src/
│   ├── adapters/
│   ├── db/
│   ├── features/
│   ├── scenarios/
│   ├── underwriting/
│   └── utils/
├── tests/
├── requirements.txt
└── README.md
```

## Setup

1. Create and activate a virtual environment (Python 3.11+):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run tests:

```bash
pytest -q
```

4. Launch Streamlit:

```bash
streamlit run app/main.py
```

The app bootstraps the SQLite DB and sample data automatically on first run.

## Data & Ingestion

- Listings: `data/listings_sample.json` loaded via `MockListingsAdapter`
- Transactions: `data/land_registry_sample.csv` loaded via `LandRegistryCSVIngestor`
- Rent comps: `data/rent_comps_sample.csv` loaded via `RentCompsCSVIngestor`
- Rates: `data/rates_sample.csv` loaded via `RatesSeriesAdapter`

You can also ingest alternative local CSV paths from the Streamlit sidebar.

## Core Assumptions

- Stamp duty defaults to a simplified UK residential progressive band model when not manually provided.
- Debt supports:
  - Amortizing annuity schedule
  - Interest-only coupon with balloon repayment at term
- Exit valuation supports either:
  - Exit cap rate on annualized NOI
  - NOI multiple
- Monte Carlo variables sampled with clipped normal distributions:
  - Rent growth
  - Vacancy
  - Exit cap rate
  - Interest rate

All assumptions are explicit and configurable in code and UI.

## Testing Coverage

Included unit tests validate:

- Debt schedule correctness
- Cash flow and NOI math
- IRR/NPV against known toy examples
- Deterministic scenario integrity and Monte Carlo shape/summary outputs

## Compliance Note

This project intentionally does **not** scrape Rightmove/Zoopla. It uses local mock data and a clear placeholder adapter for future official API integrations.
