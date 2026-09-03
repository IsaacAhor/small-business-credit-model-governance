from __future__ import annotations

import gzip
import stat
import sys
import tarfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tests.temp_utils import LocalTemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMP_ROOT = ROOT / "tmp" / "test-runs"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import credit_gov.public_artifacts as public_artifacts  # noqa: E402
from credit_gov.public_artifacts import validate_public_artifacts  # noqa: E402
from scripts import validate_public_artifacts as validator_script  # noqa: E402
from scripts import validate_repository as repository_validator  # noqa: E402


class PublicArtifactValidationTests(unittest.TestCase):
    def test_clean_relative_content_passes(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "run-record.txt"
            path.write_text("dataset=data/synthetic/monthly-demo\n", encoding="utf-8")

            self.assertEqual(validate_public_artifacts([path]), [])

    def test_absolute_user_path_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "run-record.txt"
            separator = chr(92)
            value = "C:" + separator + "Users" + separator + "sample" + separator + "work"
            path.write_text(value + "\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "absolute Windows user path")
        self.assertNotIn("sample", repr(findings[0]))

    def test_email_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "metadata.txt"
            value = "reviewer" + chr(64) + "example.org"
            path.write_text(value + "\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address")
        self.assertNotIn("reviewer", repr(findings[0]))

    def test_phone_number_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "metadata.txt"
            value = "312" + chr(45) + "555" + chr(45) + "0199"
            path.write_text(value + "\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "phone number")
        self.assertNotIn("0199", repr(findings[0]))

    def test_zip_contents_and_member_paths_are_checked(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            separator = chr(92)
            value = "C:" + separator + "Users" + separator + "sample" + separator + "work"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr("logs/run.txt", value)
                archive.writestr("../outside.txt", "relative content")

            findings = validate_public_artifacts([path])

        self.assertEqual(
            {finding.category for finding in findings},
            {"absolute Windows user path", "unsafe archive path"},
        )
        self.assertNotIn("sample", repr(findings))
        self.assertNotIn("outside", repr(findings))

    def test_sensitive_archive_member_name_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            private_name = "reviewer" + chr(64) + "example.org.txt"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr("reports/" + private_name, "relative content")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address in archive path")
        self.assertNotIn("reviewer", repr(findings))

    def test_sensitive_file_name_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            private_name = "reviewer" + chr(64) + "example.org.txt"
            path = Path(temp_dir) / private_name
            path.write_text("relative content\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address in file path")
        self.assertNotIn("reviewer", repr(findings))

    def test_sensitive_directory_name_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            private_name = "reviewer" + chr(64) + "example.org"
            private_directory = Path(temp_dir) / private_name
            private_directory.mkdir()
            (private_directory / "run.txt").write_text(
                "relative content\n",
                encoding="utf-8",
            )

            findings = validate_public_artifacts([Path(temp_dir)])

        self.assertEqual(
            {finding.category for finding in findings},
            {"email address in file path"},
        )
        self.assertNotIn("reviewer", repr(findings))

    def test_tar_contents_are_checked(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.tar.gz"
            separator = chr(92)
            value = "C:" + separator + "Users" + separator + "sample" + separator + "work"
            payload = value.encode("utf-8")
            with tarfile.open(path, mode="w:gz") as archive:
                member = tarfile.TarInfo("logs/run.txt")
                member.size = len(payload)
                archive.addfile(member, BytesIO(payload))

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "absolute Windows user path")
        self.assertNotIn("sample", repr(findings))

    def test_high_confidence_credential_is_reported_without_echoing_value(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "metadata.txt"
            value = "github" + "_pat_" + ("a" * 24)
            path.write_text(value + "\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "high-confidence credential token")
        self.assertNotIn(value, repr(findings))

    def test_social_security_number_pattern_is_reported(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "metadata.txt"
            value = "123" + chr(45) + "45" + chr(45) + "6789"
            path.write_text(value + "\n", encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "US Social Security number pattern")
        self.assertNotIn(value, repr(findings))

    def test_binary_content_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "capture.bin"
            path.write_bytes(b"public-prefix\x00uninspected-content")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "binary content requires separate inspection",
        )

    def test_non_utf8_content_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "capture.bin"
            path.write_bytes(b"public-prefix\xffuninspected-content")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "non-UTF-8 content requires separate inspection",
        )

    def test_oversized_file_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "large.txt"
            path.write_bytes(b"x" * 65)

            with patch("credit_gov.public_artifacts.MAX_MEMBER_BYTES", 64):
                findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "oversized content requires separate inspection",
        )

    def test_oversized_archive_member_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr("logs/run.txt", b"x" * 65)

            with patch("credit_gov.public_artifacts.MAX_MEMBER_BYTES", 64):
                findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "oversized archive member requires separate inspection",
        )

    def test_oversized_archive_fails_closed_before_parsing(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr("reports/run.txt", b"x" * 65)

            with patch("credit_gov.public_artifacts.MAX_ARCHIVE_BYTES", 64):
                findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "oversized artifact requires separate inspection",
        )

    def test_root_symbolic_link_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "run.txt"
            path.write_text("relative content\n", encoding="utf-8")

            with patch.object(Path, "is_symlink", return_value=True):
                findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "symbolic link requires separate inspection",
        )

    def test_unicode_normalization_exposes_disguised_email(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "metadata.txt"
            value = "reviewer" + "\uff20" + "example.org"
            path.write_text(value, encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address")
        self.assertNotIn("reviewer", repr(findings))

    def test_environment_identity_assignment_is_reported(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "environment.txt"
            value = "USER" + "NAME=workstation-user"
            path.write_text(value, encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "local environment identity assignment",
        )

    def test_credential_like_assignment_is_reported(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "environment.txt"
            value = "api" + "_key=" + ("a" * 24)
            path.write_text(value, encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "credential-like assignment")
        self.assertNotIn(value, repr(findings))

    def test_long_encoded_payload_is_reported(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "encoded.txt"
            path.write_text("A" * 128, encoding="utf-8")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "long encoded payload")

    def test_zip_archive_comment_is_checked(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            value = "reviewer" + chr(64) + "example.org"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.comment = value.encode("utf-8")
                archive.writestr("reports/run.txt", "relative content")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address")
        self.assertNotIn("reviewer", repr(findings))

    def test_zip_extra_metadata_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            info = zipfile.ZipInfo("reports/run.txt")
            info.extra = b"\x01\x00\x00\x00"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr(info, "relative content")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "archive extra metadata requires separate inspection",
        )

    def test_zip_symbolic_link_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.zip"
            info = zipfile.ZipInfo("reports/latest")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr(info, "run.txt")

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "archive symbolic link requires separate inspection",
        )

    def test_nested_archive_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            inner = BytesIO()
            with zipfile.ZipFile(inner, mode="w") as archive:
                archive.writestr("payload.txt", "relative content")
            path = Path(temp_dir) / "verification.zip"
            with zipfile.ZipFile(path, mode="w") as archive:
                archive.writestr("nested.zip", inner.getvalue())

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "nested archive requires separate inspection",
        )

    def test_tar_owner_metadata_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.tar"
            payload = b"relative content"
            with tarfile.open(path, mode="w") as archive:
                member = tarfile.TarInfo("reports/run.txt")
                member.size = len(payload)
                member.uid = 1001
                member.uname = "builder"
                archive.addfile(member, BytesIO(payload))

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "archive ownership metadata requires separate inspection",
        )

    def test_tar_link_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.tar"
            with tarfile.open(path, mode="w") as archive:
                member = tarfile.TarInfo("reports/latest")
                member.type = tarfile.SYMTYPE
                member.linkname = "../outside.txt"
                archive.addfile(member)

            findings = validate_public_artifacts([path])

        self.assertEqual(
            {finding.category for finding in findings},
            {"archive link requires separate inspection", "unsafe archive link target"},
        )

    def test_gzip_filename_metadata_is_checked(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            tar_payload = BytesIO()
            with tarfile.open(fileobj=tar_payload, mode="w") as archive:
                payload = b"relative content"
                member = tarfile.TarInfo("reports/run.txt")
                member.size = len(payload)
                archive.addfile(member, BytesIO(payload))
            path = Path(temp_dir) / "verification.tar.gz"
            value = "reviewer" + chr(64) + "example.org"
            with path.open("wb") as output:
                with gzip.GzipFile(filename=value, mode="wb", fileobj=output) as stream:
                    stream.write(tar_payload.getvalue())

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "email address in gzip filename")
        self.assertNotIn("reviewer", repr(findings))

    def test_gzip_extra_metadata_fails_closed(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.tar.gz"
            with tarfile.open(path, mode="w:gz") as archive:
                payload = b"relative content"
                member = tarfile.TarInfo("reports/run.txt")
                member.size = len(payload)
                archive.addfile(member, BytesIO(payload))
            compressed = bytearray(path.read_bytes())
            compressed[3] |= 0x04
            compressed[10:10] = b"\x04\x00meta"
            path.write_bytes(compressed)

            findings = validate_public_artifacts([path])

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category,
            "gzip extra metadata requires separate inspection",
        )

    def test_tar_global_metadata_is_checked(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            path = Path(temp_dir) / "verification.tar"
            value = "reviewer" + chr(64) + "example.org"
            with tarfile.open(
                path,
                mode="w",
                format=tarfile.PAX_FORMAT,
                pax_headers={"comment": value},
            ) as archive:
                payload = b"relative content"
                member = tarfile.TarInfo("reports/run.txt")
                member.size = len(payload)
                archive.addfile(member, BytesIO(payload))

            findings = validate_public_artifacts([path])

        self.assertEqual(
            {finding.category for finding in findings},
            {
                "email address in archive global metadata value",
                "email address in archive metadata value",
            },
        )
        self.assertNotIn("reviewer", repr(findings))

    def test_directory_traversal_error_is_redacted_and_blocks(self) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with LocalTemporaryDirectory(TEMP_ROOT) as temp_dir:
            marker = "sensitive-value-must-not-appear"
            with patch(
                "credit_gov.public_artifacts._iter_files",
                side_effect=OSError(marker),
            ):
                findings = validate_public_artifacts([Path(temp_dir)])

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "unreadable input tree")
        self.assertNotIn(marker, repr(findings))

    def test_unexpected_cli_error_is_redacted_and_blocks(self) -> None:
        marker = "sensitive-path-value-must-not-appear"
        output = StringIO()

        with patch.object(validator_script, "main", side_effect=RuntimeError(marker)):
            with redirect_stdout(output):
                exit_code = validator_script.guarded_main()

        self.assertEqual(exit_code, 2)
        self.assertNotIn(marker, output.getvalue())
        self.assertIn("details suppressed", output.getvalue())

    def test_unexpected_repository_error_is_redacted_and_blocks(self) -> None:
        marker = "sensitive-path-value-must-not-appear"
        output = StringIO()

        with patch.object(repository_validator, "main", side_effect=RuntimeError(marker)):
            with redirect_stderr(output):
                exit_code = repository_validator.guarded_main()

        self.assertEqual(exit_code, 2)
        self.assertNotIn(marker, output.getvalue())
        self.assertIn("details suppressed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
