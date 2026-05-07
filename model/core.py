"""Core simulation for the Red Button / Blue Button dilemma.

Setup:
    Each agent has an altruism weight a_i in [0, 1] and a trust belief
    p_i in [0, 1]. They press blue iff their expected utility prefers it.
    Pressing blue requires p * (1 + a) >= lambda, where lambda is the
    loss-aversion coefficient (lambda = 1 is risk-neutral / standard EU,
    lambda = 2.25 is Kahneman-Tversky 1992).

    Equivalently, the trust threshold is t*(a) = lambda / (a + lambda).

After choosing, each agent misclicks with probability `error_rate`.
If the blue fraction (after errors) is >= 0.5, blue wins and everyone
survives. Otherwise blue loses and only red voters survive.

The model is intentionally the no-communication baseline: every agent
decides privately, no contagion, no observation of others.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PopulationParams:
    n_agents: int
    altruism_alpha: float
    altruism_beta: float
    trust_alpha: float
    trust_beta: float
    error_rate: float = 0.02
    loss_aversion: float = 1.0


def decision_threshold(altruism, loss_aversion: float = 1.0):
    """Trust threshold above which an agent presses blue.

    threshold = lambda / (a + lambda)

    At lambda = 1 this collapses to the textbook 1 / (1 + a).
    """
    return loss_aversion / (np.asarray(altruism) + loss_aversion)


def _intent_blue(altruism, trust, loss_aversion: float):
    return trust >= decision_threshold(altruism, loss_aversion)


def simulate_once(params: PopulationParams, rng: np.random.Generator) -> dict:
    altruism = rng.beta(params.altruism_alpha, params.altruism_beta, size=params.n_agents)
    trust = rng.beta(params.trust_alpha, params.trust_beta, size=params.n_agents)

    intent = _intent_blue(altruism, trust, params.loss_aversion)
    flip = rng.random(params.n_agents) < params.error_rate
    actual_blue = np.where(flip, ~intent, intent)

    blue_count = int(actual_blue.sum())
    blue_fraction = blue_count / params.n_agents
    blue_wins = blue_fraction >= 0.5

    survivors = params.n_agents if blue_wins else (params.n_agents - blue_count)
    return {
        "blue_fraction": blue_fraction,
        "blue_wins": bool(blue_wins),
        "survival": survivors / params.n_agents,
    }


def simulate_many(params: PopulationParams, n_runs: int, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    blue_wins = 0
    blue_fraction_sum = 0.0
    survival_sum = 0.0
    for _ in range(n_runs):
        out = simulate_once(params, rng)
        blue_wins += out["blue_wins"]
        blue_fraction_sum += out["blue_fraction"]
        survival_sum += out["survival"]
    return {
        "p_blue_wins": blue_wins / n_runs,
        "mean_blue_fraction": blue_fraction_sum / n_runs,
        "mean_survival_rate": survival_sum / n_runs,
    }
