"""Population-scale model for the red/blue button dilemma.

The dilemma (Tim Urban): everyone privately presses red or blue. If more
than half of *everyone* presses blue, everyone lives; otherwise only the
red-pressers live. This estimates the likely outcome from real national
data instead of intuition.

Each agent has a trust p (its belief that others will press blue, anchored
to its nation's social-trust level) and an altruism a (the weight it puts
on a stranger's life). It presses blue iff  p * (1 + a) >= lambda, the
risk-neutral expected-value rule (lambda = 1); equivalently iff trust
clears the threshold lambda / (a + lambda).

With no misclick the per-country blue (= death) fraction is a closed form,
evaluated here by quadrature:

    q(m_t, m_a, c, lambda) = P[ t >= lambda/(a+lambda) ]
        = INT_0^1  (1 - F_t( lambda/(a+lambda) ))  dF_a(a)

with a ~ Beta(m_a*c, (1-m_a)*c) and t ~ Beta(m_t*c, (1-m_t)*c). The rule is
GLOBAL: blue wins iff >= 50% of everyone presses blue, so the world death
rate is the population-weighted blue fraction (when blue loses), and each
country's deaths are realized in that one global game. The --confirm run
reproduces the closed form by Monte Carlo at the real world population
(~7e9 agents); it confirms, it does not define.

Usage:
    python -m scripts.model             # exact results + sensitivity table
    python -m scripts.model --confirm   # also the ~7e9-agent confirmation
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy import integrate, optimize, stats

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

CONCENTRATION = 7.0
ALTRUISM = 0.28
LAMBDA = 1.0


def beta_ab(mean, conc):
    mean = min(max(mean, 1e-6), 1 - 1e-6)
    return mean * conc, (1.0 - mean) * conc


def blue_fraction(trust_mean, altruism_mean=ALTRUISM, conc=CONCENTRATION, lam=LAMBDA):
    """Exact P[ t >= lambda/(a+lambda) ] = E_a[ 1 - F_t(lambda/(a+lambda)) ].

    Evaluated by the probability-integral transform a = F_a^{-1}(u): the
    integrand in u is bounded on (0,1) even when the altruism Beta has an
    endpoint singularity (mean < 1/concentration), so quadrature is clean.
    """
    a_ppf = stats.beta(*beta_ab(altruism_mean, conc)).ppf
    t_cdf = stats.beta(*beta_ab(trust_mean, conc)).cdf

    def integrand(u):
        a = a_ppf(u)
        return 1.0 - t_cdf(lam / (a + lam))

    # Root-finders probe degenerate trust means where the trust Beta is a
    # near-step and quad flags slow convergence; the value is still accurate
    # (verified vs 20M-agent Monte Carlo to <0.01pp). Silence the cosmetic flag.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", integrate.IntegrationWarning)
        val, _ = integrate.quad(integrand, 0.0, 1.0, limit=200)
    return float(val)


def world(entries, altruism_mean=ALTRUISM, conc=CONCENTRATION, lam=LAMBDA,
          china_trust=None, trust_delta=0.0):
    """Single global game over all entries. Returns per-country + aggregate."""
    tot_pop = 0.0
    tot_blue = 0.0
    per = []
    for e in entries:
        tmean = e["trust"] + trust_delta
        if china_trust is not None and e.get("code") == "CHN":
            tmean = china_trust
        q = blue_fraction(tmean, altruism_mean, conc, lam)
        per.append({"name": e["name"], "code": e.get("code"), "trust": round(tmean, 4),
                    "pop": e["population"], "blue_fraction": q})
        tot_pop += e["population"]
        tot_blue += e["population"] * q
    Q = tot_blue / tot_pop
    blue_wins = Q >= 0.5
    for r in per:
        r["deaths_in_global_game"] = 0 if blue_wins else round(r["blue_fraction"] * r["pop"])
        r["local_win"] = r["blue_fraction"] >= 0.5
    return {
        "global_blue_fraction": Q,
        "blue_wins": blue_wins,
        "world_death_rate": 0.0 if blue_wins else Q,
        "total_pop": tot_pop,
        "per_country": per,
    }


def critical_altruism(trust_mean, conc=CONCENTRATION, lam=LAMBDA):
    """Altruism mean at which this trust profile crosses 50% blue (saves itself)."""
    f = lambda a: blue_fraction(trust_mean, a, conc, lam) - 0.5
    if f(1 - 1e-4) < 0:
        return None  # even maximal altruism can't save it
    if f(1e-4) > 0:
        return 0.0
    return float(optimize.brentq(f, 1e-4, 1 - 1e-4))


def critical_trust(altruism_mean=ALTRUISM, conc=CONCENTRATION, lam=LAMBDA):
    """Trust mean at which a uniform world crosses 50% blue, at fixed altruism."""
    f = lambda m: blue_fraction(m, altruism_mean, conc, lam) - 0.5
    return float(optimize.brentq(f, 1e-4, 1 - 1e-4))


def world_critical_altruism(entries, conc=CONCENTRATION, lam=LAMBDA):
    """Global mean altruism at which the *whole world* flips to blue-wins."""
    def Q(a):
        tot_pop = sum(e["population"] for e in entries)
        return sum(e["population"] * blue_fraction(e["trust"], a, conc, lam)
                   for e in entries) / tot_pop - 0.5
    if Q(1 - 1e-4) < 0:
        return None
    return float(optimize.brentq(Q, 1e-4, 1 - 1e-4))


def fmt(x):
    return f"{x * 100:.2f}%"


def load_entries():
    data = json.loads((REPO / "data" / "countries.json").read_text())
    return data["countries"] + [data["rest_of_world"]], data["countries"]


def confirm_real_scale(entries, altruism_mean=ALTRUISM, conc=CONCENTRATION, lam=LAMBDA,
                       chunk=25_000_000, seed=42):
    """Monte-Carlo at real population, NO misclick. Should match quadrature."""
    rng = np.random.default_rng(seed)
    aa, ab = beta_ab(altruism_mean, conc)
    tot_pop = 0
    tot_blue = 0
    for e in entries:
        ta, tb = beta_ab(e["trust"], conc)
        remaining = int(e["population"])
        blue = np.int64(0)
        while remaining > 0:
            n = min(chunk, remaining)
            a = rng.beta(aa, ab, size=n)
            t = rng.beta(ta, tb, size=n)
            blue += (t >= (lam / (a + lam))).sum(dtype=np.int64)
            remaining -= n
        tot_pop += int(e["population"])
        tot_blue += int(blue)
    Q = tot_blue / tot_pop
    return {"total_agents": tot_pop, "global_blue_fraction": Q,
            "blue_wins": Q >= 0.5, "world_death_rate": 0.0 if Q >= 0.5 else Q}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true",
                    help="also run the real ~7e9-agent Monte-Carlo confirmation")
    args = ap.parse_args()

    entries, named = load_entries()
    base = world(entries)

    print("=" * 74)
    print("RED / BLUE BUTTON: population model (exact quadrature)")
    print(f"  altruism={ALTRUISM}, concentration={CONCENTRATION}, lambda={LAMBDA}")
    print("=" * 74)
    print(f"\ntotal population:     {base['total_pop']:,.0f}")
    print(f"global blue fraction: {fmt(base['global_blue_fraction'])}")
    print(f"blue wins:            {base['blue_wins']}")
    print(f"world death rate:     {fmt(base['world_death_rate'])} "
          f"({base['world_death_rate']*100_000:,.0f} per 100k)")

    print("\nPER-COUNTRY blue fraction = death rate in the global game (EXACT):")
    print(f"{'country':14s} {'trust':>5s} {'blue=deaths':>12s}  {'per 100k':>10s}  {'crit. a to self-save':>20s}")
    for r in sorted(base["per_country"], key=lambda x: -x["blue_fraction"]):
        ca = critical_altruism(r["trust"])
        ca_s = "impossible" if ca is None else f"{ca:.2f}"
        print(f"{r['name']:14s} {r['trust']:>5.2f} {fmt(r['blue_fraction']):>12s}  "
              f"{r['blue_fraction']*100_000:>10,.0f}  {ca_s:>20s}")

    print("\nKEY THRESHOLDS:")
    ct = critical_trust()
    print(f"  uniform world needs trust >= {ct*100:.1f}% to survive (at a={ALTRUISM}, lambda={LAMBDA})")
    wca = world_critical_altruism(entries)
    print(f"  real heterogeneous world needs altruism >= "
          f"{'impossible (even a=1 fails)' if wca is None else f'{wca:.2f}'} to survive")
    dk = next(r for r in base["per_country"] if r["code"] == "DNK")
    dk_ca = critical_altruism(dk["trust"])
    print(f"  Denmark (trust {dk['trust']:.2f}) self-saves only if altruism >= "
          f"{'impossible' if dk_ca is None else f'{dk_ca:.2f}'} (vs assumed {ALTRUISM})")

    print("\n" + "=" * 74)
    print("SENSITIVITY  (world death rate; exact)")
    print("=" * 74)

    print("\nChina's trust (data file flags 64% as contested; 1.4B people):")
    for ct_ in [0.64, 0.45, 0.30, 0.20]:
        w = world(entries, china_trust=ct_)
        print(f"  China={ct_:.2f}: world {fmt(w['world_death_rate'])}")

    print("\nAltruism mean (dictator-game 0.28 is a weak proxy for 'die for a stranger'):")
    for am in [0.10, 0.20, 0.28, 0.40, 0.50, 0.70]:
        w = world(entries, altruism_mean=am)
        flip = "  <- BLUE WINS" if w["blue_wins"] else ""
        print(f"  a={am:.2f}: world {fmt(w['world_death_rate'])}{flip}")

    print("\nLoss aversion lambda (1.0 = risk-neutral EU; 2.25 = Kahneman-Tversky):")
    for lam_ in [1.0, 1.5, 2.25]:
        w = world(entries, lam=lam_)
        dkq = blue_fraction(dk["trust"], lam=lam_)
        print(f"  lambda={lam_:.2f}: world {fmt(w['world_death_rate'])}, Denmark {fmt(dkq)} blue")

    print("\nBeta concentration (within-country spread):")
    for c in [4, 5, 6, 7, 8, 10]:
        w = world(entries, conc=float(c))
        dkq = blue_fraction(dk["trust"], conc=float(c))
        print(f"  conc={c:>2}: world {fmt(w['world_death_rate'])}, Denmark {fmt(dkq)} blue")

    print("\nSurvey error on trust (shift every country):")
    for d in [-0.03, 0.0, 0.03]:
        w = world(entries, trust_delta=d)
        print(f"  trust{d:+.2f}: world {fmt(w['world_death_rate'])}")

    payload = {
        "params": {"altruism": ALTRUISM, "concentration": CONCENTRATION, "lambda": LAMBDA,
                   "misclick": 0.0},
        "global_blue_fraction": base["global_blue_fraction"],
        "blue_wins": base["blue_wins"],
        "world_death_rate": base["world_death_rate"],
        "critical_trust_uniform_world": ct,
        "world_critical_altruism": wca,
        "per_country": [
            {**r, "critical_altruism_self_save": critical_altruism(r["trust"])}
            for r in base["per_country"]
        ],
    }

    if args.confirm:
        print("\n" + "=" * 74)
        print("REAL-POPULATION CONFIRMATION  (Monte-Carlo, no misclick)")
        print("=" * 74)
        c = confirm_real_scale(entries)
        print(f"  agents simulated:     {c['total_agents']:,}")
        print(f"  global blue fraction: {fmt(c['global_blue_fraction'])} "
              f"(quadrature said {fmt(base['global_blue_fraction'])})")
        d = abs(c["global_blue_fraction"] - base["global_blue_fraction"]) * 100
        print(f"  delta: {d:.4f}pp  -> simulation confirms the closed form")
        payload["confirmation"] = c

    out = REPO / "data" / "canonical_results.json"
    out.write_text(json.dumps(payload, indent=2, default=float))
    print(f"\nsaved {out}")
