"""Schema and typed-model validation for deterministic demo inputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable

from .models import (
    AdverseActionReasonOutput,
    ApplicationDecisionRecord,
    BreachRecord,
    EvidencePackManifest,
    FairLendingScreeningConfig,
    ModelRegistryRecord,
    ModelVersionRecord,
    OutcomeRecord,
    OverrideEvent,
    ReasonCodeMapping,
    ScoreOutput,
    ThresholdSet,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "schemas"

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    dataset_dir: str
    validated_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dataset_dir": self.dataset_dir,
            "validated_files": self.validated_files,
            "errors": self.errors,
        }


@dataclass(frozen=True, slots=True)
class SchemaSpec:
    filename: str
    schema_file: str
    model_factory: Callable[[dict[str, Any]], Any]


SCHEMA_SPECS: tuple[SchemaSpec, ...] = (
    SchemaSpec("model-registry-record.json", "model-registry-record.schema.json", ModelRegistryRecord.from_dict),
    SchemaSpec("model-version-record.json", "model-version-record.schema.json", ModelVersionRecord.from_dict),
    SchemaSpec("threshold-set.json", "threshold-set.schema.json", ThresholdSet.from_dict),
    SchemaSpec(
        "application-decision-records.json",
        "application-decision-record.schema.json",
        ApplicationDecisionRecord.from_dict,
    ),
    SchemaSpec("score-outputs.json", "score-output.schema.json", ScoreOutput.from_dict),
    SchemaSpec("reason-code-mappings.json", "reason-code-mapping.schema.json", ReasonCodeMapping.from_dict),
    SchemaSpec(
        "adverse-action-reason-outputs.json",
        "adverse-action-reason-output.schema.json",
        AdverseActionReasonOutput.from_dict,
    ),
    SchemaSpec(
        "fair-lending-screening-config.json",
        "fair-lending-screening-config.schema.json",
        FairLendingScreeningConfig.from_dict,
    ),
    SchemaSpec("override-events.json", "override-event.schema.json", OverrideEvent.from_dict),
    SchemaSpec("outcome-records.json", "outcome-record.schema.json", OutcomeRecord.from_dict),
    SchemaSpec("breach-records.json", "breach-record.schema.json", BreachRecord.from_dict),
    SchemaSpec(
        "evidence-pack-manifest.json",
        "evidence-pack-manifest.schema.json",
        EvidencePackManifest.from_dict,
    ),
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(schema_file: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / schema_file
    if schema_path.is_file():
        return load_json(schema_path)

    resource = files("credit_gov.schemas").joinpath("json", schema_file)
    if not resource.is_file():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")
    with resource.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_date_string(value: str, field: str) -> None:
    if not DATE_PATTERN.match(value):
        raise ValueError(f"{field} must use YYYY-MM-DD")
    date.fromisoformat(value)


def validate_datetime_string(value: str, field: str) -> None:
    if not DATETIME_PATTERN.match(value):
        raise ValueError(f"{field} must use YYYY-MM-DDTHH:MM:SSZ")


def validate_pattern(value: Any, pattern: str, field: str) -> None:
    if not isinstance(value, str) or not re.match(pattern, value):
        raise ValueError(f"{field} does not match required pattern")


def validate_enum(value: Any, allowed: list[str], field: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(allowed)}")


def validate_array(value: Any, field: str, minimum: int = 0) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if len(value) < minimum:
        raise ValueError(f"{field} must contain at least {minimum} item(s)")


def validate_object(payload: dict[str, Any], schema: dict[str, Any], field_prefix: str = "") -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{field_prefix or 'payload'} must be an object")
    required = schema.get("required", [])
    for field in required:
        if field not in payload:
            raise ValueError(f"{qualify(field_prefix, field)} is required")
    if schema.get("additionalProperties") is False:
        extra = sorted(set(payload) - set(schema.get("properties", {})))
        if extra:
            raise ValueError(
                f"{field_prefix or 'payload'} has unexpected field(s): {', '.join(extra)}"
            )
    for field, definition in schema.get("properties", {}).items():
        if field in payload:
            validate_value(payload[field], definition, qualify(field_prefix, field))


def qualify(prefix: str, field: str) -> str:
    return f"{prefix}.{field}" if prefix else field


def validate_value(value: Any, definition: dict[str, Any], field: str) -> None:
    if "const" in definition and value != definition["const"]:
        raise ValueError(f"{field} must equal {definition['const']}")
    if "enum" in definition:
        validate_enum(value, definition["enum"], field)
    schema_type = definition.get("type")
    if schema_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        minimum = definition.get("minLength")
        if minimum is not None and len(value.strip()) < minimum:
            raise ValueError(f"{field} must be at least {minimum} characters")
        pattern = definition.get("pattern")
        if pattern:
            validate_pattern(value, pattern, field)
        fmt = definition.get("format")
        if fmt == "date":
            validate_date_string(value, field)
    elif schema_type == "number":
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        minimum = definition.get("exclusiveMinimum")
        if minimum is not None and float(value) <= minimum:
            raise ValueError(f"{field} must be greater than {minimum}")
    elif schema_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{field} must be boolean")
    elif schema_type == "array":
        validate_array(value, field, definition.get("minItems", 0))
        if definition.get("uniqueItems") and len(value) != len(set(value)):
            raise ValueError(f"{field} must not contain duplicate items")
        item_schema = definition.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_value(item, item_schema, f"{field}[{index}]")
    elif schema_type == "object":
        validate_object(value, definition, field)


def validate_record(payload: dict[str, Any], schema: dict[str, Any], model_factory: Callable[[dict[str, Any]], Any]) -> None:
    validate_object(payload, schema)
    model = model_factory(payload)
    if hasattr(model, "effective_date"):
        validate_date_string(model.effective_date, "effective_date")
    if hasattr(model, "application_date"):
        validate_date_string(model.application_date, "application_date")
    if hasattr(model, "override_date"):
        validate_date_string(model.override_date, "override_date")
    if hasattr(model, "created_at"):
        validate_datetime_string(model.created_at, "created_at")


def validate_dataset(dataset_dir: Path) -> ValidationResult:
    errors: list[str] = []
    validated_files: list[str] = []
    payloads: dict[str, Any] = {}
    for spec in SCHEMA_SPECS:
        data_path = dataset_dir / spec.filename
        if not data_path.is_file():
            errors.append(f"Missing dataset file: {spec.filename}")
            continue
        try:
            payload = load_json(data_path)
            payloads[spec.filename] = payload
            schema = load_schema(spec.schema_file)
            records = payload if isinstance(payload, list) else [payload]
            optional_empty_lists = {
                "adverse-action-reason-outputs.json",
                "breach-records.json",
            }
            if isinstance(payload, list) and not payload and spec.filename not in optional_empty_lists:
                raise ValueError(f"{spec.filename} must contain at least one record")
            for index, record in enumerate(records):
                validate_record(record, schema, spec.model_factory)
                if spec.filename == "application-decision-records.json":
                    validate_application_decision_business_rules(record, index)
            validated_files.append(spec.filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{spec.filename}: {exc}")
    if not errors:
        try:
            validate_dataset_relationships(dataset_dir, payloads)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"dataset relationships: {exc}")
    return ValidationResult(
        ok=not errors,
        dataset_dir=str(dataset_dir),
        validated_files=validated_files,
        errors=errors,
    )


def validate_dataset_relationships(dataset_dir: Path, payloads: dict[str, Any]) -> None:
    model_registry = require_object_payload(payloads, "model-registry-record.json")
    model_version = require_object_payload(payloads, "model-version-record.json")
    threshold_set = require_object_payload(payloads, "threshold-set.json")
    fair_lending_config = require_object_payload(payloads, "fair-lending-screening-config.json")
    manifest = require_object_payload(payloads, "evidence-pack-manifest.json")

    decisions = require_list_payload(payloads, "application-decision-records.json")
    score_outputs = require_list_payload(payloads, "score-outputs.json")
    reason_mappings = require_list_payload(payloads, "reason-code-mappings.json")
    reason_outputs = require_list_payload(payloads, "adverse-action-reason-outputs.json")
    overrides = require_list_payload(payloads, "override-events.json")
    outcomes = require_list_payload(payloads, "outcome-records.json")
    breaches = require_list_payload(payloads, "breach-records.json")

    model_id = model_registry["model_id"]
    version_id = model_version["version_id"]
    run_id = manifest["run_id"]

    require_equal(model_version["model_id"], model_id, "model-version-record.json.model_id")
    require_equal(threshold_set["model_id"], model_id, "threshold-set.json.model_id")
    require_equal(threshold_set["version_id"], version_id, "threshold-set.json.version_id")
    require_equal(fair_lending_config["model_id"], model_id, "fair-lending-screening-config.json.model_id")
    require_equal(fair_lending_config["version_id"], version_id, "fair-lending-screening-config.json.version_id")
    require_equal(manifest["model_id"], model_id, "evidence-pack-manifest.json.model_id")
    require_equal(manifest["version_id"], version_id, "evidence-pack-manifest.json.version_id")

    decision_ids = {record["decision_id"] for record in decisions}
    for index, record in enumerate(decisions):
        require_equal(
            record["monitoring"]["review_batch_id"],
            run_id,
            f"application-decision-records.json[{index}].monitoring.review_batch_id",
        )

    for index, record in enumerate(score_outputs):
        require_member(
            record["decision_id"],
            decision_ids,
            f"score-outputs.json[{index}].decision_id",
        )
        require_equal(
            record["score_version"],
            version_id,
            f"score-outputs.json[{index}].score_version",
        )

    for index, record in enumerate(reason_mappings):
        require_equal(record["version_id"], version_id, f"reason-code-mappings.json[{index}].version_id")

    for index, record in enumerate(reason_outputs):
        require_member(
            record["decision_id"],
            decision_ids,
            f"adverse-action-reason-outputs.json[{index}].decision_id",
        )
        require_equal(
            record["version_id"],
            version_id,
            f"adverse-action-reason-outputs.json[{index}].version_id",
        )

    for index, record in enumerate(overrides):
        require_member(
            record["decision_id"],
            decision_ids,
            f"override-events.json[{index}].decision_id",
        )

    for index, record in enumerate(outcomes):
        require_member(
            record["decision_id"],
            decision_ids,
            f"outcome-records.json[{index}].decision_id",
        )

    threshold_metrics = {record["metric_name"] for record in threshold_set["thresholds"]}
    for index, record in enumerate(breaches):
        require_equal(record["run_id"], run_id, f"breach-records.json[{index}].run_id")
        require_member(
            record["metric_name"],
            threshold_metrics,
            f"breach-records.json[{index}].metric_name",
        )

    for reference in manifest["input_references"]:
        if not (dataset_dir / reference).is_file():
            raise ValueError(
                f"evidence-pack-manifest.json.input_references missing file: {reference}"
            )


def require_object_payload(payloads: dict[str, Any], filename: str) -> dict[str, Any]:
    payload = payloads[filename]
    if not isinstance(payload, dict):
        raise ValueError(f"{filename} must be an object for relationship validation")
    return payload


def require_list_payload(payloads: dict[str, Any], filename: str) -> list[dict[str, Any]]:
    payload = payloads[filename]
    if not isinstance(payload, list):
        raise ValueError(f"{filename} must be an array for relationship validation")
    return payload


def require_equal(actual: str, expected: str, field: str) -> None:
    if actual != expected:
        raise ValueError(f"{field} must equal {expected}")


def require_member(actual: str, allowed: set[str], field: str) -> None:
    if actual not in allowed:
        raise ValueError(f"{field} references unknown value: {actual}")


def validate_application_decision_business_rules(record: dict[str, Any], index: int) -> None:
    underwriting = record["underwriting"]
    monitoring = record["monitoring"]
    overlap = sorted(set(underwriting) & set(monitoring))
    if overlap:
        raise ValueError(
            f"application_decision_records[{index}] mixes underwriting and monitoring fields: "
            + ", ".join(overlap)
        )
