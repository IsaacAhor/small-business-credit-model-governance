"""Validate and execute the separate synthetic recourse-assessment sidecar."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from .schemas.recourse_models import (
    RecourseActionSet,
    RecourseAssessmentOutput,
    RecourseMethodRecord,
    RecourseReviewConfig,
    RecourseSubjectRecord,
    SyntheticPredictionModel,
)
from .schemas.validators import (
    ValidationResult,
    load_json,
    load_schema,
    validate_dataset,
    validate_record,
)


@dataclass(frozen=True, slots=True)
class RecourseSchemaSpec:
    filename: str
    schema_file: str
    model_factory: Callable[[dict[str, Any]], Any]
    collection: bool


RECOURSE_SCHEMA_SPECS: tuple[RecourseSchemaSpec, ...] = (
    RecourseSchemaSpec(
        "recourse-subject-records.json",
        "recourse-subject-record.schema.json",
        RecourseSubjectRecord.from_dict,
        True,
    ),
    RecourseSchemaSpec(
        "recourse-method-record.json",
        "recourse-method-record.schema.json",
        RecourseMethodRecord.from_dict,
        False,
    ),
    RecourseSchemaSpec(
        "recourse-action-set.json",
        "recourse-action-set.schema.json",
        RecourseActionSet.from_dict,
        False,
    ),
    RecourseSchemaSpec(
        "recourse-review-config.json",
        "recourse-review-config.schema.json",
        RecourseReviewConfig.from_dict,
        False,
    ),
    RecourseSchemaSpec(
        "synthetic-prediction-model.json",
        "synthetic-prediction-model.schema.json",
        SyntheticPredictionModel.from_dict,
        False,
    ),
)

RECOURSE_INPUT_FILENAMES = tuple(spec.filename for spec in RECOURSE_SCHEMA_SPECS)
OPTIONAL_OUTPUT_FIXTURE_FILENAME = "recourse-assessment-output.json"
PROTECTED_CORE_FILENAMES = (
    "application-decision-records.json",
    "adverse-action-driver-contributions.json",
    "reason-code-mappings.json",
    "adverse-action-reason-outputs.json",
    "rendered-adverse-action-notices.json",
)
SUPPORTED_CALCULATION_MODES = {"exhaustive_enumeration", "bounded_enumeration"}


def canonical_json_sha256(payload: Any) -> str:
    content = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_core_hashes(core_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for filename in PROTECTED_CORE_FILENAMES:
        path = core_dir / filename
        if not path.is_file():
            raise ValueError(f"protected core file is missing: {filename}")
        hashes[filename] = sha256_file(path)
    return hashes


def _records(payload: Any, filename: str, *, collection: bool) -> list[dict[str, Any]]:
    if collection:
        if not isinstance(payload, list):
            raise ValueError(f"{filename} must contain an array")
        if not payload:
            raise ValueError(f"{filename} must contain at least one record")
        return payload
    if not isinstance(payload, dict):
        raise ValueError(f"{filename} must contain an object")
    return [payload]


def _require_unique(records: list[dict[str, Any]], field: str, filename: str) -> None:
    values = [record[field] for record in records]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"{filename}.{field} must be unique; duplicates: {', '.join(duplicates)}")


def _feature_map(records: list[dict[str, Any]]) -> dict[str, float]:
    return {item["feature_name"]: float(item["value"]) for item in records}


def predict_synthetic(
    prediction_model: dict[str, Any], feature_values: list[dict[str, Any]]
) -> str:
    """Return a deterministic label from the transparent synthetic provider."""
    values = _feature_map(feature_values)
    ordered = prediction_model["ordered_features"]
    if list(values) != ordered:
        raise ValueError("feature order does not match synthetic prediction model")
    weights = {
        item["feature_name"]: float(item["weight"])
        for item in prediction_model["coefficients"]
    }
    score = float(prediction_model["intercept"]) + sum(
        weights[name] * values[name] for name in ordered
    )
    if score >= float(prediction_model["threshold"]):
        return prediction_model["target_label"]
    return prediction_model["non_target_label"]


def load_recourse_payloads(recourse_dir: Path) -> dict[str, Any]:
    return {
        filename: load_json(recourse_dir / filename)
        for filename in RECOURSE_INPUT_FILENAMES
    }


def _validate_change_direction(
    *,
    control: dict[str, Any],
    from_value: float,
    to_value: float,
    field: str,
) -> None:
    direction = control["allowed_direction"]
    if direction == "increase" and to_value <= from_value:
        raise ValueError(f"{field} must increase under the declared feature control")
    if direction == "decrease" and to_value >= from_value:
        raise ValueError(f"{field} must decrease under the declared feature control")
    if direction in {"not_applicable", "unknown"}:
        raise ValueError(f"{field} is not permitted by the declared feature control")
    lower = control.get("lower_bound")
    upper = control.get("upper_bound")
    if lower is not None and to_value < float(lower):
        raise ValueError(f"{field} falls below the declared lower bound")
    if upper is not None and to_value > float(upper):
        raise ValueError(f"{field} exceeds the declared upper bound")
    allowed_values = control.get("allowed_values")
    if allowed_values is not None and to_value not in [float(item) for item in allowed_values]:
        raise ValueError(f"{field} is not one of the declared allowed values")


def validate_recourse_relationships(
    core_dir: Path, recourse_dir: Path, payloads: dict[str, Any]
) -> None:
    del recourse_dir  # Paths are retained in the public API for future controlled references.
    registry = load_json(core_dir / "model-registry-record.json")
    version = load_json(core_dir / "model-version-record.json")
    decisions = load_json(core_dir / "application-decision-records.json")
    subjects = payloads["recourse-subject-records.json"]
    method = payloads["recourse-method-record.json"]
    action_set = payloads["recourse-action-set.json"]
    config = payloads["recourse-review-config.json"]
    prediction_model = payloads["synthetic-prediction-model.json"]

    if len(subjects) != 1:
        raise ValueError(
            "first-release recourse bundles must contain exactly one subject because "
            "declared action candidates are baseline-specific"
        )
    _require_unique(subjects, "recourse_subject_id", "recourse-subject-records.json")
    _require_unique(subjects, "decision_id", "recourse-subject-records.json")
    decision_by_id = {record["decision_id"]: record for record in decisions}
    subject_ids = [record["recourse_subject_id"] for record in subjects]
    if config["recourse_subject_ids"] != subject_ids:
        raise ValueError(
            "recourse-review-config.json.recourse_subject_ids must exactly match subject record order"
        )

    model_id = registry["model_id"]
    version_id = version["version_id"]
    if version["model_id"] != model_id:
        raise ValueError("core model registry and version context are inconsistent")
    for label, record in (
        ("recourse action set", action_set),
        ("recourse review config", config),
        ("synthetic prediction model", prediction_model),
    ):
        if record["model_id"] != model_id or record["version_id"] != version_id:
            raise ValueError(f"{label} references an unknown model or version")
    if config["recourse_method_id"] != method["recourse_method_id"]:
        raise ValueError("recourse review config references an unknown method")
    if config["method_version"] != method["method_version"]:
        raise ValueError("recourse review config method version mismatch")
    if config["action_set_id"] != action_set["action_set_id"]:
        raise ValueError("recourse review config references an unknown action set")
    if config["action_set_version"] != action_set["action_set_version"]:
        raise ValueError("recourse review config action-set version mismatch")
    if method["calculation_mode"] not in SUPPORTED_CALCULATION_MODES:
        raise ValueError(
            "first-release provider supports only exhaustive_enumeration or bounded_enumeration"
        )
    if config["target_prediction"] != prediction_model["target_label"]:
        raise ValueError("review target must match the synthetic model target label")
    if config["eligible_baseline_outcome"] != prediction_model["non_target_label"]:
        raise ValueError("eligible baseline outcome must match the synthetic model non-target label")

    ordered_features = prediction_model["ordered_features"]
    controls = action_set["feature_controls"]
    control_names = [item["feature_name"] for item in controls]
    if control_names != ordered_features:
        raise ValueError("action-set feature controls must exactly match model feature order")
    control_by_name = {item["feature_name"]: item for item in controls}

    for subject_index, subject in enumerate(subjects):
        if subject["decision_id"] not in decision_by_id:
            raise ValueError(
                f"recourse-subject-records.json[{subject_index}].decision_id references an unknown decision"
            )
        if subject["model_id"] != model_id or subject["version_id"] != version_id:
            raise ValueError(
                f"recourse-subject-records.json[{subject_index}] references an unknown model or version"
            )
        if subject["feature_schema_version"] != prediction_model["feature_schema_version"]:
            raise ValueError(
                f"recourse-subject-records.json[{subject_index}] feature schema version mismatch"
            )
        subject_names = [item["feature_name"] for item in subject["feature_values"]]
        if subject_names != ordered_features:
            raise ValueError(
                f"recourse-subject-records.json[{subject_index}] feature order must match the model"
            )
        baseline = _feature_map(subject["feature_values"])
        for action_index, candidate in enumerate(action_set["action_candidates"]):
            prefix = f"recourse-action-set.json.action_candidates[{action_index}]"
            state_names = [
                item["feature_name"] for item in candidate["resulting_feature_state"]
            ]
            if state_names != ordered_features:
                raise ValueError(f"{prefix}.resulting_feature_state must be a full ordered feature state")
            state = _feature_map(candidate["resulting_feature_state"])
            changes = {item["feature_name"]: item for item in candidate["changes"]}
            unknown_changes = sorted(set(changes) - set(ordered_features))
            if unknown_changes:
                raise ValueError(f"{prefix}.changes references unknown features: {', '.join(unknown_changes)}")
            for feature_name in ordered_features:
                if feature_name in changes:
                    change = changes[feature_name]
                    if float(change["from_value"]) != baseline[feature_name]:
                        raise ValueError(f"{prefix}.changes.{feature_name}.from_value does not match subject baseline")
                    if float(change["to_value"]) != state[feature_name]:
                        raise ValueError(f"{prefix}.changes.{feature_name}.to_value does not match resulting state")
                    control = control_by_name[feature_name]
                    if change["change_role"] == "primary" and control["control_class"] not in {
                        "directly_actionable",
                        "conditionally_actionable",
                    }:
                        raise ValueError(f"{prefix} uses a non-actionable feature as a primary action")
                    if change["change_role"] == "linked_downstream" and control["control_class"] not in {
                        "derived_or_downstream",
                        "conditionally_actionable",
                    }:
                        raise ValueError(f"{prefix} linked change lacks a downstream or conditional control class")
                    _validate_change_direction(
                        control=control,
                        from_value=baseline[feature_name],
                        to_value=state[feature_name],
                        field=f"{prefix}.changes.{feature_name}",
                    )
                elif state[feature_name] != baseline[feature_name]:
                    raise ValueError(f"{prefix} changes {feature_name} without a declared delta")


def validate_recourse_baselines(core_dir: Path, payloads: dict[str, Any]) -> None:
    decisions = {
        record["decision_id"]: record
        for record in load_json(core_dir / "application-decision-records.json")
    }
    config = payloads["recourse-review-config.json"]
    model = payloads["synthetic-prediction-model.json"]
    for index, subject in enumerate(payloads["recourse-subject-records.json"]):
        predicted = predict_synthetic(model, subject["feature_values"])
        recorded = decisions[subject["decision_id"]]["decision_outcome"]
        if recorded != config["eligible_baseline_outcome"]:
            raise ValueError(
                f"recourse-subject-records.json[{index}] decision outcome is not the configured eligible baseline"
            )
        if predicted != recorded:
            raise ValueError(
                f"recourse-subject-records.json[{index}] baseline prediction mismatch: model={predicted}, recorded={recorded}"
            )


def validate_recourse_output_record(payload: dict[str, Any]) -> None:
    validate_record(
        payload,
        load_schema("recourse-assessment-output.schema.json"),
        RecourseAssessmentOutput.from_dict,
    )


def validate_recourse_bundle(recourse_dir: Path, core_dir: Path) -> ValidationResult:
    recourse_dir = recourse_dir.resolve()
    core_dir = core_dir.resolve()
    errors: list[str] = []
    validated_files: list[str] = []
    payloads: dict[str, Any] = {}
    output_fixture_records: list[dict[str, Any]] | None = None

    core_result = validate_dataset(core_dir)
    if not core_result.ok:
        errors.extend("core dataset: " + error for error in core_result.errors)
    else:
        validated_files.extend("core:" + name for name in core_result.validated_files)
        try:
            protected_core_hashes(core_dir)
        except ValueError as exc:
            errors.append(f"core dataset: {exc}")

    for spec in RECOURSE_SCHEMA_SPECS:
        path = recourse_dir / spec.filename
        if not path.is_file():
            errors.append(f"Missing recourse bundle file: {spec.filename}")
            continue
        try:
            payload = load_json(path)
            records = _records(payload, spec.filename, collection=spec.collection)
            schema = load_schema(spec.schema_file)
            for record in records:
                validate_record(record, schema, spec.model_factory)
            payloads[spec.filename] = payload
            validated_files.append(spec.filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{spec.filename}: {exc}")

    output_fixture = recourse_dir / OPTIONAL_OUTPUT_FIXTURE_FILENAME
    if output_fixture.is_file():
        try:
            payload = load_json(output_fixture)
            records = payload if isinstance(payload, list) else [payload]
            for record in records:
                validate_recourse_output_record(record)
            output_fixture_records = records
            validated_files.append(OPTIONAL_OUTPUT_FIXTURE_FILENAME)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{OPTIONAL_OUTPUT_FIXTURE_FILENAME}: {exc}")

    if not errors:
        try:
            validate_recourse_relationships(core_dir, recourse_dir, payloads)
            validate_recourse_baselines(core_dir, payloads)
            if output_fixture_records is not None:
                expected_outputs = _assess_recourse_validated(core_dir, payloads)
                if output_fixture_records != expected_outputs:
                    raise ValueError(
                        "recourse-assessment-output.json does not match recomputed bundle results"
                    )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"recourse relationships: {exc}")
    return ValidationResult(
        ok=not errors,
        dataset_dir=str(recourse_dir),
        validated_files=validated_files,
        errors=errors,
    )


def _base_uncertainties(
    method: dict[str, Any], action_set: dict[str, Any], config: dict[str, Any]
) -> list[str]:
    uncertainties: list[str] = []
    assessment_date = date.fromisoformat(config["assessment_date"])
    if assessment_date < date.fromisoformat(action_set["effective_date"]):
        uncertainties.append("The action set was not effective on the assessment date.")
    retired_date = action_set.get("retired_date")
    if retired_date is not None and assessment_date > date.fromisoformat(retired_date):
        uncertainties.append("The action set was retired before the assessment date.")
    if method["status"] != "approved_for_synthetic_review":
        uncertainties.append("The recourse method is not approved for synthetic review.")
    if action_set["reviewer_status"] != "synthetic_demonstration_only":
        uncertainties.append("The action set does not have the expected synthetic-demonstration status.")
    uncertainties.extend(action_set["unresolved_assumptions"])
    unknown_features = sorted(
        control["feature_name"]
        for control in action_set["feature_controls"]
        if control["control_class"] == "unknown"
    )
    if unknown_features:
        uncertainties.append(
            "Unknown actionability remains for features: " + ", ".join(unknown_features) + "."
        )
    unknown_actions = sorted(
        action["action_id"]
        for action in action_set["action_candidates"]
        if action["feasibility_status"] == "unknown"
    )
    if unknown_actions:
        uncertainties.append(
            "Unknown feasibility remains for action candidates: " + ", ".join(unknown_actions) + "."
        )
    if config["fixed_finding_rule"] == "documented_certificate_required":
        uncertainties.append("No separate fixed-state certificate is supported by this provider.")
    return uncertainties


def _feature_results(
    controls: list[dict[str, Any]],
    evaluated: list[tuple[dict[str, Any], str]],
    target_prediction: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for control in controls:
        feature_name = control["feature_name"]
        single_feature_actions = [
            (candidate, prediction)
            for candidate, prediction in evaluated
            if candidate["primary_action_features"] == [feature_name]
        ]
        evaluated_count = len(single_feature_actions)
        target_count = sum(
            prediction == target_prediction for _, prediction in single_feature_actions
        )
        result: dict[str, Any] = {
            "feature_name": feature_name,
            "control_class": control["control_class"],
            "evaluated_intervention_count": evaluated_count,
            "target_reaching_count": target_count,
            "responsiveness_defined": evaluated_count > 0,
        }
        if evaluated_count:
            result["responsiveness_estimate"] = target_count / evaluated_count
        results.append(result)
    return results


def _assess_recourse_validated(
    core_dir: Path, payloads: dict[str, Any]
) -> list[dict[str, Any]]:
    """Assess payloads that already passed bundle and baseline validation."""
    subjects = payloads["recourse-subject-records.json"]
    method = payloads["recourse-method-record.json"]
    action_set = payloads["recourse-action-set.json"]
    config = payloads["recourse-review-config.json"]
    prediction_model = payloads["synthetic-prediction-model.json"]
    base_uncertainties = _base_uncertainties(method, action_set, config)

    method_hash = canonical_json_sha256(method)
    action_set_hash = canonical_json_sha256(action_set)
    config_hash = canonical_json_sha256(config)
    model_hash = canonical_json_sha256(prediction_model)
    supported_candidates = sorted(
        (
            candidate
            for candidate in action_set["action_candidates"]
            if candidate["feasibility_status"]
            == "supported_by_declared_synthetic_assumption"
        ),
        key=lambda item: (len(item["primary_action_features"]), item["action_id"]),
    )
    outputs: list[dict[str, Any]] = []
    for subject in subjects:
        baseline_prediction = predict_synthetic(
            prediction_model, subject["feature_values"]
        )
        fingerprints = {
            "subject_sha256": canonical_json_sha256(subject),
            "method_sha256": method_hash,
            "action_set_sha256": action_set_hash,
            "review_config_sha256": config_hash,
            "prediction_model_sha256": model_hash,
        }
        if subject["assessment_scope"] == "excluded":
            output = {
                "record_type": "recourse_assessment_output",
                "recourse_assessment_id": "rca-" + subject["recourse_subject_id"][4:],
                "recourse_run_id": config["recourse_run_id"],
                "recourse_subject_id": subject["recourse_subject_id"],
                "decision_id": subject["decision_id"],
                "model_id": config["model_id"],
                "version_id": config["version_id"],
                "recourse_method_id": config["recourse_method_id"],
                "method_version": config["method_version"],
                "action_set_id": config["action_set_id"],
                "action_set_version": config["action_set_version"],
                "input_fingerprints": fingerprints,
                "baseline_prediction": baseline_prediction,
                "target_prediction": config["target_prediction"],
                "overall_status": "not_assessed",
                "feature_results": _feature_results(
                    action_set["feature_controls"], [], config["target_prediction"]
                ),
                "identified_paths": [],
                "search": {
                    "calculation_mode": method["calculation_mode"],
                    "exhaustive": False,
                    "single_feature_search_exhaustive": False,
                    "evaluated_state_count": 0,
                    "available_state_count": len(supported_candidates),
                    "computational_limit": config["maximum_evaluated_states"],
                    "maximum_joint_action_size": config["maximum_joint_action_size"],
                },
                "uncertainty_reasons": base_uncertainties,
                "withholding_reasons": [subject["exclusion_reason"]],
                "limitation_references": [
                    "docs/recourse-assessment-run-kit/LIMITATIONS.md",
                    method["implementation_reference"],
                ],
                "reviewer_disposition": "not_assessed",
                "audience": "reviewer_only",
                "result_type": "recourse_assessment_not_reason_not_notice_not_outcome_guarantee",
            }
            validate_recourse_output_record(output)
            outputs.append(output)
            continue

        within_joint_bound = [
            candidate
            for candidate in supported_candidates
            if len(candidate["primary_action_features"])
            <= config["maximum_joint_action_size"]
        ]
        candidates_to_evaluate = within_joint_bound[
            : config["maximum_evaluated_states"]
        ]
        evaluated = [
            (
                candidate,
                predict_synthetic(
                    prediction_model, candidate["resulting_feature_state"]
                ),
            )
            for candidate in candidates_to_evaluate
        ]
        target_paths = [
            {
                "action_id": candidate["action_id"],
                "primary_action_features": candidate["primary_action_features"],
                "evaluated_prediction": prediction,
            }
            for candidate, prediction in evaluated
            if prediction == config["target_prediction"]
        ]
        single_target_paths = [
            path for path in target_paths if len(path["primary_action_features"]) == 1
        ]
        joint_target_paths = [
            path for path in target_paths if len(path["primary_action_features"]) > 1
        ]
        supported_single_ids = {
            candidate["action_id"]
            for candidate in supported_candidates
            if len(candidate["primary_action_features"]) == 1
        }
        evaluated_ids = {candidate["action_id"] for candidate, _ in evaluated}
        single_search_exhaustive = supported_single_ids <= evaluated_ids
        exhaustive = (
            method["calculation_mode"] == "exhaustive_enumeration"
            and len(evaluated) == len(supported_candidates)
            and len(within_joint_bound) == len(supported_candidates)
            and not base_uncertainties
        )
        uncertainties = list(base_uncertainties)
        if len(evaluated) < len(supported_candidates):
            uncertainties.append(
                "Configured search bounds did not enumerate every declared supported candidate state."
            )

        if base_uncertainties:
            status = "inconclusive"
        elif single_target_paths:
            status = "single_feature_path_identified"
        elif joint_target_paths and single_search_exhaustive:
            status = "joint_path_only_identified"
        elif joint_target_paths:
            status = "inconclusive"
            uncertainties.append(
                "A joint target path was observed before single-feature exhaustion was established."
            )
        elif exhaustive and config["fixed_finding_rule"] == "exhaustive_enumeration_only":
            status = "fixed_under_declared_action_set"
        else:
            status = "no_target_path_found_within_search"

        withholding_reasons: list[str] = []
        reviewer_disposition = "pending_review"
        if status == "inconclusive":
            if "withhold_on_inconclusive" not in config["withholding_rules"]:
                raise ValueError(
                    "inconclusive result requires the configured "
                    "withhold_on_inconclusive rule"
                )
            withholding_reasons.append(
                "Uncertainty prevents a stronger reviewer finding under the declared action set."
            )
            reviewer_disposition = "withheld"
        output = {
            "record_type": "recourse_assessment_output",
            "recourse_assessment_id": "rca-" + subject["recourse_subject_id"][4:],
            "recourse_run_id": config["recourse_run_id"],
            "recourse_subject_id": subject["recourse_subject_id"],
            "decision_id": subject["decision_id"],
            "model_id": config["model_id"],
            "version_id": config["version_id"],
            "recourse_method_id": config["recourse_method_id"],
            "method_version": config["method_version"],
            "action_set_id": config["action_set_id"],
            "action_set_version": config["action_set_version"],
            "input_fingerprints": fingerprints,
            "baseline_prediction": baseline_prediction,
            "target_prediction": config["target_prediction"],
            "overall_status": status,
            "feature_results": _feature_results(
                action_set["feature_controls"], evaluated, config["target_prediction"]
            ),
            "identified_paths": target_paths,
            "search": {
                "calculation_mode": method["calculation_mode"],
                "exhaustive": exhaustive,
                "single_feature_search_exhaustive": single_search_exhaustive,
                "evaluated_state_count": len(evaluated),
                "available_state_count": len(supported_candidates),
                "computational_limit": config["maximum_evaluated_states"],
                "maximum_joint_action_size": config["maximum_joint_action_size"],
            },
            "uncertainty_reasons": uncertainties,
            "withholding_reasons": withholding_reasons,
            "limitation_references": [
                "docs/recourse-assessment-run-kit/LIMITATIONS.md",
                method["implementation_reference"],
            ],
            "reviewer_disposition": reviewer_disposition,
            "audience": "reviewer_only",
            "result_type": "recourse_assessment_not_reason_not_notice_not_outcome_guarantee",
        }
        if config.get("seed") is not None:
            output["search"]["seed"] = config["seed"]
        validate_recourse_output_record(output)
        outputs.append(output)
    return outputs


def assess_recourse(core_dir: Path, recourse_dir: Path) -> list[dict[str, Any]]:
    core_dir = core_dir.resolve()
    recourse_dir = recourse_dir.resolve()
    validation = validate_recourse_bundle(recourse_dir, core_dir)
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))
    return _assess_recourse_validated(core_dir, load_recourse_payloads(recourse_dir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a separate recourse bundle against a synthetic core dataset."
    )
    parser.add_argument("core_dataset_dir", type=Path)
    parser.add_argument("recourse_bundle_dir", type=Path)
    return parser


def validate_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_recourse_bundle(
        args.recourse_bundle_dir, args.core_dataset_dir
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(validate_main())
