from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = ROOT / "tmp" / "test-runs"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.monitoring import (  # noqa: E402
    build_input_fingerprints,
    run_monthly_monitoring,
    verify_evidence_pack,
)


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
    def test_input_fingerprints_normalize_checkout_newlines(self) -> None:
        canonical = b'{"run_id":"demo"}\n'
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            dataset_dir = Path(temp_dir)
            input_path = dataset_dir / "evidence-pack-manifest.json"
            input_path.write_bytes(canonical.replace(b"\n", b"\r\n"))

            fingerprints = build_input_fingerprints(dataset_dir)

        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            fingerprints["evidence-pack-manifest.json"],
        )

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
            self.assertTrue((output_dir / "execution_provenance.json").is_file())
            self.assertTrue((output_dir / "output_fingerprints.json").is_file())
            self.assertTrue(verify_evidence_pack(output_dir)["ok"])

    def test_evidence_packs_are_unique_and_detect_modified_outputs(self) -> None:
        dataset = ROOT / "data" / "synthetic" / "monthly-demo"
        with temp_evidence_root() as evidence_root:
            first = run_monthly_monitoring(dataset, evidence_root=evidence_root)
            second = run_monthly_monitoring(dataset, evidence_root=evidence_root)

            first_dir = Path(first.output_dir)
            second_dir = Path(second.output_dir)
            self.assertNotEqual(first_dir, second_dir)
            self.assertTrue(verify_evidence_pack(first_dir)["ok"])
            self.assertTrue(verify_evidence_pack(second_dir)["ok"])

            metric_path = first_dir / "metric_results.json"
            metric_path.write_text("{}\n", encoding="utf-8")
            verification = verify_evidence_pack(first_dir)

        self.assertFalse(verification["ok"])
        self.assertIn("fingerprint mismatch: metric_results.json", verification["errors"])

    def test_checked_in_evidence_packs_verify_with_explanatory_readmes(self) -> None:
        for pack_name in (
            "adverse-action-reason-benchmark",
            "monthly-demo",
            "monthly-portfolio",
        ):
            evidence_pack = ROOT / "examples" / "evidence-packs" / pack_name
            verification = verify_evidence_pack(evidence_pack)
            self.assertTrue(verification["ok"], verification["errors"])

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
