"""Run BISG proxy estimation and screening on a synthetic dataset.

Usage:
    python scripts/run_bisg_proxy.py data/synthetic/monthly-portfolio [--output PATH]

Requires the dataset to contain ``bisg-config.json`` and
``applicant-demographic-inputs.json``. Prints a summary and optionally writes
the full results JSON.
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

from credit_gov.bisg import run_bisg_proxy_analysis  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.resolve()
    config_path = dataset_dir / "bisg-config.json"
    inputs_path = dataset_dir / "applicant-demographic-inputs.json"
    decisions_path = dataset_dir / "application-decision-records.json"
    for path in (config_path, inputs_path, decisions_path):
        if not path.is_file():
            print(f"error: missing required input {path}", file=sys.stderr)
            return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    demographic_inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))

    results = run_bisg_proxy_analysis(
        decisions=decisions,
        demographic_inputs=demographic_inputs,
        config=config,
        dataset_dir=dataset_dir,
    )

    print(f"method={results['method']} matched={results['matched_decision_count']}/{results['decision_count']}")
    for category, metrics in results["group_metrics"].items():
        rate = metrics["proxy_weighted_approval_rate"]
        print(
            f"  {category}: weighted_total={metrics['proxy_weighted_total']} "
            f"approval_rate={rate if rate is not None else 'n/a'}"
        )
    print(f"significant_findings={results['finding_count']}")
    for finding in results["findings"]:
        print(
            f"  {finding['proxy_group']} vs {finding['reference_group']}: "
            f"{finding['proxy_weighted_approval_rate']} vs {finding['reference_approval_rate']} "
            f"(p={finding['p_value']})"
        )

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"results written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
