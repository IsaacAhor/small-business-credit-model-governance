"""Run a standalone less-discriminatory-alternative (LDA) assessment.

Compares the baseline underwriting decisions against a candidate alternative
model on the same synthetic population and prints the assessment JSON. This is
the same assessment the monitoring workflow runs when LDA inputs are present in
the dataset; this script exposes it on its own for focused review.

Usage:
    python scripts/run_lda_assessment.py data/synthetic/monthly-portfolio
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

from credit_gov.lda import assess_less_discriminatory_alternative  # noqa: E402


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a synthetic LDA assessment.")
    parser.add_argument("dataset_dir", help="Directory containing the synthetic dataset with LDA inputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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


if __name__ == "__main__":
    raise SystemExit(main())
