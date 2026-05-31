"""Pin the essay's published numbers against the model.

Run: python -m unittest tests.test_model
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.model import (
    ALTRUISM,
    CONCENTRATION,
    LAMBDA,
    blue_fraction,
    critical_trust,
    load_entries,
    world,
)


class TestModel(unittest.TestCase):
    def test_params(self):
        self.assertEqual((ALTRUISM, LAMBDA, CONCENTRATION), (0.28, 1.0, 7.0))

    def test_blue_fraction_monotonic_in_trust(self):
        vals = [blue_fraction(t) for t in (0.05, 0.2, 0.4, 0.6, 0.8)]
        self.assertEqual(vals, sorted(vals))

    def test_denmark_rate(self):
        # most trusting nation measured loses ~42%
        self.assertAlmostEqual(blue_fraction(0.74), 0.4173, places=3)

    def test_us_rate(self):
        self.assertAlmostEqual(blue_fraction(0.37), 0.0188, places=3)

    def test_critical_trust(self):
        # a uniform world needs ~77.6% trust to cross the blue-wins majority
        self.assertAlmostEqual(critical_trust(), 0.7763, places=3)

    def test_world_loses(self):
        entries, _ = load_entries()
        w = world(entries)
        self.assertFalse(w["blue_wins"])
        self.assertAlmostEqual(w["world_death_rate"], 0.0514, places=3)

    def test_china_dominates_toll(self):
        entries, _ = load_entries()
        w = world(entries)
        total = w["world_death_rate"] * w["total_pop"]
        china = next(c["deaths_in_global_game"] for c in w["per_country"] if c["code"] == "CHN")
        self.assertGreater(china / total, 0.85)  # China is ~89% of the global toll

    def test_pure_altruist_still_needs_some_trust(self):
        # at altruism = 1 the threshold is trust >= 0.5, so a low-trust pure
        # altruist still presses red; "almost always", not "always"
        self.assertLess(blue_fraction(0.3, altruism_mean=1.0), 0.5)
        self.assertGreater(blue_fraction(0.8, altruism_mean=1.0), 0.5)


if __name__ == "__main__":
    unittest.main()
