from __future__ import annotations

import json
import shutil
import subprocess
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


class Phase2MonitoringTests(unittest.TestCase):
    def test_controlled_breach_scenario_generates_expected_outputs(self) -> None:
        dataset = ROOT / "data" / "synthetic" / "monthly-demo"
        expected_breaches = json.loads((dataset / "breach-records.json").read_text(encoding="utf-8"))

        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(dataset, evidence_root=evidence_root)

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.breaches, expected_breaches)
            self.assertEqual(result.metrics["approval_rate"], 0.5)
            self.assertEqual(result.metrics["override_rate"], 0.5)
            self.assertGreaterEqual(len(result.issues), 1)

            output_dir = Path(result.output_dir)
            self.assertTrue((output_dir / "manifest.json").is_file())
            self.assertTrue((output_dir / "metric_results.json").is_file())
            self.assertTrue((output_dir / "breach_register.json").is_file())
            self.assertTrue((output_dir / "fair_lending_screening_results.json").is_file())
            self.assertTrue((output_dir / "fair_lending_escalation_register.json").is_file())
            self.assertTrue((output_dir / "issue_register.json").is_file())
            self.assertTrue((output_dir / "monitoring_report.md").is_file())
            self.assertTrue((output_dir / "reviewer_notes.md").is_file())
            self.assertTrue((output_dir / "reviewer_signoff.md").is_file())

    def test_no_breach_scenario_generates_empty_registers(self) -> None:
        dataset = ROOT / "data" / "synthetic" / "monthly-demo-no-breach"

        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(dataset, evidence_root=evidence_root)

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.breaches, [])
            self.assertEqual(result.issues, [])
            self.assertEqual(result.fair_lending["findings"], [])
            output_dir = Path(result.output_dir)
            self.assertEqual(
                json.loads((output_dir / "breach_register.json").read_text(encoding="utf-8")),
                [],
            )
            self.assertEqual(
                json.loads((output_dir / "issue_register.json").read_text(encoding="utf-8")),
                [],
            )

    def test_cli_returns_nonzero_for_invalid_dataset(self) -> None:
        invalid_dataset = ROOT / "data" / "synthetic" / "monthly-demo-invalid-overlap"
        with temp_evidence_root() as evidence_root:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_monthly_monitoring.py"),
                    str(invalid_dataset),
                    "--evidence-root",
                    str(evidence_root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("monitoring_only_fields and underwriting_fields must be separated", completed.stdout)


if __name__ == "__main__":
    unittest.main()
