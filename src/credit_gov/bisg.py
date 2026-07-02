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
probability-weighted counts, and the extreme-group gap is tested for
statistical significance.

Design notes and honest limitations:

- BISG produces *probabilistic proxies*, not observed demographics. All
  outputs are labeled accordingly and proxy-weighted counts are reported so
  reviewers can see effective sample sizes.
- The repository ships small demonstration reference tables
  (``data/reference/bisg/``) whose surname rows are approximations of the
  public U.S. Census 2010 surname file and whose geography rows are synthetic.
  The loader accepts full Census-derived tables in the same format.
- Proxy-weighted comparisons here are unadjusted screening signals. They are
  not regression estimates controlling for legitimate credit factors and not
  legal conclusions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from credit_gov.stats import compare_group_proportions

RACE_CATEGORIES = ["white", "black", "hispanic", "api", "aian", "multiracial"]
DEFAULT_MIN_EFFECTIVE_COUNT = 10.0


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
    approval rates, and tests the reference-group gap for significance using
    rounded effective counts.
    """
    repo_root = dataset_dir.resolve().parents[2]
    surname_table = load_reference_table(repo_root / config["surname_reference_path"])
    geography_table = load_reference_table(repo_root / config["geography_reference_path"])
    with (repo_root / config["national_marginals_path"]).open(encoding="utf-8") as handle:
        national_marginals = {key: float(value) for key, value in json.load(handle).items()}

    reference_group = config.get("reference_group", "white")
    alpha = float(config.get("alpha", 0.05))
    min_effective_count = float(config.get("min_effective_count", DEFAULT_MIN_EFFECTIVE_COUNT))

    inputs_by_decision = {record["decision_id"]: record for record in demographic_inputs}

    weighted: dict[str, dict[str, float]] = {
        category: {"total": 0.0, "approved": 0.0} for category in RACE_CATEGORIES
    }
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
        approved = decision["decision_outcome"] == "approved"
        for category, probability in posterior.items():
            weighted[category]["total"] += probability
            if approved:
                weighted[category]["approved"] += probability

    group_metrics: dict[str, dict[str, Any]] = {}
    for category in RACE_CATEGORIES:
        total = weighted[category]["total"]
        approved = weighted[category]["approved"]
        group_metrics[category] = {
            "proxy_weighted_total": round(total, 2),
            "proxy_weighted_approved": round(approved, 2),
            "proxy_weighted_approval_rate": round(approved / total, 4) if total > 0 else None,
            "adequate_effective_sample": total >= min_effective_count,
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
                    "min_effective_count": min_effective_count,
                }
                continue
            comparison = compare_group_proportions(
                label_a=category,
                successes_a=int(round(weighted[category]["approved"])),
                total_a=int(round(weighted[category]["total"])),
                label_b=reference_group,
                successes_b=int(round(weighted[reference_group]["approved"])),
                total_b=int(round(weighted[reference_group]["total"])),
                alpha=alpha,
            )
            comparison["caveats"].append(
                "Counts are rounded proxy-weighted (BISG posterior) totals, not observed group memberships."
            )
            comparisons[category] = comparison
            if (
                comparison["statistically_significant"]
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
            "Comparisons are unadjusted screening signals with rounded effective counts, not regression estimates or legal conclusions.",
        ],
    }
