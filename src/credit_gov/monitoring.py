"""Phase 2 monthly monitoring workflow for synthetic governance datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from credit_gov.bisg import run_bisg_proxy_analysis
from credit_gov.lda import assess_less_discriminatory_alternative
from credit_gov.reason_fidelity import (
    REQUIRED_REASON_FIDELITY_FIELDS,
    build_reason_fidelity_context,
    is_active_on_date,
    normalize_reason_text,
    rank_decision_contributions,
    source_components_for_decision,
)
from credit_gov.schemas import validate_dataset
from credit_gov.stats import compare_group_proportions
from credit_gov.validation import assess_model_change, render_change_validation_report


@dataclass(slots=True)
class MonitoringRunResult:
    ok: bool
    dataset_dir: str
    output_dir: str | None
    errors: list[str]
    metrics: dict[str, Any]
    breaches: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    reason_qa: dict[str, Any]
    fair_lending: dict[str, Any]
    lda: dict[str, Any] | None = None
    bisg: dict[str, Any] | None = None
    change_validation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dataset_dir": self.dataset_dir,
            "output_dir": self.output_dir,
            "errors": self.errors,
            "metrics": self.metrics,
            "breaches": self.breaches,
            "issues": self.issues,
            "reason_qa": self.reason_qa,
            "fair_lending": self.fair_lending,
            "lda": self.lda,
            "bisg": self.bisg,
            "change_validation": self.change_validation,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return load_json(path)


def compute_optional_lda(dataset_dir: Path, payloads: dict[str, Any]) -> dict[str, Any] | None:
    """Run the LDA assessment when its optional inputs are present in the dataset.

    Requires ``lda-assessment-config.json`` and ``alternative-model-decisions.json``.
    Returns ``None`` when either is absent so existing datasets are unaffected.
    """
    config = load_optional_json(dataset_dir / "lda-assessment-config.json")
    alternative = load_optional_json(dataset_dir / "alternative-model-decisions.json")
    if config is None or alternative is None:
        return None
    return assess_less_discriminatory_alternative(
        decisions=payloads["decisions"],
        alternative_decisions=alternative,
        outcomes=payloads["outcomes"],
        config=config,
    )


def compute_optional_bisg(dataset_dir: Path, payloads: dict[str, Any]) -> dict[str, Any] | None:
    """Run BISG proxy-based screening when its optional inputs are present.

    Requires ``bisg-config.json`` and ``applicant-demographic-inputs.json``.
    Returns ``None`` when either is absent so existing datasets are unaffected.
    """
    config = load_optional_json(dataset_dir / "bisg-config.json")
    demographic_inputs = load_optional_json(dataset_dir / "applicant-demographic-inputs.json")
    if config is None or demographic_inputs is None:
        return None
    return run_bisg_proxy_analysis(
        decisions=payloads["decisions"],
        demographic_inputs=demographic_inputs,
        config=config,
        dataset_dir=dataset_dir,
    )


def compute_optional_change_validation(
    dataset_dir: Path, payloads: dict[str, Any]
) -> dict[str, Any] | None:
    """Run the Phase 5 model-change validation when its optional inputs exist.

    Triggered by the presence of ``prior-model-version-record.json``. The prior
    threshold set (``prior-threshold-set.json``) and prior reason-code mappings
    (``prior-reason-code-mappings.json``) are each optional within the review;
    a missing prior for one of them skips that sub-diff without failing. Returns
    ``None`` when no prior model-version snapshot is present so existing datasets
    are unaffected.
    """
    prior_version = load_optional_json(dataset_dir / "prior-model-version-record.json")
    if prior_version is None:
        return None
    prior_thresholds = load_optional_json(dataset_dir / "prior-threshold-set.json")
    prior_reason_mappings = load_optional_json(dataset_dir / "prior-reason-code-mappings.json")
    config = load_optional_json(dataset_dir / "change-review-config.json")
    return assess_model_change(
        prior_version=prior_version,
        current_version=payloads["model_version"],
        current_thresholds=payloads["threshold_set"],
        current_reason_mappings=payloads["reason_mappings"],
        model_id=payloads["model_registry"]["model_id"],
        run_id=payloads["manifest"]["run_id"],
        prior_thresholds=prior_thresholds,
        prior_reason_mappings=prior_reason_mappings,
        config=config,
    )


def load_dataset_payloads(dataset_dir: Path) -> dict[str, Any]:
    return {
        "model_registry": load_json(dataset_dir / "model-registry-record.json"),
        "model_version": load_json(dataset_dir / "model-version-record.json"),
        "threshold_set": load_json(dataset_dir / "threshold-set.json"),
        "fair_lending_config": load_json(dataset_dir / "fair-lending-screening-config.json"),
        "decisions": load_json(dataset_dir / "application-decision-records.json"),
        "score_outputs": load_json(dataset_dir / "score-outputs.json"),
        "reason_mappings": load_json(dataset_dir / "reason-code-mappings.json"),
        "reason_outputs": load_json(dataset_dir / "adverse-action-reason-outputs.json"),
        "driver_contributions": load_optional_json(
            dataset_dir / "adverse-action-driver-contributions.json"
        ),
        "reason_fidelity_policy": load_optional_json(dataset_dir / "reason-fidelity-policy.json"),
        "notice_template": load_optional_json(dataset_dir / "adverse-action-notice-template.json"),
        "reason_selection_methods": load_optional_json(
            dataset_dir / "reason-selection-methods.json"
        ),
        "rendered_notices": load_optional_json(
            dataset_dir / "rendered-adverse-action-notices.json"
        ),
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
            reason_qa={},
            fair_lending={},
        )

    payloads = load_dataset_payloads(dataset_dir)
    metrics = compute_metrics(payloads)
    reason_qa = compute_reason_qa(payloads)
    fair_lending = compute_fair_lending_screening(payloads)
    lda = compute_optional_lda(dataset_dir, payloads)
    bisg = compute_optional_bisg(dataset_dir, payloads)
    change_validation = compute_optional_change_validation(dataset_dir, payloads)
    breaches = evaluate_thresholds(metrics, payloads["threshold_set"], payloads["manifest"]["run_id"])
    issues = build_issue_register(breaches, reason_qa["exceptions"], fair_lending["findings"])

    evidence_root = (evidence_root or dataset_dir / ".." / ".." / "evidence").resolve()
    evidence_dir = build_evidence_pack(
        dataset_dir=dataset_dir,
        evidence_root=evidence_root,
        payloads=payloads,
        metrics=metrics,
        breaches=breaches,
        issues=issues,
        reason_qa=reason_qa,
        fair_lending=fair_lending,
        lda=lda,
        bisg=bisg,
        change_validation=change_validation,
    )
    return MonitoringRunResult(
        ok=True,
        dataset_dir=str(dataset_dir),
        output_dir=str(evidence_dir),
        errors=[],
        metrics=metrics,
        breaches=breaches,
        issues=issues,
        reason_qa=reason_qa,
        fair_lending=fair_lending,
        lda=lda,
        bisg=bisg,
        change_validation=change_validation,
    )


def compute_metrics(payloads: dict[str, Any]) -> dict[str, Any]:
    decisions = payloads["decisions"]
    scores = payloads["score_outputs"]
    reason_mappings = payloads["reason_mappings"]
    reason_outputs = payloads["reason_outputs"]
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
    reason_codes = count_by_key(reason_outputs, "reason_code")
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
            "generated_reason_output_count": len(reason_outputs),
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


def compute_reason_qa(payloads: dict[str, Any]) -> dict[str, Any]:
    decisions = payloads["decisions"]
    reason_mappings = payloads["reason_mappings"]
    reason_outputs = payloads["reason_outputs"]

    mappings_by_code = {
        record["reason_code"]: record
        for record in reason_mappings
    }
    outputs_by_decision: dict[str, list[dict[str, Any]]] = {}
    for output in reason_outputs:
        outputs_by_decision.setdefault(output["decision_id"], []).append(output)

    exceptions: list[dict[str, Any]] = []
    declined_decisions = [
        record for record in decisions if record["decision_outcome"] == "declined"
    ]
    for decision in declined_decisions:
        outputs = outputs_by_decision.get(decision["decision_id"], [])
        if not outputs:
            exceptions.append(
                build_reason_exception(
                    decision["decision_id"],
                    None,
                    "missing_reason_code",
                    "Declined decision has no generated adverse-action reason output.",
                )
            )
            continue
        for output in sorted(outputs, key=lambda item: item["reason_rank"]):
            mapping = mappings_by_code.get(output["reason_code"])
            if mapping is None:
                exceptions.append(
                    build_reason_exception(
                        decision["decision_id"],
                        output,
                        "unmapped_reason_code",
                        "Generated reason code is not present in the governed reason-code mapping.",
                    )
                )
                continue
            if output["driver_or_signal"] != mapping["driver_or_signal"]:
                exceptions.append(
                    build_reason_exception(
                        decision["decision_id"],
                        output,
                        "driver_mapping_mismatch",
                        "Generated reason driver does not match the governed mapping.",
                    )
                )
            if output["mapping_version"] != mapping["mapping_version"]:
                exceptions.append(
                    build_reason_exception(
                        decision["decision_id"],
                        output,
                        "mapping_version_mismatch",
                        "Generated reason mapping version does not match the governed mapping.",
                    )
                )
            if is_generic_reason_text(mapping["reason_text"]):
                exceptions.append(
                    build_reason_exception(
                        decision["decision_id"],
                        output,
                        "generic_reason_text",
                        "Mapped reason text is too generic for governance review.",
                    )
                )

    fidelity_context = build_reason_fidelity_context(
        payloads.get("reason_fidelity_policy"),
        payloads.get("notice_template"),
        payloads.get("reason_selection_methods"),
    )
    if fidelity_context is None or payloads.get("driver_contributions") is None:
        missing_inputs = []
        if payloads.get("driver_contributions") is None:
            missing_inputs.append("adverse-action-driver-contributions.json")
        if fidelity_context is None:
            missing_inputs.extend(
                name
                for name, value in (
                    ("reason-fidelity-policy.json", payloads.get("reason_fidelity_policy")),
                    ("adverse-action-notice-template.json", payloads.get("notice_template")),
                    ("reason-selection-methods.json", payloads.get("reason_selection_methods")),
                )
                if value is None
            )
        fidelity = {
            "status": "not_run_missing_source_to_notice_inputs",
            "missing_inputs": missing_inputs,
            "exception_count": 0,
            "exception_types": [],
            "rendered_notice_fidelity": {
                "status": "not_run_missing_source_to_notice_inputs",
                "missing_inputs": ["source-to-reason provenance inputs"],
                "exception_count": 0,
                "exception_types": [],
            },
        }
    else:
        fidelity_exceptions = compute_reason_fidelity_exceptions(
            decisions=decisions,
            reason_mappings=reason_mappings,
            reason_outputs=reason_outputs,
            driver_contributions=payloads["driver_contributions"],
            fidelity_context=fidelity_context,
        )
        exceptions.extend(fidelity_exceptions)
        rendered_notices = payloads.get("rendered_notices")
        if rendered_notices is None:
            rendered_notice_fidelity = {
                "status": "not_run_missing_rendered_notice_input",
                "missing_inputs": ["rendered-adverse-action-notices.json"],
                "exception_count": 0,
                "exception_types": [],
            }
        else:
            rendered_notice_exceptions = compute_rendered_notice_fidelity_exceptions(
                decisions=decisions,
                reason_outputs=reason_outputs,
                rendered_notices=rendered_notices,
                fidelity_context=fidelity_context,
            )
            exceptions.extend(rendered_notice_exceptions)
            rendered_notice_fidelity = {
                "status": "ran_synthetic_rendered_notice_controls",
                "exception_count": len(rendered_notice_exceptions),
                "exception_types": sorted(
                    {exception["exception_type"] for exception in rendered_notice_exceptions}
                ),
            }
        all_fidelity_exceptions = fidelity_exceptions + (
            rendered_notice_exceptions if rendered_notices is not None else []
        )
        fidelity = {
            "status": (
                "ran_synthetic_source_to_rendered_notice_controls"
                if rendered_notices is not None
                else "ran_synthetic_source_to_reason_controls"
            ),
            "policy_id": fidelity_context.policy["policy_id"],
            "policy_version": fidelity_context.policy["policy_version"],
            "notice_template_id": fidelity_context.notice_template["template_id"],
            "notice_template_version": fidelity_context.notice_template["template_version"],
            "selection_method_components": sorted(fidelity_context.methods_by_component),
            "exception_count": len(all_fidelity_exceptions),
            "exception_types": sorted(
                {exception["exception_type"] for exception in all_fidelity_exceptions}
            ),
            "rendered_notice_fidelity": rendered_notice_fidelity,
        }

    reason_code_counts = count_by_key(reason_outputs, "reason_code") if reason_outputs else {}
    return {
        "label": "qa_screening_only_not_legal_conclusion",
        "declined_decision_count": len(declined_decisions),
        "reason_output_count": len(reason_outputs),
        "exception_count": len(exceptions),
        "exceptions": exceptions,
        "source_to_notice_fidelity": fidelity,
        "stability": {
            "mapping_versions": sorted({record["mapping_version"] for record in reason_mappings}),
            "reason_code_distribution": to_share_map(reason_code_counts, len(reason_outputs)),
            "mapped_reason_code_count": len(reason_mappings),
            "generated_reason_code_count": len(reason_code_counts),
        },
    }


def compute_reason_fidelity_exceptions(
    decisions: list[dict[str, Any]],
    reason_mappings: list[dict[str, Any]],
    reason_outputs: list[dict[str, Any]],
    driver_contributions: list[dict[str, Any]],
    fidelity_context: Any,
) -> list[dict[str, Any]]:
    """Test the synthetic source-driver-to-notice provenance chain.

    These are deterministic review triggers.  They do not determine whether a
    creditor's disclosures comply with any legal requirement.
    """
    mappings_by_code = {mapping["reason_code"]: mapping for mapping in reason_mappings}
    outputs_by_decision = group_reason_outputs_by_decision(reason_outputs)
    contributions_by_decision = {
        record.get("decision_id"): record.get("contributions", [])
        for record in driver_contributions
        if isinstance(record, dict) and record.get("decision_id")
    }
    exceptions: list[dict[str, Any]] = []

    for decision in decisions:
        if decision["decision_outcome"] != "declined":
            continue
        decision_id = decision["decision_id"]
        decision_date = decision["application_date"]
        decision_component = decision.get("decision_component")
        policy_version = decision.get("underwriting", {}).get("policy_version")
        outputs = outputs_by_decision.get(decision_id, [])
        contributions = contributions_by_decision.get(decision_id, [])

        if not isinstance(decision_component, str) or not decision_component:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "missing_decision_component",
                    "Declined decision has no recorded final decision component for source-to-notice QA.",
                )
            )
            continue
        if not isinstance(policy_version, str) or not policy_version:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "missing_policy_version",
                    "Declined decision has no recorded underwriting policy version for source-to-notice QA.",
                )
            )
        if decision_component not in fidelity_context.methods_by_component:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "unconfigured_selection_method",
                    "No governed reason-selection method is configured for the final decision component.",
                )
            )
            continue
        if not contributions:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "missing_driver_contributions",
                    "Declined decision has no source driver contributions for source-to-notice QA.",
                )
            )
            continue

        source_components = source_components_for_decision(decision)
        if not source_components:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "missing_combined_failed_components",
                    "Combined decision has no valid recorded failed source components for reason QA.",
                )
            )
            continue

        ranked = rank_decision_contributions(contributions, decision)
        source_rank_by_identity = {
            (contribution["decision_component"], contribution["driver_or_signal"]): rank
            for rank, contribution in enumerate(ranked, start=1)
        }
        method = fidelity_context.methods_by_component[decision_component]
        output_sources = {
            (
                output.get("source_decision_component", decision_component),
                output.get("driver_or_signal"),
            )
            for output in outputs
        }
        principal_sources = [
            (contribution["decision_component"], contribution["driver_or_signal"])
            for contribution in ranked[: fidelity_context.principal_driver_rank_limit]
            if contribution["driver_or_signal"]
            in {mapping["driver_or_signal"] for mapping in reason_mappings}
        ]
        omitted = [source for source in principal_sources if source not in output_sources]
        if omitted:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "principal_driver_omitted",
                    "A governed principal source driver is absent from the recorded reason outputs: "
                    + ", ".join(f"{component}:{driver}" for component, driver in omitted),
                )
            )

        for output in outputs:
            required_fields = REQUIRED_REASON_FIDELITY_FIELDS
            if decision_component != "combined":
                required_fields = tuple(
                    field for field in required_fields if field != "source_decision_component"
                )
            missing_fields = [
                field
                for field in required_fields
                if output.get(field) in (None, "")
            ]
            if missing_fields:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "missing_reason_fidelity_fields",
                        "Reason output is missing source-to-notice fields: "
                        + ", ".join(missing_fields),
                    )
                )
                continue

            mapping = mappings_by_code.get(output["reason_code"])
            if mapping is not None:
                if output["mapping_id"] != mapping.get("mapping_id"):
                    exceptions.append(
                        build_reason_exception(
                            decision_id,
                            output,
                            "mapping_identifier_mismatch",
                            "Reason output mapping identifier does not match the governed mapping.",
                        )
                    )
                if output["mapping_effective_date"] != mapping.get("effective_date"):
                    exceptions.append(
                        build_reason_exception(
                            decision_id,
                            output,
                            "mapping_effective_date_mismatch",
                            "Reason output does not pin the effective date of its governed mapping.",
                        )
                    )
                if not is_active_on_date(
                    mapping.get("effective_date"), mapping.get("retired_date"), decision_date
                ):
                    exceptions.append(
                        build_reason_exception(
                            decision_id,
                            output,
                            "mapping_not_effective_on_decision_date",
                            "Reason output references a mapping that was not active on the decision date.",
                        )
                    )
                if normalize_reason_text(output["disclosed_reason_text"]) != normalize_reason_text(
                    mapping["reason_text"]
                ):
                    exceptions.append(
                        build_reason_exception(
                            decision_id,
                            output,
                            "notice_text_mapping_mismatch",
                            "Recorded notice text does not match the governed reason text for its mapped driver.",
                        )
                    )

            template = fidelity_context.notice_template
            if (
                output["notice_template_id"] != template["template_id"]
                or output["notice_template_version"] != template["template_version"]
            ):
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "notice_template_version_mismatch",
                        "Reason output does not pin the governed notice-template identifier and version.",
                    )
                )
            if not is_active_on_date(
                template["effective_date"], template["retired_date"], decision_date
            ):
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "notice_template_not_effective_on_decision_date",
                        "Reason output uses a notice template that was not active on the decision date.",
                    )
                )
            if output["decision_component"] != decision_component:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "decision_component_mismatch",
                        "Reason output component does not match the recorded final decision component.",
                    )
                )
            if output["policy_version"] != policy_version:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "policy_version_mismatch",
                        "Reason output does not pin the underwriting policy version used for the decision.",
                    )
                )
            if (
                output["selection_method_id"] != method["selection_method_id"]
                or output["selection_method_version"] != method["selection_method_version"]
            ):
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "selection_method_version_mismatch",
                        "Reason output selection-method identifier or version does not match its decision component.",
                    )
                )

            source_component = output.get("source_decision_component", decision_component)
            if source_component not in source_components:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "source_decision_component_mismatch",
                        "Reason output source component is not a recorded failed component for the decision.",
                    )
                )
                continue
            actual_source_rank = source_rank_by_identity.get(
                (source_component, output["driver_or_signal"])
            )
            if actual_source_rank is None:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "reason_not_in_actual_contributors",
                        "Reason output driver is not an adverse source driver for the recorded source component.",
                    )
                )
            elif output["source_driver_rank"] != actual_source_rank:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "source_driver_rank_mismatch",
                        "Reason output source-driver rank does not match deterministic source contribution ranking.",
                    )
                )
    return exceptions


def compute_rendered_notice_fidelity_exceptions(
    decisions: list[dict[str, Any]],
    reason_outputs: list[dict[str, Any]],
    rendered_notices: list[dict[str, Any]],
    fidelity_context: Any,
) -> list[dict[str, Any]]:
    """Reconcile synthetic rendered reason segments to recorded reason outputs.

    The check verifies the visible synthetic notice record, not merely the
    stored reason-text field.  It remains a deterministic review trigger and
    does not assess readability or legal sufficiency in a real notice.
    """
    notices_by_decision = {notice["decision_id"]: notice for notice in rendered_notices}
    outputs_by_decision = group_reason_outputs_by_decision(reason_outputs)
    template = fidelity_context.notice_template
    exceptions: list[dict[str, Any]] = []
    for decision in decisions:
        if decision["decision_outcome"] != "declined":
            continue
        decision_id = decision["decision_id"]
        outputs = outputs_by_decision.get(decision_id, [])
        if not outputs:
            continue
        notice = notices_by_decision.get(decision_id)
        if notice is None:
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "missing_rendered_notice",
                    "Declined decision with recorded reasons has no synthetic rendered notice record.",
                )
            )
            continue
        if (
            notice["notice_template_id"] != template["template_id"]
            or notice["notice_template_version"] != template["template_version"]
        ):
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "rendered_notice_template_version_mismatch",
                    "Rendered notice does not use the governed notice-template identifier and version.",
                )
            )
        segments = {
            segment["reason_output_id"]: segment
            for segment in notice["rendered_reason_segments"]
        }
        output_ids = {output["reason_output_id"] for output in outputs}
        for output in outputs:
            segment = segments.get(output["reason_output_id"])
            if segment is None:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "missing_rendered_reason_segment",
                        "Recorded reason output is absent from the synthetic rendered notice.",
                    )
                )
                continue
            if segment["reason_code"] != output["reason_code"]:
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "rendered_notice_reason_code_mismatch",
                        "Rendered notice reason-code segment does not match its recorded reason output.",
                    )
                )
            if normalize_reason_text(segment["rendered_reason_text"]) != normalize_reason_text(
                output["disclosed_reason_text"]
            ):
                exceptions.append(
                    build_reason_exception(
                        decision_id,
                        output,
                        "rendered_notice_text_mismatch",
                        "Rendered notice reason text does not match the recorded reason output.",
                    )
                )
        for reason_output_id in sorted(set(segments) - output_ids):
            exceptions.append(
                build_reason_exception(
                    decision_id,
                    None,
                    "rendered_notice_unmatched_reason_segment",
                    "Rendered notice contains a reason segment without a recorded reason output: "
                    + reason_output_id,
                )
            )
    return exceptions


def group_reason_outputs_by_decision(
    reason_outputs: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    outputs_by_decision: dict[str, list[dict[str, Any]]] = {}
    for output in reason_outputs:
        outputs_by_decision.setdefault(output["decision_id"], []).append(output)
    return outputs_by_decision


def compute_fair_lending_screening(payloads: dict[str, Any]) -> dict[str, Any]:
    decisions = payloads["decisions"]
    reason_outputs = payloads["reason_outputs"]
    config = payloads["fair_lending_config"]

    group_results: dict[str, dict[str, Any]] = {}
    for group_config in config["comparison_groups"]:
        group_name = group_config["group_name"]
        groups = build_fair_lending_group_metrics(
            decisions,
            reason_outputs,
            group_config["source"],
            group_config["field"],
        )
        group_results[group_name] = {
            "source": group_config["source"],
            "field": group_config["field"],
            "groups": groups,
            "summary": summarize_fair_lending_groups(groups),
            "significance": compute_group_significance(groups),
        }

    findings: list[dict[str, Any]] = []
    for screen in config["screens"]:
        metric_name = screen["metric_name"]
        for group_name, group_result in group_results.items():
            observed_value = group_result["summary"].get(metric_name)
            if observed_value is None:
                continue
            if threshold_breached(
                float(observed_value),
                screen["comparison_rule"],
                float(screen["threshold_value"]),
            ):
                finding_index = len(findings) + 1
                finding = {
                    "finding_id": f"flf-{finding_index:04d}",
                    "screen_name": screen["screen_name"],
                    "metric_name": metric_name,
                    "comparison_group": group_name,
                    "observed_value": round(float(observed_value), 4),
                    "threshold_value": float(screen["threshold_value"]),
                    "comparison_rule": screen["comparison_rule"],
                    "severity": screen["severity"],
                    "owner": screen["escalation_owner"],
                    "review_trigger": "deeper_fair_lending_review",
                    "result_type": "screening_only_not_legal_conclusion",
                }
                significance = group_result["significance"].get(
                    significance_key_for_metric(metric_name)
                )
                if significance is not None:
                    finding["statistical_significance"] = significance
                findings.append(finding)

    return {
        "label": "fair_lending_screening_only_not_legal_conclusion",
        "screening_config_id": config["screening_config_id"],
        "comparison_group_count": len(config["comparison_groups"]),
        "screen_count": len(config["screens"]),
        "finding_count": len(findings),
        "group_results": group_results,
        "findings": findings,
        "limitations": [
            "Synthetic data only.",
            "No protected-class labels are used.",
            "Screening findings are governance review triggers, not legal conclusions.",
            "Significance tests are unadjusted comparisons; no regression controls for legitimate credit factors.",
        ],
    }


def significance_key_for_metric(metric_name: str) -> str:
    if metric_name == "approval_rate_ratio":
        return "approval_rate"
    if metric_name == "override_rate_difference":
        return "override_rate"
    return metric_name


def compute_group_significance(groups: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Significance tests for the extreme-group gaps that drive the screens.

    Tests the lowest-rate group against the highest-rate group for approval
    rates (the pair behind ``approval_rate_ratio``) and for override rates
    (the pair behind ``override_rate_difference``). Reported values include
    effect size, test used, p-value, and sample-adequacy caveats.
    """
    if len(groups) < 2:
        return {}

    def extreme_pair(rate_key: str, count_key: str) -> dict[str, Any]:
        ordered = sorted(groups.items(), key=lambda item: item[1][rate_key])
        low_name, low = ordered[0]
        high_name, high = ordered[-1]
        return compare_group_proportions(
            label_a=low_name,
            successes_a=low[count_key],
            total_a=low["total"],
            label_b=high_name,
            successes_b=high[count_key],
            total_b=high["total"],
        )

    return {
        "approval_rate": extreme_pair("approval_rate", "approved"),
        "override_rate": extreme_pair("override_rate", "overrides"),
    }


