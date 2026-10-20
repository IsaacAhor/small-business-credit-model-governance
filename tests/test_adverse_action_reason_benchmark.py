from __future__ import annotations

import json
import shutil
import sys
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch
from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.run_adverse_action_reason_benchmark import (  # noqa: E402
    EXPECTED_EXCEPTION_TYPES,
    install_benchmark_pack,
    run_benchmark,
)
from credit_gov.monitoring import verify_evidence_pack  # noqa: E402
from credit_gov.source_provenance import capture_source_provenance  # noqa: E402
from scripts import run_adverse_action_reason_benchmark as benchmark  # noqa: E402

DATASET = ROOT / "data" / "synthetic" / "adverse-action-reason-benchmark"
EXAMPLE_PACK = ROOT / "examples" / "evidence-packs" / "adverse-action-reason-benchmark"
TEST_OUTPUT = ROOT / "evidence" / "_test_adverse_action_reason_benchmark_pack"
DYNAMIC_EVIDENCE_FILES = {
    "execution_provenance.json",
    "manifest.json",
    "output_fingerprints.json",
}


class AdverseActionReasonBenchmarkTests(unittest.TestCase):
    def assertNotAuthorized(self, payload):
        self.assertEqual("not_provided", payload["operational_authorization_status"])
        self.assertIs(payload["authorized_for_operational_use"], False)
        self.assertIs(payload["eligible_for_final_use"], False)
        self.assertEqual("not_assessed", payload["final_use_status"])

    def test_curated_results_cover_expected_seeded_failures(self) -> None:
        results = json.loads(
            (EXAMPLE_PACK / "adverse_action_reason_benchmark_results.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            "data/synthetic/adverse-action-reason-benchmark",
            results["dataset"],
        )
        self.assertTrue(results["acceptance"]["expected_seeded_failures_observed"])
        self.assertNotAuthorized(results)
        self.assertEqual("synthetic_seeded_failure_detection", results["purpose"])
        self.assertEqual([], results["missing_expected_exception_types"])
        self.assertEqual(EXPECTED_EXCEPTION_TYPES, set(results["observed_exception_types"]))
        self.assertIn("not_legal_conclusion", results["label"])
        fidelity = results["monitoring_reason_qa"]["source_to_notice_fidelity"]
        self.assertEqual("ran_synthetic_source_to_rendered_notice_controls", fidelity["status"])
        self.assertIn("notice_text_mapping_mismatch", fidelity["exception_types"])
        self.assertIn("reason_not_in_actual_contributors", fidelity["exception_types"])
        self.assertIn("decision_component_mismatch", fidelity["exception_types"])
        self.assertIn("rendered_notice_text_mismatch", fidelity["exception_types"])
        self.assertEqual(
            "ran_synthetic_rendered_notice_controls",
            fidelity["rendered_notice_fidelity"]["status"],
        )

    def test_runner_regenerates_benchmark_pack(self) -> None:
        result = run_benchmark(
            dataset_dir=DATASET,
            output_dir=TEST_OUTPUT,
            overwrite=True,
        )

        self.assertTrue(result.ok, result.errors)
        self.assertNotAuthorized(result.to_dict())
        self.assertNotAuthorized(result.benchmark_results)
        self.assertNotAuthorized(result.benchmark_results["generation_summary"])
        self.assertGreater(result.benchmark_results["monitoring_reason_qa"]["exception_count"], 0)
        self.assertTrue((TEST_OUTPUT / "adverse_action_reason_benchmark_results.json").is_file())
        self.assertTrue((TEST_OUTPUT / "adverse_action_reason_benchmark_report.md").is_file())
        manifest = json.loads((TEST_OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(
            "adverse_action_reason_benchmark_results.json",
            manifest["output_files"],
        )
        self.assertIn(
            "adverse_action_reason_benchmark_report.md",
            manifest["output_files"],
        )
        self.assertIn("rendered_notice_qa_results.json", manifest["output_files"])
        for name in ("manifest.json", "reason_qa_results.json", "rendered_notice_qa_results.json"):
            self.assertNotAuthorized(json.loads((TEST_OUTPUT / name).read_text(encoding="utf-8")))
        for name in ("README.md", "adverse_action_reason_benchmark_report.md",
                     "monitoring_report.md", "reviewer_signoff.md"):
            self.assertIn("Operational authorization is not provided.",
                          (TEST_OUTPUT / name).read_text(encoding="utf-8"))
        self.assertTrue(verify_evidence_pack(TEST_OUTPUT)["ok"])
        provenance = json.loads((TEST_OUTPUT / "execution_provenance.json").read_text(encoding="utf-8"))
        current_source = capture_source_provenance(ROOT / "scripts/run_adverse_action_reason_benchmark.py")
        for field in ("source_snapshot_sha256", "source_files_sha256", "source_revision", "source_tree_state"):
            self.assertEqual(current_source[field], provenance[field])
        self.assertIn("entrypoint/run_adverse_action_reason_benchmark.py", provenance["source_files_sha256"])
        curated_provenance = json.loads((EXAMPLE_PACK / "execution_provenance.json").read_text(encoding="utf-8"))
        self.assertIn("source_snapshot_sha256", curated_provenance)
        self.assertIn("source_tree_state", curated_provenance)
        curated_files = sorted(path.name for path in EXAMPLE_PACK.iterdir() if path.is_file())
        regenerated_files = sorted(path.name for path in TEST_OUTPUT.iterdir() if path.is_file())
        self.assertEqual(curated_files, regenerated_files)
        self.assertTrue(verify_evidence_pack(EXAMPLE_PACK)["ok"])
        for filename in curated_files:
            if filename in DYNAMIC_EVIDENCE_FILES:
                continue
            self.assertEqual(
                (EXAMPLE_PACK / filename).read_bytes(),
                (TEST_OUTPUT / filename).read_bytes(),
                f"Curated evidence-pack artifact is stale: {filename}",
            )

    def test_late_source_failure_does_not_install_or_replace_benchmark_pack(self) -> None:
        for existing in (False, True):
            with self.subTest(existing=existing), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                output = Path(temp) / "pack"
                if existing:
                    output.mkdir()
                    (output / "previous.txt").write_bytes(b"previous completed output")
                with patch("scripts.run_adverse_action_reason_benchmark.check_source_unchanged",
                           side_effect=ValueError("Source files changed during this run")):
                    with self.assertRaisesRegex(ValueError, "Source files changed"):
                        run_benchmark(DATASET, output, overwrite=existing)
                if existing:
                    self.assertEqual(["previous.txt"], [p.name for p in output.iterdir()])
                    self.assertEqual(b"previous completed output", (output / "previous.txt").read_bytes())
                else:
                    self.assertFalse(output.exists())
                self.assertEqual([output] if existing else [], list(Path(temp).iterdir()))

    def test_install_failure_restores_previous_pack_and_cleans_staging(self) -> None:
        rename = Path.rename
        for existing in (False, True):
            with self.subTest(existing=existing), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                output = Path(temp) / "pack"
                if existing:
                    output.mkdir()
                    (output / "notes.txt").write_bytes(b"previous pack and reviewer notes")

                def fail_install(path, target):
                    if Path(target) == output and path.parent.name.startswith(".benchmark-"):
                        raise PermissionError("simulated installation failure")
                    return rename(path, target)

                with patch.object(Path, "rename", fail_install):
                    with self.assertRaisesRegex(PermissionError, "installation failure"):
                        run_benchmark(DATASET, output, overwrite=existing)
                self.assertEqual([output] if existing else [], list(Path(temp).iterdir()))
                if existing:
                    self.assertEqual(["notes.txt"], [p.name for p in output.iterdir()])
                    self.assertEqual(b"previous pack and reviewer notes", (output / "notes.txt").read_bytes())

    def test_failed_restoration_retains_recoverable_backup_outside_staging(self) -> None:
        rename = Path.rename
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            output.mkdir()
            (output / "notes.txt").write_bytes(b"irreplaceable prior notes")

            def fail_install_and_restore(path, target):
                if Path(target) == output:
                    raise PermissionError("simulated destination unavailable")
                return rename(path, target)

            with patch.object(Path, "rename", fail_install_and_restore):
                with self.assertRaisesRegex(RuntimeError, "previous pack retained at") as raised:
                    run_benchmark(DATASET, output, overwrite=True)
            backups = list(Path(temp).glob(".pack.backup-*"))
            self.assertEqual(1, len(backups))
            self.assertIn(str(backups[0]), str(raised.exception))
            self.assertEqual(b"irreplaceable prior notes", (backups[0] / "notes.txt").read_bytes())
            self.assertEqual(backups, list(Path(temp).iterdir()))

    def test_backup_failure_leaves_existing_pack_untouched(self) -> None:
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            staged = Path(temp) / "staged"
            output.mkdir()
            staged.mkdir()
            (output / "notes.txt").write_bytes(b"prior")
            with patch.object(Path, "rename", side_effect=PermissionError("cannot move old pack")):
                with self.assertRaisesRegex(PermissionError, "cannot move old pack"):
                    install_benchmark_pack(staged, output, overwrite=True)
            self.assertEqual(b"prior", (output / "notes.txt").read_bytes())
            self.assertEqual({output, staged}, set(Path(temp).iterdir()))

    def test_successful_replacement_removes_backup_only_after_installation(self) -> None:
        rename = Path.rename
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output, staged = Path(temp) / "pack", Path(temp) / "staged"
            output.mkdir()
            staged.mkdir()
            (output / "notes.txt").write_bytes(b"prior")
            (staged / "result.txt").write_bytes(b"new")

            def inspect_install(path, target):
                if path == staged:
                    backups = list(Path(temp).glob(".pack.backup-*"))
                    self.assertEqual(1, len(backups))
                    self.assertEqual(b"prior", (backups[0] / "notes.txt").read_bytes())
                return rename(path, target)

            with patch.object(Path, "rename", inspect_install):
                install_benchmark_pack(staged, output, overwrite=True)
            self.assertEqual([output], list(Path(temp).iterdir()))
            self.assertEqual(b"new", (output / "result.txt").read_bytes())

    def test_occupied_recovery_destination_is_not_overwritten(self) -> None:
        rename = Path.rename
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output, staged = Path(temp) / "pack", Path(temp) / "staged"
            output.mkdir()
            staged.mkdir()
            (output / "notes.txt").write_bytes(b"prior")

            def competing_destination(path, target):
                if path == staged:
                    output.mkdir()
                    (output / "other.txt").write_bytes(b"other writer")
                    raise PermissionError("destination occupied")
                return rename(path, target)

            with patch.object(Path, "rename", competing_destination):
                with self.assertRaisesRegex(RuntimeError, "previous pack retained at"):
                    install_benchmark_pack(staged, output, overwrite=True)
            self.assertEqual(b"other writer", (output / "other.txt").read_bytes())
            backups = list(Path(temp).glob(".pack.backup-*"))
            self.assertEqual(1, len(backups))
            self.assertEqual(b"prior", (backups[0] / "notes.txt").read_bytes())

    def test_cleanup_failure_reports_installed_pack_and_retained_backup(self) -> None:
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output, staged = Path(temp) / "pack", Path(temp) / "staged"
            output.mkdir()
            staged.mkdir()
            (output / "notes.txt").write_bytes(b"prior")
            (staged / "result.txt").write_bytes(b"new")
            with patch("scripts.run_adverse_action_reason_benchmark.shutil.rmtree",
                       side_effect=PermissionError("backup locked")):
                with self.assertLogs(benchmark.__name__, level="WARNING") as captured:
                    install_benchmark_pack(staged, output, overwrite=True)
                self.assertIn("New benchmark pack installed", captured.output[0])
            self.assertEqual(b"new", (output / "result.txt").read_bytes())
            backup = next(Path(temp).glob(".pack.backup-*"))
            self.assertEqual(b"prior", (backup / "notes.txt").read_bytes())

    def test_failed_acceptance_does_not_install_or_replace_pack(self) -> None:
        build = benchmark.build_benchmark_results
        for existing in (False, True):
            with self.subTest(existing=existing), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                output = Path(temp) / "pack"
                if existing:
                    output.mkdir()
                    (output / "notes.txt").write_bytes(b"prior")

                def missing_expected_failure(**kwargs):
                    results = build(**kwargs)
                    results["acceptance"]["expected_seeded_failures_observed"] = False
                    return results

                with patch.object(benchmark, "build_benchmark_results", side_effect=missing_expected_failure):
                    result = run_benchmark(DATASET, output, overwrite=existing)
                self.assertFalse(result.ok)
                self.assertIsNone(result.output_dir)
                self.assertIn("destination unchanged", result.errors[0])
                self.assertNotAuthorized(result.to_dict())
                self.assertEqual([output] if existing else [], list(Path(temp).iterdir()))
                if existing:
                    self.assertEqual(b"prior", (output / "notes.txt").read_bytes())

    def test_changed_monitoring_pack_cannot_be_rehashed_into_successful_replacement(self) -> None:
        run_monitoring = benchmark.run_monthly_monitoring
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            output.mkdir()
            (output / "notes.txt").write_bytes(b"prior completed pack")

            def change_output(**kwargs):
                result = run_monitoring(**kwargs)
                (Path(result.output_dir) / "metric_results.json").write_bytes(b'{"approval_rate":999}')
                return result

            with patch.object(benchmark, "run_monthly_monitoring", side_effect=change_output):
                with self.assertRaisesRegex(ValueError, "integrity"):
                    run_benchmark(DATASET, output, overwrite=True)
            self.assertEqual([output], list(Path(temp).iterdir()))
            self.assertEqual(b"prior completed pack", (output / "notes.txt").read_bytes())

    def test_changed_staged_pack_cannot_replace_previous_pack(self) -> None:
        check_source = benchmark.check_source_unchanged
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            output.mkdir()
            (output / "notes.txt").write_bytes(b"prior completed pack")

            def change_staged_output(*args):
                check_source(*args)
                staged = next(Path(temp).glob(".benchmark-*/pack"))
                (staged / "metric_results.json").write_bytes(b'{"approval_rate":999}')

            with patch.object(benchmark, "check_source_unchanged", side_effect=change_staged_output):
                with self.assertRaisesRegex(ValueError, "integrity"):
                    run_benchmark(DATASET, output, overwrite=True)
            self.assertEqual([output], list(Path(temp).iterdir()))
            self.assertEqual(b"prior completed pack", (output / "notes.txt").read_bytes())

    def test_staging_cleanup_failure_does_not_report_installed_pack_as_failed(self) -> None:
        remove = shutil.rmtree
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            output.mkdir()
            (output / "notes.txt").write_bytes(b"prior completed pack")

            def fail_staging_cleanup(path, *args, **kwargs):
                path = Path(path)
                if path.parent == Path(temp) and path.name.startswith(".benchmark-"):
                    raise PermissionError("staging cleanup failed")
                return remove(path, *args, **kwargs)

            with patch.object(benchmark.shutil, "rmtree", side_effect=fail_staging_cleanup):
                with self.assertLogs(benchmark.__name__, level="WARNING") as captured:
                    result = run_benchmark(DATASET, output, overwrite=True)
            self.assertTrue(result.ok, result.errors)
            self.assertIn("staging cleanup incomplete", captured.output[0])
            self.assertTrue(verify_evidence_pack(output)["ok"])

    def test_output_cannot_replace_dataset_or_its_parent(self) -> None:
        for relative in ("dataset", "."):
            with self.subTest(output=relative), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                dataset = Path(temp) / "dataset"
                shutil.copytree(DATASET, dataset)
                before = {p.name: p.read_bytes() for p in dataset.iterdir() if p.is_file()}
                output = Path(temp) / relative
                self.assertTrue(output.resolve().is_relative_to(Path(temp).resolve()))
                result = run_benchmark(dataset, output, overwrite=True)
                self.assertFalse(result.ok)
                self.assertIn("input", result.errors[0].lower())
                self.assertEqual(before, {p.name: p.read_bytes() for p in dataset.iterdir() if p.is_file()})

    def test_output_cannot_replace_source_folders_or_descendants(self) -> None:
        for output in (ROOT, ROOT / "src", ROOT / "src/credit_gov", ROOT / "schemas", ROOT / "scripts"):
            with self.subTest(output=output), patch.object(
                benchmark, "run_monthly_monitoring",
                side_effect=AssertionError("Unsafe output must be rejected before running"),
            ) as run:
                result = run_benchmark(DATASET, output, overwrite=True)
                self.assertFalse(result.ok)
                self.assertIn("source", result.errors[0])
                run.assert_not_called()

    def test_cleanup_failure_cannot_mask_rollback_error_or_erase_recovery_backup(self) -> None:
        rename, remove = Path.rename, shutil.rmtree
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            output = Path(temp) / "pack"
            output.mkdir()
            (output / "notes.txt").write_bytes(b"prior completed pack")

            def fail_install_and_restore(path, target):
                if Path(target) == output:
                    raise PermissionError("destination unavailable")
                return rename(path, target)

            def fail_staging_cleanup(path, *args, **kwargs):
                path = Path(path)
                if path.parent == Path(temp) and path.name.startswith(".benchmark-"):
                    raise PermissionError("staging cleanup failed too")
                return remove(path, *args, **kwargs)

            with patch.object(Path, "rename", fail_install_and_restore), \
                 patch.object(benchmark.shutil, "rmtree", side_effect=fail_staging_cleanup), \
                 warnings.catch_warnings(), self.assertLogs(benchmark.__name__, level="WARNING"):
                warnings.simplefilter("error")
                with self.assertRaisesRegex(RuntimeError, "previous pack retained at") as raised:
                    run_benchmark(DATASET, output, overwrite=True)
            backups = list(Path(temp).glob(".pack.backup-*"))
            self.assertEqual(1, len(backups))
            self.assertIn(str(backups[0]), str(raised.exception))
            self.assertEqual(b"prior completed pack", (backups[0] / "notes.txt").read_bytes())


if __name__ == "__main__":
    unittest.main()
