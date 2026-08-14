# Evidence Collection

## Contents

- Collection order
- Etherscan CLI
- Fallbacks
- Chain and links
- Deep traces
- Evidence bundle contract

## Collection Order

Collect the smallest evidence set that can answer the question, then deepen only when needed:

1. Transaction by hash.
2. Receipt and execution status.
3. Internal transaction records.
4. ABI, verified source, proxy metadata, and labels for important addresses.
5. Trace data for complete or ambiguous execution analysis.

Retrieve live data. Never reuse addresses, amounts, labels, or conclusions from examples as evidence.

Treat Etherscan as both the primary structured-data source and the human verification surface. Preserve enough context to explain which Etherscan capability established each important fact: canonical transaction fields, receipt status, decoded input, logs, token transfers, internal transactions, verified contract source and ABI, proxy metadata, or labels.

## Etherscan CLI

Confirm the installed syntax with `etherscan --help` and subcommand `--help`; CLI releases can change. Typical Standard-mode commands are:

```text
etherscan proxy eth_getTransactionByHash <hash> --chain <chain> --output json
etherscan proxy eth_getTransactionReceipt <hash> --chain <chain> --output json
etherscan proxy eth_getBlockByNumber --tag <hex-block-number> --boolean false --chain <chain> --output json
etherscan transaction status <hash> --chain <chain> --output json
etherscan transaction receipt-status <hash> --chain <chain> --output json
etherscan account txlistinternal --txhash <hash> --all --chain <chain> --output json
etherscan contract getabi <address> --chain <chain> --output json
etherscan contract getsourcecode <address> --chain <chain> --output json
```

Prefer the bundled collector:

```text
python scripts/collect_transaction_data.py <hash> --chain <chain> --output evidence.json
python scripts/collect_transaction_data.py <hash> --chain <chain> --include-contracts --output evidence.json
python scripts/summarize_transaction.py evidence.json --output summary.json
```

The collector applies a 30-second timeout to each CLI request by default; adjust it with `--cli-timeout` when needed. The CLI can use its saved login, `ETHERSCAN_API_KEY`, or an explicit flag. Never print, store in the bundle, or repeat the API key.

## Fallbacks

When the CLI is unavailable, use an available Etherscan MCP/API integration or the correct explorer page. Collect equivalent raw fields and record the source. If only a rendered explorer page is available, do not imply raw trace or ABI coverage that was not inspected.

Treat `null`, empty lists, rate-limit responses, unsupported-chain errors, and unverified-contract responses differently. Absence from a failed request is not evidence of absence onchain.

## Chain and Links

Prefer an explicit chain or chain-specific URL. Otherwise query likely chains or ask when ambiguity affects the result. Record both a human-readable chain name and chain ID when known.

Build links only after resolving the explorer host. Common Etherscan-family paths are:

- Transaction: `/tx/<hash>`
- Address or contract: `/address/<address>`
- Token: `/token/<address>`

Do not assume every supported EVM chain uses `etherscan.io` as its explorer host.

Prefer descriptive links in the final report. State what each page helps the user verify, for example transaction outcome, verified source, implementation relationship, token movement, or address context. Link only evidence that was actually used or materially helps inspection.

## Deep Traces

Use a trace-capable RPC or provider for a complete call tree. Suitable trace methods depend on the node and provider, commonly `debug_traceTransaction` with a call tracer or `trace_transaction`.

Record:

- Provider or RPC source without secrets.
- Trace method and tracer configuration.
- Whether reverted frames are included.
- Whether state diffs, logs, return data, and errors are included.

Never send API keys or authenticated RPC URLs to output. Redact secrets before saving artifacts.

## Evidence Bundle Contract

The collector writes:

- `schema_version`
- `collected_at`
- `source`
- `chain`
- `transaction_hash`
- `transaction`
- `receipt`
- `block`
- `execution_status`
- `receipt_status`
- `internal_transactions`
- `contracts` with verified source metadata and its returned ABI when requested
- `collection_warnings`

Preserve raw values. Add derived calculations to a separate `derived` object so facts remain auditable.
