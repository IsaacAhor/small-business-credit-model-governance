"""BISG protected-class proxy estimation for fair-lending screening.

Implements Bayesian Improved Surname Geocoding (BISG), the standard method
used in fair-lending analysis when protected-class labels are unavailable
(Elliott et al. 2009; CFPB proxy methodology 2014). For each applicant, the
method combines the race/ethnicity distribution of the applicant's surname
with the race/ethnicity composition of the applicant's geography to produce
posterior probabilities over race/ethnicity categories:

    P(race | surname, geography)
        proportional to  P(race | surname) * P(race | geography) / P(race)

where ``P(race)`` is the national marginal distribution. Group-level metrics
(approval rates by proxied race category) are then computed with
probability-weighted counts, and reference-group gaps are evaluated with a
posterior-predictive applicant bootstrap.

Design notes and honest limitations:

- BISG produces *probabilistic proxies*, not observed demographics. All
  outputs are labeled accordingly and proxy-weighted counts are reported so
  reviewers can see expected group mass and effective sample diagnostics.
- The repository ships small demonstration reference tables
  (``data/reference/bisg/``) whose surname rows are approximations of the
  public U.S. Census 2010 surname file and whose geography rows are synthetic.
  The loader accepts full Census-derived tables in the same format.
- Proxy-weighted comparisons here are unadjusted screening signals. They are
  not regression estimates controlling for legitimate credit factors and not
  legal conclusions.
- The posterior-predictive applicant bootstrap quantifies sampling uncertainty
  and BISG posterior membership uncertainty under the proxy model. It still does
  not identify true protected-class membership.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from credit_gov.stats import compare_group_proportions

RACE_CATEGORIES = ["white", "black", "hispanic", "api", "aian", "multiracial"]
DEFAULT_MIN_EFFECTIVE_COUNT = 10.0
DEFAULT_BOOTSTRAP_DRAWS = 2000
DEFAULT_BOOTSTRAP_SEED = 20260726
DEFAULT_BOOTSTRAP_CI_LEVEL = 0.95


def load_reference_table(path: Path) -> dict[str, dict[str, float]]:
    """Load a reference table mapping a key to race-probability rows."""
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    table: dict[str, dict[str, float]] = {}
    for key, row in payload.items():
        table[key.strip().upper()] = {category: float(row.get(category, 0.0)) for category in RACE_CATEGORIES}
    return table


def normalize_distribution(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0.0:
        return {}
    return {category: value / total for category, value in weights.items()}


def kish_effective_sample_size(weights: list[float]) -> float:
    """Kish effective sample size for concentration in posterior weights."""
    total = sum(weights)
    squared_total = sum(weight * weight for weight in weights)
    if total <= 0.0 or squared_total <= 0.0:
        return 0.0
    return (total * total) / squared_total


def percentile(values: list[float], quantile: float) -> float | None:
    """Linear-interpolated percentile for deterministic bootstrap summaries."""
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    position = (len(clean) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return clean[lower]
    lower_weight = upper - position
    upper_weight = position - lower
    return clean[lower] * lower_weight + clean[upper] * upper_weight


def confidence_interval(values: list[float], level: float) -> dict[str, Any]:
    lower_quantile = (1.0 - level) / 2.0
    upper_quantile = 1.0 - lower_quantile
    lower = percentile(values, lower_quantile)
    upper = percentile(values, upper_quantile)
    return {
        "level": round(level, 4),
        "lower": round(lower, 4) if lower is not None else None,
        "upper": round(upper, 4) if upper is not None else None,
    }


def bootstrap_tail_probability(values: list[float], null_value: float = 0.0) -> float:
    """Two-sided bootstrap tail probability around a null value.

    The add-one adjustment avoids reporting zero from finite Monte Carlo draws.
    This is a screening tail probability, not a parametric p-value.
    """
    clean = [value for value in values if math.isfinite(value)]
    if not clean:
        return 1.0
    lower_tail = (sum(value <= null_value for value in clean) + 1) / (len(clean) + 1)
    upper_tail = (sum(value >= null_value for value in clean) + 1) / (len(clean) + 1)
    return round(min(1.0, 2.0 * min(lower_tail, upper_tail)), 6)


def proxy_weighted_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    weighted: dict[str, dict[str, float]] = {
        category: {"total": 0.0, "approved": 0.0} for category in RACE_CATEGORIES
    }
    for record in records:
        for category in RACE_CATEGORIES:
            probability = float(record["posterior"].get(category, 0.0))
            weighted[category]["total"] += probability
            if record["approved"]:
                weighted[category]["approved"] += probability
    return weighted


def proxy_rates(weighted: dict[str, dict[str, float]]) -> dict[str, float | None]:
    rates: dict[str, float | None] = {}
    for category in RACE_CATEGORIES:
        total = weighted[category]["total"]
        rates[category] = weighted[category]["approved"] / total if total > 0.0 else None
    return rates


def draw_posterior_category(posterior: dict[str, float], rng: random.Random) -> str:
    threshold = rng.random()
    cumulative = 0.0
    fallback = RACE_CATEGORIES[-1]
    for category in RACE_CATEGORIES:
        probability = float(posterior.get(category, 0.0))
        if probability > 0.0:
            fallback = category
        cumulative += probability
        if threshold <= cumulative:
            return category
    return fallback


def posterior_draw_counts(
    records: list[dict[str, Any]],
    rng: random.Random,
) -> dict[str, dict[str, float]]:
    weighted: dict[str, dict[str, float]] = {
        category: {"total": 0.0, "approved": 0.0} for category in RACE_CATEGORIES
    }
    for record in records:
        category = draw_posterior_category(record["posterior"], rng)
        weighted[category]["total"] += 1.0
        if record["approved"]:
            weighted[category]["approved"] += 1.0
    return weighted


def bootstrap_proxy_distributions(
    records: list[dict[str, Any]],
    reference_group: str,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Applicant-level bootstrap distributions for BISG-weighted rates.

    Each draw resamples matched applicants with replacement, draws one latent
    group membership from each applicant's BISG posterior, and recomputes the
    approval-rate gap under that posterior measurement model.
    """
    group_rate_draws: dict[str, list[float]] = {category: [] for category in RACE_CATEGORIES}
    comparison_draws: dict[str, dict[str, list[float]]] = {
        category: {"rate_difference": [], "rate_ratio": []}
        for category in RACE_CATEGORIES
        if category != reference_group
    }
    if not records or draws <= 0:
        return {"group_rate_draws": group_rate_draws, "comparison_draws": comparison_draws}

    rng = random.Random(seed)
    record_count = len(records)
    for _ in range(draws):
        sample = [records[rng.randrange(record_count)] for _ in range(record_count)]
        weighted = posterior_draw_counts(sample, rng)
        rates = proxy_rates(weighted)
        reference_rate = rates.get(reference_group)
        for category, rate in rates.items():
            if rate is not None:
                group_rate_draws[category].append(rate)
        if reference_rate is None:
            continue
        for category in comparison_draws:
            rate = rates.get(category)
            if rate is None:
                continue
            comparison_draws[category]["rate_difference"].append(rate - reference_rate)
            if reference_rate > 0.0:
                comparison_draws[category]["rate_ratio"].append(rate / reference_rate)
    return {"group_rate_draws": group_rate_draws, "comparison_draws": comparison_draws}


