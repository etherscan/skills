# Etherscan Flow — Transports: CLI, MCP, and env-key details

> Part of the `etherscan-flow` skill. Read this when the run resolved to the CLI or MCP transport (credentials steps 1–2), or when checking `ETHERSCAN_API_KEY` (credentials step 4). Every Hard rule, the 100-call budget, and the validation rules in `SKILL.md` apply here unchanged.

Initialize the canonical query ledger and adaptive rate controller from `performance.md` before issuing transport calls. Do not impose or pass a global skill-level fixed requests-per-second value: the effective limit belongs to the user's key/plan, endpoint, and transport. The CLI-process launch gate below only preserves that transport's own default across separate invocations; never copy it to MCP or HTTP.

## Transport call mapping

> **CLI transport:** if you resolved to the official `etherscan` CLI v1+ (credentials step 1), ignore the raw HTTP URLs in Steps 1–4 and call the equivalent read-only CLI command with `--json`, `--chain {CHAIN_NAME_OR_ID}`, and pagination flags where applicable. The CLI resolves credentials from `--api-key`, then `ETHERSCAN_API_KEY`, then the plaintext config written by `etherscan login`. Do not pass `--api-key`: it places the key in `argv`, where it is visible to process listings and shell history (Hard rule 6). A usable CLI wins even when MCP or an inline `apikey=` is also available. Every data-integrity, budget (Hard rule 8), and validation rule applies identically on all transports.

> **MCP transport:** at credentials step 2, use only tools the Etherscan MCP server actually exposes in the current session. MCP is a partial interface, not a promise that every Etherscan API `module/action` has an equivalent tool. Do not pass a key—the MCP server supplies it. Every data-integrity, budget (Hard rule 8), and validation rule applies identically on all transports.

## MCP capability gate and fallback

The current Etherscan MCP contract (2026-08-12) uses task-native snake_case names. Before each new API operation, inspect the available MCP tool names and input schemas. Never construct or guess a tool name from raw HTTP documentation.

| Etherscan API operation | Current MCP tool | Flow usage |
|---|---|---|
| `account/balance` | `get_native_balance` | Native balance |
| `account/txlist` | `get_transactions` | Normal transactions by address |
| `account/txlistinternal` | `get_internal_transactions` | Internals by address or parent tx hash |
| `account/tokentx`, `account/tokennfttx`, `account/token1155tx` | `get_token_transfers` | Set `standard` to `erc20`, `erc721`, or `erc1155` |
| `nametag/getaddresstag` | `get_address_labels` | One address per MCP call; Pro Plus |
| `contract/getsourcecode` | `get_contract_source` | Verified source and compiler metadata |
| `contract/getabi` | `get_contract_abi` | Verified ABI |
| `contract/getcontractcreation` | `get_contract_creation` | Creator and creation tx for 1–5 contract addresses |
| `proxy/eth_getTransactionByHash` | `get_transaction_by_hash` | Full transaction object |
| `proxy/eth_getTransactionReceipt` | `get_transaction_receipt` | Status, gas, contract creation, and receipt logs |
| `transaction/gettxreceiptstatus` | `get_transaction_receipt_status` | Success/failure flag |
| `transaction/getstatus` | `get_transaction_status` | Execution error status |
| `logs/getlogs` | `get_logs` | Event logs by address/topics/block range |
| `block/getblocknobytime` | `get_block_by_timestamp` | Time-window block resolution |
| `/v2/chainlist` | `get_supported_chains` | Supported chain IDs |

Pass `chainid` explicitly as a numeric string (for example, `"1"`) to every chain-specific MCP call after chain resolution; `get_supported_chains` takes no `chainid`. The transaction proxy tools return JSON-RPC-shaped results where `null` means not found or pending, not a transport error.

Core transaction input shapes:

- `get_transaction_by_hash`: `{ txhash, chainid }`.
- `get_transaction_receipt`: `{ txhash, chainid }`.
- `get_logs`: `{ address?, fromblock?, toblock?, topic0?, topic1?, topic2?, topic3?, topic0_1_opr?, topic1_2_opr?, topic2_3_opr?, chainid, page?, offset? }`. Supply an address and/or at least one topic; `offset` is at most 1000.
- `get_transactions`, `get_internal_transactions`, and `get_token_transfers` use lowercase `startblock`, `endblock`, `page`, `offset`, and `sort`. `get_internal_transactions` accepts either `address` or `txhash`; `get_token_transfers.standard` is `erc20`, `erc721`, or `erc1155`.

The 16 legacy camelCase aliases are disabled by default. Never select or guess them when a current task-native tool is absent.

**Not in the current default MCP surface:** `proxy/eth_call`, `proxy/eth_getCode`, `proxy/eth_getBlockByNumber`, `proxy/eth_getStorageAt`, historical balance endpoints, and arbitrary proxy/RPC methods. `raw_rpc_call` is planned, not live—never call it until it appears in the session's tool list. Resolve these operations through the next source in the binding order.

