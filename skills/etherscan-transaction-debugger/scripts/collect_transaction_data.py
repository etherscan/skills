#!/usr/bin/env python3
"""Collect a reproducible Etherscan transaction evidence bundle."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


TX_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class CollectionError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect transaction, receipt, status, internal operations, and optional contract metadata through the Etherscan CLI."
    )
    parser.add_argument("transaction_hash", help="0x-prefixed 32-byte transaction hash")
    parser.add_argument("--chain", default="1", help="Etherscan chain name or chain ID (default: 1)")
    parser.add_argument("--include-contracts", action="store_true", help="Fetch ABI and source metadata for discovered destination contracts")
    parser.add_argument("--max-contracts", type=int, default=12, help="Maximum discovered addresses to query for contract metadata (default: 12)")
    parser.add_argument("--etherscan-bin", default="etherscan", help="Etherscan CLI executable (default: etherscan)")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")
    return parser.parse_args()


def run_json(executable: str, args: list[str], chain: str, required: bool) -> tuple[Any, str | None]:
    command = [executable, *args, "--chain", chain, "--output", "json"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "unknown CLI error").strip()
        if required:
            raise CollectionError(f"{' '.join(args[:2])} failed: {message}")
        return None, f"{' '.join(args[:2])} failed: {message}"
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as exc:
        if required:
            raise CollectionError(f"{' '.join(args[:2])} returned invalid JSON: {exc}") from exc
        return None, f"{' '.join(args[:2])} returned invalid JSON: {exc}"


def add_address(values: list[str], seen: set[str], value: Any) -> None:
    if not isinstance(value, str) or not ADDRESS_RE.fullmatch(value):
        return
    normalized = value.lower()
    if normalized not in seen:
        seen.add(normalized)
        values.append(normalized)


def discover_addresses(transaction: Any, receipt: Any, internals: Any) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    sender = transaction.get("from", "").lower() if isinstance(transaction, dict) else ""

    if isinstance(transaction, dict):
        add_address(values, seen, transaction.get("to"))
    if isinstance(receipt, dict):
        add_address(values, seen, receipt.get("contractAddress"))
        for log in receipt.get("logs", []) or []:
            if isinstance(log, dict):
                add_address(values, seen, log.get("address"))
    if isinstance(internals, list):
        for item in internals:
            if not isinstance(item, dict):
                continue
            add_address(values, seen, item.get("to"))
            candidate = item.get("from")
            if isinstance(candidate, str) and candidate.lower() != sender:
                add_address(values, seen, candidate)
    return values


def collect_contracts(
    executable: str,
    chain: str,
    addresses: list[str],
    max_contracts: int,
    warnings: list[str],
) -> dict[str, Any]:
    contracts: dict[str, Any] = {}
    for address in addresses[:max_contracts]:
        source, source_warning = run_json(
            executable, ["contract", "getsourcecode", address], chain, required=False
        )
        abi, abi_warning = run_json(
            executable, ["contract", "getabi", address], chain, required=False
        )
        entry: dict[str, Any] = {}
        if source is not None:
            entry["source_metadata"] = source
        if abi is not None:
            entry["abi"] = abi
        local_warnings = [value for value in (source_warning, abi_warning) if value]
        if local_warnings:
            entry["warnings"] = local_warnings
        contracts[address] = entry
    if len(addresses) > max_contracts:
        warnings.append(
            f"Contract metadata capped at {max_contracts} of {len(addresses)} discovered addresses."
        )
    return contracts


def main() -> int:
    args = parse_args()
    tx_hash = args.transaction_hash.lower()
    if not TX_HASH_RE.fullmatch(tx_hash):
        print("error: transaction_hash must be 0x followed by 64 hexadecimal characters", file=sys.stderr)
        return 2
    if args.max_contracts < 0:
        print("error: --max-contracts cannot be negative", file=sys.stderr)
        return 2
    executable = shutil.which(args.etherscan_bin)
    if executable is None:
        print(f"error: Etherscan CLI executable not found: {args.etherscan_bin}", file=sys.stderr)
        return 2

    warnings: list[str] = []
    try:
        transaction, _ = run_json(
            executable, ["proxy", "eth_getTransactionByHash", tx_hash], args.chain, required=True
        )
        receipt, _ = run_json(
            executable, ["proxy", "eth_getTransactionReceipt", tx_hash], args.chain, required=True
        )
        if transaction is None or receipt is None:
            raise CollectionError("transaction or receipt was null; verify the chain and confirmation state")
        execution_status, warning = run_json(
            executable, ["transaction", "status", tx_hash], args.chain, required=False
        )
        if warning:
            warnings.append(warning)
        receipt_status, warning = run_json(
            executable, ["transaction", "receipt-status", tx_hash], args.chain, required=False
        )
        if warning:
            warnings.append(warning)
        internals, warning = run_json(
            executable,
            ["account", "txlistinternal", "--txhash", tx_hash],
            args.chain,
            required=False,
        )
        if warning:
            warnings.append(warning)
            internals = []
    except CollectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    bundle: dict[str, Any] = {
        "schema_version": "1.0",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"type": "etherscan-cli", "executable": executable},
        "chain": str(args.chain),
        "transaction_hash": tx_hash,
        "transaction": transaction,
        "receipt": receipt,
        "execution_status": execution_status,
        "receipt_status": receipt_status,
        "internal_transactions": internals if isinstance(internals, list) else [],
        "collection_warnings": warnings,
    }

    if args.include_contracts:
        addresses = discover_addresses(transaction, receipt, bundle["internal_transactions"])
        bundle["discovered_contract_addresses"] = addresses
        bundle["contracts"] = collect_contracts(
            executable, args.chain, addresses, args.max_contracts, warnings
        )

    rendered = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