def build_fair_lending_group_metrics(
    decisions: list[dict[str, Any]],
    reason_outputs: list[dict[str, Any]],
    source: str,
    field: str,
) -> dict[str, dict[str, Any]]:
    reason_outputs_by_decision: dict[str, list[dict[str, Any]]] = {}
    for output in reason_outputs:
        reason_outputs_by_decision.setdefault(output["decision_id"], []).append(output)

    groups: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        group_value = get_group_value(decision, source, field)
        entry = groups.setdefault(
            group_value,
            {
                "total": 0,
                "approved": 0,
                "overrides": 0,
                "reason_code_counts": {},
            },
        )
        entry["total"] += 1
        if decision["decision_outcome"] == "approved":
            entry["approved"] += 1
        if decision["override_flag"]:
            entry["overrides"] += 1
        for output in reason_outputs_by_decision.get(decision["decision_id"], []):
            counts = entry["reason_code_counts"]
            counts[output["reason_code"]] = counts.get(output["reason_code"], 0) + 1

    for entry in groups.values():
        reason_total = sum(entry["reason_code_counts"].values())
        entry["approval_rate"] = safe_rate(entry["approved"], entry["total"])
        entry["override_rate"] = safe_rate(entry["overrides"], entry["total"])
        entry["reason_code_concentration"] = (
            round(max(entry["reason_code_counts"].values()) / reason_total, 4)
            if reason_total
            else 0.0
        )
    return {key: groups[key] for key in sorted(groups)}


