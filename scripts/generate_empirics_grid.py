"""High-resolution phase sweep for the empirics-section chart.

Outputs `data/empirics_grid.json`. Re-run after touching the model:

    python -m scripts.generate_empirics_grid

For every cell on a 41x41 (a, p) grid we draw populations whose altruism
and trust are Beta-distributed with the cell's mean and a fixed
concentration of 7, then average outcomes over n_runs simulations.

Output shape (consumed by charts/empirics.html):

    {
      "grid_size": 41,
      "altruism_axis":     [..],        # length 41
      "trust_axis":        [..],        # length 41
      "p_blue_wins_grid":  [[..], ..],  # 41x41
      "survival_grid":     [[..], ..],  # 41x41
      "cells":             [{a, p, p_blue_wins, survival, blue_fraction}, ..],
      "indifference_curve": [{a, p}, ..],   # p = 1 / (1 + a)
      "params_held_fixed":  {..}
    }
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import PopulationParams, simulate_many


CONCENTRATION = 7.0


def beta_params_from_mean(mean: float, concentration: float = CONCENTRATION):
    mean = max(0.02, min(0.98, mean))
    return mean * concentration, (1 - mean) * concentration


def run_sweep(grid_size: int, n_runs: int, n_agents: int) -> dict:
    altruism_axis = np.linspace(0.05, 0.95, grid_size)
    trust_axis = np.linspace(0.05, 0.95, grid_size)

    cells = []
    p_blue_wins = np.zeros((grid_size, grid_size))
    survival = np.zeros((grid_size, grid_size))

    for i, am in enumerate(altruism_axis):
        for j, tm in enumerate(trust_axis):
            aa, ab = beta_params_from_mean(am)
            ta, tb = beta_params_from_mean(tm)
            params = PopulationParams(
                n_agents=n_agents,
                altruism_alpha=aa, altruism_beta=ab,
                trust_alpha=ta, trust_beta=tb,
                error_rate=0.02,
            )
            out = simulate_many(params, n_runs=n_runs, seed=42 + i * grid_size + j)
            p_blue_wins[i, j] = out["p_blue_wins"]
            survival[i, j] = out["mean_survival_rate"]
            cells.append({
                "a": round(float(am), 3),
                "p": round(float(tm), 3),
                "p_blue_wins": round(float(out["p_blue_wins"]), 3),
                "survival": round(float(out["mean_survival_rate"]), 3),
                "blue_fraction": round(float(out["mean_blue_fraction"]), 3),
            })
        if (i + 1) % 5 == 0:
            print(f"  row {i+1}/{grid_size}")

    a_curve = np.linspace(0.005, 1.0, 200)
    indifference = [
        {"a": round(float(a), 4), "p": round(float(1.0 / (1.0 + a)), 4)}
        for a in a_curve
    ]

    return {
        "grid_size": grid_size,
        "altruism_axis": [round(x, 3) for x in altruism_axis.tolist()],
        "trust_axis": [round(x, 3) for x in trust_axis.tolist()],
        "p_blue_wins_grid": [[round(v, 3) for v in row] for row in p_blue_wins.tolist()],
        "survival_grid": [[round(v, 3) for v in row] for row in survival.tolist()],
        "cells": cells,
        "indifference_curve": indifference,
        "params_held_fixed": {
            "n_agents": n_agents,
            "n_runs_per_cell": n_runs,
            "error_rate": 0.02,
            "loss_aversion": 1.0,
            "beta_concentration": CONCENTRATION,
        },
    }


if __name__ == "__main__":
    print("High-res sweep at 41x41...")
    data = run_sweep(grid_size=41, n_runs=80, n_agents=3000)
    out_path = Path(__file__).resolve().parent.parent / "data" / "empirics_grid.json"
    out_path.write_text(json.dumps(data))
    print(f"Saved {out_path} — {len(data['cells'])} cells")
