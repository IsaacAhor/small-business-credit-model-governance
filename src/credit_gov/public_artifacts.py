"""Portable-content checks for public distribution artifacts."""

from __future__ import annotations

import gzip
import re
import stat
import tarfile
import unicodedata
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator


MAX_MEMBER_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 100 * 1024 * 1024
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "tmp",
}

_USER_DIRECTORY = "Us" + "ers"

CONTENT_PATTERNS = (
    (
        "absolute Windows user path",
        re.compile(
            r"(?i)(?:[A-Z]:)?[\\/]+"
            + _USER_DIRECTORY
            + r"[\\/]+[^\\/\s\"']+"
        ),
    ),
    (
        "absolute Unix home path",
        re.compile(
            r"(?i)/(?:" + _USER_DIRECTORY + r"|home|root)/[^/\s\"']*"
        ),
    ),
    (
        "Windows Subsystem for Linux user path",
        re.compile(
            r"(?i)/mnt/[A-Z]/" + _USER_DIRECTORY + r"/[^/\s\"']+"
        ),
    ),
    (
        "UNC network path",
        re.compile(r"(?i)\\\\[A-Z0-9._-]+\\[A-Z0-9$._-]+(?:\\[^\s\"']+)?"),
    ),
    (
        "email address",
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    ),
    (
        "phone number",
        re.compile(
            r"(?<![\w/])(?:"
            r"(?:\+?1[ .-])?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}"
            r"|\+\d{1,3}[ .-](?:\d{2,4}[ .-]){1,3}\d{3,4}"
            r")(?![\w-])"
        ),
    ),
    (
        "private-key marker",
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    ),
    (
        "high-confidence credential token",
        re.compile(
            r"(?i)(?<![A-Z0-9])(?:AKIA[0-9A-Z]{16}|"
            r"github_pat_[A-Z0-9_]{20,}|gh[pousr]_[A-Z0-9]{30,}|"
            r"sk-[A-Z0-9_-]{20,})(?![A-Z0-9_-])"
        ),
    ),
    (
        "US Social Security number pattern",
        re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    ),
    (
        "local environment identity assignment",
        re.compile(
            r"(?im)^\s*(?:USERPROFILE|HOMEDRIVE|HOMEPATH|HOME|USERNAME|"
            r"LOGNAME|COMPUTERNAME|HOSTNAME)\s*[:=]\s*\S+"
        ),
    ),
    (
        "credential-like assignment",
        re.compile(
            r"(?ix)(?<![A-Z0-9_-])"
            r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)"
            r"\s*[:=]\s*[\"']?"
            r"(?!example\b|placeholder\b|dummy\b|redacted\b|none\b|null\b)"
            r"[A-Z0-9_./+\-=]{12,}"
        ),
    ),
    (
        "long encoded payload",
        re.compile(
            r"(?<![A-Z0-9+/])(?:[A-Z0-9+/]{4}){32,}(?:==|=)?"
            r"(?![A-Z0-9+/])",
            re.IGNORECASE,
        ),
    ),
)

BINARY_SIGNATURES = (
    b"%PDF-",
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"PK\x03\x04",
    b"\x1f\x8b",
    b"SQLite format 3\x00",
    b"MZ",
    b"\x7fELF",
)


@dataclass(frozen=True, order=True)
class ArtifactFinding:
    location: str
    category: str


def _is_unsafe_member_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return (
        path.is_absolute()
        or ".." in path.parts
        or bool(re.match(r"(?i)^[A-Z]:/", normalized))
    )


def _scan_text(data: bytes, location: str) -> Iterator[ArtifactFinding]:
    if len(data) > MAX_MEMBER_BYTES:
        yield ArtifactFinding(
            location=location,
            category="oversized content requires separate inspection",
        )
        return
    if b"\x00" in data or any(data.startswith(signature) for signature in BINARY_SIGNATURES):
        yield ArtifactFinding(
            location=location,
            category="binary content requires separate inspection",
        )
        return
    try:
        text = unicodedata.normalize("NFKC", data.decode("utf-8"))
    except UnicodeDecodeError:
        yield ArtifactFinding(
            location=location,
            category="non-UTF-8 content requires separate inspection",
        )
        return
    for category, pattern in CONTENT_PATTERNS:
        if pattern.search(text):
            yield ArtifactFinding(location=location, category=category)


