"""Run a standalone Phase 5 model-change and validation review.

Compares a prior snapshot of the governed records against the current dataset
records for the same model and writes a deterministic change-validation result
(JSON) and reviewer-facing report (Markdown). This is the same assessment the
monitoring workflow runs when Phase 5 inputs are present in the dataset; this
script exposes it on its own for focused change review.

Required prior inputs in the dataset directory:
    prior-model-version-record.json

Optional prior inputs (each skipped if absent):
    prior-threshold-set.json
    prior-reason-code-mappings.json
    change-review-config.json

Usage:
    python scripts/run_change_validation.py data/synthetic/monthly-portfolio \\
        --output-dir evidence/change-validation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.validation import (  # noqa: E402
    assess_model_change,
    render_change_validation_report,
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path):
    if not path.is_file():
        return None
    return load_json(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a synthetic model-change and validation review (Phase 5)."
    )
    parser.add_argument(
        "dataset_dir",
        help="Directory containing the current dataset and prior-* comparison inputs.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory to write model_change_validation_results.json and "
        "model_change_validation_report.md. When omitted, the result JSON is printed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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


if __name__ == "__main__":
    raise SystemExit(main())
