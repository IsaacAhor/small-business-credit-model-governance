"""Phase 5 model-change and validation-review workflow.

This module compares a *prior* set of governed records against the *current*
set for the same model and produces a deterministic change-impact assessment:

- a model-version diff (effective date, change summary, assumptions, limitations)
- a threshold-set diff (added, removed, and changed thresholds, with a
  tightened/loosened reading where the comparison rule is unchanged)
- a reason-code mapping diff (added, removed, and changed codes, separating a
  structural text/driver change from a mapping-version bump)
- a change summary with a configurable materiality reading and derived review
  actions
- a reviewer signoff record tied to the specific current version and the
  evidence-pack run

Design notes and honest limitations:

- This is a synthetic demonstration of a change-governance *process*, not a
  production model-change control and not a legal or regulatory determination.
- Change materiality is a configurable governance heuristic. A material change
  is a trigger to document rationale and obtain independent validation signoff,
  not a finding that a change is compliant or non-compliant.
- Regulatory references used in the derived review actions (Regulation B
  12 CFR 1002.9 reason specificity; SR 26-2 principles-based model-risk
  oversight and change management) are design anchors for the governance
  concepts, not evidence of compliance.
"""

from __future__ import annotations

from typing import Any

MODEL_VERSION_SCALAR_FIELDS = (
    "version_id",
    "effective_date",
    "change_summary",
    "linked_validation_record",
)
MODEL_VERSION_LIST_FIELDS = ("assumptions", "limitations")

THRESHOLD_FIELDS = (
    "comparison_rule",
    "threshold_value",
    "severity",
    "escalation_owner",
)
REASON_MAPPING_FIELDS = (
    "driver_or_signal",
    "reason_text",
    "mapping_version",
)


def _scalar_change(prior: Any, current: Any) -> dict[str, Any]:
    return {"prior": prior, "current": current, "changed": prior != current}


def _list_change(prior: list[Any] | None, current: list[Any] | None) -> dict[str, Any]:
    prior_set = set(prior or [])
    current_set = set(current or [])
    return {
        "added": sorted(current_set - prior_set),
        "removed": sorted(prior_set - current_set),
        "unchanged_count": len(prior_set & current_set),
        "changed": bool((current_set - prior_set) or (prior_set - current_set)),
    }


