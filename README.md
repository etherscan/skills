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
| [etherscan-flow](./skills/etherscan-flow/SKILL.md) | `npx skills add etherscan/skills --skill etherscan-flow` | Trace on-chain money flow via the Etherscan API V2 and write a single Etherscan Flow Case JSON file (nodes + edges). Two modes — strict trace for tx/address investigation, and business/entity profile for income, spending, and treasury questions. Security cases reconstruct an evidence-backed incident mechanism, confidence, and losses. |

## Installation

### With the Skills CLI

Install every skill in this repo:

```bash
npx skills add etherscan/skills
```

Or install a single skill:

```bash
npx skills add etherscan/skills --skill etherscan-flow
```

### Without npm

A skill is just a folder with a `SKILL.md` — no package manager required.

**Copy the folder** into your agent's skills directory (e.g. `~/.claude/skills/`):

```bash
git clone https://github.com/etherscan/skills.git etherscan-skills
cp -r etherscan-skills/skills/etherscan-flow ~/.claude/skills/
```

**Or download the ZIP** from the green *Code* button on GitHub, unzip, and copy the `skills/etherscan-flow` folder into your skills directory.

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
