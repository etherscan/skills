# Contributing

Thanks for contributing to Etherscan Skills.

## Repository layout

Each skill lives in its own folder under `skills/`:

```
skills/
  <skill-name>/
    SKILL.md        # required — the skill entry point (YAML frontmatter + body)
    README.md       # optional — human-facing overview
    scripts/        # optional — deterministic helpers
    references/     # optional — progressive-loading detail docs
    schema/         # optional — validators, JSON Schema, tests
    examples/       # optional — example outputs
```

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md`.
2. In the frontmatter, set a unique `name` (lowercase, hyphens) and a clear `description` that says *when* an agent should use the skill.
3. Keep the entry point lean; push detail into `references/` and load it only when needed.
4. Add a row to the **Skills** table in the root [README.md](README.md).

## Validation

CI validates the structure and Skills CLI discovery of every immediate directory
under `skills/`. Run the repository-wide checks locally with:

```bash
python -m pip install PyYAML
python scripts/validate_skills.py
python -B -m unittest discover -s tests -p "test_*.py"
for skill_dir in skills/*; do
  npx --yes skills@1.5.22 add "./$skill_dir" --list
done
```

Skills that ship additional validators are also checked in CI (see
`.github/workflows/validate-skills.yml`). To run the `etherscan-flow` checks locally:

```bash
cd skills/etherscan-flow
python -m pip install jsonschema
python schema/validate.py
python -m unittest discover -s schema -p "test_*.py"
```

## Guidelines

- Every address, amount, token, and transaction hash in a skill's output must come from a live API response — never fabricated.
- Keep changes to a single skill scoped to that skill's folder.
