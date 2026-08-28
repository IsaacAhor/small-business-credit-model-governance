from __future__ import annotations

import json
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = ROOT / "tmp" / "test-runs"
CORE_DATASET = ROOT / "data" / "synthetic" / "adverse-action-reason-benchmark"
FIXTURE_ROOT = ROOT / "data" / "synthetic" / "recourse-assessment"
CHECKED_IN_EXAMPLE = ROOT / "examples" / "evidence-packs" / "recourse-assessment"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.recourse import (  # noqa: E402
    PROTECTED_CORE_FILENAMES,
    assess_recourse,
    protected_core_hashes,
    validate_main,
    validate_recourse_bundle,
    validate_recourse_output_record,
)
from credit_gov.recourse_reporting import (  # noqa: E402
    OUTPUT_FILENAMES,
    generate_recourse_evidence_pack,
    main as report_main,
    validate_distinct_paths,
    verify_recourse_evidence_pack,
)
from credit_gov.commands import main as commands_main  # noqa: E402
from credit_gov.schemas import validators  # noqa: E402
from credit_gov.schemas.validators import SCHEMA_SPECS, validate_dataset  # noqa: E402


class RecourseRunKitTests(unittest.TestCase):
    def copy_fixture(self, name: str, root: Path) -> Path:
        target = root / name
        shutil.copytree(FIXTURE_ROOT / name, target)
        return target

    def update_json(self, path: Path, mutate) -> None:  # noqa: ANN001
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_valid_and_intentionally_invalid_fixture_matrix(self) -> None:
        for name in (
            "baseline",
            "joint-only",
            "fixed-under-action-set",
            "bounded-search-inconclusive",
            "unknown-assumption-inconclusive",
        ):
            with self.subTest(name=name):
                result = validate_recourse_bundle(FIXTURE_ROOT / name, CORE_DATASET)
                self.assertTrue(result.ok, result.errors)

        expected_errors = {
            "invalid-baseline-mismatch": "baseline prediction mismatch",
            "invalid-missing-action-set-version": "action_set_version is required",
            "invalid-cross-layer-field": "unexpected field(s): reason_code",
        }
        for name, expected in expected_errors.items():
            with self.subTest(name=name):
                result = validate_recourse_bundle(FIXTURE_ROOT / name, CORE_DATASET)
                self.assertFalse(result.ok)
                self.assertTrue(any(expected in error for error in result.errors), result.errors)

    def test_status_matrix_uses_most_conservative_supported_finding(self) -> None:
        expected = {
            "baseline": "single_feature_path_identified",
            "joint-only": "joint_path_only_identified",
            "fixed-under-action-set": "fixed_under_declared_action_set",
            "bounded-search-inconclusive": "no_target_path_found_within_search",
            "unknown-assumption-inconclusive": "inconclusive",
        }
        for name, status in expected.items():
            with self.subTest(name=name):
                result = assess_recourse(CORE_DATASET, FIXTURE_ROOT / name)[0]
                self.assertEqual(status, result["overall_status"])

    def test_baseline_keeps_reason_and_recourse_questions_separate(self) -> None:
        before = json.loads(
            (CORE_DATASET / "adverse-action-reason-outputs.json").read_text(encoding="utf-8")
        )
        result = assess_recourse(CORE_DATASET, FIXTURE_ROOT / "baseline")[0]
        after = json.loads(
            (CORE_DATASET / "adverse-action-reason-outputs.json").read_text(encoding="utf-8")
        )
        by_feature = {item["feature_name"]: item for item in result["feature_results"]}
        self.assertEqual(1.0, by_feature["cash_flow_margin"]["responsiveness_estimate"])
        self.assertEqual(0.0, by_feature["debt_service_coverage"]["responsiveness_estimate"])
        self.assertEqual(before, after)
        self.assertTrue(
            any(
                item["decision_id"] == "dec-0002"
                and item["driver_or_signal"] == "debt_service_coverage"
                for item in after
            )
        )

    def test_linked_downstream_state_remains_declared_but_not_primary(self) -> None:
        action_set = json.loads(
            (FIXTURE_ROOT / "baseline" / "recourse-action-set.json").read_text(encoding="utf-8")
        )
        action = action_set["action_candidates"][0]
        self.assertEqual(["cash_flow_margin"], action["primary_action_features"])
        self.assertIn(
            {
                "feature_name": "months_in_business",
                "from_value": 18,
                "to_value": 24,
                "change_role": "linked_downstream",
            },
            action["changes"],
        )

    def test_fixed_finding_is_impossible_from_incomplete_search(self) -> None:
        fixed = assess_recourse(CORE_DATASET, FIXTURE_ROOT / "fixed-under-action-set")[0]
        bounded = assess_recourse(
            CORE_DATASET, FIXTURE_ROOT / "bounded-search-inconclusive"
        )[0]
        self.assertTrue(fixed["search"]["exhaustive"])
        self.assertEqual("fixed_under_declared_action_set", fixed["overall_status"])
        self.assertFalse(bounded["search"]["exhaustive"])
        self.assertNotEqual("fixed_under_declared_action_set", bounded["overall_status"])
        self.assertTrue(bounded["uncertainty_reasons"])

    def test_unknown_feasibility_forces_withholding(self) -> None:
        result = assess_recourse(
            CORE_DATASET, FIXTURE_ROOT / "unknown-assumption-inconclusive"
        )[0]
        self.assertEqual("inconclusive", result["overall_status"])
        self.assertEqual("withheld", result["reviewer_disposition"])
        self.assertTrue(result["withholding_reasons"])

    def test_unknown_feature_actionability_forces_inconclusive_withholding(self) -> None:
        def mark_feature_unknown(payload: dict) -> None:
            for control in payload["feature_controls"]:
                if control["feature_name"] == "debt_service_coverage":
                    control["control_class"] = "unknown"
                    control["allowed_direction"] = "unknown"
                    control.pop("lower_bound", None)
                    control.pop("upper_bound", None)
                    control.pop("allowed_values", None)
            payload["action_candidates"] = [
                action
                for action in payload["action_candidates"]
                if "debt_service_coverage" not in action["primary_action_features"]
            ]

        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))
            self.update_json(fixture / "recourse-action-set.json", mark_feature_unknown)
            result = assess_recourse(CORE_DATASET, fixture)[0]
        self.assertEqual("inconclusive", result["overall_status"])
        self.assertEqual("withheld", result["reviewer_disposition"])
        self.assertTrue(
            any(
                "Unknown actionability" in reason
                for reason in result["uncertainty_reasons"]
            )
        )

    def test_documented_exclusion_produces_not_assessed(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))
            self.update_json(
                fixture / "recourse-subject-records.json",
                lambda payload: payload[0].update(
                    {
                        "assessment_scope": "excluded",
                        "exclusion_reason": "Excluded to exercise the documented non-assessment path.",
                    }
                ),
            )
            result = assess_recourse(CORE_DATASET, fixture)[0]
        self.assertEqual("not_assessed", result["overall_status"])
        self.assertEqual("not_assessed", result["reviewer_disposition"])
        self.assertEqual(
            ["Excluded to exercise the documented non-assessment path."],
            result["withholding_reasons"],
        )
        self.assertEqual(0, result["search"]["evaluated_state_count"])

    def test_retired_action_set_forces_inconclusive_withholding(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))
            self.update_json(
                fixture / "recourse-action-set.json",
                lambda payload: payload.update(
                    {
                        "effective_date": "2026-08-25",
                        "retired_date": "2026-08-26",
                    }
                ),
            )
            result = assess_recourse(CORE_DATASET, fixture)[0]
        self.assertEqual("inconclusive", result["overall_status"])
        self.assertEqual("withheld", result["reviewer_disposition"])
        self.assertTrue(
            any("retired before" in reason for reason in result["uncertainty_reasons"])
        )

    def test_model_method_action_set_subject_and_config_mismatches_fail(self) -> None:
        mutations = (
            (
                "recourse-review-config.json",
                lambda payload: payload.update({"method_version": "rcmver-mismatch"}),
                "method version mismatch",
            ),
            (
                "recourse-review-config.json",
                lambda payload: payload.update({"action_set_version": "rasver-mismatch"}),
                "action-set version mismatch",
            ),
            (
                "recourse-subject-records.json",
                lambda payload: payload[0].update({"version_id": "ver-mismatch"}),
                "unknown model or version",
            ),
            (
                "synthetic-prediction-model.json",
                lambda payload: payload.update({"model_id": "mdl-mismatch"}),
                "unknown model or version",
            ),
            (
                "synthetic-prediction-model.json",
                lambda payload: payload.update(
                    {"feature_schema_version": "featver-mismatch"}
                ),
                "feature schema version mismatch",
            ),
        )
        for filename, mutation, expected in mutations:
            with self.subTest(filename=filename, expected=expected):
                with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
                    fixture = self.copy_fixture("baseline", Path(temporary))
                    self.update_json(fixture / filename, mutation)
                    result = validate_recourse_bundle(fixture, CORE_DATASET)
                self.assertFalse(result.ok)
                self.assertTrue(any(expected in error for error in result.errors), result.errors)

    def test_first_release_rejects_multiple_subjects_explicitly(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))

            def add_subject(payload: list[dict]) -> None:
                second = json.loads(json.dumps(payload[0]))
                second["recourse_subject_id"] = "rcs-baseline-0003"
                second["decision_id"] = "dec-0003"
                payload.append(second)

            self.update_json(fixture / "recourse-subject-records.json", add_subject)
            self.update_json(
                fixture / "recourse-review-config.json",
                lambda payload: payload["recourse_subject_ids"].append(
                    "rcs-baseline-0003"
                ),
            )
            result = validate_recourse_bundle(fixture, CORE_DATASET)
        self.assertFalse(result.ok)
        self.assertTrue(any("exactly one subject" in error for error in result.errors))

    def test_first_release_withholding_policy_is_executable_and_closed(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))
            self.update_json(
                fixture / "recourse-review-config.json",
                lambda payload: payload.update(
                    {"withholding_rules": ["withhold_on_target_path"]}
                ),
            )
            result = validate_recourse_bundle(fixture, CORE_DATASET)
        self.assertFalse(result.ok)
        self.assertTrue(any("withholding_rules" in error for error in result.errors))

    def test_sampling_and_external_provider_modes_fail_closed_in_first_build(self) -> None:
        for mode in ("sampling", "external_provider"):
            with self.subTest(mode=mode):
                with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
                    fixture = self.copy_fixture("baseline", Path(temporary))
                    self.update_json(
                        fixture / "recourse-method-record.json",
                        lambda payload, mode=mode: payload.update({"calculation_mode": mode}),
                    )
                    result = validate_recourse_bundle(fixture, CORE_DATASET)
                self.assertFalse(result.ok)
                self.assertTrue(any("first-release provider" in error for error in result.errors))

    def test_all_cross_layer_fields_are_rejected(self) -> None:
        valid = assess_recourse(CORE_DATASET, FIXTURE_ROOT / "baseline")[0]
        for field, value in {
            "reason_code": "RC-101",
            "reason_rank": 1,
            "mapping_id": "map-101",
            "mapping_version": "mapver-1",
            "disclosed_reason_text": "Example",
            "notice_template_id": "template-1",
            "notice_template_version": "template-version-1",
            "rendered_reason_text": "Example",
        }.items():
            with self.subTest(field=field):
                payload = json.loads(json.dumps(valid))
                payload[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_recourse_output_record(payload)

    def test_output_validator_rejects_internally_contradictory_fixed_record(self) -> None:
        payload = json.loads(
            json.dumps(assess_recourse(CORE_DATASET, FIXTURE_ROOT / "baseline")[0])
        )
        payload["overall_status"] = "fixed_under_declared_action_set"
        payload["identified_paths"] = []
        payload["search"]["exhaustive"] = True
        with self.assertRaisesRegex(ValueError, "target_reaching_count"):
            validate_recourse_output_record(payload)

    def test_output_validator_rejects_other_internal_contradictions(self) -> None:
        baseline = assess_recourse(CORE_DATASET, FIXTURE_ROOT / "baseline")[0]
        mutations = (
            (
                lambda payload: payload["feature_results"][0].update(
                    {"evaluated_intervention_count": 999}
                ),
                "evaluated_intervention_count",
            ),
            (
                lambda payload: payload["identified_paths"][0][
                    "primary_action_features"
                ].append("undeclared_feature"),
                "unknown feature results",
            ),
            (
                lambda payload: payload["withholding_reasons"].append(
                    "This reason contradicts a pending-review disposition."
                ),
                "pending_review disposition",
            ),
        )
        for mutation, expected in mutations:
            with self.subTest(expected=expected):
                payload = json.loads(json.dumps(baseline))
                mutation(payload)
                with self.assertRaisesRegex(ValueError, expected):
                    validate_recourse_output_record(payload)

    def test_supplied_output_fixture_must_match_recomputed_bundle(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline", Path(temporary))
            payload = assess_recourse(CORE_DATASET, fixture)
            payload[0]["recourse_run_id"] = "rcrun-structurally-valid-mismatch"
            (fixture / "recourse-assessment-output.json").write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
            result = validate_recourse_bundle(fixture, CORE_DATASET)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("does not match recomputed bundle results" in error for error in result.errors),
            result.errors,
        )

    def test_output_path_must_be_disjoint_from_both_input_trees(self) -> None:
        bundle = FIXTURE_ROOT / "baseline"
        with self.assertRaisesRegex(ValueError, "core dataset"):
            validate_distinct_paths(CORE_DATASET, bundle, CORE_DATASET / "output")
        with self.assertRaisesRegex(ValueError, "recourse bundle"):
            validate_distinct_paths(CORE_DATASET, bundle, bundle / "output")
        with self.assertRaisesRegex(ValueError, "core dataset"):
            validate_distinct_paths(CORE_DATASET, bundle, CORE_DATASET.parent)

    def test_generation_preserves_protected_core_hashes_and_exact_output_set(self) -> None:
        before = protected_core_hashes(CORE_DATASET)
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "pack"
            generate_recourse_evidence_pack(
                CORE_DATASET, FIXTURE_ROOT / "baseline", output
            )
            after = protected_core_hashes(CORE_DATASET)
            actual = sorted(path.name for path in output.iterdir() if path.is_file())
            verification = verify_recourse_evidence_pack(output)
        self.assertEqual(before, after)
        self.assertEqual(sorted(OUTPUT_FILENAMES), actual)
        self.assertTrue(verification["ok"], verification["errors"])

    def test_repeated_runs_are_byte_identical(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            generate_recourse_evidence_pack(CORE_DATASET, FIXTURE_ROOT / "baseline", first)
            generate_recourse_evidence_pack(CORE_DATASET, FIXTURE_ROOT / "baseline", second)
            first_bytes = {name: (first / name).read_bytes() for name in OUTPUT_FILENAMES}
            second_bytes = {name: (second / name).read_bytes() for name in OUTPUT_FILENAMES}
        self.assertEqual(first_bytes, second_bytes)

    def test_verifier_rejects_tampering_and_undeclared_files(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "pack"
            generate_recourse_evidence_pack(CORE_DATASET, FIXTURE_ROOT / "baseline", output)
            (output / "recourse_review_report.md").write_text("tampered\n", encoding="utf-8")
            tampered = verify_recourse_evidence_pack(output)
            (output / "undeclared.txt").write_text("extra\n", encoding="utf-8")
            undeclared = verify_recourse_evidence_pack(output)
        self.assertFalse(tampered["ok"])
        self.assertTrue(any("hash mismatch" in error for error in tampered["errors"]))
        self.assertFalse(undeclared["ok"])
        self.assertTrue(any("declared output set" in error for error in undeclared["errors"]))

    def test_generated_language_and_fields_remain_bounded(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "pack"
            generate_recourse_evidence_pack(CORE_DATASET, FIXTURE_ROOT / "baseline", output)
            text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in output.iterdir()
                if path.is_file()
            ).lower()
        for phrase in (
            "will qualify",
            "will be approved",
            "can overturn",
            "regulator-approved",
            "institutionally adopted",
            "production validated",
        ):
            self.assertNotIn(phrase, text)
        results = assess_recourse(CORE_DATASET, FIXTURE_ROOT / "baseline")
        forbidden = {
            "reason_code",
            "reason_rank",
            "mapping_id",
            "mapping_version",
            "disclosed_reason_text",
            "notice_template_id",
            "notice_template_version",
            "rendered_reason_text",
        }
        self.assertFalse(forbidden & set(results[0]))

    def test_core_validation_contract_and_monitoring_result_remain_unchanged(self) -> None:
        self.assertTrue(validate_dataset(CORE_DATASET).ok)
        self.assertFalse(any("recourse" in spec.filename for spec in SCHEMA_SPECS))
        from credit_gov.monitoring import MonitoringRunResult  # noqa: PLC0415

        self.assertNotIn("recourse", MonitoringRunResult.__annotations__)

    def test_recourse_module_does_not_import_reason_generation_or_notice_rendering(self) -> None:
        source = (SRC / "credit_gov" / "recourse.py").read_text(encoding="utf-8")
        self.assertNotIn("credit_gov.generation", source)
        self.assertNotIn("from .generation", source)
        self.assertNotIn("reason_fidelity", source)

    def test_root_and_packaged_schemas_are_byte_identical(self) -> None:
        schema_names = (
            "recourse-subject-record.schema.json",
            "recourse-method-record.schema.json",
            "recourse-action-set.schema.json",
            "recourse-review-config.schema.json",
            "synthetic-prediction-model.schema.json",
            "recourse-assessment-output.schema.json",
        )
        for name in schema_names:
            with self.subTest(name=name):
                self.assertEqual(
                    (ROOT / "schemas" / name).read_bytes(),
                    (SRC / "credit_gov" / "schemas" / "json" / name).read_bytes(),
                )

    def test_packaged_schema_fallback_validates_recourse_bundle(self) -> None:
        original_schema_dir = validators.SCHEMA_DIR
        try:
            validators.SCHEMA_DIR = Path("C:/tmp/credit-gov-missing-schemas")
            result = validate_recourse_bundle(FIXTURE_ROOT / "baseline", CORE_DATASET)
        finally:
            validators.SCHEMA_DIR = original_schema_dir
        self.assertTrue(result.ok, result.errors)

    def test_cli_success_and_failure_exit_codes(self) -> None:
        with redirect_stdout(StringIO()):
            self.assertEqual(
                0,
                validate_main([str(CORE_DATASET), str(FIXTURE_ROOT / "baseline")]),
            )
            self.assertEqual(
                1,
                validate_main(
                    [str(CORE_DATASET), str(FIXTURE_ROOT / "invalid-baseline-mismatch")]
                ),
            )
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "pack"
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    0,
                    report_main(
                        [str(CORE_DATASET), str(FIXTURE_ROOT / "baseline"), str(output)]
                    ),
                )
                self.assertEqual(
                    1,
                    report_main(
                        [str(CORE_DATASET), str(FIXTURE_ROOT / "baseline"), str(output)]
                    ),
                )

    def test_integrated_and_console_command_surfaces_are_declared(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("credit-gov-recourse-validate", pyproject)
        self.assertIn("credit-gov-recourse-report", pyproject)
        self.assertIn("dependencies = []", pyproject)
        with redirect_stdout(StringIO()):
            self.assertEqual(
                0,
                commands_main(
                    [
                        "recourse-validate",
                        str(CORE_DATASET),
                        str(FIXTURE_ROOT / "baseline"),
                    ]
                ),
            )
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "integrated-pack"
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    0,
                    commands_main(
                        [
                            "recourse-report",
                            str(CORE_DATASET),
                            str(FIXTURE_ROOT / "baseline"),
                            str(output),
                        ]
                    ),
                )

    @unittest.skipUnless(CHECKED_IN_EXAMPLE.is_dir(), "curated pack generated later in the build")
    def test_checked_in_curated_pack_is_current_and_verifiable(self) -> None:
        self.assertTrue(verify_recourse_evidence_pack(CHECKED_IN_EXAMPLE)["ok"])
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            generated = Path(temporary) / "generated"
            generate_recourse_evidence_pack(
                CORE_DATASET, FIXTURE_ROOT / "baseline", generated
            )
            expected = {
                name: (CHECKED_IN_EXAMPLE / name).read_bytes() for name in OUTPUT_FILENAMES
            }
            actual = {name: (generated / name).read_bytes() for name in OUTPUT_FILENAMES}
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
