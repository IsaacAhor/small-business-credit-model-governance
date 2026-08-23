"""Typed contracts for synthetic vendor-model oversight records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .models import BaseRecord, require_non_empty_string, require_string_list, require_type


def require_boolean(value: Any, field: str) -> bool:
    require_type(value, bool, field)
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    require_type(value, dict, field)
    return value


def require_object_list(value: Any, field: str) -> list[dict[str, Any]]:
    require_type(value, list, field)
    if not value:
        raise ValueError(f"{field} must contain at least one item")
    for index, item in enumerate(value):
        require_type(item, dict, f"{field}[{index}]")
    return value


def require_maybe_empty_object_list(value: Any, field: str) -> list[dict[str, Any]]:
    require_type(value, list, field)
    for index, item in enumerate(value):
        require_type(item, dict, f"{field}[{index}]")
    return value


def require_maybe_empty_string_list(value: Any, field: str) -> list[str]:
    require_type(value, list, field)
    cleaned: list[str] = []
    for index, item in enumerate(value):
        cleaned.append(require_non_empty_string(item, f"{field}[{index}]"))
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{field} must not contain duplicates")
    return cleaned


@dataclass(slots=True)
class VendorRiskReviewRecord(BaseRecord):
    review_id: str
    vendor_id: str
    product_id: str
    product_version: str
    review_period_start: str
    review_period_end: str
    covered_use_cases: list[str]
    decision_impact: str
    decision_authority: str
    model_id: str
    version_id: str
    applicability_determinations: list[dict[str, Any]]
    document_versions: list[dict[str, Any]]
    contract_version: str
    risk_tier: str
    risk_rationale: str
    evidence_references: list[str]
    owners: dict[str, Any]
    findings: list[dict[str, Any]]
    review_status: str
    signoff: dict[str, Any]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VendorRiskReviewRecord":
        review_start = require_non_empty_string(payload.get("review_period_start"), "review_period_start", 10)
        review_end = require_non_empty_string(payload.get("review_period_end"), "review_period_end", 10)
        if date.fromisoformat(review_start) > date.fromisoformat(review_end):
            raise ValueError("review_period_start must not be after review_period_end")
        signoff = require_object(payload.get("signoff"), "signoff")
        review_status = require_non_empty_string(payload.get("review_status"), "review_status", 3)
        if review_status in {"accepted", "accepted_with_conditions"}:
            if signoff.get("independence_status") not in {"independent_internal", "independent_external"}:
                raise ValueError("accepted vendor review requires an independent reviewer role")
            expected = "accepted" if review_status == "accepted" else "accepted_with_conditions"
            if signoff.get("disposition") != expected:
                raise ValueError("review_status must match signoff.disposition")
        return cls(
            **cls._base_kwargs(payload),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            vendor_id=require_non_empty_string(payload.get("vendor_id"), "vendor_id", 3),
            product_id=require_non_empty_string(payload.get("product_id"), "product_id", 3),
            product_version=require_non_empty_string(payload.get("product_version"), "product_version", 3),
            review_period_start=review_start,
            review_period_end=review_end,
            covered_use_cases=require_string_list(payload.get("covered_use_cases"), "covered_use_cases"),
            decision_impact=require_non_empty_string(payload.get("decision_impact"), "decision_impact", 3),
            decision_authority=require_non_empty_string(payload.get("decision_authority"), "decision_authority", 3),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            applicability_determinations=require_object_list(payload.get("applicability_determinations"), "applicability_determinations"),
            document_versions=require_object_list(payload.get("document_versions"), "document_versions"),
            contract_version=require_non_empty_string(payload.get("contract_version"), "contract_version", 3),
            risk_tier=require_non_empty_string(payload.get("risk_tier"), "risk_tier", 3),
            risk_rationale=require_non_empty_string(payload.get("risk_rationale"), "risk_rationale", 20),
            evidence_references=require_string_list(payload.get("evidence_references"), "evidence_references"),
            owners=require_object(payload.get("owners"), "owners"),
            findings=require_maybe_empty_object_list(payload.get("findings"), "findings"),
            review_status=review_status,
            signoff=signoff,
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class VendorModelComponent(BaseRecord):
    component_id: str
    review_id: str
    component_type: str
    function: str
    model_reference_status: str
    model_id: str
    version_id: str
    data_categories: list[str]
    output_type: str
    decision_role: str
    model_change_notice_method: str
    subcontractor_status: str
    transparency_state: str
    limitation_ids: list[str]
    event_status: str
    event_ids: list[str]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VendorModelComponent":
        reference_status = require_non_empty_string(payload.get("model_reference_status"), "model_reference_status", 3)
        model_id = require_non_empty_string(payload.get("model_id"), "model_id", 3)
        version_id = require_non_empty_string(payload.get("version_id"), "version_id", 3)
        if reference_status == "known" and (model_id.startswith("not_") or version_id.startswith("not_")):
            raise ValueError("known model reference requires concrete model_id and version_id")
        if reference_status != "known" and (model_id != reference_status or version_id != reference_status):
            raise ValueError("unavailable model references must use the model_reference_status sentinel")
        event_status = require_non_empty_string(payload.get("event_status"), "event_status", 3)
        event_ids = require_maybe_empty_string_list(payload.get("event_ids"), "event_ids")
        if event_status == "event_reported" and not event_ids:
            raise ValueError("event_reported component requires at least one event_id")
        if event_status == "no_event_reported" and event_ids:
            raise ValueError("no_event_reported component must not reference event_ids")
        return cls(
            **cls._base_kwargs(payload),
            component_id=require_non_empty_string(payload.get("component_id"), "component_id", 3),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            component_type=require_non_empty_string(payload.get("component_type"), "component_type", 3),
            function=require_non_empty_string(payload.get("function"), "function", 10),
            model_reference_status=reference_status,
            model_id=model_id,
            version_id=version_id,
            data_categories=require_string_list(payload.get("data_categories"), "data_categories"),
            output_type=require_non_empty_string(payload.get("output_type"), "output_type", 3),
            decision_role=require_non_empty_string(payload.get("decision_role"), "decision_role", 3),
            model_change_notice_method=require_non_empty_string(payload.get("model_change_notice_method"), "model_change_notice_method", 10),
            subcontractor_status=require_non_empty_string(payload.get("subcontractor_status"), "subcontractor_status", 3),
            transparency_state=require_non_empty_string(payload.get("transparency_state"), "transparency_state", 3),
            limitation_ids=require_maybe_empty_string_list(payload.get("limitation_ids"), "limitation_ids"),
            event_status=event_status,
            event_ids=event_ids,
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class VendorModelLimitation(BaseRecord):
    limitation_id: str
    review_id: str
    component_id: str
    category: str
    description: str
    transparency_state: str
    evidence_available: bool
    evidence_references: list[str]
    validation_status: str
    compensating_control: str
    residual_risk_decision: str
    owner: str
    review_date: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VendorModelLimitation":
        evidence_available = require_boolean(payload.get("evidence_available"), "evidence_available")
        evidence_references = require_maybe_empty_string_list(payload.get("evidence_references"), "evidence_references")
        if evidence_available and not evidence_references:
            raise ValueError("evidence_references is required when evidence_available is true")
        return cls(
            **cls._base_kwargs(payload),
            limitation_id=require_non_empty_string(payload.get("limitation_id"), "limitation_id", 3),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            component_id=require_non_empty_string(payload.get("component_id"), "component_id", 3),
            category=require_non_empty_string(payload.get("category"), "category", 3),
            description=require_non_empty_string(payload.get("description"), "description", 15),
            transparency_state=require_non_empty_string(payload.get("transparency_state"), "transparency_state", 3),
            evidence_available=evidence_available,
            evidence_references=evidence_references,
            validation_status=require_non_empty_string(payload.get("validation_status"), "validation_status", 3),
            compensating_control=require_non_empty_string(payload.get("compensating_control"), "compensating_control", 10),
            residual_risk_decision=require_non_empty_string(payload.get("residual_risk_decision"), "residual_risk_decision", 3),
            owner=require_non_empty_string(payload.get("owner"), "owner", 3),
            review_date=require_non_empty_string(payload.get("review_date"), "review_date", 10),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class VendorOversightConfig(BaseRecord):
    oversight_config_id: str
    review_id: str
    risk_tier: str
    review_cadence: str
    cadence_rationale: str
    metric_threshold_references: list[str]
    event_triggers: list[str]
    heightened_monitoring: dict[str, Any]
    owners: dict[str, Any]
    reporting_audience: list[str]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VendorOversightConfig":
        risk_tier = require_non_empty_string(payload.get("risk_tier"), "risk_tier", 3)
        heightened = require_object(payload.get("heightened_monitoring"), "heightened_monitoring")
        required = require_boolean(heightened.get("required"), "heightened_monitoring.required")
        if risk_tier in {"high", "critical"} and not required:
            raise ValueError("high or critical vendor risk requires heightened monitoring")
        if required and heightened.get("status") == "not_required":
            raise ValueError("required heightened monitoring cannot have not_required status")
        return cls(
            **cls._base_kwargs(payload),
            oversight_config_id=require_non_empty_string(payload.get("oversight_config_id"), "oversight_config_id", 3),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            risk_tier=risk_tier,
            review_cadence=require_non_empty_string(payload.get("review_cadence"), "review_cadence", 5),
            cadence_rationale=require_non_empty_string(payload.get("cadence_rationale"), "cadence_rationale", 20),
            metric_threshold_references=require_string_list(payload.get("metric_threshold_references"), "metric_threshold_references"),
            event_triggers=require_string_list(payload.get("event_triggers"), "event_triggers"),
            heightened_monitoring=heightened,
            owners=require_object(payload.get("owners"), "owners"),
            reporting_audience=require_string_list(payload.get("reporting_audience"), "reporting_audience"),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class VendorEventRecord(BaseRecord):
    event_id: str
    review_id: str
    component_id: str
    event_type: str
    detected_at: str
    vendor_notice_at: str | None
    materiality: str
    affected_version: str
    impact_summary: str
    contract_notice_status: str
    institution_assessment_required: bool
    assessment_disposition: str
    escalation_owner: str
    remediation_status: str
    evidence_references: list[str]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VendorEventRecord":
        materiality = require_non_empty_string(payload.get("materiality"), "materiality", 3)
        assessment_required = require_boolean(payload.get("institution_assessment_required"), "institution_assessment_required")
        notice_status = require_non_empty_string(
            payload.get("contract_notice_status"), "contract_notice_status", 3
        )
        notice_at = payload.get("vendor_notice_at")
        if notice_at is not None:
            notice_at = require_non_empty_string(notice_at, "vendor_notice_at", 20)
        if notice_status in {"timely", "late"} and notice_at is None:
            raise ValueError("timely or late vendor notice requires vendor_notice_at")
        if notice_status in {"not_required", "not_received"} and notice_at is not None:
            raise ValueError(
                "vendor_notice_at must be omitted when notice is not required or not received"
            )
        if materiality in {"material", "high", "critical"} and not assessment_required:
            raise ValueError("material vendor event requires institution assessment")
        return cls(
            **cls._base_kwargs(payload),
            event_id=require_non_empty_string(payload.get("event_id"), "event_id", 3),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            component_id=require_non_empty_string(payload.get("component_id"), "component_id", 3),
            event_type=require_non_empty_string(payload.get("event_type"), "event_type", 3),
            detected_at=require_non_empty_string(payload.get("detected_at"), "detected_at", 20),
            vendor_notice_at=notice_at,
            materiality=materiality,
            affected_version=require_non_empty_string(payload.get("affected_version"), "affected_version", 3),
            impact_summary=require_non_empty_string(payload.get("impact_summary"), "impact_summary", 15),
            contract_notice_status=notice_status,
            institution_assessment_required=assessment_required,
            assessment_disposition=require_non_empty_string(payload.get("assessment_disposition"), "assessment_disposition", 3),
            escalation_owner=require_non_empty_string(payload.get("escalation_owner"), "escalation_owner", 3),
            remediation_status=require_non_empty_string(payload.get("remediation_status"), "remediation_status", 3),
            evidence_references=require_string_list(payload.get("evidence_references"), "evidence_references"),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class BusinessCreditNoticeControl(BaseRecord):
    notice_control_id: str
    review_id: str
    component_id: str
    decision_id: str
    credit_classification: str
    path_determination: str
    application_date: str
    action_date: str
    reason_source_references: list[str]
    reason_mapping_ids: list[str]
    specific_reason_review: str
    retention_basis: str
    fcra_applicability: str
    esign_applicability: str
    section_1071_applicability: str
    reviewer_disposition: str
    evidence_references: list[str]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BusinessCreditNoticeControl":
        application_date = require_non_empty_string(payload.get("application_date"), "application_date", 10)
        action_date = require_non_empty_string(payload.get("action_date"), "action_date", 10)
        if date.fromisoformat(application_date) > date.fromisoformat(action_date):
            raise ValueError("application_date must not be after action_date")
        return cls(
            **cls._base_kwargs(payload),
            notice_control_id=require_non_empty_string(payload.get("notice_control_id"), "notice_control_id", 3),
            review_id=require_non_empty_string(payload.get("review_id"), "review_id", 3),
            component_id=require_non_empty_string(payload.get("component_id"), "component_id", 3),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            credit_classification=require_non_empty_string(payload.get("credit_classification"), "credit_classification", 3),
            path_determination=require_non_empty_string(payload.get("path_determination"), "path_determination", 3),
            application_date=application_date,
            action_date=action_date,
            reason_source_references=require_string_list(payload.get("reason_source_references"), "reason_source_references"),
            reason_mapping_ids=require_string_list(payload.get("reason_mapping_ids"), "reason_mapping_ids"),
            specific_reason_review=require_non_empty_string(payload.get("specific_reason_review"), "specific_reason_review", 3),
            retention_basis=require_non_empty_string(payload.get("retention_basis"), "retention_basis", 15),
            fcra_applicability=require_non_empty_string(payload.get("fcra_applicability"), "fcra_applicability", 3),
            esign_applicability=require_non_empty_string(payload.get("esign_applicability"), "esign_applicability", 3),
            section_1071_applicability=require_non_empty_string(payload.get("section_1071_applicability"), "section_1071_applicability", 3),
            reviewer_disposition=require_non_empty_string(payload.get("reviewer_disposition"), "reviewer_disposition", 3),
            evidence_references=require_string_list(payload.get("evidence_references"), "evidence_references"),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )
