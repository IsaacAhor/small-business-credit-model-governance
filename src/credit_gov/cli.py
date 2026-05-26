"""Command-line entry points for Phase 1 validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from credit_gov.schemas import validate_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Phase 1 synthetic governance records."
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="data/synthetic/monthly-demo",
        help="Directory containing Phase 1 JSON input records.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dataset_dir = Path(args.dataset_dir).resolve()
    result = validate_dataset(dataset_dir)
    json.dump(result.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
