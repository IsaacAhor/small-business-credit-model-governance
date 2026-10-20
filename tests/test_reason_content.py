"""Challenge the reason-content boundary without granting operational permission."""
from __future__ import annotations

import copy
import io
import json
import shutil
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tests.temp_utils import LocalTemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_gov.commands import main
from credit_gov.reason_content import (
    GATE_VERSION, LEGACY_REVIEW_FILE, REQUIRED_REVIEWS, assess_reason_content,
    export_reviewed_reasons,
)
from credit_gov.generation import generate_adverse_action_reasons
from credit_gov.monitoring import compute_reason_qa, load_dataset_payloads, run_monthly_monitoring
from credit_gov.reason_fidelity import build_reason_fidelity_context

SOURCE = ROOT / "data/synthetic/adverse-action-reason-benchmark"
NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


class ReasonContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = LocalTemporaryDirectory(ROOT / "tmp/test-runs")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dataset = self.root / "dataset"
        shutil.copytree(SOURCE, self.dataset)
        self.clock = patch("credit_gov.reason_content.utc_now", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.output = self.root / "reviewed-reasons.json"
        # Keep the dataset relationships but use only one declined decision.
        decisions = self.read("application-decision-records.json")
        for decision in decisions:
            if decision["decision_id"] != "dec-0002":
                decision["decision_outcome"] = "approved"
        self.write("application-decision-records.json", decisions)
        self.write("review-evidence.json", {
            "scope": "Synthetic test evidence only, not an institutional review.",
            "selection": "The two recorded scoring drivers are principal in this fixture.",
            "wording": "The two mapped phrases match the recorded decision factors.",
            "procedure": "Test-only business-credit procedure and timing assessment.",
            "lifecycle": "Decision-date synthetic convention explicitly assessed.",
        })
        self.regenerate()

    def read(self, name):
        return json.loads((self.dataset / name).read_text(encoding="utf-8"))

    def write(self, name, value):
        (self.dataset / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def mutate(self, name, callback):
        value = self.read(name)
        callback(value)
        self.write(name, value)

    def regenerate(self, max_reasons=4):
        payloads = load_dataset_payloads(self.dataset)
        context = build_reason_fidelity_context(
            payloads["reason_fidelity_policy"], payloads["notice_template"],
            payloads["reason_selection_methods"],
        )
        outputs = generate_adverse_action_reasons(
            payloads["decisions"], payloads["driver_contributions"], payloads["reason_mappings"],
            payloads["model_version"]["version_id"], fidelity_context=context, max_reasons=max_reasons,
        )
        self.write("adverse-action-reason-outputs.json", outputs)
        template = payloads["notice_template"]
        notices = [{
            "record_type": "rendered_adverse_action_notice",
            "notice_id": "aan-test-" + decision_id,
            "decision_id": decision_id,
            "notice_template_id": template["template_id"],
            "notice_template_version": template["template_version"],
            "rendered_reason_segments": [{
                "reason_output_id": output["reason_output_id"],
                "reason_code": output["reason_code"],
                "rendered_reason_text": output["disclosed_reason_text"],
            } for output in outputs if output["decision_id"] == decision_id],
        } for decision_id in sorted({output["decision_id"] for output in outputs})]
        self.write("rendered-adverse-action-notices.json", notices)
        return outputs

    def review(self):
        assessment = assess_reason_content(self.dataset)
        record = {
            "gate_version": GATE_VERSION,
            "snapshot_sha256": assessment["snapshot_sha256"],
            "reviewed_by": "synthetic-reviewer",
            "reviewed_at": "2026-10-20T11:00:00Z",
            "valid_until": "2026-10-21T00:00:00Z",
            "known_defects_complete": True,
            "material_defects": [],
            "decision_reviews": [{
                "decision_id": item["decision_id"],
                "checks": {name: {
                    "status": "satisfied",
                    "rationale": "Synthetic fixture reviewed for this declared check.",
                    "evidence_files": ["review-evidence.json"],
                } for name in REQUIRED_REVIEWS},
            } for item in self.read("application-decision-records.json") if item["decision_outcome"] == "declined"],
        }
        self.write("reason-content-review.json", record)
        return record

    def assertNotAuthorized(self, result):
        self.assertIs(result["eligible_for_final_use"], False, result)
        self.assertIs(result["authorized_for_operational_use"], False, result)
        self.assertEqual("not_provided", result["operational_authorization_status"])
        self.assertNotIn(result.get("status"), ("eligible", "ready", "authorized"))

    def assertBlocked(self, code=None):
        assessment = assess_reason_content(self.dataset)
        self.assertFalse(assessment["reason_content_checks_passed"], assessment)
        self.assertNotAuthorized(assessment)
        self.assertEqual("blocked", assessment["status"])
        if code:
            self.assertIn(code, {item["code"] for item in assessment["blockers"]}, assessment)
        result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["ok"], result)
        self.assertFalse(result["exported"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertNotAuthorized(result)
        self.assertNotAuthorized(result["assessment"])
        self.assertFalse(self.output.exists())
        return assessment

    def test_clean_automated_result_still_requires_review(self):
        result = self.assertBlocked("review_not_satisfied")
        self.assertEqual([], result["reason_qa"]["exceptions"])

    def test_clean_reviewed_snapshot_can_export_exact_reason_content(self):
        self.review()
        assessment = assess_reason_content(self.dataset)
        self.assertTrue(assessment["reason_content_checks_passed"])
        self.assertEqual("reason_content_checks_passed", assessment["status"])
        self.assertEqual([], assessment["blockers"])
        self.assertNotAuthorized(assessment)
        result = export_reviewed_reasons(self.dataset, self.output)
        self.assertTrue(result["ok"], result)
        self.assertNotAuthorized(result)
        self.assertNotAuthorized(result["assessment"])
        exported = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertTrue(exported["assessment"]["reason_content_checks_passed"])
        self.assertNotAuthorized(exported)
        self.assertNotAuthorized(exported["assessment"])
        self.assertNotIn("eligibility", exported)
        self.assertEqual("reviewed_reason_content_snapshot", exported["artifact_type"])
        self.assertIn("not_full_notice", exported["scope"])
        self.assertEqual(self.read("adverse-action-reason-outputs.json"), exported["reason_outputs"])
        self.assertEqual(self.read("rendered-adverse-action-notices.json"), exported["rendered_notices"])
        self.assertEqual(self.read("reason-content-review.json")["snapshot_sha256"],
                         exported["assessment"]["snapshot_sha256"])

    def test_both_generation_commands_feed_review_and_export_without_changing_reviews_or_notices(self):
        from scripts.generate_adverse_action_reasons import main as script_main
        from credit_gov.reason_fidelity import REQUIRED_REASON_FIDELITY_FIELDS
        for index, generate in enumerate((
            lambda: main(["generate-reasons", str(self.dataset)]),
            lambda: script_main([str(self.dataset)]),
        )):
            with self.subTest(entry=index):
                self.review()
                preserved = {name: (self.dataset / name).read_bytes() for name in (
                    "reason-content-review.json", "rendered-adverse-action-notices.json",
                )}
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, generate())
                for output in self.read("adverse-action-reason-outputs.json"):
                    self.assertTrue(set(REQUIRED_REASON_FIDELITY_FIELDS).issubset(output))
                for name, contents in preserved.items():
                    self.assertEqual(contents, (self.dataset / name).read_bytes())
                self.review()
                with redirect_stdout(io.StringIO()) as stream:
                    self.assertEqual(0, main(["assess-reason-content", str(self.dataset)]))
                self.assertNotAuthorized(json.loads(stream.getvalue()))
                target = self.root / f"command-export-{index}.json"
                with redirect_stdout(io.StringIO()) as stream:
                    self.assertEqual(0, main([
                        "export-reviewed-reasons", str(self.dataset), "--output", str(target),
                    ]))
                self.assertNotAuthorized(json.loads(stream.getvalue()))
                artifact = json.loads(target.read_text(encoding="utf-8"))
                self.assertTrue(artifact["assessment"]["reason_content_checks_passed"])
                self.assertNotAuthorized(artifact)

    def test_rich_command_generation_preserves_unmapped_principal_blocker(self):
        self.mutate("adverse-action-driver-contributions.json", lambda rows:
                    next(r for r in rows if r["decision_id"] == "dec-0002")["contributions"][0]
                    .update(driver_or_signal="unmapped_principal"))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["generate-reasons", str(self.dataset)]))
        self.review()
        # Generation leaves old notices untouched, so their stale reference blocks first.
        self.assertBlocked("invalid_dataset")
        self.regenerate()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["generate-reasons", str(self.dataset)]))
        self.review()
        self.assertBlocked("principal_driver_unmapped")

    def test_removed_operational_commands_cannot_assess_or_export_even_clean_content(self):
        self.review()
        for command in (
            ["assess-final-use", str(self.dataset)],
            ["export-final-reasons", str(self.dataset), "--output", str(self.output)],
        ):
            with self.subTest(command=command[0]), redirect_stderr(io.StringIO()) as errors, \
                 redirect_stdout(io.StringIO()) as output:
                self.assertEqual(2, main(command))
                self.assertIn("unknown command", errors.getvalue())
                self.assertEqual("", output.getvalue())
        self.assertFalse(self.output.exists())

    def test_old_review_cannot_be_ignored_or_relabelled_as_current(self):
        review = self.review()
        old = copy.deepcopy(review)
        old["gate_version"] = "reason-content-review-v3"
        old["material_defects"] = [{
            "defect_id": "unresolved-old-defect", "material": True, "status": "open",
            "rationale": "Unresolved defect from the earlier review.",
            "evidence_files": ["review-evidence.json"],
        }]
        for name in (LEGACY_REVIEW_FILE, LEGACY_REVIEW_FILE.upper()):
            for keep_current in (False, True):
                with self.subTest(name=name, keep_current=keep_current):
                    self.write(name, old)
                    if keep_current:
                        self.review()
                    else:
                        (self.dataset / "reason-content-review.json").unlink()
                    self.assertBlocked("legacy_review_file")
                    (self.dataset / name).unlink()
                    self.review()
        self.write("reason-content-review.json", old)
        self.assertBlocked("review_not_satisfied")
        migrated = self.review()
        migrated["material_defects"] = old["material_defects"]
        self.write("reason-content-review.json", migrated)
        self.assertBlocked("review_not_satisfied")

    def test_migration_updates_manifest_and_requires_fresh_binding_before_export(self):
        review = self.review()
        review["gate_version"] = "reason-content-review-v3"
        self.write(LEGACY_REVIEW_FILE, review)
        (self.dataset / "reason-content-review.json").unlink()
        self.mutate("evidence-pack-manifest.json",
                    lambda m: m["input_references"].append(LEGACY_REVIEW_FILE))
        self.assertBlocked("legacy_review_file")
        original = (self.dataset / LEGACY_REVIEW_FILE).read_bytes()
        preserved = self.root / "previous-review.json"
        (self.dataset / LEGACY_REVIEW_FILE).rename(preserved)
        self.assertEqual(original, preserved.read_bytes())
        self.assertBlocked("invalid_dataset")
        self.mutate("evidence-pack-manifest.json", lambda m: m.update(
            input_references=["reason-content-review.json" if ref == LEGACY_REVIEW_FILE else ref
                              for ref in m["input_references"]]))
        # Merely updating the filename and version cannot reuse an old binding.
        review["gate_version"] = GATE_VERSION
        self.write("reason-content-review.json", review)
        self.assertBlocked("review_not_satisfied")
        self.review()
        result = export_reviewed_reasons(self.dataset, self.output)
        self.assertTrue(result["ok"], result)
        self.assertNotAuthorized(result)
        self.assertEqual(original, preserved.read_bytes())

    def test_readiness_claims_in_reason_or_notice_records_cannot_survive_export(self):
        for name, location in (
            ("adverse-action-reason-outputs.json", lambda rows: rows[0]),
            ("rendered-adverse-action-notices.json", lambda rows: rows[0]),
            ("rendered-adverse-action-notices.json", lambda rows: rows[0]["rendered_reason_segments"][0]),
        ):
            for field, value in (
                ("eligible_for_final_use", True), ("authorized_for_operational_use", True),
                ("status", "ready"), ("approval", {"status": "approved"}),
            ):
                with self.subTest(name=name, field=field):
                    original = (self.dataset / name).read_bytes()
                    self.mutate(name, lambda rows: location(rows).update({field: value}))
                    self.review()
                    self.assertBlocked("invalid_dataset")
                    (self.dataset / name).write_bytes(original)

    def test_command_help_lists_only_supported_content_commands(self):
        with redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, main(["--help"]))
        self.assertIn("Command success does not provide operational authorization.", stream.getvalue())
        self.assertNotIn("assess-final-use", stream.getvalue())
        self.assertNotIn("export-final-reasons", stream.getvalue())
        self.assertIn("export-reviewed-reasons (checked review snapshot only)", stream.getvalue())

    def test_editable_reviewer_identity_never_establishes_operational_authority(self):
        self.review()
        self.mutate("reason-content-review.json", lambda r: r.update(reviewed_by="unverified-reviewer-claim"))
        result = export_reviewed_reasons(self.dataset, self.output)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["assessment"]["reason_content_checks_passed"])
        self.assertNotAuthorized(result)
        exported = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertNotAuthorized(exported)
        self.assertNotAuthorized(exported["assessment"])

    def test_claimed_authorization_fields_cannot_override_review_contract(self):
        for field, value in (
            ("authorized_for_operational_use", True),
            ("eligible_for_final_use", True),
            ("operational_authorization_status", "authorized"),
        ):
            with self.subTest(field=field):
                review = self.review()
                review[field] = value
                self.write("reason-content-review.json", review)
                self.assertBlocked("review_not_satisfied")

    def test_restoring_old_review_never_restores_operational_permission(self):
        self.review()
        previous = (self.dataset / "reason-content-review.json").read_bytes()
        self.mutate("reason-content-review.json", lambda r: r.update(known_defects_complete=False))
        self.assertBlocked("review_not_satisfied")
        (self.dataset / "reason-content-review.json").write_bytes(previous)
        result = export_reviewed_reasons(self.dataset, self.output)
        # Restored attestations can pass content checks; there is no revocation ledger.
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["assessment"]["reason_content_checks_passed"])
        self.assertNotAuthorized(result)
        exported = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertNotAuthorized(exported)
        self.assertNotAuthorized(exported["assessment"])

    def test_change_after_last_freshness_check_cannot_turn_snapshot_into_authorization(self):
        from credit_gov import reason_content
        self.review()
        reviewed_outputs = self.read("adverse-action-reason-outputs.json")
        install = reason_content._install_new_file

        def change_then_install(source, destination):
            self.mutate("adverse-action-reason-outputs.json",
                        lambda r: r[0].update(disclosed_reason_text="Concurrent replacement"))
            install(source, destination)

        with patch("credit_gov.reason_content._install_new_file", side_effect=change_then_install):
            result = export_reviewed_reasons(self.dataset, self.output)
        # No writer coordination is claimed: this remains the earlier checked snapshot.
        self.assertTrue(result["ok"], result)
        self.assertNotAuthorized(result)
        exported = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(reviewed_outputs, exported["reason_outputs"])
        self.assertNotEqual(self.read("adverse-action-reason-outputs.json"), exported["reason_outputs"])
        self.assertNotAuthorized(exported)
        self.assertNotAuthorized(exported["assessment"])
        self.assertFalse(assess_reason_content(self.dataset)["reason_content_checks_passed"])

    def test_unreadable_dataset_is_neither_content_pass_nor_authorization(self):
        missing = self.root / "missing"
        assessment = assess_reason_content(missing)
        self.assertFalse(assessment["reason_content_checks_passed"])
        self.assertNotAuthorized(assessment)
        result = export_reviewed_reasons(missing, self.output)
        self.assertFalse(result["ok"])
        self.assertFalse(result["exported"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertNotAuthorized(result)
        self.assertNotAuthorized(result["assessment"])
        self.assertFalse(self.output.exists())

    def test_unmapped_principal_blocks_even_with_lower_mapped_candidate_and_review(self):
        self.mutate("adverse-action-driver-contributions.json", lambda records:
                    next(r for r in records if r["decision_id"] == "dec-0002")["contributions"][0]
                    .update(driver_or_signal="unmapped_principal"))
        candidates = self.regenerate()
        self.assertEqual(1, len(candidates))
        self.review()
        self.assertBlocked("principal_driver_unmapped")

    def test_wholly_unmapped_principals_cannot_export_empty_reasons(self):
        def unmap(records):
            for index, item in enumerate(next(r for r in records if r["decision_id"] == "dec-0002")["contributions"]):
                item["driver_or_signal"] = f"unmapped_{index}"
        self.mutate("adverse-action-driver-contributions.json", unmap)
        self.assertEqual([], self.regenerate())
        self.review()
        # An empty rendered-notice set fails structural validation first.
        self.assertBlocked("invalid_dataset")

    def test_missing_principal_output_blocks(self):
        self.regenerate(max_reasons=1)
        self.review()
        self.assertBlocked("principal_driver_omitted")

    def test_lifecycle_cannot_be_waived_by_review(self):
        for name, code in (
            ("reason-code-mappings.json", "mapping_not_effective_on_decision_date"),
            ("adverse-action-notice-template.json", "notice_template_not_effective_on_decision_date"),
        ):
            original = self.read(name)
            for field, value in (("effective_date", "2026-07-03"), ("retired_date", "2026-07-02")):
                with self.subTest(name=name, field=field):
                    mutated = copy.deepcopy(original)
                    for record in mutated if isinstance(mutated, list) else [mutated]:
                        record[field] = value
                    self.write(name, mutated)
                    self.regenerate()
                    self.review()
                    self.assertBlocked(code)
            self.write(name, original)

    def test_rendered_text_defect_blocks(self):
        self.mutate("rendered-adverse-action-notices.json", lambda records:
                    records[0]["rendered_reason_segments"][0].update(rendered_reason_text="A different explanation"))
        self.review()
        self.assertBlocked("rendered_notice_text_mismatch")

    def test_unknown_new_qa_finding_is_blocking(self):
        self.review()
        qa = compute_reason_qa(load_dataset_payloads(self.dataset))
        qa["exceptions"].append({
            "exception_type": "future_material_check",
            "message": "New defect must not be silently allowlisted.",
            "decision_id": "dec-0002",
        })
        with patch("credit_gov.reason_content.compute_reason_qa", return_value=qa):
            self.assertBlocked("future_material_check")

    def test_missing_required_inputs_are_never_a_pass(self):
        for name in (
            "adverse-action-driver-contributions.json", "reason-fidelity-policy.json",
            "adverse-action-notice-template.json", "reason-selection-methods.json",
            "rendered-adverse-action-notices.json",
        ):
            with self.subTest(name=name):
                original = (self.dataset / name).read_bytes()
                (self.dataset / name).unlink()
                self.review()
                self.assertBlocked()
                (self.dataset / name).write_bytes(original)

    def test_not_run_and_not_applicable_cannot_be_treated_as_clean(self):
        for status in ("not_applicable", "not_run_missing_source_to_notice_inputs", "unknown"):
            with self.subTest(status=status):
                self.review()
                qa = {"exceptions": [], "source_to_notice_fidelity": {"status": status}}
                with patch("credit_gov.reason_content.compute_reason_qa", return_value=qa):
                    self.assertBlocked("required_checks_not_run")

    def test_unresolved_review_and_missing_decision_coverage_block(self):
        for name in REQUIRED_REVIEWS:
            with self.subTest(check=name):
                review = self.review()
                review["decision_reviews"][0]["checks"][name]["status"] = "not_assessed"
                self.write("reason-content-review.json", review)
                self.assertBlocked("review_not_satisfied")
        review = self.review()
        review["decision_reviews"] = []
        self.write("reason-content-review.json", review)
        self.assertBlocked("review_not_satisfied")

    def test_material_defect_blocks_until_resolved_with_bound_evidence(self):
        review = self.review()
        review["material_defects"] = [{
            "defect_id": "manual-accuracy-finding", "material": True, "status": "open",
            "rationale": "Test-only externally identified accuracy issue.",
            "evidence_files": ["review-evidence.json"],
        }]
        self.write("reason-content-review.json", review)
        self.assertBlocked("review_not_satisfied")
        review["material_defects"][0]["status"] = "resolved"
        review["material_defects"][0]["evidence_files"] = ["missing-evidence.json"]
        self.write("reason-content-review.json", review)
        self.assertBlocked("review_not_satisfied")
        review["material_defects"][0]["evidence_files"] = ["review-evidence.json"]
        self.write("reason-content-review.json", review)
        self.assertTrue(assess_reason_content(self.dataset)["reason_content_checks_passed"])

    def test_unknown_defect_materiality_blocks(self):
        review = self.review()
        review["material_defects"] = [{
            "defect_id": "unclassified", "material": None, "status": "open",
            "rationale": "Materiality not established.", "evidence_files": ["review-evidence.json"],
        }]
        self.write("reason-content-review.json", review)
        self.assertBlocked("review_not_satisfied")

    def test_changed_input_or_evidence_invalidates_review(self):
        for name in ("adverse-action-reason-outputs.json", "reason-fidelity-policy.json", "review-evidence.json"):
            with self.subTest(name=name):
                self.review()
                with (self.dataset / name).open("a", encoding="utf-8") as handle:
                    handle.write(" ")
                self.assertBlocked("review_not_satisfied")

    def test_review_expiry_future_date_and_gate_version_block(self):
        for field, value in (
            ("valid_until", "2026-10-20T12:00:00Z"),
            ("reviewed_at", "2026-10-20T12:00:01Z"),
            ("reviewed_at", "2026-02-30T00:00:00Z"),
            ("gate_version", "obsolete-gate"),
            ("known_defects_complete", False),
        ):
            with self.subTest(field=field, value=value):
                review = self.review()
                review[field] = value
                self.write("reason-content-review.json", review)
                self.assertBlocked("review_not_satisfied")

    def test_duplicate_ambiguous_and_malformed_inputs_block(self):
        for name, mutate in (
            ("adverse-action-driver-contributions.json", lambda r: r.append(copy.deepcopy(r[1]))),
            ("reason-code-mappings.json", lambda r: r[1].update(reason_code=r[0]["reason_code"])),
            ("adverse-action-notice-template.json", lambda r: r.update(effective_date="not-a-date")),
            ("reason-fidelity-policy.json", lambda r: r.update(principal_driver_rank_limit=True)),
            ("adverse-action-reason-outputs.json", lambda r: r.append(copy.deepcopy(r[0]))),
        ):
            with self.subTest(name=name):
                original = (self.dataset / name).read_bytes()
                self.mutate(name, mutate)
                self.review()
                self.assertBlocked()
                (self.dataset / name).write_bytes(original)
        for text in ('{"duplicate": 1, "duplicate": 2}', '{"bad": NaN}', '{broken'):
            with self.subTest(text=text):
                (self.dataset / "review-evidence.json").write_text(text, encoding="utf-8")
                self.assertBlocked("assessment_error")

    def test_export_does_not_trust_a_previous_positive_assessment(self):
        self.review()
        self.assertTrue(assess_reason_content(self.dataset)["reason_content_checks_passed"])
        self.mutate("rendered-adverse-action-notices.json", lambda r:
                    r[0]["rendered_reason_segments"][0].update(rendered_reason_text="Changed after review"))
        self.assertBlocked("rendered_notice_text_mismatch")

    def test_export_does_not_overwrite_existing_artifact_or_input(self):
        self.review()
        self.output.write_text("existing artifact", encoding="utf-8")
        result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["ok"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertEqual("existing artifact", self.output.read_text(encoding="utf-8"))
        target = self.dataset / "new-export.json"
        result = export_reviewed_reasons(self.dataset, target)
        self.assertFalse(result["ok"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(target.exists())

    def test_assessment_error_does_not_export_partial_file(self):
        self.review()
        with patch("credit_gov.reason_content._install_new_file", side_effect=OSError("simulated failure")):
            result = export_reviewed_reasons(self.dataset, self.output)
            self.assertFalse(result["ok"])
            self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())
        self.assertEqual(["dataset"], sorted(p.name for p in self.root.iterdir()))

    def test_review_expiring_during_export_cannot_pass(self):
        self.review()
        with patch("credit_gov.reason_content.utc_now", side_effect=[
            NOW, NOW, datetime(2026, 10, 21, tzinfo=timezone.utc),
        ]):
            result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["ok"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())

    def test_snapshot_export_blocks_changed_bytes_after_assessment(self):
        self.review()
        original = self.read("adverse-action-reason-outputs.json")
        from credit_gov import reason_content
        assess = reason_content._assess_snapshot

        def assess_then_change(files):
            result = assess(files)
            self.mutate("adverse-action-reason-outputs.json", lambda r:
                        r[0].update(disclosed_reason_text="Unreviewed replacement"))
            return result

        with patch("credit_gov.reason_content._assess_snapshot", side_effect=assess_then_change):
            result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["ok"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())
        self.assertNotEqual(original, self.read("adverse-action-reason-outputs.json"))
        self.assertFalse(assess_reason_content(self.dataset)["reason_content_checks_passed"])

    def test_review_withdrawal_deletion_or_new_defect_before_export_blocks(self):
        from credit_gov import reason_content
        assess = reason_content._assess_snapshot
        def revoke():
            self.mutate("reason-content-review.json", lambda r: r.update(known_defects_complete=False))
        def remove():
            (self.dataset / "reason-content-review.json").unlink()
        def add_defect():
            self.write("new-defect.json", {"material": True, "status": "open"})
        for change in (revoke, remove, add_defect):
            with self.subTest(change=change.__name__):
                self.review()
                def assess_then_change(files):
                    result = assess(files)
                    change()
                    return result
                with patch("credit_gov.reason_content._assess_snapshot", side_effect=assess_then_change):
                    result = export_reviewed_reasons(self.dataset, self.output)
                self.assertFalse(result["ok"])
                self.assertFalse(result["assessment"]["reason_content_checks_passed"])
                self.assertIn("snapshot_changed", {b["code"] for b in result["assessment"]["blockers"]})
                self.assertFalse(self.output.exists())

    def test_assessment_cannot_pass_if_review_changes_during_checks(self):
        self.review()
        from credit_gov import reason_content
        assess = reason_content._assess_snapshot
        def assess_then_withdraw(files):
            result = assess(files)
            self.mutate("reason-content-review.json", lambda r: r.update(known_defects_complete=False))
            return result
        with patch("credit_gov.reason_content._assess_snapshot", side_effect=assess_then_withdraw):
            result = assess_reason_content(self.dataset)
        self.assertFalse(result["reason_content_checks_passed"])
        self.assertIn("snapshot_changed", {b["code"] for b in result["blockers"]})

    def test_control_source_or_schema_changes_invalidate_existing_review(self):
        from credit_gov import reason_content
        controls = reason_content._control_fingerprints()
        self.assertIn("package/monitoring.py", controls)
        self.assertIn("schemas/application-decision-record.schema.json", controls)
        for name in ("package/reason_content.py", "package/reason_fidelity.py", "package/result_scope.py",
                     "schemas/application-decision-record.schema.json"):
            with self.subTest(control=name):
                self.review()
                changed = {**controls, name: "0" * 64}
                with patch("credit_gov.reason_content._control_fingerprints", return_value=changed):
                    self.assertBlocked("review_not_satisfied")

    def test_control_change_during_export_and_unreadable_freshness_block(self):
        from credit_gov import reason_content
        self.review()
        controls = reason_content._control_fingerprints()
        changed = {**controls, "package/reason_content.py": "0" * 64}
        with patch("credit_gov.reason_content._control_fingerprints", side_effect=[controls, changed]):
            result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())
        snapshot = reason_content._snapshot(self.dataset)
        with patch("credit_gov.reason_content._snapshot", side_effect=[snapshot, OSError("unreadable")]):
            result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())

    def test_missing_or_changed_control_version_cannot_reuse_prior_review(self):
        for version in ("reason-final-use-v1", "reason-final-use-v2", "reason-content-review-v3"):
            with self.subTest(version=version):
                review = self.review()
                review["gate_version"] = version
                self.write("reason-content-review.json", review)
                self.assertBlocked("review_not_satisfied")
        with patch("credit_gov.reason_content._control_fingerprints", side_effect=OSError("missing source")):
            self.assertBlocked("assessment_error")

    def test_incomplete_qa_success_labels_cannot_authorize_export(self):
        self.review()
        qa = {"exceptions": [], "source_to_notice_fidelity": {
            "status": "ran_synthetic_source_to_rendered_notice_controls",
            "rendered_notice_fidelity": {"status": "ran_synthetic_rendered_notice_controls"},
        }}
        with patch("credit_gov.reason_content.compute_reason_qa", return_value=qa):
            self.assertBlocked("incomplete_qa_result")

    def test_inconsistent_qa_counts_coverage_configuration_or_missing_fields_block(self):
        self.review()
        original = compute_reason_qa(load_dataset_payloads(self.dataset))
        cases = [
            ((), "exception_count", 1), ((), "exception_count", False),
            ((), "declined_decision_count", 0), ((), "reason_output_count", 0),
            (("source_to_notice_fidelity",), "exception_count", 1),
            (("source_to_notice_fidelity",), "exception_types", ["unreported_defect"]),
            (("source_to_notice_fidelity",), "policy_version", "other-policy"),
            (("source_to_notice_fidelity",), "selection_method_components", []),
            (("source_to_notice_fidelity", "rendered_notice_fidelity"), "exception_count", 1),
            (("source_to_notice_fidelity", "rendered_notice_fidelity"), "exception_types", ["unreported_defect"]),
        ]
        for path, field, value in cases:
            with self.subTest(path=path, field=field, value=value):
                qa = copy.deepcopy(original)
                target = qa
                for name in path:
                    target = target[name]
                target[field] = value
                with patch("credit_gov.reason_content.compute_reason_qa", return_value=qa):
                    self.assertBlocked("incomplete_qa_result")
        for field in ("exception_count", "exception_types", "policy_id", "selection_method_components"):
            with self.subTest(missing=field):
                qa = copy.deepcopy(original)
                del qa["source_to_notice_fidelity"][field]
                with patch("credit_gov.reason_content.compute_reason_qa", return_value=qa):
                    self.assertBlocked("incomplete_qa_result")

    def test_absent_optional_check_inputs_do_not_pass_even_when_schema_allows_them(self):
        optional = {
            "reason-fidelity-policy.json", "adverse-action-notice-template.json",
            "reason-selection-methods.json", "adverse-action-driver-contributions.json",
            "rendered-adverse-action-notices.json",
        }
        for name in optional:
            (self.dataset / name).unlink()
        self.mutate("evidence-pack-manifest.json", lambda m: m.update(
            input_references=[name for name in m["input_references"] if name not in optional]))
        self.review()
        result = self.assertBlocked("required_checks_not_run")
        self.assertNotIn("invalid_dataset", {b["code"] for b in result["blockers"]})

    def test_each_declared_failed_component_needs_source_evidence(self):
        self.mutate("application-decision-records.json", lambda records:
                    next(r for r in records if r["decision_id"] == "dec-0002").update(
                        decision_component="combined", failed_components=["scoring", "judgmental"]))
        self.regenerate()
        self.review()
        self.assertBlocked("assessment_error")
        self.mutate("adverse-action-driver-contributions.json", lambda records:
                    next(r for r in records if r["decision_id"] == "dec-0002")["contributions"].append({
                        "driver_or_signal": self.read("reason-code-mappings.json")[2]["driver_or_signal"],
                        "contribution": 0.25, "direction": "adverse", "decision_component": "judgmental",
                    }))
        self.regenerate()
        self.review()
        result = assess_reason_content(self.dataset)
        self.assertTrue(result["reason_content_checks_passed"], result["blockers"])

    def test_duplicate_reason_from_one_source_cannot_pass(self):
        outputs = self.read("adverse-action-reason-outputs.json")
        duplicate = {**outputs[0], "reason_output_id": "rso-extra-duplicate", "reason_rank": 3}
        outputs.append(duplicate)
        self.write("adverse-action-reason-outputs.json", outputs)
        notices = self.read("rendered-adverse-action-notices.json")
        segment = {**notices[0]["rendered_reason_segments"][0], "reason_output_id": duplicate["reason_output_id"]}
        notices[0]["rendered_reason_segments"].append(segment)
        self.write("rendered-adverse-action-notices.json", notices)
        self.review()
        self.assertBlocked("assessment_error")

    def test_empty_evidence_and_overflow_numbers_are_not_a_review(self):
        for evidence in (None, {}, [], {"source": None}, {"source": " "}, [{"source": []}], "unstructured"):
            with self.subTest(evidence=evidence):
                self.write("review-evidence.json", evidence)
                self.review()
                self.assertBlocked("review_not_satisfied")
        (self.dataset / "review-evidence.json").write_text('{"amount": 1e999}', encoding="utf-8")
        self.assertBlocked("assessment_error")

    def test_missing_and_blank_review_checks_cannot_pass(self):
        for name in REQUIRED_REVIEWS:
            for change in ("missing", "blank_rationale", "no_evidence"):
                with self.subTest(check=name, change=change):
                    review = self.review()
                    checks = review["decision_reviews"][0]["checks"]
                    if change == "missing":
                        del checks[name]
                    elif change == "blank_rationale":
                        checks[name]["rationale"] = " "
                    else:
                        checks[name]["evidence_files"] = []
                    self.write("reason-content-review.json", review)
                    self.assertBlocked("review_not_satisfied")

    def test_invalid_shared_configuration_blocks_assessment_and_export(self):
        cases = (
            ("reason-fidelity-policy.json", lambda p: p.update(policy_id=" ")),
            ("reason-fidelity-policy.json", lambda p: p.update(policy_version=False)),
            ("reason-fidelity-policy.json", lambda p: p.update(principal_driver_rank_limit=True)),
            ("reason-fidelity-policy.json", lambda p: p.update(principal_driver_rank_limit=0)),
            ("reason-fidelity-policy.json", lambda p: p.update(principal_driver_rank_limit=2.5)),
            ("adverse-action-notice-template.json", lambda p: p.update(template_id=" ")),
            ("adverse-action-notice-template.json", lambda p: p.update(template_version=[])),
            ("adverse-action-notice-template.json", lambda p: p.update(effective_date="2026-02-30")),
            ("adverse-action-notice-template.json", lambda p: p.update(retired_date=False)),
            ("adverse-action-notice-template.json", lambda p: p.update(retired_date=p["effective_date"])),
            ("adverse-action-notice-template.json", lambda p: p.pop("retired_date")),
            ("reason-selection-methods.json", lambda p: p.clear()),
            ("reason-selection-methods.json", lambda p: p.append(copy.deepcopy(p[0]))),
            ("reason-selection-methods.json", lambda p: p[0].update(decision_component="unknown")),
            ("reason-selection-methods.json", lambda p: p[0].update(selection_method_version=" ")),
        )
        for index, (name, mutate) in enumerate(cases):
            with self.subTest(file=name, case=index):
                original = (self.dataset / name).read_bytes()
                self.mutate(name, mutate)
                self.review()
                self.assertBlocked()
                (self.dataset / name).write_bytes(original)

    def test_clock_rollback_before_export_cannot_pass_future_review(self):
        self.review()
        with patch("credit_gov.reason_content.utc_now", side_effect=[
            NOW, NOW, datetime(2026, 10, 20, 10, tzinfo=timezone.utc),
        ]):
            result = export_reviewed_reasons(self.dataset, self.output)
        self.assertFalse(result["ok"])
        self.assertFalse(result["assessment"]["reason_content_checks_passed"])
        self.assertFalse(self.output.exists())

    def test_mapping_retirement_must_be_explicit_and_valid(self):
        self.mutate("reason-code-mappings.json", lambda rows: rows[0].pop("retired_date"))
        self.review()
        self.assertBlocked("assessment_error")
        self.mutate("reason-code-mappings.json", lambda rows: rows[0].update(retired_date=None))
        self.review()
        self.assertTrue(assess_reason_content(self.dataset)["reason_content_checks_passed"])

    def test_review_cannot_predate_its_final_decision(self):
        self.mutate("application-decision-records.json", lambda rows:
                    next(r for r in rows if r["decision_id"] == "dec-0002")["underwriting"].update(
                        decision_timestamp="2026-10-20T11:30:00Z"))
        review = self.review()
        self.assertBlocked("review_not_satisfied")
        review["reviewed_at"] = "2026-10-20T11:30:00Z"
        self.write("reason-content-review.json", review)
        self.assertTrue(assess_reason_content(self.dataset)["reason_content_checks_passed"])

    def test_noncontiguous_ranks_and_blank_control_identifiers_block(self):
        self.mutate("adverse-action-reason-outputs.json", lambda rows: rows[1].update(reason_rank=3))
        self.review()
        self.assertBlocked("assessment_error")
        self.regenerate()
        self.mutate("adverse-action-notice-template.json", lambda t: t.update(template_version="   "))
        # Malformed configuration now fails before generation. Also exercise
        # the gate against independently corrupted, internally matching records.
        with self.assertRaises(ValueError):
            self.regenerate()
        for name in ("adverse-action-reason-outputs.json", "rendered-adverse-action-notices.json"):
            self.mutate(name, lambda rows: [r.update(notice_template_version="   ") for r in rows])
        self.review()
        self.assertBlocked("invalid_dataset")

    def test_configured_five_principal_reasons_are_not_rejected_by_a_legal_four_reason_cap(self):
        mappings = self.read("reason-code-mappings.json")
        def add_drivers(records):
            contributions = next(r for r in records if r["decision_id"] == "dec-0002")["contributions"]
            for mapping, amount in zip((mappings[2], mappings[4], mappings[7]), (0.25, 0.2, 0.15)):
                contributions.append({
                    "driver_or_signal": mapping["driver_or_signal"],
                    "contribution": amount, "direction": "adverse", "decision_component": "scoring",
                })
        self.mutate("adverse-action-driver-contributions.json", add_drivers)
        self.mutate("reason-fidelity-policy.json", lambda p: p.update(principal_driver_rank_limit=5))
        self.assertEqual(5, len(self.regenerate(max_reasons=5)))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["generate-reasons", str(self.dataset)]))
        self.assertEqual(5, len(self.read("adverse-action-reason-outputs.json")))
        self.review()
        result = assess_reason_content(self.dataset)
        self.assertTrue(result["reason_content_checks_passed"], result["blockers"])

    def test_cli_returns_failure_without_creating_an_export(self):
        for command in (
            ["assess-reason-content", str(self.dataset)],
            ["export-reviewed-reasons", str(self.dataset), "--output", str(self.output)],
        ):
            with self.subTest(command=command[0]), redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(1, main(command))
                self.assertIn('"eligible_for_final_use": false', stream.getvalue())
        self.assertFalse(self.output.exists())
        self.review()
        with redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, main(["assess-reason-content", str(self.dataset)]))
            result = json.loads(stream.getvalue())
            self.assertTrue(result["reason_content_checks_passed"])
            self.assertNotAuthorized(result)
        with redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, main(["export-reviewed-reasons", str(self.dataset), "--output", str(self.output)]))
            result = json.loads(stream.getvalue())
            self.assertTrue(result["ok"])
            self.assertTrue(result["assessment"]["reason_content_checks_passed"])
            self.assertNotAuthorized(result)
            self.assertNotAuthorized(result["assessment"])

    def test_diagnostic_monitoring_success_does_not_imply_eligibility(self):
        result = run_monthly_monitoring(self.dataset, self.root / "evidence")
        self.assertTrue(result.ok, result.errors)
        self.assertFalse(result.to_dict()["eligible_for_final_use"])
        self.assertNotAuthorized(result.to_dict())
        self.assertEqual("not_assessed", result.to_dict()["final_use_status"])

    def test_seeded_defective_benchmark_never_exports_even_with_review(self):
        for path in SOURCE.glob("*.json"):
            shutil.copy2(path, self.dataset / path.name)
        self.review()
        result = self.assertBlocked("principal_driver_unmapped")
        self.assertGreater(len(result["blockers"]), 1)


if __name__ == "__main__":
    unittest.main()
