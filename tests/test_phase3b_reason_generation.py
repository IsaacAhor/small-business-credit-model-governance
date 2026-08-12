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
from credit_gov.reason_fidelity import build_reason_fidelity_context  # noqa: E402

DATASET = ROOT / "data" / "synthetic" / "monthly-portfolio"
BENCHMARK_DATASET = ROOT / "data" / "synthetic" / "adverse-action-reason-benchmark"


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

    def test_fidelity_generation_pins_source_text_component_and_versions(self) -> None:
        decisions = json.loads(
            (BENCHMARK_DATASET / "application-decision-records.json").read_text(encoding="utf-8")
        )
        contributions = json.loads(
            (BENCHMARK_DATASET / "adverse-action-driver-contributions.json").read_text(
                encoding="utf-8"
            )
        )
        mappings = json.loads(
            (BENCHMARK_DATASET / "reason-code-mappings.json").read_text(encoding="utf-8")
        )
        fidelity_context = build_reason_fidelity_context(
            json.loads((BENCHMARK_DATASET / "reason-fidelity-policy.json").read_text(encoding="utf-8")),
            json.loads(
                (BENCHMARK_DATASET / "adverse-action-notice-template.json").read_text(
                    encoding="utf-8"
                )
            ),
            json.loads(
                (BENCHMARK_DATASET / "reason-selection-methods.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        outputs = generate_adverse_action_reasons(
            decisions,
            contributions,
            mappings,
            "ver-2026-07-adverse-action",
            fidelity_context=fidelity_context,
        )
        output = next(item for item in outputs if item["reason_output_id"] == "rso-0002-1")
        self.assertEqual("cash_flow_stability", output["driver_or_signal"])
        self.assertEqual("Insufficient cash flow stability", output["disclosed_reason_text"])
        self.assertEqual("aat-small-business-reason", output["notice_template_id"])
        self.assertEqual("scoring", output["decision_component"])
        self.assertEqual(1, output["source_driver_rank"])
        self.assertEqual("polver-2026-08", output["policy_version"])

    def test_fidelity_source_rank_counts_unmapped_adverse_drivers(self) -> None:
        mappings = json.loads(
            (BENCHMARK_DATASET / "reason-code-mappings.json").read_text(encoding="utf-8")
        )
        fidelity_context = build_reason_fidelity_context(
            json.loads((BENCHMARK_DATASET / "reason-fidelity-policy.json").read_text(encoding="utf-8")),
            json.loads(
                (BENCHMARK_DATASET / "adverse-action-notice-template.json").read_text(
                    encoding="utf-8"
                )
            ),
            json.loads(
                (BENCHMARK_DATASET / "reason-selection-methods.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        cash_flow_mapping = next(
            mapping for mapping in mappings if mapping["driver_or_signal"] == "cash_flow_stability"
        )
        outputs = generate_reasons_for_decision(
            "dec-0002",
            [
                {
                    "driver_or_signal": "unmapped_adverse_driver",
                    "contribution": 0.7,
                    "direction": "adverse",
                    "decision_component": "scoring",
                },
                {
                    "driver_or_signal": "cash_flow_stability",
                    "contribution": 0.5,
                    "direction": "adverse",
                    "decision_component": "scoring",
                },
            ],
            {"cash_flow_stability": cash_flow_mapping},
            "ver-2026-07-adverse-action",
            decision_context={
                "decision_component": "scoring",
                "underwriting": {"policy_version": "polver-2026-08"},
            },
            fidelity_context=fidelity_context,
        )
        self.assertEqual(1, outputs[0]["reason_rank"])
        self.assertEqual(2, outputs[0]["source_driver_rank"])

    def test_summary_reports_uncovered_declined_decisions(self) -> None:
        generated = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        summary = summarize_generation(self.decisions, generated)
        # The portfolio dataset seeds exactly one declined decision with no reason.
        self.assertEqual(len(summary["declined_without_generated_reasons"]), 1)


if __name__ == "__main__":
    unittest.main()
