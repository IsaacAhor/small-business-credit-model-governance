"""Run the Phase 2 monthly monitoring workflow for a synthetic dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 2 synthetic monthly monitoring workflow."
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_monthly_monitoring(
        dataset_dir=Path(args.dataset_dir),
        evidence_root=Path(args.evidence_root),
    )
    json.dump(result.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
