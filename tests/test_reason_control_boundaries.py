"""Decision-specific counterexamples for coverage and lifecycle controls."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_gov.generation import generate_adverse_action_reasons
from credit_gov.monitoring import compute_reason_fidelity_exceptions
from credit_gov.reason_fidelity import build_reason_fidelity_context
from credit_gov.schemas.models import ApplicationDecisionRecord
from credit_gov.schemas.validators import load_schema, validate_object

DATA = ROOT / "data/synthetic/adverse-action-reason-benchmark"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class ReasonControlBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.decision = next(x for x in load("application-decision-records.json")
                             if x["decision_id"] == "dec-0002")
        self.drivers = [next(x for x in load("adverse-action-driver-contributions.json")
                             if x["decision_id"] == "dec-0002")]
        self.mappings = load("reason-code-mappings.json")
        self.policy = load("reason-fidelity-policy.json")
        self.template = load("adverse-action-notice-template.json")
        self.methods = load("reason-selection-methods.json")

    def run_controls(self):
        context = build_reason_fidelity_context(self.policy, self.template, self.methods)
        outputs = generate_adverse_action_reasons(
            [self.decision], self.drivers, self.mappings, "ver-2026-07-adverse-action",
            fidelity_context=context)
        findings = compute_reason_fidelity_exceptions(
            [self.decision], self.mappings, outputs, self.drivers, context)
        self.assertTrue(all(x["decision_id"] == "dec-0002" for x in findings))
        return outputs, findings

    def unmap(self, index):
        self.drivers[0]["contributions"][index]["driver_or_signal"] = f"unmapped_signal_{index}"

    def test_clean_chain_has_no_findings(self):
        outputs, findings = self.run_controls()
        self.assertEqual(2, len(outputs))
        self.assertEqual([], findings)

    def test_unmapped_principal_cannot_hide_behind_mapped_reason(self):
        for index in (0, 1):
            with self.subTest(index=index):
                self.setUp()
                self.unmap(index)
                outputs, findings = self.run_controls()
                self.assertEqual(1, len(outputs))
                self.assertEqual({"principal_driver_unmapped", "principal_driver_omitted"},
                                 {x["exception_type"] for x in findings})
                self.assertTrue(all(f"unmapped_signal_{index}" in x["message"]
                                    for x in findings))
                self.assertFalse(any(x["driver_or_signal"].startswith("unmapped") for x in outputs))

    def test_wholly_unmapped_scope_has_explicit_findings_without_invented_text(self):
        self.unmap(0)
        self.unmap(1)
        outputs, findings = self.run_controls()
        self.assertEqual([], outputs)
        self.assertEqual({"principal_driver_unmapped", "principal_driver_omitted"},
                         {x["exception_type"] for x in findings})

    def test_unmapped_driver_outside_principal_scope_is_not_flagged_as_principal(self):
        self.policy["principal_driver_rank_limit"] = 1
        self.unmap(1)
        outputs, findings = self.run_controls()
        self.assertEqual(1, len(outputs))
        self.assertEqual([], findings)

    def test_lifecycle_uses_decision_event_with_inclusive_start_exclusive_retirement(self):
        cases = [
            ("2026-07-05", None, "2026-07-04T23:59:59Z", True),
            ("2026-07-05", None, "2026-07-05T00:00:00Z", False),
            ("2026-07-05", None, "2026-07-10T12:00:00Z", False),
            ("2026-07-01", "2026-07-05", "2026-07-04T23:59:59Z", False),
            ("2026-07-01", "2026-07-05", "2026-07-05T00:00:00Z", True),
            ("2026-07-01", "2026-07-05", "2026-07-10T12:00:00Z", True),
        ]
        for target in ("mapping", "template"):
            for effective, retired, timestamp, invalid in cases:
                with self.subTest(target=target, timestamp=timestamp, retired=retired):
                    self.setUp()
                    self.decision["application_date"] = "2026-07-02"
                    self.decision["underwriting"]["decision_timestamp"] = timestamp
                    records = self.mappings if target == "mapping" else [self.template]
                    for record in records:
                        record.update(effective_date=effective, retired_date=retired)
                    _, findings = self.run_controls()
                    kind = ("mapping_not_effective_on_decision_date" if target == "mapping"
                            else "notice_template_not_effective_on_decision_date")
                    self.assertEqual({kind} if invalid else set(),
                                     {x["exception_type"] for x in findings})
                    self.assertEqual(2 if invalid else 0, len(findings))

    def test_application_date_cannot_change_lifecycle_result(self):
        self.decision["underwriting"]["decision_timestamp"] = "2026-07-10T12:00:00Z"
        for mapping in self.mappings:
            mapping["retired_date"] = "2026-07-05"
        _, before = self.run_controls()
        self.decision["application_date"] = "2026-07-10"
        _, after = self.run_controls()
        self.assertEqual(before, after)

    def test_invalid_timestamps_rejected_by_schema_and_typed_model(self):
        bad_values = [None, "not-a-timestamp", "2026-02-30T12:00:00Z",
                      "2026-07-10", "2026-07-10T12:00:00", "2026-07-10T12:00:00-05:00",
                      "2026-07-10T24:00:00Z", "2026-07-10T12:00:00Z\n"]
        schema = load_schema("application-decision-record.schema.json")
        for value in bad_values:
            for validation in (ApplicationDecisionRecord.from_dict,
                               lambda record: validate_object(record, schema)):
                with self.subTest(value=value, validation=validation):
                    record = copy.deepcopy(self.decision)
                    if value is None:
                        del record["underwriting"]["decision_timestamp"]
                    else:
                        record["underwriting"]["decision_timestamp"] = value
                    with self.assertRaises((ValueError, TypeError)):
                        validation(record)

    def test_valid_leap_day_accepted(self):
        self.decision["underwriting"]["decision_timestamp"] = "2024-02-29T23:59:59Z"
        ApplicationDecisionRecord.from_dict(self.decision)
        validate_object(self.decision, load_schema("application-decision-record.schema.json"))

    def test_direct_qa_rejects_invalid_timestamp_without_application_fallback(self):
        self.decision["underwriting"]["decision_timestamp"] = "not-a-timestamp"
        with self.assertRaisesRegex(ValueError, "decision_timestamp"):
            self.run_controls()


if __name__ == "__main__":
    unittest.main()
