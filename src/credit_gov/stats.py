"""Statistical significance utilities for fair-lending screening.

This module upgrades the fair-lending screens from raw descriptive gaps to
inferential results: every reported disparity carries an effect size, a
p-value, the test used, and a sample-adequacy assessment.

Design notes and honest limitations:

- Pure standard-library implementation (``math`` only) so results are
  deterministic and the repository stays dependency-free.
- The two-proportion z-test uses the pooled-variance form. When expected cell
  counts are too small for the normal approximation, the module automatically
  falls back to Fisher's exact test (two-sided, computed in log space via
  ``math.lgamma`` for numerical stability).
- A significance result on synthetic or observational data is a screening
  signal for governance review. It is not a causal estimate, a regression
  controlling for legitimate credit factors, or a legal conclusion.
"""

from __future__ import annotations

import math
from typing import Any

DEFAULT_ALPHA = 0.05
MIN_EXPECTED_CELL_COUNT = 5.0


def normal_sf(z: float) -> float:
    """Survival function of the standard normal distribution, P(Z > z)."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def two_proportion_z_test(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
) -> dict[str, Any]:
    """Two-sided pooled two-proportion z-test.

    Returns the z statistic and two-sided p-value for the difference between
    the two group proportions. Degenerate inputs (empty groups or zero pooled
    variance) return a p-value of 1.0 with a note.
    """
    if total_a <= 0 or total_b <= 0:
        return {"z_statistic": 0.0, "p_value": 1.0, "note": "empty_group"}
    rate_a = successes_a / total_a
    rate_b = successes_b / total_b
    pooled = (successes_a + successes_b) / (total_a + total_b)
    variance = pooled * (1.0 - pooled) * (1.0 / total_a + 1.0 / total_b)
    if variance <= 0.0:
        return {"z_statistic": 0.0, "p_value": 1.0, "note": "zero_pooled_variance"}
    z = (rate_a - rate_b) / math.sqrt(variance)
    p_value = 2.0 * normal_sf(abs(z))
    return {"z_statistic": round(z, 4), "p_value": round(min(p_value, 1.0), 6)}


def _log_hypergeometric_pmf(k: int, row1: int, row2: int, col1: int, total: int) -> float:
    """Log of the hypergeometric probability of ``k`` for a fixed-margin 2x2 table."""

    def log_comb(n: int, r: int) -> float:
        return math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)

    return (
        log_comb(row1, k)
        + log_comb(row2, col1 - k)
        - log_comb(total, col1)
    )


def fisher_exact_two_sided(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
) -> dict[str, Any]:
    """Two-sided Fisher's exact test on a 2x2 table.

    The two-sided p-value sums the probabilities of all tables (with the same
    margins) whose probability does not exceed that of the observed table,
    which matches the conventional definition used by R and SciPy.
    """
    if total_a <= 0 or total_b <= 0:
        return {"p_value": 1.0, "note": "empty_group"}
    failures_a = total_a - successes_a
    failures_b = total_b - successes_b
    total = total_a + total_b
    col1 = successes_a + successes_b
    if col1 == 0 or (failures_a + failures_b) == 0:
        return {"p_value": 1.0, "note": "degenerate_margin"}

    k_min = max(0, col1 - total_b)
    k_max = min(col1, total_a)
    observed_log_p = _log_hypergeometric_pmf(successes_a, total_a, total_b, col1, total)
    tolerance = 1e-9
    p_value = 0.0
    for k in range(k_min, k_max + 1):
        log_p = _log_hypergeometric_pmf(k, total_a, total_b, col1, total)
        if log_p <= observed_log_p + tolerance:
            p_value += math.exp(log_p)
    return {"p_value": round(min(p_value, 1.0), 6)}


def sample_adequate_for_z_test(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
) -> bool:
    """Check the expected-count rule for the normal approximation.

    Requires every expected success and failure cell (under the pooled rate)
    to be at least ``MIN_EXPECTED_CELL_COUNT``.
    """
    if total_a <= 0 or total_b <= 0:
        return False
    pooled = (successes_a + successes_b) / (total_a + total_b)
    for total in (total_a, total_b):
        if total * pooled < MIN_EXPECTED_CELL_COUNT:
            return False
        if total * (1.0 - pooled) < MIN_EXPECTED_CELL_COUNT:
            return False
    return True


def compare_group_proportions(
    label_a: str,
    successes_a: int,
    total_a: int,
    label_b: str,
    successes_b: int,
    total_b: int,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:
    """Full significance comparison between two group proportions.

    Chooses the two-proportion z-test when the sample supports the normal
    approximation, otherwise Fisher's exact test. Reports effect sizes
    (difference and ratio), the p-value, the test used, and explicit caveats.
    """
    rate_a = successes_a / total_a if total_a else 0.0
    rate_b = successes_b / total_b if total_b else 0.0
    adequate = sample_adequate_for_z_test(successes_a, total_a, successes_b, total_b)
    if adequate:
        test_name = "two_proportion_z_test_pooled"
        test_result = two_proportion_z_test(successes_a, total_a, successes_b, total_b)
    else:
        test_name = "fisher_exact_two_sided"
        test_result = fisher_exact_two_sided(successes_a, total_a, successes_b, total_b)

    p_value = test_result["p_value"]
    caveats = [
        "Screening signal only; not a causal estimate or a legal conclusion.",
        "No adjustment for legitimate credit factors (no regression controls).",
    ]
    if not adequate:
        caveats.append(
            "Sample too small for the normal approximation; Fisher's exact test used."
        )

    result: dict[str, Any] = {
        "group_a": {"label": label_a, "successes": successes_a, "total": total_a, "rate": round(rate_a, 4)},
        "group_b": {"label": label_b, "successes": successes_b, "total": total_b, "rate": round(rate_b, 4)},
        "effect_size": {
            "rate_difference": round(rate_a - rate_b, 4),
            "rate_ratio": round(rate_a / rate_b, 4) if rate_b > 0 else None,
        },
        "test": test_name,
        "p_value": p_value,
        "alpha": alpha,
        "statistically_significant": bool(p_value < alpha),
        "sample_adequate_for_normal_approximation": adequate,
        "caveats": caveats,
    }
    if "z_statistic" in test_result:
        result["z_statistic"] = test_result["z_statistic"]
    if "note" in test_result:
        result["note"] = test_result["note"]
    return result
