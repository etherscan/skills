# Etherscan Flow — Transports: MCP, CLI, and env-key details

> Part of the `etherscan-flow` skill. Read this when the run resolved to the MCP or CLI transport (credentials steps 2–3), or when checking `ETHERSCAN_API_KEY` (credentials step 4). Every Hard rule, the 100-call budget, and the validation rules in `SKILL.md` apply here unchanged.

Initialize the canonical query ledger and adaptive rate controller from `performance.md` before issuing transport calls. Do not impose or pass a global skill-level fixed requests-per-second value: the effective limit belongs to the user's key/plan, endpoint, and transport. The CLI-process launch gate below only preserves that transport's own default across separate invocations; never copy it to MCP or HTTP.

## Transport call mapping

> **MCP transport:** if you resolved to the Etherscan MCP server (credentials step 2), ignore the raw HTTP URLs in Steps 1–4. For each `module={M}&action={A}` call below, invoke the Etherscan MCP tool that performs the same operation (matching module/action — e.g. `account`/`txlist`, `account`/`tokentx`, `account`/`txlistinternal`, `proxy`/`eth_getTransactionByHash`, `proxy`/`eth_getTransactionReceipt`, `nametag`/`getaddresstag`, `contract`/`getsourcecode`), passing the same `chainid`, `address`/`txhash`, and pagination parameters. Do not pass a key — the MCP server supplies it. Every data-integrity, budget (Hard rule 8), and validation rule applies identically on all transports.

> **CLI transport:** if you resolved to the official `etherscan` CLI v1+ (credentials step 3), ignore the raw HTTP URLs in Steps 1–4 and call the equivalent read-only CLI command with `--json`, `--chain {CHAIN_NAME_OR_ID}`, and pagination flags where applicable. The CLI resolves credentials from `--api-key`, then `ETHERSCAN_API_KEY`, then the plaintext config written by `etherscan login`. Do not pass `--api-key`: it places the key in `argv`, where it is visible to process listings and shell history (Hard rule 6). This branch is reached only when the prompt did not contain `apikey=`. Every data-integrity, budget (Hard rule 8), and validation rule applies identically on all transports.

## CLI transport — command table and behaviour (credentials step 3)

Require the production command contract before using this table:

1. Run `etherscan version`; accept `1.0.0` or newer.
2. Run `etherscan whoami`; it shows the active chain and a masked key. Treat `(none — run 'etherscan login')` as an unresolved CLI credential.
3. If the executable is older, either v1 command is absent, or `whoami` reports no credential, do not guess between legacy command shapes. Fall through to `ETHERSCAN_API_KEY` and then the local key-file source. If no fallback resolves, ask the user to install/update the official v1+ CLI and run `etherscan login`, or to provide another key source.

Map API calls to CLI commands:

| API call | CLI command shape |
|----------|-------------------|
| `account` / `balance` | `etherscan account balance {ADDRESS} --chain {CHAIN} --json` |
| `account` / `txlist` | `etherscan account txlist {ADDRESS} --chain {CHAIN} --page {N} --offset 100 --sort {asc\|desc} --json` |
| `account` / `tokentx` | `etherscan account tokentx {ADDRESS} --chain {CHAIN} --page {N} --offset 100 --sort {asc\|desc} --json` |
| `account` / `tokennfttx` | `etherscan account tokennfttx {ADDRESS} --chain {CHAIN} --page {N} --offset 20 --sort desc --json` |
| `account` / `token1155tx` | `etherscan account token1155tx {ADDRESS} --chain {CHAIN} --page {N} --offset 20 --sort desc --json` |
| `account` / `txlistinternal` by address | `etherscan account txlistinternal --address {ADDRESS} --chain {CHAIN} --page {N} --offset 100 --json` |
| `account` / `txlistinternal` by txhash | `etherscan account txlistinternal --txhash {TXHASH} --chain {CHAIN} --json` |
| `proxy` / `eth_getTransactionByHash` | `etherscan proxy eth_getTransactionByHash {TXHASH} --chain {CHAIN} --json` |
| `proxy` / `eth_getTransactionReceipt` | `etherscan proxy eth_getTransactionReceipt {TXHASH} --chain {CHAIN} --json` |
| `proxy` / `eth_getCode` | `etherscan proxy eth_getCode {ADDRESS} --chain {CHAIN} --json` |
| `proxy` / `eth_getBlockByNumber` | `etherscan proxy eth_getBlockByNumber --tag {HEX_BLOCK} --boolean false --chain {CHAIN} --json` |
| `proxy` / `eth_call` | `etherscan proxy eth_call --to {ADDRESS} --data {CALLDATA} --tag latest --chain {CHAIN} --json` |
| `contract` / `getsourcecode` | `etherscan contract getsourcecode {ADDRESS} --chain {CHAIN} --json` |
| `nametag` / `getaddresstag` | `etherscan nametag getaddresstag {ADDR1,ADDR2,…} --chain {CHAIN} --json` |

