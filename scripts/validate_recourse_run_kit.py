"""Validate the separate synthetic recourse run kit from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.recourse import validate_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(validate_main())
