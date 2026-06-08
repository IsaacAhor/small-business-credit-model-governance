from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = Path("C:/tmp") if Path("C:/tmp").exists() else Path(tempfile.gettempdir())
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.schemas import validate_dataset  # noqa: E402


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


class Phase1ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset_dir = ROOT / "data" / "synthetic" / "monthly-demo"

    def test_demo_dataset_validates(self) -> None:
        result = validate_dataset(self.dataset_dir)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(len(result.validated_files), 11)

    def test_invalid_record_produces_specific_error(self) -> None:
        invalid_dataset = (
            ROOT
            / "data"
            / "synthetic"
            / "monthly-demo-invalid-missing-effective-date"
        )
        result = validate_dataset(invalid_dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("model-version-record.json: effective_date is required" in error for error in result.errors),
            result.errors,
        )

    def test_overlapping_monitoring_and_underwriting_fields_fail(self) -> None:
        invalid_dataset = ROOT / "data" / "synthetic" / "monthly-demo-invalid-overlap"
        result = validate_dataset(invalid_dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("monitoring_only_fields and underwriting_fields must be separated: score" in error for error in result.errors),
            result.errors,
        )

    def test_score_output_unknown_decision_fails(self) -> None:
        with mutated_dataset(
            "score-outputs.json",
            lambda payload: payload[0].update({"decision_id": "dec-missing"}),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "score-outputs.json[0].decision_id references unknown value: dec-missing" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_override_unknown_decision_fails(self) -> None:
        with mutated_dataset(
            "override-events.json",
            lambda payload: payload[0].update({"decision_id": "dec-missing"}),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "override-events.json[0].decision_id references unknown value: dec-missing" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_outcome_unknown_decision_fails(self) -> None:
        with mutated_dataset(
            "outcome-records.json",
            lambda payload: payload[0].update({"decision_id": "dec-missing"}),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "outcome-records.json[0].decision_id references unknown value: dec-missing" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_mismatched_model_version_context_fails(self) -> None:
        with mutated_dataset(
            "threshold-set.json",
            lambda payload: payload.update({"version_id": "ver-mismatch"}),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("threshold-set.json.version_id must equal ver-2026-05" in error for error in result.errors),
            result.errors,
        )

    def test_breach_metric_without_threshold_fails(self) -> None:
        with mutated_dataset(
            "breach-records.json",
            lambda payload: payload[0].update({"metric_name": "missing_metric"}),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "breach-records.json[0].metric_name references unknown value: missing_metric" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_manifest_missing_input_reference_fails(self) -> None:
        with mutated_dataset(
            "evidence-pack-manifest.json",
            lambda payload: payload["input_references"].append("missing-input.json"),
        ) as dataset:
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "evidence-pack-manifest.json.input_references missing file: missing-input.json" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_cli_returns_nonzero_for_relationship_failure(self) -> None:
        with mutated_dataset(
            "score-outputs.json",
            lambda payload: payload[0].update({"decision_id": "dec-missing"}),
        ) as dataset:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_phase1.py"), str(dataset)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn(
            "score-outputs.json[0].decision_id references unknown value: dec-missing",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
