# Etherscan Flow — Output: Step 4B validation and the Step 5 JSON schema

> Part of the `etherscan-flow` skill. MANDATORY read before writing any case JSON — never write the file from memory of this schema. Every Hard rule, the 100-call budget, and the validation rules in `SKILL.md` apply here unchanged.

## Contents

- [Lossless amount arithmetic](#lossless-amount-arithmetic)
- [Step 4B — Pre-output validation](#step-4b--pre-output-validation)
- [Step 5 — Write JSON output](#step-5--write-json-output)
- [`_meta.gaps` entries](#meta-gaps-entries)

## Lossless amount arithmetic

Treat amounts as digit strings, not general-purpose numbers. This applies to edge `amount`, node `balance`, merged totals, `_meta.financials`, business totals, and incident-analysis asset amounts.

1. Keep an API decimal `value` as its non-negative integer string. For a proxy hex `value`, decode it with an arbitrary-precision integer only; never via a floating-point or fixed-precision decimal type.
2. Keep the scale separately: 18 for Ethereum ETH/wei, or the API-verified token `tokenDecimal`. If the scale is unresolved, emit `null`; never guess it.
3. Format `raw` at scale `d` by left-padding it to at least `d + 1` digits and inserting a decimal point `d` digits from the right. Strip redundant leading integer zeros and trailing fractional zeros; if all raw digits are zero, emit `"0"`.
4. Sum or subtract amounts only as raw arbitrary-precision integers with the same token contract and scale. For merged edges, sum raw units first and format once. Never add already-formatted values with `float`, JavaScript `Number`, `parseFloat`, `Decimal`/`BigDecimal`, database `DECIMAL`/`NUMERIC`, or equivalent casts.
5. Emit the result as a quoted plain-decimal JSON string. Exponents (`9.2695e-14`), numeric JSON values, rounding, truncation, and fixed display precision are forbidden. If `raw > 0`, the formatted result must compare textually unequal to `"0"`.

Examples:

| Raw integer string | Decimals | Exact JSON string |
|---|---:|---|
| `92695` | 18 | `"0.000000000000092695"` |
| `1` | 18 | `"0.000000000000000001"` |
| `1000000` | 6 | `"1"` |
| `1234500` | 6 | `"1.2345"` |

Use the bundled `python scripts/exact_amount.py format RAW DECIMALS` and `python scripts/exact_amount.py sum DECIMALS RAW...` commands whenever Python is available. The helper uses strings plus arbitrary-precision integers and never imports or casts through a decimal/floating type. If Python is unavailable, reproduce steps 1–5 exactly in the available language; do not substitute ordinary numeric conversion.

## Step 4B — Pre-output validation

Before writing any JSON, check every node and edge against these rules. Fix or drop offending entries — do not emit them.

| Check | Rule | Action on failure |
|-------|------|-------------------|
| No NaN / undefined | Every numeric or string field must be a valid value or explicit `null` | Replace with `null`, note in gaps |
| No placeholder data | No placeholder/non-hex addresses, no illustrative-only nodes, no estimated business-flow edges, no empty-string `txhash`, and no `"no_live_data"` case | Stop and ask for a real tx hash/address; do not write JSON |
| Edge has txhash | Every edge must reference a real `txhash` from an API response, normalized from API `hash`, receipt/log `transactionHash`, or the validated seed `{TXHASH}` | Backfill `txhash` from the verified source field; if none exists, drop edge and note in gaps |
| Node has chainid | Every node must include `chainid` as an integer for the chain resolved in this run (maintained common-chain table or live `chainlist`; see *Chain resolution*). For single-chain cases, use the run's `{CHAINID}`. | Add the run's `{CHAINID}` when the node was fetched on that chain; drop or split ambiguous nodes |
| Edge has chainid | Every edge must include `chainid` as an integer for the chain resolved in this run. The edge `chainid` must be the chain where `txhash` was fetched. | Add the source API call's `{CHAINID}`; if unknown, drop the edge and note in gaps |
| Edge endpoints match the tx | The txhash's transaction must support `source → target`: tx `from`/`to` match, or an internal tx / token-transfer log in it moves value source → target. Deploy edges: tx `from` = deployer, receipt `contractAddress` = deployed contract. **Mint/burn edges use the zero address `0x0000000000000000000000000000000000000000` as the counterparty exactly as the `Transfer` log records it — `mint` → `source` = zero address, `burn` → `target` = zero address. The emitting token/vault contract is never the endpoint; putting it there makes the edge fail on-chain validation because the log's real `from`/`to` is the zero address.** | Correct endpoints from API data — for a mint point `source` at the zero address, for a burn point `target` at it — or drop the edge and note in gaps |
| Amount is exact decimal string | Amounts follow *Lossless amount arithmetic*: quoted plain-decimal strings produced from raw integer units without numeric/decimal casts, rounding, truncation, or exponents. Every positive raw value remains non-zero | Recompute from the raw API string; if it is unavailable, use `null` rather than `0` |
| Address is valid hex | Every `address` field is a valid 42-char `0x…` hex string | Drop the node, note in gaps |
| ENS/name stored separately | ENS names, exchange display names, project aliases, or second-line labels are in `label`/`subLabel`, never `address` | Move display text to `label` or `subLabel`; keep only the verified 0x address in `address` |
| No duplicate movements | Deduplicate only when the exact same API movement was fetched through more than one query. A tx hash identifies a transaction, not every movement inside it: use `(chainid, txhash)` for a top-level normal tx, `(chainid, txhash, logIndex)` for event-log/token movements, and `(chainid, txhash, traceId)` for internal movements. If an endpoint provides no stable movement index, compare the complete normalized source row rather than dropping same-tx movements. | Remove exact source duplicates, then perform Step 5 edge merging |
| Merged edges are consistent | If an edge merges several txs (`txcount` > 1), its `txhash` is the earliest tx in the group, `amount` is the summed decimal total, and `edge.txhashes` lists every distinct merged hash (earliest first, so `txhashes[0] === txhash`) | Recompute, or split the edge |
| Token symbol resolved | If symbol is unknown after tokentx lookup, write `null` not an empty string or guess | Use `null` |
| Token identified by address | Every ERC-20 edge **must** carry `token_address` = the emitting contract's `contractAddress` (the token's true identity; symbols can be spoofed *or shared* — two vaults can both report `LVUSDC`). The on-chain validator binds by `token_address` when present and otherwise falls back to a symbol match that fails on any collision, so a missing `token_address` silently breaks validation for mint/burn and vault-share edges. Keep `token` the bare symbol (Hard rule 22) — never a compound label like `"LVUSDC (LowerRisk)"`. Native-coin edges omit `token_address` | Backfill from the `tokentx` row / `Transfer` log `address`; move any parenthetical qualifier out of `token` into the node `label`/`subLabel` |
| Hops 0-indexed | Every seed/scope address is `hop: 0`; no node exceeds the run's depth | Recompute `hop` from distance to the nearest seed |
| Balance not fabricated | `balance` is a real figure from an `account`/`balance` response in this run, or `null` | Replace an unfetched balance with `null` |
| Tracer strings sanitized | Every tracer-authored string — node/edge fields, case `name`, and tracer-owned `_meta` fields (timeline, gaps and their quoted `claim` text, patterns, candidates, business_profile prose) — contains no HTML tags or control characters, each ≤ 200 chars (Hard rule 5). The tracer never emits the reserved `_meta.ui` namespace. | Strip and truncate |
| No API key | The apikey string appears nowhere in the JSON | Remove it |
| Evidence-backed roles | Every `attacker_eoa`/`scam_contract`/`victim_wallet` role has API evidence, not just a user claim | Downgrade to `unknown_*?`, note in gaps |
| Security analysis present | Every scam/hack/exploit/drain/phishing/rug-pull/compromised-wallet case, and every run where evidence indicates involuntary loss, has a non-null `_meta.analysis` with every required field | Complete `references/incident-analysis.md`; if the mechanism remains unknown, use `insufficient_evidence` and state the limitations |
| Analysis status matches its evidence | A `confirmed`/`probable`/`possible` status cites at least one `evidence` entry and at least one `alternative_hypotheses` entry; `confirmed` additionally requires at least one `observed` claim; `insufficient_evidence` states at least one limitation | Supply the missing evidence or hypothesis, or lower `status` until it matches what the evidence supports |
| Analysis evidence is traceable | Every `observed` evidence claim identifies at least one API source and cites the relevant txhash/address/block/selector where available; every cited txhash/address came from this run | Remove unsupported citations, downgrade the claim/status/confidence, and record the gap |
| Analysis accounting is grounded | Every analysis loss/profit decimal is computed from canonical successful movements; tokens remain separate, and neutral routers/pools/fees are not counted as attacker profit | Recompute or omit the asset row and add a limitation |
| Performance counters reconcile | `new_api_calls` counts successful new requests, `network_attempts` also includes retries, cache/fetch-log hits are separate, and no credential appears in metrics | Recompute counters from the query ledger |
| Attempted gaps name their call | Every `*_unavailable` / `*_incomplete` / `*_empty` gap names the `endpoint` it called, and quotes the verbatim `error` if the call returned one. A blocker you never attempted is not a gap, and its `endpoint` must appear in the query ledger / fetch log for this run | Make the call. If it succeeds, use the data and delete the gap; if it fails, quote the real error; if you chose not to call it, reclassify as `scope_limited` with the reason |
| Totals declare their coverage | No summed figure may span a window that was not fully paginated. Mode B carries `_meta.business_profile.totals.coverage` (0D-3a) with sums computed over `effective_window`; strict-mode `_meta.financials` truncated by the page cap or budget carries `"coverage_complete": false` and a `totals_truncated` gap | Recompute the sums over the range actually covered, then set coverage — never emit a partial sum as if it were whole |

For cross-endpoint duplicates, decoded receipt logs are canonical. When a `tokentx`, `tokennfttx`, or `token1155tx` row describes a movement already represented by a receipt log from the same `chainid` and `txhash`, use the account-feed row only to verify or fill token metadata; do not add another movement. Never collapse two canonical receipt logs merely because their source, target, token, and amount match — distinct `logIndex` values are distinct movements.

---

## Step 5 — Write JSON output

Save `case-{SHORT_ID}-flow.json` using the **Etherscan Flow Case** schema. This is the **only** output — no chat summary, no prose.

> The machine-checkable form of this contract is [`schema/case.schema.json`](../schema/case.schema.json), with a validating fixture in [`examples/strict-trace.example.json`](../examples/strict-trace.example.json). CI validates the fixture on every push. When you change a field, an enum value, or a required key below, update the schema in the same commit so the two never drift.

- `SHORT_ID` — see Hard rule 7 for the exact derivation (seed tx hash, else seed address, else the lexicographically smallest scope address). Never derive it from free-form user text.
- Directory: the platform's temp/scratchpad directory if one exists, otherwise `./cases/`. The user cannot override the path.

Node `id` values must be short unique alphanumeric strings (2–12 chars, e.g. `subj01`, `atk01`, `cex01`). Edge `id` values follow the same convention (e.g. `e_atk_cex`). Tracer output sets `x` and `y` to `0`; Etherscan Flow may later persist user-edited numeric coordinates when the case is saved or exported. Every node and edge must include `chainid`; for single-chain cases this equals `_meta.chainid`, and for future multi-chain cases it preserves the chain context for each address and tx hash.

### Field conventions

- **`hop` is 0-indexed from the seed.** Seed/scope addresses are `hop: 0`; addresses one transfer away are `hop: 1`, and so on. Hop values therefore run `0 … depth`, so the default depth of 2 (Step 0) yields hops 0, 1, and 2. In Mode B, every validated scope address is `hop: 0` regardless of how many there are.
- **`balance` is optional and frequently `null`.** Steps 2 and 0D-2 fetch `balance` only when it is needed as evidence, so most nodes will not have one. Write `null` when it was not fetched — never `0`, never `"0.0"`, and never a guess (a fabricated `"0.0"` reads as a drained wallet).
- **`subLabel` is optional** — `null` when there is no ENS name or second-line alias.
- **`_meta.chains`** lists every chain that contributed a node or edge to this case, as `{ "chain": name, "chainid": int }` objects. For a single-chain case it holds exactly one entry, matching `_meta.chain` / `_meta.chainid`. It exists so a consumer can read the case's chain scope without walking every node.
- **`_meta.financials`** is where all financial totals live (Step 3B). There is no top-level `financials` key; the top level is exactly `id`, `name`, `schemaVersion`, `nodes`, `edges`, `_meta`.
- **`_meta.analysis`** is `null` for ordinary cases and a required structured forensic conclusion for security cases. `_meta.patterns` remains a compact index of detected patterns; it never replaces the evidence, confidence, competing hypotheses, and limitations in `_meta.analysis`.
- **`_meta.ui` is reserved for Etherscan Flow.** The tracer does not emit it. After a user edits Case Findings, Etherscan Flow stores the displayed Markdown at `_meta.ui.findings_markdown` while preserving `_meta.analysis`. This user-authored Markdown may contain newlines and exceed the tracer's 200-character field limit; the schema caps `findings_markdown` at 1,048,576 Unicode characters (not bytes), while the whole-document byte size is a separate limit the application enforces. Older root `findings`, `_meta.findings_markdown`, and structured `_meta.ui.findings` are migration inputs, not new tracer output fields; a structured `_meta.ui.findings` is still fully sanitized (HTML tags/control chars stripped, each string ≤ 200 chars) — only `findings_markdown` is exempt.

### Edge merging

Repeated movements between the same pair collapse into one edge. First remove only exact duplicate source movements using Step 4B; then merge the remaining rows whose `(chainid, source, target, token, type)` all match. A DAO paying one vendor 200 times in USDC is a single edge, not 200 parallel ones, and two legitimate transfer logs in one transaction both contribute to the merged amount. On the merged edge:

- `txcount` = number of distinct merged `txhash` values, not the number of movement rows.
- `txhash` = the **earliest** tx in the group. It is a real hash from this run and must still pass the Step 4B endpoint check (Hard rule 10).
- `txhashes` = **every** distinct merged hash — including the earliest — once each, in ascending block order, so `txhashes[0] === txhash`. Each entry is a real hash from this run (Hard rule 10 applies to all of them). Cap at 100 hashes per edge; if the group is larger, keep the earliest 100, keep the true `txcount`, and add `edge_txhashes_truncated` to `_meta.gaps`.
- `amount` = sum the raw smallest-unit integers across all deduplicated movement rows, then format once with *Lossless amount arithmetic*. Do not sum formatted decimal values.
- `timestamp` = the earliest tx's timestamp.

Single-tx edges (`txcount` = 1) may omit `txhashes` or write it as the one-element `[txhash]`. The legacy `_meta.edge_txhashes` map is superseded by `edge.txhashes` — do not emit it.

Two rows that differ in `token` or `type` never merge, even within one transaction — that is what keeps both legs of a swap.

**Valid `role` values for nodes:**
`wallet` `erc20_token` `nft_contract` `defi_pool` `multisig` `staking_contract` `lending_protocol` `dao_contract` `attacker_eoa` `scam_contract` `victim_wallet` `intermediate_wallet` `cex_deposit` `dex_router` `mixer_contract` `bridge` `nft_drainer_contract` `sweeper_bot` `unknown_eoa` `unknown_contract`

> **Output the `role` field as exactly one of the bare values above — never append `?` or any other suffix in the JSON.** The `?` used in earlier steps is an internal reasoning marker only. When a role is unproven, emit the closest `unknown_*` value and record the uncertainty in the node's `notes` and in `_meta.gaps` (Hard rule 3). A `?`-suffixed role is not a valid enum value and will not render.

**Valid `type` values for edges:**
`transfer` `token_transfer` `dex_swap` `bridge` `nft` `approve` `contract_call` `mint` `burn` `stake` `unstake` `borrow` `repay` `liquidity_add` `liquidity_remove`

```json
{
  "id": "case-{SHORT_ID}",
  "name": "0x{SHORT_ADDR}… — {one-line description}",
  "schemaVersion": 1,
  "nodes": [
    {
      "id": "subj01",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chainid": 1,
      "label": "Subject",
      "subLabel": "alice.eth",
      "role": "unknown_eoa",
      "hop": 0,
      "balance": "12.5",
      "notes": "Seed address",
      "x": 0,
      "y": 0
    },
    {
      "id": "atk01",
      "address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
      "chainid": 1,
      "label": "Attacker EOA",
      "subLabel": null,
      "role": "attacker_eoa",
      "hop": 1,
      "balance": null,
      "notes": "Created 3 days before drain",
      "x": 0,
      "y": 0
    }
  ],
  "edges": [
    {
      "id": "e_subj_atk",
      "source": "subj01",
      "target": "atk01",
      "amount": "5000",
      "token": "USDT",
      "token_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "txcount": 1,
      "type": "token_transfer",
      "txhash": "0x...",
      "txhashes": ["0x..."],
      "chainid": 1,
      "timestamp": "2024-03-15T10:23:00Z"
    }
  ]
}
```

Every edge object must include the `txhash` and `chainid` fields exactly as shown above. If the API row used `hash` or `transactionHash`, rename/copy it to `txhash` in the output edge. Set `edge.chainid` to the `{CHAINID}` used for the API call that returned that tx hash. Merged edges (`txcount` > 1) must also carry `txhashes` with every merged hash (see *Edge merging*); the canvas shows the full list and its on-chain validator checks each one.

For any ERC-20 movement, also set `edge.token_address` to the emitting token's **contract address** — the `contractAddress` field of the `tokentx` row (or the `Transfer` log's `address`). A symbol alone is not an identity: anyone can deploy a look-alike contract with the same `token` symbol, so the on-chain validator treats a symbol-only edge as ambiguous when two same-symbol contracts moved between the endpoints. Emitting `token_address` binds the amount to one contract and lets it verify. Use `null`/omit for native-coin edges (ETH, BNB, POL…), where `token` is the gas coin and value lives in `tx.value`.

`balance` and `amount` are **exact bare decimal strings** with no unit suffix, exponent, or raw wei — `"12.5"`, never `"12.5 ETH"`, `"1.25e1"`, or `"12500000000000000000"`. Preserve arbitrarily small positive values (for example, `"0.000000000000092695"`) and use `null`, not `"0"`, when unresolved. The unit is the chain's native coin for `balance`, and the edge's `token` for `amount`.

> **AI soft layer**: `label`, `subLabel`, `role`, and `notes` on each node are LLM-assigned from API evidence. All `address`, `chainid`, `txhash`, `amount`, `token`, `timestamp` fields are API-sourced or run-parameter sourced only — never fabricated. `subLabel` is optional and is the right place for an ENS name, alias, or second-line display name; it must never replace `address`.

Also append a `_meta` block after the nodes/edges:

```json
{
  "id": "case-{SHORT_ID}",
  "name": "...",
  "schemaVersion": 1,
  "nodes": [...],
  "edges": [...],
  "_meta": {
    "created_at": "{ISO_TIMESTAMP}",
    "mode": "strict_trace",
    "chain": "ethereum",
    "chainid": 1,
    "chains": [
      { "chain": "ethereum", "chainid": 1 }
    ],
    "seed_txhashes": ["0x..."],
    "seed_addresses": ["0x..."],
    "hops_traced": 2,
    "trace_window": {
      "startblock": 0,
      "endblock": 0,
      "start_timestamp": "2024-03-15T10:23:00Z",
      "end_timestamp": "2024-03-22T10:23:00Z",
      "days": 7,
      "source": "seed_tx"
    },
    "financials": {},
    "analysis": {
      "status": "confirmed",
      "incident_type": "approval_drain",
      "summary": "A spender used an earlier approval to transfer the victim's token.",
      "attack_vector": "ERC-20 allowance abuse",
      "root_cause": "The spender retained sufficient allowance at the loss transaction.",
      "confidence": "high",
      "decisive_txhashes": ["0x..."],
      "evidence": [
        {
          "claim": "Loss tx is a transferFrom moving 5000 USDC from victim to spender.",
          "kind": "observed",
          "sources": ["proxy/eth_getTransactionReceipt"],
          "txhashes": ["0x..."],
          "addresses": ["0x{VICTIM}", "0x{SPENDER}"],
          "block": 19420000,
          "selector": "0x23b872dd"
        },
        {
          "claim": "Allowance set 3 days earlier best explains the spender-initiated move.",
          "kind": "inferred",
          "sources": ["account/txlist", "proxy/eth_call"],
          "txhashes": ["0x..."],
          "addresses": ["0x{SPENDER}"],
          "block": 19420000,
          "selector": null
        }
      ],
      "losses_by_token": [
        {
          "token": "USDC",
          "token_address": "0x{TOKEN}",
          "gross_amount": "5000",
          "returned_or_recovered": "0",
          "net_amount": "5000"
        }
      ],
      "attacker_profit_by_token": [
        {
          "token": "USDC",
          "token_address": "0x{TOKEN}",
          "gross_amount": "5000",
          "returned_or_recovered": "0",
          "net_amount": "5000"
        }
      ],
      "alternative_hypotheses": [
        {
          "hypothesis": "The victim signed the transfer themselves (key compromise).",
          "assessment": "unlikely",
          "evidence_against": ["Loss tx sender is the spender, not the victim."],
          "evidence_for": []
        }
      ],
      "limitations": ["No debug trace available; internal call tree not inspected."]
    },
    "business_profile": null,
    "performance": {
      "profile": "standard",
      "new_api_calls": 0,
      "network_attempts": 0,
      "cache_hits": 0,
      "fetchlog_hits": 0,
      "retries": 0,
      "rate_limit_responses": 0,
      "pages_fetched": 0,
      "pages_reused": 0,
      "soft_call_target": 40,
      "hard_call_limit": 100,
      "elapsed_ms": 0,
      "stage_elapsed_ms": {
        "seed": 0,
        "classification": 0,
        "trace": 0,
        "totals": 0,
        "analysis": 0,
        "validation": 0
      },
      "soft_budget_overrun_reason": null
    },
    "timeline": [],
    "patterns": [],
    "candidates": [],
    "gaps": [],
    "disclaimer": "Roles, labels and notes are AI inference over public Etherscan API data — not Etherscan verdicts, accusations, or legal findings."
  }
}
```

## Meta gaps entries

Every gap is an object. `type` and `detail` are always required; `endpoint` and `error` are required for the blocked types below. Use `detail` — never `note`, `reason`, or another synonym.

```json
{
  "type": "source_unavailable",
  "detail": "Provider implementation source could not be read; classification fell back to bytecode.",
  "endpoint": "contract/getsourcecode",
  "error": "Sorry, it looks like you are trying to access an API Exclusive endpoint."
}
```

**Attempted types — `endpoint` required, plus verbatim `error` whenever the call returned one:** `source_unavailable`, `nametag_unavailable`, `historical_state_unavailable`, `internal_txs_empty`, and any other `*_unavailable` / `*_incomplete` / `*_empty` type. These assert that you called something and it did not give you what you needed, so they must name what you called.

Not every failed call errors. A call can return `200 OK` and still be useless — `proxy/eth_call` ignoring a historical block tag, or `account/txlistinternal` returning zero rows. Then there is no `error` to quote: give the `endpoint` and describe in `detail` what came back instead. Omit `error` rather than inventing one.

**Detail-only types:** `scope_limited`, `unresolved_entity`, `unverified_claim`, `mechanism_uncertainty`, `timeframe_limited`, `chain_unsupported`, `chain_degraded`, `edge_txhashes_truncated`, `budget_exhausted`, `totals_truncated`. These record a choice, provider status, or an internal limit, not a call that failed. `budget_exhausted` and `totals_truncated` are evidenced by `_meta.performance` counters, not by an endpoint.

Use these type names as written — they are the vocabulary. Do not coin a synonym for a type that already exists.

A blocked gap is a claim about the outside world, and it is load-bearing: it justifies a fallback, a lower `_meta.analysis.confidence`, and a narrower trace. So it carries the same burden of proof as an `observed` evidence claim — quote what the transport actually said, exactly as it said it.

Three rules follow from that:

- **Never infer a blocker from a sibling.** One endpoint being plan-gated says nothing about a different endpoint. `nametag/getaddresstag` is Pro Plus on many keys while `contract/getsourcecode` is free — a plan error on the first is not evidence about the second. Attempt each endpoint you intend to report as blocked.
- **Distinguish "the API said no" from "the transport broke."** An API error with a response body (plan-gated, rate-limited, `NOTOK`) is a fact you quote. A transport that never returned is a different failure with a different error. Do not describe the first as the second.
- **A choice is not a blocker.** Stopping at a high-volume node, or at the hop depth, is `scope_limited` with a reason — not `*_unavailable`. Reserve blocked types for calls you made and that failed.

When no error string exists because the call was never made, there is no gap to write. Make the call, or say plainly that you did not.

Print the full path to the JSON file at the end of your reply.

---