def _scan_name(name: str, location: str, name_kind: str) -> Iterator[ArtifactFinding]:
    for finding in _scan_text(name.encode("utf-8"), location):
        yield ArtifactFinding(
            location=finding.location,
            category=f"{finding.category} in {name_kind}",
        )


def _looks_like_nested_archive(data: bytes) -> bool:
    return (
        data.startswith((b"PK\x03\x04", b"\x1f\x8b"))
        or (len(data) > 262 and data[257:262] == b"ustar")
    )


def _scan_gzip_metadata(path: Path, location: str) -> Iterator[ArtifactFinding]:
    with path.open("rb") as stream:
        header = stream.read(10)
        if len(header) != 10 or not header.startswith(b"\x1f\x8b"):
            yield ArtifactFinding(location, "unreadable gzip metadata")
            return
        flags = header[3]
        if flags & 0xE0:
            yield ArtifactFinding(location, "unreadable gzip metadata")
            return
        if flags & 0x04:
            encoded_length = stream.read(2)
            if len(encoded_length) != 2:
                yield ArtifactFinding(location, "unreadable gzip metadata")
                return
            extra_length = int.from_bytes(encoded_length, "little")
            if len(stream.read(extra_length)) != extra_length:
                yield ArtifactFinding(location, "unreadable gzip metadata")
                return
            if extra_length:
                yield ArtifactFinding(
                    location,
                    "gzip extra metadata requires separate inspection",
                )
        for flag, kind in ((0x08, "gzip filename"), (0x10, "gzip comment")):
            if not flags & flag:
                continue
            value = bytearray()
            while len(value) <= MAX_MEMBER_BYTES:
                character = stream.read(1)
                if not character:
                    yield ArtifactFinding(location, "unreadable gzip metadata")
                    return
                if character == b"\x00":
                    break
                value.extend(character)
            else:
                yield ArtifactFinding(
                    location,
                    f"oversized {kind} requires separate inspection",
                )
                return
            decoded = bytes(value).decode("latin-1")
            yield from _scan_name(decoded, location, kind)


def _scan_zip(path: Path, location: str) -> Iterator[ArtifactFinding]:
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            yield ArtifactFinding(location, "archive member limit exceeded")
            return
        if archive.comment:
            yield from _scan_text(archive.comment, f"{location}!archive-comment")
        total_size = 0
        for index, member in enumerate(members, start=1):
            member_location = f"{location}!member[{index}]"
            yield from _scan_name(member.filename, member_location, "archive path")
            if member.comment:
                yield from _scan_text(member.comment, f"{member_location}!comment")
            if member.extra:
                yield ArtifactFinding(
                    location=member_location,
                    category="archive extra metadata requires separate inspection",
                )
            if _is_unsafe_member_name(member.filename):
                yield ArtifactFinding(
                    location=member_location,
                    category="unsafe archive path",
                )
            member_mode = member.external_attr >> 16
            if stat.S_ISLNK(member_mode):
                yield ArtifactFinding(
                    location=member_location,
                    category="archive symbolic link requires separate inspection",
                )
                continue
            if member.is_dir():
                continue
            total_size += member.file_size
            if total_size > MAX_ARCHIVE_TOTAL_BYTES:
                yield ArtifactFinding(location, "archive expanded-size limit exceeded")
                return
            if member.flag_bits & 0x1:
                yield ArtifactFinding(
                    location=member_location,
                    category="encrypted archive member cannot be inspected",
                )
                continue
            if member.file_size > MAX_MEMBER_BYTES:
                yield ArtifactFinding(
                    location=member_location,
                    category="oversized archive member requires separate inspection",
                )
                continue
            member_data = archive.read(member)
            if _looks_like_nested_archive(member_data):
                yield ArtifactFinding(
                    location=member_location,
                    category="nested archive requires separate inspection",
                )
                continue
            yield from _scan_text(member_data, member_location)


