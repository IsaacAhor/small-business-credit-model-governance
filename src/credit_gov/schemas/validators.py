"""Schema and typed-model validation for deterministic demo inputs."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable

from .governance_models import (
    ExplainabilityMethodRecord,
    ModelMonitoringPlan,
    ModelRiskProfile,
    ModelValidationRecord,
)
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

OPTIONAL_GOVERNANCE_SCHEMA_SPECS: tuple[SchemaSpec, ...] = (
    SchemaSpec(
        "model-risk-profile.json",
        "model-risk-profile.schema.json",
        ModelRiskProfile.from_dict,
    ),
    SchemaSpec(
        "explainability-method-records.json",
        "explainability-method-record.schema.json",
        ExplainabilityMethodRecord.from_dict,
    ),
    SchemaSpec(
        "model-validation-record.json",
        "model-validation-record.schema.json",
        ModelValidationRecord.from_dict,
    ),
    SchemaSpec(
        "model-monitoring-plan.json",
        "model-monitoring-plan.schema.json",
        ModelMonitoringPlan.from_dict,
    ),
)

OPTIONAL_GOVERNANCE_FILENAMES = {
    spec.filename for spec in OPTIONAL_GOVERNANCE_SCHEMA_SPECS
}

APPLICABILITY_FILENAME = "monitoring-applicability.json"


def validate_monitoring_applicability(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply semantic checks that the lightweight JSON-schema walker cannot infer."""
    modules = payload.get("modules")
    if not isinstance(modules, dict):
        raise ValueError("modules must be an object")
    required_modules = {
        "decision_outcome_rates",
        "manual_review",
        "override_monitoring",
        "adverse_action_reason_qa",
        "fair_lending_screening",
    }
    missing = sorted(required_modules - set(modules))
    extra = sorted(set(modules) - required_modules)
    if missing:
        raise ValueError(f"modules is missing: {', '.join(missing)}")
    if extra:
        raise ValueError(f"modules has unexpected field(s): {', '.join(extra)}")
    for name, module in modules.items():
        if not isinstance(module, dict):
            raise ValueError(f"modules.{name} must be an object")
        if set(module) != {"applicable", "reason"}:
            raise ValueError(f"modules.{name} must contain only applicable and reason")
        if not isinstance(module["applicable"], bool):
            raise ValueError(f"modules.{name}.applicable must be boolean")
        if not isinstance(module["reason"], str) or len(module["reason"].strip()) < 10:
            raise ValueError(f"modules.{name}.reason must be at least 10 characters")
    return payload


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


def resolve_dataset_reference(dataset_dir: Path, reference: str) -> Path | None:
    """Resolve a local evidence reference from a dataset or source checkout."""
    dataset_root = dataset_dir.resolve()
    allowed_roots = [dataset_root]
    source_candidates = [ROOT.resolve(), dataset_root, *dataset_root.parents]
    for candidate in source_candidates:
        if (candidate / "pyproject.toml").is_file() and candidate not in allowed_roots:
            allowed_roots.append(candidate)

    reference_path = Path(reference)
    if reference_path.is_absolute():
        candidates = [reference_path]
    else:
        candidates = [root / reference_path for root in allowed_roots]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if not any(
            resolved == allowed_root or allowed_root in resolved.parents
            for allowed_root in allowed_roots
        ):
            continue
        if resolved.is_file():
            return resolved
    return None


def validate_date_string(value: str, field: str) -> None:
    if not DATE_PATTERN.match(value):
        raise ValueError(f"{field} must use YYYY-MM-DD")
    date.fromisoformat(value)


