# Automated Real Estate Underwriting Engine (UK)

This is an offline-first Python underwriting project for UK property deals. It reads local datasets (Land Registry transactions, rent comps, a rates curve, and mock listing data), stores what it needs in SQLite, then produces a full leveraged underwriting output. Results can be exported as clean JSON for machines, and also viewed in a Streamlit dashboard for humans.

The code is set up around small adapters so the data sources are swappable. Land Registry and rent comps are ingested from CSV into a SQLite database using SQLAlchemy, listings are loaded through a `ListingsAdapter` interface (defaulting to `MockListingsAdapter` backed by a local JSON file), and rates come from a CSV with a hard-coded fallback curve if nothing is provided. The database layer auto-creates tables on first run.

Underwriting is done with monthly and annual projections, supporting both interest-only and amortising debt schedules. It computes the usual levered metrics (IRR, NPV, equity multiple, cash-on-cash, DSCR, LTV) and includes a handful of practical feature calculations like price per sqft, postcode-level transaction averages and trends, a basic yield estimate with yield spread versus the reference rate, and rule-based vacancy heuristics keyed off property type and postcode prefix.

On top of the base case there is scenario support. You can run deterministic stresses (rates, rent, exit yield) and a Monte Carlo simulation that produces IRR/NPV distributions plus downside probabilities. The Streamlit app also lets you export JSON as well as CSVs for the annual cash flow and the debt schedule.

Repository layout:
.
├── app/
│ └── main.py
├── data/
│ ├── land_registry_sample.csv
│ ├── listings_sample.json
│ ├── rates_sample.csv
│ └── rent_comps_sample.csv
├── src/
│ ├── adapters/
│ ├── db/
│ ├── features/
│ ├── scenarios/
│ ├── underwriting/
│ └── utils/
├── tests/
├── requirements.txt
└── README.md


Setup is straightforward. Create a venv (Python 3.11+), install requirements, run tests, then start Streamlit:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app/main.py

Data sources in the default demo are:

data/listings_sample.json via MockListingsAdapter

data/land_registry_sample.csv via LandRegistryCSVIngestor

data/rent_comps_sample.csv via RentCompsCSVIngestor

data/rates_sample.csv via RatesSeriesAdapter
