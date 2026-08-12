# Etherscan Flow

[![License: MIT](https://img.shields.io/badge/license-MIT-2563eb.svg)](https://github.com/etherscan/skills/blob/main/LICENSE)
[![Etherscan API V2](https://img.shields.io/badge/Etherscan-API%20V2-21325b.svg)](https://docs.etherscan.io/)
[![Download ZIP](https://img.shields.io/badge/download-ZIP-16a34a.svg)](https://github.com/etherscan/skills/archive/refs/heads/main.zip)

**An installable agent skill for tracing, verifying, and visualizing on-chain money flows.**

Give your AI agent a transaction hash, wallet address, resolvable business or entity, draft case, or source URL. Etherscan Flow queries live Etherscan API V2 data and produces a single import-ready **Etherscan Flow Case** JSON file (`nodes` + `edges`).

Use it for a plain transfer, token launch, DeFi swap route, NFT mint, treasury profile, or a full scam/hack investigation from victim to attacker, laundering hops, and exchange deposit.

Every address, amount, and transaction hash in the output is grounded in a real API response. Flow data is never invented.

The skill has two modes, plus a document-import path:

- **Strict trace mode:** start from a tx hash or address and follow the money.
- **Business/entity profile mode:** start from a DAO/protocol/project/business scope, resolve it to verified addresses, then summarize income, spending, categories, and totals inside the JSON. Ask for a period — "last year", "since launch", "in 2025" — and you get that period. Ask without one and you get the **last 7 days**, because a short window the tracer can fully paginate is a true number and a wide one it can't is not. Every total carries a `coverage` block saying which window it actually covers and whether it finished summing it.
- **Document import (into hypothesis validation):** paste a draft case, notes, or any link you typed yourself — a gist, a tweet/X post, a news article, a blog post, a forum thread. The skill extracts the addresses and flow claims from it and validates every one against the live API — nothing from the document is copied into the output unverified. The URL fetch is read-only, never carries your API key, and only ever hits links *you* typed (it never crawls links found inside a page). If a page can't be read (login wall, JS-only), it asks you to paste the text instead of stopping.

Named entities such as `ENS DAO` are treated as scope hypotheses, not evidence. The skill resolves them to real `0x...` addresses from user-provided addresses, API-resolved ENS names, or its known-entity scope table — which ships with the well-known ENS DAO candidates (treasury timelock, registrar controllers, token, governor) so `show ENS DAO as a business` works out of the box. Every table candidate is still validated live before it appears in a case.

## How it works

```mermaid
flowchart LR
    A["You paste a tx hash<br/>or wallet address"] --> B["etherscan-flow skill<br/>(runs inside your agent)"]
    B --> C["Etherscan API V2<br/>or Etherscan MCP"]
    C --> D["Trace flow · classify<br/>entities · follow hops"]
    D --> E["Etherscan Flow Case JSON<br/>nodes + edges"]
    E --> F["Import into the<br/>Etherscan Flow canvas"]
```

Common supported chains: **Ethereum** (default), BNB Chain, Polygon, Arbitrum, Optimism, Base, and Avalanche. Other named EVM chains are accepted only after a live V2 support check.

The skill ships as a lean `SKILL.md` (hard rules, routing, credential order) plus `references/*.md` files the agent reads on demand per step (progressive disclosure — keeps context small so any skills-capable model handles it well). Install the whole folder; `SKILL.md` alone is not the complete skill.

## Performance model

The tracer treats 100 calls and 20 pages per address as safety ceilings, not targets. It caches canonical requests, resumes from its fetch log, batches independent calls into bounded evidence waves, widens only active branches, and reuses tracing pages when calculating totals. Standard runs use a 40-call soft target; explicit quick and deep requests select different soft targets without weakening the hard grounding rules.

Rate control is key-aware. The skill does not assume a fixed requests-per-second value: it follows API/transport signals, adapts concurrency, honors retry guidance, and backs off when a key or endpoint is limited. Every case includes `_meta.performance` counters so a slow run can be diagnosed without exposing credentials.

## Installation

Install the complete `skills/etherscan-flow/` directory. Required workflow detail lives in `references/`, the deterministic amount helper lives in `scripts/`, and `schema/` plus `examples/` support validation. Copying `SKILL.md` alone is incomplete.

### Skills CLI

Install just this skill:

```bash
npx skills add etherscan/skills --skill etherscan-flow
```

### Git or repository ZIP

Clone or [download the `etherscan/skills` repository](https://github.com/etherscan/skills/archive/refs/heads/main.zip), then copy its `skills/etherscan-flow/` directory into your agent's skills directory:

| Agent | Destination |
|---|---|
| Codex | `~/.codex/skills/etherscan-flow/` |
| Claude Code | `~/.claude/skills/etherscan-flow/` |
| Project-scoped Codex | `.codex/skills/etherscan-flow/` |

The copied directory must have `SKILL.md` at its root.

### Claude.ai upload

For [Claude Skills](https://claude.ai/customize/skills), download and extract the repository, then create a ZIP whose archive root is the contents of `skills/etherscan-flow/`—not the monorepo root. Upload that ZIP and, on paid plans, allowlist `api.etherscan.io` in the skill's network settings.

On the web UI, supply the API key by pasting it in chat or through a connector; see the privacy notes below.

## Your Etherscan API key — and how private it really is

Etherscan API V2 requires a key — there is no anonymous or demo tier. A key is read-only and rate-limited, so leaking one is low-stakes, but keep it out of the chat transcript where you reasonably can. The skill picks a transport and key source in this order, first usable match wins:

**Etherscan CLI → Etherscan MCP → inline `apikey=` → `ETHERSCAN_API_KEY` env var → local key file**

First usable match wins for each required API operation: the official CLI is tried first, MCP second, and an inline `apikey=` only when neither exposes that operation. An inline key still takes precedence over the environment variable and local key file. The current MCP tools for core transaction evidence are `get_transaction_by_hash`, `get_transaction_receipt`, and `get_logs`; agents must use those exact names, not raw API action names. MCP presence does not imply full API coverage, so genuinely absent operations such as `eth_call` fall through instead of getting stuck. Keys from earlier conversation turns and `apikey=` text inside quoted documents are ignored. If no source can perform a required operation, the skill asks once for access. It never writes a case file without live API data.

**Where the key actually goes depends on where you run it:**

```mermaid
flowchart LR
    subgraph L["🖥️ Local agent — Claude Code / Codex CLI"]
        k1["key in env var / file /<br/>local MCP server"]:::safe -->|referenced by name in a shell command| c1["API call"]
        c1 -->|"request + results only"| ai1["AI provider"]
    end
    subgraph W["🌐 claude.ai web chat UI"]
        inl["paste apikey= in chat"]:::warn -->|"key sits in the transcript"| ai2["AI provider"]
        conn["MCP connector"]:::safe -->|"key held server-side"| ai2
    end
    classDef safe fill:#dcfce7,stroke:#16a34a,color:#065f46;
    classDef warn fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
```

| Where you run it | How you give the key | Does the key value reach the AI provider? |
|---|---|---|
| **Claude Code / Codex** (local) | CLI login/config, local MCP, env var, or local file | **No** — the local transport or shell references it without exposing the value; the model only sees the request and API results |
| **Any tool** | inline `apikey=…` | **Yes** — it's in the chat. Use a throwaway free-tier key |
| **claude.ai web** | MCP / connector | **No** — the connector holds it server-side |
| **claude.ai web** | inline `apikey=…` | **Yes** — it's in the transcript |

**Be honest with yourself about the boundary:** the local paths keep the *secret key* off the wire — but they do **not** make the investigation private. The addresses, hashes, and Etherscan responses still travel through your AI provider (Anthropic / OpenAI) as normal model context, exactly like any other prompt. So the guarantee is *"your key stays on your machine,"* not *"nothing leaves your machine."* Full local privacy would require running a local model too, which is out of scope here.

Get a free key at [etherscan.io/apis](https://etherscan.io/apis).

## Usage

Paste a hash or address and ask to investigate:

```
trace this scam 0x<txhash>
follow the money from this victim wallet 0x<address>
this is the scammer address 0x<address>, find the victims
build a case for this hack 0x<address> apikey=YOUR_KEY
```

Or profile a DAO/protocol/business from a verified scope:

```
show ENS DAO as a business
show ENS DAO as a business using these treasury, controller, and timelock addresses: 0x<address> 0x<address>
map income and spending for this protocol treasury 0x<address>
show where this DAO gets income and how it spends money, with totals, apikey=YOUR_KEY 0x<address>
```

Or import a draft, notes, or any link and have every claim verified on-chain:

```
extract the flows from this gist and build the case: https://gist.github.com/<user>/<id> apikey=YOUR_KEY
someone reported this scam on X — verify it and build the case: https://x.com/<user>/status/<id>
build a case from the addresses in this article: https://<news-site>/<path>
here's my draft case JSON — validate it and produce a verified version: <pasted draft>
```

You get a JSON file. Open [Etherscan Flow](https://etherscan.io), choose **Import**, and paste it — the schema maps one-to-one, no reformatting.

## Stop it asking permission for every call

A single trace makes **many** API calls (up to 100). If your agent asks you to approve each one, that's the agent's **permission system**, not the skill — every call is a read-only `GET` to one host (`api.etherscan.io`), so it's safe to allowlist once and let the whole trace run uninterrupted.

<details open>
<summary><b>Claude Code (CLI)</b></summary>

Fastest: the first time it prompts, choose **"Yes, and don't ask again for curl commands"** (or WebFetch to `api.etherscan.io`).

Or set it up ahead of time — run `/permissions` and add the rules, or add them to your **user** settings at `~/.claude/settings.json` (this is where an installed skill runs from):

```json
{
  "permissions": {
    "allow": [
      "WebFetch(domain:api.etherscan.io)",
      "Bash(curl:*)"
    ]
  }
}
```

`Bash(curl:*)` allows all `curl` invocations; the skill's Hard rule 2 already restricts it to the single Etherscan host. If you'd rather not allow `curl` globally, keep just the `WebFetch` rule and tell the agent to "use WebFetch, not curl."
</details>

<details>
<summary><b>Codex CLI</b></summary>

Enable workspace writes, outbound network access, and unattended approvals in `~/.codex/config.toml`:

```toml
approval_policy = "never"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

Then run the trace normally:

```bash
codex "trace this scam 0x…"
```

`workspace-write` does not enable outbound access by itself; `network_access = true` is required for the Etherscan calls. Scope this configuration to trusted use — `never` stops all approval prompts, not just Etherscan ones, and network access applies to every command in that Codex session.
</details>

<details>
<summary><b>Claude.ai (web)</b></summary>

There are no per-call prompts here; instead, on paid plans you must **allowlist `api.etherscan.io`** once in the skill's network settings (see [Installation](#installation)) or the calls are blocked outright.
</details>

## If your AI's safety filter flags a trace

Fund-flow investigations legitimately mention mixers, laundering, and stolen funds — which can pattern-match a provider's cybersecurity safeguards even though the work is read-only forensics on public data. (Anthropic says its current safeguards are "intentionally broad" and may flag routine security work; other providers have equivalents.) The skill is built to make this a bump, not a wall:

- **It states its purpose up front** — read-only public-ledger forensics, no exploit tooling — and keeps investigative narrative inside the JSON instead of chat commentary, which is where false positives are most often triggered.
- **Nothing is lost on interruption.** Every API response is appended to a scratchpad fetch log as it arrives; relaunching the same trace resumes from the log instead of re-spending your API budget.
- **It will not try to evade the filter** — no rewording, no encoding tricks. If the safeguard fires, that's between you and the provider, and the honest fixes are below.

If you hit a false positive on Claude: report it via `/feedback`, and if you do security or forensics work regularly, apply to Anthropic's [Cyber Verification Program](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude) for vetted access to security-sensitive capabilities.

## Output schema

```json
{
  "id": "case-a1b2c3d4",
  "name": "0xabcd… — approval drain traced to Binance 14",
  "schemaVersion": 1,
  "nodes": [ { "id": "victim01", "address": "0x…", "chainid": 1, "role": "victim_wallet", "hop": 0, "label": "Victim", "subLabel": null, "balance": null, "notes": "…" } ],
  "edges": [ { "id": "e1", "source": "victim01", "target": "atk01", "amount": "5000", "token": "USDT", "type": "token_transfer", "txcount": 1, "txhash": "0x…", "txhashes": ["0x…"], "chainid": 1, "timestamp": "2024-03-15T10:23:00Z" } ],
  "_meta": { "chain": "ethereum", "chainid": 1, "chains": [{ "chain": "ethereum", "chainid": 1 }], "financials": {}, "analysis": null, "performance": {}, "patterns": [], "gaps": [], "disclaimer": "…" }
}
```

Every node and edge carries a `chainid`. `hop` counts transfers from the seed, so seed and scope addresses are `hop: 0`. Repeated movements between the same pair collapse into one edge: `txcount` is how many transactions it merges, `txhash` is the earliest, and `txhashes` lists all of them so the canvas can validate each one on-chain. Anything the API did not resolve — a balance that was never needed, an unknown token symbol — is `null` rather than a guess. Financial totals live under `_meta.financials`; structured forensic conclusions live under `_meta.analysis` (`null` for ordinary cases). There are no top-level `financials` or `analysis` keys.

When a user edits Case Findings in Etherscan Flow, the canvas preserves the structured analysis and stores the displayed Markdown at `_meta.ui.findings_markdown`. The tracer itself does not emit this reserved UI field. Saved and exported layouts may also carry non-zero numeric `x` and `y` coordinates.

The full contract is [`schema/case.schema.json`](./schema/case.schema.json) (JSON Schema), with a validating example in [`examples/`](./examples/). CI checks the example against the schema on every push, so the documented shape and a real case can't drift apart.

Roles, labels, and notes are AI inference over public Etherscan data — **not** Etherscan verdicts, accusations, or legal findings.

## Optional: keep the key out of the prompt (CLI or MCP)

You can always pass an inline `apikey=`, but two optional local transports let the key live outside the chat. Per-operation resolution order is **CLI** → **MCP** → inline `apikey=` → `ETHERSCAN_API_KEY` → local key file. MCP uses task-native names such as `get_transaction_by_hash`, `get_transaction_receipt`, and `get_logs`; missing operations automatically fall through.

**Etherscan CLI** (first choice; local read-only transport). Install the official [Etherscan CLI](https://github.com/etherscan/etherscan-cli) v1.0.0+ and run `etherscan login` once; the key then stays in `ETHERSCAN_API_KEY` or the CLI's local config. The skill drives it with paged read-only commands (`etherscan account txlist … --json`) and pages them itself rather than `--all`, so it can stop the moment a branch reaches a CEX, mixer, or bridge.

**Etherscan MCP** (second choice; the key stays in the client config). Bring-your-own-key hosted endpoint:

```text
https://mcp.etherscan.io/mcp
```

Each user sends their own Etherscan V2 key in the `Authorization: Bearer <key>` header. Example for Claude Code:

```bash
claude mcp add --transport http etherscan https://mcp.etherscan.io/mcp \
  --header "Authorization: Bearer YOUR_ETHERSCAN_API_KEY"
```

Any MCP client uses the same URL and Bearer header (Codex: `codex mcp add etherscan --url https://mcp.etherscan.io/mcp --bearer-token-env-var ETHERSCAN_API_KEY`). Replace `YOUR_ETHERSCAN_API_KEY` with your own key — never paste a shared production key into public docs or screenshots.

The current default MCP surface includes `get_transaction_by_hash`, `get_transaction_receipt`, `get_logs`, account transactions/transfers, contract source/ABI/creation, labels, timestamp-to-block lookup, and supported-chain lookup. It does not yet include arbitrary proxy/RPC calls such as `eth_call`, `eth_getCode`, `eth_getBlockByNumber`, or `eth_getStorageAt`; the skill falls through for those operations.

## Tool coverage

| Tool | v1 |
|---|---|
| Claude Code | ✅ |
| Codex CLI | ✅ |
| Claude.ai (web) | ✅ |
| Gemini CLI, others | later — [open an issue](https://github.com/etherscan/skills/issues) if you want one |

Coverage grows with demand — tell us what you use.

## License

[MIT](https://github.com/etherscan/skills/blob/main/LICENSE)
