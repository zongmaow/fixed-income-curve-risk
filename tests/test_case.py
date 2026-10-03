"""Regression tests for the curve-risk case.

Run from the repository root:

    python3 -m unittest tests/test_case.py
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bonds import INSTRUMENT_IDS, build_instruments  # noqa: E402
from src.curve import load_curve_parameters  # noqa: E402
from src.portfolio import DV01_TARGET, NAV, portfolio_dv01, normalize_weights  # noqa: E402

DESIGN_PRICES = {
    "S06M": 99.582157,
    "S02Y": 99.194643,
    "S03Y": 99.065240,
    "S05Y": 99.087613,
    "S07Y": 99.566682,
    "S10Y": 99.582423,
    "S20Y": 98.181553,
    "S30Y": 97.092721,
}
JUL_OCT_BP = (0.90, 26.18, 77.43, 108.10, 119.44, 93.82)
MARCH_BP = (-37.57, -95.13, -62.51, -41.39, -21.86, -13.14)


class CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads((ROOT / "outputs" / "case_results.json").read_text())
        curves = load_curve_parameters(ROOT / "data" / "curve_parameters_2022_2023.csv")
        cls.curves = curves
        cls.instruments = build_instruments(curves["2023-07-31"])

    def test_frozen_sample(self):
        self.assertEqual(len(self.curves), 499)
        manifest = json.loads((ROOT / "data" / "source_manifest.json").read_text())
        self.assertEqual(manifest["filter"]["dated_rows"], 520)
        self.assertEqual(manifest["filter"]["dropped_missing_beta_or_tau"], 21)
        self.assertEqual(len(manifest["dropped_dates"]), 21)

    def test_prices_within_1e_6(self):
        for name, expected in DESIGN_PRICES.items():
            dirty = self.instruments[name]["dirty"]
            self.assertLess(abs(dirty - expected), 1e-6, msg=f"{name} {dirty}")

    def test_clean_equals_dirty(self):
        for name in INSTRUMENT_IDS:
            inst = self.instruments[name]
            self.assertEqual(inst["accrued"], 0.0)
            self.assertEqual(inst["clean"], inst["dirty"])

    def test_nav_and_dv01(self):
        for book, payload in self.case["books"].items():
            weights = payload["weights"]
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=10, msg=book)
            self.assertTrue(all(weight >= -1e-12 for weight in weights.values()), book)
            normalized = normalize_weights(weights, INSTRUMENT_IDS)
            dv01 = portfolio_dv01(normalized, self.instruments)
            self.assertAlmostEqual(dv01, DV01_TARGET, delta=1e-6, msg=book)
            self.assertAlmostEqual(sum(payload["market_value"].values()), NAV, delta=1e-4, msg=book)

    def test_control_weights_are_present(self):
        weights = self.case["books"]["control_2y20y"]["weights"]
        self.assertGreater(weights["S02Y"], 0.5)
        self.assertGreater(weights["S20Y"], 0.1)
        self.assertEqual(weights["S30Y"], 0.0)
        self.assertEqual(weights["S06M"], 0.0)

    def test_node_shocks_round_to_published_checks(self):
        checks = self.case["node_shock_checks"]
        self.assertEqual(checks["hist_2023_07_31_to_2023_10_19"]["rounded_bp"], list(JUL_OCT_BP))
        self.assertEqual(checks["hist_2023_03_08_to_2023_03_13"]["rounded_bp"], list(MARCH_BP))

    def test_ten_percent_book_does_not_repair(self):
        book = self.case["books"]["candidate_10pct_s05y"]
        self.assertAlmostEqual(book["turnover_vs_current"], 0.10, places=8)
        self.assertAlmostEqual(book["weights"]["S05Y"], 0.10, places=10)
        failed = [name for name, row in book["scenarios"].items() if not row["within_budget"]]
        self.assertTrue(failed)

    def test_expanded_book_clears_with_cushion(self):
        book = self.case["books"]["candidate_expanded_s05y"]
        self.assertTrue(all(row["within_budget"] for row in book["scenarios"].values()))
        expanded = self.case["expanded_s05y"]
        self.assertGreater(expanded["cushion_dollars"], 0.0)
        self.assertLess(expanded["turnover_just"], book["turnover_vs_current"])
        # One point of NAV turnover was added on top of the just-clearing trade.
        self.assertAlmostEqual(book["turnover_vs_current"] - expanded["turnover_just"], 0.01, places=8)

    def test_s05y_is_not_beaten_by_another_feasible_tenor(self):
        decision = self.case["case_decision"]
        self.assertEqual(decision["directions_that_clear_at_lower_turnover"], [])
        self.assertEqual(decision["lowest_feasible_direction"]["buy"], "S05Y")


if __name__ == "__main__":
    unittest.main()