def _scan_tar(path: Path, location: str) -> Iterator[ArtifactFinding]:
    with tarfile.open(path, mode="r:*") as archive:
        for key, value in sorted(archive.pax_headers.items()):
            yield from _scan_name(key, location, "archive global metadata key")
            yield from _scan_name(value, location, "archive global metadata value")
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            yield ArtifactFinding(location, "archive member limit exceeded")
            return
        total_size = 0
        for index, member in enumerate(members, start=1):
            member_location = f"{location}!member[{index}]"
            yield from _scan_name(member.name, member_location, "archive path")
            if member.uname or member.gname or member.uid or member.gid:
                yield ArtifactFinding(
                    location=member_location,
                    category="archive ownership metadata requires separate inspection",
                )
            for key, value in sorted(member.pax_headers.items()):
                yield from _scan_name(key, member_location, "archive metadata key")
                yield from _scan_name(value, member_location, "archive metadata value")
            if _is_unsafe_member_name(member.name):
                yield ArtifactFinding(
                    location=member_location,
                    category="unsafe archive path",
                )
            if member.isdir():
                continue
            if member.issym() or member.islnk():
                yield from _scan_name(
                    member.linkname,
                    member_location,
                    "archive link target",
                )
                if _is_unsafe_member_name(member.linkname):
                    yield ArtifactFinding(
                        location=member_location,
                        category="unsafe archive link target",
                    )
                yield ArtifactFinding(
                    location=member_location,
                    category="archive link requires separate inspection",
                )
                continue
            if not member.isfile():
                yield ArtifactFinding(
                    location=member_location,
                    category="unsupported archive member cannot be inspected",
                )
                continue
            total_size += member.size
            if total_size > MAX_ARCHIVE_TOTAL_BYTES:
                yield ArtifactFinding(location, "archive expanded-size limit exceeded")
                return
            if member.size > MAX_MEMBER_BYTES:
                yield ArtifactFinding(
                    location=member_location,
                    category="oversized archive member requires separate inspection",
                )
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                yield ArtifactFinding(
                    location=member_location,
                    category="unreadable archive member",
                )
                continue
            member_data = extracted.read()
            if _looks_like_nested_archive(member_data):
                yield ArtifactFinding(
                    location=member_location,
                    category="nested archive requires separate inspection",
                )
                continue
            yield from _scan_text(member_data, member_location)


def _scan_file(path: Path, location: str) -> Iterator[ArtifactFinding]:
    file_size = path.stat().st_size
    if file_size > MAX_ARCHIVE_BYTES:
        yield ArtifactFinding(
            location,
            "oversized artifact requires separate inspection",
        )
        return
    if zipfile.is_zipfile(path):
        yield from _scan_zip(path, location)
        return
    if tarfile.is_tarfile(path):
        if path.name.lower().endswith((".gz", ".tgz")):
            yield from _scan_gzip_metadata(path, location)
        yield from _scan_tar(path, location)
        return
    if file_size > MAX_MEMBER_BYTES:
        yield ArtifactFinding(
            location,
            "oversized content requires separate inspection",
        )
        return
    yield from _scan_text(path.read_bytes(), location)


def _iter_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        yield path
        return
    for candidate in sorted(path.rglob("*")):
        should_skip = any(
            part in SKIP_PARTS or part.startswith(".tmp-")
            for part in candidate.relative_to(path).parts
        )
        if not should_skip and (
            candidate.is_symlink() or candidate.is_dir() or candidate.is_file()
        ):
            yield candidate


