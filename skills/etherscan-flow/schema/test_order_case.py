from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "order_case.py"
SPEC = importlib.util.spec_from_file_location("order_case", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
ORDER_CASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORDER_CASE)


def node(node_id: str, hop: int) -> dict:
    return {"id": node_id, "hop": hop, "x": 0, "y": 0}


def edge(
    edge_id: str,
    source: str,
    target: str,
    timestamp=None,
    block=None,
    txhash=None,
    transaction_index=None,
    log_index=None,
    trace_id=None,
) -> dict:
    value = {
        "id": edge_id,
        "source": source,
        "target": target,
        "chainid": 1,
        "txhash": txhash or "0x" + edge_id[-1] * 64,
    }
    if timestamp is not None:
        value["timestamp"] = timestamp
    if block is not None:
        value["block"] = block
    if transaction_index is not None:
        value["transaction_index"] = transaction_index
    if log_index is not None:
        value["log_index"] = log_index
    if trace_id is not None:
        value["trace_id"] = trace_id
    return value


class OrderCaseTests(unittest.TestCase):
    def test_edges_are_sorted_by_timestamp(self):
        case = {
            "nodes": [node("seed01", 0), node("late01", 1), node("early01", 1)],
            "edges": [
                edge("edge2", "seed01", "late01", "2026-01-01T00:02:00Z", 10),
                edge("edge1", "seed01", "early01", "2026-01-01T00:01:00Z", 20),
            ],
        }

        ordered = ORDER_CASE.order_case(case)

        self.assertEqual(["edge1", "edge2"], [item["id"] for item in ordered["edges"]])

    def test_malformed_collections_are_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, "edges must be an array of objects"):
            ORDER_CASE.order_case({"nodes": [], "edges": ["not-an-edge"]})

    def test_single_chain_edges_fall_back_to_block_number(self):
        case = {
            "nodes": [node("seed01", 0), node("late01", 1), node("early01", 1)],
            "edges": [
                edge("edge2", "seed01", "late01", block="0x14"),
                edge("edge1", "seed01", "early01", block="0xa"),
            ],
        }

        ordered = ORDER_CASE.order_case(case)

        self.assertEqual(["edge1", "edge2"], [item["id"] for item in ordered["edges"]])
        self.assertEqual([10, 20], [item["block"] for item in ordered["edges"]])

    def test_same_transaction_logs_are_sorted_by_log_index(self):
        txhash = "0x" + "a" * 64
        case = {
            "nodes": [node("seed01", 0), node("first01", 1), node("second01", 1)],
            "edges": [
                edge(
                    "edge7",
                    "seed01",
                    "second01",
                    "2026-01-01T00:01:00Z",
                    10,
                    txhash,
                    "0x3",
                    "0x7",
                ),
                edge(
                    "edge2",
                    "seed01",
                    "first01",
                    "2026-01-01T00:01:00Z",
                    10,
                    txhash,
                    "0x3",
                    "0x2",
                ),
            ],
        }

        ordered = ORDER_CASE.order_case(case)

        self.assertEqual(["edge2", "edge7"], [item["id"] for item in ordered["edges"]])
        self.assertEqual([2, 7], [item["log_index"] for item in ordered["edges"]])
        self.assertEqual([3, 3], [item["transaction_index"] for item in ordered["edges"]])

    def test_same_block_transactions_are_sorted_by_transaction_index(self):
        case = {
            "nodes": [node("seed01", 0), node("first01", 1), node("second01", 1)],
            "edges": [
                edge(
                    "edge2",
                    "seed01",
                    "second01",
                    "2026-01-01T00:01:00Z",
                    10,
                    transaction_index=9,
                ),
                edge(
                    "edge1",
                    "seed01",
                    "first01",
                    "2026-01-01T00:01:00Z",
                    10,
                    transaction_index=2,
                ),
            ],
        }

        ordered = ORDER_CASE.order_case(case)

        self.assertEqual(["edge1", "edge2"], [item["id"] for item in ordered["edges"]])

    def test_same_transaction_internal_rows_use_hierarchical_trace_id(self):
        txhash = "0x" + "b" * 64
        case = {
            "nodes": [node("seed01", 0), node("first01", 1), node("second01", 1)],
            "edges": [
                edge("edge2", "seed01", "second01", block=10, txhash=txhash, trace_id="0_10"),
                edge("edge1", "seed01", "first01", block=10, txhash=txhash, trace_id="0_2"),
            ],
        }

        ordered = ORDER_CASE.order_case(case)

        self.assertEqual(["edge1", "edge2"], [item["id"] for item in ordered["edges"]])

    def test_layout_is_left_to_right_then_top_to_bottom(self):
        case = {
            "nodes": [
                node("late01", 1),
                node("seed01", 0),
                node("early01", 1),
                node("exit01", 2),
            ],
            "edges": [
                edge("edge3", "late01", "exit01", "2026-01-01T00:03:00Z", 30),
                edge("edge2", "seed01", "late01", "2026-01-01T00:02:00Z", 20),
                edge("edge1", "seed01", "early01", "2026-01-01T00:01:00Z", 10),
            ],
        }

        ordered = ORDER_CASE.order_case(case)
        nodes = {item["id"]: item for item in ordered["nodes"]}

        self.assertEqual((0, 0), (nodes["seed01"]["x"], nodes["seed01"]["y"]))
        self.assertEqual((360, 0), (nodes["early01"]["x"], nodes["early01"]["y"]))
        self.assertEqual((360, 180), (nodes["late01"]["x"], nodes["late01"]["y"]))
        self.assertEqual((720, 0), (nodes["exit01"]["x"], nodes["exit01"]["y"]))
        self.assertEqual(
            ["seed01", "early01", "late01", "exit01"],
            [item["id"] for item in ordered["nodes"]],
        )
        self.assertEqual(
            {
                "algorithm": "chronological_hops_v1",
                "direction": "left_to_right_top_to_bottom",
                "edge_order": "timestamp",
                "same_transaction_order": "transaction_edge_then_log_index_then_trace_id",
                "node_order": "hop_then_first_edge",
                "x_spacing": 360,
                "y_spacing": 180,
            },
            ordered["_meta"]["layout"],
        )


if __name__ == "__main__":
    unittest.main()
