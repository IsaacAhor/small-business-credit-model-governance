"""Deterministically build the larger synthetic 'monthly-portfolio' dataset.

This script regenerates ``data/synthetic/monthly-portfolio/`` from a fixed seed
so the dataset is reproducible evidence rather than hand-authored fixtures. It
also invokes the Phase 3B reason-generation module so the shipped
adverse-action reason outputs are provably generated, not typed by hand.

Everything here is synthetic. No production data, no protected-class labels,
and no legal conclusions are represented.

Usage:
    python scripts/build_portfolio_dataset.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.generation import generate_adverse_action_reasons, summarize_generation  # noqa: E402

SEED = 42
DECISION_COUNT = 320
MODEL_ID = "mdl-smb-credit-xgb"
VERSION_ID = "ver-2026-06"
RUN_ID = "run-2026-06"
MAPPING_VERSION = "mapver-2026-06"
DATASET_DIR = ROOT / "data" / "synthetic" / "monthly-portfolio"

REGIONS = ["south", "midwest", "northeast", "west"]
REGION_WEIGHTS = [0.30, 0.25, 0.25, 0.20]
SEGMENTS = ["micro", "small", "medium"]
SEGMENT_WEIGHTS = [0.5, 0.35, 0.15]
CHANNELS = ["digital", "branch", "broker"]

# Baseline model applies a region-specific score cutoff. The west cutoff is
# deliberately stricter, which creates the group approval-rate disparity the
# fair-lending screen and the LDA assessment are designed to surface.
BASELINE_CUTOFF = {"south": 545.0, "midwest": 560.0, "northeast": 552.0, "west": 660.0}
# The candidate alternative applies one region-neutral cutoff (removes the
# region-specific penalty) -- a plausible less-discriminatory alternative.
ALTERNATIVE_CUTOFF = 570.0

# Governed reason-code mappings (driver -> reason code).
DRIVER_TO_CODE = [
    ("cash_flow_stability", "RC-101", "Insufficient cash flow stability"),
    ("debt_service_coverage", "RC-102", "Debt service coverage below policy range"),
    ("time_in_business", "RC-103", "Limited time in business"),
    ("credit_utilization", "RC-104", "Elevated credit utilization"),
    ("collateral_coverage", "RC-105", "Insufficient collateral coverage"),
    ("industry_risk", "RC-106", "Elevated industry risk profile"),
]
DRIVERS = [driver for driver, _code, _text in DRIVER_TO_CODE]

# A small number of declined decisions are seeded with no driver contributions
# to produce a realistic, low-rate crop of reason-QA 'missing_reason_code'
# exceptions (declined decision with no generated reason).
MISSING_CONTRIB_EVERY = 90

# Synthetic demographic inputs for BISG proxy estimation. Surname pools are
# correlated with region so the proxied groups differ across regions -- which,
# combined with the stricter west cutoff, gives the BISG screen a realistic
# disparity signal to surface. Drawn from a SEPARATE seeded RNG so adding this
# section leaves every previously generated file byte-identical.
DEMOGRAPHIC_SEED = SEED + 1
REGION_SURNAME_POOLS: dict[str, tuple[list[str], list[float]]] = {
    "south": (
        ["SMITH", "JOHNSON", "WILLIAMS", "WASHINGTON", "JEFFERSON", "DAVIS", "BROWN", "GARCIA"],
        [0.20, 0.16, 0.14, 0.12, 0.08, 0.12, 0.12, 0.06],
    ),
    "midwest": (
        ["SMITH", "MILLER", "JOHNSON", "DAVIS", "BROWN", "NGUYEN"],
        [0.26, 0.24, 0.18, 0.14, 0.12, 0.06],
    ),
    "northeast": (
        ["SMITH", "JOHNSON", "CHEN", "KIM", "PATEL", "MILLER", "RODRIGUEZ"],
        [0.22, 0.16, 0.12, 0.10, 0.10, 0.16, 0.14],
    ),
    "west": (
        ["GARCIA", "RODRIGUEZ", "MARTINEZ", "LOPEZ", "NGUYEN", "KIM", "CHEN", "LEE", "SMITH", "BEGAY"],
        [0.16, 0.14, 0.12, 0.10, 0.10, 0.08, 0.08, 0.08, 0.10, 0.04],
    ),
}


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def score_band(score: float) -> str:
    if score >= 720:
        return "A"
    if score >= 640:
        return "B"
    if score >= 560:
        return "C"
    if score >= 480:
        return "D"
    return "E"


def weighted_choice(rng: random.Random, options: list[str], weights: list[float]) -> str:
    return rng.choices(options, weights=weights, k=1)[0]


def build() -> None:
    rng = random.Random(SEED)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    decisions: list[dict] = []
    scores: list[dict] = []
    outcomes: list[dict] = []
    overrides: list[dict] = []
    driver_contributions: list[dict] = []
    alternative_decisions: list[dict] = []

    override_seq = 0
    for i in range(1, DECISION_COUNT + 1):
        decision_id = f"dec-{i:04d}"
        region = weighted_choice(rng, REGIONS, REGION_WEIGHTS)
        segment = weighted_choice(rng, SEGMENTS, SEGMENT_WEIGHTS)
        channel = rng.choice(CHANNELS)

        # Latent applicant quality drives both score and true repayment outcome.
        quality = rng.random()
        score_value = round(300.0 + 550.0 * quality + rng.uniform(-25.0, 25.0), 1)
        score_value = max(300.0, min(900.0, score_value))
        true_good = rng.random() < (0.25 + 0.6 * quality)

        baseline_approved = score_value >= BASELINE_CUTOFF[region]
        alternative_approved = score_value >= ALTERNATIVE_CUTOFF

        manual_review_flag = rng.random() < 0.18
        override_flag = rng.random() < 0.12
        outcome_label = "approved" if baseline_approved else "declined"

        day = (i % 27) + 1
        hour = (i % 12) + 8
        minute = (i * 7) % 60
        decisions.append(
            {
                "record_type": "application_decision_record",
                "decision_id": decision_id,
                "application_date": f"2026-06-{day:02d}",
                "segment": segment,
                "decision_outcome": outcome_label,
                "manual_review_flag": manual_review_flag,
                "override_flag": override_flag,
                "underwriting": {
                    "score": score_value,
                    "requested_amount": float(rng.choice([25000, 45000, 60000, 90000, 120000])),
                    "decision_timestamp": f"2026-06-{day:02d}T{hour:02d}:{minute:02d}:00Z",
                },
                "monitoring": {
                    "region": region,
                    "channel": channel,
                    "review_batch_id": RUN_ID,
                },
            }
        )
        scores.append(
            {
                "record_type": "score_output",
                "decision_id": decision_id,
                "score_value": score_value,
                "score_band": score_band(score_value),
                "score_version": VERSION_ID,
            }
        )
        outcomes.append(
            {
                "record_type": "outcome_record",
                "outcome_id": f"out-{i:04d}",
                "decision_id": decision_id,
                "observation_period": "6m",
                "repayment_or_default_indicator": "performing" if true_good else rng.choice(["delinquent", "default"]),
                "realized_outcome_value": 1.0 if true_good else 0.0,
            }
        )
        if override_flag:
            override_seq += 1
            overrides.append(
                {
                    "record_type": "override_event",
                    "override_id": f"ovr-{override_seq:04d}",
                    "decision_id": decision_id,
                    "override_type": "manual_decline" if outcome_label == "declined" else "manual_approval",
                    "override_reason": "Analyst review recorded for governance demonstration.",
                    "reviewer": "Credit Policy Analyst",
                    "override_date": f"2026-06-{day:02d}",
                }
            )
        alternative_decisions.append(
            {
                "decision_id": decision_id,
                "alternative_outcome": "approved" if alternative_approved else "declined",
                "alternative_model_id": f"{MODEL_ID}-altcut",
            }
        )

        # Driver contributions only for declined decisions (adverse action).
        if outcome_label == "declined":
            if i % MISSING_CONTRIB_EVERY == 0:
                contributions: list[dict] = []  # seeded gap -> reason QA exception
            else:
                k = rng.randint(2, 4)
                chosen = rng.sample(DRIVERS, k)
                contributions = [
                    {
                        "driver_or_signal": driver,
                        "contribution": round(rng.uniform(0.15, 0.6), 4),
                        "direction": "adverse",
                    }
                    for driver in chosen
                ]
            driver_contributions.append(
                {"decision_id": decision_id, "contributions": contributions}
            )

    reason_mappings = [
        {
            "record_type": "reason_code_mapping",
            "mapping_id": f"map-{index:03d}",
            "version_id": VERSION_ID,
            "driver_or_signal": driver,
            "reason_code": code,
            "reason_text": text,
            "mapping_version": MAPPING_VERSION,
        }
        for index, (driver, code, text) in enumerate(DRIVER_TO_CODE, start=1)
    ]

    reason_outputs = generate_adverse_action_reasons(
        decisions=decisions,
        driver_contributions=driver_contributions,
        reason_mappings=reason_mappings,
        version_id=VERSION_ID,
    )

    model_registry = {
        "record_type": "model_registry_record",
        "model_id": MODEL_ID,
        "model_name": "Small Business Credit Underwriting Model",
        "business_owner": "Small Business Credit Risk",
        "technical_owner": "Model Risk Governance",
        "intended_use": "Risk-rank small business applicants for manual and automated underwriting review.",
        "target_population": "U.S. small business credit applicants",
        "status": "active",
        "monitoring_only_fields": ["region", "channel", "review_batch_id"],
        "underwriting_fields": ["score", "requested_amount", "decision_timestamp"],
    }
    model_version = {
        "record_type": "model_version_record",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "effective_date": "2026-06-01",
        "change_summary": "Portfolio-scale monthly monitoring demonstration version with 320 synthetic decisions.",
        "assumptions": [
            "Synthetic records approximate reviewer-visible control artifacts.",
            "Monitoring thresholds are illustrative and governance-oriented.",
        ],
        "limitations": [
            "No production lending decisions are represented.",
            "No protected-class labels or legal conclusions are embedded.",
        ],
        "linked_validation_record": "val-portfolio-demo",
    }
    threshold_set = {
        "record_type": "threshold_set",
        "threshold_set_id": "thr-2026-06-monthly",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "review_cadence": "monthly",
        "thresholds": [
            {
                "metric_name": "approval_rate",
                "comparison_rule": "less_than",
                "threshold_value": 0.35,
                "severity": "medium",
                "escalation_owner": "Model Risk Governance",
            },
            {
                "metric_name": "override_rate",
                "comparison_rule": "greater_than",
                "threshold_value": 0.1,
                "severity": "high",
                "escalation_owner": "Credit Policy Review",
            },
        ],
    }
    fair_lending_config = {
        "record_type": "fair_lending_screening_config",
        "screening_config_id": "fls-2026-06-monthly",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "comparison_groups": [
            {"group_name": "region", "source": "monitoring", "field": "region"},
            {"group_name": "segment", "source": "decision", "field": "segment"},
        ],
        "screens": [
            {
                "screen_name": "Regional approval-rate ratio",
                "metric_name": "approval_rate_ratio",
                "comparison_rule": "less_than",
                "threshold_value": 0.8,
                "severity": "medium",
                "escalation_owner": "Fair Lending Review",
            },
            {
                "screen_name": "Regional override-rate difference",
                "metric_name": "override_rate_difference",
                "comparison_rule": "greater_than",
                "threshold_value": 0.25,
                "severity": "medium",
                "escalation_owner": "Fair Lending Review",
            },
            {
                "screen_name": "Reason-code concentration by segment",
                "metric_name": "reason_code_concentration",
                "comparison_rule": "greater_than",
                "threshold_value": 0.75,
                "severity": "low",
                "escalation_owner": "Model Risk Governance",
            },
        ],
    }
    lda_config = {
        "record_type": "lda_assessment_config",
        "assessment_id": "lda-2026-06-monthly",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "group_source": "monitoring",
        "group_field": "region",
        "performance_metric": "approval_good_bad_separation",
        "disparity_metric": "approval_rate_ratio",
        "min_disparity_improvement": 0.05,
        "performance_tolerance": 0.03,
        "outcome_good_indicator": "performing",
    }
    manifest = {
        "record_type": "evidence_pack_manifest",
        "run_id": RUN_ID,
        "created_at": "2026-07-01T12:00:00Z",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "input_references": [
            "model-registry-record.json",
            "model-version-record.json",
            "threshold-set.json",
            "fair-lending-screening-config.json",
            "application-decision-records.json",
            "adverse-action-reason-outputs.json",
        ],
        "output_files": [
            "metric_results.json",
            "breach_register.json",
            "reason_qa_results.json",
            "reason_stability_report.json",
            "fair_lending_screening_results.json",
            "fair_lending_escalation_register.json",
            "lda_assessment_results.json",
            "reviewer_notes.md",
            "monitoring_report.md",
        ],
        "reviewer_status": "pending_review",
    }

    write_json(DATASET_DIR / "model-registry-record.json", model_registry)
    write_json(DATASET_DIR / "model-version-record.json", model_version)
    write_json(DATASET_DIR / "threshold-set.json", threshold_set)
    write_json(DATASET_DIR / "fair-lending-screening-config.json", fair_lending_config)
    write_json(DATASET_DIR / "application-decision-records.json", decisions)
    write_json(DATASET_DIR / "score-outputs.json", scores)
    write_json(DATASET_DIR / "reason-code-mappings.json", reason_mappings)
    write_json(DATASET_DIR / "adverse-action-driver-contributions.json", driver_contributions)
    write_json(DATASET_DIR / "adverse-action-reason-outputs.json", reason_outputs)
    write_json(DATASET_DIR / "override-events.json", overrides)
    write_json(DATASET_DIR / "outcome-records.json", outcomes)
    write_json(DATASET_DIR / "breach-records.json", [])
    write_json(DATASET_DIR / "alternative-model-decisions.json", alternative_decisions)
    write_json(DATASET_DIR / "lda-assessment-config.json", lda_config)
    write_json(DATASET_DIR / "evidence-pack-manifest.json", manifest)

    demographic_rng = random.Random(DEMOGRAPHIC_SEED)
    demographic_inputs = []
    for decision in decisions:
        region = decision["monitoring"]["region"]
        surnames, weights = REGION_SURNAME_POOLS[region]
        demographic_inputs.append(
            {
                "record_type": "applicant_demographic_input",
                "decision_id": decision["decision_id"],
                "surname": weighted_choice(demographic_rng, surnames, weights),
                "geography_id": f"GEO-{region.upper()}-{demographic_rng.choice([1, 2])}",
            }
        )
    bisg_config = {
        "record_type": "bisg_config",
        "config_id": "bisg-2026-06-monthly",
        "surname_reference_path": "data/reference/bisg/demo-surname-probabilities.json",
        "geography_reference_path": "data/reference/bisg/demo-geography-probabilities.json",
        "national_marginals_path": "data/reference/bisg/national-marginals.json",
        "reference_group": "white",
        "alpha": 0.05,
        "min_effective_count": 10,
        "bootstrap_draws": 2000,
        "bootstrap_seed": 20260726,
        "bootstrap_ci_level": 0.95,
        "measurement_error_sensitivity": {
            "enabled": True,
            "method": "per_applicant_absolute_posterior_error_sensitivity",
            "probability_error_margins": [0.0, 0.025, 0.05, 0.1],
            "finding_probability_error_margin": 0.05,
            "assumption": (
                "Each applicant's group-specific BISG posterior may vary independently "
                "within +/- the configured probability-error margin, clipped to [0, 1]."
            ),
        },
    }
    write_json(DATASET_DIR / "applicant-demographic-inputs.json", demographic_inputs)
    write_json(DATASET_DIR / "bisg-config.json", bisg_config)

    summary = summarize_generation(decisions, reason_outputs)
    declined = sum(1 for d in decisions if d["decision_outcome"] == "declined")
    approved = sum(1 for d in decisions if d["decision_outcome"] == "approved")
    print(f"decisions={len(decisions)} approved={approved} declined={declined}")
    print(f"overrides={len(overrides)} reason_outputs={len(reason_outputs)}")
    print(f"generation_summary={summary}")


if __name__ == "__main__":
    build()
