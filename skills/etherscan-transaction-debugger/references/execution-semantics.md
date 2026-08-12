# Execution Semantics

## Contents

- Call types
- Proxy attribution
- Logs, assets, and permissions
- Common patterns
- Evidence traps

## Call Types

- `CALL`: execute the callee's code in the callee's storage context; native value may move.
- `STATICCALL`: execute read-only code; state writes are forbidden.
- `DELEGATECALL`: execute the implementation's code in the caller's storage, address, and balance context while preserving the original message sender/value semantics for that frame.
- `CREATE` / `CREATE2`: create a contract; report the resulting address only when receipt or trace evidence supports it.

Describe the purpose of a frame only after resolving the callee, selector, ABI, source, or a well-supported protocol pattern.

## Proxy Attribution

Separate these roles:

- The address called by the user.
- The proxy that owns storage and emits logs.
- The implementation whose bytecode executed.
- The admin, beacon, or upgrade authority when relevant.

Use verified proxy metadata first. Confirm important cases with trace `DELEGATECALL` frames, verified source, or standard implementation slots when available. Do not infer a proxy relationship merely because two contracts share selectors.

For upgrades, distinguish an upgrade function call from proof that the implementation slot changed. Report the before/after implementation only when observed.

## Logs, Assets, and Permissions

Reconcile committed effects from the successful receipt and decoded logs:

- Native value from the top-level call and successful internal value transfers.
- ERC-20 `Transfer` values using token decimals from live token metadata or verified contract calls.
- ERC-721 transfers by token ID.
- ERC-1155 single and batch transfers by ID and amount.
- WETH-style deposit/withdraw events and corresponding native transfers.
- `Approval`, `ApprovalForAll`, permit-driven allowances, roles, ownership, and upgrade events.

Keep raw integer amounts when decimals or token standards are uncertain. State whether a number is gross flow or net change. Gas is paid by the transaction sender even when execution reverts.

An approval changes permission; it is not itself a token transfer. A permit signature may be consumed inside the transaction even when the top-level method is not named `permit`.

## Common Patterns

- **Router swap:** user or permit system funds a router/pool; callbacks can be expected settlement behavior.
- **Wrap/unwrap:** native asset and wrapped-token mint/burn events should reconcile.
- **Bridge:** source-chain lock/burn does not prove destination-chain receipt; destination confirmation requires separate evidence.
- **Multicall/batch:** top-level success can include optional child failures when caught; only a trace or explicit result data can prove the child behavior.
- **Account abstraction:** separate user operation intent from bundler transaction sender and EntryPoint execution.
- **Multisig:** separate proposal/authorization from the executed downstream call.
- **Contract creation:** constructor effects may appear under the created contract despite no normal destination address.
- **Selfdestruct or forced native transfer:** native balance changes may lack a conventional value-carrying call on modern traces/providers.

## Evidence Traps

- Logs describe emitted events, not every state change or call.
- A familiar selector can collide with another signature.
- A label is metadata, not proof of ownership or intent.
- Internal transaction endpoints are not guaranteed to contain every zero-value call, static call, delegate call, or reverted child.
- Net token movements alone may hide flash loans, fees, intermediate custody, or reverted attempts.
- A successful outer transaction does not prove every attempted child call succeeded.
