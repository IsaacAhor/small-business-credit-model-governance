from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = Path("C:/tmp") if Path("C:/tmp").exists() else Path(tempfile.gettempdir())
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.bisg import bisg_posterior, load_reference_table, run_bisg_proxy_analysis  # noqa: E402
from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402

PORTFOLIO = ROOT / "data" / "synthetic" / "monthly-portfolio"
SURNAMES = load_reference_table(ROOT / "data" / "reference" / "bisg" / "demo-surname-probabilities.json")
GEOGRAPHIES = load_reference_table(ROOT / "data" / "reference" / "bisg" / "demo-geography-probabilities.json")
with (ROOT / "data" / "reference" / "bisg" / "national-marginals.json").open(encoding="utf-8") as handle:
    MARGINALS = {key: float(value) for key, value in json.load(handle).items()}


class BisgPosteriorTests(unittest.TestCase):
    def test_posterior_is_normalized(self) -> None:
        estimate = bisg_posterior("WASHINGTON", "GEO-SOUTH-2", SURNAMES, GEOGRAPHIES, MARGINALS)
        self.assertEqual(estimate["basis"], "surname_and_geography")
        self.assertAlmostEqual(sum(estimate["posterior"].values()), 1.0, places=9)

    def test_informative_surname_dominates(self) -> None:
        estimate = bisg_posterior("NGUYEN", "GEO-MIDWEST-1", SURNAMES, GEOGRAPHIES, MARGINALS)
        self.assertGreater(estimate["posterior"]["api"], 0.85)

    def test_geography_shifts_posterior(self) -> None:
        south = bisg_posterior("SMITH", "GEO-SOUTH-2", SURNAMES, GEOGRAPHIES, MARGINALS)
        midwest = bisg_posterior("SMITH", "GEO-MIDWEST-1", SURNAMES, GEOGRAPHIES, MARGINALS)
        self.assertGreater(south["posterior"]["black"], midwest["posterior"]["black"])

    def test_unknown_surname_falls_back_to_geography(self) -> None:
        estimate = bisg_posterior("ZZZUNKNOWN", "GEO-WEST-1", SURNAMES, GEOGRAPHIES, MARGINALS)
        self.assertEqual(estimate["basis"], "geography_only")
        self.assertIsNotNone(estimate["posterior"])

    def test_unknown_surname_and_geography_produces_no_posterior(self) -> None:
        estimate = bisg_posterior("ZZZUNKNOWN", "GEO-NOWHERE", SURNAMES, GEOGRAPHIES, MARGINALS)
        self.assertEqual(estimate["basis"], "no_reference_match")
        self.assertIsNone(estimate["posterior"])


class BisgAnalysisTests(unittest.TestCase):
    def test_portfolio_analysis_matches_all_decisions(self) -> None:
        decisions = json.loads((PORTFOLIO / "application-decision-records.json").read_text(encoding="utf-8"))
        demographic_inputs = json.loads((PORTFOLIO / "applicant-demographic-inputs.json").read_text(encoding="utf-8"))
        config = json.loads((PORTFOLIO / "bisg-config.json").read_text(encoding="utf-8"))
        results = run_bisg_proxy_analysis(decisions, demographic_inputs, config, PORTFOLIO)

        self.assertEqual(results["label"], "bisg_proxy_screening_only_not_legal_conclusion")
        self.assertEqual(results["matched_decision_count"], len(decisions))
        self.assertEqual(results["unmatched_decision_count"], 0)
        for category in ("white", "black", "hispanic", "api"):
            self.assertTrue(results["group_metrics"][category]["adequate_effective_sample"], category)
        # Small effective groups must be excluded from comparisons, not silently tested.
        self.assertTrue(results["comparisons"]["aian"].get("skipped"))
        # Every executed comparison carries a test, a p-value, and caveats.
        for category, comparison in results["comparisons"].items():
            if comparison.get("skipped"):
                continue
            self.assertIn("p_value", comparison, category)
            self.assertIn("test", comparison, category)
            self.assertTrue(comparison["caveats"], category)

    def test_monitoring_run_emits_bisg_evidence(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            evidence_root = Path(temp_dir) / "evidence"
            evidence_root.mkdir(parents=True, exist_ok=True)
            result = run_monthly_monitoring(PORTFOLIO, evidence_root=evidence_root)

            self.assertTrue(result.ok, result.errors)
            self.assertIsNotNone(result.bisg)
            output_dir = Path(result.output_dir)
            bisg_payload = json.loads((output_dir / "bisg_proxy_results.json").read_text(encoding="utf-8"))
            self.assertEqual(bisg_payload["method"], "bayesian_improved_surname_geocoding")
            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("bisg_proxy_results.json", manifest["output_files"])
            report = (output_dir / "monitoring_report.md").read_text(encoding="utf-8")
            self.assertIn("BISG Proxy Screening", report)

    def test_datasets_without_bisg_inputs_are_unaffected(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            evidence_root = Path(temp_dir) / "evidence"
            evidence_root.mkdir(parents=True, exist_ok=True)
            result = run_monthly_monitoring(
                ROOT / "data" / "synthetic" / "monthly-demo",
                evidence_root=evidence_root,
            )
            self.assertTrue(result.ok, result.errors)
            self.assertIsNone(result.bisg)
            output_dir = Path(result.output_dir)
            self.assertFalse((output_dir / "bisg_proxy_results.json").exists())


class SignificanceIntegrationTests(unittest.TestCase):
    def test_fair_lending_findings_carry_significance(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            evidence_root = Path(temp_dir) / "evidence"
            evidence_root.mkdir(parents=True, exist_ok=True)
            result = run_monthly_monitoring(PORTFOLIO, evidence_root=evidence_root)

            self.assertTrue(result.ok, result.errors)
            for group_result in result.fair_lending["group_results"].values():
                self.assertIn("significance", group_result)
                self.assertIn("approval_rate", group_result["significance"])
            approval_findings = [
                finding
                for finding in result.fair_lending["findings"]
                if finding["metric_name"] == "approval_rate_ratio"
            ]
            self.assertTrue(approval_findings)
            for finding in approval_findings:
                significance = finding["statistical_significance"]
                self.assertIn("p_value", significance)
                self.assertIn("test", significance)
                self.assertIn("statistically_significant", significance)


if __name__ == "__main__":
    unittest.main()
