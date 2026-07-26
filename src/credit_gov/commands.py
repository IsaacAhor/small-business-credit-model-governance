"""Console commands for installed credit-gov packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from credit_gov.bisg import run_bisg_proxy_analysis
from credit_gov.cli import main as validate_main
from credit_gov.generation import generate_adverse_action_reasons, summarize_generation
from credit_gov.lda import assess_less_discriminatory_alternative
from credit_gov.monitoring import run_monthly_monitoring
from credit_gov.validation import assess_model_change, render_change_validation_report


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path):
    if not path.is_file():
        return None
    return load_json(path)


def monitor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic monthly monitoring governance workflow."
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="data/synthetic/monthly-demo",
        help="Directory containing the synthetic monitoring dataset.",
    )
    parser.add_argument(
        "--evidence-root",
        default="evidence",
        help="Directory where the generated evidence pack should be written.",
    )
    return parser


def monitor_main(argv: list[str] | None = None) -> int:
    args = monitor_parser().parse_args(argv)
    result = run_monthly_monitoring(
        dataset_dir=Path(args.dataset_dir),
        evidence_root=Path(args.evidence_root),
    )
    json.dump(result.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.ok else 1


def generate_reasons_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate governed adverse-action reason outputs."
    )
    parser.add_argument("dataset_dir", help="Directory containing the synthetic dataset.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare regenerated reasons against the on-disk file instead of writing.",
    )
    return parser


def generate_reasons_main(argv: list[str] | None = None) -> int:
    args = generate_reasons_parser().parse_args(argv)
    dataset_dir = Path(args.dataset_dir)

    decisions = load_json(dataset_dir / "application-decision-records.json")
    contributions = load_json(dataset_dir / "adverse-action-driver-contributions.json")
    mappings = load_json(dataset_dir / "reason-code-mappings.json")
    version_id = load_json(dataset_dir / "model-version-record.json")["version_id"]

    generated = generate_adverse_action_reasons(
        decisions=decisions,
        driver_contributions=contributions,
        reason_mappings=mappings,
        version_id=version_id,
    )
    summary = summarize_generation(decisions, generated)
    output_path = dataset_dir / "adverse-action-reason-outputs.json"

    if args.check:
        existing = load_json(output_path) if output_path.is_file() else None
        if existing == generated:
            print(f"OK: on-disk reasons match regeneration ({summary['reason_output_count']} outputs).")
            return 0
        print("DRIFT: on-disk adverse-action reasons differ from current generation logic.")
        return 1

    output_path.write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {summary['reason_output_count']} reason outputs to {output_path}")
    print(f"generation_summary={summary}")
    return 0


def lda_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a synthetic LDA assessment.")
    parser.add_argument("dataset_dir", help="Directory containing the synthetic dataset with LDA inputs.")
    return parser


def lda_main(argv: list[str] | None = None) -> int:
    args = lda_parser().parse_args(argv)
    dataset_dir = Path(args.dataset_dir)
    config_path = dataset_dir / "lda-assessment-config.json"
    alternative_path = dataset_dir / "alternative-model-decisions.json"
    if not config_path.is_file() or not alternative_path.is_file():
        print("Missing LDA inputs: lda-assessment-config.json and alternative-model-decisions.json required.")
        return 1

    result = assess_less_discriminatory_alternative(
        decisions=load_json(dataset_dir / "application-decision-records.json"),
        alternative_decisions=load_json(alternative_path),
        outcomes=load_json(dataset_dir / "outcome-records.json"),
        config=load_json(config_path),
    )
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def bisg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BISG proxy estimation and screening on a synthetic dataset.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def bisg_main(argv: list[str] | None = None) -> int:
    args = bisg_parser().parse_args(argv)
    dataset_dir = args.dataset_dir.resolve()
    config_path = dataset_dir / "bisg-config.json"
    inputs_path = dataset_dir / "applicant-demographic-inputs.json"
    decisions_path = dataset_dir / "application-decision-records.json"
    for path in (config_path, inputs_path, decisions_path):
        if not path.is_file():
            print(f"error: missing required input {path}", file=sys.stderr)
            return 1

    results = run_bisg_proxy_analysis(
        decisions=load_json(decisions_path),
        demographic_inputs=load_json(inputs_path),
        config=load_json(config_path),
        dataset_dir=dataset_dir,
    )

    print(f"method={results['method']} matched={results['matched_decision_count']}/{results['decision_count']}")
    print(
        f"inference={results['inference_method']} "
        f"draws={results['bootstrap']['draws']} seed={results['bootstrap']['seed']} "
        f"ci_level={results['bootstrap']['ci_level']}"
    )
    for category, metrics in results["group_metrics"].items():
        rate = metrics["proxy_weighted_approval_rate"]
        ci = metrics["bootstrap_approval_rate_ci"]
        print(
            f"  {category}: weighted_total={metrics['proxy_weighted_total']} "
            f"n_eff={metrics['effective_sample_size']} "
            f"approval_rate={rate if rate is not None else 'n/a'} "
            f"ci=[{ci['lower']}, {ci['upper']}]"
        )

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"results written to {args.output}")
    return 0


def change_review_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a synthetic model-change and validation review."
    )
    parser.add_argument(
        "dataset_dir",
        help="Directory containing the current dataset and prior-* comparison inputs.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory to write model_change_validation_results.json and model_change_validation_report.md.",
    )
    return parser


def change_review_main(argv: list[str] | None = None) -> int:
    args = change_review_parser().parse_args(argv)
    dataset_dir = Path(args.dataset_dir)

    prior_version_path = dataset_dir / "prior-model-version-record.json"
    if not prior_version_path.is_file():
        print(
            "Missing Phase 5 input: prior-model-version-record.json is required "
            f"in {dataset_dir}."
        )
        return 1

    manifest = load_json(dataset_dir / "evidence-pack-manifest.json")
    model_registry = load_json(dataset_dir / "model-registry-record.json")
    result = assess_model_change(
        prior_version=load_json(prior_version_path),
        current_version=load_json(dataset_dir / "model-version-record.json"),
        current_thresholds=load_json(dataset_dir / "threshold-set.json"),
        current_reason_mappings=load_json(dataset_dir / "reason-code-mappings.json"),
        model_id=model_registry["model_id"],
        run_id=manifest["run_id"],
        prior_thresholds=load_optional_json(dataset_dir / "prior-threshold-set.json"),
        prior_reason_mappings=load_optional_json(dataset_dir / "prior-reason-code-mappings.json"),
        config=load_optional_json(dataset_dir / "change-review-config.json"),
    )

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "model_change_validation_results.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        (output_dir / "model_change_validation_report.md").write_text(
            render_change_validation_report(result), encoding="utf-8"
        )
        print(f"Wrote change-validation artifacts to {output_dir}")
    else:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "validate": validate_main,
        "monitor": monitor_main,
        "generate-reasons": generate_reasons_main,
        "lda": lda_main,
        "bisg": bisg_main,
        "change-review": change_review_main,
    }
    if not args or args[0] in {"-h", "--help"}:
        print("usage: credit-gov {validate,monitor,generate-reasons,lda,bisg,change-review} ...")
        print("\nInstalled command entry point for the credit governance evidence engine.")
        print("\ncommands:")
        for command in commands:
            print(f"  {command}")
        return 0

    command = args[0]
    handler = commands.get(command)
    if handler is None:
        print(f"error: unknown command: {command}", file=sys.stderr)
        print("usage: credit-gov {validate,monitor,generate-reasons,lda,bisg,change-review} ...", file=sys.stderr)
        return 2
    return handler(args[1:])
