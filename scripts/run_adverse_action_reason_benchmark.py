"""Run the synthetic adverse-action reason accuracy benchmark.

The benchmark is a reviewer-facing run kit for adverse-action reason accuracy
and transparency under Regulation B 12 CFR 1002.9. It reuses the repository's
monthly monitoring workflow, then adds benchmark-specific checks that are not
part of the general monthly pipeline.

The output is synthetic governance evidence only. It is not a legal conclusion,
production notice process, lender adoption claim, or compliance certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
import uuid
from tempfile import mkdtemp
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.generation import (  # noqa: E402
    DEFAULT_MAX_REASONS,
    generate_adverse_action_reasons,
    summarize_generation,
)
from credit_gov.monitoring import build_output_fingerprints, run_monthly_monitoring  # noqa: E402
from credit_gov.monitoring import verify_evidence_pack  # noqa: E402
from credit_gov.input_snapshot import DatasetSnapshot  # noqa: E402
from credit_gov.reason_fidelity import build_reason_fidelity_context  # noqa: E402
from credit_gov.result_scope import diagnostic_scope  # noqa: E402
from credit_gov.source_provenance import check_source_unchanged  # noqa: E402


WORKSTREAM_NAME = "Adverse-action reason accuracy and transparency under Regulation B 12 CFR 1002.9"

EXPECTED_EXCEPTION_TYPES = {
    "missing_reason_code",
    "unmapped_reason_code",
    "generic_reason_text",
    "driver_mapping_mismatch",
    "mapping_version_mismatch",
    "non_declined_reason_output",
    "excessive_reason_count",
    "credit_report_only_placeholder",
    "no_mapped_adverse_driver",
    "recorded_output_differs_from_regeneration",
    "principal_driver_omitted",
    "principal_driver_unmapped",
    "notice_text_mapping_mismatch",
    "notice_template_version_mismatch",
    "mapping_effective_date_mismatch",
    "decision_component_mismatch",
    "selection_method_version_mismatch",
    "source_driver_rank_mismatch",
    "policy_version_mismatch",
    "reason_not_in_actual_contributors",
    "rendered_notice_text_mismatch",
}


@dataclass(slots=True)
class BenchmarkRunResult:
    ok: bool
    dataset_dir: str
    output_dir: str | None
    errors: list[str]
    benchmark_results: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            **diagnostic_scope("synthetic_seeded_failure_detection"),
            "dataset_dir": self.dataset_dir,
            "output_dir": self.output_dir,
            "errors": self.errors,
            "benchmark_results": self.benchmark_results,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2) + "\n")


def write_text(path: Path, contents: str) -> None:
    """Write UTF-8 benchmark artifacts with LF endings on every platform."""
    path.write_bytes(contents.encode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic adverse-action reason accuracy benchmark."
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="data/synthetic/adverse-action-reason-benchmark",
        help="Synthetic benchmark dataset directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="examples/evidence-packs/adverse-action-reason-benchmark",
        help="Stable curated evidence-pack directory to write.",
    )
    parser.add_argument(
        "--max-reasons",
        type=int,
        default=DEFAULT_MAX_REASONS,
        help="Maximum expected principal reasons per declined decision.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing curated output directory.",
    )
    return parser


def run_benchmark(
    dataset_dir: Path,
    output_dir: Path,
    max_reasons: int = DEFAULT_MAX_REASONS,
    overwrite: bool = False,
) -> BenchmarkRunResult:
    dataset_dir = dataset_dir.resolve()
    output_dir = output_dir.resolve()

    if dataset_dir.is_relative_to(output_dir) or any(
        source.is_relative_to(output_dir) or output_dir.is_relative_to(source)
        for source in (Path(__file__).resolve().parent, SRC.resolve(), (ROOT / "schemas").resolve())
    ):
        return BenchmarkRunResult(
            ok=False,
            dataset_dir=str(dataset_dir),
            output_dir=None,
            errors=["Output must not replace the input dataset, source directories, or their ancestors."],
            benchmark_results={},
        )

    if output_dir.exists() and not overwrite:
        return BenchmarkRunResult(
            ok=False,
            dataset_dir=str(dataset_dir),
            output_dir=None,
            errors=[f"Output directory already exists: {output_dir}. Use --overwrite to replace it."],
            benchmark_results={},
        )

    scratch_suffix = hashlib.sha1(str(output_dir).encode("utf-8")).hexdigest()[:8]
    scratch_evidence_root = ROOT / "evidence" / f"_aarb_{scratch_suffix}"
    scratch_evidence_root.mkdir(parents=True, exist_ok=True)
    inputs = DatasetSnapshot(dataset_dir)
    monitoring_result = run_monthly_monitoring(
        dataset_dir=dataset_dir,
        evidence_root=scratch_evidence_root,
        source_entrypoint=Path(__file__),
        input_snapshot=inputs,
    )
    if not monitoring_result.ok:
        return BenchmarkRunResult(
            ok=False,
            dataset_dir=str(dataset_dir),
            output_dir=None,
            errors=monitoring_result.errors,
            benchmark_results={},
        )

    source_output = Path(monitoring_result.output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(mkdtemp(prefix=".benchmark-", dir=output_dir.parent))
    try:
        staged_output = staging_root / "pack"
        shutil.copytree(source_output, staged_output)
        require_pack_integrity(staged_output)
        benchmark_results = build_benchmark_results(
            dataset_dir=inputs,
            monitoring_reason_qa=monitoring_result.reason_qa,
            max_reasons=max_reasons,
        )
        if not benchmark_results["acceptance"]["expected_seeded_failures_observed"]:
            return BenchmarkRunResult(
                ok=False,
                dataset_dir=str(dataset_dir),
                output_dir=None,
                errors=["Expected benchmark exception types were not all observed; destination unchanged."],
                benchmark_results=benchmark_results,
            )
        write_json(staged_output / "adverse_action_reason_benchmark_results.json", benchmark_results)
        write_text(
            staged_output / "adverse_action_reason_benchmark_report.md",
            render_benchmark_report(benchmark_results),
        )
        write_text(staged_output / "README.md", render_example_readme(benchmark_results))
        update_manifest(staged_output)
        check_source_unchanged(load_json(staged_output / "execution_provenance.json"), Path(__file__))
        require_pack_integrity(staged_output)
        install_benchmark_pack(staged_output, output_dir, overwrite=overwrite)
    finally:
        cleanup_directory(staging_root, "Benchmark staging cleanup incomplete")

    return BenchmarkRunResult(
        ok=True,
        dataset_dir=str(dataset_dir),
        output_dir=str(output_dir),
        errors=[],
        benchmark_results=benchmark_results,
    )


def require_pack_integrity(pack: Path) -> None:
    verification = verify_evidence_pack(pack)
    if not verification["ok"]:
        raise ValueError("Benchmark pack integrity check failed: " + "; ".join(verification["errors"]))


def cleanup_directory(path: Path, message: str) -> None:
    """Cleanup must not change installation status or mask a recovery error."""
    try:
        shutil.rmtree(path)
    except OSError as cleanup_error:
        logging.getLogger(__name__).warning("%s at %s: %s", message, path, cleanup_error)


def install_benchmark_pack(staged: Path, destination: Path, *, overwrite: bool) -> None:
    """Retain the old pack until installation succeeds; recover on rename failure.

    Backups live outside the staging temporary directory so failed restoration
    cannot erase them. This is exception recovery, not a concurrent-writer lock.
    """
    backup = None
    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"Output directory appeared during the run: {destination}")
        backup = destination.with_name(f".{destination.name}.backup-{uuid.uuid4().hex}")
        destination.rename(backup)
    try:
        if destination.exists():
            raise FileExistsError(f"Output directory appeared during installation: {destination}")
        staged.rename(destination)
    except BaseException:
        if backup is not None:
            try:
                if destination.exists():
                    raise FileExistsError(f"Recovery destination is occupied: {destination}")
                backup.rename(destination)
            except OSError as recovery_error:
                raise RuntimeError(
                    f"Benchmark installation and restoration failed; previous pack retained at {backup}"
                ) from recovery_error
        raise
    if backup is not None:
        cleanup_directory(backup, "New benchmark pack installed; old backup cleanup incomplete")


def build_benchmark_results(
    dataset_dir: Path | DatasetSnapshot,
    monitoring_reason_qa: dict[str, Any],
    max_reasons: int,
) -> dict[str, Any]:
    decisions = load_json(dataset_dir / "application-decision-records.json")
    reason_outputs = load_json(dataset_dir / "adverse-action-reason-outputs.json")
    reason_mappings = load_json(dataset_dir / "reason-code-mappings.json")
    model_version = load_json(dataset_dir / "model-version-record.json")
    driver_contributions = load_json(dataset_dir / "adverse-action-driver-contributions.json")
    fidelity_context = build_reason_fidelity_context(
        load_json(dataset_dir / "reason-fidelity-policy.json"),
        load_json(dataset_dir / "adverse-action-notice-template.json"),
        load_json(dataset_dir / "reason-selection-methods.json"),
    )

    generated = generate_adverse_action_reasons(
        decisions=decisions,
        driver_contributions=driver_contributions,
        reason_mappings=reason_mappings,
        version_id=model_version["version_id"],
        max_reasons=max_reasons,
        fidelity_context=fidelity_context,
    )
    generation_summary = summarize_generation(decisions, generated)
    supplemental_exceptions = build_supplemental_exceptions(
        decisions=decisions,
        reason_outputs=reason_outputs,
        reason_mappings=reason_mappings,
        driver_contributions=driver_contributions,
        generated_reason_outputs=generated,
        max_reasons=max_reasons,
    )
    monitoring_exception_types = {
        exception["exception_type"]
        for exception in monitoring_reason_qa["exceptions"]
    }
    supplemental_exception_types = {
        exception["exception_type"]
        for exception in supplemental_exceptions
    }
    observed_exception_types = sorted(monitoring_exception_types | supplemental_exception_types)
    missing_expected_types = sorted(EXPECTED_EXCEPTION_TYPES - set(observed_exception_types))

    declined_count = sum(1 for decision in decisions if decision["decision_outcome"] == "declined")
    return {
        "label": "synthetic_adverse_action_reason_accuracy_benchmark_not_legal_conclusion",
        "workstream": WORKSTREAM_NAME,
        "dataset": dataset_dir.relative_to(ROOT).as_posix(),
        "regulatory_anchor": "Regulation B 12 CFR 1002.9 specific principal reasons tied to actual factors considered or scored.",
        "public_data_status": (
            "This run uses synthetic small-business credit records. It does not "
            "evaluate real-world reason accuracy or establish whether a suitable "
            "public dataset exists."
        ),
        "decision_count": len(decisions),
        "declined_decision_count": declined_count,
        "recorded_reason_output_count": len(reason_outputs),
        "generated_reason_output_count": len(generated),
        "max_expected_reasons_per_declined_decision": max_reasons,
        "generation_summary": generation_summary,
        **diagnostic_scope("synthetic_seeded_failure_detection"),
        "monitoring_reason_qa": {
            "label": monitoring_reason_qa["label"],
            "exception_count": monitoring_reason_qa["exception_count"],
            "exception_types": sorted(monitoring_exception_types),
            "exceptions": monitoring_reason_qa["exceptions"],
            "source_to_notice_fidelity": monitoring_reason_qa["source_to_notice_fidelity"],
        },
        "supplemental_benchmark_checks": {
            "exception_count": len(supplemental_exceptions),
            "exception_types": sorted(supplemental_exception_types),
            "exceptions": supplemental_exceptions,
        },
        "expected_exception_types": sorted(EXPECTED_EXCEPTION_TYPES),
        "observed_exception_types": observed_exception_types,
        "missing_expected_exception_types": missing_expected_types,
        "acceptance": {
            "expected_seeded_failures_observed": not missing_expected_types,
            "result_type": "benchmark_integrity_check_not_legal_conclusion",
        },
        "limitations": [
            "Synthetic small-business credit benchmark only.",
            "No production applicant records, lender notices, or legal conclusions are represented.",
            "Benchmark exceptions are governance review triggers.",
            "Synthetic source-to-rendered-notice checks reconcile controlled notice segments to recorded reason outputs; they do not assess real-world notice readability or legal sufficiency.",
            "The synthetic selection-method check verifies recorded method provenance and deterministic behavior, not a real creditor's selection-method sufficiency.",
            "Evaluating actual reason accuracy requires evidence linking the relevant decision process to disclosed reasons, with a justified reference and stated limits; public or private status alone does not establish suitability.",
            "An HMDA mortgage-denial mechanics exercise would not establish small-business reason accuracy.",
        ],
        "primary_source_urls": [
            "https://www.consumerfinance.gov/rules-policy/regulations/1002/9/",
            "https://www.consumerfinance.gov/rules-policy/regulations/1002/",
        ],
    }


def build_supplemental_exceptions(
    decisions: list[dict[str, Any]],
    reason_outputs: list[dict[str, Any]],
    reason_mappings: list[dict[str, Any]],
    driver_contributions: list[dict[str, Any]],
    generated_reason_outputs: list[dict[str, Any]],
    max_reasons: int,
) -> list[dict[str, Any]]:
    exceptions: list[dict[str, Any]] = []
    decisions_by_id = {decision["decision_id"]: decision for decision in decisions}
    mappings_by_code = {mapping["reason_code"]: mapping for mapping in reason_mappings}
    mapped_drivers = {mapping["driver_or_signal"] for mapping in reason_mappings}
    outputs_by_decision = group_by_decision(reason_outputs)
    contributions_by_decision = {
        record["decision_id"]: record.get("contributions", [])
        for record in driver_contributions
    }

    for output in reason_outputs:
        decision = decisions_by_id[output["decision_id"]]
        if decision["decision_outcome"] != "declined":
            exceptions.append(
                build_benchmark_exception(
                    exception_type="non_declined_reason_output",
                    decision_id=output["decision_id"],
                    reason_output_id=output["reason_output_id"],
                    message="Reason output is attached to a decision that was not declined.",
                )
            )
        mapping = mappings_by_code.get(output["reason_code"])
        if mapping and is_credit_report_only_placeholder(mapping["reason_text"]):
            exceptions.append(
                build_benchmark_exception(
                    exception_type="credit_report_only_placeholder",
                    decision_id=output["decision_id"],
                    reason_output_id=output["reason_output_id"],
                    message=(
                        "Mapped reason text is a credit-report-only placeholder and "
                        "requires review for a specific principal reason."
                    ),
                )
            )

    for decision_id, outputs in sorted(outputs_by_decision.items()):
        if len(outputs) > max_reasons:
            exceptions.append(
                build_benchmark_exception(
                    exception_type="excessive_reason_count",
                    decision_id=decision_id,
                    reason_output_id=None,
                    message=(
                        f"Decision has {len(outputs)} recorded reason outputs; "
                        f"benchmark maximum is {max_reasons}."
                    ),
                )
            )

    for decision in decisions:
        if decision["decision_outcome"] != "declined":
            continue
        contributions = contributions_by_decision.get(decision["decision_id"], [])
        mapped_adverse = [
            contribution
            for contribution in contributions
            if contribution.get("direction", "adverse") == "adverse"
            and contribution["driver_or_signal"] in mapped_drivers
        ]
        if not mapped_adverse:
            exceptions.append(
                build_benchmark_exception(
                    exception_type="no_mapped_adverse_driver",
                    decision_id=decision["decision_id"],
                    reason_output_id=None,
                    message="Declined decision has no adverse driver that resolves to a governed reason-code mapping.",
                )
            )

    if reason_identity_set(reason_outputs) != reason_identity_set(generated_reason_outputs):
        exceptions.append(
            build_benchmark_exception(
                exception_type="recorded_output_differs_from_regeneration",
                decision_id=None,
                reason_output_id=None,
                message=(
                    "Recorded reason outputs differ from deterministic regeneration. "
                    "This is expected in the synthetic benchmark because seeded QA "
                    "failures are intentionally present."
                ),
            )
        )

    return exceptions


def group_by_decision(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["decision_id"], []).append(record)
    return grouped


def reason_identity_set(records: list[dict[str, Any]]) -> set[tuple[Any, ...]]:
    return {
        (
            record["decision_id"],
            record["reason_rank"],
            record["reason_code"],
            record["driver_or_signal"],
            record["mapping_version"],
        )
        for record in records
    }


def is_credit_report_only_placeholder(reason_text: str) -> bool:
    normalized = " ".join(reason_text.lower().split())
    placeholders = {
        "information from credit report",
        "credit report information",
        "credit report used",
    }
    return normalized in placeholders


def build_benchmark_exception(
    exception_type: str,
    decision_id: str | None,
    reason_output_id: str | None,
    message: str,
) -> dict[str, Any]:
    identity = reason_output_id or decision_id or "global"
    return {
        "exception_id": f"bench-{identity}-{exception_type}",
        "exception_type": exception_type,
        "decision_id": decision_id,
        "reason_output_id": reason_output_id,
        "message": message,
        "result_type": "benchmark_review_trigger_not_legal_conclusion",
    }


def update_manifest(output_dir: Path) -> None:
    manifest_path = output_dir / "manifest.json"
    manifest = load_json(manifest_path)
    additions = [
        "adverse_action_reason_benchmark_results.json",
        "adverse_action_reason_benchmark_report.md",
        "README.md",
    ]
    for filename in additions:
        if filename not in manifest["output_files"]:
            manifest["output_files"].append(filename)
    write_json(manifest_path, manifest)
    fingerprint_path = output_dir / "output_fingerprints.json"
    if fingerprint_path.is_file():
        write_json(
            fingerprint_path,
            build_output_fingerprints(output_dir, manifest["output_files"]),
        )


def render_benchmark_report(results: dict[str, Any]) -> str:
    supplemental_lines = "\n".join(
        f"- {exception['exception_type']}: {exception['message']}"
        for exception in results["supplemental_benchmark_checks"]["exceptions"]
    )
    if not supplemental_lines:
        supplemental_lines = "- No supplemental benchmark exceptions were generated."

    monitoring_lines = "\n".join(
        f"- {exception['decision_id']}: {exception['exception_type']} ({exception['message']})"
        for exception in results["monitoring_reason_qa"]["exceptions"]
    )
    if not monitoring_lines:
        monitoring_lines = "- No monitoring reason QA exceptions were generated."

    return (
        "# Adverse-Action Reason Accuracy Benchmark Report\n\n"
        "This report is synthetic governance evidence only. It does not provide legal advice, "
        "certify Regulation B compliance, or represent a production notice process.\n\n"
        "Benchmark success means expected seeded failure types were detected. It does not "
        "establish a passed reason-content review. Operational authorization is not provided.\n\n"
        f"- Workstream: {results['workstream']}\n"
        f"- Dataset: `{results['dataset']}`\n"
        f"- Decisions reviewed: {results['decision_count']}\n"
        f"- Declined decisions reviewed: {results['declined_decision_count']}\n"
        f"- Recorded reason outputs: {results['recorded_reason_output_count']}\n"
        f"- Regenerated reason outputs: {results['generated_reason_output_count']}\n"
        f"- Expected seeded failure types observed: {results['acceptance']['expected_seeded_failures_observed']}\n\n"
        "## Monitoring Reason QA Exceptions\n\n"
        f"{monitoring_lines}\n\n"
        "## Supplemental Benchmark Exceptions\n\n"
        f"{supplemental_lines}\n\n"
        "## Public-Data Boundary\n\n"
        f"{results['public_data_status']}\n\n"
        "This benchmark assesses synthetic record consistency. Any proposed real-world "
        "evaluation must justify its data, decision-process reference, reason records "
        "and review evidence for the specific accuracy claim. Portfolio, lending-volume "
        "or off-domain reason-code mechanics results alone do not establish that claim.\n\n"
        "## Limitations\n\n"
        + "\n".join(f"- {item}" for item in results["limitations"])
        + "\n"
    )


def render_example_readme(results: dict[str, Any]) -> str:
    return (
        "# Adverse-Action Reason Benchmark Evidence Pack\n\n"
        "This evidence pack is generated from a synthetic small-business credit benchmark. "
        "It demonstrates reason-generation and reason-QA controls under the adverse-action "
        "reason accuracy and transparency workstream.\n\n"
        "Benchmark acceptance records expected failure detection, not a passed reason-content "
        "review. Operational authorization is not provided.\n\n"
        "## How To Review This Pack\n\n"
        "1. Read `adverse_action_reason_benchmark_report.md` for the benchmark summary.\n"
        "2. Read `adverse_action_reason_benchmark_results.json` for machine-readable expected and observed exception types.\n"
        "3. Read `reason_qa_results.json` and `rendered_notice_qa_results.json` for source and visible-notice reconciliation.\n"
        "4. Read `monitoring_report.md` for the broader evidence-pack output.\n\n"
        "## Regeneration Command\n\n"
        "```bash\n"
        "python scripts/run_adverse_action_reason_benchmark.py --overwrite\n"
        "```\n\n"
        "## Important Limits\n\n"
        "- Synthetic data only.\n"
        "- Not a production notice process.\n"
        "- Not legal advice or a Regulation B compliance certification.\n"
        "- Not evidence of lender adoption, deployment, regulatory approval, or external validation.\n"
        "- This synthetic run does not establish the availability or suitability of other datasets.\n\n"
        f"Expected seeded failure types observed: {results['acceptance']['expected_seeded_failures_observed']}.\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_benchmark(
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        max_reasons=args.max_reasons,
        overwrite=args.overwrite,
    )
    json.dump(result.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