**`chainlist` on non-HTTP transports.** Production CLI v1 exposes `etherscan chains list`, which lists the chains built into that binary and costs no API call. Use the maintained common-chain table in `SKILL.md` without a live lookup. For a name or ID outside that table, issue the keyless `GET https://api.etherscan.io/v2/chainlist` (the live list is authoritative for unknown entries); accept status `1` (available) or `2` (degraded), record the `chain_degraded` gap required by *Chain resolution* for status `2`, and count that request against the 100-call budget. Treat status `0` or an absent entry as unsupported. If a resolved chain is absent from `etherscan chains list`, the installed CLI cannot address it. Fall through to HTTP only when `ETHERSCAN_API_KEY` or the local key-file source resolves; do not extract the CLI's saved config key. If neither HTTP source resolves, ask the user to update the CLI or provide `apikey=` / `ETHERSCAN_API_KEY` rather than substituting another chain.

Notes on CLI behaviour that the skill depends on:

- `--boolean false` is **required** on `eth_getBlockByNumber`; omitting it returns `json-rpc error -32700: parse error`.
- `nametag getaddresstag` accepts a **comma-separated address list of at most 100 addresses**. Batch the surviving Step 2 entity set into as few calls as possible, split at 100, and cache each batch.
- **Pagination.** Pass `--page` and `--offset` together for deterministic paging. Always loop pages manually, including Step 3B totals. Do not use `--all`: it returns one combined result rather than the raw response for each page, so the canonical query ledger cannot retain every response or count attempts exactly. Stop on a short page, the relevant tracing landmark, the 20-page per-address ceiling, or the 100-call run ceiling. Although v1's `--all` defaults to `--max-pages 20` and warns on truncation, those safeguards do not satisfy the fetch-log contract.
- **Advanced filters.** `txlist`, `txlistinternal`, `tokentx`, `tokennfttx`, and `token1155tx` accept `--from`, `--to`, and required `--fromto-opr and|or`. Do not combine these with the positional/`--address` filter. Use them only when the procedure needs a directed pair or claim-specific query; otherwise retain address-based paging so both inflows and outflows remain visible.
- **Round trips and rate ownership.** Production v1 applies its client-side limiter inside one process (default 3 requests/second), but separate manual-page invocations do not share it. Execute CLI commands sequentially and use one run-scoped launch gate: start successive CLI API commands at least 350 ms apart, counting process runtime toward that interval. Do not launch a parallel wave of subprocesses or pass the hidden `--rate-limit` override. Honor stderr retry/rate-limit signals and reduce subsequent work after a limit response. This gate mirrors the CLI's own default only; MCP and HTTP retain the adaptive wave behavior in `performance.md`.

If the CLI command fails because it is not installed, not logged in, or lacks a required endpoint, fall through to the next key source. If it fails because the API returns an error, record that API error in `_meta.gaps` and continue where possible.

**Separate the two failure modes — they are different facts and they are not each other's evidence.**

| What happened | How to tell | What to record |
|---------------|-------------|----------------|
| The API answered "no" | The command ran and returned an error body: plan-gated (`API Exclusive endpoint`), `NOTOK`, rate limit, bad params | A blocked gap quoting that body verbatim, with the `endpoint` (`references/output-spec.md` → *`_meta.gaps` entries*). Do not fall through — the key is fine, this endpoint is not for it |
| The transport did not answer | Non-zero exit with no API body, binary missing, timeout, no key resolved | Fall through to the next key source. Only if every source fails is it a blocked gap, quoting the transport's own error |

`nametag/getaddresstag` is **Pro Plus** and returns `Sorry, it looks like you are trying to access an API Exclusive endpoint` on keys without it. This is expected and benign: it means no curated Etherscan labels are available for this run, so every label must come from observed behaviour (Hard rule 3 applies unchanged). It is a plan fact about one endpoint — it is **not** evidence that the transport is broken, and it says nothing about any other endpoint's availability.

In particular, `contract/getsourcecode` carries no plan gate on a standard key and is the single highest-value classification call in a security case: verified source is what separates "the guard was missing" from "the guard passed because the attacker had become the authorized caller" — opposite root causes that produce identical logs. Never report source as unavailable without having called it and received an error to quote. Falling back to bytecode when the source was there for the asking produces a confidently-hedged wrong answer, which is worse than a slow right one.

## `ETHERSCAN_API_KEY` — per-shell check and reference syntax (credentials step 4)

**POSIX shells (bash/zsh — macOS, Linux):**
```bash
test -n "$ETHERSCAN_API_KEY" && echo SET || echo UNSET
```
If SET, reference it **by name** in every request (`…&apikey=$ETHERSCAN_API_KEY`) so the shell expands it at execution.

**PowerShell (Windows, or pwsh anywhere):**
```powershell
if ($env:ETHERSCAN_API_KEY) { 'SET' } else { 'UNSET' }
```
If SET, reference it by name as `$env:ETHERSCAN_API_KEY` — e.g. build the URL with `"...&apikey=$env:ETHERSCAN_API_KEY"` so PowerShell expands it at execution.

**Windows cmd.exe:** `if defined ETHERSCAN_API_KEY (echo SET) else (echo UNSET)`; reference as `%ETHERSCAN_API_KEY%`.

In every case the variable is expanded **by the shell at call time** so the literal key never enters your context or the transcript. Never `echo`, `printenv`, `Write-Host $env:ETHERSCAN_API_KEY`, or otherwise print its value. Picking the wrong shell's syntax (e.g. `test -n` in PowerShell) silently reports UNSET and wrongly abandons a key that was there all along — match the shell.
