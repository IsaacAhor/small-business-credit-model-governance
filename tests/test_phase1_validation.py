from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.schemas import validate_dataset  # noqa: E402


class Phase1ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset_dir = ROOT / "data" / "synthetic" / "monthly-demo"

    def test_demo_dataset_validates(self) -> None:
        result = validate_dataset(self.dataset_dir)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(len(result.validated_files), 10)

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


if __name__ == "__main__":
    unittest.main()
