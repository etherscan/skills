# Examples

Files here are **synthetic schema fixtures**, not real traces.

`strict-trace.example.json` is a hand-built, minimal approval-drain case
(victim → attacker → exchange deposit) whose only purpose is to validate against
[`../schema/case.schema.json`](../schema/case.schema.json). **Every address,
transaction hash, and amount in it is fabricated.** The all-`1`s / all-`2`s
addresses and `0xaaaa…` / `0xbbbb…` hashes are not real, and `_meta.disclaimer`
plus a `synthetic_fixture` gap say so inside the file itself.

It exists so that:

- editors of `references/output-spec.md` have a canonical "this is valid output"
  reference, and
- CI can prove the documented schema and a full case still agree on every push
  (see `.github/workflows/package-skill.yml`).

A real run of the skill never writes here. Live output is `case-{SHORT_ID}-flow.json`,
which `.gitignore` keeps out of the repo. Do not treat this fixture as evidence of
anything on-chain.