def normalize_source_distribution(path: Path) -> None:
    """Remove host ownership fields while preserving a source archive's payload."""

    if not path.is_file() or not path.name.lower().endswith((".tar.gz", ".tgz")):
        raise ValueError("input is not a gzip-compressed source archive")
    temporary_path = path.with_name(f".{path.name}.normalized")
    temporary_path.unlink(missing_ok=True)
    try:
        with tarfile.open(path, mode="r:gz") as source:
            members = source.getmembers()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise ValueError("archive member limit exceeded")
            total_size = 0
            payloads: list[tuple[tarfile.TarInfo, bytes | None]] = []
            for member in members:
                if _is_unsafe_member_name(member.name):
                    raise ValueError("unsafe archive path")
                if not member.isfile() and not member.isdir():
                    raise ValueError("unsupported archive member")
                if member.isdir():
                    payloads.append((member, None))
                    continue
                total_size += member.size
                if member.size > MAX_MEMBER_BYTES:
                    raise ValueError("archive member limit exceeded")
                if total_size > MAX_ARCHIVE_TOTAL_BYTES:
                    raise ValueError("archive expanded-size limit exceeded")
                extracted = source.extractfile(member)
                if extracted is None:
                    raise ValueError("unreadable archive member")
                data = extracted.read(MAX_MEMBER_BYTES + 1)
                if len(data) != member.size:
                    raise ValueError("archive member size mismatch")
                payloads.append((member, data))

        with temporary_path.open("wb") as raw_output:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw_output,
                mtime=0,
            ) as compressed_output:
                with tarfile.open(
                    fileobj=compressed_output,
                    mode="w",
                    format=tarfile.PAX_FORMAT,
                ) as normalized:
                    for member, data in payloads:
                        clean = tarfile.TarInfo(member.name)
                        clean.mode = member.mode
                        clean.mtime = int(member.mtime)
                        clean.uid = 0
                        clean.gid = 0
                        clean.uname = ""
                        clean.gname = ""
                        clean.type = (
                            tarfile.DIRTYPE if member.isdir() else tarfile.REGTYPE
                        )
                        clean.size = 0 if data is None else len(data)
                        normalized.addfile(
                            clean,
                            None if data is None else BytesIO(data),
                        )

        with tarfile.open(temporary_path, mode="r:gz") as check:
            normalized_members = check.getmembers()
            if len(normalized_members) != len(payloads):
                raise ValueError("normalized archive member count mismatch")
            for (source_member, source_data), normalized_member in zip(
                payloads,
                normalized_members,
                strict=True,
            ):
                if (
                    normalized_member.name != source_member.name
                    or normalized_member.mode != source_member.mode
                    or normalized_member.mtime != int(source_member.mtime)
                    or normalized_member.isdir() != source_member.isdir()
                    or normalized_member.size
                    != (0 if source_data is None else len(source_data))
                ):
                    raise ValueError("normalized archive metadata mismatch")
                if source_data is not None:
                    extracted = check.extractfile(normalized_member)
                    if extracted is None or extracted.read() != source_data:
                        raise ValueError("normalized archive payload mismatch")

        if validate_public_artifacts([temporary_path]):
            raise ValueError("normalized archive did not pass validation")
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def validate_public_artifacts(paths: Iterable[Path]) -> list[ArtifactFinding]:
    """Return redaction-safe findings without echoing matched content."""

    findings: set[ArtifactFinding] = set()
    for input_index, supplied in enumerate(paths, start=1):
        path = Path(supplied)
        input_location = f"input[{input_index}]"
        if not path.exists():
            findings.add(ArtifactFinding(input_location, "path does not exist"))
            continue
        if path.is_symlink():
            findings.add(
                ArtifactFinding(
                    input_location,
                    "symbolic link requires separate inspection",
                )
            )
            continue
        if path.is_dir():
            findings.update(_scan_name(path.name, input_location, "input path"))
        try:
            files = list(_iter_files(path))
        except Exception:
            findings.add(ArtifactFinding(input_location, "unreadable input tree"))
            continue
        for file_index, file_path in enumerate(files, start=1):
            location = (
                input_location
                if path.is_file()
                else f"{input_location}!file[{file_index}]"
            )
            try:
                if file_path.is_symlink():
                    findings.add(
                        ArtifactFinding(
                            location,
                            "symbolic link requires separate inspection",
                        )
                    )
                    continue
                public_name = (
                    file_path.name
                    if path.is_file()
                    else file_path.relative_to(path).as_posix()
                )
                findings.update(_scan_name(public_name, location, "file path"))
                if not file_path.is_dir():
                    findings.update(_scan_file(file_path, location))
            except Exception:
                findings.add(ArtifactFinding(location, "unreadable artifact"))
    return sorted(findings)