def get_group_value(decision: dict[str, Any], source: str, field: str) -> str:
    if source == "monitoring":
        return str(decision["monitoring"][field])
    return str(decision[field])


def summarize_fair_lending_groups(groups: dict[str, dict[str, Any]]) -> dict[str, float]:
    approval_rates = [entry["approval_rate"] for entry in groups.values()]
    override_rates = [entry["override_rate"] for entry in groups.values()]
    concentrations = [entry["reason_code_concentration"] for entry in groups.values()]
    max_approval_rate = max(approval_rates, default=0.0)
    min_approval_rate = min(approval_rates, default=0.0)
    return {
        "approval_rate_ratio": (
            round(min_approval_rate / max_approval_rate, 4)
            if max_approval_rate > 0
            else 1.0
        ),
        "override_rate_difference": round(max(override_rates, default=0.0) - min(override_rates, default=0.0), 4),
        "reason_code_concentration": max(concentrations, default=0.0),
    }


def build_reason_exception(
    decision_id: str,
    output: dict[str, Any] | None,
    exception_type: str,
    message: str,
) -> dict[str, Any]:
    return {
        "exception_id": f"rex-{decision_id}-{exception_type}",
        "decision_id": decision_id,
        "reason_output_id": output["reason_output_id"] if output else None,
        "reason_code": output["reason_code"] if output else None,
        "exception_type": exception_type,
        "message": message,
    }


