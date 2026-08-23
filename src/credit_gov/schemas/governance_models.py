"""Typed records for model-risk, explainability, validation, and monitoring governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import (
    BaseRecord,
    require_non_empty_string,
    require_string_list,
    require_type,
)


RISK_RANK = {"immaterial": 0, "low": 1, "moderate": 2, "high": 3}
RIGOR_RANK = {"limited": 1, "standard": 2, "heightened": 3}


def require_boolean(value: Any, field: str) -> bool:
    require_type(value, bool, field)
    return value


@dataclass(slots=True)
class ModelRiskProfile(BaseRecord):
    risk_profile_id: str
    model_id: str
    version_id: str
    assessment_date: str
    model_purpose: str
    inherent_risk: str
    model_exposure: str
    model_materiality: str
    materiality_rationale: str
    complexity_summary: str
    data_constraints: list[str]
    aggregate_dependencies: list[str]
    validation_rigor: str
    monitoring_rigor: str
    owner: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelRiskProfile":
        materiality = require_non_empty_string(
            payload.get("model_materiality"), "model_materiality", 3
        )
        validation_rigor = require_non_empty_string(
            payload.get("validation_rigor"), "validation_rigor", 3
        )
        monitoring_rigor = require_non_empty_string(
            payload.get("monitoring_rigor"), "monitoring_rigor", 3
        )
        minimum_rigor = 3 if materiality == "high" else 2 if materiality == "moderate" else 1
        if RIGOR_RANK.get(validation_rigor, 0) < minimum_rigor:
            raise ValueError(
                "validation_rigor is not commensurate with model_materiality"
            )
        if RIGOR_RANK.get(monitoring_rigor, 0) < minimum_rigor:
            raise ValueError(
                "monitoring_rigor is not commensurate with model_materiality"
            )
        return cls(
            **cls._base_kwargs(payload),
            risk_profile_id=require_non_empty_string(
                payload.get("risk_profile_id"), "risk_profile_id", 3
            ),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(
                payload.get("version_id"), "version_id", 3
            ),
            assessment_date=require_non_empty_string(
                payload.get("assessment_date"), "assessment_date", 10
            ),
            model_purpose=require_non_empty_string(
                payload.get("model_purpose"), "model_purpose", 10
            ),
            inherent_risk=require_non_empty_string(
                payload.get("inherent_risk"), "inherent_risk", 3
            ),
            model_exposure=require_non_empty_string(
                payload.get("model_exposure"), "model_exposure", 3
            ),
            model_materiality=materiality,
            materiality_rationale=require_non_empty_string(
                payload.get("materiality_rationale"), "materiality_rationale", 20
            ),
            complexity_summary=require_non_empty_string(
                payload.get("complexity_summary"), "complexity_summary", 10
            ),
            data_constraints=require_string_list(
                payload.get("data_constraints"), "data_constraints"
            ),
            aggregate_dependencies=require_string_list(
                payload.get("aggregate_dependencies"), "aggregate_dependencies"
            ),
            validation_rigor=validation_rigor,
            monitoring_rigor=monitoring_rigor,
            owner=require_non_empty_string(payload.get("owner"), "owner", 3),
            result_type=require_non_empty_string(
                payload.get("result_type"), "result_type", 10
            ),
        )


@dataclass(slots=True)
class ReferencePopulation:
    population_id: str
    description: str
    selection_rationale: str
    data_boundary: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "ReferencePopulation":
        require_type(payload, dict, field)
        return cls(
            population_id=require_non_empty_string(
                payload.get("population_id"), f"{field}.population_id", 3
            ),
            description=require_non_empty_string(
                payload.get("description"), f"{field}.description", 10
            ),
            selection_rationale=require_non_empty_string(
                payload.get("selection_rationale"), f"{field}.selection_rationale", 15
            ),
            data_boundary=require_non_empty_string(
                payload.get("data_boundary"), f"{field}.data_boundary", 10
            ),
        )


@dataclass(slots=True)
class ExplainabilityMethodRecord(BaseRecord):
    explainability_method_id: str
    model_id: str
    version_id: str
    method_name: str
    method_version: str
    method_family: str
    use_cases: list[str]
    explanation_scope: str
    implementation_reference: str
    reference_population: ReferencePopulation
    correlation_assumptions: list[str]
    aggregation_rationale: str
    directionality_review: str
    known_limitations: list[str]
    validation_test_references: list[str]
    owner: str
    status: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExplainabilityMethodRecord":
        return cls(
            **cls._base_kwargs(payload),
            explainability_method_id=require_non_empty_string(
                payload.get("explainability_method_id"), "explainability_method_id", 3
            ),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(
                payload.get("version_id"), "version_id", 3
            ),
            method_name=require_non_empty_string(
                payload.get("method_name"), "method_name", 3
            ),
            method_version=require_non_empty_string(
                payload.get("method_version"), "method_version", 3
            ),
            method_family=require_non_empty_string(
                payload.get("method_family"), "method_family", 3
            ),
            use_cases=require_string_list(payload.get("use_cases"), "use_cases"),
            explanation_scope=require_non_empty_string(
                payload.get("explanation_scope"), "explanation_scope", 3
            ),
            implementation_reference=require_non_empty_string(
                payload.get("implementation_reference"), "implementation_reference", 5
            ),
            reference_population=ReferencePopulation.from_dict(
                payload.get("reference_population"), "reference_population"
            ),
            correlation_assumptions=require_string_list(
                payload.get("correlation_assumptions"), "correlation_assumptions"
            ),
            aggregation_rationale=require_non_empty_string(
                payload.get("aggregation_rationale"), "aggregation_rationale", 10
            ),
            directionality_review=require_non_empty_string(
                payload.get("directionality_review"), "directionality_review", 3
            ),
            known_limitations=require_string_list(
                payload.get("known_limitations"), "known_limitations"
            ),
            validation_test_references=require_string_list(
                payload.get("validation_test_references"),
                "validation_test_references",
            ),
            owner=require_non_empty_string(payload.get("owner"), "owner", 3),
            status=require_non_empty_string(payload.get("status"), "status", 3),
            result_type=require_non_empty_string(
                payload.get("result_type"), "result_type", 10
            ),
        )


@dataclass(slots=True)
class ValidationFinding:
    finding_id: str
    severity: str
    summary: str
    status: str
    owner: str
    target_date: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "ValidationFinding":
        require_type(payload, dict, field)
        return cls(
            finding_id=require_non_empty_string(
                payload.get("finding_id"), f"{field}.finding_id", 3
            ),
            severity=require_non_empty_string(
                payload.get("severity"), f"{field}.severity", 3
            ),
            summary=require_non_empty_string(
                payload.get("summary"), f"{field}.summary", 10
            ),
            status=require_non_empty_string(payload.get("status"), f"{field}.status", 3),
            owner=require_non_empty_string(payload.get("owner"), f"{field}.owner", 3),
            target_date=require_non_empty_string(
                payload.get("target_date"), f"{field}.target_date", 10
            ),
        )


@dataclass(slots=True)
class ModelValidationRecord(BaseRecord):
    validation_id: str
    model_id: str
    version_id: str
    validation_date: str
    validation_scope: list[str]
    validator_role: str
    independence_status: str
    reviewer_identity: str
    evidence_references: list[str]
    explainability_method_ids: list[str]
    findings: list[ValidationFinding]
    limitations: list[str]
    overall_disposition: str
    promotion_allowed: bool
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelValidationRecord":
        finding_payloads = payload.get("findings")
        require_type(finding_payloads, list, "findings")
        findings = [
            ValidationFinding.from_dict(item, f"findings[{index}]")
            for index, item in enumerate(finding_payloads)
        ]
        if not findings:
            raise ValueError("findings must contain at least one item")
        finding_ids = [finding.finding_id for finding in findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("findings.finding_id must be unique")

        independence_status = require_non_empty_string(
            payload.get("independence_status"), "independence_status", 3
        )
        disposition = require_non_empty_string(
            payload.get("overall_disposition"), "overall_disposition", 3
        )
        promotion_allowed = require_boolean(
            payload.get("promotion_allowed"), "promotion_allowed"
        )
        independent = independence_status in {
            "independent_internal",
            "independent_external",
        }
        if disposition in {"approved", "approved_with_conditions"} and not independent:
            raise ValueError(
                "an approved validation disposition requires an independent validator"
            )
        if promotion_allowed:
            if not independent or disposition not in {
                "approved",
                "approved_with_conditions",
            }:
                raise ValueError(
                    "promotion_allowed requires independent validation and an approved disposition"
                )
            unresolved_severe = [
                finding.finding_id
                for finding in findings
                if finding.status == "open" and finding.severity in {"high", "critical"}
            ]
            if unresolved_severe:
                raise ValueError(
                    "promotion_allowed cannot be true with open high or critical findings: "
                    + ", ".join(sorted(unresolved_severe))
                )
        return cls(
            **cls._base_kwargs(payload),
            validation_id=require_non_empty_string(
                payload.get("validation_id"), "validation_id", 3
            ),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(
                payload.get("version_id"), "version_id", 3
            ),
            validation_date=require_non_empty_string(
                payload.get("validation_date"), "validation_date", 10
            ),
            validation_scope=require_string_list(
                payload.get("validation_scope"), "validation_scope"
            ),
            validator_role=require_non_empty_string(
                payload.get("validator_role"), "validator_role", 3
            ),
            independence_status=independence_status,
            reviewer_identity=require_non_empty_string(
                payload.get("reviewer_identity"), "reviewer_identity", 3
            ),
            evidence_references=require_string_list(
                payload.get("evidence_references"), "evidence_references"
            ),
            explainability_method_ids=require_string_list(
                payload.get("explainability_method_ids"),
                "explainability_method_ids",
            ),
            findings=findings,
            limitations=require_string_list(payload.get("limitations"), "limitations"),
            overall_disposition=disposition,
            promotion_allowed=promotion_allowed,
            result_type=require_non_empty_string(
                payload.get("result_type"), "result_type", 10
            ),
        )


@dataclass(slots=True)
class MonitoringMetric:
    metric_name: str
    purpose: str
    evidence_source: str
    threshold_reference: str
    action_on_breach: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "MonitoringMetric":
        require_type(payload, dict, field)
        return cls(
            metric_name=require_non_empty_string(
                payload.get("metric_name"), f"{field}.metric_name", 3
            ),
            purpose=require_non_empty_string(
                payload.get("purpose"), f"{field}.purpose", 10
            ),
            evidence_source=require_non_empty_string(
                payload.get("evidence_source"), f"{field}.evidence_source", 3
            ),
            threshold_reference=require_non_empty_string(
                payload.get("threshold_reference"), f"{field}.threshold_reference", 3
            ),
            action_on_breach=require_non_empty_string(
                payload.get("action_on_breach"), f"{field}.action_on_breach", 10
            ),
        )


@dataclass(slots=True)
class ModelMonitoringPlan(BaseRecord):
    monitoring_plan_id: str
    model_id: str
    version_id: str
    risk_profile_id: str
    validation_id: str
    threshold_set_id: str
    plan_version: str
    effective_date: str
    review_cadence: str
    explainability_method_ids: list[str]
    metrics: list[MonitoringMetric]
    limitation_review_items: list[str]
    change_triggers: list[str]
    reason_monitoring_scope: str
    escalation_owner: str
    review_owner: str
    status: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelMonitoringPlan":
        metric_payloads = payload.get("metrics")
        require_type(metric_payloads, list, "metrics")
        metrics = [
            MonitoringMetric.from_dict(item, f"metrics[{index}]")
            for index, item in enumerate(metric_payloads)
        ]
        if not metrics:
            raise ValueError("metrics must contain at least one item")
        metric_names = [metric.metric_name for metric in metrics]
        if len(metric_names) != len(set(metric_names)):
            raise ValueError("metrics.metric_name must be unique")
        return cls(
            **cls._base_kwargs(payload),
            monitoring_plan_id=require_non_empty_string(
                payload.get("monitoring_plan_id"), "monitoring_plan_id", 3
            ),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(
                payload.get("version_id"), "version_id", 3
            ),
            risk_profile_id=require_non_empty_string(
                payload.get("risk_profile_id"), "risk_profile_id", 3
            ),
            validation_id=require_non_empty_string(
                payload.get("validation_id"), "validation_id", 3
            ),
            threshold_set_id=require_non_empty_string(
                payload.get("threshold_set_id"), "threshold_set_id", 3
            ),
            plan_version=require_non_empty_string(
                payload.get("plan_version"), "plan_version", 3
            ),
            effective_date=require_non_empty_string(
                payload.get("effective_date"), "effective_date", 10
            ),
            review_cadence=require_non_empty_string(
                payload.get("review_cadence"), "review_cadence", 3
            ),
            explainability_method_ids=require_string_list(
                payload.get("explainability_method_ids"),
                "explainability_method_ids",
            ),
            metrics=metrics,
            limitation_review_items=require_string_list(
                payload.get("limitation_review_items"), "limitation_review_items"
            ),
            change_triggers=require_string_list(
                payload.get("change_triggers"), "change_triggers"
            ),
            reason_monitoring_scope=require_non_empty_string(
                payload.get("reason_monitoring_scope"), "reason_monitoring_scope", 10
            ),
            escalation_owner=require_non_empty_string(
                payload.get("escalation_owner"), "escalation_owner", 3
            ),
            review_owner=require_non_empty_string(
                payload.get("review_owner"), "review_owner", 3
            ),
            status=require_non_empty_string(payload.get("status"), "status", 3),
            result_type=require_non_empty_string(
                payload.get("result_type"), "result_type", 10
            ),
        )
