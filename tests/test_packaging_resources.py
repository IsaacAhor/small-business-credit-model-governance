from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.bisg import load_reference_json  # noqa: E402
from credit_gov.schemas import validate_dataset  # noqa: E402
from credit_gov.schemas import validators  # noqa: E402
from credit_gov.vendor_risk import validate_vendor_risk_dataset  # noqa: E402

DATASET = ROOT / "data" / "synthetic" / "monthly-demo"
TEMP_ROOT = ROOT / "tmp" / "test-runs"


class PackagingResourceTests(unittest.TestCase):
    def test_schema_validation_falls_back_to_packaged_resources(self) -> None:
        original_schema_dir = validators.SCHEMA_DIR
        original_root = validators.ROOT
        try:
            validators.SCHEMA_DIR = Path("C:/tmp/credit-gov-missing-schemas")
            validators.ROOT = Path("C:/tmp/credit-gov-installed-package-root")
            result = validate_dataset(DATASET)
        finally:
            validators.SCHEMA_DIR = original_schema_dir
            validators.ROOT = original_root

        self.assertTrue(result.ok, result.errors)

    def test_bisg_loader_falls_back_to_packaged_reference_tables(self) -> None:
        payload = load_reference_json(
            TEMP_ROOT,
            "packaged/demo-surname-probabilities.json",
        )

        self.assertIn("SMITH", payload)
        self.assertIn("white", payload["SMITH"])

    def test_vendor_schema_validation_falls_back_to_packaged_resources(self) -> None:
        original_schema_dir = validators.SCHEMA_DIR
        try:
            validators.SCHEMA_DIR = Path("C:/tmp/credit-gov-missing-schemas")
            result = validate_vendor_risk_dataset(
                ROOT / "data" / "synthetic" / "credit-union-vendor-risk" / "baseline-complete",
                DATASET,
            )
        finally:
            validators.SCHEMA_DIR = original_schema_dir

        self.assertTrue(result.ok, result.errors)


if __name__ == "__main__":
    unittest.main()
