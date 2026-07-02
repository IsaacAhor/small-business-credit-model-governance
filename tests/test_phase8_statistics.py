from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.stats import (  # noqa: E402
    compare_group_proportions,
    fisher_exact_two_sided,
    sample_adequate_for_z_test,
    two_proportion_z_test,
)


class TwoProportionZTestTests(unittest.TestCase):
    def test_large_gap_is_significant(self) -> None:
        result = two_proportion_z_test(80, 100, 40, 100)
        self.assertLess(result["p_value"], 0.001)

    def test_identical_rates_are_not_significant(self) -> None:
        result = two_proportion_z_test(50, 100, 50, 100)
        self.assertEqual(result["p_value"], 1.0)

    def test_empty_group_is_degenerate(self) -> None:
        result = two_proportion_z_test(0, 0, 10, 100)
        self.assertEqual(result["p_value"], 1.0)
        self.assertEqual(result["note"], "empty_group")

    def test_known_value_matches_reference(self) -> None:
        # 60/100 vs 45/100: z = 2.1237..., two-sided p ~ 0.0337 (reference: scipy)
        result = two_proportion_z_test(60, 100, 45, 100)
        self.assertAlmostEqual(result["z_statistic"], 2.1237, places=3)
        self.assertAlmostEqual(result["p_value"], 0.0337, places=3)


class FisherExactTests(unittest.TestCase):
    def test_matches_reference_value(self) -> None:
        # Table [[1, 9], [11, 3]]: two-sided p ~ 0.002759 (reference: scipy/R)
        result = fisher_exact_two_sided(1, 10, 11, 14)
        self.assertAlmostEqual(result["p_value"], 0.002759, places=5)

    def test_balanced_table_is_not_significant(self) -> None:
        result = fisher_exact_two_sided(5, 10, 5, 10)
        self.assertGreater(result["p_value"], 0.99)

    def test_degenerate_margin(self) -> None:
        result = fisher_exact_two_sided(0, 10, 0, 10)
        self.assertEqual(result["p_value"], 1.0)


class SampleAdequacyTests(unittest.TestCase):
    def test_large_samples_are_adequate(self) -> None:
        self.assertTrue(sample_adequate_for_z_test(50, 100, 40, 100))

    def test_small_samples_are_not_adequate(self) -> None:
        self.assertFalse(sample_adequate_for_z_test(1, 5, 2, 6))


class CompareGroupProportionsTests(unittest.TestCase):
    def test_selects_z_test_for_adequate_samples(self) -> None:
        result = compare_group_proportions("west", 30, 100, "south", 60, 100)
        self.assertEqual(result["test"], "two_proportion_z_test_pooled")
        self.assertTrue(result["statistically_significant"])
        self.assertEqual(result["effect_size"]["rate_difference"], -0.3)
        self.assertTrue(result["sample_adequate_for_normal_approximation"])

    def test_falls_back_to_fisher_for_small_samples(self) -> None:
        result = compare_group_proportions("a", 1, 5, "b", 4, 6)
        self.assertEqual(result["test"], "fisher_exact_two_sided")
        self.assertFalse(result["sample_adequate_for_normal_approximation"])
        self.assertTrue(any("Fisher" in caveat for caveat in result["caveats"]))

    def test_screening_caveats_always_present(self) -> None:
        result = compare_group_proportions("a", 50, 100, "b", 55, 100)
        self.assertTrue(any("not a causal estimate" in caveat for caveat in result["caveats"]))
        self.assertTrue(any("regression controls" in caveat for caveat in result["caveats"]))


if __name__ == "__main__":
    unittest.main()
