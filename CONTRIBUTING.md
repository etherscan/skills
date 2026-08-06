# Contributing

Thanks for contributing to Etherscan Skills.

## Repository layout

Each skill lives in its own folder under `skills/`:

```
skills/
  <skill-name>/
    SKILL.md        # required — the skill entry point (YAML frontmatter + body)
    README.md       # optional — human-facing overview
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

Skills that ship a `schema/` validator are checked in CI (see
`.github/workflows/validate-skills.yml`). To run the `etherscan-flow` validator locally:

```bash
cd skills/etherscan-flow
python -m pip install jsonschema
python schema/validate.py
python -m unittest schema/test_validate.py
```

## Guidelines

- Every address, amount, token, and transaction hash in a skill's output must come from a live API response — never fabricated.
- Keep changes to a single skill scoped to that skill's folder.