def validate_datetime_string(value: str, field: str) -> None:
    if not DATETIME_PATTERN.match(value):
        raise ValueError(f"{field} must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid UTC timestamp") from exc


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
        elif fmt == "date-time":
            validate_datetime_string(value, field)
    elif schema_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        if not math.isfinite(float(value)):
            raise ValueError(f"{field} must be finite")
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
    applicability_path = dataset_dir / APPLICABILITY_FILENAME
    if applicability_path.is_file():
        try:
            applicability = load_json(applicability_path)
            schema = load_schema("monitoring-applicability.schema.json")
            validate_record(applicability, schema, validate_monitoring_applicability)
            payloads[APPLICABILITY_FILENAME] = applicability
            validated_files.append(APPLICABILITY_FILENAME)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{APPLICABILITY_FILENAME}: {exc}")

    modules = payloads.get(APPLICABILITY_FILENAME, {}).get("modules", {})
    optional_empty_lists = {
        "adverse-action-reason-outputs.json",
        "breach-records.json",
    }
    if modules.get("override_monitoring", {}).get("applicable") is False:
        optional_empty_lists.add("override-events.json")
    if modules.get("adverse_action_reason_qa", {}).get("applicable") is False:
        optional_empty_lists.add("reason-code-mappings.json")
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
            if isinstance(payload, list) and not payload and spec.filename not in optional_empty_lists:
                raise ValueError(f"{spec.filename} must contain at least one record")
            for index, record in enumerate(records):
                validate_record(record, schema, spec.model_factory)
                if spec.filename == "application-decision-records.json":
                    validate_application_decision_business_rules(record, index)
            validated_files.append(spec.filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{spec.filename}: {exc}")
    present_governance_files = {
        filename
        for filename in OPTIONAL_GOVERNANCE_FILENAMES
        if (dataset_dir / filename).is_file()
    }
    governance_bundle_present = bool(present_governance_files)
    if governance_bundle_present:
        missing_governance_files = sorted(
            OPTIONAL_GOVERNANCE_FILENAMES - present_governance_files
        )
        for filename in missing_governance_files:
            errors.append(
                "Incomplete governance bundle; missing dataset file: " + filename
            )
        for spec in OPTIONAL_GOVERNANCE_SCHEMA_SPECS:
            data_path = dataset_dir / spec.filename
            if not data_path.is_file():
                continue
            try:
                payload = load_json(data_path)
                payloads[spec.filename] = payload
                schema = load_schema(spec.schema_file)
                records = payload if isinstance(payload, list) else [payload]
                if isinstance(payload, list) and not payload:
                    raise ValueError(f"{spec.filename} must contain at least one record")
                for record in records:
                    validate_record(record, schema, spec.model_factory)
                validated_files.append(spec.filename)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{spec.filename}: {exc}")
    if not errors:
        try:
            validate_dataset_relationships(dataset_dir, payloads)
            if governance_bundle_present:
                validate_governance_relationships(dataset_dir, payloads)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"dataset relationships: {exc}")
    if not errors:
        rendered_notice_path = dataset_dir / "rendered-adverse-action-notices.json"
        if rendered_notice_path.is_file():
            try:
                validate_rendered_notice_records(rendered_notice_path, payloads)
                validated_files.append(rendered_notice_path.name)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rendered_notice_path.name}: {exc}")
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

    applicability = payloads.get(APPLICABILITY_FILENAME)
    if applicability is not None:
        modules = applicability["modules"]
        if modules["override_monitoring"]["applicable"] is False and overrides:
            raise ValueError("override-events.json must be empty when override monitoring is not applicable")
        if modules["adverse_action_reason_qa"]["applicable"] is False:
            if reason_mappings or reason_outputs:
                raise ValueError(
                    "reason-code mappings and outputs must be empty when reason QA is not applicable"
                )
        fair_applicable = modules["fair_lending_screening"]["applicable"]
        if bool(fair_lending_config.get("applicable", True)) != fair_applicable:
            raise ValueError(
                "fair-lending-screening-config.json applicable must match monitoring-applicability.json"
            )

    require_unique_values(decisions, "decision_id", "application-decision-records.json")
    require_unique_values(score_outputs, "decision_id", "score-outputs.json")
    require_unique_values(reason_mappings, "mapping_id", "reason-code-mappings.json")
    require_unique_values(reason_outputs, "reason_output_id", "adverse-action-reason-outputs.json")
    require_unique_values(overrides, "override_id", "override-events.json")
    require_unique_values(outcomes, "outcome_id", "outcome-records.json")
    require_unique_values(breaches, "breach_id", "breach-records.json")
    require_unique_pairs(
        reason_outputs,
        "decision_id",
        "reason_rank",
        "adverse-action-reason-outputs.json",
    )
    require_unique_pairs(outcomes, "decision_id", "observation_period", "outcome-records.json")

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


