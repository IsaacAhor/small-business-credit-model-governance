"""Generate diagnostic adverse-action reason candidates for a synthetic dataset.

Reads a dataset's decisions, driver contributions, and reason-code mappings,
then writes ``adverse-action-reason-outputs.json``. This is the reason
*generation* step; the monitoring workflow's reason QA reviews the result.
When the policy, template and selection-method configuration is present, the
shared command includes source-to-notice fields and uses its principal rank limit.
Rendered notices and declared reviews remain separate inputs.

Use ``--check`` to regenerate in memory and compare against the file already on
disk. A non-zero exit reports drift or an input/configuration failure.
Equality is not a reason-content review or operational authorization.

Usage:
    python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio
    python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio --check
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from credit_gov.commands import (  # noqa: E402
    generate_reasons_main as main,
    generate_reasons_parser as build_parser,
)


if __name__ == "__main__":
    raise SystemExit(main())
