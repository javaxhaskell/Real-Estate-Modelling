"""Streamlit app for the automated UK real estate underwriting engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.adapters.land_registry import LandRegistryCSVIngestor
from src.adapters.rates_adapter import RatesSeriesAdapter
from src.db.base import get_engine, get_session_factory, session_scope
from src.db.repository import add_rates, average_rent_for_postcode, get_listing_by_id, list_listings
from src.features.engineering import build_feature_bundle
from src.scenarios.deterministic import run_standard_scenarios
from src.scenarios.monte_carlo import MonteCarloConfig, run_monte_carlo
from src.underwriting.engine import UnderwritingEngine
from src.underwriting.models import (
    AcquisitionCosts,
    ExitAssumptions,
    FinancingAssumptions,
    RentalAssumptions,
    UnderwritingInputs,
)
from src.utils.bootstrap import bootstrap_database
from src.utils.config import (
    DEFAULT_DB_URL,
    SAMPLE_RATES_PATH,
    SAMPLE_TRANSACTIONS_PATH,
)

st.set_page_config(page_title="UK Underwriting Engine", page_icon="🏠", layout="wide")


@st.cache_resource
def get_runtime(db_url: str):
    engine = get_engine(db_url)
    bootstrap_database(engine)
    return engine, get_session_factory(engine)


def _money(value: float | None) -> str:
    return "N/A" if value is None else f"£{value:,.0f}"


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.2f}%"


def _safe_float(value: float | None, fallback: float) -> float:
    return fallback if value is None or (isinstance(value, float) and np.isnan(value)) else float(value)


def _json_default(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Unsupported type for JSON serialization: {type(value)!r}")


_engine_sql, session_factory = get_runtime(DEFAULT_DB_URL)
model_engine = UnderwritingEngine()

st.title("Automated Real Estate Underwriting Engine (UK)")
st.caption("Offline-ready underwriting with modular ingestion, deterministic scenarios, and Monte Carlo simulation.")

with st.sidebar:
    st.header("Data Ingestion")
    land_registry_path = st.text_input("Land Registry CSV path", value=str(SAMPLE_TRANSACTIONS_PATH))
    rates_path = st.text_input("Rates CSV path", value=str(SAMPLE_RATES_PATH))

    if st.button("Ingest Land Registry CSV"):
        try:
            with session_scope(session_factory) as session:
                inserted = LandRegistryCSVIngestor().ingest(session, land_registry_path)
            st.success(f"Inserted {inserted} transaction rows.")
        except Exception as exc:
            st.error(f"Failed to ingest Land Registry data: {exc}")

    if st.button("Ingest Rates CSV"):
        try:
            with session_scope(session_factory) as session:
                records = RatesSeriesAdapter().load(rates_path)
                inserted = add_rates(session, records)
            st.success(f"Inserted {inserted} rate rows.")
        except Exception as exc:
            st.error(f"Failed to ingest rates data: {exc}")

with session_scope(session_factory) as session:
    listings = list_listings(session)

if not listings:
    st.error("No listings available. Add listings via sample data/bootstrap before underwriting.")
    st.stop()

listing_options = {
    f"{l.id} | {l.address} | {l.postcode} | £{l.asking_price:,.0f}": l.id for l in listings
}
selected_label = st.selectbox("Select Property", options=list(listing_options.keys()))
selected_id = listing_options[selected_label]

with session_scope(session_factory) as session:
    selected_listing = get_listing_by_id(session, selected_id)
    avg_rent = average_rent_for_postcode(session, selected_listing.postcode) if selected_listing else None

if selected_listing is None:
    st.error("Selected listing not found.")
    st.stop()

default_rent = avg_rent if avg_rent is not None else (selected_listing.asking_price * 0.05 / 12)

with session_scope(session_factory) as session:
    feature_preview = build_feature_bundle(
        session=session,
        listing=selected_listing,
        market_rent_monthly=default_rent,
        purchase_price=selected_listing.asking_price,
    )

tab_selection, tab_underwrite = st.tabs(["Property Selection", "Underwriting Dashboard"])

with tab_selection:
    st.subheader("Selected Listing")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Asking Price", _money(selected_listing.asking_price))
    col_b.metric("Bedrooms", str(selected_listing.bedrooms) if selected_listing.bedrooms is not None else "N/A")
    col_c.metric("Property Type", selected_listing.property_type or "N/A")

    st.write(
        {
            "address": selected_listing.address,
            "postcode": selected_listing.postcode,
            "bathrooms": selected_listing.bathrooms,
            "floor_area_sqft": selected_listing.floor_area_sqft,
            "listing_date": str(selected_listing.listing_date) if selected_listing.listing_date else None,
            "source": selected_listing.source,
        }
    )

    st.subheader("Feature Engineering Snapshot")
    st.json(feature_preview)

with tab_underwrite:
    st.subheader("Input Assumptions")

    c1, c2, c3 = st.columns(3)
    with c1:
        purchase_price = st.number_input(
            "Purchase Price (£)",
            min_value=50_000.0,
            value=float(selected_listing.asking_price),
            step=1_000.0,
        )
        market_rent = st.number_input(
            "Market Rent / Month (£)",
            min_value=100.0,
            value=float(default_rent),
            step=25.0,
        )
        annual_growth = st.slider("Annual Rent Growth", min_value=-0.05, max_value=0.10, value=0.02, step=0.005)

    with c2:
        default_vacancy = _safe_float(feature_preview.get("vacancy_heuristic"), 0.05)
        vacancy = st.slider("Vacancy Rate", min_value=0.0, max_value=0.25, value=float(default_vacancy), step=0.005)
        opex_ratio = st.slider("Operating Expense Ratio", min_value=0.05, max_value=0.60, value=0.30, step=0.01)
        discount_rate = st.slider("Discount Rate (NPV)", min_value=0.00, max_value=0.20, value=0.08, step=0.005)

    with c3:
        auto_stamp = st.checkbox("Auto Stamp Duty", value=True)
        stamp_duty = None
        if not auto_stamp:
            stamp_duty = st.number_input("Stamp Duty (£)", min_value=0.0, value=0.0, step=100.0)
        legal_fees = st.number_input("Legal Fees (£)", min_value=0.0, value=1_500.0, step=100.0)
        broker_fees = st.number_input("Broker Fees (£)", min_value=0.0, value=0.0, step=100.0)
        other_costs = st.number_input("Other Acquisition Costs (£)", min_value=0.0, value=0.0, step=100.0)

    st.markdown("---")
    st.subheader("Financing and Exit")

    f1, f2, f3 = st.columns(3)
    with f1:
        ltv = st.slider("LTV", min_value=0.0, max_value=0.90, value=0.75, step=0.01)
        interest_rate = st.slider("Loan Interest Rate", min_value=0.0, max_value=0.15, value=0.05, step=0.001)
        amortizing = st.checkbox("Amortizing Loan", value=False)

    with f2:
        term_years = st.number_input("Loan Term (years)", min_value=1, max_value=40, value=25)
        financing_fee_pct = st.slider("Financing Fee %", min_value=0.0, max_value=0.05, value=0.01, step=0.001)
        hold_years = st.number_input("Hold Period (years)", min_value=1, max_value=20, value=5)

    with f3:
        exit_method = st.radio("Exit Valuation Method", options=["Cap Rate", "NOI Multiple"], horizontal=False)
        exit_cap_rate = st.slider("Exit Cap Rate", min_value=0.03, max_value=0.15, value=0.06, step=0.001)
        exit_multiple = None
        if exit_method == "NOI Multiple":
            exit_multiple = st.number_input("Exit NOI Multiple", min_value=1.0, max_value=40.0, value=16.0, step=0.1)
        sales_cost_pct = st.slider("Sales Cost %", min_value=0.0, max_value=0.10, value=0.02, step=0.001)

    st.markdown("---")
    st.subheader("Scenario / Monte Carlo")
    s1, s2 = st.columns(2)
    with s1:
        n_sims = st.number_input("Monte Carlo Simulations", min_value=100, max_value=10_000, value=2_000, step=100)
    with s2:
        hurdle_irr = st.slider("IRR Hurdle", min_value=0.00, max_value=0.30, value=0.12, step=0.005)

    run_clicked = st.button("Run Underwriting", type="primary")

    if run_clicked:
        try:
            assumptions = UnderwritingInputs(
                purchase_price=purchase_price,
                acquisition_costs=AcquisitionCosts(
                    stamp_duty=stamp_duty,
                    legal_fees=legal_fees,
                    broker_fees=broker_fees,
                    other_costs=other_costs,
                ),
                rental=RentalAssumptions(
                    market_rent_monthly=market_rent,
                    annual_rent_growth=annual_growth,
                    vacancy_rate=vacancy,
                    operating_expense_ratio=opex_ratio,
                ),
                financing=FinancingAssumptions(
                    ltv=ltv,
                    annual_interest_rate=interest_rate,
                    amortizing=amortizing,
                    term_years=int(term_years),
                    financing_fee_pct=financing_fee_pct,
                ),
                exit=ExitAssumptions(
                    hold_years=int(hold_years),
                    exit_cap_rate=exit_cap_rate,
                    exit_multiple=exit_multiple,
                    sales_cost_pct=sales_cost_pct,
                ),
                discount_rate=discount_rate,
                target_hurdle_irr=hurdle_irr,
            )

            result = model_engine.run(assumptions)
            scenario_df = run_standard_scenarios(assumptions, engine=model_engine)
            mc = run_monte_carlo(
                base_inputs=assumptions,
                config=MonteCarloConfig(
                    n_simulations=int(n_sims),
                    target_hurdle_irr=hurdle_irr,
                ),
                engine=model_engine,
            )

            export_payload = result.to_dict()
            export_payload["listing"] = {
                "id": selected_listing.id,
                "address": selected_listing.address,
                "postcode": selected_listing.postcode,
            }
            export_payload["features"] = feature_preview
            export_payload["deterministic_scenarios"] = scenario_df.to_dict(orient="records")
            export_payload["monte_carlo_summary"] = mc["summary"]

            st.session_state["uw_result"] = result
            st.session_state["uw_scenarios"] = scenario_df
            st.session_state["uw_mc"] = mc
            st.session_state["uw_export"] = export_payload
        except Exception as exc:
            st.error(f"Underwriting run failed: {exc}")

    if "uw_result" in st.session_state:
        result = st.session_state["uw_result"]
        scenario_df = st.session_state["uw_scenarios"]
        mc = st.session_state["uw_mc"]
        export_payload = st.session_state["uw_export"]

        st.subheader("Key Metrics")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("IRR", _pct(result.metrics.get("irr")))
        k2.metric("NPV", _money(result.metrics.get("npv")))
        k3.metric("Equity Multiple", f"{result.metrics.get('equity_multiple', float('nan')):.2f}x" if result.metrics.get("equity_multiple") is not None else "N/A")
        k4.metric("Cash-on-Cash", _pct(result.metrics.get("cash_on_cash")))
        k5.metric("Min DSCR", f"{result.metrics.get('min_dscr', float('nan')):.2f}" if result.metrics.get("min_dscr") is not None else "N/A")

        st.subheader("Tables")
        st.markdown("Annual Cash Flow")
        st.dataframe(result.annual_cash_flows, use_container_width=True)
        st.markdown("Debt Schedule")
        st.dataframe(result.debt_schedule, use_container_width=True)

        st.subheader("Charts")
        cf_chart_df = result.monthly_cash_flows.loc[result.monthly_cash_flows["month"] > 0, ["date", "levered_cf"]].set_index("date")
        st.markdown("Cash Flow Over Time")
        st.line_chart(cf_chart_df)

        dscr_df = result.monthly_cash_flows[["date", "dscr"]].dropna().set_index("date")
        if not dscr_df.empty:
            st.markdown("DSCR Over Time")
            st.line_chart(dscr_df)

        st.markdown("Monte Carlo IRR Distribution")
        irr_values = (mc["simulations"]["irr"].dropna() * 100).to_numpy()
        if irr_values.size > 0:
            counts, bins = np.histogram(irr_values, bins=30)
            hist_df = pd.DataFrame({"IRR (%)": bins[:-1], "count": counts}).set_index("IRR (%)")
            st.bar_chart(hist_df)
        else:
            st.info("No valid IRR outcomes available for histogram.")

        st.markdown("Scenario Tornado (NPV Delta)")
        tornado = scenario_df.dropna(subset=["npv_delta"]).sort_values("npv_delta")
        if not tornado.empty:
            st.bar_chart(tornado.set_index("scenario")[["npv_delta"]])

        st.subheader("Monte Carlo Summary")
        st.json(mc["summary"])

        st.subheader("Export")
        st.download_button(
            label="Export Underwriting JSON",
            data=json.dumps(export_payload, indent=2, default=_json_default),
            file_name="underwriting_result.json",
            mime="application/json",
        )
        st.download_button(
            label="Export Annual Cash Flows CSV",
            data=result.annual_cash_flows.to_csv(index=False),
            file_name="annual_cash_flows.csv",
            mime="text/csv",
        )
        st.download_button(
            label="Export Debt Schedule CSV",
            data=result.debt_schedule.to_csv(index=False),
            file_name="debt_schedule.csv",
            mime="text/csv",
        )