def validate_governance_relationships(
    dataset_dir: Path, payloads: dict[str, Any]
) -> None:
    """Validate links within the optional governance bundle and to core records."""
    model_registry = require_object_payload(payloads, "model-registry-record.json")
    model_version = require_object_payload(payloads, "model-version-record.json")
    threshold_set = require_object_payload(payloads, "threshold-set.json")
    manifest = require_object_payload(payloads, "evidence-pack-manifest.json")
    risk_profile = require_object_payload(payloads, "model-risk-profile.json")
    explainability_methods = require_list_payload(
        payloads, "explainability-method-records.json"
    )
    validation = require_object_payload(payloads, "model-validation-record.json")
    monitoring_plan = require_object_payload(payloads, "model-monitoring-plan.json")

    require_unique_values(
        explainability_methods,
        "explainability_method_id",
        "explainability-method-records.json",
    )
    model_id = model_registry["model_id"]
    version_id = model_version["version_id"]
    for filename, record in (
        ("model-risk-profile.json", risk_profile),
        ("model-validation-record.json", validation),
        ("model-monitoring-plan.json", monitoring_plan),
    ):
        require_equal(record["model_id"], model_id, f"{filename}.model_id")
        require_equal(record["version_id"], version_id, f"{filename}.version_id")
    for index, record in enumerate(explainability_methods):
        require_equal(
            record["model_id"],
            model_id,
            f"explainability-method-records.json[{index}].model_id",
        )
        require_equal(
            record["version_id"],
            version_id,
            f"explainability-method-records.json[{index}].version_id",
        )

    require_equal(
        validation["validation_id"],
        model_version["linked_validation_record"],
        "model-validation-record.json.validation_id",
    )
    require_equal(
        monitoring_plan["risk_profile_id"],
        risk_profile["risk_profile_id"],
        "model-monitoring-plan.json.risk_profile_id",
    )
    require_equal(
        monitoring_plan["validation_id"],
        validation["validation_id"],
        "model-monitoring-plan.json.validation_id",
    )
    require_equal(
        monitoring_plan["threshold_set_id"],
        threshold_set["threshold_set_id"],
        "model-monitoring-plan.json.threshold_set_id",
    )

    known_method_ids = {
        record["explainability_method_id"] for record in explainability_methods
    }
    validation_method_ids = set(validation["explainability_method_ids"])
    monitoring_method_ids = set(monitoring_plan["explainability_method_ids"])
    unknown_validation_ids = sorted(validation_method_ids - known_method_ids)
    if unknown_validation_ids:
        raise ValueError(
            "model-validation-record.json.explainability_method_ids references "
            "unknown value(s): " + ", ".join(unknown_validation_ids)
        )
    unknown_monitoring_ids = sorted(monitoring_method_ids - known_method_ids)
    if unknown_monitoring_ids:
        raise ValueError(
            "model-monitoring-plan.json.explainability_method_ids references "
            "unknown value(s): " + ", ".join(unknown_monitoring_ids)
        )
    if validation_method_ids != known_method_ids:
        missing = sorted(known_method_ids - validation_method_ids)
        raise ValueError(
            "model-validation-record.json.explainability_method_ids must cover every "
            "method record; missing: " + ", ".join(missing)
        )
    if monitoring_method_ids != known_method_ids:
        missing = sorted(known_method_ids - monitoring_method_ids)
        raise ValueError(
            "model-monitoring-plan.json.explainability_method_ids must cover every "
            "method record; missing: " + ", ".join(missing)
        )

    manifest_references = set(manifest["input_references"])
    missing_manifest_references = sorted(
        OPTIONAL_GOVERNANCE_FILENAMES - manifest_references
    )
    if missing_manifest_references:
        raise ValueError(
            "evidence-pack-manifest.json.input_references must include governance "
            "bundle file(s): " + ", ".join(missing_manifest_references)
        )
    for reference in validation["evidence_references"]:
        if not (dataset_dir / reference).is_file():
            raise ValueError(
                "model-validation-record.json.evidence_references missing file: "
                + reference
            )
    for index, method in enumerate(explainability_methods):
        for reference in method["validation_test_references"]:
            if resolve_dataset_reference(dataset_dir, reference) is None:
                raise ValueError(
                    "explainability-method-records.json"
                    f"[{index}].validation_test_references missing file: {reference}"
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


def require_unique_values(records: list[dict[str, Any]], field: str, filename: str) -> None:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for record in records:
        value = record[field]
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        duplicate_values = ", ".join(str(value) for value in sorted(duplicates))
        raise ValueError(f"{filename}.{field} must be unique; duplicates: {duplicate_values}")


def require_unique_pairs(
    records: list[dict[str, Any]],
    first_field: str,
    second_field: str,
    filename: str,
) -> None:
    seen: set[tuple[Any, Any]] = set()
    duplicates: set[tuple[Any, Any]] = set()
    for record in records:
        pair = (record[first_field], record[second_field])
        if pair in seen:
            duplicates.add(pair)
        seen.add(pair)
    if duplicates:
        duplicate_values = ", ".join(
            f"({first}, {second})" for first, second in sorted(duplicates)
        )
        raise ValueError(
            f"{filename}.{first_field}/{second_field} pairs must be unique; duplicates: {duplicate_values}"
        )


def validate_application_decision_business_rules(record: dict[str, Any], index: int) -> None:
    underwriting = record["underwriting"]
    monitoring = record["monitoring"]
    overlap = sorted(set(underwriting) & set(monitoring))
    if overlap:
        raise ValueError(
            f"application_decision_records[{index}] mixes underwriting and monitoring fields: "
            + ", ".join(overlap)
        )
    decision_component = record.get("decision_component")
    failed_components = record.get("failed_components")
    if decision_component == "combined" and not failed_components:
        raise ValueError(
            f"application_decision_records[{index}] combined decision requires failed_components"
        )
    if decision_component != "combined" and failed_components is not None:
        raise ValueError(
            f"application_decision_records[{index}] failed_components is only valid for combined decisions"
        )


def validate_rendered_notice_records(dataset_path: Path, payloads: dict[str, Any]) -> None:
    """Validate the optional synthetic rendered-notice input and its links."""
    payload = load_json(dataset_path)
    if not isinstance(payload, list) or not payload:
        raise ValueError("must contain a non-empty array")
    schema = load_schema("rendered-adverse-action-notice.schema.json")
    decisions_by_id = {
        record["decision_id"]
        for record in require_list_payload(payloads, "application-decision-records.json")
    }
    outputs_by_id = {
        record["reason_output_id"]: record
        for record in require_list_payload(payloads, "adverse-action-reason-outputs.json")
    }
    notice_decision_ids: set[str] = set()
    for index, record in enumerate(payload):
        validate_object(record, schema, f"rendered_adverse_action_notices[{index}]")
        decision_id = record["decision_id"]
        if decision_id not in decisions_by_id:
            raise ValueError(f"rendered_adverse_action_notices[{index}].decision_id references unknown value: {decision_id}")
        if decision_id in notice_decision_ids:
            raise ValueError(
                f"rendered_adverse_action_notices[{index}].decision_id has more than one rendered notice"
            )
        notice_decision_ids.add(decision_id)
        segment_ids: set[str] = set()
        for segment_index, segment in enumerate(record["rendered_reason_segments"]):
            reason_output_id = segment["reason_output_id"]
            if reason_output_id in segment_ids:
                raise ValueError(
                    f"rendered_adverse_action_notices[{index}].rendered_reason_segments[{segment_index}].reason_output_id is duplicated"
                )
            segment_ids.add(reason_output_id)
            output = outputs_by_id.get(reason_output_id)
            if output is None:
                raise ValueError(
                    f"rendered_adverse_action_notices[{index}].rendered_reason_segments[{segment_index}].reason_output_id references unknown value: {reason_output_id}"
                )
            if output["decision_id"] != decision_id:
                raise ValueError(
                    f"rendered_adverse_action_notices[{index}].rendered_reason_segments[{segment_index}] belongs to a different decision"
                )
