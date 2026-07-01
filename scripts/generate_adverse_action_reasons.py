"""Generate governed adverse-action reason outputs for a synthetic dataset.

Reads a dataset's decisions, driver contributions, and reason-code mappings,
then writes ``adverse-action-reason-outputs.json``. This is the reason
*generation* step; the monitoring workflow's reason QA reviews the result.

Use ``--check`` to regenerate in memory and compare against the file already on
disk. A non-zero exit means the shipped reasons drifted from what the current
generation logic would produce (a governance provenance signal).

Usage:
    python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio
    python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio --check
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

from credit_gov.generation import generate_adverse_action_reasons, summarize_generation  # noqa: E402


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate governed adverse-action reason outputs.")
    parser.add_argument("dataset_dir", help="Directory containing the synthetic dataset.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare regenerated reasons against the on-disk file instead of writing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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


if __name__ == "__main__":
    raise SystemExit(main())
