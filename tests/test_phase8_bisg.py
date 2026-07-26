from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = Path("C:/tmp") if Path("C:/tmp").exists() else Path(tempfile.gettempdir())
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.bisg import (  # noqa: E402
    bisg_posterior,
    bootstrap_proxy_distributions,
    build_measurement_error_sensitivity,
    confidence_interval,
    load_reference_table,
    parse_measurement_error_sensitivity_config,
    proxy_weighted_counts,
    run_bisg_proxy_analysis,
)
from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402

PORTFOLIO = ROOT / "data" / "synthetic" / "monthly-portfolio"
SURNAMES = load_reference_table(ROOT / "data" / "reference" / "bisg" / "demo-surname-probabilities.json")
GEOGRAPHIES = load_reference_table(ROOT / "data" / "reference" / "bisg" / "demo-geography-probabilities.json")
with (ROOT / "data" / "reference" / "bisg" / "national-marginals.json").open(encoding="utf-8") as handle:
    MARGINALS = {key: float(value) for key, value in json.load(handle).items()}


def legacy_rate_difference_ci_width(comparison: dict[str, object]) -> float:
    legacy = comparison["legacy_rounded_count_comparison"]
    group_a = legacy["group_a"]
    group_b = legacy["group_b"]
    rate_a = group_a["successes"] / group_a["total"]
    rate_b = group_b["successes"] / group_b["total"]
    standard_error = math.sqrt(
        rate_a * (1.0 - rate_a) / group_a["total"]
        + rate_b * (1.0 - rate_b) / group_b["total"]
    )
    return 2.0 * 1.959963984540054 * standard_error


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
        self.assertEqual(results["inference_method"], "applicant_level_posterior_predictive_bootstrap")
        self.assertEqual(results["bootstrap"]["draws"], 2000)
        sensitivity_config = results["measurement_error_sensitivity"]
        self.assertTrue(sensitivity_config["enabled"])
        self.assertEqual(
            sensitivity_config["method"],
            "per_applicant_absolute_posterior_error_sensitivity",
        )
        self.assertEqual(sensitivity_config["finding_probability_error_margin"], 0.05)
        self.assertEqual(results["matched_decision_count"], len(decisions))
        self.assertEqual(results["unmatched_decision_count"], 0)
        for category in ("white", "black", "hispanic", "api"):
            metrics = results["group_metrics"][category]
            self.assertTrue(metrics["adequate_effective_sample"], category)
            self.assertGreater(metrics["effective_sample_size"], 0.0, category)
            self.assertIsNotNone(metrics["bootstrap_approval_rate_ci"]["lower"], category)
            self.assertIsNotNone(metrics["bootstrap_approval_rate_ci"]["upper"], category)
        # Small expected proxy-weighted groups must be excluded from comparisons, not silently tested.
        self.assertTrue(results["comparisons"]["aian"].get("skipped"))
        self.assertFalse(
            results["comparisons"]["aian"]["sample_gate"]["proxy_weighted_total_meets_minimum"]
        )
        # Every executed comparison carries bootstrap inference plus the legacy rounded-count diagnostic.
        for category, comparison in results["comparisons"].items():
            if comparison.get("skipped"):
                continue
            self.assertIn("p_value", comparison, category)
            self.assertEqual(comparison["test"], "applicant_level_posterior_predictive_bootstrap", category)
            self.assertIn("bootstrap", comparison, category)
            self.assertIn("legacy_rounded_count_comparison", comparison, category)
            self.assertIn("measurement_error_sensitivity", comparison, category)
            self.assertIn("finding_gate", comparison, category)
            self.assertEqual(
                comparison["finding_gate"]["method"],
                "bootstrap_ci_plus_measurement_error_sensitivity",
            )
            self.assertTrue(comparison["caveats"], category)

        hispanic = results["comparisons"]["hispanic"]
        bootstrap_ci = hispanic["bootstrap"]["rate_difference_ci"]
        self.assertLessEqual(bootstrap_ci["lower"], 0.0)
        self.assertGreaterEqual(bootstrap_ci["upper"], 0.0)
        self.assertFalse(hispanic["statistically_significant"])

    def test_measurement_error_sensitivity_contains_proxy_estimate_and_widens(self) -> None:
        decisions = json.loads((PORTFOLIO / "application-decision-records.json").read_text(encoding="utf-8"))
        demographic_inputs = json.loads((PORTFOLIO / "applicant-demographic-inputs.json").read_text(encoding="utf-8"))
        config = json.loads((PORTFOLIO / "bisg-config.json").read_text(encoding="utf-8"))
        results = run_bisg_proxy_analysis(decisions, demographic_inputs, config, PORTFOLIO)

        comparison = results["comparisons"]["hispanic"]
        point_estimate = comparison["effect_size"]["rate_difference"]
        sensitivity = comparison["measurement_error_sensitivity"]
        widths = []
        for entry in sensitivity["grid"]:
            interval = entry["rate_difference_interval"]
            self.assertLessEqual(interval["lower"], point_estimate)
            self.assertGreaterEqual(interval["upper"], point_estimate)
            widths.append(interval["upper"] - interval["lower"])
        self.assertEqual(widths, sorted(widths))
        self.assertEqual(sensitivity["grid"][0]["probability_error_margin"], 0.0)
        self.assertEqual(
            sensitivity["grid"][0]["rate_difference_interval"],
            {"lower": point_estimate, "upper": point_estimate},
        )

    def test_measurement_error_sensitivity_blocks_overconfident_finding(self) -> None:
        records = []
        for index in range(100):
            records.append(
                {
                    "approved": index < 55,
                    "posterior": {
                        "white": 0.0,
                        "black": 0.0,
                        "hispanic": 1.0,
                        "api": 0.0,
                        "aian": 0.0,
                        "multiracial": 0.0,
                    },
                }
            )
        for index in range(100):
            records.append(
                {
                    "approved": index < 60,
                    "posterior": {
                        "white": 1.0,
                        "black": 0.0,
                        "hispanic": 0.0,
                        "api": 0.0,
                        "aian": 0.0,
                        "multiracial": 0.0,
                    },
                }
            )
        sensitivity_config = parse_measurement_error_sensitivity_config(
            {
                "measurement_error_sensitivity": {
                    "probability_error_margins": [0.0, 0.1],
                    "finding_probability_error_margin": 0.1,
                }
            }
        )
        sensitivity = build_measurement_error_sensitivity(
            records=records,
            category="hispanic",
            reference_group="white",
            point_rate_difference=-0.05,
            bootstrap_ci={"level": 0.95, "lower": -0.06, "upper": -0.04},
            sensitivity_config=sensitivity_config,
        )

        gate = sensitivity["finding_gate"]
        self.assertFalse(gate["excludes_zero_in_adverse_direction"])
        self.assertEqual(gate["rate_difference_interval"]["direction"], "includes_zero")


    def test_posterior_predictive_bootstrap_widens_ambiguous_proxy_interval(self) -> None:
        records = [
            {
                "approved": index < 40,
                "posterior": {
                    "white": 0.5,
                    "black": 0.0,
                    "hispanic": 0.5,
                    "api": 0.0,
                    "aian": 0.0,
                    "multiracial": 0.0,
                },
            }
            for index in range(80)
        ]
        weighted = proxy_weighted_counts(records)
        bootstrap = bootstrap_proxy_distributions(
            records=records,
            reference_group="white",
            draws=2000,
            seed=20260726,
        )
        bootstrap_ci = confidence_interval(
            bootstrap["comparison_draws"]["hispanic"]["rate_difference"],
            0.95,
        )
        bootstrap_width = bootstrap_ci["upper"] - bootstrap_ci["lower"]
        legacy_comparison = {
            "legacy_rounded_count_comparison": {
                "group_a": {
                    "successes": int(round(weighted["hispanic"]["approved"])),
                    "total": int(round(weighted["hispanic"]["total"])),
                },
                "group_b": {
                    "successes": int(round(weighted["white"]["approved"])),
                    "total": int(round(weighted["white"]["total"])),
                },
            }
        }
        self.assertGreater(bootstrap_width, legacy_rate_difference_ci_width(legacy_comparison))

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
