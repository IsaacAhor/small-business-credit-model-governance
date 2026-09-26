from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_review_target import validate_review_target
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
        target.write_text(f"# Review target: {tag}\n", encoding="utf-8")
        notes.write_text(
            f"# {tag}\n\n[Review target](https://github.com/{self.repository}/blob/"
            f"{tag}/docs/external-review/targets/{tag}.md)\n", encoding="utf-8",
        )
        return target, notes

    def check(self, tag="v1.2.3"):
        validate_review_target(self.root, tag, self.repository)

    def test_each_release_uses_its_own_sheet_without_writing_files(self):
        for tag in ["v1.2.3", "v1.2.4"]:
            with self.subTest(tag=tag):
                paths = self.files(tag)
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


if __name__ == "__main__":
    unittest.main()
