"""Check the review sheet and release-note link for a selected release."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def validate_review_target(root: Path, tag: str, repository: str) -> None:
    if not re.fullmatch(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", tag):
        raise ValueError("Release tag must use vMAJOR.MINOR.PATCH.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be an owner/name pair.")
    target = f"docs/external-review/targets/{tag}.md"
    try:
        sheet = (root / target).read_text(encoding="utf-8")
        notes = (root / f"docs/releases/{tag}.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("Review target or release notes are missing or unreadable.") from exc
    if sheet.splitlines()[:1] != [f"# Review target: {tag}"]:
        raise ValueError("Review target heading does not match the release.")
    link = f"[Review target](https://github.com/{repository}/blob/{tag}/{target})"
    if link not in notes:
        raise ValueError("Release notes must include the version-pinned Review target link.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        validate_review_target(Path.cwd(), args.tag, args.repository)
    except ValueError as exc:
        print(f"Review target check failed: {exc}", file=sys.stderr)
        return 1
    print("Review target and version-pinned release link checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
