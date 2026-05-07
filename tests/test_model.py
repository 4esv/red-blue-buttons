"""Sanity checks for the core simulation.

Run with: python -m pytest tests/ -q
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import PopulationParams, decision_threshold, simulate_many


def test_threshold_collapses_to_eu_when_lambda_is_one():
    # At lambda = 1, threshold = 1/(1+a)
    for a in [0.0, 0.1, 0.28, 0.5, 0.9]:
        assert math.isclose(
            float(decision_threshold(a, 1.0)),
            1.0 / (1.0 + a),
            rel_tol=1e-12,
        )


def test_threshold_loss_averse_matches_article():
    # Article quotes 0.78 at lambda=1 and 0.89 at lambda=2.25 for a=0.28.
    assert round(float(decision_threshold(0.28, 1.0)), 2) == 0.78
    assert round(float(decision_threshold(0.28, 2.25)), 2) == 0.89


def test_universal_blue_at_low_error_wins():
    # Everyone has high a and high p -> blue dominates, all survive.
    params = PopulationParams(
        n_agents=2000,
        altruism_alpha=8.0, altruism_beta=2.0,    # mean ~0.8
        trust_alpha=8.0, trust_beta=2.0,          # mean ~0.8
        error_rate=0.02,
    )
    out = simulate_many(params, n_runs=20, seed=0)
    assert out["p_blue_wins"] == 1.0
    assert out["mean_survival_rate"] > 0.99


def test_universal_red_loses_only_misclickers():
    # Everyone has low a and low p -> nobody intends blue. Only the
    # 2% misclickers press blue and die. Expected survival ~0.98.
    params = PopulationParams(
        n_agents=2000,
        altruism_alpha=2.0, altruism_beta=8.0,
        trust_alpha=2.0, trust_beta=8.0,
        error_rate=0.02,
    )
    out = simulate_many(params, n_runs=20, seed=0)
    assert out["p_blue_wins"] == 0.0
    assert 0.96 < out["mean_survival_rate"] < 0.99


def test_trap_zone_high_trust_low_altruism():
    # High p, low a: enough people press blue to die for the cause but
    # not enough to win. Survival should drop materially below 1.0.
    params = PopulationParams(
        n_agents=2000,
        altruism_alpha=2.0, altruism_beta=8.0,    # mean ~0.2
        trust_alpha=7.0, trust_beta=3.0,          # mean ~0.7
        error_rate=0.02,
    )
    out = simulate_many(params, n_runs=20, seed=0)
    assert out["p_blue_wins"] == 0.0
    assert 0.7 < out["mean_survival_rate"] < 0.85


def test_simulate_outputs_are_well_formed():
    params = PopulationParams(
        n_agents=500,
        altruism_alpha=2.0, altruism_beta=2.0,
        trust_alpha=2.0, trust_beta=2.0,
    )
    out = simulate_many(params, n_runs=10, seed=42)
    assert 0.0 <= out["p_blue_wins"] <= 1.0
    assert 0.0 <= out["mean_blue_fraction"] <= 1.0
    assert 0.0 <= out["mean_survival_rate"] <= 1.0


def test_threshold_is_vectorised():
    a = np.array([0.0, 0.5, 1.0])
    t = decision_threshold(a, 1.0)
    assert np.allclose(t, [1.0, 1.0 / 1.5, 0.5])
