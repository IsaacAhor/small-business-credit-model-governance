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
DATASET = ROOT / "data" / "synthetic" / "monthly-demo"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.governance_review import (  # noqa: E402
    MANIFEST_FILENAME,
    REPORT_FILENAME,
    SUMMARY_FILENAME,
    generate_governance_review,
    main,
    sha256_file,
)
from credit_gov.schemas import validate_dataset  # noqa: E402


class ModelGovernanceReviewTests(unittest.TestCase):
    def copy_dataset(self, root: Path) -> Path:
        target = root / "dataset"
        shutil.copytree(DATASET, target)
        return target

    def update_json(self, path: Path, mutate) -> None:  # noqa: ANN001
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_governance_bundle_validates_and_legacy_dataset_remains_valid(self) -> None:
        current = validate_dataset(DATASET)
        legacy = validate_dataset(ROOT / "data" / "synthetic" / "monthly-demo-no-breach")

        self.assertTrue(current.ok, current.errors)
        self.assertEqual(16, len(current.validated_files))
        self.assertTrue(legacy.ok, legacy.errors)
        self.assertEqual(12, len(legacy.validated_files))

    def test_partial_governance_bundle_fails_closed(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            dataset = self.copy_dataset(Path(temporary))
            (dataset / "model-monitoring-plan.json").unlink()
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("Incomplete governance bundle" in error for error in result.errors),
            result.errors,
        )

    def test_unknown_explainability_method_link_fails(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            dataset = self.copy_dataset(Path(temporary))
            self.update_json(
                dataset / "model-validation-record.json",
                lambda payload: payload.update(
                    {"explainability_method_ids": ["xai-unknown-method"]}
                ),
            )
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("references unknown value(s): xai-unknown-method" in error for error in result.errors),
            result.errors,
        )

    def test_missing_explainability_validation_reference_fails(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            dataset = self.copy_dataset(Path(temporary))
            self.update_json(
                dataset / "explainability-method-records.json",
                lambda payload: payload[0].update(
                    {"validation_test_references": ["tests/test_missing_reason_check.py"]}
                ),
            )
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "validation_test_references missing file: "
                "tests/test_missing_reason_check.py" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_explainability_reference_outside_dataset_or_source_root_fails(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            dataset = self.copy_dataset(root / "dataset-copy")
            outside_reference = Path(sys.executable).resolve()
            self.update_json(
                dataset / "explainability-method-records.json",
                lambda payload: payload[0].update(
                    {"validation_test_references": [str(outside_reference)]}
                ),
            )
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("validation_test_references missing file" in error for error in result.errors),
            result.errors,
        )

    def test_self_review_cannot_claim_approval_or_promotion(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            dataset = self.copy_dataset(Path(temporary))
            self.update_json(
                dataset / "model-validation-record.json",
                lambda payload: payload.update(
                    {"overall_disposition": "approved", "promotion_allowed": True}
                ),
            )
            result = validate_dataset(dataset)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("requires an independent validator" in error for error in result.errors),
            result.errors,
        )

    def test_review_outputs_are_deterministic_and_hash_verifiable(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            manifest = generate_governance_review(DATASET, first)
            generate_governance_review(DATASET, second)

            for filename in (SUMMARY_FILENAME, REPORT_FILENAME, MANIFEST_FILENAME):
                self.assertEqual(
                    (first / filename).read_bytes(),
                    (second / filename).read_bytes(),
                )
            for output in manifest["outputs"]:
                self.assertEqual(
                    output["sha256"], sha256_file(first / output["filename"])
                )
            summary = json.loads((first / SUMMARY_FILENAME).read_text(encoding="utf-8"))

        self.assertFalse(summary["validation"]["promotion_allowed"])
        self.assertEqual("developer_self_review", summary["validation"]["independence_status"])
        self.assertTrue(
            any(gap["gap_id"] == "independent-validation" for gap in summary["review_gaps"])
        )
        self.assertIn("not_validation_or_approval", summary["result_type"])

    def test_existing_outputs_require_explicit_overwrite(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "review"
            generate_governance_review(DATASET, output)
            with self.assertRaises(FileExistsError):
                generate_governance_review(DATASET, output)
            generate_governance_review(DATASET, output, overwrite=True)

    def test_cli_returns_success_for_valid_bundle(self) -> None:
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            output = Path(temporary) / "review"
            with redirect_stdout(StringIO()):
                exit_code = main([str(DATASET), str(output)])

        self.assertEqual(0, exit_code)


if __name__ == "__main__":
    unittest.main()
