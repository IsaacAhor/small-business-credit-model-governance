"""Generate deterministic reviewer outputs for a validated vendor-risk bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .vendor_risk import (
    CORE_CONTEXT_FILENAMES,
    VENDOR_INPUT_FILENAMES,
    load_vendor_payloads,
    resolve_evidence_reference,
    validate_vendor_risk_dataset,
)

SUMMARY_FILENAME = "vendor-oversight-summary.json"
REPORT_FILENAME = "vendor-oversight-report.md"
MANIFEST_FILENAME = "vendor-oversight-manifest.json"
OPEN_FINDINGS_FILENAME = "vendor-open-findings.json"
OUTPUT_FILENAMES = (
    SUMMARY_FILENAME,
    REPORT_FILENAME,
    OPEN_FINDINGS_FILENAME,
    MANIFEST_FILENAME,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_manifest_input(path: Path) -> str:
    """Hash stable JSON meaning or normalized UTF-8 text for cross-platform inputs."""
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


def write_json(path: Path, payload: Any) -> None:
    write_text_lf(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _gap(gap_id: str, severity: str, description: str) -> dict[str, str]:
    return {"gap_id": gap_id, "severity": severity, "description": description}


def build_vendor_summary(payloads: dict[str, Any]) -> dict[str, Any]:
    review = payloads["vendor-risk-review-record.json"]
    components = payloads["vendor-model-components.json"]
    limitations = payloads["vendor-model-limitations.json"]
    config = payloads["vendor-oversight-config.json"]
    events = payloads["vendor-event-records.json"]
    notices = payloads["business-credit-notice-controls.json"]

    open_findings = sorted(
        [item for item in review["findings"] if item["status"] == "open"],
        key=lambda item: item["finding_id"],
    )
    gaps: list[dict[str, str]] = []
    if open_findings:
        gaps.append(
            _gap(
                "open-vendor-findings",
                max(
                    (item["severity"] for item in open_findings),
                    key=("low", "moderate", "high", "critical").index,
                ),
                f"{len(open_findings)} vendor oversight finding(s) remain open.",
            )
        )
    pending_sources = sorted(
        item["source_id"]
        for item in review["applicability_determinations"]
        if item["applicability"] == "pending_determination"
    )
    if pending_sources:
        gaps.append(
            _gap(
                "pending-applicability",
                "high",
                "Applicability remains pending for: " + ", ".join(pending_sources),
            )
        )
    if review["signoff"]["independence_status"] not in {
        "independent_internal",
        "independent_external",
    }:
        gaps.append(
            _gap(
                "independent-review-not-established",
                "high",
                "The vendor bundle does not establish an independent reviewer role.",
            )
        )
    partial_components = sorted(
        item["component_id"]
        for item in components
        if item["transparency_state"] in {"partial", "opaque"}
    )
    if partial_components:
        gaps.append(
            _gap(
                "vendor-transparency-limited",
                "moderate",
                "Partial or opaque vendor information is recorded for: "
                + ", ".join(partial_components),
            )
        )
    pending_limitations = sorted(
        item["limitation_id"]
        for item in limitations
        if item["validation_status"] in {"not_started", "pending", "not_available"}
        or item["residual_risk_decision"] == "pending"
    )
    if pending_limitations:
        gaps.append(
            _gap(
                "limitation-review-incomplete",
                "high",
                "Limitation review remains incomplete for: " + ", ".join(pending_limitations),
            )
        )
    pending_events = sorted(
        item["event_id"]
        for item in events
        if item["assessment_disposition"] == "pending"
        or item["remediation_status"] in {"open", "in_progress"}
    )
    if pending_events:
        gaps.append(
            _gap(
                "vendor-event-review-incomplete",
                "high",
                "Vendor event assessment or remediation remains incomplete for: "
                + ", ".join(pending_events),
            )
        )
    notice_gaps = sorted(
        item["notice_control_id"]
        for item in notices
        if item["specific_reason_review"] in {"pending", "gap_identified"}
        or item["reviewer_disposition"] == "pending"
    )
    if notice_gaps:
        gaps.append(
            _gap(
                "notice-control-review-incomplete",
                "high",
                "Business-credit notice review remains incomplete for: "
                + ", ".join(notice_gaps),
            )
        )
    if "adverse_action_reason_support" in review["covered_use_cases"] and not notices:
        gaps.append(
            _gap(
                "notice-control-evidence-not-supplied",
                "high",
                "Adverse-action reason support is in scope, but no business-credit notice-control evidence was supplied.",
            )
        )
    pending_conditional_sources = sorted(
        item["notice_control_id"]
        for item in notices
        if "pending_determination"
        in {
            item["fcra_applicability"],
            item["esign_applicability"],
            item["section_1071_applicability"],
        }
    )
    if pending_conditional_sources:
        gaps.append(
            _gap(
                "conditional-notice-applicability-pending",
                "moderate",
                "One or more conditional FCRA, E-SIGN, or Section 1071 determinations remain pending for: "
                + ", ".join(pending_conditional_sources),
            )
        )

    return {
        "result_type": "synthetic_vendor_oversight_summary_not_compliance_or_regulatory_approval",
        "review": {
            "review_id": review["review_id"],
            "vendor_id": review["vendor_id"],
            "product_id": review["product_id"],
            "product_version": review["product_version"],
            "review_period_start": review["review_period_start"],
            "review_period_end": review["review_period_end"],
            "covered_use_cases": sorted(review["covered_use_cases"]),
            "decision_impact": review["decision_impact"],
            "decision_authority": review["decision_authority"],
            "risk_tier": review["risk_tier"],
            "risk_rationale": review["risk_rationale"],
            "review_status": review["review_status"],
            "signoff": review["signoff"],
        },
        "applicability_determinations": sorted(
            review["applicability_determinations"], key=lambda item: item["source_id"]
        ),
        "components": sorted(components, key=lambda item: item["component_id"]),
        "limitations": sorted(limitations, key=lambda item: item["limitation_id"]),
        "monitoring": config,
        "events": sorted(events, key=lambda item: item["event_id"]),
        "business_credit_notice_controls": sorted(
            notices, key=lambda item: item["notice_control_id"]
        ),
        "open_findings": open_findings,
        "review_gaps": gaps,
        "limitations_of_output": [
            "All vendor, product, institution, reviewer, contract, and event records in the checked-in fixture are synthetic.",
            "This output does not establish institutional adoption, model accuracy, notice legal sufficiency, compliance, safety, soundness, security, reliability, or regulatory approval.",
            "Source applicability and risk acceptance require institution-specific legal, compliance, model-risk, security, and business review.",
        ],
    }


def render_vendor_report(summary: dict[str, Any]) -> str:
    review = summary["review"]
    monitoring = summary["monitoring"]
    lines = [
        "# Synthetic Vendor Oversight Review",
        "",
        "> Demonstration records only. This report is not a legal opinion, compliance certification, regulatory approval, institutional adoption claim, or production validation.",
        "",
        "## Review context",
        "",
        f"- Review: `{review['review_id']}`",
        f"- Fictional vendor / product: `{review['vendor_id']}` / `{review['product_id']}`",
        f"- Product version: `{review['product_version']}`",
        f"- Review period: `{review['review_period_start']}` through `{review['review_period_end']}`",
        f"- Decision impact / authority: `{review['decision_impact']}` / `{review['decision_authority']}`",
        f"- Risk tier: `{review['risk_tier']}`",
        f"- Review status: `{review['review_status']}`",
        "",
        "## Applicability record",
        "",
    ]
    for item in summary["applicability_determinations"]:
        lines.append(
            f"- `{item['source_id']}` — class `{item['source_class']}`, "
            f"status `{item['applicability']}`, checked `{item['checked_on']}`"
        )
    lines.extend(["", "## Component inventory and transparency", ""])
    for item in summary["components"]:
        lines.append(
            f"- `{item['component_id']}` — `{item['component_type']}`, role "
            f"`{item['decision_role']}`, transparency `{item['transparency_state']}`"
        )
    lines.extend(["", "## Limitations and compensating controls", ""])
    for item in summary["limitations"]:
        lines.append(
            f"- `{item['limitation_id']}` — {item['description']} "
            f"Control: {item['compensating_control']} Residual decision: "
            f"`{item['residual_risk_decision']}`."
        )
    if not summary["limitations"]:
        lines.append("- No limitation records were supplied.")
    lines.extend(
        [
            "",
            "## Monitoring and heightened review",
            "",
            f"- Cadence: {monitoring['review_cadence']}",
            f"- Rationale: {monitoring['cadence_rationale']}",
            f"- Heightened monitoring: `{monitoring['heightened_monitoring']['status']}`",
            "",
            "## Vendor events and change review",
            "",
        ]
    )
    for item in summary["events"]:
        lines.append(
            f"- `{item['event_id']}` — `{item['event_type']}`, materiality "
            f"`{item['materiality']}`, assessment `{item['assessment_disposition']}`"
        )
    if not summary["events"]:
        lines.append("- No vendor events are recorded for this synthetic review period.")
    lines.extend(["", "## Business-credit notice controls", ""])
    for item in summary["business_credit_notice_controls"]:
        lines.append(
            f"- `{item['notice_control_id']}` for `{item['decision_id']}` — path "
            f"`{item['path_determination']}`, specific-reason review "
            f"`{item['specific_reason_review']}`, disposition `{item['reviewer_disposition']}`"
        )
    if not summary["business_credit_notice_controls"]:
        lines.append("- No business-credit notice-control evidence was supplied.")
    lines.extend(["", "## Open findings and review gaps", ""])
    if summary["open_findings"]:
        for item in summary["open_findings"]:
            lines.append(
                f"- Finding `{item['finding_id']}` (`{item['severity']}`): {item['summary']}"
            )
    else:
        lines.append("- No open finding is recorded in the synthetic review record.")
    for item in summary["review_gaps"]:
        lines.append(f"- Gap **{item['gap_id']}** (`{item['severity']}`): {item['description']}")
    lines.extend(["", "## Output limitations", ""])
    for item in summary["limitations_of_output"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def collect_evidence_references(payloads: dict[str, Any]) -> list[str]:
    review = payloads["vendor-risk-review-record.json"]
    references = set(review["evidence_references"])
    references.update(
        item["evidence_reference"] for item in review["applicability_determinations"]
    )
    references.update(item["evidence_reference"] for item in review["document_versions"])
    for item in payloads["vendor-model-limitations.json"]:
        references.update(item["evidence_references"])
    for item in payloads["vendor-event-records.json"]:
        references.update(item["evidence_references"])
    for item in payloads["business-credit-notice-controls.json"]:
        references.update(item["reason_source_references"])
        references.update(item["evidence_references"])
    return sorted(references)


def supporting_evidence_manifest_entries(
    payloads: dict[str, Any], vendor_dir: Path, core_dir: Path
) -> list[dict[str, str]]:
    excluded = {
        (vendor_dir / filename).resolve() for filename in VENDOR_INPUT_FILENAMES
    } | {(core_dir / filename).resolve() for filename in CORE_CONTEXT_FILENAMES}
    entries: list[dict[str, str]] = []
    seen: set[Path] = set()
    for reference in collect_evidence_references(payloads):
        path = resolve_evidence_reference(reference, vendor_dir, core_dir)
        if path is None:
            raise ValueError(f"supporting evidence disappeared after validation: {reference}")
        resolved = path.resolve()
        if resolved in excluded or resolved in seen:
            continue
        seen.add(resolved)
        if resolved == vendor_dir or vendor_dir in resolved.parents:
            source = "vendor_evidence"
            filename = resolved.relative_to(vendor_dir).as_posix()
        elif resolved == core_dir or core_dir in resolved.parents:
            source = "core_evidence"
            filename = resolved.relative_to(core_dir).as_posix()
        else:
            source = "repository_evidence"
            filename = reference
        entries.append(
            {
                "source": source,
                "filename": filename,
                "sha256": sha256_manifest_input(resolved),
            }
        )
    return sorted(entries, key=lambda item: (item["source"], item["filename"]))


def generate_vendor_oversight_report(
    vendor_dir: Path,
    core_dir: Path,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    vendor_dir = vendor_dir.resolve()
    core_dir = core_dir.resolve()
    output_dir = output_dir.resolve()
    result = validate_vendor_risk_dataset(vendor_dir, core_dir)
    if not result.ok:
        raise ValueError("vendor dataset validation failed: " + "; ".join(result.errors))
    payloads = load_vendor_payloads(vendor_dir, core_dir)
    summary = build_vendor_summary(payloads)

    existing = [name for name in OUTPUT_FILENAMES if (output_dir / name).exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "refusing to overwrite existing vendor output(s): " + ", ".join(existing)
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    staging = output_dir / f".vendor-oversight-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        summary_path = staging / SUMMARY_FILENAME
        report_path = staging / REPORT_FILENAME
        findings_path = staging / OPEN_FINDINGS_FILENAME
        write_json(summary_path, summary)
        write_text_lf(report_path, render_vendor_report(summary))
        write_json(findings_path, summary["open_findings"])
        manifest = {
            "record_type": "vendor_oversight_manifest",
            "result_type": "reproducibility_manifest_not_validation_or_regulatory_approval",
            "hash_policy": "sha256_canonical_json_or_lf_text_inputs_raw_generated_outputs_v1",
            "review_id": summary["review"]["review_id"],
            "inputs": [
                {
                    "source": "core_context",
                    "filename": filename,
                    "sha256": sha256_manifest_input(core_dir / filename),
                }
                for filename in sorted(CORE_CONTEXT_FILENAMES)
            ]
            + [
                {
                    "source": "vendor_dataset",
                    "filename": filename,
                    "sha256": sha256_manifest_input(vendor_dir / filename),
                }
                for filename in sorted(VENDOR_INPUT_FILENAMES)
            ]
            + supporting_evidence_manifest_entries(payloads, vendor_dir, core_dir),
            "outputs": [
                {"filename": SUMMARY_FILENAME, "sha256": sha256_file(summary_path)},
                {"filename": REPORT_FILENAME, "sha256": sha256_file(report_path)},
                {"filename": OPEN_FINDINGS_FILENAME, "sha256": sha256_file(findings_path)},
            ],
        }
        write_json(staging / MANIFEST_FILENAME, manifest)
        for filename in OUTPUT_FILENAMES:
            os.replace(staging / filename, output_dir / filename)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic reviewer report for a validated synthetic vendor-risk bundle."
    )
    parser.add_argument("vendor_dataset_dir", type=Path)
    parser.add_argument("core_dataset_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = generate_vendor_oversight_report(
            args.vendor_dataset_dir,
            args.core_dataset_dir,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"vendor oversight report failed: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
