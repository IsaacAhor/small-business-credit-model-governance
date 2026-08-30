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
FIXTURE_ROOT = ROOT / "data" / "synthetic" / "credit-union-vendor-risk"
CORE_DATASET = ROOT / "data" / "synthetic" / "monthly-demo"
CHECKED_IN_EXAMPLE = ROOT / "examples" / "evidence-packs" / "credit-union-vendor-risk"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.vendor_reporting import (  # noqa: E402
    MANIFEST_FILENAME,
    OPEN_FINDINGS_FILENAME,
    REPORT_FILENAME,
    SUMMARY_FILENAME,
    build_vendor_summary,
    generate_vendor_oversight_report,
    main as report_main,
    sha256_file,
    sha256_manifest_input,
)
from credit_gov.vendor_risk import (  # noqa: E402
    load_vendor_payloads,
    validate_main,
    validate_vendor_risk_dataset,
)


class VendorRiskRunKitTests(unittest.TestCase):
    def copy_fixture(self, name: str, root: Path) -> Path:
        target = root / name
        shutil.copytree(FIXTURE_ROOT / name, target)
        return target

    def update_json(self, path: Path, mutate) -> None:  # noqa: ANN001
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_valid_fixture_set_and_intentionally_invalid_fixtures(self) -> None:
        for name in (
            "baseline-complete",
            "opaque-component",
            "material-change",
            "incident-escalation",
            "notice-control-gap",
        ):
            with self.subTest(name=name):
                result = validate_vendor_risk_dataset(FIXTURE_ROOT / name, CORE_DATASET)
                self.assertTrue(result.ok, result.errors)
                self.assertEqual(11, len(result.validated_files))

        for name in ("invalid-missing-evidence", "invalid-broken-link"):
            with self.subTest(name=name):
                result = validate_vendor_risk_dataset(FIXTURE_ROOT / name, CORE_DATASET)
                self.assertFalse(result.ok)

    def test_missing_evidence_and_broken_link_fail_for_expected_reasons(self) -> None:
        missing = validate_vendor_risk_dataset(
            FIXTURE_ROOT / "invalid-missing-evidence", CORE_DATASET
        )
        broken = validate_vendor_risk_dataset(
            FIXTURE_ROOT / "invalid-broken-link", CORE_DATASET
        )

        self.assertTrue(
            any("missing-vendor-evidence.md" in error for error in missing.errors),
            missing.errors,
        )
        self.assertTrue(
            any("references unknown review" in error for error in broken.errors),
            broken.errors,
        )

    def test_opaque_component_requires_limitation_and_residual_decision(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("opaque-component", Path(temporary))
            self.update_json(
                fixture / "vendor-model-components.json",
                lambda payload: payload[0].update({"limitation_ids": []}),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("requires a limitation record" in error for error in result.errors),
            result.errors,
        )

    def test_high_risk_requires_heightened_monitoring(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline-complete", Path(temporary))
            self.update_json(
                fixture / "vendor-oversight-config.json",
                lambda payload: payload["heightened_monitoring"].update(
                    {"required": False, "status": "not_required"}
                ),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("requires heightened monitoring" in error for error in result.errors),
            result.errors,
        )

    def test_material_change_and_incident_surface_review_status(self) -> None:
        material_payloads = load_vendor_payloads(
            FIXTURE_ROOT / "material-change", CORE_DATASET
        )
        incident_payloads = load_vendor_payloads(
            FIXTURE_ROOT / "incident-escalation", CORE_DATASET
        )
        material = build_vendor_summary(material_payloads)
        incident = build_vendor_summary(incident_payloads)

        self.assertEqual("model_change", material["events"][0]["event_type"])
        self.assertEqual("security_event", incident["events"][0]["event_type"])
        self.assertTrue(
            any(gap["gap_id"] == "vendor-event-review-incomplete" for gap in material["review_gaps"])
        )
        self.assertIn("not_reportability_determination", incident["events"][0]["result_type"])

    def test_event_timestamps_require_canonical_utc_format(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("material-change", Path(temporary))
            self.update_json(
                fixture / "vendor-event-records.json",
                lambda payload: payload[0].update(
                    {"detected_at": "2026-05-20 14:00:00"}
                ),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("detected_at must use" in error for error in result.errors),
            result.errors,
        )

    def test_component_event_status_must_match_linked_events(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("material-change", Path(temporary))
            self.update_json(
                fixture / "vendor-model-components.json",
                lambda payload: payload[0].update({"event_status": "no_event_reported"}),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("must not reference event_ids" in error for error in result.errors),
            result.errors,
        )

    def test_component_links_must_match_record_ownership(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            limitation_fixture = self.copy_fixture("baseline-complete", root / "limitation")
            self.update_json(
                limitation_fixture / "vendor-model-components.json",
                lambda payload: payload[1].update(
                    {"limitation_ids": ["vml-synthetic-proprietary-detail"]}
                ),
            )
            limitation_result = validate_vendor_risk_dataset(
                limitation_fixture, CORE_DATASET
            )

            unlinked_fixture = self.copy_fixture("baseline-complete", root / "unlinked")
            self.update_json(
                unlinked_fixture / "vendor-model-components.json",
                lambda payload: payload[0].update(
                    {"transparency_state": "transparent", "limitation_ids": []}
                ),
            )
            unlinked_result = validate_vendor_risk_dataset(
                unlinked_fixture, CORE_DATASET
            )

            event_fixture = self.copy_fixture("material-change", root / "event")
            self.update_json(
                event_fixture / "vendor-model-components.json",
                lambda payload: (
                    payload[0].update(
                        {"event_status": "no_event_reported", "event_ids": []}
                    ),
                    payload[1].update(
                        {
                            "event_status": "event_reported",
                            "event_ids": ["vme-synthetic-model-change"],
                        }
                    ),
                ),
            )
            event_result = validate_vendor_risk_dataset(event_fixture, CORE_DATASET)

        self.assertFalse(limitation_result.ok)
        self.assertTrue(
            any("limitation_ids belongs to a different component" in error for error in limitation_result.errors),
            limitation_result.errors,
        )
        self.assertFalse(unlinked_result.ok)
        self.assertTrue(
            any("limitation records must be linked" in error for error in unlinked_result.errors),
            unlinked_result.errors,
        )
        self.assertFalse(event_result.ok)
        self.assertTrue(
            any("event_ids belongs to a different component" in error for error in event_result.errors),
            event_result.errors,
        )

    def test_vendor_notice_time_matches_notice_status(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            missing_time = self.copy_fixture("material-change", root / "missing")
            self.update_json(
                missing_time / "vendor-event-records.json",
                lambda payload: payload[0].pop("vendor_notice_at"),
            )
            missing_result = validate_vendor_risk_dataset(missing_time, CORE_DATASET)

            not_received = self.copy_fixture("material-change", root / "not-received")
            self.update_json(
                not_received / "vendor-event-records.json",
                lambda payload: (
                    payload[0].pop("vendor_notice_at"),
                    payload[0].update({"contract_notice_status": "not_received"}),
                ),
            )
            not_received_result = validate_vendor_risk_dataset(not_received, CORE_DATASET)

        self.assertFalse(missing_result.ok)
        self.assertTrue(
            any("requires vendor_notice_at" in error for error in missing_result.errors),
            missing_result.errors,
        )
        self.assertTrue(not_received_result.ok, not_received_result.errors)

    def test_notice_control_gap_is_reported_without_breaking_contract_validation(self) -> None:
        payloads = load_vendor_payloads(
            FIXTURE_ROOT / "notice-control-gap", CORE_DATASET
        )
        summary = build_vendor_summary(payloads)

        self.assertTrue(
            any(gap["gap_id"] == "notice-control-review-incomplete" for gap in summary["review_gaps"])
        )

    def test_notice_mapping_links_match_the_decision_reason_outputs(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline-complete", Path(temporary))
            self.update_json(
                fixture / "business-credit-notice-controls.json",
                lambda payload: payload[0].update({"reason_mapping_ids": ["map-001"]}),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("must exactly match the recorded adverse-action reason outputs" in error for error in result.errors),
            result.errors,
        )

    def test_notice_dates_match_the_linked_decision(self) -> None:
        cases = (
            (
                "application_date",
                "2025-05-04",
                "application_date must match the linked decision application_date",
            ),
            (
                "action_date",
                "2026-05-05",
                "action_date must match the linked decision timestamp date",
            ),
        )
        for field, value, expected_error in cases:
            with self.subTest(field=field):
                with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
                    fixture = self.copy_fixture("baseline-complete", Path(temporary))
                    self.update_json(
                        fixture / "business-credit-notice-controls.json",
                        lambda payload, field=field, value=value: payload[0].update(
                            {field: value}
                        ),
                    )
                    result = validate_vendor_risk_dataset(fixture, CORE_DATASET)
                self.assertFalse(result.ok)
                self.assertTrue(
                    any(expected_error in error for error in result.errors),
                    result.errors,
                )

    def test_empty_findings_limitations_and_notice_records_remain_reviewable(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            fixture = self.copy_fixture("baseline-complete", Path(temporary))
            self.update_json(
                fixture / "vendor-risk-review-record.json",
                lambda payload: payload.update({"findings": []}),
            )
            self.update_json(
                fixture / "vendor-model-components.json",
                lambda payload: payload[0].update(
                    {"transparency_state": "transparent", "limitation_ids": []}
                ),
            )
            self.update_json(
                fixture / "vendor-model-limitations.json",
                lambda payload: payload.clear(),
            )
            self.update_json(
                fixture / "business-credit-notice-controls.json",
                lambda payload: payload.clear(),
            )
            result = validate_vendor_risk_dataset(fixture, CORE_DATASET)
            summary = build_vendor_summary(load_vendor_payloads(fixture, CORE_DATASET))

        self.assertTrue(result.ok, result.errors)
        self.assertTrue(
            any(
                gap["gap_id"] == "notice-control-evidence-not-supplied"
                for gap in summary["review_gaps"]
            )
        )

    def test_report_outputs_are_deterministic_and_hash_verifiable(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            manifest = generate_vendor_oversight_report(
                FIXTURE_ROOT / "baseline-complete", CORE_DATASET, first
            )
            generate_vendor_oversight_report(
                FIXTURE_ROOT / "baseline-complete", CORE_DATASET, second
            )

            for filename in (
                SUMMARY_FILENAME,
                REPORT_FILENAME,
                OPEN_FINDINGS_FILENAME,
                MANIFEST_FILENAME,
            ):
                self.assertNotIn(b"\r\n", (first / filename).read_bytes())
                self.assertEqual(
                    (first / filename).read_bytes(),
                    (second / filename).read_bytes(),
                )
            for output in manifest["outputs"]:
                self.assertEqual(output["sha256"], sha256_file(first / output["filename"]))
            report = (first / REPORT_FILENAME).read_text(encoding="utf-8").lower()

        evidence_sources = {item["source"] for item in manifest["inputs"]}
        self.assertIn("vendor_evidence", evidence_sources)
        self.assertIn("core_evidence", evidence_sources)
        self.assertEqual(
            "sha256_canonical_json_or_lf_text_inputs_raw_generated_outputs_v1",
            manifest["hash_policy"],
        )

        self.assertNotIn("is compliant", report)
        self.assertNotIn("regulator approved", report)
        self.assertNotIn("production-ready", report)
        self.assertIn("not a legal opinion", report)

    def test_manifest_input_hashes_ignore_platform_line_endings(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            json_lf = root / "lf.json"
            json_crlf = root / "crlf.json"
            text_lf = root / "lf.md"
            text_crlf = root / "crlf.md"
            json_lf.write_bytes(b'{"b": 2, "a": 1}\n')
            json_crlf.write_bytes(b'{\r\n  "a": 1,\r\n  "b": 2\r\n}\r\n')
            text_lf.write_bytes(b"alpha\nbeta\n")
            text_crlf.write_bytes(b"alpha\r\nbeta\r\n")

            self.assertEqual(
                sha256_manifest_input(json_lf), sha256_manifest_input(json_crlf)
            )
            self.assertEqual(
                sha256_manifest_input(text_lf), sha256_manifest_input(text_crlf)
            )

    def test_manifest_normalizes_absolute_repository_evidence_references(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            fixture = self.copy_fixture("baseline-complete", root / "fixture")
            absolute_reference = str((ROOT / "README.md").resolve())
            self.update_json(
                fixture / "vendor-risk-review-record.json",
                lambda payload: payload["evidence_references"].append(
                    absolute_reference
                ),
            )
            manifest = generate_vendor_oversight_report(
                fixture, CORE_DATASET, root / "report"
            )

        repository_entries = [
            item
            for item in manifest["inputs"]
            if item["source"] == "repository_evidence"
        ]
        self.assertIn("README.md", {item["filename"] for item in repository_entries})
        self.assertNotIn(str(ROOT.resolve()), json.dumps(manifest))
        self.assertTrue(
            all(not Path(item["filename"]).is_absolute() for item in repository_entries)
        )

    def test_existing_outputs_require_explicit_overwrite(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "review"
            generate_vendor_oversight_report(
                FIXTURE_ROOT / "baseline-complete", CORE_DATASET, output
            )
            with self.assertRaises(FileExistsError):
                generate_vendor_oversight_report(
                    FIXTURE_ROOT / "baseline-complete", CORE_DATASET, output
                )
            generate_vendor_oversight_report(
                FIXTURE_ROOT / "baseline-complete",
                CORE_DATASET,
                output,
                overwrite=True,
            )

    def test_checked_in_example_matches_a_fresh_build(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "review"
            generate_vendor_oversight_report(
                FIXTURE_ROOT / "baseline-complete", CORE_DATASET, output
            )
            for filename in (
                SUMMARY_FILENAME,
                REPORT_FILENAME,
                OPEN_FINDINGS_FILENAME,
                MANIFEST_FILENAME,
            ):
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (CHECKED_IN_EXAMPLE / filename).read_bytes(),
                        (output / filename).read_bytes(),
                    )

    def test_cli_success_and_failure_paths(self) -> None:
        with redirect_stdout(StringIO()):
            valid_exit = validate_main(
                [str(FIXTURE_ROOT / "baseline-complete"), str(CORE_DATASET)]
            )
            invalid_exit = validate_main(
                [str(FIXTURE_ROOT / "invalid-broken-link"), str(CORE_DATASET)]
            )
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            with redirect_stdout(StringIO()):
                report_exit = report_main(
                    [
                        str(FIXTURE_ROOT / "baseline-complete"),
                        str(CORE_DATASET),
                        str(Path(temporary) / "report"),
                    ]
                )

        self.assertEqual(0, valid_exit)
        self.assertEqual(1, invalid_exit)
        self.assertEqual(0, report_exit)


if __name__ == "__main__":
    unittest.main()
