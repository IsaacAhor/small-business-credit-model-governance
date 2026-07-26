from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = ROOT / "tmp" / "test-runs"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402
from credit_gov.validation import (  # noqa: E402
    assess_model_change,
    diff_model_version,
    diff_reason_code_mappings,
    diff_threshold_set,
    render_change_validation_report,
)

DATASET = ROOT / "data" / "synthetic" / "monthly-portfolio"


def load(name: str):
    return json.loads((DATASET / name).read_text(encoding="utf-8"))


def _threshold_set(thresholds: list[dict]) -> dict:
    return {"threshold_set_id": "thr-x", "thresholds": thresholds}


def _threshold(metric: str, rule: str, value: float, severity: str = "medium", owner: str = "MRG") -> dict:
    return {
        "metric_name": metric,
        "comparison_rule": rule,
        "threshold_value": value,
        "severity": severity,
        "escalation_owner": owner,
    }


def _mapping(code: str, driver: str, text: str, version: str = "mapver-1") -> dict:
    return {
        "reason_code": code,
        "driver_or_signal": driver,
        "reason_text": text,
        "mapping_version": version,
    }


class ModelVersionDiffTests(unittest.TestCase):
    def test_scalar_and_list_changes_are_detected(self) -> None:
        prior = {
            "version_id": "ver-1",
            "effective_date": "2026-05-01",
            "change_summary": "baseline",
            "linked_validation_record": "val-1",
            "assumptions": ["a1", "a2"],
            "limitations": ["l1"],
        }
        current = {
            "version_id": "ver-2",
            "effective_date": "2026-06-01",
            "change_summary": "updated",
            "linked_validation_record": "val-2",
            "assumptions": ["a1", "a2"],
            "limitations": ["l1", "l2"],
        }
        diff = diff_model_version(prior, current)
        self.assertTrue(diff["changed"])
        self.assertTrue(diff["version_id"]["changed"])
        self.assertEqual(diff["limitations"]["added"], ["l2"])
        self.assertEqual(diff["assumptions"]["added"], [])
        self.assertFalse(diff["assumptions"]["changed"])

    def test_identical_version_reports_no_change(self) -> None:
        record = {
            "version_id": "ver-1",
            "effective_date": "2026-05-01",
            "change_summary": "baseline",
            "linked_validation_record": "val-1",
            "assumptions": ["a1"],
            "limitations": ["l1"],
        }
        diff = diff_model_version(dict(record), dict(record))
        self.assertFalse(diff["changed"])


class ThresholdSetDiffTests(unittest.TestCase):
    def test_added_removed_and_directional_changes(self) -> None:
        prior = _threshold_set(
            [
                _threshold("approval_rate", "less_than", 0.30),
                _threshold("override_rate", "greater_than", 0.12),
                _threshold("manual_review_rate", "greater_than", 0.5),
            ]
        )
        current = _threshold_set(
            [
                _threshold("approval_rate", "less_than", 0.35),
                _threshold("override_rate", "greater_than", 0.10, severity="high"),
                _threshold("decline_rate", "greater_than", 0.6),
            ]
        )
        diff = diff_threshold_set(prior, current)
        added = [entry["metric_name"] for entry in diff["added"]]
        removed = [entry["metric_name"] for entry in diff["removed"]]
        changed = {entry["metric_name"]: entry for entry in diff["changed"]}
        self.assertEqual(added, ["decline_rate"])
        self.assertEqual(removed, ["manual_review_rate"])
        # less_than raising the value fires more easily -> tightened
        self.assertEqual(changed["approval_rate"]["direction"], "tightened")
        # greater_than lowering the value fires more easily -> tightened
        self.assertEqual(changed["override_rate"]["direction"], "tightened")
        self.assertIn("severity", changed["override_rate"]["field_changes"])
        self.assertEqual(diff["change_count"], 4)

    def test_loosened_and_rule_change_directions(self) -> None:
        prior = _threshold_set([_threshold("approval_rate", "less_than", 0.35)])
        loosened = _threshold_set([_threshold("approval_rate", "less_than", 0.30)])
        self.assertEqual(diff_threshold_set(prior, loosened)["changed"][0]["direction"], "loosened")
        rule_changed = _threshold_set([_threshold("approval_rate", "greater_than", 0.35)])
        self.assertEqual(
            diff_threshold_set(prior, rule_changed)["changed"][0]["direction"], "rule_changed"
        )


class ReasonCodeMappingDiffTests(unittest.TestCase):
    def test_added_removed_structural_and_version_only(self) -> None:
        prior = [
            _mapping("RC-101", "cash_flow", "Insufficient cash flow", "mapver-1"),
            _mapping("RC-104", "utilization", "High credit utilization", "mapver-1"),
            _mapping("RC-199", "other", "Other", "mapver-1"),
        ]
        current = [
            _mapping("RC-101", "cash_flow", "Insufficient cash flow", "mapver-2"),
            _mapping("RC-104", "utilization", "Elevated credit utilization", "mapver-2"),
            _mapping("RC-106", "industry", "Elevated industry risk", "mapver-2"),
        ]
        diff = diff_reason_code_mappings(prior, current)
        self.assertEqual([entry["reason_code"] for entry in diff["added"]], ["RC-106"])
        self.assertEqual([entry["reason_code"] for entry in diff["removed"]], ["RC-199"])
        changed = {entry["reason_code"]: entry for entry in diff["changed"]}
        # RC-104 changed reason text -> structural; RC-101 only version bump
        self.assertTrue(changed["RC-104"]["structural_change"])
        self.assertFalse(changed["RC-101"]["structural_change"])
        self.assertEqual(diff["structural_change_count"], 1)
        self.assertTrue(diff["mapping_version"]["changed"])


