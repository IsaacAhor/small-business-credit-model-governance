"""Command-line wrapper for the canonical SBA public-data adapter."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from credit_gov.sba_to_monitoring import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
