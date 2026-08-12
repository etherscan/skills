# Etherscan

An agent skill for navigating Etherscan across its website, API, CLI, and MCP interfaces. It helps an agent select the right interface, discover current capabilities from official sources, construct requests or commands, and preserve relevant chain, authentication, rate-limit, and error context.

Install the complete `skills/etherscan/` directory. The interface-specific guidance lives in `references/`, so copying `SKILL.md` alone is incomplete.

## Installation

### Skills CLI

Install just this skill:

```bash
npx skills add etherscan/skills --skill etherscan
```

### Codex

Clone or [download the repository](https://github.com/etherscan/skills/archive/refs/heads/main.zip), then copy the complete skill directory to a personal or project-scoped Codex skills directory:

```bash
# Personal installation
cp -r skills/etherscan ~/.codex/skills/etherscan

# Project-scoped installation
cp -r skills/etherscan .codex/skills/etherscan
```

The installed directory must contain `SKILL.md` at its root. Restart Codex or begin a new session if the skill is not discovered immediately.

### Claude Code

Clone or download the repository, then copy the complete skill directory into the Claude Code skills directory:

```bash
cp -r skills/etherscan ~/.claude/skills/etherscan
```

The installed directory must contain `SKILL.md` at its root. Restart Claude Code or begin a new session if the skill is not discovered immediately.

## Further References

- See the [Etherscan Skills repository README](../../README.md) for all available skills, repository-wide installation options, usage examples, contribution guidance, security reporting, and licensing.

