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

from credit_gov.lda import assess_less_discriminatory_alternative  # noqa: E402
from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402

DATASET = ROOT / "data" / "synthetic" / "monthly-portfolio"


def load(name: str):
    return json.loads((DATASET / name).read_text(encoding="utf-8"))


def _decision(decision_id: str, region: str, outcome: str) -> dict:
    return {
        "decision_id": decision_id,
        "segment": "micro",
        "decision_outcome": outcome,
        "monitoring": {"region": region, "channel": "digital", "review_batch_id": "run-x"},
    }


def _alt(decision_id: str, outcome: str) -> dict:
    return {"decision_id": decision_id, "alternative_outcome": outcome, "alternative_model_id": "alt"}


def _outcome(decision_id: str, indicator: str) -> dict:
    return {"decision_id": decision_id, "repayment_or_default_indicator": indicator}


BASE_CONFIG = {
    "assessment_id": "lda-test",
    "group_source": "monitoring",
    "group_field": "region",
    "min_disparity_improvement": 0.05,
    "performance_tolerance": 0.03,
    "outcome_good_indicator": "performing",
}


class LDAAssessmentUnitTests(unittest.TestCase):
    def test_qualifying_alternative_on_portfolio_dataset(self) -> None:
        result = assess_less_discriminatory_alternative(
            decisions=load("application-decision-records.json"),
            alternative_decisions=load("alternative-model-decisions.json"),
            outcomes=load("outcome-records.json"),
            config=load("lda-assessment-config.json"),
        )
        self.assertTrue(result["qualifying_alternative_identified"])
        self.assertEqual(result["review_trigger"], "document_and_review_alternative")
        self.assertGreater(
            result["alternative"]["disparity"]["approval_rate_ratio"],
            result["baseline"]["disparity"]["approval_rate_ratio"],
        )

    def test_no_qualifying_when_alternative_equals_baseline(self) -> None:
        decisions = [
            _decision("dec-0001", "south", "approved"),
            _decision("dec-0002", "west", "declined"),
        ]
        alternative = [_alt("dec-0001", "approved"), _alt("dec-0002", "declined")]
        outcomes = [_outcome("dec-0001", "performing"), _outcome("dec-0002", "default")]
        result = assess_less_discriminatory_alternative(decisions, alternative, outcomes, BASE_CONFIG)
        self.assertFalse(result["qualifying_alternative_identified"])
        self.assertEqual(result["review_trigger"], "no_qualifying_alternative")

    def test_reduces_disparity_but_degrades_performance_records_tradeoff(self) -> None:
        # Baseline: cleanly separates goods (approved) from bads (declined), but
        # west (a bad) is declined -> disparity. Alternative approves everyone,
        # erasing disparity but also approving the bad -> separation collapses.
        decisions = [
            _decision("dec-0001", "south", "approved"),
            _decision("dec-0002", "south", "approved"),
            _decision("dec-0003", "west", "declined"),
        ]
        alternative = [
            _alt("dec-0001", "approved"),
            _alt("dec-0002", "approved"),
            _alt("dec-0003", "approved"),
        ]
        outcomes = [
            _outcome("dec-0001", "performing"),
            _outcome("dec-0002", "performing"),
            _outcome("dec-0003", "default"),
        ]
        result = assess_less_discriminatory_alternative(decisions, alternative, outcomes, BASE_CONFIG)
        self.assertTrue(result["comparison"]["reduces_disparity"])
        self.assertFalse(result["comparison"]["holds_performance"])
        self.assertEqual(result["review_trigger"], "record_tradeoff_only")


class LDAMonitoringIntegrationTests(unittest.TestCase):
    def test_monitoring_run_emits_lda_evidence(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as tmp:
            result = run_monthly_monitoring(DATASET, evidence_root=Path(tmp))
            self.assertTrue(result.ok, result.errors)
            self.assertIsNotNone(result.lda)
            self.assertTrue(result.lda["qualifying_alternative_identified"])
            output_dir = Path(result.output_dir)
            self.assertTrue((output_dir / "lda_assessment_results.json").is_file())
            report = (output_dir / "monitoring_report.md").read_text(encoding="utf-8")
            self.assertIn("## Less-Discriminatory-Alternative Assessment", report)

    def test_monitoring_run_without_lda_inputs_is_unaffected(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as tmp:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo",
                evidence_root=Path(tmp),
            )
            self.assertTrue(result.ok, result.errors)
            self.assertIsNone(result.lda)
            output_dir = Path(result.output_dir)
            self.assertFalse((output_dir / "lda_assessment_results.json").is_file())


if __name__ == "__main__":
    unittest.main()
