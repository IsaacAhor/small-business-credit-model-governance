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


class temp_evidence_root:
    def __init__(self) -> None:
        self._temp_dir = None
        self.path: Path | None = None

    def __enter__(self) -> Path:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._temp_dir = LocalTemporaryDirectory(TEMP_ROOT)
        self.path = Path(self._temp_dir.name) / "evidence"
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        if self._temp_dir is not None:
            self._temp_dir.cleanup()


class Phase4FairLendingTests(unittest.TestCase):
    def test_portfolio_screening_generates_only_gate_supported_findings(self) -> None:
        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-portfolio",
                evidence_root=evidence_root,
            )

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.fair_lending["label"], "fair_lending_screening_only_not_legal_conclusion")
            self.assertGreater(result.fair_lending["finding_count"], 0)
            self.assertTrue(
                any(finding["metric_name"] == "approval_rate_ratio" for finding in result.fair_lending["findings"]),
                result.fair_lending["findings"],
            )
            self.assertTrue(
                any(issue.get("linked_fair_lending_finding_ids") for issue in result.issues),
                result.issues,
            )
            self.assertTrue(
                all(
                    finding["finding_gate"]["status"] == "passed_statistical_significance"
                    for finding in result.fair_lending["findings"]
                ),
                result.fair_lending["findings"],
            )
            self.assertTrue(
                any(
                    screen["finding_gate"]["status"]
                    == "inconclusive_not_statistically_significant"
                    for screen in result.fair_lending["inconclusive_screens"]
                ),
                result.fair_lending["inconclusive_screens"],
            )

            output_dir = Path(result.output_dir)
            screening = json.loads((output_dir / "fair_lending_screening_results.json").read_text(encoding="utf-8"))
            escalations = json.loads((output_dir / "fair_lending_escalation_register.json").read_text(encoding="utf-8"))
            notes = (output_dir / "reviewer_notes.md").read_text(encoding="utf-8")
            self.assertEqual(screening["finding_count"], len(escalations))
            self.assertGreater(screening["inconclusive_screen_count"], 0)
            self.assertIn("review triggers, not legal conclusions", notes)

    def test_small_sample_threshold_observations_are_inconclusive_not_escalations(self) -> None:
        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo",
                evidence_root=evidence_root,
            )

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.fair_lending["finding_count"], 0)
            self.assertGreater(result.fair_lending["inconclusive_screen_count"], 0)
            self.assertTrue(
                all(
                    screen["finding_gate"]["status"] == "inconclusive_insufficient_sample"
                    for screen in result.fair_lending["inconclusive_screens"]
                ),
                result.fair_lending["inconclusive_screens"],
            )
            self.assertFalse(
                any(issue.get("linked_fair_lending_finding_ids") for issue in result.issues),
                result.issues,
            )

    def test_no_breach_scenario_generates_no_fair_lending_findings(self) -> None:
        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo-no-breach",
                evidence_root=evidence_root,
            )

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.fair_lending["finding_count"], 0)
            self.assertEqual(result.fair_lending["findings"], [])


if __name__ == "__main__":
    unittest.main()
