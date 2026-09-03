#!/usr/bin/env python3
"""Normalize host-specific metadata in source distributions."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.public_artifacts import normalize_source_distribution


def main(arguments: list[str] | None = None) -> int:
    values = sys.argv[1:] if arguments is None else arguments
    paths = [Path(value) for value in values]
    if not paths:
        print("Usage: python scripts/normalize_sdist.py <archive> [<archive> ...]")
        return 2
    for path in paths:
        normalize_source_distribution(path)
    print(f"Normalized {len(paths)} source distribution(s).")
    return 0


def guarded_main() -> int:
    try:
        return main()
    except Exception:
        print("Source-distribution normalization failed (details suppressed).")
        return 2


if __name__ == "__main__":
    raise SystemExit(guarded_main())
