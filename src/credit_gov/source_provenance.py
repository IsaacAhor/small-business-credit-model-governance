"""Identify source files in a stable local run; no approval or attestation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from credit_gov.schemas import validators


def _source_files(package: Path, schema_dir: Path, entrypoint: Path | None) -> dict[str, Path]:
    sources = {
        "package/credit_gov/" + path.relative_to(package).as_posix(): path
        for path in package.rglob("*")
        if path.suffix in {".py", ".json"} and "__pycache__" not in path.parts
    }
    # Match the validator's override-before-packaged-resource lookup.
    packaged_schemas = package / "schemas/json"
    schema_names = {path.name for directory in (packaged_schemas, schema_dir)
                    for path in directory.glob("*.json")}
    for name in schema_names:
        override = schema_dir / name
        sources["effective_schemas/" + name] = (
            override if override.is_file() else packaged_schemas / name
        )
    if entrypoint is not None:
        sources["entrypoint/" + entrypoint.name] = entrypoint
    if not sources or "package/credit_gov/__init__.py" not in sources:
        raise ValueError("Source package is unavailable for fingerprinting.")
    return sources


def _git_state(package: Path) -> dict[str, str]:
    unavailable = {"source_revision": "unavailable", "source_tree_state": "unavailable"}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(package), *args], capture_output=True, text=True,
            check=True, timeout=10,
            env={key: value for key, value in os.environ.items()
                 if not key.upper().startswith("GIT_")},
        ).stdout.strip()

    try:
        root = Path(git("rev-parse", "--show-toplevel")).resolve()
        relative = (package / "__init__.py").resolve().relative_to(root).as_posix()
        # An unrelated repository surrounding an installed package is not its source.
        git("ls-files", "--error-unmatch", "--", ":(top)" + relative)
        revision = git("rev-parse", "HEAD")
        state = "modified" if git("status", "--porcelain", "--untracked-files=all") else "clean"
        return {"source_revision": revision, "source_tree_state": state}
    except (OSError, ValueError, subprocess.SubprocessError):
        return unavailable


def capture_source_provenance(entrypoint: Path | None = None) -> dict[str, Any]:
    """Hash package code/resources, effective schemas and an optional driver.

    Git metadata comes from the code location, never the dataset or an environment
    override. The hashes identify disk bytes, not a signed executable or runtime.
    Retain those source files to reproduce a modified or unpacked installation.
    """
    package = Path(__file__).resolve().parent
    sources = _source_files(package, validators.SCHEMA_DIR, entrypoint)
    hashes = {}
    for name, path in sorted(sources.items()):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Source fingerprints require readable regular files.")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    canonical = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "source_fingerprint_version": 1,
        "source_snapshot_scope": "package_code_resources_effective_schemas"
                                 + ("_and_entrypoint" if entrypoint is not None else ""),
        "source_snapshot_sha256": hashlib.sha256(canonical).hexdigest(),
        "source_files_sha256": hashes,
        **_git_state(package),
    }


def check_source_unchanged(provenance: dict[str, Any], entrypoint: Path | None = None) -> None:
    """Detect changes present at this check; this does not coordinate writers."""
    current = capture_source_provenance(entrypoint)
    # Checkout state is the initial Git observation. Writing outputs can change
    # it legitimately; source identities and the observed commit must stay fixed.
    fields = ("source_fingerprint_version", "source_snapshot_scope",
              "source_snapshot_sha256", "source_files_sha256", "source_revision")
    if any(field not in current or current[field] != provenance.get(field) for field in fields):
        raise ValueError("Source files changed during this run; rerun with stable source files.")
