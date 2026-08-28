"""Typed contracts for the separate, reviewer-facing recourse sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .models import (
    BaseRecord,
    require_finite_number,
    require_non_empty_string,
    require_positive_integer,
    require_string_list,
    require_type,
)


def require_boolean(value: Any, field: str) -> bool:
    require_type(value, bool, field)
    return value


def require_nonnegative_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must not be negative")
    return value


def require_object_list(
    value: Any, field: str, *, allow_empty: bool = False
) -> list[dict[str, Any]]:
    require_type(value, list, field)
    if not value and not allow_empty:
        raise ValueError(f"{field} must contain at least one item")
    for index, item in enumerate(value):
        require_type(item, dict, f"{field}[{index}]")
    return value


def require_maybe_empty_string_list(value: Any, field: str) -> list[str]:
    require_type(value, list, field)
    cleaned = [
        require_non_empty_string(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{field} must not contain duplicates")
    return cleaned


def require_unique_object_field(
    records: list[dict[str, Any]], field: str, collection: str
) -> None:
    values = [require_non_empty_string(record.get(field), f"{collection}.{field}") for record in records]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(
            f"{collection}.{field} must be unique; duplicates: {', '.join(duplicates)}"
        )


@dataclass(slots=True)
class RecourseSubjectRecord(BaseRecord):
    recourse_subject_id: str
    decision_id: str
    model_id: str
    version_id: str
    feature_schema_version: str
    feature_values: list[dict[str, Any]]
    source_class: str
    provenance_note: str
    assessment_scope: str
    exclusion_reason: str | None
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecourseSubjectRecord":
        feature_values = require_object_list(payload.get("feature_values"), "feature_values")
        require_unique_object_field(feature_values, "feature_name", "feature_values")
        for index, item in enumerate(feature_values):
            require_finite_number(item.get("value"), f"feature_values[{index}].value")
        assessment_scope = require_non_empty_string(
            payload.get("assessment_scope"), "assessment_scope"
        )
        exclusion_reason = payload.get("exclusion_reason")
        if exclusion_reason is not None:
            exclusion_reason = require_non_empty_string(
                exclusion_reason, "exclusion_reason", 10
            )
        if assessment_scope == "excluded" and exclusion_reason is None:
            raise ValueError("excluded subject requires exclusion_reason")
        if assessment_scope == "eligible" and exclusion_reason is not None:
            raise ValueError("eligible subject must not include exclusion_reason")
        return cls(
            **cls._base_kwargs(payload),
            recourse_subject_id=require_non_empty_string(
                payload.get("recourse_subject_id"), "recourse_subject_id", 3
            ),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            feature_schema_version=require_non_empty_string(
                payload.get("feature_schema_version"), "feature_schema_version", 3
            ),
            feature_values=feature_values,
            source_class=require_non_empty_string(payload.get("source_class"), "source_class", 3),
            provenance_note=require_non_empty_string(
                payload.get("provenance_note"), "provenance_note", 15
            ),
            assessment_scope=assessment_scope,
            exclusion_reason=exclusion_reason,
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class RecourseMethodRecord(BaseRecord):
    recourse_method_id: str
    method_version: str
    method_name: str
    method_family: str
    implementation_reference: str
    source_citations: list[str]
    calculation_mode: str
    target_outcome_interpretation: str
    single_feature_action_treatment: str
    linked_change_treatment: str
    randomness_policy: str
    validation_references: list[str]
    known_limitations: list[str]
    owner: str
    status: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecourseMethodRecord":
        return cls(
            **cls._base_kwargs(payload),
            recourse_method_id=require_non_empty_string(
                payload.get("recourse_method_id"), "recourse_method_id", 3
            ),
            method_version=require_non_empty_string(
                payload.get("method_version"), "method_version", 3
            ),
            method_name=require_non_empty_string(payload.get("method_name"), "method_name", 5),
            method_family=require_non_empty_string(
                payload.get("method_family"), "method_family", 5
            ),
            implementation_reference=require_non_empty_string(
                payload.get("implementation_reference"), "implementation_reference", 5
            ),
            source_citations=require_string_list(
                payload.get("source_citations"), "source_citations"
            ),
            calculation_mode=require_non_empty_string(
                payload.get("calculation_mode"), "calculation_mode", 3
            ),
            target_outcome_interpretation=require_non_empty_string(
                payload.get("target_outcome_interpretation"),
                "target_outcome_interpretation",
                15,
            ),
            single_feature_action_treatment=require_non_empty_string(
                payload.get("single_feature_action_treatment"),
                "single_feature_action_treatment",
                15,
            ),
            linked_change_treatment=require_non_empty_string(
                payload.get("linked_change_treatment"), "linked_change_treatment", 15
            ),
            randomness_policy=require_non_empty_string(
                payload.get("randomness_policy"), "randomness_policy", 10
            ),
            validation_references=require_maybe_empty_string_list(
                payload.get("validation_references"), "validation_references"
            ),
            known_limitations=require_string_list(
                payload.get("known_limitations"), "known_limitations"
            ),
            owner=require_non_empty_string(payload.get("owner"), "owner", 3),
            status=require_non_empty_string(payload.get("status"), "status", 3),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class RecourseActionSet(BaseRecord):
    action_set_id: str
    action_set_version: str
    model_id: str
    version_id: str
    population_scope: str
    effective_date: str
    retired_date: str | None
    time_horizon: str
    source_basis: str
    reviewer_status: str
    feature_controls: list[dict[str, Any]]
    action_candidates: list[dict[str, Any]]
    joint_constraints: list[str]
    unresolved_assumptions: list[str]
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecourseActionSet":
        effective_date = require_non_empty_string(
            payload.get("effective_date"), "effective_date", 10
        )
        date.fromisoformat(effective_date)
        retired_date = payload.get("retired_date")
        if retired_date is not None:
            retired_date = require_non_empty_string(retired_date, "retired_date", 10)
            if date.fromisoformat(retired_date) < date.fromisoformat(effective_date):
                raise ValueError("retired_date must not precede effective_date")

        controls = require_object_list(payload.get("feature_controls"), "feature_controls")
        require_unique_object_field(controls, "feature_name", "feature_controls")
        for index, control in enumerate(controls):
            lower = control.get("lower_bound")
            upper = control.get("upper_bound")
            if lower is not None:
                lower = require_finite_number(lower, f"feature_controls[{index}].lower_bound")
            if upper is not None:
                upper = require_finite_number(upper, f"feature_controls[{index}].upper_bound")
            if lower is not None and upper is not None and lower > upper:
                raise ValueError(
                    f"feature_controls[{index}].lower_bound must not exceed upper_bound"
                )
            control_class = control.get("control_class")
            direction = control.get("allowed_direction")
            if control_class == "not_actionable_under_set" and direction != "not_applicable":
                raise ValueError(
                    "not_actionable_under_set feature must use not_applicable direction"
                )
            if control_class == "unknown" and direction != "unknown":
                raise ValueError("unknown feature control must use unknown direction")

        candidates = require_object_list(payload.get("action_candidates"), "action_candidates")
        require_unique_object_field(candidates, "action_id", "action_candidates")
        for index, candidate in enumerate(candidates):
            primary = require_string_list(
                candidate.get("primary_action_features"),
                f"action_candidates[{index}].primary_action_features",
            )
            state = require_object_list(
                candidate.get("resulting_feature_state"),
                f"action_candidates[{index}].resulting_feature_state",
            )
            changes = require_object_list(
                candidate.get("changes"), f"action_candidates[{index}].changes"
            )
            require_unique_object_field(
                state, "feature_name", f"action_candidates[{index}].resulting_feature_state"
            )
            require_unique_object_field(
                changes, "feature_name", f"action_candidates[{index}].changes"
            )
            primary_changes = sorted(
                change["feature_name"]
                for change in changes
                if change.get("change_role") == "primary"
            )
            if primary_changes != sorted(primary):
                raise ValueError(
                    f"action_candidates[{index}] primary_action_features must match primary changes"
                )
            for change_index, change in enumerate(changes):
                from_value = require_finite_number(
                    change.get("from_value"),
                    f"action_candidates[{index}].changes[{change_index}].from_value",
                )
                to_value = require_finite_number(
                    change.get("to_value"),
                    f"action_candidates[{index}].changes[{change_index}].to_value",
                )
                if from_value == to_value:
                    raise ValueError(
                        f"action_candidates[{index}].changes[{change_index}] must change the value"
                    )

        return cls(
            **cls._base_kwargs(payload),
            action_set_id=require_non_empty_string(
                payload.get("action_set_id"), "action_set_id", 3
            ),
            action_set_version=require_non_empty_string(
                payload.get("action_set_version"), "action_set_version", 3
            ),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            population_scope=require_non_empty_string(
                payload.get("population_scope"), "population_scope", 15
            ),
            effective_date=effective_date,
            retired_date=retired_date,
            time_horizon=require_non_empty_string(
                payload.get("time_horizon"), "time_horizon", 5
            ),
            source_basis=require_non_empty_string(
                payload.get("source_basis"), "source_basis", 15
            ),
            reviewer_status=require_non_empty_string(
                payload.get("reviewer_status"), "reviewer_status", 3
            ),
            feature_controls=controls,
            action_candidates=candidates,
            joint_constraints=require_maybe_empty_string_list(
                payload.get("joint_constraints"), "joint_constraints"
            ),
            unresolved_assumptions=require_maybe_empty_string_list(
                payload.get("unresolved_assumptions"), "unresolved_assumptions"
            ),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class RecourseReviewConfig(BaseRecord):
    recourse_run_id: str
    assessment_date: str
    model_id: str
    version_id: str
    recourse_method_id: str
    method_version: str
    action_set_id: str
    action_set_version: str
    recourse_subject_ids: list[str]
    target_prediction: str
    eligible_baseline_outcome: str
    maximum_joint_action_size: int
    maximum_evaluated_states: int
    sample_count: int | None
    seed: int | None
    fixed_finding_rule: str
    withholding_rules: list[str]
    audience: str
    output_directory_policy: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecourseReviewConfig":
        assessment_date = require_non_empty_string(
            payload.get("assessment_date"), "assessment_date", 10
        )
        date.fromisoformat(assessment_date)
        sample_count = payload.get("sample_count")
        if sample_count is not None:
            sample_count = require_positive_integer(sample_count, "sample_count")
        seed = payload.get("seed")
        if seed is not None:
            seed = require_nonnegative_integer(seed, "seed")
        return cls(
            **cls._base_kwargs(payload),
            recourse_run_id=require_non_empty_string(
                payload.get("recourse_run_id"), "recourse_run_id", 3
            ),
            assessment_date=assessment_date,
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            recourse_method_id=require_non_empty_string(
                payload.get("recourse_method_id"), "recourse_method_id", 3
            ),
            method_version=require_non_empty_string(
                payload.get("method_version"), "method_version", 3
            ),
            action_set_id=require_non_empty_string(
                payload.get("action_set_id"), "action_set_id", 3
            ),
            action_set_version=require_non_empty_string(
                payload.get("action_set_version"), "action_set_version", 3
            ),
            recourse_subject_ids=require_string_list(
                payload.get("recourse_subject_ids"), "recourse_subject_ids"
            ),
            target_prediction=require_non_empty_string(
                payload.get("target_prediction"), "target_prediction", 3
            ),
            eligible_baseline_outcome=require_non_empty_string(
                payload.get("eligible_baseline_outcome"), "eligible_baseline_outcome", 3
            ),
            maximum_joint_action_size=require_positive_integer(
                payload.get("maximum_joint_action_size"), "maximum_joint_action_size"
            ),
            maximum_evaluated_states=require_positive_integer(
                payload.get("maximum_evaluated_states"), "maximum_evaluated_states"
            ),
            sample_count=sample_count,
            seed=seed,
            fixed_finding_rule=require_non_empty_string(
                payload.get("fixed_finding_rule"), "fixed_finding_rule", 3
            ),
            withholding_rules=require_string_list(
                payload.get("withholding_rules"), "withholding_rules"
            ),
            audience=require_non_empty_string(payload.get("audience"), "audience", 3),
            output_directory_policy=require_non_empty_string(
                payload.get("output_directory_policy"), "output_directory_policy", 10
            ),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class SyntheticPredictionModel(BaseRecord):
    model_id: str
    version_id: str
    provider_type: str
    ordered_features: list[str]
    intercept: float
    coefficients: list[dict[str, Any]]
    threshold: float
    threshold_comparison: str
    target_label: str
    non_target_label: str
    implementation_version: str
    synthetic_only: bool
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SyntheticPredictionModel":
        ordered_features = require_string_list(
            payload.get("ordered_features"), "ordered_features"
        )
        coefficients = require_object_list(payload.get("coefficients"), "coefficients")
        require_unique_object_field(coefficients, "feature_name", "coefficients")
        coefficient_names = [item["feature_name"] for item in coefficients]
        if coefficient_names != ordered_features:
            raise ValueError("coefficient order must exactly match ordered_features")
        for index, item in enumerate(coefficients):
            require_finite_number(item.get("weight"), f"coefficients[{index}].weight")
        target_label = require_non_empty_string(
            payload.get("target_label"), "target_label", 3
        )
        non_target_label = require_non_empty_string(
            payload.get("non_target_label"), "non_target_label", 3
        )
        if target_label == non_target_label:
            raise ValueError("target_label and non_target_label must differ")
        synthetic_only = require_boolean(payload.get("synthetic_only"), "synthetic_only")
        if not synthetic_only:
            raise ValueError("first-release prediction provider must be synthetic_only")
        return cls(
            **cls._base_kwargs(payload),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            provider_type=require_non_empty_string(
                payload.get("provider_type"), "provider_type", 3
            ),
            ordered_features=ordered_features,
            intercept=require_finite_number(payload.get("intercept"), "intercept"),
            coefficients=coefficients,
            threshold=require_finite_number(payload.get("threshold"), "threshold"),
            threshold_comparison=require_non_empty_string(
                payload.get("threshold_comparison"), "threshold_comparison", 3
            ),
            target_label=target_label,
            non_target_label=non_target_label,
            implementation_version=require_non_empty_string(
                payload.get("implementation_version"), "implementation_version", 3
            ),
            synthetic_only=synthetic_only,
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )


@dataclass(slots=True)
class RecourseAssessmentOutput(BaseRecord):
    recourse_assessment_id: str
    recourse_run_id: str
    recourse_subject_id: str
    decision_id: str
    model_id: str
    version_id: str
    recourse_method_id: str
    method_version: str
    action_set_id: str
    action_set_version: str
    input_fingerprints: dict[str, Any]
    baseline_prediction: str
    target_prediction: str
    overall_status: str
    feature_results: list[dict[str, Any]]
    identified_paths: list[dict[str, Any]]
    search: dict[str, Any]
    uncertainty_reasons: list[str]
    withholding_reasons: list[str]
    limitation_references: list[str]
    reviewer_disposition: str
    audience: str
    result_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecourseAssessmentOutput":
        feature_results = require_object_list(payload.get("feature_results"), "feature_results")
        require_unique_object_field(feature_results, "feature_name", "feature_results")
        for index, result in enumerate(feature_results):
            evaluated = require_nonnegative_integer(
                result.get("evaluated_intervention_count"),
                f"feature_results[{index}].evaluated_intervention_count",
            )
            reaching = require_nonnegative_integer(
                result.get("target_reaching_count"),
                f"feature_results[{index}].target_reaching_count",
            )
            if reaching > evaluated:
                raise ValueError(
                    f"feature_results[{index}].target_reaching_count must not exceed evaluated count"
                )
            defined = require_boolean(
                result.get("responsiveness_defined"),
                f"feature_results[{index}].responsiveness_defined",
            )
            estimate = result.get("responsiveness_estimate")
            if defined and estimate is None:
                raise ValueError(
                    f"feature_results[{index}] defined responsiveness requires an estimate"
                )
            if not defined and estimate is not None:
                raise ValueError(
                    f"feature_results[{index}] undefined responsiveness must omit its estimate"
                )
            if estimate is not None:
                estimate = require_finite_number(
                    estimate, f"feature_results[{index}].responsiveness_estimate"
                )
                if not 0 <= estimate <= 1:
                    raise ValueError(
                        f"feature_results[{index}].responsiveness_estimate must be between zero and one"
                    )
        paths = require_object_list(
            payload.get("identified_paths"), "identified_paths", allow_empty=True
        )
        input_fingerprints = payload.get("input_fingerprints")
        require_type(input_fingerprints, dict, "input_fingerprints")
        search = payload.get("search")
        require_type(search, dict, "search")
        require_boolean(search.get("exhaustive"), "search.exhaustive")
        evaluated_states = require_nonnegative_integer(
            search.get("evaluated_state_count"), "search.evaluated_state_count"
        )
        available_states = require_nonnegative_integer(
            search.get("available_state_count"), "search.available_state_count"
        )
        computational_limit = require_positive_integer(
            search.get("computational_limit"), "search.computational_limit"
        )
        require_positive_integer(
            search.get("maximum_joint_action_size"),
            "search.maximum_joint_action_size",
        )
        if search.get("seed") is not None:
            require_nonnegative_integer(search["seed"], "search.seed")
        if evaluated_states > available_states:
            raise ValueError("search.evaluated_state_count must not exceed available states")
        if evaluated_states > computational_limit:
            raise ValueError("search.evaluated_state_count must not exceed computational limit")
        status = require_non_empty_string(payload.get("overall_status"), "overall_status", 3)
        if status == "fixed_under_declared_action_set" and not search.get("exhaustive"):
            raise ValueError("fixed_under_declared_action_set requires exhaustive search")
        if status == "single_feature_path_identified" and not any(
            len(path.get("primary_action_features", [])) == 1 for path in paths
        ):
            raise ValueError("single-feature status requires a single-feature target path")
        if status == "joint_path_only_identified":
            if not paths or any(len(path.get("primary_action_features", [])) == 1 for path in paths):
                raise ValueError("joint-only status requires only joint target paths")
        if status in {
            "fixed_under_declared_action_set",
            "no_target_path_found_within_search",
            "not_assessed",
        } and paths:
            raise ValueError(f"{status} must not include identified paths")
        return cls(
            **cls._base_kwargs(payload),
            recourse_assessment_id=require_non_empty_string(
                payload.get("recourse_assessment_id"), "recourse_assessment_id", 3
            ),
            recourse_run_id=require_non_empty_string(
                payload.get("recourse_run_id"), "recourse_run_id", 3
            ),
            recourse_subject_id=require_non_empty_string(
                payload.get("recourse_subject_id"), "recourse_subject_id", 3
            ),
            decision_id=require_non_empty_string(payload.get("decision_id"), "decision_id", 3),
            model_id=require_non_empty_string(payload.get("model_id"), "model_id", 3),
            version_id=require_non_empty_string(payload.get("version_id"), "version_id", 3),
            recourse_method_id=require_non_empty_string(
                payload.get("recourse_method_id"), "recourse_method_id", 3
            ),
            method_version=require_non_empty_string(
                payload.get("method_version"), "method_version", 3
            ),
            action_set_id=require_non_empty_string(
                payload.get("action_set_id"), "action_set_id", 3
            ),
            action_set_version=require_non_empty_string(
                payload.get("action_set_version"), "action_set_version", 3
            ),
            input_fingerprints=input_fingerprints,
            baseline_prediction=require_non_empty_string(
                payload.get("baseline_prediction"), "baseline_prediction", 3
            ),
            target_prediction=require_non_empty_string(
                payload.get("target_prediction"), "target_prediction", 3
            ),
            overall_status=status,
            feature_results=feature_results,
            identified_paths=paths,
            search=search,
            uncertainty_reasons=require_maybe_empty_string_list(
                payload.get("uncertainty_reasons"), "uncertainty_reasons"
            ),
            withholding_reasons=require_maybe_empty_string_list(
                payload.get("withholding_reasons"), "withholding_reasons"
            ),
            limitation_references=require_string_list(
                payload.get("limitation_references"), "limitation_references"
            ),
            reviewer_disposition=require_non_empty_string(
                payload.get("reviewer_disposition"), "reviewer_disposition", 3
            ),
            audience=require_non_empty_string(payload.get("audience"), "audience", 3),
            result_type=require_non_empty_string(payload.get("result_type"), "result_type", 10),
        )
