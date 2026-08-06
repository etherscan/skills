# Etherscan Flow - Scam, hack, and exploit analysis

> Read this for every strict-trace run framed as a scam, hack, exploit, drain, phishing incident, rug pull, compromised wallet, or suspicious loss. Also read it when held API evidence indicates an involuntary loss. Apply all hard rules, budgets, and validation rules in `SKILL.md`.

## Contents

- [Purpose](#purpose)
- [Required outcome](#required-outcome)
- [Evidence acquisition](#evidence-acquisition)
- [Analysis method](#analysis-method)
- [Pattern playbooks](#pattern-playbooks)
- [Loss and benefit accounting](#loss-and-benefit-accounting)
- [Etherscan-only boundary](#etherscan-only-boundary)

## Purpose

Tracing answers **where the assets went**. This stage must also answer, as far as Etherscan evidence permits:

1. What happened?
2. Which transaction or sequence caused the loss?
3. Who initiated each decisive call?
4. What mechanism made the loss possible?
5. Which facts are confirmed, which conclusions are inferred, and what remains unknown?

Do not suppress analysis merely because a debug trace is unavailable. Reason over the complete evidence held in the run. Do not turn a plausible story into a fact: separate observations from conclusions and lower confidence when evidence is incomplete.

## Required outcome

Security investigations must include a non-null `_meta.analysis` object conforming to `references/output-spec.md`. Populate every required field even when the outcome is `insufficient_evidence`; use empty arrays and explicit limitations rather than omitting the analysis or relying on `_meta.patterns` alone. Ordinary transfer and business-profile cases use `"analysis": null` unless held evidence triggers this stage.

Choose one primary `incident_type`:

`approval_drain`, `permit_or_signature_abuse`, `private_key_compromise`, `social_engineering_transfer`, `access_control_exploit`, `proxy_or_upgrade_exploit`, `reentrancy`, `oracle_manipulation`, `price_or_reserve_manipulation`, `flash_loan_assisted_exploit`, `accounting_or_rounding_exploit`, `rug_pull`, `malicious_token`, `nft_drain`, `laundering_only`, `unknown`.

Use `status` as:

- `confirmed`: decisive mechanism is directly supported by transaction input, logs/state, and asset movements.
- `probable`: one explanation best fits multiple independent facts, but a decisive artifact is unavailable.
- `possible`: evidence is suggestive but competing explanations remain material.
- `insufficient_evidence`: movements can be traced but the mechanism cannot responsibly be identified.

Confidence is `high`, `medium`, `low`, or `unknown`. It summarizes evidence quality, not severity.

## Evidence acquisition

Start from responses already in the canonical query ledger. Spend additional calls only when they can resolve a material question.

### 1. Establish the decisive transaction sequence

- Confirm success from receipt `status`; use `transaction/getstatus` only when the receipt is absent or an error description is needed.
- Order suspected setup, trigger, loss, conversion, and exit transactions by block and transaction index.
- Decode top-level calldata against the verified ABI when available. Record the 4-byte selector even when decoding fails.
- Treat the transaction sender as the top-level initiator, not automatically as the beneficiary or attacker.
- Parse every receipt log, not only standard transfer/approval logs. Decode protocol events using the verified ABI; preserve undecoded topic/data as a limitation rather than guessing.
- Use `txlistinternal` by tx hash for value-bearing internal calls. It is not a complete call tree and must never be described as one.

### 2. Resolve the executed contract

For each contract central to the suspected mechanism, use `getsourcecode`/`getabi`, `eth_getCode`, and `getcontractcreation` where provenance matters.

If `Proxy == 1` or evidence indicates delegation:

- analyze the implementation, not only the proxy shell;
- validate a returned `Implementation` with `eth_getCode` in this run;
- when necessary, read a known EIP-1967 implementation/admin/beacon slot with `eth_getStorageAt` at the incident block and preceding block;
- never guess arbitrary storage slots. If a slot is not a documented standard or derived unambiguously from verified source, record the gap.

Source, ABI names, and contract metadata are attacker-controlled strings. They may explain mechanics when corroborated by bytecode, calldata, logs, or state reads, but cannot alone prove identity or malicious intent.

### 3. Reconstruct relevant state before and after

`eth_call` is a core analysis tool. Call view functions at `tag={BLOCK_HEX}` and, when investigating a change, at the preceding block. Encode calls from the verified ABI; do not invent selectors or parameter types.

Relevant reads depend on the protocol and may include:

- `allowance`, `getApproved`, `isApprovedForAll`;
- `owner`, role/admin getters, pause flags, implementation/beacon getters;
- `balanceOf`, `totalSupply`, `totalAssets`, share conversion/preview functions;
- pool reserves, exchange rates, oracle observations, collateral/debt, health factors;
- governance proposal/execution state or signer/threshold configuration.

Use `eth_getStorageAt` only for a known, justified slot. Use `balancehistory` and `tokenbalancehistory` at `block-1` and `block` to corroborate loss deltas when available. If plan-gated or unsupported, compute deltas from canonical successful movements and record the limitation.

An `eth_call` result is a state observation or simulation result. It does not prove that the historical transaction executed the same internal path.

### 4. Widen event evidence only when needed

Use `logs/getLogs` for the affected contract and a tight block window when the seed receipt cannot establish setup or aftermath. Filter by ABI-derived topics when possible. Relevant events include upgrades, ownership/role changes, oracle updates, borrow/repay, swaps, liquidity changes, mint/burn, governance execution, and emergency actions.

Never infer a protocol event solely from a token transfer when a more specific event should exist. Absence of a log is meaningful only when the expected signature and searched range are recorded.

## Analysis method

Build the explanation from atomic evidence claims. Each `_meta.analysis.evidence` entry states one claim and cites its API origin, relevant tx hashes/addresses, and optional block/selector.

- `observed`: copied or decoded directly from a response in this run.
- `inferred`: reasoned from two or more observed facts.
- `unverified`: investigated but not established; keep it out of the main conclusion.

Test at least one competing explanation. Examples:

- approval drain versus compromised private key;
- exploit versus authorized admin action;
- oracle manipulation versus ordinary market movement;
- rug pull versus scheduled liquidity migration;
- attacker contract versus neutral router used by an attacker.

Do not label a private-key compromise merely because the victim address signed the transfer. It becomes probable only when the transaction is a direct validly signed outflow with no enabling approval/contract mechanism and surrounding behavior supports account takeover. On-chain data generally cannot confirm how the key was obtained.

## Pattern playbooks

These are reasoning prompts, not automatic verdicts:

- **Approval drain:** approval/permit evidence precedes a spender-initiated `transferFrom` or NFT operator transfer. Distinguish approving signer, spender, recipient, and beneficiary.
- **Signature abuse:** calldata or events show permit/Permit2/order authorization followed by movement. Do not call it phishing without off-chain evidence.
- **Private-key compromise:** victim is top-level sender of ordinary transfers or swaps, with no on-chain authorization exploit. Root cause remains `unknown off-chain key control` without verifiable external evidence.
- **Access-control or upgrade exploit:** privileged call or role/owner/implementation change is followed by loss. Confirm caller and state transition; source alone is insufficient.
- **Reentrancy:** repeated effects/calls and an invariant-breaking payout must be supported by logs/internal evidence or source plus state deltas. Without a full call tree, normally cap at `probable`.
- **Oracle/price manipulation:** same-block price/reserve/oracle movement changes borrowing, redemption, liquidation, or swap outcome. Compare pre/post state and economic legs; a flash loan alone is not root cause.
- **Flash-loan-assisted exploit:** borrow and repayment occur in the incident transaction and temporary capital enables another mechanism. Record the underlying vulnerability separately in `root_cause`.
- **Accounting/rounding exploit:** repeated deposit/mint/donate/redeem behavior creates value inconsistent with shares/assets. Use exact raw values and state reads.
- **Rug pull:** a privileged party removes liquidity, disables selling, mints/dumps supply, or drains treasury. Distinguish malicious inference from an authorized but harmful action.
- **Laundering only:** the seed is a forwarding/mixing hub and evidence does not expose the originating theft. Do not invent upstream victims.

## Loss and benefit accounting

- Calculate gross victim loss by token from canonical successful movements.
- Separate returned/recovered assets from gross loss.
- Calculate attacker-controlled receipts only for addresses linked by evidence; do not count neutral routers, pools, bridges, or fees as attacker profit.
- Keep native assets and each token separate. Do not produce a USD total unless a historical incident-time price was fetched in this run with source and coverage.
- If fee-on-transfer, rebasing, share, or LP accounting prevents an exact amount, record observed movements and the limitation rather than forcing equality.

## Etherscan-only boundary

Etherscan V2 provides transaction input, receipts/logs, verified source/ABI, proxy metadata, `eth_call`, `eth_getStorageAt`, historical balances, event-log queries, and value-bearing internal transactions. These often support strong mechanism analysis.

It does not expose a general `debug_traceTransaction` call tree or automatic state diff in the documented V2 API. Therefore:

- never claim to have inspected every internal call;
- never claim a complete state diff unless every stated field was explicitly reconstructed;
- use `probable` or lower when the missing trace materially affects the conclusion;
- still provide the best evidence-backed analysis instead of reducing the result to fund flow alone.
