"""Typed record models for Phase 1 governance inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def require_type(value: Any, expected_type: type | tuple[type, ...], field: str) -> None:
    if not isinstance(value, expected_type):
        names = (
            ", ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise TypeError(f"{field} must be of type {names}")


def require_non_empty_string(value: Any, field: str, minimum: int = 1) -> str:
    require_type(value, str, field)
    cleaned = value.strip()
    if len(cleaned) < minimum:
        raise ValueError(f"{field} must be at least {minimum} characters")
    return cleaned


def require_string_list(value: Any, field: str) -> list[str]:
    require_type(value, list, field)
    cleaned: list[str] = []
    for index, item in enumerate(value):
        cleaned.append(require_non_empty_string(item, f"{field}[{index}]"))
    if not cleaned:
        raise ValueError(f"{field} must contain at least one item")
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{field} must not contain duplicates")
    return cleaned


@dataclass(slots=True)
class BaseRecord:
    record_type: str

    @classmethod
    def _base_kwargs(cls, payload: dict[str, Any]) -> dict[str, Any]:
        return {"record_type": require_non_empty_string(payload.get("record_type"), "record_type")}


@dataclass(slots=True)
class ModelRegistryRecord(BaseRecord):
    model_id: str
    model_name: str
    business_owner: str
    technical_owner: str
    intended_use: str
    target_population: str
    status: str
    monitoring_only_fields: list[str]
    underwriting_fields: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelRegistryRecord":
        monitoring_only_fields = require_string_list(
            payload.get("monitoring_only_fields"), "monitoring_only_fields"
        )
        underwriting_fields = require_string_list(
            payload.get("underwriting_fields"), "underwriting_fields"
        )
        overlap = sorted(set(monitoring_only_fields) & set(underwriting_fields))
        if overlap:
            raise ValueError(
                "monitoring_only_fields and underwriting_fields must be separated: "
                + ", ".join(overlap)
            )
        return cls(
            **cls._base_kwargs(payload),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            model_name=require_non_empty_string(payload.get("model_name"), "model_name", 3),
            business_owner=require_non_empty_string(payload.get("business_owner"), "business_owner", 3),
            technical_owner=require_non_empty_string(payload.get("technical_owner"), "technical_owner", 3),
            intended_use=require_non_empty_string(payload.get("intended_use"), "intended_use", 10),
            target_population=require_non_empty_string(payload.get("target_population"), "target_population", 5),
            status=require_non_empty_string(payload.get("status"), "status", 3),
            monitoring_only_fields=monitoring_only_fields,
            underwriting_fields=underwriting_fields,
        )


@dataclass(slots=True)
class ModelVersionRecord(BaseRecord):
    model_id: str
    version_id: str
    effective_date: str
    change_summary: str
    assumptions: list[str]
    limitations: list[str]
    linked_validation_record: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelVersionRecord":
        return cls(
            **cls._base_kwargs(payload),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            effective_date=require_non_empty_string(payload.get("effective_date"), "effective_date", 10),
            change_summary=require_non_empty_string(payload.get("change_summary"), "change_summary", 10),
            assumptions=require_string_list(payload.get("assumptions"), "assumptions"),
            limitations=require_string_list(payload.get("limitations"), "limitations"),
            linked_validation_record=require_non_empty_string(
                payload.get("linked_validation_record"), "linked_validation_record", 3
            ),
        )


@dataclass(slots=True)
class ThresholdDefinition:
    metric_name: str
    comparison_rule: str
    threshold_value: float
    severity: str
    escalation_owner: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "ThresholdDefinition":
        threshold_value = payload.get("threshold_value")
        require_type(threshold_value, (int, float), f"{field}.threshold_value")
        return cls(
            metric_name=require_non_empty_string(payload.get("metric_name"), f"{field}.metric_name", 3),
            comparison_rule=require_non_empty_string(payload.get("comparison_rule"), f"{field}.comparison_rule", 3),
            threshold_value=float(threshold_value),
            severity=require_non_empty_string(payload.get("severity"), f"{field}.severity", 3),
            escalation_owner=require_non_empty_string(
                payload.get("escalation_owner"), f"{field}.escalation_owner", 3
            ),
        )


@dataclass(slots=True)
class ThresholdSet(BaseRecord):
    threshold_set_id: str
    model_id: str
    version_id: str
    review_cadence: str
    thresholds: list[ThresholdDefinition]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ThresholdSet":
        thresholds_payload = payload.get("thresholds")
        require_type(thresholds_payload, list, "thresholds")
        thresholds = [
            ThresholdDefinition.from_dict(item, f"thresholds[{index}]")
            for index, item in enumerate(thresholds_payload)
        ]
        if not thresholds:
            raise ValueError("thresholds must contain at least one item")
        return cls(
            **cls._base_kwargs(payload),
            threshold_set_id=require_non_empty_string(payload.get("threshold_set_id"), "threshold_set_id", 3),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            review_cadence=require_non_empty_string(payload.get("review_cadence"), "review_cadence", 3),
            thresholds=thresholds,
        )


@dataclass(slots=True)
class UnderwritingFields:
    score: float
    requested_amount: float
    decision_timestamp: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "UnderwritingFields":
        score = payload.get("score")
        requested_amount = payload.get("requested_amount")
        require_type(score, (int, float), f"{field}.score")
        require_type(requested_amount, (int, float), f"{field}.requested_amount")
        if float(requested_amount) <= 0:
            raise ValueError(f"{field}.requested_amount must be greater than zero")
        return cls(
            score=float(score),
            requested_amount=float(requested_amount),
            decision_timestamp=require_non_empty_string(
                payload.get("decision_timestamp"), f"{field}.decision_timestamp", 10
            ),
        )


@dataclass(slots=True)
class MonitoringFields:
    region: str
    channel: str
    review_batch_id: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], field: str) -> "MonitoringFields":
        return cls(
            region=require_non_empty_string(payload.get("region"), f"{field}.region", 2),
            channel=require_non_empty_string(payload.get("channel"), f"{field}.channel", 2),
            review_batch_id=require_non_empty_string(
                payload.get("review_batch_id"), f"{field}.review_batch_id", 3
            ),
        )


@dataclass(slots=True)
class ApplicationDecisionRecord(BaseRecord):
    decision_id: str
    application_date: str
    segment: str
    decision_outcome: str
    manual_review_flag: bool
    override_flag: bool
    underwriting: UnderwritingFields
    monitoring: MonitoringFields

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ApplicationDecisionRecord":
        manual_review_flag = payload.get("manual_review_flag")
        override_flag = payload.get("override_flag")
        require_type(manual_review_flag, bool, "manual_review_flag")
        require_type(override_flag, bool, "override_flag")
        return cls(
            **cls._base_kwargs(payload),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            application_date=require_non_empty_string(payload.get("application_date"), "application_date", 10),
            segment=require_non_empty_string(payload.get("segment"), "segment", 3),
            decision_outcome=require_non_empty_string(payload.get("decision_outcome"), "decision_outcome", 3),
            manual_review_flag=manual_review_flag,
            override_flag=override_flag,
            underwriting=UnderwritingFields.from_dict(payload.get("underwriting"), "underwriting"),
            monitoring=MonitoringFields.from_dict(payload.get("monitoring"), "monitoring"),
        )


@dataclass(slots=True)
class ScoreOutput(BaseRecord):
    decision_id: str
    score_value: float
    score_band: str
    score_version: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScoreOutput":
        score_value = payload.get("score_value")
        require_type(score_value, (int, float), "score_value")
        return cls(
            **cls._base_kwargs(payload),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            score_value=float(score_value),
            score_band=require_non_empty_string(payload.get("score_band"), "score_band", 1),
            score_version=require_non_empty_string(payload.get("score_version"), "score_version", 3),
        )


@dataclass(slots=True)
class ReasonCodeMapping(BaseRecord):
    mapping_id: str
    version_id: str
    driver_or_signal: str
    reason_code: str
    reason_text: str
    mapping_version: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReasonCodeMapping":
        return cls(
            **cls._base_kwargs(payload),
            mapping_id=require_non_empty_string(payload.get("mapping_id"), "mapping_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            driver_or_signal=require_non_empty_string(payload.get("driver_or_signal"), "driver_or_signal", 3),
            reason_code=require_non_empty_string(payload.get("reason_code"), "reason_code", 3),
            reason_text=require_non_empty_string(payload.get("reason_text"), "reason_text", 5),
            mapping_version=require_non_empty_string(payload.get("mapping_version"), "mapping_version", 3),
        )


@dataclass(slots=True)
class OverrideEvent(BaseRecord):
    override_id: str
    decision_id: str
    override_type: str
    override_reason: str
    reviewer: str
    override_date: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OverrideEvent":
        return cls(
            **cls._base_kwargs(payload),
            override_id=require_non_empty_string(payload.get("override_id"), "override_id", 3),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            override_type=require_non_empty_string(payload.get("override_type"), "override_type", 3),
            override_reason=require_non_empty_string(payload.get("override_reason"), "override_reason", 5),
            reviewer=require_non_empty_string(payload.get("reviewer"), "reviewer", 3),
            override_date=require_non_empty_string(payload.get("override_date"), "override_date", 10),
        )


@dataclass(slots=True)
class OutcomeRecord(BaseRecord):
    outcome_id: str
    decision_id: str
    observation_period: str
    repayment_or_default_indicator: str
    realized_outcome_value: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OutcomeRecord":
        realized_outcome_value = payload.get("realized_outcome_value")
        require_type(realized_outcome_value, (int, float), "realized_outcome_value")
        return cls(
            **cls._base_kwargs(payload),
            outcome_id=require_non_empty_string(payload.get("outcome_id"), "outcome_id", 3),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            observation_period=require_non_empty_string(payload.get("observation_period"), "observation_period", 2),
            repayment_or_default_indicator=require_non_empty_string(
                payload.get("repayment_or_default_indicator"),
                "repayment_or_default_indicator",
                3,
            ),
            realized_outcome_value=float(realized_outcome_value),
        )


@dataclass(slots=True)
class BreachRecord(BaseRecord):
    breach_id: str
    run_id: str
    metric_name: str
    observed_value: float
    threshold_value: float
    severity: str
    owner: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BreachRecord":
        observed_value = payload.get("observed_value")
        threshold_value = payload.get("threshold_value")
        require_type(observed_value, (int, float), "observed_value")
        require_type(threshold_value, (int, float), "threshold_value")
        return cls(
            **cls._base_kwargs(payload),
            breach_id=require_non_empty_string(payload.get("breach_id"), "breach_id", 3),
            run_id=require_non_empty_string(payload.get("run_id"), "run_id", 3),
            metric_name=require_non_empty_string(payload.get("metric_name"), "metric_name", 3),
            observed_value=float(observed_value),
            threshold_value=float(threshold_value),
            severity=require_non_empty_string(payload.get("severity"), "severity", 3),
            owner=require_non_empty_string(payload.get("owner"), "owner", 3),
        )


@dataclass(slots=True)
class EvidencePackManifest(BaseRecord):
    run_id: str
    created_at: str
    model_id: str
    version_id: str
    input_references: list[str]
    output_files: list[str]
    reviewer_status: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidencePackManifest":
        return cls(
            **cls._base_kwargs(payload),
            run_id=require_non_empty_string(payload.get("run_id"), "run_id", 3),
            created_at=require_non_empty_string(payload.get("created_at"), "created_at", 10),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            input_references=require_string_list(payload.get("input_references"), "input_references"),
            output_files=require_string_list(payload.get("output_files"), "output_files"),
            reviewer_status=require_non_empty_string(payload.get("reviewer_status"), "reviewer_status", 3),
        )