def bisg_posterior(
    surname: str,
    geography_id: str,
    surname_table: dict[str, dict[str, float]],
    geography_table: dict[str, dict[str, float]],
    national_marginals: dict[str, float],
) -> dict[str, Any]:
    """Posterior race/ethnicity probabilities for one applicant.

    Falls back gracefully: with only one prior available it uses that prior
    alone; with neither available it returns no posterior and a reason.
    """
    surname_row = surname_table.get(surname.strip().upper())
    geography_row = geography_table.get(str(geography_id).strip().upper())

    if surname_row is None and geography_row is None:
        return {"posterior": None, "basis": "no_reference_match"}
    if surname_row is None:
        return {"posterior": normalize_distribution(dict(geography_row)), "basis": "geography_only"}
    if geography_row is None:
        return {"posterior": normalize_distribution(dict(surname_row)), "basis": "surname_only"}

    combined: dict[str, float] = {}
    for category in RACE_CATEGORIES:
        marginal = national_marginals.get(category, 0.0)
        if marginal <= 0.0:
            combined[category] = 0.0
            continue
        combined[category] = surname_row.get(category, 0.0) * geography_row.get(category, 0.0) / marginal
    posterior = normalize_distribution(combined)
    if not posterior:
        return {"posterior": None, "basis": "zero_joint_support"}
    return {"posterior": posterior, "basis": "surname_and_geography"}


