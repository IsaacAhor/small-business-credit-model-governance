from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.run_adverse_action_reason_benchmark import (  # noqa: E402
    EXPECTED_EXCEPTION_TYPES,
    run_benchmark,
)
from credit_gov.monitoring import verify_evidence_pack  # noqa: E402

DATASET = ROOT / "data" / "synthetic" / "adverse-action-reason-benchmark"
EXAMPLE_PACK = ROOT / "examples" / "evidence-packs" / "adverse-action-reason-benchmark"
TEST_OUTPUT = ROOT / "evidence" / "_test_adverse_action_reason_benchmark_pack"


class AdverseActionReasonBenchmarkTests(unittest.TestCase):
    def test_curated_results_cover_expected_seeded_failures(self) -> None:
        results = json.loads(
            (EXAMPLE_PACK / "adverse_action_reason_benchmark_results.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            "data/synthetic/adverse-action-reason-benchmark",
            results["dataset"],
        )
        self.assertTrue(results["acceptance"]["expected_seeded_failures_observed"])
        self.assertEqual([], results["missing_expected_exception_types"])
        self.assertEqual(EXPECTED_EXCEPTION_TYPES, set(results["observed_exception_types"]))
        self.assertIn("not_legal_conclusion", results["label"])
        fidelity = results["monitoring_reason_qa"]["source_to_notice_fidelity"]
        self.assertEqual("ran_synthetic_source_to_rendered_notice_controls", fidelity["status"])
        self.assertIn("notice_text_mapping_mismatch", fidelity["exception_types"])
        self.assertIn("reason_not_in_actual_contributors", fidelity["exception_types"])
        self.assertIn("decision_component_mismatch", fidelity["exception_types"])
        self.assertIn("rendered_notice_text_mismatch", fidelity["exception_types"])
        self.assertEqual(
            "ran_synthetic_rendered_notice_controls",
            fidelity["rendered_notice_fidelity"]["status"],
        )

    def test_runner_regenerates_benchmark_pack(self) -> None:
        result = run_benchmark(
            dataset_dir=DATASET,
            output_dir=TEST_OUTPUT,
            overwrite=True,
        )

        self.assertTrue(result.ok, result.errors)
        self.assertTrue((TEST_OUTPUT / "adverse_action_reason_benchmark_results.json").is_file())
        self.assertTrue((TEST_OUTPUT / "adverse_action_reason_benchmark_report.md").is_file())
        manifest = json.loads((TEST_OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(
            "adverse_action_reason_benchmark_results.json",
            manifest["output_files"],
        )
        self.assertIn(
            "adverse_action_reason_benchmark_report.md",
            manifest["output_files"],
        )
        self.assertIn("rendered_notice_qa_results.json", manifest["output_files"])
        self.assertTrue(verify_evidence_pack(TEST_OUTPUT)["ok"])
        curated_files = sorted(path.name for path in EXAMPLE_PACK.iterdir() if path.is_file())
        regenerated_files = sorted(path.name for path in TEST_OUTPUT.iterdir() if path.is_file())
        self.assertEqual(
            sorted(set(curated_files) | {"execution_provenance.json", "output_fingerprints.json"}),
            regenerated_files,
        )
        for filename in curated_files:
            if filename == "manifest.json":
                continue
            self.assertEqual(
                (EXAMPLE_PACK / filename).read_bytes(),
                (TEST_OUTPUT / filename).read_bytes(),
                f"Curated evidence-pack artifact is stale: {filename}",
            )


if __name__ == "__main__":
    unittest.main()
