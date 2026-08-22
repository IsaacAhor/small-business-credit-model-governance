"""Command-line wrapper for the canonical synthetic SBA fixture generator."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from credit_gov.make_sba_fixture import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
