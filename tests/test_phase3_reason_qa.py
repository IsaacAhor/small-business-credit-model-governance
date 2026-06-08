from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = Path("C:/tmp") if Path("C:/tmp").exists() else Path(tempfile.gettempdir())
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402


class mutated_dataset:
    def __init__(self, filename: str, mutate) -> None:  # noqa: ANN001
        self.filename = filename
        self.mutate = mutate
        self._temp_dir = None
        self.path: Path | None = None

    def __enter__(self) -> Path:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._temp_dir = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.path = Path(self._temp_dir.name) / "dataset"
        shutil.copytree(ROOT / "data" / "synthetic" / "monthly-demo", self.path)
        target = self.path / self.filename
        payload = json.loads(target.read_text(encoding="utf-8"))
        self.mutate(payload)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return self.path

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        if self._temp_dir is not None:
            self._temp_dir.cleanup()


class temp_evidence_root:
    def __init__(self) -> None:
        self._temp_dir = None
        self.path: Path | None = None

    def __enter__(self) -> Path:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._temp_dir = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.path = Path(self._temp_dir.name) / "evidence"
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        if self._temp_dir is not None:
            self._temp_dir.cleanup()


class Phase3ReasonQATests(unittest.TestCase):
    def test_valid_reason_outputs_generate_no_reason_exceptions(self) -> None:
        with temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo",
                evidence_root=evidence_root,
            )

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.reason_qa["exception_count"], 0)
            output_dir = Path(result.output_dir)
            self.assertTrue((output_dir / "reason_qa_results.json").is_file())
            self.assertTrue((output_dir / "reason_stability_report.json").is_file())
            report = (output_dir / "monitoring_report.md").read_text(encoding="utf-8")
            self.assertIn("## Adverse-Action Reason QA", report)

    def test_missing_decline_reason_is_traceable_exception(self) -> None:
        with mutated_dataset(
            "adverse-action-reason-outputs.json",
            lambda payload: payload.clear(),
        ) as dataset, temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(dataset, evidence_root=evidence_root)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.reason_qa["exception_count"], 1)
        self.assertEqual(result.reason_qa["exceptions"][0]["exception_type"], "missing_reason_code")
        self.assertEqual(result.reason_qa["exceptions"][0]["decision_id"], "dec-0002")
        self.assertEqual(len(result.issues), 2)

    def test_unmapped_reason_code_is_qa_exception_not_validation_failure(self) -> None:
        with mutated_dataset(
            "adverse-action-reason-outputs.json",
            lambda payload: payload[0].update({"reason_code": "RC-999"}),
        ) as dataset, temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(dataset, evidence_root=evidence_root)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.reason_qa["exceptions"][0]["exception_type"], "unmapped_reason_code")

    def test_generic_reason_text_is_qa_exception(self) -> None:
        with mutated_dataset(
            "reason-code-mappings.json",
            lambda payload: payload[0].update({"reason_text": "Other"}),
        ) as dataset, temp_evidence_root() as evidence_root:
            result = run_monthly_monitoring(dataset, evidence_root=evidence_root)

        self.assertTrue(result.ok, result.errors)
        exception_types = {
            exception["exception_type"]
            for exception in result.reason_qa["exceptions"]
        }
        self.assertIn("generic_reason_text", exception_types)


if __name__ == "__main__":
    unittest.main()
