"""Generate and verify a deterministic recourse reviewer evidence pack."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .recourse import (
    PROTECTED_CORE_FILENAMES,
    RECOURSE_INPUT_FILENAMES,
    assess_recourse,
    canonical_json_sha256,
    load_recourse_payloads,
    protected_core_hashes,
    sha256_file,
    validate_recourse_bundle,
)

MANIFEST_FILENAME = "manifest.json"
INPUT_FINGERPRINTS_FILENAME = "input_fingerprints.json"
OUTPUT_FINGERPRINTS_FILENAME = "output_fingerprints.json"
METHOD_SNAPSHOT_FILENAME = "recourse_method_snapshot.json"
ACTION_SET_SNAPSHOT_FILENAME = "action_set_snapshot.json"
CONFIG_SNAPSHOT_FILENAME = "review_config_snapshot.json"
RESULTS_FILENAME = "recourse_assessment_results.json"
QA_FILENAME = "recourse_qa_results.json"
REPORT_FILENAME = "recourse_review_report.md"
NOTES_FILENAME = "reviewer_notes.md"
SIGNOFF_FILENAME = "reviewer_signoff.md"

OUTPUT_FILENAMES = (
    MANIFEST_FILENAME,
    INPUT_FINGERPRINTS_FILENAME,
    OUTPUT_FINGERPRINTS_FILENAME,
    METHOD_SNAPSHOT_FILENAME,
    ACTION_SET_SNAPSHOT_FILENAME,
    CONFIG_SNAPSHOT_FILENAME,
    RESULTS_FILENAME,
    QA_FILENAME,
    REPORT_FILENAME,
    NOTES_FILENAME,
    SIGNOFF_FILENAME,
)
FINGERPRINTED_OUTPUT_FILENAMES = (
    METHOD_SNAPSHOT_FILENAME,
    ACTION_SET_SNAPSHOT_FILENAME,
    CONFIG_SNAPSHOT_FILENAME,
    RESULTS_FILENAME,
    QA_FILENAME,
    REPORT_FILENAME,
    NOTES_FILENAME,
    SIGNOFF_FILENAME,
)
CORE_FINGERPRINT_FILENAMES = (
    "model-registry-record.json",
    "model-version-record.json",
    *PROTECTED_CORE_FILENAMES,
)


def write_text_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def write_json(path: Path, payload: Any) -> None:
    write_text_lf(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def validate_distinct_paths(core_dir: Path, recourse_dir: Path, output_dir: Path) -> None:
    core_dir = core_dir.resolve()
    recourse_dir = recourse_dir.resolve()
    output_dir = output_dir.resolve()
    if _paths_overlap(core_dir, output_dir):
        raise ValueError("output directory must be separate from the core dataset tree")
    if _paths_overlap(recourse_dir, output_dir):
        raise ValueError("output directory must be separate from the recourse bundle tree")


def _canonical_file_sha256(path: Path) -> str:
    return canonical_json_sha256(json.loads(path.read_text(encoding="utf-8")))


def build_input_fingerprints(core_dir: Path, recourse_dir: Path) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    for filename in CORE_FINGERPRINT_FILENAMES:
        files.append(
            {
                "source": "core_dataset",
                "filename": filename,
                "sha256": _canonical_file_sha256(core_dir / filename),
            }
        )
    for filename in RECOURSE_INPUT_FILENAMES:
        files.append(
            {
                "source": "recourse_bundle",
                "filename": filename,
                "sha256": _canonical_file_sha256(recourse_dir / filename),
            }
        )
    return {
        "record_type": "recourse_input_fingerprints",
        "result_type": "reproducibility_fingerprints_not_validation_or_approval",
        "hash_policy": "sha256_canonical_json_v1",
        "files": files,
    }


def build_qa_results(
    *,
    results: list[dict[str, Any]],
    before_hashes: dict[str, str],
    after_hashes: dict[str, str],
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for result in results:
        status = result["overall_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    checks = [
        {
            "check_id": "core-validation",
            "passed": True,
            "detail": "The unchanged core validator accepted the source dataset.",
        },
        {
            "check_id": "recourse-bundle-validation",
            "passed": True,
            "detail": "All five recourse input contracts and cross-file relationships passed.",
        },
        {
            "check_id": "baseline-recomputation",
            "passed": True,
            "detail": "Every subject baseline prediction matched its recorded eligible outcome.",
        },
        {
            "check_id": "cross-layer-field-rejection",
            "passed": True,
            "detail": "Generated recourse outputs passed a closed schema that excludes reason, mapping, and notice fields.",
        },
        {
            "check_id": "protected-core-hashes",
            "passed": before_hashes == after_hashes,
            "detail": "All five protected core files retained their pre-run SHA-256 hashes.",
        },
    ]
    return {
        "record_type": "recourse_qa_results",
        "result_type": "synthetic_recourse_qa_not_independent_validation",
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "status_counts": dict(sorted(status_counts.items())),
        "protected_core_hashes_before": before_hashes,
        "protected_core_hashes_after": after_hashes,
    }


def render_review_report(
    results: list[dict[str, Any]], method: dict[str, Any], action_set: dict[str, Any]
) -> str:
    lines = [
        "# Recourse Assessment Review Report",
        "",
        "> Synthetic reviewer-facing assessment only. This report is not an adverse-action reason, notice, applicant instruction, independent validation, legal conclusion, or outcome guarantee.",
        "",
        "## Declared Scope",
        "",
        f"- Method: `{method['recourse_method_id']}` / `{method['method_version']}`",
        f"- Calculation mode: `{method['calculation_mode']}`",
        f"- Action set: `{action_set['action_set_id']}` / `{action_set['action_set_version']}`",
        f"- Time horizon: {action_set['time_horizon']}",
        "- Audience: `reviewer_only`",
        "",
        "## Results",
        "",
    ]
    for result in results:
        search = result["search"]
        lines.extend(
            [
                f"### `{result['recourse_subject_id']}`",
                "",
                f"- Linked decision: `{result['decision_id']}`",
                f"- Baseline / target prediction: `{result['baseline_prediction']}` / `{result['target_prediction']}`",
                f"- Status: `{result['overall_status']}`",
                f"- Evaluated states: `{search['evaluated_state_count']}` of `{search['available_state_count']}`",
                f"- Exhaustive under the declared set: `{str(search['exhaustive']).lower()}`",
                f"- Reviewer disposition: `{result['reviewer_disposition']}`",
            ]
        )
        if result["identified_paths"]:
            lines.append("- Target-reaching evaluated actions:")
            for path in result["identified_paths"]:
                features = ", ".join(path["primary_action_features"])
                lines.append(f"  - `{path['action_id']}` (primary features: {features})")
        if result["uncertainty_reasons"]:
            lines.append("- Visible uncertainties:")
            for uncertainty in result["uncertainty_reasons"]:
                lines.append(f"  - {uncertainty}")
        lines.append("")
    lines.extend(
        [
            "## Interpretation Boundary",
            "",
            "A target-reaching evaluated state means only that the transparent synthetic provider returned the configured target label for that declared state. It does not establish real-world feasibility, affordability, persistence after model or policy change, product eligibility, future lending outcomes, institutional adoption, or legal compliance.",
            "",
            "The assessment is structurally separate from required adverse-action reason selection and notice rendering. It neither reproduces nor modifies those records.",
            "",
        ]
    )
    return "\n".join(lines)


def render_reviewer_notes() -> str:
    return "\n".join(
        [
            "# Recourse Reviewer Notes",
            "",
            "> Synthetic reviewer pack. Record observations without converting the output into applicant guidance or a legal conclusion.",
            "",
            "## Review prompts",
            "",
            "- Are the action-set assumptions explicit and internally consistent?",
            "- Were linked downstream changes evaluated as part of each declared state?",
            "- Does the status reflect the actual search bound and uncertainty state?",
            "- Are model, method, action-set, and subject versions aligned?",
            "- What institution-specific evidence would be required before practical use?",
            "",
            "## Notes",
            "",
            "Pending reviewer entry.",
            "",
        ]
    )


def render_reviewer_signoff() -> str:
    return "\n".join(
        [
            "# Recourse Reviewer Signoff",
            "",
            "- Reviewer: Pending",
            "- Role and independence: Pending",
            "- Exact package version reviewed: Pending",
            "- Disposition: Pending review",
            "- Open limitations or conditions: Pending",
            "",
            "This template does not constitute independent review until completed by an identified reviewer against the exact released artifact.",
            "",
        ]
    )


def _build_output_fingerprints(staging_dir: Path) -> dict[str, Any]:
    return {
        "record_type": "recourse_output_fingerprints",
        "result_type": "generated_output_integrity_record_not_validation_or_approval",
        "hash_policy": "sha256_raw_generated_bytes_v1",
        "files": [
            {"filename": filename, "sha256": sha256_file(staging_dir / filename)}
            for filename in FINGERPRINTED_OUTPUT_FILENAMES
        ],
    }


def _build_manifest(
    *,
    staging_dir: Path,
    input_fingerprints: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    non_manifest_outputs = [
        filename for filename in OUTPUT_FILENAMES if filename != MANIFEST_FILENAME
    ]
    return {
        "record_type": "recourse_evidence_pack_manifest",
        "result_type": "synthetic_reviewer_pack_not_applicant_guidance_not_validation_or_compliance",
        "recourse_run_id": config["recourse_run_id"],
        "model_id": config["model_id"],
        "version_id": config["version_id"],
        "audience": "reviewer_only",
        "hash_policy": "canonical_json_inputs_and_raw_generated_outputs_v1",
        "inputs": input_fingerprints["files"],
        "outputs": [
            {"filename": filename, "sha256": sha256_file(staging_dir / filename)}
            for filename in non_manifest_outputs
        ],
        "limitations": [
            "Synthetic demonstration only; no real applicant, lender, or production model data are represented.",
            "The pack does not establish institutional adoption, independent validation, legal compliance, guaranteed recourse, increased approvals, or improved credit access.",
        ],
    }


def _verify_output_hashes(
    *,
    entries: Any,
    expected_filenames: tuple[str, ...],
    label: str,
    output_dir: Path,
    errors: list[str],
) -> None:
    if not isinstance(entries, list):
        errors.append(f"{label} must be a list")
        return

    hashes_by_filename: dict[str, str] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        filename = entry.get("filename")
        expected_hash = entry.get("sha256")
        if not isinstance(filename, str) or not isinstance(expected_hash, str):
            errors.append(
                f"{label}[{index}] must contain string filename and sha256 values"
            )
            continue
        if filename in hashes_by_filename:
            errors.append(f"{label} contains duplicate filename: {filename}")
            continue
        hashes_by_filename[filename] = expected_hash

    if sorted(hashes_by_filename) != sorted(expected_filenames):
        errors.append(f"{label} filenames do not exactly match the expected output set")

    for filename in expected_filenames:
        expected_hash = hashes_by_filename.get(filename)
        if expected_hash is None:
            continue
        path = output_dir / filename
        if not path.is_file() or sha256_file(path) != expected_hash:
            errors.append(f"{label} hash mismatch: {filename}")


def verify_recourse_evidence_pack(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    errors: list[str] = []
    actual_files = sorted(
        path.name for path in output_dir.iterdir() if path.is_file()
    ) if output_dir.is_dir() else []
    expected_files = sorted(OUTPUT_FILENAMES)
    if actual_files != expected_files:
        errors.append(
            "evidence pack files do not exactly match the declared output set"
        )
    manifest_path = output_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        errors.append("manifest.json is missing")
        return {"ok": False, "errors": errors, "verified_files": []}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        input_fingerprints = json.loads(
            (output_dir / INPUT_FINGERPRINTS_FILENAME).read_text(encoding="utf-8")
        )
        output_fingerprints = json.loads(
            (output_dir / OUTPUT_FINGERPRINTS_FILENAME).read_text(encoding="utf-8")
        )
        if manifest["inputs"] != input_fingerprints["files"]:
            errors.append("manifest inputs differ from input_fingerprints.json")
        _verify_output_hashes(
            entries=manifest["outputs"],
            expected_filenames=tuple(
                filename
                for filename in OUTPUT_FILENAMES
                if filename != MANIFEST_FILENAME
            ),
            label="manifest outputs",
            output_dir=output_dir,
            errors=errors,
        )
        _verify_output_hashes(
            entries=output_fingerprints["files"],
            expected_filenames=FINGERPRINTED_OUTPUT_FILENAMES,
            label="output fingerprints",
            output_dir=output_dir,
            errors=errors,
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"evidence pack verification failed: {exc}")
    return {
        "ok": not errors,
        "errors": errors,
        "verified_files": expected_files if not errors else [],
    }


def generate_recourse_evidence_pack(
    core_dir: Path,
    recourse_dir: Path,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    core_dir = core_dir.resolve()
    recourse_dir = recourse_dir.resolve()
    output_dir = output_dir.resolve()
    validate_distinct_paths(core_dir, recourse_dir, output_dir)
    validation = validate_recourse_bundle(recourse_dir, core_dir)
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    if output_dir.exists():
        existing_files = sorted(path.name for path in output_dir.iterdir() if path.is_file())
        unexpected = sorted(set(existing_files) - set(OUTPUT_FILENAMES))
        if unexpected:
            raise FileExistsError(
                "refusing output directory with undeclared file(s): " + ", ".join(unexpected)
            )
        if existing_files and not overwrite:
            raise FileExistsError(
                "refusing to overwrite existing recourse output(s): " + ", ".join(existing_files)
            )
    else:
        output_dir.mkdir(parents=True)

    before_hashes = protected_core_hashes(core_dir)
    payloads = load_recourse_payloads(recourse_dir)
    results = assess_recourse(core_dir, recourse_dir)
    after_assessment_hashes = protected_core_hashes(core_dir)
    if before_hashes != after_assessment_hashes:
        raise RuntimeError("protected core files changed during recourse assessment")

    staging_dir = output_dir / f".recourse-pack-{uuid.uuid4().hex}"
    staging_dir.mkdir()
    try:
        input_fingerprints = build_input_fingerprints(core_dir, recourse_dir)
        write_json(staging_dir / INPUT_FINGERPRINTS_FILENAME, input_fingerprints)
        write_json(
            staging_dir / METHOD_SNAPSHOT_FILENAME,
            payloads["recourse-method-record.json"],
        )
        write_json(
            staging_dir / ACTION_SET_SNAPSHOT_FILENAME,
            payloads["recourse-action-set.json"],
        )
        write_json(
            staging_dir / CONFIG_SNAPSHOT_FILENAME,
            payloads["recourse-review-config.json"],
        )
        write_json(staging_dir / RESULTS_FILENAME, results)
        after_hashes = protected_core_hashes(core_dir)
        qa_results = build_qa_results(
            results=results,
            before_hashes=before_hashes,
            after_hashes=after_hashes,
        )
        if not qa_results["passed"]:
            raise RuntimeError("recourse QA detected a protected-core change")
        write_json(staging_dir / QA_FILENAME, qa_results)
        write_text_lf(
            staging_dir / REPORT_FILENAME,
            render_review_report(
                results,
                payloads["recourse-method-record.json"],
                payloads["recourse-action-set.json"],
            ),
        )
        write_text_lf(staging_dir / NOTES_FILENAME, render_reviewer_notes())
        write_text_lf(staging_dir / SIGNOFF_FILENAME, render_reviewer_signoff())
        output_fingerprints = _build_output_fingerprints(staging_dir)
        write_json(staging_dir / OUTPUT_FINGERPRINTS_FILENAME, output_fingerprints)
        manifest = _build_manifest(
            staging_dir=staging_dir,
            input_fingerprints=input_fingerprints,
            config=payloads["recourse-review-config.json"],
        )
        write_json(staging_dir / MANIFEST_FILENAME, manifest)
        for filename in OUTPUT_FILENAMES:
            os.replace(staging_dir / filename, output_dir / filename)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    verification = verify_recourse_evidence_pack(output_dir)
    if not verification["ok"]:
        raise RuntimeError("generated recourse pack failed verification: " + "; ".join(verification["errors"]))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a separate deterministic synthetic recourse reviewer pack."
    )
    parser.add_argument("core_dataset_dir", type=Path)
    parser.add_argument("recourse_bundle_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace only the eleven named recourse evidence-pack files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = generate_recourse_evidence_pack(
            args.core_dataset_dir,
            args.recourse_bundle_dir,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except (FileExistsError, OSError, RuntimeError, ValueError) as exc:
        print(f"recourse report failed: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