class ChangeSummaryAndReportTests(unittest.TestCase):
    def test_material_change_summary_and_signoff_on_portfolio(self) -> None:
        result = assess_model_change(
            prior_version=load("prior-model-version-record.json"),
            current_version=load("model-version-record.json"),
            current_thresholds=load("threshold-set.json"),
            current_reason_mappings=load("reason-code-mappings.json"),
            model_id="mdl-smb-credit-xgb",
            run_id="run-2026-06",
            prior_thresholds=load("prior-threshold-set.json"),
            prior_reason_mappings=load("prior-reason-code-mappings.json"),
            config=load("change-review-config.json"),
        )
        summary = result["summary"]
        self.assertTrue(summary["material_change"])
        self.assertIn("threshold_tightened", summary["change_categories"])
        self.assertIn("reason_code_added", summary["change_categories"])
        signoff = result["reviewer_signoff"]
        self.assertEqual(signoff["current_version_id"], "ver-2026-06")
        self.assertEqual(signoff["evidence_pack_run_id"], "run-2026-06")
        self.assertEqual(signoff["validation_status"], "pending_review")
        self.assertTrue(signoff["required_before_promotion"])

    def test_report_renders_sections_and_is_deterministic(self) -> None:
        kwargs = dict(
            prior_version=load("prior-model-version-record.json"),
            current_version=load("model-version-record.json"),
            current_thresholds=load("threshold-set.json"),
            current_reason_mappings=load("reason-code-mappings.json"),
            model_id="mdl-smb-credit-xgb",
            run_id="run-2026-06",
            prior_thresholds=load("prior-threshold-set.json"),
            prior_reason_mappings=load("prior-reason-code-mappings.json"),
            config=load("change-review-config.json"),
        )
        report_a = render_change_validation_report(assess_model_change(**kwargs))
        report_b = render_change_validation_report(assess_model_change(**kwargs))
        self.assertEqual(report_a, report_b)
        self.assertIn("# Model-Change Validation Review", report_a)
        self.assertIn("## Threshold-Set Changes", report_a)
        self.assertIn("## Reason-Code Mapping Changes", report_a)
        self.assertIn("Regulation B 12 CFR 1002.9", report_a)

    def test_missing_prior_subinputs_skip_those_diffs(self) -> None:
        result = assess_model_change(
            prior_version=load("prior-model-version-record.json"),
            current_version=load("model-version-record.json"),
            current_thresholds=load("threshold-set.json"),
            current_reason_mappings=load("reason-code-mappings.json"),
            model_id="mdl-smb-credit-xgb",
            run_id="run-2026-06",
            prior_thresholds=None,
            prior_reason_mappings=None,
            config=None,
        )
        self.assertEqual(result["threshold_set_diff"]["status"], "prior_not_available")
        self.assertEqual(result["reason_code_mapping_diff"]["status"], "prior_not_available")
        # Only the model-version change remains; no threshold/reason materiality.
        self.assertEqual(result["summary"]["threshold_change_count"], "prior_not_available")


class ChangeValidationMonitoringIntegrationTests(unittest.TestCase):
    def test_monitoring_run_emits_change_validation_evidence(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as tmp:
            result = run_monthly_monitoring(DATASET, evidence_root=Path(tmp))
            self.assertTrue(result.ok, result.errors)
            self.assertIsNotNone(result.change_validation)
            self.assertTrue(result.change_validation["summary"]["material_change"])
            output_dir = Path(result.output_dir)
            self.assertTrue((output_dir / "model_change_validation_results.json").is_file())
            self.assertTrue((output_dir / "model_change_validation_report.md").is_file())
            report = (output_dir / "monitoring_report.md").read_text(encoding="utf-8")
            self.assertIn("## Model-Change Validation Review", report)
            signoff = (output_dir / "reviewer_signoff.md").read_text(encoding="utf-8")
            self.assertIn("## Model-Change Validation Signoff", signoff)
            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("model_change_validation_results.json", manifest["output_files"])

    def test_monitoring_run_without_change_inputs_is_unaffected(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as tmp:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo",
                evidence_root=Path(tmp),
            )
            self.assertTrue(result.ok, result.errors)
            self.assertIsNone(result.change_validation)
            output_dir = Path(result.output_dir)
            self.assertFalse((output_dir / "model_change_validation_results.json").is_file())
            self.assertNotIn(
                "## Model-Change Validation Review",
                (output_dir / "monitoring_report.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