def is_generic_reason_text(reason_text: str) -> bool:
    normalized = reason_text.strip().lower()
    generic_values = {
        "other",
        "insufficient information",
        "not applicable",
        "generic reason",
        "miscellaneous",
    }
    return normalized in generic_values or len(normalized.split()) < 3


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


def build_issue_register(
    breaches: list[dict[str, Any]],
    reason_exceptions: list[dict[str, Any]],
    fair_lending_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
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
    for exception in reason_exceptions:
        issue_index = len(issues) + 1
        issues.append(
            {
                "issue_id": f"iss-{issue_index:04d}",
                "linked_breach_ids": [],
                "linked_reason_exception_ids": [exception["exception_id"]],
                "summary": (
                    f"Reason QA exception for {exception['decision_id']}: "
                    f"{exception['exception_type']}."
                ),
                "status": "open",
                "owner": "Model Risk Governance",
                "due_date": "2026-06-30",
            }
        )
    for finding in fair_lending_findings:
        issue_index = len(issues) + 1
        issues.append(
            {
                "issue_id": f"iss-{issue_index:04d}",
                "linked_breach_ids": [],
                "linked_reason_exception_ids": [],
                "linked_fair_lending_finding_ids": [finding["finding_id"]],
                "summary": (
                    f"Fair-lending screening trigger for {finding['comparison_group']}: "
                    f"{finding['metric_name']} observed {finding['observed_value']}."
                ),
                "status": "open",
                "owner": finding["owner"],
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
    reason_qa: dict[str, Any],
    fair_lending: dict[str, Any],
    lda: dict[str, Any] | None = None,
    bisg: dict[str, Any] | None = None,
    change_validation: dict[str, Any] | None = None,
) -> Path:
    manifest = payloads["manifest"]
    evidence_dir = evidence_root / format_evidence_dir_name(
        dataset_dir.name,
        manifest["run_id"],
        manifest["created_at"],
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    output_files = [
        "manifest.json",
        "config_snapshot.json",
        "input_fingerprints.json",
        "model_record.json",
        "threshold_set.json",
        "metric_results.json",
        "breach_register.json",
        "reason_qa_results.json",
        "reason_stability_report.json",
        "fair_lending_screening_results.json",
        "fair_lending_escalation_register.json",
        "issue_register.json",
        "monitoring_report.md",
        "reviewer_notes.md",
        "reviewer_signoff.md",
    ]
    if lda is not None:
        output_files.insert(output_files.index("issue_register.json"), "lda_assessment_results.json")
    if bisg is not None:
        output_files.insert(output_files.index("issue_register.json"), "bisg_proxy_results.json")
    if change_validation is not None:
        insert_at = output_files.index("issue_register.json")
        output_files.insert(insert_at, "model_change_validation_results.json")
        output_files.insert(insert_at + 1, "model_change_validation_report.md")
    rendered_notice_fidelity = reason_qa["source_to_notice_fidelity"].get(
        "rendered_notice_fidelity", {}
    )
    if rendered_notice_fidelity.get("status") == "ran_synthetic_rendered_notice_controls":
        output_files.insert(output_files.index("issue_register.json"), "rendered_notice_qa_results.json")

    generated_manifest = {
        "record_type": "evidence_pack_manifest",
        "run_id": manifest["run_id"],
        "created_at": manifest["created_at"],
        "model_id": manifest["model_id"],
        "version_id": manifest["version_id"],
        "input_references": manifest["input_references"],
        "output_files": output_files,
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
    write_json(evidence_dir / "reason_qa_results.json", reason_qa)
    if rendered_notice_fidelity.get("status") == "ran_synthetic_rendered_notice_controls":
        write_json(evidence_dir / "rendered_notice_qa_results.json", rendered_notice_fidelity)
    write_json(evidence_dir / "reason_stability_report.json", reason_qa["stability"])
    write_json(evidence_dir / "fair_lending_screening_results.json", fair_lending)
    write_json(evidence_dir / "fair_lending_escalation_register.json", fair_lending["findings"])
    if lda is not None:
        write_json(evidence_dir / "lda_assessment_results.json", lda)
    if bisg is not None:
        write_json(evidence_dir / "bisg_proxy_results.json", bisg)
    if change_validation is not None:
        write_json(evidence_dir / "model_change_validation_results.json", change_validation)
        write_text(
            evidence_dir / "model_change_validation_report.md",
            render_change_validation_report(change_validation),
        )
    write_json(evidence_dir / "issue_register.json", issues)
    write_text(
        evidence_dir / "monitoring_report.md",
        render_monitoring_report(
            metrics, breaches, issues, reason_qa, fair_lending, lda, bisg, change_validation
        ),
    )
    write_text(
        evidence_dir / "reviewer_notes.md",
        render_reviewer_notes(fair_lending),
    )
    write_text(
        evidence_dir / "reviewer_signoff.md",
        render_reviewer_signoff(
            generated_manifest,
            breaches,
            reason_qa["exceptions"],
            fair_lending["findings"],
            change_validation,
        ),
    )
    return evidence_dir


def build_input_fingerprints(dataset_dir: Path) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for path in sorted(dataset_dir.glob("*.json")):
        fingerprints[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return fingerprints


def render_finding_significance(finding: dict[str, Any]) -> str:
    significance = finding.get("statistical_significance")
    if significance is None:
        return ""
    verdict = "significant" if significance["statistically_significant"] else "not significant"
    return (
        f"\n  Statistical test: {significance['test']} | p = {significance['p_value']} | "
        f"{verdict} at alpha {significance['alpha']}"
    )


def render_bisg_section(bisg: dict[str, Any] | None) -> str:
    if bisg is None:
        return ""
    finding_lines = (
        "\n".join(
            f"- {finding['proxy_group']} vs {finding['reference_group']}: "
            f"proxy-weighted approval rate {finding['proxy_weighted_approval_rate']} vs "
            f"{finding['reference_approval_rate']} (p = {finding['p_value']}, "
            f"sensitivity interval = "
            f"{finding.get('measurement_error_rate_difference_interval', {}).get('lower')} to "
            f"{finding.get('measurement_error_rate_difference_interval', {}).get('upper')})"
            for finding in bisg["findings"]
        )
        if bisg["findings"]
        else "- No sensitivity-robust adverse proxy-group approval-rate gaps were identified."
    )
    sensitivity = bisg.get("measurement_error_sensitivity", {})
    sensitivity_line = "- Measurement-error sensitivity: disabled\n"
    if sensitivity.get("enabled"):
        sensitivity_line = (
            f"- Measurement-error sensitivity: {sensitivity['method']} "
            f"(gate margin {sensitivity['finding_probability_error_margin']}, "
            f"grid {sensitivity['probability_error_margins']})\n"
        )
    return (
        "## BISG Proxy Screening\n\n"
        f"- Method: Bayesian Improved Surname Geocoding (`{bisg['config_id']}`)\n"
        f"- Decisions matched to demographic inputs: {bisg['matched_decision_count']} of {bisg['decision_count']}\n"
        f"- Reference group: {bisg['reference_group']} | alpha: {bisg['alpha']}\n"
        f"- Inference: {bisg['inference_method']} "
        f"({bisg['bootstrap']['draws']} draws, seed {bisg['bootstrap']['seed']}, "
        f"CI level {bisg['bootstrap']['ci_level']})\n"
        f"{sensitivity_line}"
        f"- Sensitivity-robust finding count: {bisg['finding_count']}\n"
        "- Result type: probabilistic proxy screening, not observed demographics or a legal conclusion\n\n"
        f"{finding_lines}\n\n"
    )


def render_lda_section(lda: dict[str, Any] | None) -> str:
    if lda is None:
        return ""
    baseline = lda["baseline"]
    alternative = lda["alternative"]
    comparison = lda["comparison"]
    return (
        "## Less-Discriminatory-Alternative Assessment\n\n"
        f"- Assessment ID: `{lda['assessment_id']}`\n"
        f"- Comparison group: {lda['group_source']}.{lda['group_field']}\n"
        f"- Baseline disparity ratio: {baseline['disparity']['approval_rate_ratio']} | "
        f"separation: {baseline['separation']['separation']}\n"
        f"- Alternative disparity ratio: {alternative['disparity']['approval_rate_ratio']} | "
        f"separation: {alternative['separation']['separation']}\n"
        f"- Disparity improvement: {comparison['disparity_improvement']} | "
        f"separation change: {comparison['separation_change']}\n"
        f"- Qualifying alternative identified: {lda['qualifying_alternative_identified']}\n"
        f"- Recommendation: {lda['recommendation']}\n"
        "- Result type: synthetic assessment trigger, not a legal conclusion\n\n"
    )


def render_change_validation_section(change_validation: dict[str, Any] | None) -> str:
    if change_validation is None:
        return ""
    summary = change_validation["summary"]
    categories = ", ".join(summary["change_categories"]) or "none"
    action_lines = "\n".join(f"- {action}" for action in summary["review_actions"])
    return (
        "## Model-Change Validation Review\n\n"
        f"- Change review ID: `{change_validation['change_review_id']}`\n"
        f"- Prior version: `{summary['prior_version_id']}` -> current version: `{summary['current_version_id']}`\n"
        f"- Threshold changes: {summary['threshold_change_count']} | "
        f"reason-code changes: {summary['reason_code_change_count']}\n"
        f"- Material change: {summary['material_change']}\n"
        f"- Change categories: {categories}\n"
        "- Result type: change-governance review triggers, not a legal conclusion\n\n"
        f"{action_lines}\n\n"
    )


def render_monitoring_report(
    metrics: dict[str, Any],
    breaches: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    reason_qa: dict[str, Any],
    fair_lending: dict[str, Any],
    lda: dict[str, Any] | None = None,
    bisg: dict[str, Any] | None = None,
    change_validation: dict[str, Any] | None = None,
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
    reason_exception_lines = (
        "\n".join(
            f"- {exception['decision_id']}: {exception['exception_type']} ({exception['message']})"
            for exception in reason_qa["exceptions"]
        )
        if reason_qa["exceptions"]
        else "- No reason QA exceptions were generated for this run."
    )
    fidelity = reason_qa["source_to_notice_fidelity"]
    rendered_notice_fidelity = fidelity.get("rendered_notice_fidelity", {})
    rendered_notice_status = rendered_notice_fidelity.get("status", "not_run")
    rendered_notice_exception_count = rendered_notice_fidelity.get("exception_count", 0)
    fair_lending_lines = (
        "\n".join(
            f"- {finding['comparison_group']}: {finding['metric_name']} observed {finding['observed_value']} "
            f"against threshold {finding['threshold_value']} ({finding['severity']}, owner: {finding['owner']})"
            + render_finding_significance(finding)
            for finding in fair_lending["findings"]
        )
        if fair_lending["findings"]
        else "- No fair-lending screening findings were generated for this run."
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
        "## Adverse-Action Reason QA\n\n"
        f"- Declined decisions reviewed: {reason_qa['declined_decision_count']}\n"
        f"- Generated reason outputs reviewed: {reason_qa['reason_output_count']}\n"
        f"- QA exception count: {reason_qa['exception_count']}\n"
        f"- Source-to-notice control status: `{fidelity['status']}`\n"
        f"- Rendered-notice control status: `{rendered_notice_status}` "
        f"({rendered_notice_exception_count} exception(s))\n"
        "- Result type: screening only, not a legal conclusion\n\n"
        f"{reason_exception_lines}\n\n"
        "## Fair-Lending Screening\n\n"
        f"- Comparison groups reviewed: {fair_lending['comparison_group_count']}\n"
        f"- Screening rules applied: {fair_lending['screen_count']}\n"
        f"- Screening finding count: {fair_lending['finding_count']}\n"
        "- Result type: screening only, not a legal conclusion\n\n"
        f"{fair_lending_lines}\n\n"
        f"{render_bisg_section(bisg)}"
        f"{render_lda_section(lda)}"
        f"{render_change_validation_section(change_validation)}"
        "## Threshold Breaches\n\n"
        f"{breach_lines}\n\n"
        "## Issue Register\n\n"
        f"{issue_lines}\n"
    )


def render_reviewer_signoff(
    manifest: dict[str, Any],
    breaches: list[dict[str, Any]],
    reason_exceptions: list[dict[str, Any]],
    fair_lending_findings: list[dict[str, Any]],
    change_validation: dict[str, Any] | None = None,
) -> str:
    review_state = (
        "Escalation recommended"
        if breaches or reason_exceptions or fair_lending_findings
        else "No escalation required in demo run"
    )
    return (
        "# Reviewer Signoff\n\n"
        "This artifact supports governance workflow demonstration only.\n\n"
        f"- Run ID: `{manifest['run_id']}`\n"
        f"- Model ID: `{manifest['model_id']}`\n"
        f"- Version ID: `{manifest['version_id']}`\n"
        f"- Reviewer status: `{manifest['reviewer_status']}`\n"
        f"- Review summary: {review_state}\n\n"
        f"{render_change_validation_signoff_block(change_validation)}"
        "Reviewer: ____________________\n\n"
        "Date: ____________________\n"
    )


def render_change_validation_signoff_block(change_validation: dict[str, Any] | None) -> str:
    if change_validation is None:
        return ""
    signoff = change_validation["reviewer_signoff"]
    requirement_lines = "\n".join(
        f"- {item}" for item in signoff["required_before_promotion"]
    )
    return (
        "## Model-Change Validation Signoff\n\n"
        f"- Prior version: `{signoff['prior_version_id']}` -> current version: `{signoff['current_version_id']}`\n"
        f"- Evidence pack run: `{signoff['evidence_pack_run_id']}`\n"
        f"- Validation owner: {signoff['validation_owner']}\n"
        f"- Promotion gate: `{signoff['promotion_gate']}`\n"
        f"- Material change: {signoff['material_change']}\n"
        f"- Validation status: `{signoff['validation_status']}`\n\n"
        "Required before promotion to active:\n\n"
        f"{requirement_lines}\n\n"
        "Independent validation reviewer: ____________________\n\n"
        "Validation signoff date: ____________________\n\n"
    )


def render_reviewer_notes(fair_lending: dict[str, Any]) -> str:
    finding_lines = (
        "\n".join(
            f"- {finding['finding_id']}: review {finding['metric_name']} for {finding['comparison_group']} "
            f"with owner {finding['owner']}."
            for finding in fair_lending["findings"]
        )
        if fair_lending["findings"]
        else "- No fair-lending screening findings require reviewer notes."
    )
    return (
        "# Reviewer Notes\n\n"
        "This artifact supports synthetic governance review only. Fair-lending screening findings are review triggers, not legal conclusions.\n\n"
        "## Fair-Lending Review Notes\n\n"
        f"{finding_lines}\n\n"
        "Reviewer notes:\n\n"
        "- ____________________\n"
    )


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2) + "\n")


def write_text(path: Path, contents: str) -> None:
    """Write UTF-8 artifacts with LF endings on every operating system."""
    path.write_bytes(contents.encode("utf-8"))


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
