"""Fail when public artifacts contain non-portable or sensitive content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.public_artifacts import validate_public_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check public files and archives for portable, reviewable content."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    findings = validate_public_artifacts(args.paths)
    if findings:
        print("Public artifact validation failed:")
        for finding in findings:
            print(f"- {finding.category}: {finding.location}")
        return 1

    print("Public artifact validation passed.")
    return 0


def guarded_main() -> int:
    """Return a generic failure without exposing exception values or paths."""

    try:
        return main()
    except Exception:
        print("Public artifact validation failed: internal error details suppressed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(guarded_main())
