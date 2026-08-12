from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import validate_skills


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.skills_root = Path(self.temporary_directory.name) / "skills"
        self.skills_root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_skill(
        self,
        directory_name: str,
        *,
        name: str | None = None,
        description: str = "A test skill.",
        raw_frontmatter: str | None = None,
    ) -> None:
        skill_directory = self.skills_root / directory_name
        skill_directory.mkdir()
        if raw_frontmatter is None:
            raw_frontmatter = (
                f"name: {name or directory_name}\n"
                f"description: {description}\n"
            )
        (skill_directory / "SKILL.md").write_text(
            f"---\n{raw_frontmatter}---\n\n# Test\n",
            encoding="utf-8",
        )

    def assert_error_contains(self, expected: str) -> None:
        errors = validate_skills(self.skills_root)
        self.assertTrue(
            any(expected in error for error in errors),
            f"Expected an error containing {expected!r}, got {errors!r}",
        )

    def test_valid_skills(self) -> None:
        self.write_skill("alpha")
        self.write_skill("beta-skill")

        self.assertEqual(validate_skills(self.skills_root), [])

    def test_missing_skill_file(self) -> None:
        (self.skills_root / "missing").mkdir()

        self.assert_error_contains("missing SKILL.md")

    def test_malformed_frontmatter(self) -> None:
        self.write_skill("broken", raw_frontmatter="name: [broken\n")

        self.assert_error_contains("invalid YAML frontmatter")

    def test_missing_required_field(self) -> None:
        self.write_skill("missing-description", raw_frontmatter="name: missing-description\n")

        self.assert_error_contains("'description' must be a non-empty string")

    def test_directory_name_must_match_skill_name(self) -> None:
        self.write_skill("directory-name", name="different-name")

        self.assert_error_contains("must match directory name 'directory-name'")

    def test_duplicate_names(self) -> None:
        self.write_skill("first", name="shared")
        self.write_skill("second", name="shared")

        self.assert_error_contains("duplicate skill name 'shared'")

    def test_name_must_be_spec_compatible(self) -> None:
        self.write_skill("invalid--name")

        self.assert_error_contains("using lowercase letters, numbers, and single hyphens")


if __name__ == "__main__":
    unittest.main()
