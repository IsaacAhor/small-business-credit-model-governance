from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

import pandas as pd

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = ROOT / "tmp" / "test-runs"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.monitoring import load_dataset_payloads, run_monthly_monitoring
from credit_gov.sba_to_monitoring import (
    canonical_column_map,
    prepare_chunk,
    write_cohort,
)
from credit_gov.schemas.validators import validate_dataset


class SbaFixedHorizonAdapterTests(unittest.TestCase):
    def test_fair_lending_schema_preserves_applicable_dataset_requirements(self) -> None:
        root_schema = json.loads(
            (ROOT / "schemas" / "fair-lending-screening-config.schema.json").read_text(
                encoding="utf-8"
            )
        )
        packaged_schema = json.loads(
            (
                SRC
                / "credit_gov"
                / "schemas"
                / "json"
                / "fair-lending-screening-config.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(root_schema, packaged_schema)
        conditional = root_schema["allOf"][0]
        self.assertEqual(conditional["if"]["properties"]["applicable"]["const"], False)
        self.assertEqual(conditional["then"]["properties"]["comparison_groups"]["maxItems"], 0)
        self.assertEqual(conditional["then"]["properties"]["screens"]["maxItems"], 0)
        self.assertEqual(conditional["else"]["properties"]["comparison_groups"]["minItems"], 1)
        self.assertEqual(conditional["else"]["properties"]["screens"]["minItems"], 1)

    def test_current_status_spacing_and_fixed_horizon_rules(self) -> None:
        raw = pd.DataFrame(
            {
                "AsOfDate": ["2026-06-30"] * 8,
                "Program": ["7A"] * 8,
                "GrossApproval": [100_000] * 8,
                "ApprovalDate": ["2017-12-01"] * 8,
                "ApprovalFY": [2018] * 8,
                "FirstDisbursementDate": [
                    "2018-01-15",
                    "2019-02-01",
                    "2025-01-01",
                    "2018-03-01",
                    "2018-03-01",
                    "2018-01-01",
                    "2018-01-01",
                    "2018-01-01",
                ],
                "ProcessingMethod": ["PLP"] * 8,
                "TermInMonths": [120] * 8,
                "NaicsCode": [541611] * 8,
                "BorrState": ["IL"] * 8,
                "BusinessType": ["CORPORATION"] * 8,
                "JobsSupported": [3] * 8,
                "LoanStatus": [
                    "P I F",
                    "EXEMPT",
                    "EXEMPT",
                    "CHGOFF",
                    "CHGOFF",
                    "CANCLD",
                    "CHGOFF",
                    "UNKNOWN",
                ],
                "PaidInFullDate": ["2021-01-01", None, None, None, None, None, None, None],
                "ChargeOffDate": [None, None, None, "2020-02-01", "2022-04-01", None, None, None],
                "GrossChargeOffAmount": [0, 0, 0, 25_000, 25_000, 0, 25_000, 0],
            }
        )
        columns = canonical_column_map(raw.columns)
        prepared, counts = prepare_chunk(raw, columns, horizon_months=36)

        self.assertEqual(len(prepared), 4)
        self.assertEqual(prepared["default"].tolist(), [0, 0, 1, 0])
        self.assertEqual(counts["eligible_default_within_horizon"], 1)
        self.assertEqual(counts["eligible_nondefault_at_horizon"], 3)
        self.assertEqual(counts["excluded_unseasoned_at_as_of_date"], 1)
        self.assertEqual(counts["excluded_cancelled"], 1)
        self.assertEqual(counts["excluded_chargeoff_missing_event_date"], 1)
        self.assertEqual(counts["excluded_unsupported_status"], 1)

    def test_public_data_modules_validate_and_render_not_applicable(self) -> None:
        frame = pd.DataFrame(
            {
                "origin_date": pd.to_datetime(["2020-01-01", "2020-02-01"]),
                "amount": [100_000.0, 200_000.0],
                "delivery": ["PLP", "GP"],
                "region": ["midwest", "south"],
                "default": [0, 1],
                "score": [720.0, 610.0],
            }
        )
        with LocalTemporaryDirectory(TEMP_ROOT) as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            write_cohort(
                "sba-2020",
                frame,
                dataset,
                "SBA 7(a)",
                36,
                baseline_default_rate=0.10,
                baseline_score_average=700.0,
            )
            validation = validate_dataset(dataset)
            self.assertTrue(validation.ok, validation.errors)

            payloads = load_dataset_payloads(dataset)
            self.assertEqual(payloads["overrides"], [])
            self.assertEqual(payloads["reason_mappings"], [])
            result = run_monthly_monitoring(dataset, root / "evidence")
            self.assertTrue(result.ok, result.errors)
            self.assertIsNone(result.metrics["approval_rate"])
            self.assertIsNone(result.metrics["override_rate"])
            self.assertEqual(result.reason_qa["status"], "not_applicable")
            self.assertEqual(result.fair_lending["status"], "not_applicable")
            report = next((root / "evidence").rglob("monitoring_report.md")).read_text(
                encoding="utf-8"
            )
            self.assertIn("Status: `not_applicable`", report)
            self.assertNotIn("SCHEMA_PLACEHOLDER", report)


if __name__ == "__main__":
    unittest.main()