def run_bisg_proxy_analysis(
    decisions: list[dict[str, Any]],
    demographic_inputs: list[dict[str, Any]],
    config: dict[str, Any],
    dataset_dir: Path,
) -> dict[str, Any]:
    """Proxy-weighted fair-lending screening over BISG posteriors.

    For each race/ethnicity category, accumulates probability-weighted totals
    and approvals across all matched decisions, reports proxy-weighted
    approval rates, and uses applicant-level bootstrap inference for
    reference-group comparisons. Rounded-count proportion tests are retained
    only as legacy diagnostics.
    """
    repo_root = dataset_dir.resolve().parents[2]
    surname_table = load_reference_table(repo_root / config["surname_reference_path"])
    geography_table = load_reference_table(repo_root / config["geography_reference_path"])
    with (repo_root / config["national_marginals_path"]).open(encoding="utf-8") as handle:
        national_marginals = {key: float(value) for key, value in json.load(handle).items()}

    reference_group = config.get("reference_group", "white")
    alpha = float(config.get("alpha", 0.05))
    min_effective_count = float(config.get("min_effective_count", DEFAULT_MIN_EFFECTIVE_COUNT))
    bootstrap_draws = int(config.get("bootstrap_draws", DEFAULT_BOOTSTRAP_DRAWS))
    bootstrap_seed = int(config.get("bootstrap_seed", DEFAULT_BOOTSTRAP_SEED))
    bootstrap_ci_level = float(config.get("bootstrap_ci_level", DEFAULT_BOOTSTRAP_CI_LEVEL))

    inputs_by_decision = {record["decision_id"]: record for record in demographic_inputs}

    matched_records: list[dict[str, Any]] = []
    matched = 0
    unmatched = 0
    basis_counts: dict[str, int] = {}
    for decision in decisions:
        demographic = inputs_by_decision.get(decision["decision_id"])
        if demographic is None:
            unmatched += 1
            continue
        estimate = bisg_posterior(
            demographic["surname"],
            demographic["geography_id"],
            surname_table,
            geography_table,
            national_marginals,
        )
        basis_counts[estimate["basis"]] = basis_counts.get(estimate["basis"], 0) + 1
        posterior = estimate["posterior"]
        if posterior is None:
            unmatched += 1
            continue
        matched += 1
        matched_records.append(
            {
                "decision_id": decision["decision_id"],
                "approved": decision["decision_outcome"] == "approved",
                "posterior": posterior,
            }
        )

    weighted = proxy_weighted_counts(matched_records)
    bootstrap = bootstrap_proxy_distributions(
        records=matched_records,
        reference_group=reference_group,
        draws=bootstrap_draws,
        seed=bootstrap_seed,
    )

    group_metrics: dict[str, dict[str, Any]] = {}
    for category in RACE_CATEGORIES:
        total = weighted[category]["total"]
        approved = weighted[category]["approved"]
        effective_sample_size = kish_effective_sample_size(
            [float(record["posterior"].get(category, 0.0)) for record in matched_records]
        )
        meets_expected_count = total >= min_effective_count
        meets_effective_sample = effective_sample_size >= min_effective_count
        group_metrics[category] = {
            "proxy_weighted_total": round(total, 2),
            "proxy_weighted_approved": round(approved, 2),
            "proxy_weighted_approval_rate": round(approved / total, 4) if total > 0 else None,
            "effective_sample_size": round(effective_sample_size, 2),
            "bootstrap_approval_rate_ci": confidence_interval(
                bootstrap["group_rate_draws"][category],
                bootstrap_ci_level,
            ),
            "adequate_effective_sample": meets_expected_count and meets_effective_sample,
            "sample_gate": {
                "min_effective_count": min_effective_count,
                "proxy_weighted_total_meets_minimum": meets_expected_count,
                "effective_sample_size_meets_minimum": meets_effective_sample,
            },
        }

    reference = group_metrics.get(reference_group, {})
    comparisons: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    if reference.get("proxy_weighted_approval_rate") is not None:
        for category in RACE_CATEGORIES:
            if category == reference_group:
                continue
            entry = group_metrics[category]
            if entry["proxy_weighted_approval_rate"] is None:
                continue
            if not entry["adequate_effective_sample"]:
                comparisons[category] = {
                    "skipped": True,
                    "reason": "effective_sample_below_minimum",
                    "proxy_weighted_total": entry["proxy_weighted_total"],
                    "effective_sample_size": entry["effective_sample_size"],
                    "sample_gate": entry["sample_gate"],
                    "min_effective_count": min_effective_count,
                }
                continue
            legacy_comparison = compare_group_proportions(
                label_a=category,
                successes_a=int(round(weighted[category]["approved"])),
                total_a=int(round(weighted[category]["total"])),
                label_b=reference_group,
                successes_b=int(round(weighted[reference_group]["approved"])),
                total_b=int(round(weighted[reference_group]["total"])),
                alpha=alpha,
            )
            legacy_comparison["caveats"].append(
                "Legacy diagnostic only; rounded proxy-weighted counts are not treated as observed group memberships."
            )
            rate_a = entry["proxy_weighted_approval_rate"]
            rate_b = reference["proxy_weighted_approval_rate"]
            rate_difference = (
                round(float(rate_a) - float(rate_b), 4)
                if rate_a is not None and rate_b is not None
                else None
            )
            rate_ratio = (
                round(float(rate_a) / float(rate_b), 4)
                if rate_a is not None and rate_b not in (None, 0.0)
                else None
            )
            comparison_draws = bootstrap["comparison_draws"][category]
            rate_difference_ci = confidence_interval(
                comparison_draws["rate_difference"],
                bootstrap_ci_level,
            )
            rate_ratio_ci = confidence_interval(comparison_draws["rate_ratio"], bootstrap_ci_level)
            tail_probability = bootstrap_tail_probability(comparison_draws["rate_difference"])
            ci_lower = rate_difference_ci["lower"]
            ci_upper = rate_difference_ci["upper"]
            ci_excludes_null = (
                ci_lower is not None
                and ci_upper is not None
                and not (ci_lower <= 0.0 <= ci_upper)
            )
            comparison = {
                "group_a": {
                    "label": category,
                    "proxy_weighted_approved": entry["proxy_weighted_approved"],
                    "proxy_weighted_total": entry["proxy_weighted_total"],
                    "effective_sample_size": entry["effective_sample_size"],
                    "rate": rate_a,
                },
                "group_b": {
                    "label": reference_group,
                    "proxy_weighted_approved": reference["proxy_weighted_approved"],
                    "proxy_weighted_total": reference["proxy_weighted_total"],
                    "effective_sample_size": reference["effective_sample_size"],
                    "rate": rate_b,
                },
                "effect_size": {
                    "rate_difference": rate_difference,
                    "rate_ratio": rate_ratio,
                },
                "test": "applicant_level_posterior_predictive_bootstrap",
                "p_value": tail_probability,
                "alpha": alpha,
                "statistically_significant": ci_excludes_null,
                "sample_adequate_for_bootstrap": True,
                "bootstrap": {
                    "draws": bootstrap_draws,
                    "seed": bootstrap_seed,
                    "ci_level": round(bootstrap_ci_level, 4),
                    "rate_difference_ci": rate_difference_ci,
                    "rate_ratio_ci": rate_ratio_ci,
                    "tail_probability": tail_probability,
                    "tail_probability_note": "Two-sided bootstrap tail probability for the rate difference crossing zero; screening only.",
                },
                "legacy_rounded_count_comparison": legacy_comparison,
                "caveats": [
                    "Screening signal only; not a causal estimate or a legal conclusion.",
                    "No adjustment for legitimate credit factors (no regression controls).",
                    "Bootstrap resamples applicants and samples latent group membership from BISG posteriors.",
                    "Bootstrap uncertainty does not correct BISG proxy measurement bias or identify true protected-class membership.",
                    "Legacy rounded-count tests are retained only as diagnostics and are not used for BISG findings.",
                ],
            }
            comparisons[category] = comparison
            if (
                comparison["statistically_significant"]
                and comparison["effect_size"]["rate_difference"] is not None
                and comparison["effect_size"]["rate_difference"] < 0
            ):
                findings.append(
                    {
                        "finding_id": f"bisg-{len(findings) + 1:04d}",
                        "proxy_group": category,
                        "reference_group": reference_group,
                        "proxy_weighted_approval_rate": entry["proxy_weighted_approval_rate"],
                        "reference_approval_rate": reference["proxy_weighted_approval_rate"],
                        "rate_difference": comparison["effect_size"]["rate_difference"],
                        "rate_difference_ci": comparison["bootstrap"]["rate_difference_ci"],
                        "p_value": comparison["p_value"],
                        "review_trigger": "deeper_fair_lending_review",
                        "result_type": "proxy_screening_only_not_legal_conclusion",
                    }
                )

    return {
        "label": "bisg_proxy_screening_only_not_legal_conclusion",
        "method": "bayesian_improved_surname_geocoding",
        "config_id": config.get("config_id", "bisg-demo"),
        "reference_group": reference_group,
        "alpha": alpha,
        "inference_method": "applicant_level_posterior_predictive_bootstrap",
        "bootstrap": {
            "draws": bootstrap_draws,
            "seed": bootstrap_seed,
            "ci_level": round(bootstrap_ci_level, 4),
        },
        "decision_count": len(decisions),
        "matched_decision_count": matched,
        "unmatched_decision_count": unmatched,
        "posterior_basis_counts": dict(sorted(basis_counts.items())),
        "group_metrics": group_metrics,
        "comparisons": comparisons,
        "finding_count": len(findings),
        "findings": findings,
        "limitations": [
            "BISG produces probabilistic proxies, not observed demographics.",
            "Demonstration reference tables approximate public Census surname data; geography rows are synthetic.",
            "Bootstrap comparisons are unadjusted screening signals, not regression estimates or legal conclusions.",
            "Posterior-predictive bootstrap intervals quantify applicant sampling and BISG posterior membership uncertainty under the proxy model; they still do not prove true protected-class membership.",
            "Legacy rounded-count proportion tests are diagnostics only and are not used for BISG findings.",
        ],
    }
