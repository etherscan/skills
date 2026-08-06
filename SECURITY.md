# Security Policy

## Reporting a vulnerability

If you find a security issue in any skill in this repository, please report it
privately rather than opening a public issue.

- Use GitHub's [private vulnerability reporting](https://github.com/etherscan/skills/security/advisories/new), or
- Email the maintainers.

Please include enough detail to reproduce the issue. We'll acknowledge your
report and keep you updated on the fix.

## Scope

These skills instruct AI agents and produce JSON output from live Etherscan API
responses. Of particular interest:

- Any path that could let untrusted API data inject markup or scripts into
  generated output (the `etherscan-flow` schema enforces string sanitization —
  report gaps).
- API key handling and leakage.
