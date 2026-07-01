"""Phase 4B less-discriminatory-alternative (LDA) assessment.

This module implements a *triggered review* comparison between a baseline
underwriting model and a candidate alternative model on the same synthetic
population. It measures, for each model, a predictive-separation proxy and a
group approval-rate disparity, then reports whether the alternative would
reduce disparity without materially degrading predictive separation.

Design notes and honest limitations:

- This is a synthetic demonstration of an assessment *process*, not a fair
  model search and not a legal conclusion.
- Predictive separation uses synthetic outcome labels as ground truth. In real
  lending, declined applicants have no repayment outcome (reject inference);
  here outcomes are assumed available for demonstration and this assumption is
  stated in the output limitations.
- A positive finding is a governance trigger to review and document a candidate
  alternative, consistent with the framework's treatment of LDA review. It is
  not a determination that a model is unlawful or that an alternative must be
  adopted.
"""

from __future__ import annotations

from typing import Any


def _round(value: float) -> float:
    return round(float(value), 4)


def _approval_rate(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    approved = sum(1 for record in records if record["decision_outcome"] == "approved")
    return approved / len(records)


def build_outcome_index(outcomes: list[dict[str, Any]], good_indicator: str) -> dict[str, bool]:
    """Map decision id -> True when the synthetic outcome is 'good'."""
    index: dict[str, bool] = {}
    for record in outcomes:
        index[record["decision_id"]] = (
            record["repayment_or_default_indicator"] == good_indicator
        )
    return index


def compute_separation(
    model_decisions: dict[str, str],
    outcome_index: dict[str, bool],
) -> dict[str, Any]:
    """Predictive-separation proxy: approval rate among goods minus among bads.

    Higher separation means the model approves goods and declines bads more
    cleanly. Only decisions with a known synthetic outcome are used.
    """
    good_total = good_approved = bad_total = bad_approved = 0
    for decision_id, is_good in outcome_index.items():
        outcome = model_decisions.get(decision_id)
        if outcome is None:
            continue
        approved = outcome == "approved"
        if is_good:
            good_total += 1
            good_approved += int(approved)
        else:
            bad_total += 1
            bad_approved += int(approved)
    good_rate = good_approved / good_total if good_total else 0.0
    bad_rate = bad_approved / bad_total if bad_total else 0.0
    return {
        "good_count": good_total,
        "bad_count": bad_total,
        "approval_rate_goods": _round(good_rate),
        "approval_rate_bads": _round(bad_rate),
        "separation": _round(good_rate - bad_rate),
    }


def compute_disparity(
    decisions: list[dict[str, Any]],
    model_decisions: dict[str, str],
    group_source: str,
    group_field: str,
) -> dict[str, Any]:
    """Group approval-rate disparity ratio (min/max) for a model's decisions."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        if group_source == "monitoring":
            group_value = str(decision["monitoring"][group_field])
        else:
            group_value = str(decision[group_field])
        outcome = model_decisions.get(decision["decision_id"])
        if outcome is None:
            continue
        groups.setdefault(group_value, []).append({"decision_outcome": outcome})

    group_rates = {name: _round(_approval_rate(records)) for name, records in sorted(groups.items())}
    rates = list(group_rates.values())
    max_rate = max(rates, default=0.0)
    min_rate = min(rates, default=0.0)
    ratio = _round(min_rate / max_rate) if max_rate > 0 else 1.0
    return {
        "approval_rate_by_group": group_rates,
        "min_group_approval_rate": min_rate,
        "max_group_approval_rate": max_rate,
        "approval_rate_ratio": ratio,
    }


def _model_decision_map(records: list[dict[str, Any]], outcome_key: str) -> dict[str, str]:
    return {record["decision_id"]: record[outcome_key] for record in records}


def assess_less_discriminatory_alternative(
    decisions: list[dict[str, Any]],
    alternative_decisions: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Compare a baseline model to a candidate alternative on the same population.

    Returns a structured assessment with per-model separation and disparity, the
    deltas, and a governance recommendation. A qualifying alternative both
    reduces disparity (by at least ``min_disparity_improvement``) and holds
    predictive separation within ``performance_tolerance`` of the baseline.
    """
    group_source = config["group_source"]
    group_field = config["group_field"]
    good_indicator = config.get("outcome_good_indicator", "performing")
    min_disparity_improvement = float(config.get("min_disparity_improvement", 0.05))
    performance_tolerance = float(config.get("performance_tolerance", 0.03))

    outcome_index = build_outcome_index(outcomes, good_indicator)

    baseline_map = _model_decision_map(decisions, "decision_outcome")
    alternative_map = _model_decision_map(alternative_decisions, "alternative_outcome")

    baseline = {
        "model_label": "baseline",
        "separation": compute_separation(baseline_map, outcome_index),
        "disparity": compute_disparity(decisions, baseline_map, group_source, group_field),
    }
    alternative = {
        "model_label": "alternative",
        "alternative_model_id": (
            alternative_decisions[0].get("alternative_model_id")
            if alternative_decisions
            else None
        ),
        "separation": compute_separation(alternative_map, outcome_index),
        "disparity": compute_disparity(decisions, alternative_map, group_source, group_field),
    }

    disparity_improvement = _round(
        alternative["disparity"]["approval_rate_ratio"]
        - baseline["disparity"]["approval_rate_ratio"]
    )
    separation_change = _round(
        alternative["separation"]["separation"] - baseline["separation"]["separation"]
    )

    reduces_disparity = disparity_improvement >= min_disparity_improvement
    holds_performance = separation_change >= -performance_tolerance
    qualifies = reduces_disparity and holds_performance

    if qualifies:
        recommendation = (
            "Candidate alternative reduces group approval-rate disparity while holding "
            "predictive separation within tolerance. Trigger a documented less-discriminatory-"
            "alternative review under the governance framework."
        )
        review_trigger = "document_and_review_alternative"
    elif reduces_disparity and not holds_performance:
        recommendation = (
            "Candidate alternative reduces disparity but degrades predictive separation beyond "
            "tolerance. Record the tradeoff; do not treat as a qualifying alternative at the "
            "configured tolerance."
        )
        review_trigger = "record_tradeoff_only"
    else:
        recommendation = (
            "Candidate alternative does not reduce group approval-rate disparity at the configured "
            "improvement threshold. No qualifying less-discriminatory alternative identified in this run."
        )
        review_trigger = "no_qualifying_alternative"

    return {
        "label": "lda_assessment_synthetic_not_legal_conclusion",
        "assessment_id": config.get("assessment_id", "lda-demo"),
        "group_source": group_source,
        "group_field": group_field,
        "thresholds": {
            "min_disparity_improvement": min_disparity_improvement,
            "performance_tolerance": performance_tolerance,
        },
        "baseline": baseline,
        "alternative": alternative,
        "comparison": {
            "disparity_improvement": disparity_improvement,
            "separation_change": separation_change,
            "reduces_disparity": reduces_disparity,
            "holds_performance": holds_performance,
        },
        "qualifying_alternative_identified": qualifies,
        "review_trigger": review_trigger,
        "recommendation": recommendation,
        "limitations": [
            "Synthetic data only; no protected-class labels are used.",
            "Predictive separation uses synthetic outcome labels; real declined applicants lack outcomes (reject inference).",
            "A positive finding is a governance review trigger, not a legal conclusion or a mandate to adopt the alternative.",
        ],
    }
