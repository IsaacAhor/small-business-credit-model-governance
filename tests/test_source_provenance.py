from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_gov import source_provenance
from credit_gov import monitoring
from credit_gov.monitoring import run_monthly_monitoring
from credit_gov.source_provenance import capture_source_provenance, check_source_unchanged


class SourceProvenanceTests(unittest.TestCase):
    def test_loaded_package_revision_ignores_environment_claim_and_records_relative_hashes(self):
        expected = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        driver = ROOT / "scripts/run_adverse_action_reason_benchmark.py"
        with patch.dict(os.environ, {"CREDIT_GOV_SOURCE_REVISION": "unverified-override"}):
            result = capture_source_provenance(driver)
        self.assertEqual(expected, result["source_revision"])
        self.assertIn(result["source_tree_state"], ("clean", "modified"))
        self.assertTrue(result["source_snapshot_scope"].endswith("_and_entrypoint"))
        self.assertEqual(
            hashlib.sha256(driver.read_bytes()).hexdigest(),
            result["source_files_sha256"]["entrypoint/" + driver.name],
        )
        self.assertNotIn(str(ROOT), json.dumps(result))
        self.assertNotIn("unverified-override", json.dumps(result))
        self.assertIn("effective_schemas/application-decision-record.schema.json",
                      result["source_files_sha256"])
        canonical = json.dumps(result["source_files_sha256"], sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                         result["source_snapshot_sha256"])

    def test_source_schema_resource_and_driver_edits_change_digest_without_a_commit(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            root = Path(temp)
            package = root / "package"
            schema_dir = root / "schemas"
            (package / "schemas/json").mkdir(parents=True)
            schema_dir.mkdir()
            (package / "__init__.py").write_text("# sample package\n", encoding="utf-8")
            (package / "schemas/json/example.json").write_text("{}", encoding="utf-8")
            override = schema_dir / "example.json"
            override.write_text('{"type": "object"}', encoding="utf-8")
            driver = root / "driver.py"
            driver.write_text("# sample driver\n", encoding="utf-8")
            with patch.object(source_provenance, "__file__", str(package / "source_provenance.py")), \
                 patch.object(source_provenance.validators, "SCHEMA_DIR", schema_dir):
                original = capture_source_provenance(driver)
                # These unpacked files are not tracked in the surrounding repository.
                self.assertEqual("unavailable", original["source_revision"])
                self.assertEqual("unavailable", original["source_tree_state"])
                self.assertEqual(original, capture_source_provenance(driver))
                for path in (package / "__init__.py", package / "schemas/json/example.json", override, driver):
                    with self.subTest(file=path.name):
                        before = path.read_bytes()
                        path.write_bytes(before + b" ")
                        changed = capture_source_provenance(driver)
                        self.assertNotEqual(original["source_snapshot_sha256"], changed["source_snapshot_sha256"])
                        with self.assertRaisesRegex(ValueError, "Source files changed"):
                            check_source_unchanged(original, driver)
                        path.write_bytes(before)
                        self.assertEqual(original, capture_source_provenance(driver))
                (package / "new_control.py").write_text("# new code\n", encoding="utf-8")
                self.assertNotEqual(original["source_snapshot_sha256"],
                                    capture_source_provenance(driver)["source_snapshot_sha256"])

    def test_unavailable_git_still_identifies_source_without_claiming_a_clean_revision(self):
        with patch.object(source_provenance.subprocess, "run", side_effect=FileNotFoundError):
            result = capture_source_provenance()
        self.assertEqual("unavailable", result["source_revision"])
        self.assertEqual("unavailable", result["source_tree_state"])
        self.assertEqual(64, len(result["source_snapshot_sha256"]))
        self.assertTrue(result["source_files_sha256"])
        self.assertEqual("package_code_resources_effective_schemas", result["source_snapshot_scope"])
        self.assertFalse(any(name.startswith("entrypoint/") for name in result["source_files_sha256"]))

    def test_missing_driver_cannot_produce_partial_source_identity(self):
        with self.assertRaisesRegex(ValueError, "readable regular files"):
            capture_source_provenance(ROOT / "tmp/nonexistent-driver.py")

    def test_override_only_schema_is_fingerprinted_and_changes_are_detected(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            package = Path(temp) / "package"
            schemas = Path(temp) / "schemas"
            package.mkdir()
            schemas.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            schema = schemas / "override-only.schema.json"
            schema.write_text('{"type":"object"}', encoding="utf-8")
            with patch.object(source_provenance, "__file__", str(package / "source_provenance.py")), \
                 patch.object(source_provenance.validators, "SCHEMA_DIR", schemas):
                before = capture_source_provenance()
                self.assertIn("effective_schemas/" + schema.name, before["source_files_sha256"])
                schema.write_text('{"type":"array"}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Source files changed"):
                    check_source_unchanged(before)

    def test_git_environment_cannot_redirect_observed_code_revision(self):
        expected = capture_source_provenance()
        with patch.dict(os.environ, {"GIT_DIR": str(ROOT / "tmp/not-a-git-dir"),
                                     "GIT_WORK_TREE": str(ROOT / "tmp")}):
            result = capture_source_provenance()
        self.assertEqual(expected["source_revision"], result["source_revision"])
        self.assertEqual(expected["source_tree_state"], result["source_tree_state"])

    def test_unchanged_aggregate_does_not_hide_wrong_file_hashes_or_revision(self):
        for field, wrong in (("source_files_sha256", {}), ("source_revision", "wrong-revision"),
                             ("source_snapshot_scope", "wrong-scope")):
            with self.subTest(field=field):
                provenance = capture_source_provenance()
                provenance[field] = wrong
                with self.assertRaisesRegex(ValueError, "Source files changed"):
                    check_source_unchanged(provenance)

    def test_source_changes_during_validation_cannot_become_the_initial_snapshot(self):
        original = capture_source_provenance()
        changed = {**original, "source_snapshot_sha256": "changed-during-validation"}
        current = original
        validate = monitoring.validate_dataset

        def change_after_validation(dataset):
            nonlocal current
            result = validate(dataset)
            current = changed
            return result

        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            with patch.object(monitoring, "capture_source_provenance", side_effect=lambda _: current), \
                 patch.object(source_provenance, "capture_source_provenance", side_effect=lambda _: current), \
                 patch.object(monitoring, "validate_dataset", side_effect=change_after_validation):
                with self.assertRaisesRegex(ValueError, "Source files changed"):
                    run_monthly_monitoring(ROOT / "data/synthetic/monthly-demo", Path(temp))
            self.assertEqual([], list(Path(temp).iterdir()))

    def test_monitoring_does_not_install_pack_after_detected_source_change(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            with patch.object(source_provenance, "capture_source_provenance",
                              return_value={"source_snapshot_sha256": "changed"}):
                with self.assertRaisesRegex(ValueError, "Source files changed"):
                    run_monthly_monitoring(ROOT / "data/synthetic/monthly-demo", Path(temp))
            self.assertEqual([], list(Path(temp).iterdir()))


if __name__ == "__main__":
    unittest.main()
