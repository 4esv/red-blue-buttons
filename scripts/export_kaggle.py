"""Export the Kaggle dataset bundle from countries.json + the model.

Writes kaggle/dataset/: countries.csv (inputs), results.csv (per-entry
outputs), world_summary.csv (the headline row), sensitivity.csv (the sweeps
the CLI prints), plus a copy of countries.json for the full provenance block.

    python -m scripts.export_kaggle
"""

import csv
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.model import (
    ALTRUISM,
    CONCENTRATION,
    LAMBDA,
    critical_altruism,
    critical_trust,
    load_entries,
    world,
    world_critical_altruism,
)

OUT = REPO / "kaggle" / "dataset"


def write_csv(path, rows, fields):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"saved {path}  ({len(rows)} rows)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((REPO / "data" / "countries.json").read_text())
    entries, _ = load_entries()

    rows = [{"code": e.get("code", ""), "iso2": e.get("iso2", ""), "name": e["name"],
             "trust": e["trust"], "altruism": e["altruism"], "population": e["population"]}
            for e in data["countries"] + [data["rest_of_world"]]]
    write_csv(OUT / "countries.csv", rows,
              ["code", "iso2", "name", "trust", "altruism", "population"])

    base = world(entries)
    rows = [{"code": r["code"] or "", "name": r["name"], "trust": r["trust"],
             "population": r["pop"], "blue_fraction": r["blue_fraction"],
             "deaths_per_100k": round(r["blue_fraction"] * 100_000, 1),
             "deaths_in_global_game": r["deaths_in_global_game"],
             "local_win": r["local_win"],
             "critical_altruism_self_save": critical_altruism(r["trust"])}
            for r in base["per_country"]]
    write_csv(OUT / "results.csv", rows,
              ["code", "name", "trust", "population", "blue_fraction", "deaths_per_100k",
               "deaths_in_global_game", "local_win", "critical_altruism_self_save"])

    toll = base["world_death_rate"] * base["total_pop"]
    china = next(r["deaths_in_global_game"] for r in base["per_country"] if r["code"] == "CHN")
    write_csv(OUT / "world_summary.csv", [{
        "altruism": ALTRUISM, "concentration": CONCENTRATION, "lambda": LAMBDA, "misclick": 0.0,
        "total_population": int(base["total_pop"]),
        "global_blue_fraction": base["global_blue_fraction"],
        "blue_wins": base["blue_wins"],
        "world_death_rate": base["world_death_rate"],
        "world_deaths": round(toll),
        "china_share_of_toll": china / toll,
        "critical_trust_uniform_world": critical_trust(),
        "world_critical_altruism": world_critical_altruism(entries),
    }], ["altruism", "concentration", "lambda", "misclick", "total_population",
         "global_blue_fraction", "blue_wins", "world_death_rate", "world_deaths",
         "china_share_of_toll", "critical_trust_uniform_world", "world_critical_altruism"])

    sweeps = (
        [("china_trust", v, world(entries, china_trust=v)) for v in (0.64, 0.45, 0.30, 0.20)]
        + [("altruism", v, world(entries, altruism_mean=v))
           for v in (0.10, 0.20, 0.28, 0.40, 0.50, 0.70, 1.00)]
        + [("lambda", v, world(entries, lam=v)) for v in (1.0, 1.5, 2.25)]
        + [("concentration", float(v), world(entries, conc=float(v))) for v in (4, 5, 6, 7, 8, 10)]
        + [("trust_delta", v, world(entries, trust_delta=v)) for v in (-0.03, 0.0, 0.03)]
    )
    rows = [{"parameter": p, "value": v, "world_death_rate": w["world_death_rate"],
             "global_blue_fraction": w["global_blue_fraction"], "blue_wins": w["blue_wins"]}
            for p, v, w in sweeps]
    write_csv(OUT / "sensitivity.csv", rows,
              ["parameter", "value", "world_death_rate", "global_blue_fraction", "blue_wins"])

    shutil.copy(REPO / "data" / "countries.json", OUT / "countries.json")
    print(f"saved {OUT / 'countries.json'}")


if __name__ == "__main__":
    main()
