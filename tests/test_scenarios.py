from __future__ import annotations

from src.scenarios.deterministic import run_standard_scenarios
from src.scenarios.monte_carlo import MonteCarloConfig, run_monte_carlo
from src.underwriting.engine import UnderwritingEngine
from src.underwriting.models import UnderwritingInputs


def test_deterministic_scenarios_shape_and_integrity(base_inputs: UnderwritingInputs) -> None:
    engine = UnderwritingEngine()

    scenario_df = run_standard_scenarios(base_inputs, engine=engine)

    assert len(scenario_df) == 9
    assert set(["scenario", "irr", "npv", "irr_delta", "npv_delta"]).issubset(scenario_df.columns)
    assert base_inputs.financing.annual_interest_rate == 0.05


def test_monte_carlo_summary_and_sample_size(base_inputs: UnderwritingInputs) -> None:
    engine = UnderwritingEngine()

    output = run_monte_carlo(
        base_inputs,
        config=MonteCarloConfig(n_simulations=200, seed=7, target_hurdle_irr=0.10),
        engine=engine,
    )

    sims = output["simulations"]
    summary = output["summary"]

    assert len(sims) == 200
    assert "irr_p50" in summary
    assert "prob_irr_below_hurdle" in summary
    assert summary["prob_irr_below_hurdle"] is None or 0.0 <= summary["prob_irr_below_hurdle"] <= 1.0
