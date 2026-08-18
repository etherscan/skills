#!/usr/bin/env python3
"""Chronologically order an Etherscan Flow case and assign a stable canvas layout."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


HORIZONTAL_SPACING = 360
VERTICAL_SPACING = 180
MAX_TIMESTAMP = dt.datetime.max.replace(tzinfo=dt.timezone.utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="Etherscan Flow Case JSON file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write to another path instead of updating the input file",
    )
    return parser.parse_args()


def parse_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        try:
            parsed = int(value, 16) if value.lower().startswith("0x") else int(value, 10)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def parse_trace_id(value: Any) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not value:
        return None
    parts = value.split("_")
    if any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def transaction_sort_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    transaction_index = parse_nonnegative_int(edge.get("transaction_index"))
    return (
        transaction_index if transaction_index is not None else sys.maxsize,
        str(edge.get("txhash") or ""),
    )


def movement_sort_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    """Order rows within one transaction without claiming cross-source execution order."""
    log_index = parse_nonnegative_int(edge.get("log_index"))
    if log_index is not None:
        return (1, (log_index,))
    trace_id = parse_trace_id(edge.get("trace_id"))
    if trace_id is not None:
        return (2, trace_id)
    return (0, ())


def edge_sort_key(edge: dict[str, Any], strategy: str) -> tuple[Any, ...]:
    timestamp = parse_timestamp(edge.get("timestamp"))
    block = parse_nonnegative_int(edge.get("block"))
    chainid = edge.get("chainid") if isinstance(edge.get("chainid"), int) else sys.maxsize
    transaction = transaction_sort_key(edge)
    movement = movement_sort_key(edge)
    edge_id = str(edge.get("id") or "")
    if strategy == "timestamp":
        return (
            timestamp,
            chainid,
            block if block is not None else sys.maxsize,
            *transaction,
            *movement,
            edge_id,
        )
    if strategy == "block":
        return (block, chainid, *transaction, *movement, timestamp or MAX_TIMESTAMP, edge_id)
    if timestamp is not None:
        return (
            0,
            timestamp,
            chainid,
            block if block is not None else sys.maxsize,
            *transaction,
            *movement,
            edge_id,
        )
    if block is not None:
        return (1, chainid, block, *transaction, *movement, edge_id)
    return (2, chainid, *transaction, *movement, edge_id)


def chronology_strategy(edges: list[dict[str, Any]]) -> str:
    if edges and all(parse_timestamp(edge.get("timestamp")) is not None for edge in edges):
        return "timestamp"
    chainids = {edge.get("chainid") for edge in edges if isinstance(edge.get("chainid"), int)}
    if len(chainids) <= 1 and edges and all(parse_nonnegative_int(edge.get("block")) is not None for edge in edges):
        return "block"
    return "mixed"


def order_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with chronological edges and deterministic node coordinates."""
    ordered = copy.deepcopy(case)
    edges = ordered.get("edges", [])
    nodes = ordered.get("nodes", [])
    if not isinstance(edges, list) or any(not isinstance(edge, dict) for edge in edges):
        raise ValueError("case edges must be an array of objects")
    if not isinstance(nodes, list) or any(not isinstance(node, dict) for node in nodes):
        raise ValueError("case nodes must be an array of objects")

    for edge in edges:
        for field in ("block", "transaction_index", "log_index"):
            if field in edge:
                edge[field] = parse_nonnegative_int(edge.get(field))

    strategy = chronology_strategy(edges)
    edges.sort(key=lambda edge: edge_sort_key(edge, strategy))
    ordered["edges"] = edges

    first_flow_rank: dict[str, int] = {}
    for rank, edge in enumerate(edges):
        for endpoint in (edge.get("source"), edge.get("target")):
            if isinstance(endpoint, str):
                first_flow_rank.setdefault(endpoint, rank)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        hop = node.get("hop") if isinstance(node.get("hop"), int) else sys.maxsize
        grouped.setdefault(hop, []).append(node)

    laid_out: list[dict[str, Any]] = []
    for hop in sorted(grouped):
        column = sorted(
            grouped[hop],
            key=lambda node: (
                first_flow_rank.get(str(node.get("id")), sys.maxsize),
                str(node.get("id") or ""),
            ),
        )
        for row, node in enumerate(column):
            node["x"] = hop * HORIZONTAL_SPACING if hop != sys.maxsize else 0
            node["y"] = row * VERTICAL_SPACING
            laid_out.append(node)

    ordered["nodes"] = laid_out
    meta = ordered.setdefault("_meta", {})
    if not isinstance(meta, dict):
        raise ValueError("case _meta must be an object when present")
    meta["layout"] = {
        "algorithm": "chronological_hops_v1",
        "direction": "left_to_right_top_to_bottom",
        "edge_order": strategy,
        "same_transaction_order": "transaction_edge_then_log_index_then_trace_id",
        "node_order": "hop_then_first_edge",
        "x_spacing": HORIZONTAL_SPACING,
        "y_spacing": VERTICAL_SPACING,
    }
    return ordered


def main() -> int:
    args = parse_args()
    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read case JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(case, dict):
        print("error: case JSON root must be an object", file=sys.stderr)
        return 1

    destination = args.output or args.case
    try:
        ordered = order_case(case)
    except ValueError as exc:
        print(f"error: cannot order case: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write ordered case JSON: {exc}", file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
