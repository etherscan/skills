# Etherscan Flow — Business/entity profile mode: Step 0D

> Part of the `etherscan-flow` skill. Read this when Mode B was selected (a DAO / protocol / project / company asked about as a business). ENS resolution is in `references/ens-resolution.md`; Steps 1–4 are in `references/trace-steps.md`. Every Hard rule, the 100-call budget, and the validation rules in `SKILL.md` apply here unchanged.

## Mode B output requirements

Business/entity profile mode must produce:

- A `_meta.business_profile` object with `entity_name`, `scope_addresses`, `income_categories`, `spending_categories`, `totals`, `plain_english_summary`, and `confidence_notes`.
- Nodes for the verified entity addresses and major counterparties.
- Edges only for real transfers, token transfers, internal transfers, or contract calls with a real `txhash`.
- Totals only from paginated API rows fetched in this run, with timeframe and budget limits stated in `_meta.gaps`.

## Step 0D — Business/entity profile mode

Use this when the user wants to understand a DAO/protocol/project as a business: where money comes from, how much came in, where money goes, and how much was spent.

### 0D-1. Resolve the entity scope

Build a candidate address list in this order:

1. **Prompt addresses.** Extract every valid `0x...` address from the user prompt.
2. **Prompt ENS names.** If the prompt contains ENS names, resolve them through Step 0E. Never put the ENS name in an `address` field.
3. **Known entity scope table.** If the entity name exactly matches an entry in the maintained table below, add those candidate addresses.
4. **No candidates.** If the list is empty, stop and ask once: "Which treasury, timelock, controller, registrar, multisig, or revenue addresses should I include for this entity?"

Every candidate is still only a hypothesis until validated by API data in this run.

### 0D-2. Validate candidate addresses

Validate candidates in evidence waves rather than issuing a fixed five-call checklist. Start with the two independent activity probes below and reuse them if already in the query ledger:

```
GET https://api.etherscan.io/v2/api?chainid={CHAINID}&module=account&action=txlist&address={ADDRESS}&startblock=0&endblock=99999999&page=1&offset=25&sort=desc&apikey={APIKEY}
GET https://api.etherscan.io/v2/api?chainid={CHAINID}&module=account&action=tokentx&address={ADDRESS}&page=1&offset=25&sort=desc&apikey={APIKEY}
```

If neither probe confirms the candidate, or contract/EOA type is needed, call `eth_getCode`. Call `balance` only when current balance is requested or required in output. For a confirmed contract, call `getsourcecode` only when identity/business-role evidence remains unresolved:

```
GET https://api.etherscan.io/v2/api?chainid={CHAINID}&module=proxy&action=eth_getCode&address={ADDRESS}&apikey={APIKEY}
GET https://api.etherscan.io/v2/api?chainid={CHAINID}&module=account&action=balance&address={ADDRESS}&tag=latest&apikey={APIKEY}
GET https://api.etherscan.io/v2/api?chainid={CHAINID}&module=contract&action=getsourcecode&address={ADDRESS}&apikey={APIKEY}
```

Use one batched nametag wave for surviving candidates if available. Stop validating once sufficient API evidence confirms existence and scope confidence; do not spend balance/sourcecode calls mechanically. Include a candidate only if at least one API response confirms it. Unsupported table labels remain hypotheses in `notes` and confidence notes.

### 0D-3. Choose the business window

**Any period the user expresses wins** — not only an explicit `2024-01-01 → 2024-03-31` range, but any period language: "last year", "in 2025", "since launch", "this quarter", "over the past 6 months". Resolve it to `{WINDOW_START_TIMESTAMP}` / `{WINDOW_END_TIMESTAMP}` and use it. "Since launch" resolves to the earliest activity timestamp across the validated scope addresses.

Only when the user expresses **no** period at all: inspect the validated scope addresses' recent transaction rows, take the latest confirmed activity timestamp as `{WINDOW_END_TIMESTAMP}`, and set `{WINDOW_START_TIMESTAMP}` to **7 days** earlier. If no scope address has a transaction or transfer row, no edge can survive Step 4B: stop without writing a case.

