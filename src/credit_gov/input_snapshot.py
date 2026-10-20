"""Captured diagnostic inputs, shared by validation, computation and provenance."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any


class DatasetSnapshot:
    """Capture top-level JSON once; later edits and additions cannot change it.

    Reference existence checks may still inspect the filesystem. External BISG
    reference bytes are recorded when loaded. This is not a filesystem transaction
    or an assertion that the captured inputs remain current.
    """

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.files = MappingProxyType({
            path.name: path.read_bytes()
            for path in sorted(self.root.glob("*.json")) if path.is_file()
        })
        self._files_by_name = {os.path.normcase(name): raw for name, raw in self.files.items()}
        self._references: dict[str, bytes] = {}

    def __str__(self) -> str:
        return str(self.root)

    def __truediv__(self, name: str | Path) -> _InputFile:
        return _InputFile(self, self.root / name)

    def resolve(self) -> Path:
        return self.root

    def relative_to(self, other: Path) -> Path:
        return self.root.relative_to(other)

    def reference_json(self, role: str, raw: bytes) -> Any:
        if role in self._references:
            raise ValueError(f"Reference already captured: {role}")
        self._references[role] = raw
        return json.loads(raw.decode("utf-8"))

    def normalized_fingerprints(self) -> dict[str, str]:
        return {
            name: hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()
            for name, raw in self.files.items()
        }

    def provenance(self) -> dict[str, Any]:
        hashes = {
            **{f"dataset/{name}": hashlib.sha256(raw).hexdigest()
               for name, raw in self.files.items()},
            **{f"reference/{role}": hashlib.sha256(raw).hexdigest()
               for role, raw in self._references.items()},
        }
        return {
            "input_snapshot_scope": (
                "Captured top-level dataset JSON and external reference bytes used; "
                "not an atomic filesystem snapshot or a current-use authorization."
            ),
            "input_files_sha256": hashes,
            "input_snapshot_sha256": hashlib.sha256(
                json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "input_fingerprints_normalization": "Dataset JSON only; CRLF and CR normalized to LF.",
        }


class _InputFile:
    def __init__(self, snapshot: DatasetSnapshot, path: Path):
        self.snapshot = snapshot
        self.path = Path(os.path.abspath(path))

    @property
    def name(self) -> str:
        return self.path.name

    def _is_dataset_json(self) -> bool:
        return self.path.parent == self.snapshot.root and os.path.normcase(self.path.suffix) == ".json"

    def is_file(self) -> bool:
        if self._is_dataset_json():
            return os.path.normcase(self.name) in self.snapshot._files_by_name
        return self.path.is_file()

    def read_bytes(self) -> bytes:
        if self._is_dataset_json():
            try:
                return self.snapshot._files_by_name[os.path.normcase(self.name)]
            except KeyError:
                raise FileNotFoundError(self.path) from None
        # Only explicitly loaded external references take this path. Their caller
        # records these same bytes through reference_json before computing.
        return self.path.read_bytes()

    def open(self, *, encoding: str = "utf-8") -> io.StringIO:
        return io.StringIO(self.read_bytes().decode(encoding))
