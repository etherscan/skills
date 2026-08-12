#!/usr/bin/env python3
"""Derive auditable transaction facts from a collector evidence bundle."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
APPROVAL_FOR_ALL = "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31"
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize exact status, gas, native value, common token events, permissions, and evidence limitations."
    )
    parser.add_argument("bundle", type=Path, help="JSON bundle from collect_transaction_data.py")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")
    return parser.parse_args()


def integer(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 16) if value.lower().startswith("0x") else int(value, 10)
        except ValueError:
            return None
    return None


def address_from_topic(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    raw = value.lower().removeprefix("0x")
    if len(raw) != 64:
        return None
    return "0x" + raw[-40:]


def data_words(value: Any) -> list[int]:
    if not isinstance(value, str):
        return []
    raw = value.lower().removeprefix("0x")
    if not raw or len(raw) % 64:
        return []
    try:
        return [int(raw[index : index + 64], 16) for index in range(0, len(raw), 64)]
    except ValueError:
        return []


def iso_timestamp(value: Any) -> str | None:
    timestamp = integer(value)
    if timestamp is None:
        return None
    try:
        return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def receipt_succeeded(receipt: dict[str, Any]) -> bool | None:
    status = integer(receipt.get("status"))
    if status is None:
        return None
    return status == 1


def decode_log(log: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    topics = log.get("topics") or []
    if not isinstance(topics, list) or not topics or not isinstance(topics[0], str):
        return None, None
    topic0 = topics[0].lower()
    contract = str(log.get("address", "")).lower()
    words = data_words(log.get("data"))
    log_index = integer(log.get("logIndex"))

    if topic0 == TRANSFER:
        if len(topics) >= 4:
            return {
                "standard": "ERC-721-like",
                "contract": contract,
                "from": address_from_topic(topics[1]),
                "to": address_from_topic(topics[2]),
                "token_id": integer(topics[3]),
                "log_index": log_index,
            }, None
        if len(topics) >= 3 and words:
            return {
                "standard": "ERC-20-like",
                "contract": contract,
                "from": address_from_topic(topics[1]),
                "to": address_from_topic(topics[2]),
                "raw_value": words[0],
                "log_index": log_index,
            }, None

    if topic0 == TRANSFER_SINGLE and len(topics) >= 4 and len(words) >= 2:
        return {
            "standard": "ERC-1155",
            "contract": contract,
            "operator": address_from_topic(topics[1]),
            "from": address_from_topic(topics[2]),
            "to": address_from_topic(topics[3]),
            "token_id": words[0],
            "raw_value": words[1],
            "log_index": log_index,
        }, None

    if topic0 == TRANSFER_BATCH and len(topics) >= 4:
        return {
            "standard": "ERC-1155 batch",
            "contract": contract,
            "operator": address_from_topic(topics[1]),
            "from": address_from_topic(topics[2]),
            "to": address_from_topic(topics[3]),
            "raw_data": log.get("data"),
            "log_index": log_index,
        }, None

    if topic0 == APPROVAL:
        if len(topics) >= 4:
            return None, {
                "standard": "ERC-721-like",
                "contract": contract,
                "owner": address_from_topic(topics[1]),
                "approved_address": address_from_topic(topics[2]),
                "token_id": integer(topics[3]),
                "log_index": log_index,
            }
        if len(topics) >= 3 and words:
            return None, {
                "standard": "ERC-20-like",
                "contract": contract,
                "owner": address_from_topic(topics[1]),
                "spender": address_from_topic(topics[2]),
                "raw_value": words[0],
                "unlimited_candidate": words[0] == (2**256 - 1),
                "log_index": log_index,
            }

    if topic0 == APPROVAL_FOR_ALL and len(topics) >= 3 and words:
        return None, {
            "standard": "ERC-721/1155-like",
            "contract": contract,
            "owner": address_from_topic(topics[1]),
            "operator": address_from_topic(topics[2]),
            "approved": bool(words[0]),
            "log_index": log_index,
        }
    return None, None


def add_address(values: set[str], value: Any) -> None:
    if isinstance(value, str) and value.lower().startswith("0x") and len(value) == 42:
        values.add(value.lower())


def summarize(bundle: dict[str, Any]) -> dict[str, Any]:
    transaction = bundle.get("transaction") if isinstance(bundle.get("transaction"), dict) else {}
    receipt = bundle.get("receipt") if isinstance(bundle.get("receipt"), dict) else {}
    internals = bundle.get("internal_transactions") if isinstance(bundle.get("internal_transactions"), list) else []
    success = receipt_succeeded(receipt)
    gas_used = integer(receipt.get("gasUsed"))
    gas_price = integer(receipt.get("effectiveGasPrice"))
    gas_fee = gas_used * gas_price if gas_used is not None and gas_price is not None else None
    value = integer(transaction.get("value")) or 0

    native_movements: list[dict[str, Any]] = []
    if success and value:
        native_movements.append(
            {
                "kind": "top-level",
                "from": transaction.get("from"),
                "to": transaction.get("to") or receipt.get("contractAddress"),
                "raw_value_wei": value,
            }
        )
    if success:
        for item in internals:
            if not isinstance(item, dict) or str(item.get("isError", "0")) == "1":
                continue
            internal_value = integer(item.get("value")) or 0
            if internal_value:
                native_movements.append(
                    {
                        "kind": "internal-record",
                        "from": item.get("from"),
                        "to": item.get("to") or item.get("contractAddress"),
                        "raw_value_wei": internal_value,
                        "call_type": item.get("type"),
                        "trace_id": item.get("traceId"),
                    }
                )

    transfers: list[dict[str, Any]] = []
    permissions: list[dict[str, Any]] = []
    for log in receipt.get("logs", []) or []:
        if not isinstance(log, dict):
            continue
        transfer, permission = decode_log(log)
        if transfer:
            transfers.append(transfer)
        if permission:
            permissions.append(permission)

    addresses: set[str] = set()
    for key in ("from", "to"):
        add_address(addresses, transaction.get(key))
    add_address(addresses, receipt.get("contractAddress"))
    for movement in native_movements + transfers + permissions:
        for key in (
            "contract",
            "from",
            "to",
            "owner",
            "spender",
            "operator",
            "approved_address",
        ):
            add_address(addresses, movement.get(key))

    warnings = list(bundle.get("collection_warnings") or [])
    warnings.append(
        "Etherscan internal transaction records are partial execution evidence, not a guaranteed complete call trace."
    )
    if success is False:
        warnings.append(
            "The transaction reverted; attempted trace effects are not committed asset or permission changes. Gas remains paid."
        )
    if any(item.get("standard") == "ERC-20-like" for item in transfers):
        warnings.append(
            "ERC-20-like values are raw integers until token standard and decimals are confirmed from live metadata."
        )
    if any(item.get("standard") == "ERC-1155 batch" for item in transfers):
        warnings.append("ERC-1155 batch arrays remain raw ABI data and require ABI decoding.")

    return {
        "schema_version": "1.0",
        "transaction_hash": bundle.get("transaction_hash") or transaction.get("hash"),
        "chain": bundle.get("chain"),
        "status": "success" if success is True else "failed" if success is False else "unknown",
        "sender": transaction.get("from"),
        "destination": transaction.get("to"),
        "created_contract": receipt.get("contractAddress"),
        "block_number": integer(receipt.get("blockNumber") or transaction.get("blockNumber")),
        "block_timestamp": iso_timestamp(transaction.get("blockTimestamp")),
        "input_selector": str(transaction.get("input", ""))[:10] if transaction.get("input") else None,
        "raw_native_value_wei": value,
        "gas_used": gas_used,
        "effective_gas_price_wei": gas_price,
        "gas_fee_wei": gas_fee,
        "native_movements": native_movements,
        "token_transfer_events": transfers,
        "permission_events": permissions,
        "address_inventory": sorted(addresses),
        "execution_status": bundle.get("execution_status"),
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read evidence bundle: {exc}", file=sys.stderr)
        return 1
    if not isinstance(bundle, dict):
        print("error: evidence bundle root must be a JSON object", file=sys.stderr)
        return 1
    rendered = json.dumps(summarize(bundle), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