Seven days is deliberately short. Within a 100-call budget a wide window on a busy entity cannot be paginated to the end, and a **silently truncated sum is worse than a narrow complete one** — a partial total still reads to the user as "this DAO's revenue". A short window that is fully covered is a true statement; a wide window that is 30% covered is a false one. Do not widen the default to make the number look bigger.

Because the default is narrow, the window is a headline fact, not a footnote: state it in `_meta.trace_window`, in `_meta.business_profile.timeframe`, as the **first sentence** of `plain_english_summary`, and in the case `name` (e.g. `"ENS DAO — income and spending, 7 days to 2026-07-14"`). Add `timeframe_limited` to `_meta.gaps` whenever the window does not cover the entity's full history — which, for a default-window run, is always.

Step 3 converts these timestamps to block numbers once for the run.

### 0D-3a. Coverage — never report a total you did not finish summing

Totals pages are fetched `sort=asc` from `{WINDOW_START_TIMESTAMP}`, so when pagination stops early (20-page cap, 100-call budget, high-volume address), you have **completely** covered the window from its start up to the last row you fetched, and covered nothing after. That sub-range is a fact you can report; the full window is not.

So when any scope address truncates:

1. Take `{COVERED_END}` = the **earliest** "last fetched row" timestamp across all truncated scope addresses. Before that instant, every scope address is fully paginated; after it, at least one has a hole.
2. The `effective_window` is `{WINDOW_START_TIMESTAMP}` → `{COVERED_END}`.
3. **Compute every figure in `totals` over the `effective_window` only** — you already hold those rows, so this costs no calls. Drop rows after `{COVERED_END}` from the sums rather than letting a half-paginated address contribute a partial tail.
4. Record the coverage honestly and add `totals_truncated` to `_meta.gaps`.

Nodes and edges may still show movements after `{COVERED_END}` — they are individually real and evidence-backed. Only the **summed** figures are restricted to the `effective_window`, because a sum is a claim about a period and the others are not.

Emit `totals.coverage` on every Mode B case, including complete ones:

```json
"coverage": {
  "complete": false,
  "requested_window": { "start": "2026-07-07T00:00:00Z", "end": "2026-07-14T00:00:00Z" },
  "effective_window": { "start": "2026-07-07T00:00:00Z", "end": "2026-07-11T04:12:00Z" },
  "truncated_addresses": ["0x253553366Da8546fC250F225fe3d25d0C782303b"],
  "reason": "page_cap"
}
```

`reason` is one of `page_cap`, `budget_exhausted`, `high_volume_address`, or `null` when `complete` is `true`. When `complete` is `true`, `effective_window` equals `requested_window`.

Every total is therefore either complete over the window it names, or explicitly not. There is no third state.

### 0D-4. Classify income and spending

For each validated scope address, reuse compatible activity/Step 3 pages from the query ledger, then fetch only missing continuation pages. Use `offset=100`, the same block window, and `sort=asc` so totals pages remain reusable. Classify rows:

| Direction | Category | Rule |
|-----------|----------|------|
| Inbound | `user_revenue` | Many inbound payments from diverse wallets into a controller/revenue contract, or ETH/token value accompanying user-facing contract calls |
| Inbound | `treasury_funding` | Inbound transfer to a treasury, multisig, timelock, or DAO contract |
| Inbound | `unknown_income` | Money came in, but API evidence does not support a business purpose |
| Outbound | `treasury_spending` | Outbound transfer from treasury/multisig/timelock |
| Outbound | `grant_or_contributor_payment` | Repeated outbound payments to wallets/contracts that look like program or contributor payments; mark uncertain unless labels support it |
| Outbound | `vendor_or_service_payment` | Outbound payments to named vendor/service addresses from nametag/sourcecode evidence |
| Outbound | `market_or_treasury_management` | DEX, bridge, CEX, liquidity, custody, or treasury-management movements |
| Outbound | `unknown_spending` | Money went out, but API evidence does not support a business purpose |