def diff_model_version(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Field-level diff of two model-version records."""
    diff: dict[str, Any] = {"status": "compared"}
    for field in MODEL_VERSION_SCALAR_FIELDS:
        diff[field] = _scalar_change(prior.get(field), current.get(field))
    for field in MODEL_VERSION_LIST_FIELDS:
        diff[field] = _list_change(prior.get(field), current.get(field))
    diff["changed"] = any(
        diff[field]["changed"]
        for field in (*MODEL_VERSION_SCALAR_FIELDS, *MODEL_VERSION_LIST_FIELDS)
    )
    return diff


def _threshold_direction(rule: str, prior_value: float, current_value: float) -> str:
    """Whether a threshold-value change makes the screen fire more or less easily.

    A ``less_than`` breach fires when the observed value drops below the
    threshold, so raising the threshold value makes it more sensitive
    (tightened). A ``greater_than`` breach fires when the observed value rises
    above the threshold, so lowering the threshold value tightens it.
    """
    if current_value == prior_value:
        return "unchanged"
    if rule == "less_than":
        return "tightened" if current_value > prior_value else "loosened"
    if rule == "greater_than":
        return "tightened" if current_value < prior_value else "loosened"
    return "changed"


def _index_by(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {record[key]: record for record in records}


def _field_changes(
    prior: dict[str, Any],
    current: dict[str, Any],
    fields: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for field in fields:
        if prior.get(field) != current.get(field):
            changes[field] = {"prior": prior.get(field), "current": current.get(field)}
    return changes


def diff_threshold_set(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Diff two threshold sets keyed by ``metric_name``."""
    prior_thresholds = _index_by(prior.get("thresholds", []), "metric_name")
    current_thresholds = _index_by(current.get("thresholds", []), "metric_name")

    added = sorted(set(current_thresholds) - set(prior_thresholds))
    removed = sorted(set(prior_thresholds) - set(current_thresholds))
    shared = sorted(set(prior_thresholds) & set(current_thresholds))

    changed: list[dict[str, Any]] = []
    unchanged: list[str] = []
    for metric_name in shared:
        prior_threshold = prior_thresholds[metric_name]
        current_threshold = current_thresholds[metric_name]
        field_changes = _field_changes(prior_threshold, current_threshold, THRESHOLD_FIELDS)
        if not field_changes:
            unchanged.append(metric_name)
            continue
        rule_changed = prior_threshold.get("comparison_rule") != current_threshold.get("comparison_rule")
        if rule_changed:
            direction = "rule_changed"
        else:
            direction = _threshold_direction(
                current_threshold.get("comparison_rule"),
                float(prior_threshold.get("threshold_value")),
                float(current_threshold.get("threshold_value")),
            )
        changed.append(
            {
                "metric_name": metric_name,
                "direction": direction,
                "field_changes": field_changes,
            }
        )

    return {
        "status": "compared",
        "threshold_set_id": _scalar_change(
            prior.get("threshold_set_id"), current.get("threshold_set_id")
        ),
        "added": [_threshold_summary(current_thresholds[name]) for name in added],
        "removed": [_threshold_summary(prior_thresholds[name]) for name in removed],
        "changed": changed,
        "unchanged": unchanged,
        "change_count": len(added) + len(removed) + len(changed),
    }


def _threshold_summary(threshold: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric_name": threshold["metric_name"],
        "comparison_rule": threshold["comparison_rule"],
        "threshold_value": threshold["threshold_value"],
        "severity": threshold.get("severity"),
        "escalation_owner": threshold.get("escalation_owner"),
    }


def diff_reason_code_mappings(
    prior: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> dict[str, Any]:
    """Diff two reason-code mapping tables keyed by ``reason_code``."""
    prior_by_code = _index_by(prior, "reason_code")
    current_by_code = _index_by(current, "reason_code")

    added = sorted(set(current_by_code) - set(prior_by_code))
    removed = sorted(set(prior_by_code) - set(current_by_code))
    shared = sorted(set(prior_by_code) & set(current_by_code))

    changed: list[dict[str, Any]] = []
    unchanged: list[str] = []
    structural_change_count = 0
    for reason_code in shared:
        field_changes = _field_changes(
            prior_by_code[reason_code], current_by_code[reason_code], REASON_MAPPING_FIELDS
        )
        if not field_changes:
            unchanged.append(reason_code)
            continue
        structural = any(field in field_changes for field in ("driver_or_signal", "reason_text"))
        if structural:
            structural_change_count += 1
        changed.append(
            {
                "reason_code": reason_code,
                "structural_change": structural,
                "field_changes": field_changes,
            }
        )

    prior_versions = sorted({record.get("mapping_version") for record in prior if record.get("mapping_version")})
    current_versions = sorted(
        {record.get("mapping_version") for record in current if record.get("mapping_version")}
    )

    return {
        "status": "compared",
        "added": [_reason_summary(current_by_code[code]) for code in added],
        "removed": [_reason_summary(prior_by_code[code]) for code in removed],
        "changed": changed,
        "unchanged": unchanged,
        "structural_change_count": structural_change_count,
        "mapping_version": {
            "prior_versions": prior_versions,
            "current_versions": current_versions,
            "changed": prior_versions != current_versions,
        },
        "change_count": len(added) + len(removed) + len(changed),
    }


def _reason_summary(mapping: dict[str, Any]) -> dict[str, Any]:
    return {
        "reason_code": mapping["reason_code"],
        "driver_or_signal": mapping.get("driver_or_signal"),
        "reason_text": mapping.get("reason_text"),
        "mapping_version": mapping.get("mapping_version"),
    }


def _threshold_categories(threshold_diff: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    if threshold_diff.get("status") != "compared":
        return categories
    if threshold_diff["added"]:
        categories.append("threshold_added")
    if threshold_diff["removed"]:
        categories.append("threshold_removed")
    directions = {entry["direction"] for entry in threshold_diff["changed"]}
    if "tightened" in directions:
        categories.append("threshold_tightened")
    if "loosened" in directions:
        categories.append("threshold_loosened")
    if directions & {"changed", "rule_changed"}:
        categories.append("threshold_rule_or_value_changed")
    return categories


def _reason_categories(reason_diff: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    if reason_diff.get("status") != "compared":
        return categories
    if reason_diff["added"]:
        categories.append("reason_code_added")
    if reason_diff["removed"]:
        categories.append("reason_code_removed")
    if reason_diff["structural_change_count"]:
        categories.append("reason_code_text_or_driver_changed")
    if reason_diff["mapping_version"]["changed"]:
        categories.append("reason_code_mapping_version_bumped")
    return categories


def build_change_summary(
    version_diff: dict[str, Any],
    threshold_diff: dict[str, Any],
    reason_diff: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate the three diffs into a materiality reading and review actions."""
    categories: list[str] = []
    if version_diff.get("limitations", {}).get("added"):
        categories.append("model_limitations_expanded")
    if version_diff.get("change_summary", {}).get("changed"):
        categories.append("model_change_summary_updated")
    categories.extend(_threshold_categories(threshold_diff))
    categories.extend(_reason_categories(reason_diff))

    material_categories = {
        "threshold_added",
        "threshold_removed",
        "threshold_tightened",
        "threshold_loosened",
        "threshold_rule_or_value_changed",
        "reason_code_added",
        "reason_code_removed",
        "reason_code_text_or_driver_changed",
    }
    material_change = any(category in material_categories for category in categories)

    return {
        "prior_version_id": version_diff["version_id"]["prior"],
        "current_version_id": version_diff["version_id"]["current"],
        "model_version_changed": version_diff["changed"],
        "threshold_change_count": _diff_change_count(threshold_diff),
        "reason_code_change_count": _diff_change_count(reason_diff),
        "material_change": material_change,
        "change_categories": categories,
        "review_actions": _review_actions(threshold_diff, reason_diff, material_change),
    }


def _diff_change_count(diff: dict[str, Any]) -> Any:
    if diff.get("status") != "compared":
        return diff.get("status", "not_available")
    return diff["change_count"]


def _review_actions(
    threshold_diff: dict[str, Any],
    reason_diff: dict[str, Any],
    material_change: bool,
) -> list[str]:
    actions: list[str] = []

    if threshold_diff.get("status") == "compared":
        changed_metrics = sorted(entry["metric_name"] for entry in threshold_diff["changed"])
        if changed_metrics:
            actions.append(
                "Document the rationale and expected monitoring impact for changed threshold(s) "
                f"({', '.join(changed_metrics)}) and re-baseline breach expectations for the new version."
            )
        removed_metrics = sorted(entry["metric_name"] for entry in threshold_diff["removed"])
        if removed_metrics:
            actions.append(
                f"Confirm that removing the {', '.join(removed_metrics)} threshold(s) is an approved "
                "governance decision with a documented compensating control."
            )
        added_metrics = sorted(entry["metric_name"] for entry in threshold_diff["added"])
        if added_metrics:
            actions.append(
                f"Confirm ownership and escalation routing for added threshold(s) ({', '.join(added_metrics)})."
            )

    if reason_diff.get("status") == "compared":
        added_codes = sorted(entry["reason_code"] for entry in reason_diff["added"])
        if added_codes:
            actions.append(
                f"Verify adverse-action notices and reason-code mappings for added code(s) ({', '.join(added_codes)}) "
                "produce specific, accurate reasons consistent with Regulation B 12 CFR 1002.9."
            )
        removed_codes = sorted(entry["reason_code"] for entry in reason_diff["removed"])
        if removed_codes:
            actions.append(
                f"Confirm no active adverse-action notice depends on removed reason code(s) ({', '.join(removed_codes)})."
            )
        structural_codes = sorted(
            entry["reason_code"] for entry in reason_diff["changed"] if entry["structural_change"]
        )
        if structural_codes:
            actions.append(
                f"Review revised reason text or driver mapping for code(s) ({', '.join(structural_codes)}) "
                "for continued specificity and accuracy."
            )

    if material_change:
        actions.append(
            "Obtain independent validation signoff tying the current version to this evidence pack before "
            "promoting the version to active, consistent with principles-based model-risk change management."
        )
    else:
        actions.append(
            "Record the change as non-material at the configured policy and retain this comparison as evidence."
        )
    return actions


def build_reviewer_signoff_record(
    summary: dict[str, Any],
    model_id: str,
    run_id: str,
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    """Structured signoff record tied to the specific version and evidence pack."""
    config = config or {}
    return {
        "record_type": "model_change_validation_signoff",
        "model_id": model_id,
        "prior_version_id": summary["prior_version_id"],
        "current_version_id": summary["current_version_id"],
        "evidence_pack_run_id": run_id,
        "validation_owner": config.get("validation_owner", "Independent Model Validation"),
        "promotion_gate": config.get("promotion_gate", "independent_validation_signoff"),
        "material_change": summary["material_change"],
        "required_before_promotion": summary["review_actions"],
        "validation_status": "pending_review",
        "reviewer": None,
        "signoff_date": None,
    }


def assess_model_change(
    prior_version: dict[str, Any],
    current_version: dict[str, Any],
    current_thresholds: dict[str, Any],
    current_reason_mappings: list[dict[str, Any]],
    model_id: str,
    run_id: str,
    prior_thresholds: dict[str, Any] | None = None,
    prior_reason_mappings: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full Phase 5 change-validation assessment.

    ``prior_thresholds`` and ``prior_reason_mappings`` are optional; when a prior
    snapshot for one of them is absent, that sub-diff is reported as
    ``prior_not_available`` and does not contribute to materiality.
    """
    config = config or {}
    version_diff = diff_model_version(prior_version, current_version)

    if prior_thresholds is not None:
        threshold_diff = diff_threshold_set(prior_thresholds, current_thresholds)
    else:
        threshold_diff = {"status": "prior_not_available"}

    if prior_reason_mappings is not None:
        reason_diff = diff_reason_code_mappings(prior_reason_mappings, current_reason_mappings)
    else:
        reason_diff = {"status": "prior_not_available"}

    summary = build_change_summary(version_diff, threshold_diff, reason_diff)
    signoff = build_reviewer_signoff_record(summary, model_id, run_id, config)

    return {
        "label": "model_change_validation_synthetic_not_legal_conclusion",
        "change_review_id": config.get("change_review_id", "chg-demo"),
        "model_id": model_id,
        "evidence_pack_run_id": run_id,
        "model_version_diff": version_diff,
        "threshold_set_diff": threshold_diff,
        "reason_code_mapping_diff": reason_diff,
        "summary": summary,
        "reviewer_signoff": signoff,
        "limitations": [
            "Synthetic data only; no production model change is represented.",
            "Change materiality is a configurable governance heuristic, not a legal or regulatory determination.",
            "Signoff fields are illustrative placeholders; no independent validation has occurred.",
            "Regulatory references (Regulation B 12 CFR 1002.9 reason specificity; SR 26-2 principles-based "
            "model-risk oversight and change management) are design anchors, not evidence of compliance.",
        ],
    }


def render_change_validation_report(result: dict[str, Any]) -> str:
    """Reviewer-facing Markdown report for a change-validation assessment."""
    summary = result["summary"]
    version_diff = result["model_version_diff"]
    threshold_diff = result["threshold_set_diff"]
    reason_diff = result["reason_code_mapping_diff"]

    version_lines = "\n".join(
        f"- {field}: `{version_diff[field]['prior']}` -> `{version_diff[field]['current']}`"
        for field in MODEL_VERSION_SCALAR_FIELDS
        if version_diff[field]["changed"]
    ) or "- No scalar model-version fields changed."

    threshold_lines = _render_threshold_lines(threshold_diff)
    reason_lines = _render_reason_lines(reason_diff)
    action_lines = "\n".join(f"- {action}" for action in summary["review_actions"])
    category_text = ", ".join(summary["change_categories"]) or "none"
    limitation_lines = "\n".join(f"- {item}" for item in result["limitations"])

    return (
        "# Model-Change Validation Review\n\n"
        "This report is deterministic, synthetic, and intended only for change-governance workflow "
        "demonstration. Findings are governance review triggers, not legal or regulatory conclusions.\n\n"
        f"- Change review ID: `{result['change_review_id']}`\n"
        f"- Model ID: `{result['model_id']}`\n"
        f"- Prior version: `{summary['prior_version_id']}` -> current version: `{summary['current_version_id']}`\n"
        f"- Evidence pack run: `{result['evidence_pack_run_id']}`\n"
        f"- Material change: {summary['material_change']}\n"
        f"- Change categories: {category_text}\n\n"
        "## Model-Version Changes\n\n"
        f"{version_lines}\n\n"
        f"- Assumptions added: {version_diff['assumptions']['added'] or 'none'}\n"
        f"- Assumptions removed: {version_diff['assumptions']['removed'] or 'none'}\n"
        f"- Limitations added: {version_diff['limitations']['added'] or 'none'}\n"
        f"- Limitations removed: {version_diff['limitations']['removed'] or 'none'}\n\n"
        "## Threshold-Set Changes\n\n"
        f"{threshold_lines}\n\n"
        "## Reason-Code Mapping Changes\n\n"
        f"{reason_lines}\n\n"
        "## Required Review Actions Before Promotion\n\n"
        f"{action_lines}\n\n"
        "## Limitations\n\n"
        f"{limitation_lines}\n"
    )


def _render_threshold_lines(threshold_diff: dict[str, Any]) -> str:
    if threshold_diff.get("status") != "compared":
        return "- No prior threshold set was supplied; threshold comparison was skipped."
    lines: list[str] = []
    for entry in threshold_diff["added"]:
        lines.append(f"- Added: {entry['metric_name']} ({entry['comparison_rule']} {entry['threshold_value']})")
    for entry in threshold_diff["removed"]:
        lines.append(f"- Removed: {entry['metric_name']} ({entry['comparison_rule']} {entry['threshold_value']})")
    for entry in threshold_diff["changed"]:
        field_bits = ", ".join(
            f"{field} {change['prior']} -> {change['current']}"
            for field, change in sorted(entry["field_changes"].items())
        )
        lines.append(f"- Changed ({entry['direction']}): {entry['metric_name']} [{field_bits}]")
    if not lines:
        return "- No threshold changes were identified."
    return "\n".join(lines)


def _render_reason_lines(reason_diff: dict[str, Any]) -> str:
    if reason_diff.get("status") != "compared":
        return "- No prior reason-code mapping was supplied; reason-code comparison was skipped."
    lines: list[str] = []
    for entry in reason_diff["added"]:
        lines.append(f"- Added: {entry['reason_code']} ({entry['reason_text']})")
    for entry in reason_diff["removed"]:
        lines.append(f"- Removed: {entry['reason_code']} ({entry['reason_text']})")
    for entry in reason_diff["changed"]:
        kind = "structural" if entry["structural_change"] else "version-only"
        field_bits = ", ".join(
            f"{field} {change['prior']!r} -> {change['current']!r}"
            for field, change in sorted(entry["field_changes"].items())
        )
        lines.append(f"- Changed ({kind}): {entry['reason_code']} [{field_bits}]")
    if reason_diff["mapping_version"]["changed"]:
        lines.append(
            f"- Mapping version: {reason_diff['mapping_version']['prior_versions']} -> "
            f"{reason_diff['mapping_version']['current_versions']}"
        )
    if not lines:
        return "- No reason-code mapping changes were identified."
    return "\n".join(lines)
