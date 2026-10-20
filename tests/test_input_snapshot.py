from __future__ import annotations

import hashlib
import json
import shutil
import sys
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_gov import monitoring  # noqa: E402
from credit_gov.input_snapshot import DatasetSnapshot  # noqa: E402
from scripts import run_adverse_action_reason_benchmark as benchmark  # noqa: E402


class InputSnapshotTests(unittest.TestCase):
    def read_pack(self, result, name):
        return json.loads((Path(result.output_dir) / name).read_text(encoding="utf-8"))

    def assertInputHashes(self, result, captured, references=None):
        provenance = self.read_pack(result, "execution_provenance.json")
        expected = {f"dataset/{name}": hashlib.sha256(raw).hexdigest()
                    for name, raw in captured.items()}
        expected.update({f"reference/bisg/{role}": hashlib.sha256(raw).hexdigest()
                         for role, raw in (references or {}).items()})
        self.assertEqual(expected, provenance["input_files_sha256"])
        canonical = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), provenance["input_snapshot_sha256"])
        self.assertEqual(
            {name: hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()
             for name, raw in captured.items()},
            self.read_pack(result, "input_fingerprints.json"),
        )
        self.assertTrue(monitoring.verify_evidence_pack(Path(result.output_dir))["ok"])
        self.assertIs(result.to_dict()["authorized_for_operational_use"], False)

    def test_validation_computation_and_hashes_use_captured_bytes_despite_live_changes(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(ROOT / "data/synthetic/monthly-demo", dataset)
            threshold = dataset / "threshold-set.json"
            threshold.write_bytes(threshold.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            captured = {p.name: p.read_bytes() for p in dataset.glob("*.json")}
            validate = monitoring.validate_dataset

            def mutate_after_validation(inputs):
                result = validate(inputs)
                self.assertTrue(result.ok, result.errors)
                threshold.write_bytes(b"invalid replacement")
                (dataset / "application-decision-records.json").unlink()
                (dataset / "prior-model-version-record.json").write_bytes(b"invalid new optional input")
                return result

            with patch.object(monitoring, "validate_dataset", side_effect=mutate_after_validation):
                result = monitoring.run_monthly_monitoring(dataset, Path(temp) / "output")
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(0.5, result.metrics["approval_rate"])
            self.assertEqual(json.loads(captured["breach-records.json"]), result.breaches)
            self.assertEqual(json.loads(captured["threshold-set.json"])["thresholds"],
                             self.read_pack(result, "config_snapshot.json")["thresholds"])
            self.assertIsNone(result.change_validation)
            self.assertInputHashes(result, captured)
            self.assertNotEqual(
                self.read_pack(result, "input_fingerprints.json")["threshold-set.json"],
                self.read_pack(result, "execution_provenance.json")["input_files_sha256"]["dataset/threshold-set.json"],
            )

    def test_optional_analyses_and_all_reference_sources_use_fingerprinted_bytes(self):
        for reference_source in ("external", "dataset", "packaged"):
            with self.subTest(source=reference_source), LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
                dataset = Path(temp) / "dataset"
                shutil.copytree(ROOT / "data/synthetic/monthly-portfolio", dataset)
                config = json.loads((dataset / "bisg-config.json").read_text(encoding="utf-8"))
                references, reference_paths = {}, []
                for field in ("surname_reference_path", "geography_reference_path", "national_marginals_path"):
                    name = Path(config[field]).name
                    raw = files("credit_gov.reference.bisg").joinpath(name).read_bytes()
                    references[field] = raw
                    if reference_source == "packaged":
                        config[field] = "missing-reference-directory/" + name
                    else:
                        path = (dataset if reference_source == "dataset" else Path(temp)) / name
                        path.write_bytes(raw)
                        reference_paths.append(path)
                        config[field] = name if reference_source == "dataset" else str(path)
                (dataset / "bisg-config.json").write_text(json.dumps(config), encoding="utf-8")
                captured = {p.name: p.read_bytes() for p in dataset.glob("*.json")}
                baseline = monitoring.run_monthly_monitoring(dataset, Path(temp) / "baseline")
                self.assertTrue(baseline.ok, baseline.errors)
                validate = monitoring.validate_dataset
                analyze = monitoring.run_bisg_proxy_analysis

                def mutate_dataset(inputs):
                    result = validate(inputs)
                    for path in dataset.glob("*.json"):
                        path.write_bytes(b"invalid changed input")
                    return result

                def mutate_references(**kwargs):
                    for path in reference_paths:
                        path.write_bytes(b"invalid changed reference")
                    return analyze(**kwargs)

                with patch.object(monitoring, "validate_dataset", side_effect=mutate_dataset), \
                     patch.object(monitoring, "run_bisg_proxy_analysis", side_effect=mutate_references):
                    result = monitoring.run_monthly_monitoring(dataset, Path(temp) / "output")
                self.assertTrue(result.ok, result.errors)
                for name in ("metrics", "lda", "bisg", "change_validation"):
                    self.assertEqual(getattr(baseline, name), getattr(result, name))
                self.assertInputHashes(result, captured, references)

    def test_benchmark_supplemental_checks_share_monitoring_snapshot(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(ROOT / "data/synthetic/adverse-action-reason-benchmark", dataset)
            captured = {p.name: p.read_bytes() for p in dataset.glob("*.json")}
            expected = json.loads((ROOT / "examples/evidence-packs/adverse-action-reason-benchmark"
                                   / "adverse_action_reason_benchmark_results.json").read_text(encoding="utf-8"))
            run_monitoring = benchmark.run_monthly_monitoring

            def mutate_after_monitoring(**kwargs):
                result = run_monitoring(**kwargs)
                for path in dataset.glob("*.json"):
                    path.write_bytes(b"invalid changed benchmark input")
                return result

            with patch.object(benchmark, "run_monthly_monitoring", side_effect=mutate_after_monitoring):
                result = benchmark.run_benchmark(dataset, Path(temp) / "pack")
            self.assertTrue(result.ok, result.errors)
            expected["dataset"] = dataset.relative_to(ROOT).as_posix()
            self.assertEqual(expected, result.benchmark_results)
            self.assertInputHashes(result, captured)

    def test_snapshot_for_another_dataset_is_rejected(self):
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            with self.assertRaisesRegex(ValueError, "different dataset"):
                monitoring.run_monthly_monitoring(
                    ROOT / "data/synthetic/monthly-demo", Path(temp),
                    input_snapshot=DatasetSnapshot(ROOT / "data/synthetic/monthly-demo-no-breach"),
                )
            self.assertEqual([], list(Path(temp).iterdir()))

    def test_changes_during_capture_are_bound_to_each_actual_read(self):
        read_bytes = Path.read_bytes
        with LocalTemporaryDirectory(ROOT / "tmp/test-runs") as temp:
            dataset = Path(temp) / "dataset"
            shutil.copytree(ROOT / "data/synthetic/monthly-demo", dataset)
            threshold = dataset / "threshold-set.json"
            replacement = json.loads(threshold.read_text(encoding="utf-8"))
            replacement["thresholds"][0]["threshold_value"] = 0.95
            reads = {}

            def read_then_edit(path):
                raw = read_bytes(path)
                if path.parent == dataset and path.suffix == ".json":
                    self.assertNotIn(path.name, reads, "Dataset input was reread from disk")
                    reads[path.name] = raw
                    if path.name == "model-version-record.json":
                        self.assertIn("application-decision-records.json", reads)
                        self.assertNotIn("threshold-set.json", reads)
                        (dataset / "application-decision-records.json").write_bytes(b"changed after capture")
                        threshold.write_bytes(json.dumps(replacement).encode("utf-8"))
                return raw

            with patch.object(Path, "read_bytes", read_then_edit):
                result = monitoring.run_monthly_monitoring(dataset, Path(temp) / "output")
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(0.5, result.metrics["approval_rate"])
            self.assertEqual(replacement["thresholds"], self.read_pack(result, "config_snapshot.json")["thresholds"])
            self.assertTrue(any(breach["metric_name"] == "approval_rate" for breach in result.breaches))
            self.assertInputHashes(result, reads)
            self.assertIn("not an atomic", self.read_pack(result, "execution_provenance.json")["input_snapshot_scope"])


if __name__ == "__main__":
    unittest.main()
