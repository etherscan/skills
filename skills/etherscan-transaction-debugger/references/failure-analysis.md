# Failure Analysis

## Contents

- Failure workflow
- Revert decoding
- Propagation and caught failures
- Root-cause language
- Reproduction guidance

## Failure Workflow

1. Confirm receipt status and gas use. Distinguish a mined revert from a pending, dropped, replaced, or not-found transaction.
2. Capture any Etherscan status description and raw revert data.
3. In Deep mode, find the deepest relevant failed frame, then follow propagation to the top. A deeper error is not necessarily the user-facing root cause if the caller catches or transforms it.
4. Resolve proxy storage context and implementation code before mapping the failure to source.
5. Decode the error against verified ABIs for the failing contract and relevant implementation.
6. Inspect the called function, arguments, return data, events before the failure, and source condition when available.
7. State the narrowest supported cause and the missing evidence that prevents greater precision.

## Revert Decoding

Recognize, without overclaiming:

- `Error(string)`: decode the string payload.
- `Panic(uint256)`: map the panic code, retain the numeric code, and identify the frame.
- Custom errors: match the 4-byte selector to a verified ABI and decode arguments.
- Empty or truncated data: report it as such; do not invent a reason.
- Out of gas: distinguish transaction gas exhaustion from a deliberately limited child call when trace gas fields support it.
- Invalid opcode or exceptional halt: identify only when the trace reports it.

Selector databases are hints. Prefer a verified ABI or source because selector collisions exist.

## Propagation and Caught Failures

A failed child frame may be:

- Propagated unchanged.
- Wrapped in a new error.
- Ignored after a low-level call returns `false`.
- Caught by `try/catch`.
- Expected as part of probing or fallback behavior.

Only Deep mode or explicit return/event evidence can reliably distinguish these cases. A successful receipt proves the outer transaction committed, not that every attempted child call succeeded.

## Root-Cause Language

Use one of these forms:

- **Confirmed:** “Frame X reverted with custom error Y; verified source maps it to condition Z.”
- **Strongly supported:** “The top-level revert data decodes to Y from implementation X, but no full trace is available.”
- **Possible:** “The available status suggests Y; the exact failing frame cannot be established without a trace.”
- **Unknown:** “The transaction reverted with no decodable error in the available evidence.”

Do not rewrite a protocol error into a more specific economic explanation unless arguments, state, or source support it.

## Reproduction Guidance

When requested, recommend a read-only reproduction at the historical block using the same sender, destination, value, calldata, and relevant state. Use simulation or tracing tools without signing or broadcasting. Note that pending-state, oracle, timestamp, MEV, and cross-chain conditions can make exact reproduction impossible.
