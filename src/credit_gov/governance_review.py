"""Build a deterministic reviewer summary from the optional governance bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .schemas.validators import (
    OPTIONAL_GOVERNANCE_FILENAMES,
    load_json,
    validate_dataset,
)

SUMMARY_FILENAME = "governance-review-summary.json"
REPORT_FILENAME = "governance-review-report.md"
MANIFEST_FILENAME = "governance-review-manifest.json"
OUTPUT_FILENAMES = (SUMMARY_FILENAME, REPORT_FILENAME, MANIFEST_FILENAME)
CORE_INPUT_FILENAMES = (
    "model-registry-record.json",
    "model-version-record.json",
    "threshold-set.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_manifest_input(path: Path) -> str:
    """Hash stable JSON meaning or normalized UTF-8 text for manifest inputs."""
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        content = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    elif path.suffix.lower() in {".md", ".txt", ".csv", ".tsv"}:
        text = path.read_text(encoding="utf-8")
        content = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    else:
        return sha256_file(path)
    return hashlib.sha256(content).hexdigest()


def write_text_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text_lf(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_governance_payloads(dataset_dir: Path) -> dict[str, Any]:
    result = validate_dataset(dataset_dir)
    if not result.ok:
        raise ValueError("dataset validation failed: " + "; ".join(result.errors))
    if not OPTIONAL_GOVERNANCE_FILENAMES.issubset(set(result.validated_files)):
        raise ValueError(
            "dataset does not contain the complete optional governance bundle"
        )
    filenames = set(CORE_INPUT_FILENAMES) | OPTIONAL_GOVERNANCE_FILENAMES
    return {filename: load_json(dataset_dir / filename) for filename in filenames}


def build_review_summary(payloads: dict[str, Any]) -> dict[str, Any]:
    registry = payloads["model-registry-record.json"]
    version = payloads["model-version-record.json"]
    risk = payloads["model-risk-profile.json"]
    methods = payloads["explainability-method-records.json"]
    validation = payloads["model-validation-record.json"]
    monitoring = payloads["model-monitoring-plan.json"]

    open_findings = [
        finding for finding in validation["findings"] if finding["status"] == "open"
    ]
    gaps: list[dict[str, str]] = []
    if validation["independence_status"] not in {
        "independent_internal",
        "independent_external",
    }:
        gaps.append(
            {
                "gap_id": "independent-validation",
                "severity": "high",
                "description": "Independent validation is not established by this bundle.",
            }
        )
    if open_findings:
        gaps.append(
            {
                "gap_id": "open-validation-findings",
                "severity": max(
                    (finding["severity"] for finding in open_findings),
                    key=("low", "moderate", "high", "critical").index,
                ),
                "description": f"{len(open_findings)} validation finding(s) remain open.",
            }
        )
    pending_directionality = [
        method["explainability_method_id"]
        for method in methods
        if method["directionality_review"] in {"not_started", "pending"}
    ]
    if pending_directionality:
        gaps.append(
            {
                "gap_id": "explanation-directionality-review",
                "severity": "moderate",
                "description": "Directionality review remains incomplete for: "
                + ", ".join(sorted(pending_directionality)),
            }
        )
    draft_methods = [
        method["explainability_method_id"]
        for method in methods
        if method["status"] != "approved"
    ]
    if draft_methods:
        gaps.append(
            {
                "gap_id": "explainability-method-approval",
                "severity": "moderate",
                "description": "Approved method status is not established for: "
                + ", ".join(sorted(draft_methods)),
            }
        )

    return {
        "result_type": "synthetic_model_governance_review_not_validation_or_approval",
        "model": {
            "model_id": registry["model_id"],
            "model_name": registry["model_name"],
            "version_id": version["version_id"],
            "intended_use": registry["intended_use"],
        },
        "risk_profile": {
            "risk_profile_id": risk["risk_profile_id"],
            "model_materiality": risk["model_materiality"],
            "inherent_risk": risk["inherent_risk"],
            "model_exposure": risk["model_exposure"],
            "validation_rigor": risk["validation_rigor"],
            "monitoring_rigor": risk["monitoring_rigor"],
            "data_constraints": risk["data_constraints"],
        },
        "explainability_methods": [
            {
                "explainability_method_id": method["explainability_method_id"],
                "method_name": method["method_name"],
                "method_family": method["method_family"],
                "scope": method["explanation_scope"],
                "reference_population_id": method["reference_population"][
                    "population_id"
                ],
                "directionality_review": method["directionality_review"],
                "status": method["status"],
                "known_limitations": method["known_limitations"],
            }
            for method in methods
        ],
        "validation": {
            "validation_id": validation["validation_id"],
            "independence_status": validation["independence_status"],
            "reviewer_identity": validation["reviewer_identity"],
            "overall_disposition": validation["overall_disposition"],
            "promotion_allowed": validation["promotion_allowed"],
            "open_findings": sorted(open_findings, key=lambda item: item["finding_id"]),
            "limitations": validation["limitations"],
        },
        "monitoring_plan": {
            "monitoring_plan_id": monitoring["monitoring_plan_id"],
            "status": monitoring["status"],
            "review_cadence": monitoring["review_cadence"],
            "metrics": monitoring["metrics"],
            "change_triggers": monitoring["change_triggers"],
            "reason_monitoring_scope": monitoring["reason_monitoring_scope"],
        },
        "review_gaps": gaps,
        "limitations": [
            "The source dataset is synthetic and does not represent production lending decisions.",
            "This output summarizes governance records; it is not an independent validation, regulatory conclusion, legal opinion, or deployment approval.",
        ],
    }


def render_review_report(summary: dict[str, Any]) -> str:
    model = summary["model"]
    risk = summary["risk_profile"]
    validation = summary["validation"]
    lines = [
        "# Model Governance Review Summary",
        "",
        "> Synthetic governance review only. This is not an independent validation, regulatory conclusion, legal opinion, or deployment approval.",
        "",
        "## Model context",
        "",
        f"- Model: `{model['model_id']}` — {model['model_name']}",
        f"- Version: `{model['version_id']}`",
        f"- Intended use: {model['intended_use']}",
        "",
        "## Risk-based governance",
        "",
        f"- Materiality: `{risk['model_materiality']}`",
        f"- Inherent risk / exposure: `{risk['inherent_risk']}` / `{risk['model_exposure']}`",
        f"- Validation / monitoring rigor: `{risk['validation_rigor']}` / `{risk['monitoring_rigor']}`",
        "",
        "## Explainability methods",
        "",
    ]
    for method in summary["explainability_methods"]:
        lines.append(
            f"- `{method['explainability_method_id']}`: {method['method_name']} "
            f"(status `{method['status']}`, directionality review "
            f"`{method['directionality_review']}`)"
        )
    lines.extend(
        [
            "",
            "## Validation posture",
            "",
            f"- Independence: `{validation['independence_status']}`",
            f"- Reviewer: {validation['reviewer_identity']}",
            f"- Disposition: `{validation['overall_disposition']}`",
            f"- Promotion allowed: `{str(validation['promotion_allowed']).lower()}`",
            f"- Open findings: `{len(validation['open_findings'])}`",
            "",
            "## Review gaps",
            "",
        ]
    )
    for gap in summary["review_gaps"]:
        lines.append(
            f"- **{gap['gap_id']}** (`{gap['severity']}`): {gap['description']}"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in summary["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def generate_governance_review(
    dataset_dir: Path, output_dir: Path, *, overwrite: bool = False
) -> dict[str, Any]:
    dataset_dir = dataset_dir.resolve()
    output_dir = output_dir.resolve()
    payloads = load_governance_payloads(dataset_dir)
    summary = build_review_summary(payloads)

    existing = [name for name in OUTPUT_FILENAMES if (output_dir / name).exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "refusing to overwrite existing review output(s): " + ", ".join(existing)
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir / f".governance-review-{uuid.uuid4().hex}"
    staging_dir.mkdir()
    try:
        summary_path = staging_dir / SUMMARY_FILENAME
        report_path = staging_dir / REPORT_FILENAME
        write_json(summary_path, summary)
        write_text_lf(report_path, render_review_report(summary))

        input_filenames = sorted(
            set(CORE_INPUT_FILENAMES) | OPTIONAL_GOVERNANCE_FILENAMES
        )
        manifest = {
            "record_type": "governance_review_manifest",
            "result_type": "reproducibility_manifest_not_validation_or_approval",
            "hash_policy": "sha256_canonical_json_or_lf_text_inputs_raw_generated_outputs_v1",
            "model_id": summary["model"]["model_id"],
            "version_id": summary["model"]["version_id"],
            "inputs": [
                {
                    "filename": filename,
                    "sha256": sha256_manifest_input(dataset_dir / filename),
                }
                for filename in input_filenames
            ],
            "outputs": [
                {"filename": SUMMARY_FILENAME, "sha256": sha256_file(summary_path)},
                {"filename": REPORT_FILENAME, "sha256": sha256_file(report_path)},
            ],
        }
        write_json(staging_dir / MANIFEST_FILENAME, manifest)
        for filename in OUTPUT_FILENAMES:
            os.replace(staging_dir / filename, output_dir / filename)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic summary of a validated governance bundle."
    )
    parser.add_argument("dataset_dir", type=Path, help="Validated dataset directory")
    parser.add_argument("output_dir", type=Path, help="Review output directory")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace only the three named governance-review output files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = generate_governance_review(
            args.dataset_dir, args.output_dir, overwrite=args.overwrite
        )
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"governance review failed: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