- If an exact MCP tool exists and accepts the required inputs, use it.
- If a tool documented in the table is absent, the connected MCP server is stale, filtered, or older. Do not substitute the raw `module/action` or a legacy camelCase alias. Immediately continue through the binding order for this run: inline `apikey=`, `ETHERSCAN_API_KEY`, then local key file.
- If the tool exists but cannot express the required chain, hash/address, block range, topics, or pagination, MCP does not support that operation in this session; fall through the same way.
- Do not call a guessed MCP name, repeatedly search for the same missing tool, wait for it to appear, omit required receipt/log evidence, or abandon the run merely because another MCP tool worked earlier.
- A run may therefore be mixed-transport. For example, MCP may supply `get_transactions` and `get_transaction_by_hash`, while HTTP supplies `proxy/eth_call`. Keep one canonical query ledger keyed by the transport actually used and never refetch a held response through another transport.
- If no later HTTP key source resolves, ask once to refresh/reconnect the current MCP server or provide another Etherscan access source as specified in `SKILL.md`; do not hang.

## CLI transport — command table and behaviour (credentials step 1)

Require the production command contract before using this table:

1. Run `etherscan version`; accept `1.0.0` or newer.
2. Run `etherscan whoami`; it shows the active chain and a masked key. Treat `(none — run 'etherscan login')` as an unresolved CLI credential.
3. If the executable is older, either v1 command is absent, or `whoami` reports no credential, do not guess between legacy command shapes. Fall through in order to MCP, the current invocation's inline `apikey=`, `ETHERSCAN_API_KEY`, and then the local key-file source. If no fallback resolves, ask the user to install/update the official v1+ CLI and run `etherscan login`, or to provide another key source.

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

**`chainlist` on non-HTTP transports.** Production CLI v1 exposes `etherscan chains list`, which lists the chains built into that binary and costs no API call. Use the maintained common-chain table in `SKILL.md` without a live lookup. For a name or ID outside that table, issue the keyless `GET https://api.etherscan.io/v2/chainlist` (the live list is authoritative for unknown entries); accept status `1` (available) or `2` (degraded), record the `chain_degraded` gap required by *Chain resolution* for status `2`, and count that request against the 100-call budget. Treat status `0` or an absent entry as unsupported. If a resolved chain is absent from `etherscan chains list`, the installed CLI cannot address it. Fall through in the normal order to MCP and then HTTP backed by an inline `apikey=`, `ETHERSCAN_API_KEY`, or the local key file; do not extract the CLI's saved config key. If none resolves, ask the user to update the CLI or configure one of those fallbacks rather than substituting another chain.

Notes on CLI behaviour that the skill depends on:

- `--boolean false` is **required** on `eth_getBlockByNumber`; omitting it returns `json-rpc error -32700: parse error`.
- `nametag getaddresstag` accepts a **comma-separated address list of at most 100 addresses**. Batch the surviving Step 2 entity set into as few calls as possible, split at 100, and cache each batch.
- **Pagination.** Pass `--page` and `--offset` together for deterministic paging. Always loop pages manually, including Step 3B totals. Do not use `--all`: it returns one combined result rather than the raw response for each page, so the canonical query ledger cannot retain every response or count attempts exactly. Stop on a short page, the relevant tracing landmark, the 20-page per-address ceiling, or the 100-call run ceiling. Although v1's `--all` defaults to `--max-pages 20` and warns on truncation, those safeguards do not satisfy the fetch-log contract.
- **Advanced filters.** `txlist`, `txlistinternal`, `tokentx`, `tokennfttx`, and `token1155tx` accept `--from`, `--to`, and required `--fromto-opr and|or`. Do not combine these with the positional/`--address` filter. Use them only when the procedure needs a directed pair or claim-specific query; otherwise retain address-based paging so both inflows and outflows remain visible.
- **Round trips and rate ownership.** Production v1 applies its client-side limiter inside one process (default 3 requests/second), but separate manual-page invocations do not share it. Execute CLI commands sequentially and use one run-scoped launch gate: start successive CLI API commands at least 350 ms apart, counting process runtime toward that interval. Do not launch a parallel wave of subprocesses or pass the hidden `--rate-limit` override. Honor stderr retry/rate-limit signals and reduce subsequent work after a limit response. This gate mirrors the CLI's own default only; MCP and HTTP retain the adaptive wave behavior in `performance.md`.

If the CLI command fails because it is not installed, not logged in, cannot address the selected chain, or lacks a required endpoint, fall through for that operation to MCP and then the remaining key sources in the binding order. If it fails because the API returns an error, record that API error in `_meta.gaps` and continue where possible.

**Separate the two failure modes — they are different facts and they are not each other's evidence.**

| What happened | How to tell | What to record |
|---------------|-------------|----------------|
| The API answered "no" | The command ran and returned an error body: plan-gated (`API Exclusive endpoint`), `NOTOK`, rate limit, bad params | A blocked gap quoting that body verbatim, with the `endpoint` (`references/output-spec.md` → *`_meta.gaps` entries*). Do not fall through — the key is fine, this endpoint is not for it |
| The transport did not answer | Non-zero exit with no API body, binary missing, missing MCP tool, timeout, no key resolved | Fall through to the next transport/key source for that operation. Only if every source fails is it a blocked gap, quoting the transport's own error |

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
