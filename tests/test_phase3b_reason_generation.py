from __future__ import annotations

import json
import io
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from contextlib import redirect_stderr
from unittest.mock import patch
from tests.temp_utils import LocalTemporaryDirectory

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
from credit_gov.commands import generate_reasons_main  # noqa: E402

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

    def test_script_and_installed_generation_share_scope_on_write_match_and_drift(self) -> None:
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(DATASET, dataset)
            prefixes = [
                [sys.executable, str(ROOT / "scripts/generate_adverse_action_reasons.py")],
                [sys.executable, "-m", "credit_gov.commands", "generate-reasons"],
            ]
            env = {**os.environ, "PYTHONPATH": str(SRC)}
            for mode, expected in (("write", 0), ("match", 0), ("drift", 1)):
                if mode == "drift":
                    (dataset / "adverse-action-reason-outputs.json").write_text("[]\n", encoding="utf-8")
                outputs = []
                for prefix in prefixes:
                    with self.subTest(mode=mode, entry=prefix[1]):
                        args = prefix + [str(dataset)] + ([] if mode == "write" else ["--check"])
                        result = subprocess.run(args, capture_output=True, text=True, env=env, check=False)
                        self.assertEqual(expected, result.returncode, result.stderr)
                        summary = json.loads(next(
                            line.split("=", 1)[1] for line in result.stdout.splitlines()
                            if line.startswith("generation_summary=")
                        ))
                        self.assertEqual("diagnostic_reason_generation", summary["purpose"])
                        self.assertEqual("not_assessed", summary["final_use_status"])
                        self.assertEqual("not_provided", summary["operational_authorization_status"])
                        self.assertIs(summary["authorized_for_operational_use"], False)
                        self.assertIs(summary["eligible_for_final_use"], False)
                        outputs.append(result.stdout)
                self.assertEqual(outputs[0], outputs[1])

    def test_partial_or_invalid_configuration_fails_without_overwriting_candidates(self) -> None:
        for problem in ("missing", "malformed", "null", "boolean_limit", "fractional_limit", "zero_limit"):
            with self.subTest(problem=problem), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                dataset = Path(temp) / "dataset"
                shutil.copytree(BENCHMARK_DATASET, dataset)
                output = dataset / "adverse-action-reason-outputs.json"
                original = output.read_bytes()
                policy = dataset / "reason-fidelity-policy.json"
                if problem == "missing":
                    (dataset / "reason-selection-methods.json").unlink()
                elif problem in ("malformed", "null"):
                    policy.write_text("{" if problem == "malformed" else "null", encoding="utf-8")
                else:
                    value = json.loads(policy.read_text(encoding="utf-8"))
                    value["principal_driver_rank_limit"] = {
                        "boolean_limit": True, "fractional_limit": 1.5, "zero_limit": 0,
                    }[problem]
                    policy.write_text(json.dumps(value), encoding="utf-8")
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(1, generate_reasons_main([str(dataset)]))
                    self.assertEqual(1, generate_reasons_main([str(dataset), "--check"]))
                self.assertEqual(original, output.read_bytes())

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

    def test_rich_inputs_cannot_silently_downgrade_when_all_configuration_is_missing(self) -> None:
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(BENCHMARK_DATASET, dataset)
            output = dataset / "adverse-action-reason-outputs.json"
            original = output.read_bytes()
            for name in ("reason-fidelity-policy.json", "adverse-action-notice-template.json",
                         "reason-selection-methods.json"):
                (dataset / name).unlink()
            with redirect_stderr(io.StringIO()):
                self.assertEqual(1, generate_reasons_main([str(dataset)]))
                self.assertEqual(1, generate_reasons_main([str(dataset), "--check"]))
            self.assertEqual(original, output.read_bytes())

    def test_incomplete_typed_configuration_does_not_replace_candidates(self) -> None:
        cases = (
            ("reason-fidelity-policy.json", "policy_version", False),
            ("adverse-action-notice-template.json", "template_id", "  "),
            ("adverse-action-notice-template.json", "effective_date", "2026-02-30"),
            ("adverse-action-notice-template.json", "retired_date", False),
            ("adverse-action-notice-template.json", "retired_date", "2026-06-01"),
            ("reason-selection-methods.json", "selection_method_version", []),
            ("reason-selection-methods.json", "decision_component", "unsupported"),
        )
        for name, field, value in cases:
            with self.subTest(field=field, value=value), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                dataset = Path(temp) / "dataset"
                shutil.copytree(BENCHMARK_DATASET, dataset)
                output = dataset / "adverse-action-reason-outputs.json"
                original = output.read_bytes()
                path = dataset / name
                config = json.loads(path.read_text(encoding="utf-8"))
                (config[0] if isinstance(config, list) else config)[field] = value
                path.write_text(json.dumps(config), encoding="utf-8")
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(1, generate_reasons_main([str(dataset)]))
                    self.assertEqual(1, generate_reasons_main([str(dataset), "--check"]))
                self.assertEqual(original, output.read_bytes())

    def test_current_and_old_review_names_prevent_basic_mode_downgrade(self) -> None:
        for name in ("reason-content-review.json", "final-use-review.json"):
            with self.subTest(review_file=name), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                dataset = Path(temp) / "dataset"
                shutil.copytree(DATASET, dataset)
                for config in ("reason-fidelity-policy.json", "adverse-action-notice-template.json",
                               "reason-selection-methods.json"):
                    self.assertFalse((dataset / config).exists())
                (dataset / name).write_text("{}", encoding="utf-8")
                output = dataset / "adverse-action-reason-outputs.json"
                original = output.read_bytes()
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(1, generate_reasons_main([str(dataset)]))
                    self.assertEqual(1, generate_reasons_main([str(dataset), "--check"]))
                self.assertEqual(original, output.read_bytes())

    def test_case_variant_fidelity_inputs_cannot_downgrade_on_case_sensitive_filesystems(self) -> None:
        exists = Path.exists
        names = (
            "FINAL-USE-REVIEW.JSON", "REASON-CONTENT-REVIEW.JSON",
            "REASON-FIDELITY-POLICY.JSON", "ADVERSE-ACTION-NOTICE-TEMPLATE.JSON",
            "REASON-SELECTION-METHODS.JSON", "RENDERED-ADVERSE-ACTION-NOTICES.JSON",
        )
        for name in names:
            for check in (False, True):
                with self.subTest(name=name, check=check), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                    dataset = Path(temp) / "dataset"
                    shutil.copytree(DATASET, dataset)
                    (dataset / name).write_text("{}", encoding="utf-8")
                    output = dataset / "adverse-action-reason-outputs.json"
                    original = output.read_bytes()

                    def case_sensitive_exists(path):
                        # Exercise case-sensitive lookup even on a Windows host.
                        if path.parent == dataset:
                            return any(entry.name == path.name for entry in dataset.iterdir())
                        return exists(path)

                    with patch.object(Path, "exists", case_sensitive_exists), redirect_stderr(io.StringIO()):
                        self.assertEqual(1, generate_reasons_main(
                            [str(dataset)] + (["--check"] if check else [])))
                    self.assertEqual(original, output.read_bytes())

    def test_missing_method_blocks_even_when_no_driver_would_generate_a_reason(self) -> None:
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(BENCHMARK_DATASET, dataset)
            output = dataset / "adverse-action-reason-outputs.json"
            original = output.read_bytes()
            methods = dataset / "reason-selection-methods.json"
            configured = json.loads(methods.read_text(encoding="utf-8"))
            methods.write_text(json.dumps([m for m in configured if m["decision_component"] != "scoring"]),
                               encoding="utf-8")
            (dataset / "reason-code-mappings.json").write_text("[]", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(1, generate_reasons_main([str(dataset)]))
                self.assertEqual(1, generate_reasons_main([str(dataset), "--check"]))
            self.assertEqual(original, output.read_bytes())

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

    def test_combined_decision_uses_recorded_failed_source_components(self) -> None:
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
        decision = next(item for item in decisions if item["decision_id"] == "dec-0011")
        decision_contributions = next(
            item["contributions"] for item in contributions if item["decision_id"] == "dec-0011"
        )
        outputs = generate_reasons_for_decision(
            "dec-0011",
            decision_contributions,
            {mapping["driver_or_signal"]: mapping for mapping in mappings},
            "ver-2026-07-adverse-action",
            decision_context=decision,
            fidelity_context=fidelity_context,
        )

        self.assertEqual(["RC-101", "RC-105"], [output["reason_code"] for output in outputs])
        self.assertEqual(["combined", "combined"], [output["decision_component"] for output in outputs])
        self.assertEqual(
            ["scoring", "judgmental"],
            [output["source_decision_component"] for output in outputs],
        )
        self.assertEqual([1, 2], [output["source_driver_rank"] for output in outputs])

    def test_summary_reports_uncovered_declined_decisions(self) -> None:
        generated = generate_adverse_action_reasons(
            self.decisions, self.contributions, self.mappings, self.version_id
        )
        summary = summarize_generation(self.decisions, generated)
        # The portfolio dataset seeds exactly one declined decision with no reason.
        self.assertEqual(len(summary["declined_without_generated_reasons"]), 1)


if __name__ == "__main__":
    unittest.main()
