#!/usr/bin/env python3
"""Validate the structure and frontmatter of every publishable skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(skill_file: Path) -> dict[str, object]:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must begin with a YAML frontmatter delimiter (---)")

    try:
        closing_delimiter = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError("SKILL.md frontmatter is missing its closing delimiter (---)") from error

    try:
        frontmatter = yaml.safe_load("\n".join(lines[1:closing_delimiter]))
    except yaml.YAMLError as error:
        raise ValueError(f"SKILL.md contains invalid YAML frontmatter: {error}") from error

    if not isinstance(frontmatter, dict):
        raise ValueError("SKILL.md frontmatter must be a YAML mapping")

    return frontmatter


def validate_skills(skills_root: Path) -> list[str]:
    errors: list[str] = []

    if not skills_root.is_dir():
        return [f"{skills_root}: skills directory does not exist"]

    skill_directories = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_directories:
        return [f"{skills_root}: no skill directories found"]

    names: dict[str, Path] = {}

    for skill_directory in skill_directories:
        skill_file = skill_directory / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_directory}: missing SKILL.md")
            continue

        try:
            frontmatter = parse_frontmatter(skill_file)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{skill_file}: {error}")
            continue

        name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not isinstance(name, str) or not name.strip():
            errors.append(f"{skill_file}: frontmatter 'name' must be a non-empty string")
        else:
            if len(name) > 64 or not NAME_PATTERN.fullmatch(name):
                errors.append(
                    f"{skill_file}: frontmatter name '{name}' must be at most 64 "
                    "characters using lowercase letters, numbers, and single hyphens"
                )
            if name != skill_directory.name:
                errors.append(
                    f"{skill_file}: frontmatter name '{name}' must match directory "
                    f"name '{skill_directory.name}'"
                )
            if name in names:
                errors.append(
                    f"{skill_file}: duplicate skill name '{name}' also used by "
                    f"{names[name] / 'SKILL.md'}"
                )
            else:
                names[name] = skill_directory

        if not isinstance(description, str) or not description.strip():
            errors.append(
                f"{skill_file}: frontmatter 'description' must be a non-empty string"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "skills",
        help="directory containing one publishable skill per immediate subdirectory",
    )
    args = parser.parse_args()

    errors = validate_skills(args.skills_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated all skill directories in {args.skills_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
