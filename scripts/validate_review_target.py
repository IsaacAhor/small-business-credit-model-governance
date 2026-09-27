"""Check review packet versions, source references, and release routing."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

VERSION = r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
PACKETS = {
    "technical-review.md": "Technical Implementation Reviewers",
    "practitioner-assessment.md": "Credit Governance and Adverse-Action Reviewers",
    "methodology-assessment.md": "Methodology and Evaluation Reviewers",
}
FORM = ".github/ISSUE_TEMPLATE/external-review.yml"


def _validate_arguments(tag: str, repository: str) -> None:
    if not re.fullmatch(VERSION, tag):
        raise ValueError("Release tag must use vMAJOR.MINOR.PATCH.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be an owner/name pair.")


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Review file is missing or unreadable: {relative}.") from exc


def _project_tag(root: Path) -> str:
    text = _read(root, "pyproject.toml")
    project = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[|\Z)", text)
    version = re.search(r'''(?m)^version\s*=\s*["']([^"']+)["']\s*(?:\#.*)?$''',
                        project[1] if project else "")
    if not version:
        raise ValueError("A static project version is required in pyproject.toml.")
    return "v" + version[1]


def validate_review_form(root: Path) -> None:
    """Check the stable fields and offline headings; not a general YAML parser."""
    form = _read(root, FORM)
    record = _read(root, "docs/external-review/review-record-template.md")
    if (root / ".github/ISSUE_TEMPLATE/external-review.md").exists():
        raise ValueError("Remove the duplicate Markdown external-review template.")
    fields = {}
    for block in re.split(r"(?m)^  - type: ", form)[1:]:
        if block.startswith("markdown\n"):
            continue
        identifier = re.search(r"(?m)^    id: ([a-z0-9_-]+)$", block)
        label = re.search(r"(?m)^      label: (.+)$", block)
        if not identifier or not label or identifier[1] in fields:
            raise ValueError("Review form needs unique field IDs and labels.")
        fields[identifier[1]] = block
        if f"## {label[1]}" not in record.splitlines():
            raise ValueError("Offline report headings must match the review form.")
        if identifier[1] == "profile":
            if not re.search(r"(?m)^      required: false$", block):
                raise ValueError("Professional profile must remain optional.")
        elif not re.search(r"(?m)^ +required: true$", block):
            raise ValueError("Review report fields must be required; partial work is a valid answer.")
    expected = {"reviewer-name", "qualifications", "profile",
                "packet", "source", "group", "scope", "assessment", "findings",
                "conclusion", "context", "confirmation"}
    if set(fields) != expected:
        raise ValueError("Review form must preserve the shared report field IDs.")
    if list(fields)[:3] != ["reviewer-name", "qualifications", "profile"]:
        raise ValueError("Reviewer details must appear first in the form.")
    options = re.findall(r"(?m)^        - (.+)$", fields["group"])
    if options != list(PACKETS.values()):
        raise ValueError("Review form groups must match the settled reviewer groups.")
    for name in ("reviewer-name", "profile", "packet", "source"):
        if not fields[name].startswith("input\n") or re.search(r"(?m)^      value:", fields[name]):
            raise ValueError("Review identity fields must be text inputs without moving defaults.")


def validate_review_packets(root: Path, tag: str, repository: str) -> str:
    """Check references only; excerpts and technical conclusions need review."""
    _validate_arguments(tag, repository)
    folder = "docs/external-review/"
    latest = f"https://github.com/{repository}/releases/latest"
    return_path = f"https://github.com/{repository}/issues/new"
    validate_review_form(root)
    for entry in ("README.md", "START_HERE.md", folder + "current.md"):
        if latest not in _read(root, entry):
            raise ValueError(f"{entry}: new reviews must route to the latest published release.")
    overview = _read(root, folder + "README.md")
    target_line = f"Review target: [{tag}](targets/{tag}.md)."
    if [line for line in overview.splitlines() if line.startswith("Review target:")] != [target_line]:
        raise ValueError(f"{folder}README.md: Review target must match {tag}.")
    refs = re.findall(r"(?m)^Source ref: `([^`]+)`\.$", overview)
    if len(refs) != 1 or not (refs[0] == tag or re.fullmatch(r"[0-9a-f]{40}", refs[0])):
        raise ValueError(f"{folder}README.md: Source ref must be {tag} or a full commit hash.")
    source_ref = refs[0]
    sheet = _read(root, folder + f"targets/{tag}.md")
    if sheet.splitlines()[:1] != [f"# Review target: {tag}"]:
        raise ValueError("Review target heading does not match the release.")
    pinned = re.findall(r"(?m)^- \[Pinned source\]\(([^)]+)\)\.$", sheet)
    if pinned != [f"https://github.com/{repository}/tree/{source_ref}"]:
        raise ValueError("Target sheet Pinned source must match the overview Source ref.")
    # A source tree hash is distinct from its commit. Preserve that distinction.
    tree_hashes = re.findall(r"(?m)^- Tree: `([0-9a-f]{40})`\.$", sheet)
    source_urls = rf"https://github\.com/{re.escape(repository)}/(?:blob|tree)/([^/\s)]+)"
    archive_urls = rf"https://github\.com/{re.escape(repository)}/archive/([^\s)]+)\.zip"
    identity = rf"(?m)^- (?:\*\*(?:Software(?: and prepared records)?|Source):\*\*|Software(?: target)?:)\s*({VERSION})\b"
    for name in ("README.md", *PACKETS):
        text = overview if name == "README.md" else _read(root, folder + name)
        if latest not in text:
            raise ValueError(f"{folder}{name}: new reviews must route to the latest published release.")
        form_links = re.findall(rf"{re.escape(return_path)}\?[^\s)]+", text)
        if not form_links:
            raise ValueError(f"{folder}{name}: public responses must link to the external-review issue template.")
        for link in form_links:
            query = parse_qs(urlsplit(link).query)
            if query.get("template") != ["external-review.yml"]:
                raise ValueError(f"{folder}{name}: public responses must link to the external-review issue template.")
            if name in PACKETS and query.get("source") != [f"{tag} / {source_ref}"]:
                raise ValueError(f"{folder}{name}: form source prefill must match the packet version and source.")
            if "packet" in query:
                raise ValueError("Packet permalink must be supplied by the reviewer, not a moving prefill.")
        target_refs = re.findall(r"targets/(v[0-9]+\.[0-9]+\.[0-9]+)\.md", text)
        if not target_refs or set(target_refs) != {tag}:
            raise ValueError(f"{folder}{name}: target-sheet links must match {tag}.")
        if name in PACKETS:
            versions = re.findall(identity, text)
            if not versions or set(versions) != {tag}:
                raise ValueError(f"{folder}{name}: software identity and response version must match {tag}.")
        linked_refs = re.findall(source_urls, text) + re.findall(archive_urls, text)
        if (name in PACKETS and not linked_refs) or any(ref != source_ref for ref in linked_refs):
            raise ValueError(f"{folder}{name}: source links must use the overview Source ref.")
        commit_text = text
        for tree_hash in tree_hashes:
            commit_text = re.sub(rf"(?i)\btree\s+`{tree_hash}`", "", commit_text)
        if set(re.findall(r"\b[0-9a-f]{40}\b", commit_text)) - {source_ref}:
            raise ValueError(f"{folder}{name}: commit or tree hash does not match the target sheet.")
        if name == "technical-review.md":
            checkout_refs = re.findall(r"(?m)^git checkout --detach (\S+)\s*$", text)
            if checkout_refs != [source_ref]:
                raise ValueError(f"{folder}{name}: checkout command must use the overview Source ref.")
    return source_ref


def validate_review_target(root: Path, tag: str, repository: str) -> None:
    _validate_arguments(tag, repository)
    target = f"docs/external-review/targets/{tag}.md"
    sheet = _read(root, target)
    notes = _read(root, f"docs/releases/{tag}.md")
    if sheet.splitlines()[:1] != [f"# Review target: {tag}"]:
        raise ValueError("Review target heading does not match the release.")
    link = f"[Review target](https://github.com/{repository}/blob/{tag}/{target})"
    if link not in notes:
        raise ValueError("Release notes must include the version-pinned Review target link.")
    sections = re.findall(r"(?ms)^## Review this release\s*\n(.*?)(?=^## |\Z)", notes)
    if len(sections) != 1:
        raise ValueError("Release notes must have one Review this release section.")
    for name, label in PACKETS.items():
        link = f"[{label}](https://github.com/{repository}/blob/{tag}/docs/external-review/{name})"
        if link not in sections[0]:
            raise ValueError(f"Release notes must include the version-pinned packet link: {name}.")
    packet_urls = re.findall(
        rf"https://github\.com/{re.escape(repository)}/blob/([^/]+)/docs/external-review/([^\s)#]+)",
        sections[0],
    )
    if any(ref != tag for ref, name in packet_urls if name in PACKETS):
        raise ValueError("Review this release must not mix packet versions.")
    source_ref = validate_review_packets(root, tag, repository)
    if source_ref != tag:
        try:
            resolved = subprocess.run(
                ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                cwd=root, capture_output=True, text=True, check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError("Cannot resolve the release tag to verify the packet commit.") from exc
        if resolved != source_ref:
            raise ValueError("Packet source commit does not match the release tag.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Release tag; defaults to the static project version.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--packets-only", action="store_true",
                        help="Check packet references without requiring release notes or Git tags.")
    args = parser.parse_args()
    try:
        root = Path.cwd()
        tag = args.tag or _project_tag(root)
        if args.packets_only:
            validate_review_packets(root, tag, args.repository)
        else:
            validate_review_target(root, tag, args.repository)
    except ValueError as exc:
        print(f"Review target check failed: {exc}", file=sys.stderr)
        return 1
    print("Review packet references checked." if args.packets_only else
          "Review packets, target, and version-pinned release link checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
