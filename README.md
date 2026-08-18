# Etherscan Skills

[Agent Skills](https://skills.sh) for working with [Etherscan](https://etherscan.io) and on-chain data. These skills let AI agents turn raw Etherscan API responses into structured, verifiable output — every address, amount, and transaction hash comes from a live API call, never invented.

<!-- Badge row 1 - status -->

[![GitHub contributors](https://img.shields.io/github/contributors/etherscan/skills)](https://github.com/etherscan/skills/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/etherscan/skills)](https://github.com/etherscan/skills/graphs/contributors)
![GitHub repo size](https://img.shields.io/github/repo-size/etherscan/skills)

<!-- Badge row 2 - links and profiles -->

[![Website etherscan.io](https://img.shields.io/website-up-down-green-red/https/etherscan.io.svg)](https://etherscan.io)
[![Docs](https://img.shields.io/badge/docs-up-green)](https://docs.etherscan.io/)
[![Twitter Etherscan](https://img.shields.io/twitter/follow/etherscan?style=social)](https://twitter.com/etherscan)

<!-- Badge row 3 - detailed status -->

[![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/etherscan/skills)](https://github.com/etherscan/skills/pulls)
[![GitHub Issues](https://img.shields.io/github/issues-raw/etherscan/skills.svg)](https://github.com/etherscan/skills/issues)

## Skills

| Skill | Install | Description |
| ----- | ------- | ----------- |
| [etherscan](./skills/etherscan/SKILL.md) | `npx skills add etherscan/skills --skill etherscan` | Navigate Etherscan website features, API endpoints, CLI commands, and MCP tools, selecting the right interface and verifying current behavior from live official sources. |
| [etherscan-contract-review](./skills/etherscan-contract-review/SKILL.md) | `npx skills add etherscan/skills --skill etherscan-contract-review` | Review and explain verified deployed EVM contracts, including architecture, user and admin flows, proxy roles, asset movement, privileged controls, and evidence-backed uncertainty. |
| [etherscan-flow](./skills/etherscan-flow/SKILL.md) | `npx skills add etherscan/skills --skill etherscan-flow` | Trace on-chain money flow via the Etherscan API V2 and write a single Etherscan Flow Case JSON file (nodes + edges). Two modes — strict trace for tx/address investigation, and business/entity profile for income, spending, and treasury questions. Security cases reconstruct an evidence-backed incident mechanism, confidence, and losses. |
| [etherscan-transaction-debugger](./skills/etherscan-transaction-debugger/SKILL.md) | `npx skills add etherscan/skills --skill etherscan-transaction-debugger` | Analyze and explain one or two EVM transactions from live Etherscan data, with human-verifiable evidence links. Reconstructs the supported execution path, decodes calls and events, summarizes asset and permission changes, and explains failures — with confidence ratings and stated limitations. |

## Installation

### With the Skills CLI

Install every skill in this repo:

```bash
npx skills add etherscan/skills
```

Or install a single skill:

```bash
npx skills add etherscan/skills --skill etherscan
npx skills add etherscan/skills --skill etherscan-contract-review
npx skills add etherscan/skills --skill etherscan-flow
npx skills add etherscan/skills --skill etherscan-transaction-debugger
```

### Without npm

A skill is just a folder with a `SKILL.md` — no package manager required.

**Copy the folder** into your agent's skills directory (e.g. `~/.claude/skills/`):

```bash
git clone https://github.com/etherscan/skills.git etherscan-skills

# Install etherscan only
cp -r etherscan-skills/skills/etherscan ~/.claude/skills/

# Install etherscan-contract-review only
cp -r etherscan-skills/skills/etherscan-contract-review ~/.claude/skills/

# Install etherscan-flow only
cp -r etherscan-skills/skills/etherscan-flow ~/.claude/skills/

# Install etherscan-transaction-debugger only
cp -r etherscan-skills/skills/etherscan-transaction-debugger ~/.claude/skills/

# Install all skills
cp -r etherscan-skills/skills/etherscan-contract-review etherscan-skills/skills/etherscan etherscan-skills/skills/etherscan-flow etherscan-skills/skills/etherscan-transaction-debugger ~/.claude/skills/
```

**Or download the ZIP** from the green *Code* button on GitHub, unzip it, and copy any or all folders under `skills/` into your skills directory. Copy each complete skill folder so that its `SKILL.md` remains at the folder root.

## Usage

Skills are available to your agent as soon as they're installed. The agent uses them automatically when a relevant task shows up.

**Examples:**

```text
Trace this transaction: 0x...
```

```text
Follow the money from this address
```

```text
Build a case for this scam
```

```text
Show ENS DAO's income and spending as a business
```

## Contributing

New skills go in `skills/<name>/` with a `SKILL.md` at the folder root. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

Licensed under the terms of the [LICENSE](LICENSE) file (MIT).
