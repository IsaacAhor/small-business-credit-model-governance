"""Phase 2 monthly monitoring workflow for synthetic governance datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from credit_gov.schemas import validate_dataset


@dataclass(slots=True)
class MonitoringRunResult:
    ok: bool
    dataset_dir: str
    output_dir: str | None
    errors: list[str]
    metrics: dict[str, Any]
    breaches: list[dict[str, Any]]
    issues: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dataset_dir": self.dataset_dir,
            "output_dir": self.output_dir,
            "errors": self.errors,
            "metrics": self.metrics,
            "breaches": self.breaches,
            "issues": self.issues,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_dataset_payloads(dataset_dir: Path) -> dict[str, Any]:
    return {
        "model_registry": load_json(dataset_dir / "model-registry-record.json"),
        "model_version": load_json(dataset_dir / "model-version-record.json"),
        "threshold_set": load_json(dataset_dir / "threshold-set.json"),
        "decisions": load_json(dataset_dir / "application-decision-records.json"),
        "score_outputs": load_json(dataset_dir / "score-outputs.json"),
        "reason_mappings": load_json(dataset_dir / "reason-code-mappings.json"),
        "overrides": load_json(dataset_dir / "override-events.json"),
        "outcomes": load_json(dataset_dir / "outcome-records.json"),
        "manifest": load_json(dataset_dir / "evidence-pack-manifest.json"),
    }


def run_monthly_monitoring(
    dataset_dir: Path,
    evidence_root: Path | None = None,
) -> MonitoringRunResult:
    dataset_dir = dataset_dir.resolve()
    validation = validate_dataset(dataset_dir)
    if not validation.ok:
        return MonitoringRunResult(
            ok=False,
            dataset_dir=str(dataset_dir),
            output_dir=None,
            errors=validation.errors,
            metrics={},
            breaches=[],
            issues=[],
        )

    payloads = load_dataset_payloads(dataset_dir)
    metrics = compute_metrics(payloads)
    breaches = evaluate_thresholds(metrics, payloads["threshold_set"], payloads["manifest"]["run_id"])
    issues = build_issue_register(breaches)

    evidence_root = (evidence_root or dataset_dir / ".." / ".." / "evidence").resolve()
    evidence_dir = build_evidence_pack(
        dataset_dir=dataset_dir,
        evidence_root=evidence_root,
        payloads=payloads,
        metrics=metrics,
        breaches=breaches,
        issues=issues,
    )
    return MonitoringRunResult(
        ok=True,
        dataset_dir=str(dataset_dir),
        output_dir=str(evidence_dir),
        errors=[],
        metrics=metrics,
        breaches=breaches,
        issues=issues,
    )


def compute_metrics(payloads: dict[str, Any]) -> dict[str, Any]:
    decisions = payloads["decisions"]
    scores = payloads["score_outputs"]
    reason_mappings = payloads["reason_mappings"]
    outcomes = payloads["outcomes"]

    total_decisions = len(decisions)
    approved = sum(1 for record in decisions if record["decision_outcome"] == "approved")
    declined = sum(1 for record in decisions if record["decision_outcome"] == "declined")
    manual_reviews = sum(1 for record in decisions if record["manual_review_flag"])
    overrides = sum(1 for record in decisions if record["override_flag"])

    score_values = [record["score_value"] for record in scores]
    score_bands = count_by_key(scores, "score_band")
    segments = count_by_key(decisions, "segment")
    regions = count_by_nested_key(decisions, "monitoring", "region")
    channels = count_by_nested_key(decisions, "monitoring", "channel")
    reason_codes = count_by_key(reason_mappings, "reason_code")
    outcomes_summary = count_by_key(outcomes, "repayment_or_default_indicator")

    fairness_by_region = build_group_outcomes(decisions, "region")
    fairness_by_segment = build_group_outcomes(decisions, "segment")

    return {
        "run_id": payloads["manifest"]["run_id"],
        "model_id": payloads["model_registry"]["model_id"],
        "version_id": payloads["model_version"]["version_id"],
        "total_decisions": total_decisions,
        "approval_rate": safe_rate(approved, total_decisions),
        "decline_rate": safe_rate(declined, total_decisions),
        "override_rate": safe_rate(overrides, total_decisions),
        "manual_review_rate": safe_rate(manual_reviews, total_decisions),
        "score_distribution": {
            "count": len(score_values),
            "minimum": min(score_values),
            "maximum": max(score_values),
            "average": round(sum(score_values) / len(score_values), 4),
            "bands": score_bands,
        },
        "reason_code_distribution": {
            "configured_reason_code_count": len(reason_mappings),
            "counts": reason_codes,
        },
        "population_drift_indicators": {
            "baseline": "not_configured_for_demo",
            "segment_mix": to_share_map(segments, total_decisions),
            "region_mix": to_share_map(regions, total_decisions),
            "channel_mix": to_share_map(channels, total_decisions),
        },
        "fair_lending_screening": {
            "label": "screening_only_not_legal_conclusion",
            "approval_rate_by_region": fairness_by_region,
            "approval_rate_by_segment": fairness_by_segment,
            "minimum_region_approval_rate": min(
                (entry["approval_rate"] for entry in fairness_by_region.values()),
                default=0.0,
            ),
            "maximum_region_approval_rate": max(
                (entry["approval_rate"] for entry in fairness_by_region.values()),
                default=0.0,
            ),
        },
        "outcome_summary": outcomes_summary,
    }


def evaluate_thresholds(
    metrics: dict[str, Any],
    threshold_set: dict[str, Any],
    run_id: str,
) -> list[dict[str, Any]]:
    breaches: list[dict[str, Any]] = []
    for threshold in threshold_set["thresholds"]:
        metric_name = threshold["metric_name"]
        observed_value = metrics.get(metric_name)
        if not isinstance(observed_value, (int, float)):
            continue
        if threshold_breached(
            float(observed_value),
            threshold["comparison_rule"],
            float(threshold["threshold_value"]),
        ):
            breach_index = len(breaches) + 1
            breaches.append(
                {
                    "record_type": "breach_record",
                    "breach_id": f"brc-{breach_index:04d}",
                    "run_id": run_id,
                    "metric_name": metric_name,
                    "observed_value": round(float(observed_value), 4),
                    "threshold_value": float(threshold["threshold_value"]),
                    "severity": threshold["severity"],
                    "owner": threshold["escalation_owner"],
                }
            )
    return breaches


def threshold_breached(observed_value: float, comparison_rule: str, threshold_value: float) -> bool:
    if comparison_rule == "greater_than":
        return observed_value > threshold_value
    if comparison_rule == "less_than":
        return observed_value < threshold_value
    raise ValueError(f"Unsupported comparison rule: {comparison_rule}")


def build_issue_register(breaches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for index, breach in enumerate(breaches, start=1):
        issues.append(
            {
                "issue_id": f"iss-{index:04d}",
                "linked_breach_ids": [breach["breach_id"]],
                "summary": (
                    f"{breach['metric_name']} breached its configured threshold "
                    f"({breach['observed_value']} vs {breach['threshold_value']})."
                ),
                "status": "open",
                "owner": breach["owner"],
                "due_date": "2026-06-30",
            }
        )
    return issues


def build_evidence_pack(
    dataset_dir: Path,
    evidence_root: Path,
    payloads: dict[str, Any],
    metrics: dict[str, Any],
    breaches: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> Path:
    manifest = payloads["manifest"]
    evidence_dir = evidence_root / format_evidence_dir_name(
        dataset_dir.name,
        manifest["run_id"],
        manifest["created_at"],
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    generated_manifest = {
        "record_type": "evidence_pack_manifest",
        "run_id": manifest["run_id"],
        "created_at": manifest["created_at"],
        "model_id": manifest["model_id"],
        "version_id": manifest["version_id"],
        "input_references": manifest["input_references"],
        "output_files": [
            "manifest.json",
            "config_snapshot.json",
            "input_fingerprints.json",
            "model_record.json",
            "threshold_set.json",
            "metric_results.json",
            "breach_register.json",
            "issue_register.json",
            "monitoring_report.md",
            "reviewer_signoff.md",
        ],
        "reviewer_status": manifest["reviewer_status"],
    }
    write_json(evidence_dir / "manifest.json", generated_manifest)
    write_json(
        evidence_dir / "config_snapshot.json",
        {
            "threshold_set_id": payloads["threshold_set"]["threshold_set_id"],
            "review_cadence": payloads["threshold_set"]["review_cadence"],
            "thresholds": payloads["threshold_set"]["thresholds"],
        },
    )
    write_json(evidence_dir / "input_fingerprints.json", build_input_fingerprints(dataset_dir))
    write_json(evidence_dir / "model_record.json", payloads["model_registry"])
    write_json(evidence_dir / "threshold_set.json", payloads["threshold_set"])
    write_json(evidence_dir / "metric_results.json", metrics)
    write_json(evidence_dir / "breach_register.json", breaches)
    write_json(evidence_dir / "issue_register.json", issues)
    (evidence_dir / "monitoring_report.md").write_text(
        render_monitoring_report(metrics, breaches, issues),
        encoding="utf-8",
    )
    (evidence_dir / "reviewer_signoff.md").write_text(
        render_reviewer_signoff(generated_manifest, breaches),
        encoding="utf-8",
    )
    return evidence_dir


def build_input_fingerprints(dataset_dir: Path) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for path in sorted(dataset_dir.glob("*.json")):
        fingerprints[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return fingerprints


def render_monitoring_report(
    metrics: dict[str, Any],
    breaches: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> str:
    breach_lines = (
        "\n".join(
            f"- {breach['metric_name']}: observed {breach['observed_value']} vs threshold {breach['threshold_value']} "
            f"({breach['severity']}, owner: {breach['owner']})"
            for breach in breaches
        )
        if breaches
        else "- No threshold breaches were generated for this run."
    )
    issue_lines = (
        "\n".join(
            f"- {issue['issue_id']}: {issue['summary']} Owner: {issue['owner']}. Due: {issue['due_date']}."
            for issue in issues
        )
        if issues
        else "- No remediation issues were opened."
    )
    return (
        "# Monthly Monitoring Report\n\n"
        "This report is deterministic, synthetic, and intended only for governance workflow demonstration.\n\n"
        f"- Run ID: `{metrics['run_id']}`\n"
        f"- Model ID: `{metrics['model_id']}`\n"
        f"- Version ID: `{metrics['version_id']}`\n"
        f"- Total decisions reviewed: {metrics['total_decisions']}\n"
        f"- Approval rate: {metrics['approval_rate']}\n"
        f"- Decline rate: {metrics['decline_rate']}\n"
        f"- Override rate: {metrics['override_rate']}\n"
        f"- Manual review rate: {metrics['manual_review_rate']}\n\n"
        "## Threshold Breaches\n\n"
        f"{breach_lines}\n\n"
        "## Issue Register\n\n"
        f"{issue_lines}\n"
    )


def render_reviewer_signoff(manifest: dict[str, Any], breaches: list[dict[str, Any]]) -> str:
    review_state = "Escalation recommended" if breaches else "No escalation required in demo run"
    return (
        "# Reviewer Signoff\n\n"
        "This artifact supports governance workflow demonstration only.\n\n"
        f"- Run ID: `{manifest['run_id']}`\n"
        f"- Reviewer status: `{manifest['reviewer_status']}`\n"
        f"- Review summary: {review_state}\n\n"
        "Reviewer: ____________________\n\n"
        "Date: ____________________\n"
    )


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def format_evidence_dir_name(dataset_name: str, run_id: str, created_at: str) -> str:
    sanitized = created_at.replace(":", "").replace("-", "").replace("T", "-").replace("Z", "Z")
    return f"{dataset_name}-{run_id}-{sanitized}"


def count_by_key(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record[key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def count_by_nested_key(records: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record[outer_key][inner_key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def to_share_map(counts: dict[str, int], total: int) -> dict[str, float]:
    return {key: safe_rate(value, total) for key, value in sorted(counts.items())}


def build_group_outcomes(records: list[dict[str, Any]], mode: str) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, dict[str, int]] = {}
    for record in records:
        if mode == "region":
            group = record["monitoring"]["region"]
        else:
            group = record["segment"]
        entry = grouped.setdefault(group, {"total": 0, "approved": 0})
        entry["total"] += 1
        if record["decision_outcome"] == "approved":
            entry["approved"] += 1
    return {
        key: {
            "total": value["total"],
            "approved": value["approved"],
            "approval_rate": safe_rate(value["approved"], value["total"]),
        }
        for key, value in sorted(grouped.items())
    }


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
