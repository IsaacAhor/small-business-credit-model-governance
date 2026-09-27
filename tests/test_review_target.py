from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

from scripts.validate_review_target import validate_review_form, validate_review_packets, validate_review_target
from tests.temp_utils import LocalTemporaryDirectory


class ReviewTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = LocalTemporaryDirectory(Path(__file__).resolve().parents[1] / "tmp" / "test-runs")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repository = "example/model-review"

    def files(self, tag):
        target = self.root / f"docs/external-review/targets/{tag}.md"
        notes = self.root / f"docs/releases/{tag}.md"
        for path in (target, notes):
            path.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"# Review target: {tag}\n\n"
            f"- [Pinned source](https://github.com/{self.repository}/tree/{tag}).\n",
            encoding="utf-8",
        )
        notes.write_text(
            f"# {tag}\n\n[Review target](https://github.com/{self.repository}/blob/"
            f"{tag}/docs/external-review/targets/{tag}.md)\n\n## Review this release\n\n" +
            "\n".join(f"- [{label}](https://github.com/{self.repository}/blob/{tag}/docs/external-review/{name})"
                      for name, label in [
                          ("technical-review.md", "Technical Implementation Reviewers"),
                          ("practitioner-assessment.md", "Credit Governance and Adverse-Action Reviewers"),
                          ("methodology-assessment.md", "Methodology and Evaluation Reviewers")]) + "\n",
            encoding="utf-8",
        )
        folder = self.root / "docs/external-review"
        latest = f"[Start a review](https://github.com/{self.repository}/releases/latest)\n"
        response = f"[Return review](https://github.com/{self.repository}/issues/new?template=external-review.yml)\n"
        packet_response = f"[Write review](https://github.com/{self.repository}/issues/new?" + urlencode({"template": "external-review.yml", "source": f"{tag} / {tag}"}) + ")\n"
        template = self.root / ".github/ISSUE_TEMPLATE/external-review.yml"
        template.parent.mkdir(parents=True, exist_ok=True)
        project = Path(__file__).resolve().parents[1]
        template.write_bytes((project / ".github/ISSUE_TEMPLATE/external-review.yml").read_bytes())
        (folder / "review-record-template.md").write_bytes(
            (project / "docs/external-review/review-record-template.md").read_bytes())
        (template.parent / "config.yml").write_text("blank_issues_enabled: false\n", encoding="utf-8")
        for entry in [self.root / "README.md", self.root / "START_HERE.md", folder / "current.md"]:
            entry.write_text(latest, encoding="utf-8")
        (folder / "README.md").write_text(
            f"# External review packets\n\nReview target: [{tag}](targets/{tag}.md).\n\n"
            f"Source ref: `{tag}`.\n\n" + latest + response, encoding="utf-8",
        )
        for name in ["technical-review.md", "practitioner-assessment.md", "methodology-assessment.md"]:
            body = (f"# Review packet\n\n- **Software:** {tag}.\n"
                    f"- Software target: {tag}.\n\n[Target](targets/{tag}.md)\n"
                    f"[Source](https://github.com/{self.repository}/blob/{tag}/PROJECT_BRIEF.md)\n" + latest + packet_response)
            if name == "technical-review.md":
                body += f"\n```text\ngit checkout --detach {tag}\n```\n"
            (folder / name).write_text(body, encoding="utf-8")
        (self.root / "pyproject.toml").write_text(
            f'[project]\nname = "model-review"\nversion = "{tag[1:]}"\n', encoding="utf-8",
        )
        return target, notes

    def check(self, tag="v1.2.3"):
        validate_review_target(self.root, tag, self.repository)

    def test_each_release_uses_its_own_sheet_without_writing_files(self):
        for tag in ["v1.2.3", "v1.2.4"]:
            with self.subTest(tag=tag):
                self.files(tag)
                paths = sorted(path for path in self.root.rglob("*") if path.is_file())
                before = [path.read_bytes() for path in paths]
                self.check(tag)
                self.assertEqual(before, [path.read_bytes() for path in paths])

    def test_missing_sheet_or_notes_fails(self):
        for index in [0, 1]:
            with self.subTest(missing=index):
                paths = self.files("v1.2.3")
                paths[index].unlink()
                with self.assertRaisesRegex(ValueError, "missing or unreadable"):
                    self.check()

    def test_empty_or_wrong_version_sheet_fails(self):
        target, _ = self.files("v1.2.3")
        for text in ["", "# Review target: v1.2.2\n"]:
            with self.subTest(text=text):
                target.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "heading"):
                    self.check()

    def test_missing_moving_or_wrong_version_link_fails(self):
        _, notes = self.files("v1.2.3")
        valid = notes.read_text(encoding="utf-8")
        for text in ["# Release\n", valid.replace("/blob/v1.2.3/", "/blob/main/"),
                     valid.replace("v1.2.3", "v1.2.2"), valid.replace("example/model-review", "example/other")]:
            with self.subTest(text=text):
                notes.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "version-pinned"):
                    self.check()

    def test_invalid_tag_or_repository_fails(self):
        for tag in ["../v1.2.3", "v1.2", "v01.2.3"]:
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "tag"):
                self.check(tag)
        with self.assertRaisesRegex(ValueError, "owner/name"):
            validate_review_target(self.root, "v1.2.3", "https://github.com/example/model-review")

    def test_new_release_fails_until_all_packet_versions_are_updated(self):
        self.files("v0.13.0")
        folder = self.root / "docs/external-review"
        saved = {name: (folder / name).read_bytes() for name in [
            "README.md", "technical-review.md", "practitioner-assessment.md", "methodology-assessment.md"]}
        self.files("v0.14.0")
        for name, old in saved.items():
            with self.subTest(stale=name):
                path = folder / name
                current = path.read_bytes()
                path.write_bytes(old)
                with self.assertRaisesRegex(ValueError, "must match"):
                    self.check("v0.14.0")
                path.write_bytes(current)
        self.check("v0.14.0")
        self.assertTrue((folder / "targets/v0.13.0.md").exists())

    def test_stale_response_version_is_rejected(self):
        self.files("v0.13.0")
        path = self.root / "docs/external-review/practitioner-assessment.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "- Software target: v0.13.0", "- Software target: v0.12.0"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "response version"):
            self.check("v0.13.0")

    def test_stale_or_moving_source_links_and_checkout_are_rejected(self):
        self.files("v0.13.0")
        path = self.root / "docs/external-review/technical-review.md"
        valid = path.read_text(encoding="utf-8")
        for text in [valid.replace("/blob/v0.13.0/", "/blob/main/"),
                     valid.replace("/blob/v0.13.0/", "/blob/v0.12.0/"),
                     valid.replace("--detach v0.13.0", "--detach v0.12.0"),
                     valid + f"\n[Archive](https://github.com/{self.repository}/archive/v0.12.0.zip)\n"]:
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "source links|checkout command"):
                    self.check("v0.13.0")

    def test_source_declaration_and_target_source_must_agree(self):
        target, _ = self.files("v0.13.0")
        target.write_text(target.read_text(encoding="utf-8").replace(
            "/tree/v0.13.0", "/tree/v0.12.0"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Pinned source"):
            self.check("v0.13.0")

    def test_missing_packet_and_malformed_overview_fail(self):
        for name in ["technical-review.md", "practitioner-assessment.md", "methodology-assessment.md"]:
            self.files("v0.13.0")
            (self.root / "docs/external-review" / name).unlink()
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "missing or unreadable"):
                self.check("v0.13.0")
        self.files("v0.13.0")
        overview = self.root / "docs/external-review/README.md"
        valid = overview.read_text(encoding="utf-8")
        for text in [valid.replace("Source ref: `v0.13.0`.", "Source ref: `main`."),
                     valid + "\nSource ref: `v0.13.0`.\n", "# Packets\n"]:
            overview.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.check("v0.13.0")

    def test_stale_plain_commit_hash_is_rejected(self):
        self.files("v0.13.0")
        path = self.root / "docs/external-review/methodology-assessment.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nSource commit: `" + "a" * 40 + "`.\n",
                        encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "commit or tree hash"):
            self.check("v0.13.0")

    def test_full_release_binds_commit_reference_to_tag(self):
        self.files("v0.13.0")
        source = "a" * 40
        for path in (self.root / "docs/external-review").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for old in ["/tree/v0.13.0", "/blob/v0.13.0", "--detach v0.13.0", "Source ref: `v0.13.0`", "+%2F+v0.13.0"]:
                text = text.replace(old, old.replace("v0.13.0", source))
            path.write_text(text, encoding="utf-8")
        with patch("scripts.validate_review_target.subprocess.run") as run:
            run.return_value.stdout = source + "\n"
            self.check("v0.13.0")
            run.return_value.stdout = "b" * 40 + "\n"
            with self.assertRaisesRegex(ValueError, "does not match the release tag"):
                self.check("v0.13.0")
            run.side_effect = OSError()
            with self.assertRaisesRegex(ValueError, "Cannot resolve"):
                self.check("v0.13.0")

    def test_ci_command_uses_project_version_without_rewriting_old_notes(self):
        _, notes = self.files("v0.13.0")
        notes.write_text("# Historical release notes\n", encoding="utf-8")
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/validate_review_target.py"),
                   "--packets-only", "--repository", self.repository]
        run = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(notes.read_text(encoding="utf-8"), "# Historical release notes\n")
        (self.root / "pyproject.toml").write_text('[project]\nversion = "0.14.0"\n', encoding="utf-8")
        run = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("README.md: Review target must match v0.14.0", run.stderr)

    def test_tree_hash_cannot_substitute_for_source_commit(self):
        target, _ = self.files("v0.13.0")
        tree = "b" * 40
        target.write_text(target.read_text(encoding="utf-8") + f"- Tree: `{tree}`.\n", encoding="utf-8")
        path = self.root / "docs/external-review/methodology-assessment.md"
        valid = path.read_text(encoding="utf-8") + f"\nSource tree `{tree}`.\n"
        path.write_text(valid, encoding="utf-8")
        validate_review_packets(self.root, "v0.13.0", self.repository)
        path.write_text(valid.replace("Source tree", "Source commit"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "commit or tree hash"):
            self.check("v0.13.0")

    def test_release_must_offer_each_packet_directly_at_its_own_version(self):
        _, notes = self.files("v0.13.0")
        valid = notes.read_text(encoding="utf-8")
        for name in ["technical-review.md", "practitioner-assessment.md", "methodology-assessment.md"]:
            old = f"/blob/v0.13.0/docs/external-review/{name}"
            for replacement in ["/blob/main/", "/blob/v0.12.0/", "/blob/v0.14.0/"]:
                with self.subTest(packet=name, ref=replacement):
                    notes.write_text(valid.replace(old, old.replace("/blob/v0.13.0/", replacement)), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "version-pinned packet"):
                        self.check("v0.13.0")
        for text in [valid.replace("## Review this release", "## Details"),
                     valid + "\n## Review this release\nDuplicate entry\n"]:
            notes.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "one Review this release"):
                self.check("v0.13.0")
        notes.write_text(valid + f"\n[Old packet](https://github.com/{self.repository}/blob/v0.12.0/docs/external-review/technical-review.md)\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mix packet versions"):
            self.check("v0.13.0")

    def test_entry_pages_keep_new_reviews_on_the_published_release(self):
        self.files("v0.13.0")
        for entry in ["README.md", "START_HERE.md", "docs/external-review/current.md",
                      "docs/external-review/README.md", "docs/external-review/technical-review.md",
                      "docs/external-review/practitioner-assessment.md", "docs/external-review/methodology-assessment.md"]:
            path = self.root / entry
            valid = path.read_text(encoding="utf-8")
            with self.subTest(entry=entry):
                path.write_text(valid.replace("/releases/latest", "/tree/main"), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "latest published release"):
                    validate_review_packets(self.root, "v0.13.0", self.repository)
                path.write_text(valid, encoding="utf-8")

    def test_preparing_next_version_keeps_prior_release_packet_links_fixed(self):
        _, old_notes = self.files("v0.13.0")
        saved_notes = old_notes.read_bytes()
        self.files("v0.14.0")
        validate_review_packets(self.root, "v0.14.0", self.repository)
        self.check("v0.14.0")
        self.assertEqual(old_notes.read_bytes(), saved_notes)
        self.assertEqual(saved_notes.count(b"/blob/v0.13.0/docs/external-review/"), 4)
        self.assertNotIn(b"v0.14.0", saved_notes)
        self.assertIn("/releases/latest", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_public_return_path_uses_an_existing_template_when_blank_issues_are_disabled(self):
        self.files("v0.13.0")
        self.check("v0.13.0")
        for name in ["README.md", "technical-review.md", "practitioner-assessment.md", "methodology-assessment.md"]:
            path = self.root / "docs/external-review" / name
            valid = path.read_text(encoding="utf-8")
            with self.subTest(packet=name):
                path.write_text(valid.replace("?template=external-review.yml", ""), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "external-review issue template"):
                    self.check("v0.13.0")
                path.write_text(valid, encoding="utf-8")
        (self.root / ".github/ISSUE_TEMPLATE/external-review.yml").unlink()
        with self.assertRaisesRegex(ValueError, "missing or unreadable"):
            self.check("v0.13.0")


    def test_form_prefill_keeps_the_reviewed_source_even_when_newer_work_exists(self):
        self.files("v0.13.0")
        old = (self.root / "docs/external-review/technical-review.md").read_bytes()
        self.files("v0.14.0")
        path = self.root / "docs/external-review/technical-review.md"
        valid = path.read_text(encoding="utf-8")
        for wrong in [valid.replace("source=v0.14.0", "source=v0.13.0"),
                      valid.replace("+%2F+v0.14.0", "+%2F+main"),
                      valid.replace("&source=v0.14.0+%2F+v0.14.0", ""),
                      valid.replace("+%2F+v0.14.0", "+%2F+v0.14.0&source=v0.13.0")]:
            path.write_text(wrong, encoding="utf-8")
            with self.subTest(link=wrong), self.assertRaisesRegex(ValueError, "form source prefill"):
                self.check("v0.14.0")
        path.write_text(valid, encoding="utf-8")
        self.check("v0.14.0")
        self.assertIn(b"source=v0.13.0+%2F+v0.13.0", old)
        self.assertNotIn(b"v0.14.0", old)

    def test_form_does_not_silently_assign_a_moving_instruction_revision(self):
        self.files("v0.13.0")
        path = self.root / "docs/external-review/practitioner-assessment.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "template=external-review.yml", "template=external-review.yml&packet=main"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Packet permalink"):
            self.check("v0.13.0")

    def test_form_and_offline_report_retain_the_same_fields(self):
        self.files("v0.13.0")
        report = self.root / "docs/external-review/review-record-template.md"
        report.write_text(report.read_text(encoding="utf-8").replace(
            "## Conclusion and limitations", "## Summary"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "headings must match"):
            validate_review_form(self.root)

    def test_form_preserves_identity_fields_and_explicit_answers(self):
        self.files("v0.13.0")
        path = self.root / ".github/ISSUE_TEMPLATE/external-review.yml"
        valid = path.read_text(encoding="utf-8")
        changes = [
            ("    id: source", "    id: changed-source", "field IDs"),
            ("      label: Software version and source", "      value: latest\n      label: Software version and source", "without moving defaults"),
            ("      required: true", "      required: false", "must be required"),
            ("        - Methodology and Evaluation Reviewers", "        - Researchers", "settled reviewer groups"),
            ("    id: source", "    id: packet", "unique field IDs"),
        ]
        for before, after, message in changes:
            path.write_text(valid.replace(before, after, 1), encoding="utf-8")
            with self.subTest(change=after), self.assertRaisesRegex(ValueError, message):
                validate_review_form(self.root)
        path.write_text(valid, encoding="utf-8")
        (path.parent / "external-review.md").write_text("Duplicate old form", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate Markdown"):
            validate_review_form(self.root)

    def test_profile_link_cannot_become_a_required_submission_condition(self):
        self.files("v0.13.0")
        path = self.root / ".github/ISSUE_TEMPLATE/external-review.yml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "      required: false", "      required: true"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "profile must remain optional"):
            validate_review_form(self.root)

    def test_reviewer_details_cannot_be_buried_below_the_report(self):
        self.files("v0.13.0")
        path = self.root / ".github/ISSUE_TEMPLATE/external-review.yml"
        text = path.read_text(encoding="utf-8")
        start = text.index("  - type: input\n    id: reviewer-name")
        end = text.index("  - type: input\n    id: packet")
        path.write_text(text[:start] + text[end:] + text[start:end], encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "details must appear first"):
            validate_review_form(self.root)


if __name__ == "__main__":
    unittest.main()
