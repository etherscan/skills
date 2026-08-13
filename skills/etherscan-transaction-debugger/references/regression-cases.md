# Regression Cases

Maintain public, non-sensitive hashes for each supported case and rerun them after workflow or script changes. Keep expected assertions factual and minimal so tests do not rot with labels or presentation changes.

## Standard Cases

- Successful native transfer with no logs.
- Successful ERC-20 transfer.
- ERC-721 and ERC-1155 transfers.
- Approval without an asset transfer.
- Router swap with callback and fee.
- Wrap and unwrap transaction.
- Contract deployment.
- Verified proxy using `DELEGATECALL`.
- Proxy upgrade with confirmed implementation change.
- Batch or multicall with several effects.
- Account-abstraction transaction.
- Bridge source transaction with no assumed destination result.

## Failure Cases

- `Error(string)` revert.
- `Panic(uint256)` revert.
- Verified custom error.
- Empty revert data.
- Failed child propagated to the top.
- Failed child caught by a successful parent.
- Out-of-gas or exceptional halt supported by trace evidence.

## Assertions

For every case, check:

- Correct chain and receipt status.
- Exact raw values, deterministic execution gas fee, and conservative total-fee availability when chain-specific components are missing.
- No invented labels, names, decimals, or errors.
- No complete-call-tree claim in Standard mode.
- Committed and attempted effects remain distinct.
- Proxy and implementation roles are correct.
- Explorer links use the right host.
- Confidence matches evidence depth.

Do not embed API keys, authenticated RPC URLs, private transactions, or personal user data in regression fixtures.
