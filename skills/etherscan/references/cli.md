# Etherscan CLI reference

Use this reference to discover syntax from the installed CLI and service semantics from the corresponding live Etherscan documentation. Do not treat this file as a fixed command inventory.

## Use this interface when

- Working interactively in a terminal.
- Building scripts, pipelines, or structured exports.
- Troubleshooting the behavior of the CLI version installed in the current environment.

## Live authorities

Use the narrowest applicable authority, in this order:

1. The installed CLI's top-level, group-level, and command-specific `--help` output for current command names, arguments, flags, defaults, and output options.
2. The installed CLI's reported version and the matching [Etherscan CLI repository](https://github.com/etherscan/etherscan-cli) release or source when version-specific behavior matters.
3. The [official CLI guide](https://docs.etherscan.io/ai/cli.md) for installation, setup, and supported integration patterns.
4. The exact live API endpoint page for service semantics, chain support, plan access, limits, pagination, and response behavior of an API-backed command.
5. [CLI GitHub Issues](https://github.com/etherscan/etherscan-cli/issues) or [Etherscan support](https://etherscan.io/contactus?id=11) when the installed help and official documentation do not resolve the problem.

Built-in help is authoritative for terminal syntax. The exact endpoint page is authoritative for API behavior.

## Discover current behavior

1. Confirm which `etherscan` executable and version are available in the current environment.
2. Inspect `etherscan --help`, then the relevant group and command help. Do not construct a command from a remembered inventory.
3. Resolve the target chain using names or IDs accepted by the installed version; use its current chain-discovery mechanism rather than guessing.
4. Select a structured or human-readable output mode only from the options advertised by current help.
5. For API-backed commands, locate the corresponding live endpoint documentation and verify plan access, chain restrictions, throttling, pagination, and response semantics.
6. Run the narrowest safe command, inspect both standard output and diagnostics, and preserve truncation or partial-result warnings.

## Durable constraints

Use the generic command shape only as orientation; confirm every concrete token with live help:

```text
etherscan [global options] <group> <command> [arguments] [options]
```

- Keep the API key in the CLI's supported secret configuration or an environment variable such as `ETHERSCAN_API_KEY`. Never place a real key in examples, prompts, logs, committed files, or reported output.
- Use identity or configuration inspection that masks secrets; never print or copy the CLI credential store.
- Prefer a structured output mode advertised by the installed version for agents and pipelines. Use a tabular export mode only when the returned data is actually tabular.
- Treat pagination, maximum-page behavior, retries, pacing, exit codes, and stdout/stderr conventions as version-specific until confirmed by current help.
- Avoid wrapping the CLI in uncontrolled retry loops. Preserve warnings even when a command returns usable rows or a successful exit code.
- Require explicit authorization before commands that submit verification, broadcast signed data, delete configuration, or otherwise change external or local state.

## If verification fails

- If the CLI is unavailable, do not invent command syntax; provide the official installation or repository authority instead.
- If installed help is unavailable or inconsistent with the documentation, report the detected version and the unresolved difference.
- Do not guess current commands, flags, defaults, limits, supported chains, or output behavior.
- Do not run a state-changing command whose syntax, payload, chain, or effect cannot be verified.
