"""Monte Carlo simulation for underwriting uncertainty."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.underwriting.engine import UnderwritingEngine
from src.underwriting.models import UnderwritingInputs


@dataclass(slots=True)
class MonteCarloConfig:
    n_simulations: int = 2_000
    seed: int = 42
    rent_growth_std: float = 0.01
    vacancy_std: float = 0.015
    exit_cap_rate_std: float = 0.005
    rate_std: float = 0.0075
    target_hurdle_irr: float = 0.12


def run_monte_carlo(
    base_inputs: UnderwritingInputs,
    config: MonteCarloConfig | None = None,
    engine: UnderwritingEngine | None = None,
) -> dict[str, Any]:
    """Simulate distributions for IRR and NPV under uncertain assumptions."""

    cfg = config or MonteCarloConfig(target_hurdle_irr=base_inputs.target_hurdle_irr)
    model = engine or UnderwritingEngine()
    rng = np.random.default_rng(cfg.seed)

    records: list[dict] = []

    for i in range(cfg.n_simulations):
        sim_inputs = copy.deepcopy(base_inputs)

        sim_inputs.rental.annual_rent_growth = float(
            np.clip(
                rng.normal(base_inputs.rental.annual_rent_growth, cfg.rent_growth_std),
                -0.20,
                0.20,
            )
        )
        sim_inputs.rental.vacancy_rate = float(
            np.clip(
                rng.normal(base_inputs.rental.vacancy_rate, cfg.vacancy_std),
                0.01,
                0.35,
            )
        )
        sim_inputs.exit.exit_cap_rate = float(
            np.clip(
                rng.normal(base_inputs.exit.exit_cap_rate, cfg.exit_cap_rate_std),
                0.03,
                0.20,
            )
        )
        sim_inputs.financing.annual_interest_rate = float(
            np.clip(
                rng.normal(base_inputs.financing.annual_interest_rate, cfg.rate_std),
                0.00,
                0.20,
            )
        )

        result = model.run(sim_inputs)
        records.append(
            {
                "simulation": i + 1,
                "irr": result.metrics.get("irr"),
                "npv": result.metrics.get("npv"),
                "rent_growth": sim_inputs.rental.annual_rent_growth,
                "vacancy": sim_inputs.rental.vacancy_rate,
                "exit_cap_rate": sim_inputs.exit.exit_cap_rate,
                "interest_rate": sim_inputs.financing.annual_interest_rate,
            }
        )

    sims = pd.DataFrame(records)
    irr_series = sims["irr"].dropna()
    npv_series = sims["npv"].dropna()

    summary = {
        "irr_p5": float(np.percentile(irr_series, 5)) if not irr_series.empty else None,
        "irr_p50": float(np.percentile(irr_series, 50)) if not irr_series.empty else None,
        "irr_p95": float(np.percentile(irr_series, 95)) if not irr_series.empty else None,
        "npv_p5": float(np.percentile(npv_series, 5)) if not npv_series.empty else None,
        "npv_p50": float(np.percentile(npv_series, 50)) if not npv_series.empty else None,
        "npv_p95": float(np.percentile(npv_series, 95)) if not npv_series.empty else None,
        "prob_irr_below_zero": float((irr_series < 0).mean()) if not irr_series.empty else None,
        "prob_irr_below_hurdle": float((irr_series < cfg.target_hurdle_irr).mean()) if not irr_series.empty else None,
    }

    return {
        "summary": summary,
        "simulations": sims,
    }