### 0D-5. Summarize business profile inside JSON

Populate `_meta.business_profile`:

```json
{
  "entity_name": "ENS DAO",
  "mode": "business_entity_profile",
  "timeframe": "API-derived range or user-requested range",
  "scope_addresses": [
    {
      "address": "0x...",
      "chainid": 1,
      "label": "Treasury / registrar / controller / timelock",
      "evidence": "sourcecode, nametag, balance, txlist, tokentx, or known table validated by API",
      "confidence": "high|medium|low"
    }
  ],
  "income_categories": [],
  "spending_categories": [],
  "totals": {
    "coverage": {
      "complete": true,
      "requested_window": { "start": "…", "end": "…" },
      "effective_window": { "start": "…", "end": "…" },
      "truncated_addresses": [],
      "reason": null
    },
    "inbound_by_token": {},
    "outbound_by_token": {},
    "net_by_token": {}
  },
  "plain_english_summary": [],
  "confidence_notes": []
}
```

`totals.coverage` is required (0D-3a). `plain_english_summary[0]` states the window and whether the totals are complete over it — a reader who sees only the first sentence must not come away with a wrong impression of what the numbers mean.

Then continue to Step 2, Step 3, Step 4, Step 4B, and Step 5 with the validated scope addresses as seeds. Every validated scope address is `hop: 0` (`references/output-spec.md`).

Assign node roles from the **structural roles** table in Step 2 (`references/trace-steps.md`) — a validated treasury timelock, governor, or registrar/controller is a `dao_contract` or `multisig`, not an `unknown_contract`. Do not use scam-specific labels unless the API evidence supports them.

### Maintained known entity scopes

This table is optional and conservative. Entries are candidate scopes, not final truth. Each address must still be validated through Etherscan API calls in this run before it appears in the JSON. Match entity names case-insensitively against the entity key and its aliases.

| Entity key | Aliases | Chain | Candidate scope |
|------------|---------|-------|-----------------|
| `ENS DAO` | `ENS`, `Ethereum Name Service`, `ensdao.eth` | Ethereum mainnet (chainid 1) | See ENS DAO candidate list below |

**ENS DAO candidates (chainid 1).** Every address below is a hypothesis until Step 0D-2 validates it in this run. Step 2's `nametag` (when available) is authoritative: if it disagrees with the expected identity, trust the nametag; if validation fails outright, drop the candidate and add `scope_candidate_failed` to `_meta.gaps`. Never present a table label as verified in the output — confidence comes from this run's API evidence only.

| Candidate address | Expected identity | Business relevance |
|-------------------|-------------------|--------------------|
| `0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7` | ENS: DAO Wallet — treasury timelock (contract) | Treasury funding and spending |
| `0x253553366Da8546fC250F225fe3d25d0C782303b` | ETHRegistrarController (2023+) (contract) | User revenue — .eth registrations/renewals |
| `0x283Af0B28c62C092C9727F1Ee09c02CA627EB7F5` | ENS: Legacy ETH Registrar Controller (contract) | Historical user revenue (pre-2023) |
| `0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85` | ENS: Base Registrar — .eth NFT (contract) | Registry infrastructure |
| `0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72` | ENS: Token — $ENS (contract) | Governance token flows |
| `0x323A76393544d5ecca80cd6ef2A560C6a395b7E3` | ENS: Governor (contract) | Proposal execution |
| `0x690F0581eCecCf8389c223170778cD9D029606F2` | ENS: Cold Wallet (verify via nametag before labeling) | Treasury reserves |

When adding a new entity to this table, follow the same discipline as the landmark table: prefer addresses confirmed by a `nametag` hit or the entity's own published documentation, record the expected identity so Step 0D-2 has something concrete to check, and never add a row you could not defend if the label were wrong.

---
