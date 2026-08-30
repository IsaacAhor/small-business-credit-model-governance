"""Validate linked, synthetic vendor-model oversight records."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .schemas.models import (
    ApplicationDecisionRecord,
    ModelRegistryRecord,
    ModelVersionRecord,
    ReasonCodeMapping,
    ThresholdSet,
)
from .schemas.validators import (
    ROOT,
    ValidationResult,
    load_json,
    load_schema,
    validate_dataset,
    validate_record,
)
from .schemas.vendor_models import (
    BusinessCreditNoticeControl,
    VendorEventRecord,
    VendorModelComponent,
    VendorModelLimitation,
    VendorOversightConfig,
    VendorRiskReviewRecord,
)


@dataclass(frozen=True, slots=True)
class VendorSchemaSpec:
    filename: str
    schema_file: str
    model_factory: Callable[[dict[str, Any]], Any]
    collection: bool
    allow_empty: bool = False


VENDOR_SCHEMA_SPECS: tuple[VendorSchemaSpec, ...] = (
    VendorSchemaSpec(
        "vendor-risk-review-record.json",
        "vendor-risk-review-record.schema.json",
        VendorRiskReviewRecord.from_dict,
        False,
    ),
    VendorSchemaSpec(
        "vendor-model-components.json",
        "vendor-model-component.schema.json",
        VendorModelComponent.from_dict,
        True,
    ),
    VendorSchemaSpec(
        "vendor-model-limitations.json",
        "vendor-model-limitation.schema.json",
        VendorModelLimitation.from_dict,
        True,
        allow_empty=True,
    ),
    VendorSchemaSpec(
        "vendor-oversight-config.json",
        "vendor-oversight-config.schema.json",
        VendorOversightConfig.from_dict,
        False,
    ),
    VendorSchemaSpec(
        "vendor-event-records.json",
        "vendor-event-record.schema.json",
        VendorEventRecord.from_dict,
        True,
        allow_empty=True,
    ),
    VendorSchemaSpec(
        "business-credit-notice-controls.json",
        "business-credit-notice-control.schema.json",
        BusinessCreditNoticeControl.from_dict,
        True,
        allow_empty=True,
    ),
)

VENDOR_INPUT_FILENAMES = tuple(spec.filename for spec in VENDOR_SCHEMA_SPECS)
CORE_CONTEXT_SPECS: tuple[tuple[str, str, Callable[[dict[str, Any]], Any]], ...] = (
    ("model-registry-record.json", "model-registry-record.schema.json", ModelRegistryRecord.from_dict),
    ("model-version-record.json", "model-version-record.schema.json", ModelVersionRecord.from_dict),
    ("threshold-set.json", "threshold-set.schema.json", ThresholdSet.from_dict),
    (
        "application-decision-records.json",
        "application-decision-record.schema.json",
        ApplicationDecisionRecord.from_dict,
    ),
    ("reason-code-mappings.json", "reason-code-mapping.schema.json", ReasonCodeMapping.from_dict),
)
CORE_CONTEXT_FILENAMES = tuple(spec[0] for spec in CORE_CONTEXT_SPECS)


def _records(payload: Any, filename: str, *, collection: bool, allow_empty: bool) -> list[dict[str, Any]]:
    if collection:
        if not isinstance(payload, list):
            raise ValueError(f"{filename} must contain an array")
        if not payload and not allow_empty:
            raise ValueError(f"{filename} must contain at least one record")
        return payload
    if not isinstance(payload, dict):
        raise ValueError(f"{filename} must contain an object")
    return [payload]


def _unique(records: list[dict[str, Any]], field: str, filename: str) -> None:
    values = [record[field] for record in records]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"{filename}.{field} must be unique; duplicates: {', '.join(duplicates)}")


def resolve_evidence_reference(reference: str, vendor_dir: Path, core_dir: Path) -> Path | None:
    candidate = Path(reference)
    if candidate.is_absolute():
        candidates = [candidate]
    else:
        candidates = [vendor_dir / candidate, core_dir / candidate, ROOT / candidate]
    allowed_roots = [vendor_dir.resolve(), core_dir.resolve(), ROOT.resolve()]
    for path in candidates:
        resolved = path.resolve()
        if not any(resolved == root or root in resolved.parents for root in allowed_roots):
            continue
        if resolved.is_file():
            return resolved
    return None


def _require_evidence(reference: str, field: str, vendor_dir: Path, core_dir: Path) -> None:
    if resolve_evidence_reference(reference, vendor_dir, core_dir) is None:
        raise ValueError(f"{field} missing file: {reference}")


def load_vendor_payloads(vendor_dir: Path, core_dir: Path) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for filename in VENDOR_INPUT_FILENAMES:
        payloads[filename] = load_json(vendor_dir / filename)
    for filename in CORE_CONTEXT_FILENAMES:
        payloads[filename] = load_json(core_dir / filename)
    return payloads


def validate_vendor_relationships(vendor_dir: Path, core_dir: Path, payloads: dict[str, Any]) -> None:
    review = payloads["vendor-risk-review-record.json"]
    components = payloads["vendor-model-components.json"]
    limitations = payloads["vendor-model-limitations.json"]
    config = payloads["vendor-oversight-config.json"]
    events = payloads["vendor-event-records.json"]
    notice_controls = payloads["business-credit-notice-controls.json"]
    registry = payloads["model-registry-record.json"]
    version = payloads["model-version-record.json"]
    thresholds = payloads["threshold-set.json"]
    decisions = payloads["application-decision-records.json"]
    reason_mappings = payloads["reason-code-mappings.json"]

    _unique(components, "component_id", "vendor-model-components.json")
    _unique(limitations, "limitation_id", "vendor-model-limitations.json")
    _unique(events, "event_id", "vendor-event-records.json")
    _unique(notice_controls, "notice_control_id", "business-credit-notice-controls.json")
    _unique(review["findings"], "finding_id", "vendor-risk-review-record.json.findings")
    _unique(
        review["applicability_determinations"],
        "source_id",
        "vendor-risk-review-record.json.applicability_determinations",
    )

    if review["model_id"] != registry["model_id"]:
        raise ValueError("vendor-risk-review-record.json.model_id must match model registry")
    if review["version_id"] != version["version_id"]:
        raise ValueError("vendor-risk-review-record.json.version_id must match model version")
    if version["model_id"] != registry["model_id"]:
        raise ValueError("core model registry and version context are inconsistent")

    for reference in review["evidence_references"]:
        _require_evidence(reference, "vendor-risk-review-record.json.evidence_references", vendor_dir, core_dir)
    for index, determination in enumerate(review["applicability_determinations"]):
        _require_evidence(
            determination["evidence_reference"],
            f"vendor-risk-review-record.json.applicability_determinations[{index}].evidence_reference",
            vendor_dir,
            core_dir,
        )
    for index, document in enumerate(review["document_versions"]):
        _require_evidence(
            document["evidence_reference"],
            f"vendor-risk-review-record.json.document_versions[{index}].evidence_reference",
            vendor_dir,
            core_dir,
        )

    review_id = review["review_id"]
    component_by_id = {item["component_id"]: item for item in components}
    limitation_by_id = {item["limitation_id"]: item for item in limitations}
    event_by_id = {item["event_id"]: item for item in events}
    for index, component in enumerate(components):
        if component["review_id"] != review_id:
            raise ValueError(f"vendor-model-components.json[{index}].review_id references unknown review")
        if component["model_reference_status"] == "known":
            if component["model_id"] != registry["model_id"] or component["version_id"] != version["version_id"]:
                raise ValueError(f"vendor-model-components.json[{index}] references unknown model or version")
        unknown_limitations = sorted(set(component["limitation_ids"]) - set(limitation_by_id))
        if unknown_limitations:
            raise ValueError(
                f"vendor-model-components.json[{index}].limitation_ids references unknown value(s): "
                + ", ".join(unknown_limitations)
            )
        mismatched_limitations = sorted(
            limitation_id
            for limitation_id in component["limitation_ids"]
            if limitation_by_id[limitation_id]["component_id"] != component["component_id"]
        )
        if mismatched_limitations:
            raise ValueError(
                f"vendor-model-components.json[{index}].limitation_ids belongs to a different component: "
                + ", ".join(mismatched_limitations)
            )
        unknown_events = sorted(set(component["event_ids"]) - set(event_by_id))
        if unknown_events:
            raise ValueError(
                f"vendor-model-components.json[{index}].event_ids references unknown value(s): "
                + ", ".join(unknown_events)
            )
        mismatched_events = sorted(
            event_id
            for event_id in component["event_ids"]
            if event_by_id[event_id]["component_id"] != component["component_id"]
        )
        if mismatched_events:
            raise ValueError(
                f"vendor-model-components.json[{index}].event_ids belongs to a different component: "
                + ", ".join(mismatched_events)
            )
        if component["transparency_state"] in {"partial", "opaque"}:
            if not component["limitation_ids"]:
                raise ValueError(
                    f"vendor-model-components.json[{index}] partial or opaque component requires a limitation record"
                )
            unresolved = [
                item_id
                for item_id in component["limitation_ids"]
                if limitation_by_id[item_id]["residual_risk_decision"] == "pending"
            ]
            if unresolved:
                raise ValueError(
                    f"vendor-model-components.json[{index}] requires a compensating-control residual-risk decision"
                )

    for index, limitation in enumerate(limitations):
        if limitation["review_id"] != review_id:
            raise ValueError(f"vendor-model-limitations.json[{index}].review_id references unknown review")
        if limitation["component_id"] not in component_by_id:
            raise ValueError(f"vendor-model-limitations.json[{index}].component_id references unknown component")
        for reference in limitation["evidence_references"]:
            _require_evidence(reference, f"vendor-model-limitations.json[{index}].evidence_references", vendor_dir, core_dir)
    linked_limitation_ids = {
        limitation_id for component in components for limitation_id in component["limitation_ids"]
    }
    unlinked_limitations = sorted(set(limitation_by_id) - linked_limitation_ids)
    if unlinked_limitations:
        raise ValueError(
            "vendor limitation records must be linked from their component: "
            + ", ".join(unlinked_limitations)
        )

    if config["review_id"] != review_id:
        raise ValueError("vendor-oversight-config.json.review_id references unknown review")
    if config["risk_tier"] != review["risk_tier"]:
        raise ValueError("vendor-oversight-config.json.risk_tier must match vendor review")
    allowed_threshold_references = {thresholds["threshold_set_id"]} | {
        item["metric_name"] for item in thresholds["thresholds"]
    }
    unknown_thresholds = sorted(set(config["metric_threshold_references"]) - allowed_threshold_references)
    if unknown_thresholds:
        raise ValueError(
            "vendor-oversight-config.json.metric_threshold_references references unknown value(s): "
            + ", ".join(unknown_thresholds)
        )

    for index, event in enumerate(events):
        if event["review_id"] != review_id:
            raise ValueError(f"vendor-event-records.json[{index}].review_id references unknown review")
        if event["component_id"] not in component_by_id:
            raise ValueError(f"vendor-event-records.json[{index}].component_id references unknown component")
        for reference in event["evidence_references"]:
            _require_evidence(reference, f"vendor-event-records.json[{index}].evidence_references", vendor_dir, core_dir)
    linked_event_ids = {event_id for component in components for event_id in component["event_ids"]}
    unlinked_events = sorted(set(event_by_id) - linked_event_ids)
    if unlinked_events:
        raise ValueError("vendor event records must be linked from a component: " + ", ".join(unlinked_events))
    pending_material_events = [
        event["event_id"]
        for event in events
        if event["materiality"] in {"material", "high", "critical"}
        and event["assessment_disposition"] == "pending"
    ]
    if review["review_status"] in {"accepted", "accepted_with_conditions"} and pending_material_events:
        raise ValueError("accepted vendor review cannot have pending material event assessment")

    decision_by_id = {item["decision_id"]: item for item in decisions}
    decision_ids = set(decision_by_id)
    mapping_by_id = {item["mapping_id"]: item for item in reason_mappings}
    mapping_ids = set(mapping_by_id)
    reason_outputs_path = core_dir / "adverse-action-reason-outputs.json"
    reason_outputs = load_json(reason_outputs_path) if reason_outputs_path.is_file() else []
    for index, control in enumerate(notice_controls):
        if control["review_id"] != review_id:
            raise ValueError(f"business-credit-notice-controls.json[{index}].review_id references unknown review")
        if control["component_id"] not in component_by_id:
            raise ValueError(f"business-credit-notice-controls.json[{index}].component_id references unknown component")
        if control["decision_id"] not in decision_ids:
            raise ValueError(f"business-credit-notice-controls.json[{index}].decision_id references unknown decision")
        linked_decision = decision_by_id[control["decision_id"]]
        if control["application_date"] != linked_decision["application_date"]:
            raise ValueError(
                f"business-credit-notice-controls.json[{index}].application_date "
                "must match the linked decision application_date"
            )
        linked_action_date = linked_decision["underwriting"]["decision_timestamp"][:10]
        if control["action_date"] != linked_action_date:
            raise ValueError(
                f"business-credit-notice-controls.json[{index}].action_date "
                "must match the linked decision timestamp date"
            )
        unknown_mapping_ids = sorted(set(control["reason_mapping_ids"]) - mapping_ids)
        if unknown_mapping_ids:
            raise ValueError(
                f"business-credit-notice-controls.json[{index}].reason_mapping_ids references unknown value(s): "
                + ", ".join(unknown_mapping_ids)
            )
        expected_reason_codes = {
            mapping_by_id[mapping_id]["reason_code"]
            for mapping_id in control["reason_mapping_ids"]
        }
        actual_reason_codes = {
            output["reason_code"]
            for output in reason_outputs
            if output["decision_id"] == control["decision_id"]
        }
        if expected_reason_codes != actual_reason_codes:
            raise ValueError(
                f"business-credit-notice-controls.json[{index}].reason_mapping_ids "
                "must exactly match the recorded adverse-action reason outputs for the decision"
            )
        for field in ("reason_source_references", "evidence_references"):
            for reference in control[field]:
                _require_evidence(reference, f"business-credit-notice-controls.json[{index}].{field}", vendor_dir, core_dir)


def validate_vendor_risk_dataset(vendor_dir: Path, core_dir: Path) -> ValidationResult:
    vendor_dir = vendor_dir.resolve()
    core_dir = core_dir.resolve()
    errors: list[str] = []
    validated_files: list[str] = []
    payloads: dict[str, Any] = {}

    core_result = validate_dataset(core_dir)
    if not core_result.ok:
        errors.extend("core dataset: " + error for error in core_result.errors)
    else:
        try:
            for filename, schema_file, factory in CORE_CONTEXT_SPECS:
                payload = load_json(core_dir / filename)
                records = payload if isinstance(payload, list) else [payload]
                schema = load_schema(schema_file)
                for record in records:
                    validate_record(record, schema, factory)
                payloads[filename] = payload
                validated_files.append("core:" + filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"core context: {exc}")

    for spec in VENDOR_SCHEMA_SPECS:
        path = vendor_dir / spec.filename
        if not path.is_file():
            errors.append(f"Missing vendor dataset file: {spec.filename}")
            continue
        try:
            payload = load_json(path)
            records = _records(
                payload,
                spec.filename,
                collection=spec.collection,
                allow_empty=spec.allow_empty,
            )
            schema = load_schema(spec.schema_file)
            for record in records:
                validate_record(record, schema, spec.model_factory)
            payloads[spec.filename] = payload
            validated_files.append(spec.filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{spec.filename}: {exc}")

    if not errors:
        try:
            validate_vendor_relationships(vendor_dir, core_dir, payloads)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"vendor relationships: {exc}")
    return ValidationResult(
        ok=not errors,
        dataset_dir=str(vendor_dir),
        validated_files=validated_files,
        errors=errors,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a synthetic vendor-model oversight dataset and its core model context."
    )
    parser.add_argument("vendor_dataset_dir", type=Path)
    parser.add_argument("core_dataset_dir", type=Path)
    return parser


def validate_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_vendor_risk_dataset(args.vendor_dataset_dir, args.core_dataset_dir)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(validate_main())
