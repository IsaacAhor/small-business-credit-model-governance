from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.generation import (  # noqa: E402
    generate_adverse_action_reasons,
    generate_reasons_for_decision,
    summarize_generation,
)

DATASET = ROOT / "data" / "synthetic" / "monthly-portfolio"


def load(name: str):
    return json.loads((DATASET / name).read_text(encoding="utf-8"))


class ReasonGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decisions = load("application-decision-records.json")
        self.contributions = load("adverse-action-driver-contributions.json")
        self.mappings = load("reason-code-mappings.json")
        self.version_id = load("model-version-record.json")["version_id"]

    def test_generation_is_deterministic_and_matches_shipped_file(self) -> None:
        generated = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        again = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        self.assertEqual(generated, again)
        shipped = load("adverse-action-reason-outputs.json")
        self.assertEqual(
            generated,
            shipped,
            "Shipped adverse-action reasons drifted from current generation logic.",
        )

    def test_reasons_only_for_declined_decisions(self) -> None:
        generated = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        declined_ids = {
            record["decision_id"]
            for record in self.decisions
            if record["decision_outcome"] == "declined"
        }
        produced_ids = {output["decision_id"] for output in generated}
        self.assertTrue(produced_ids.issubset(declined_ids))

    def test_reasons_are_ranked_and_mapped(self) -> None:
        mapping_index = {m["driver_or_signal"]: m for m in self.mappings}
        contributions = [
            {"driver_or_signal": "debt_service_coverage", "contribution": 0.2, "direction": "adverse"},
            {"driver_or_signal": "cash_flow_stability", "contribution": 0.5, "direction": "adverse"},
        ]
        outputs = generate_reasons_for_decision(
            "dec-0002", contributions, mapping_index, self.version_id
        )
        # Highest contribution first, ranks contiguous from 1.
        self.assertEqual(outputs[0]["driver_or_signal"], "cash_flow_stability")
        self.assertEqual([o["reason_rank"] for o in outputs], [1, 2])
        self.assertEqual(outputs[0]["reason_code"], mapping_index["cash_flow_stability"]["reason_code"])

    def test_missing_contributions_yield_no_outputs(self) -> None:
        mapping_index = {m["driver_or_signal"]: m for m in self.mappings}
        outputs = generate_reasons_for_decision("dec-0002", [], mapping_index, self.version_id)
        self.assertEqual(outputs, [])

    def test_summary_reports_uncovered_declined_decisions(self) -> None:
        generated = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        summary = summarize_generation(self.decisions, generated)
        # The portfolio dataset seeds exactly one declined decision with no reason.
        self.assertEqual(len(summary["declined_without_generated_reasons"]), 1)


if __name__ == "__main__":
    unittest.main()
