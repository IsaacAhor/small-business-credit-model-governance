"""Run the deterministic model-governance review command from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.governance_review import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
