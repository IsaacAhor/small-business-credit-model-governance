"""Repository guardrails for governance artifacts.

The checks are intentionally lightweight and stdlib-only so they can run in
GitHub Actions before publishing distribution artifacts.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    "START_HERE.md",
    "USE_CASES.md",
    "IMPLEMENTATION_GUIDE.md",
    "PROJECT_BRIEF.md",
    "CONTRIBUTING.md",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/model-governance-gap.md",
    ".github/ISSUE_TEMPLATE/validation-finding.md",
    ".github/ISSUE_TEMPLATE/monitoring-breach.md",
    "docs/evidence-map.md",
    "docs/release-strategy.md",
    "docs/releases/v0.4.0.md",
    "docs/releases/v0.4.1.md",
    "docs/references.md",
    "docs/repository-roadmap.md",
    "examples/evidence-packs/monthly-demo/README.md",
    "governance/control-matrix.md",
    "governance/data-policy.md",
    "governance/model-inventory-template.md",
    "governance/validation-checklist.md",
    "governance/change-log-template.md",
    "templates/model-governance-checklist.md",
    "templates/fair-lending-monitoring-checklist.md",
]

REQUIRED_TERMS = {
    "README.md": [
        "For Reviewers",
        "Start Here",
        "Reproducibility",
        "Evidence Standard",
        "Data Policy",
        "fair-lending monitoring",
    ],
    "START_HERE.md": [
        "Fast Review Path",
        "Role-Based Paths",
        "Important Limits",
    ],
    "USE_CASES.md": [
        "Model-Risk or Validation Reviewer",
        "Fair-Lending or Compliance Reviewer",
        "Common Misuses To Avoid",
    ],
    "IMPLEMENTATION_GUIDE.md": [
        "Define The Governed Model Context",
        "Generate A Monthly Evidence Pack",
        "Review Findings And Escalations",
    ],
    "PROJECT_BRIEF.md": [
        "Problem",
        "Project Contribution",
        "Current Limitations",
    ],
    "docs/evidence-map.md": [
        "What it supports",
        "What it does not prove",
        "Synthetic data should be described as demonstration data.",
    ],
    "docs/release-strategy.md": [
        "versioned releases",
        "stable public milestones",
        "Evidence Discipline",
    ],
    "docs/releases/v0.4.0.md": [
        "Phase 4 Fair-Lending Screening Demo",
        "What This Release Demonstrates",
        "Limitations",
    ],
    "docs/releases/v0.4.1.md": [
        "Outsider Packaging Patch",
        "What This Release Adds",
        "Limitations",
    ],
    "docs/references.md": [
        "Regulation B",
        "Model Risk Management",
        "NIST",
    ],
    "examples/evidence-packs/monthly-demo/README.md": [
        "How To Review This Pack",
        "Synthetic data only.",
        "not legal conclusions",
        "Regeneration Command",
    ],
    "governance/model-inventory-template.md": [
        "Adverse-action or reason-code mapping",
        "Protected-class proxy review",
        "Less discriminatory alternative trigger logic",
    ],
    "governance/validation-checklist.md": [
        "Explainability",
        "Fair-Lending Screening",
        "Thresholds and Overrides",
    ],
    ".github/pull_request_template.md": [
        "Domain Impact",
        "Data provenance or synthetic-data assumptions",
        "Fair-lending monitoring",
    ],
}

DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".parquet",
    ".feather",
    ".sqlite",
    ".db",
}

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("Missing required files: " + ", ".join(missing))


def check_required_terms() -> None:
    for path, terms in REQUIRED_TERMS.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        missing = [term for term in terms if term not in text]
        if missing:
            fail(f"{path} is missing required terms: {', '.join(missing)}")


def check_local_markdown_links() -> None:
    for markdown_path in ROOT.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            target = match.group(1).strip()
            if (
                target.startswith(("http://", "https://", "mailto:"))
                or target.startswith("#")
                or "://" in target
            ):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (markdown_path.parent / target_path).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                fail(f"{markdown_path} links outside repo: {target}")
            if not resolved.exists():
                fail(f"{markdown_path} has broken local link: {target}")


def check_notebooks() -> None:
    for notebook_path in ROOT.rglob("*.ipynb"):
        with notebook_path.open(encoding="utf-8") as handle:
            notebook = json.load(handle)
        cells = notebook.get("cells", [])
        markdown_text = "\n".join(
            "".join(cell.get("source", []))
            for cell in cells
            if cell.get("cell_type") == "markdown"
        ).lower()
        if "synthetic" not in markdown_text and "demonstration" not in markdown_text:
            fail(
                f"{notebook_path} must disclose synthetic or demonstration status"
            )


def check_data_files() -> None:
    data_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in DATA_EXTENSIONS
    ]
    for path in data_files:
        relative = path.relative_to(ROOT)
        parts = relative.parts
        is_allowed = (
            len(parts) >= 2
            and parts[0] == "data"
            and parts[1] == "synthetic"
            and any(token in path.name.lower() for token in ("synthetic", "demo"))
        )
        if not is_allowed:
            fail(
                "Data-like files must live under data/synthetic/ and include "
                f"'synthetic' or 'demo' in the filename: {relative}"
            )


def check_packaged_resources() -> None:
    schema_resource_dir = ROOT / "src" / "credit_gov" / "schemas" / "json"
    for schema_path in sorted((ROOT / "schemas").glob("*.json")):
        packaged_path = schema_resource_dir / schema_path.name
        if not packaged_path.is_file():
            fail(f"Packaged schema resource is missing: {packaged_path.relative_to(ROOT)}")
        if schema_path.read_text(encoding="utf-8") != packaged_path.read_text(encoding="utf-8"):
            fail(f"Packaged schema resource is stale: {packaged_path.relative_to(ROOT)}")

    reference_resource_dir = ROOT / "src" / "credit_gov" / "reference" / "bisg"
    for reference_path in sorted((ROOT / "data" / "reference" / "bisg").glob("*.json")):
        packaged_path = reference_resource_dir / reference_path.name
        if not packaged_path.is_file():
            fail(f"Packaged BISG reference resource is missing: {packaged_path.relative_to(ROOT)}")
        if reference_path.read_text(encoding="utf-8") != packaged_path.read_text(encoding="utf-8"):
            fail(f"Packaged BISG reference resource is stale: {packaged_path.relative_to(ROOT)}")


def main() -> None:
    check_required_files()
    check_required_terms()
    check_local_markdown_links()
    check_notebooks()
    check_data_files()
    check_packaged_resources()
    print("Repository guardrails passed.")


if __name__ == "__main__":
    main()
