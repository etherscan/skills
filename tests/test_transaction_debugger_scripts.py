from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "etherscan-transaction-debugger" / "scripts"


def load_script(name: str) -> ModuleType:
    path = SCRIPT_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def address_topic(address: str) -> str:
    return "0x" + ("0" * 24) + address.removeprefix("0x")


class TransactionDebuggerScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.collector = load_script("collect_transaction_data")
        cls.summarizer = load_script("summarize_transaction")

    def test_collector_requests_current_cli_json_output(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"result": "ok"}', stderr=""
        )
        with patch.object(self.collector.subprocess, "run", return_value=completed) as run:
            result, warning = self.collector.run_json(
                "etherscan",
                ["proxy", "eth_getTransactionByHash", "0x" + ("1" * 64)],
                "1",
                required=True,
            )

        self.assertEqual(result, {"result": "ok"})
        self.assertIsNone(warning)
        self.assertEqual(
            run.call_args.args[0][-4:], ["--chain", "1", "--output", "json"]
        )
        self.assertEqual(run.call_args.kwargs["timeout"], 30.0)

    def test_collector_turns_timeout_into_a_warning_for_optional_calls(self) -> None:
        with patch.object(
            self.collector.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd=["etherscan"], timeout=5),
        ):
            result, warning = self.collector.run_json(
                "etherscan",
                ["transaction", "status"],
                "1",
                required=False,
                timeout_seconds=5,
            )

        self.assertIsNone(result)
        self.assertEqual(warning, "transaction status timed out after 5 seconds")

    def test_collector_normalizes_empty_auto_paginated_list(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with patch.object(self.collector.subprocess, "run", return_value=completed):
            result, warning = self.collector.run_json(
                "etherscan",
                ["account", "txlistinternal", "--txhash", "0x" + ("1" * 64), "--all"],
                "1",
                required=False,
                allow_empty_list=True,
            )

        self.assertEqual(result, [])
        self.assertIsNone(warning)

    def test_discovers_transaction_sender_and_internal_participants(self) -> None:
        sender = "0x" + ("1" * 40)
        destination = "0x" + ("2" * 40)
        internal_sender = "0x" + ("3" * 40)
        internal_destination = "0x" + ("4" * 40)

        addresses = self.collector.discover_addresses(
            {"from": sender, "to": destination},
            {},
            [{"from": internal_sender, "to": internal_destination}],
        )

        self.assertEqual(
            addresses, [sender, destination, internal_destination, internal_sender]
        )

    def test_contract_collection_uses_source_metadata_without_redundant_abi_call(self) -> None:
        address = "0x" + ("1" * 40)
        with patch.object(
            self.collector,
            "run_json",
            return_value=([{"ABI": "[]", "SourceCode": "contract C {}"}], None),
        ) as run:
            contracts = self.collector.collect_contracts(
                "etherscan", "1", [address], 12, [], 30
            )

        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[1], ["contract", "getsourcecode", address])
        self.assertIn("source_metadata", contracts[address])

    def test_main_fetches_block_and_auto_paginates_internal_transactions(self) -> None:
        transaction_hash = "0x" + ("9" * 64)
        sender = "0x" + ("1" * 40)
        destination = "0x" + ("2" * 40)
        calls: list[list[str]] = []

        def fake_run_json(
            executable: str,
            args: list[str],
            chain: str,
            required: bool,
            timeout_seconds: float = 30,
            allow_empty_list: bool = False,
        ) -> tuple[object, None]:
            calls.append(args)
            if args[:2] == ["proxy", "eth_getTransactionByHash"]:
                return {
                    "hash": transaction_hash,
                    "from": sender,
                    "to": destination,
                    "blockNumber": "0x10",
                }, None
            if args[:2] == ["proxy", "eth_getTransactionReceipt"]:
                return {"status": "0x1", "logs": []}, None
            if args[:2] == ["proxy", "eth_getBlockByNumber"]:
                return {"number": "0x10", "timestamp": "0x20"}, None
            return [], None

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle.json"
            arguments = Namespace(
                transaction_hash=transaction_hash,
                chain="1",
                include_contracts=False,
                max_contracts=12,
                etherscan_bin="etherscan",
                cli_timeout=30.0,
                output=output,
            )
            with (
                patch.object(self.collector, "parse_args", return_value=arguments),
                patch.object(self.collector.shutil, "which", return_value="etherscan"),
                patch.object(self.collector, "run_json", side_effect=fake_run_json),
            ):
                result = self.collector.main()

            bundle = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(bundle["block"]["timestamp"], "0x20")
        self.assertIn(
            ["proxy", "eth_getBlockByNumber", "--tag", "0x10", "--boolean", "false"],
            calls,
        )
        self.assertIn(
            ["account", "txlistinternal", "--txhash", transaction_hash, "--all"],
            calls,
        )

    def test_decodes_erc721_approval_with_indexed_token_id(self) -> None:
        owner = "0x" + ("2" * 40)
        approved = "0x" + ("3" * 40)
        log = {
            "address": "0x" + ("1" * 40),
            "topics": [
                self.summarizer.APPROVAL,
                address_topic(owner),
                address_topic(approved),
                "0x" + format(123, "064x"),
            ],
            "data": "0x",
            "logIndex": "0x4",
        }

        transfer, permission = self.summarizer.decode_log(log)

        self.assertIsNone(transfer)
        self.assertEqual(
            permission,
            {
                "standard": "ERC-721-like",
                "contract": "0x" + ("1" * 40),
                "owner": owner,
                "approved_address": approved,
                "token_id": 123,
                "log_index": 4,
            },
        )

    def test_erc721_approved_address_is_in_inventory(self) -> None:
        approved = "0x" + ("3" * 40)
        bundle = {
            "chain": "1",
            "transaction_hash": "0x" + ("4" * 64),
            "transaction": {},
            "receipt": {
                "status": "0x1",
                "logs": [
                    {
                        "address": "0x" + ("1" * 40),
                        "topics": [
                            self.summarizer.APPROVAL,
                            address_topic("0x" + ("2" * 40)),
                            address_topic(approved),
                            "0x" + format(123, "064x"),
                        ],
                        "data": "0x",
                        "logIndex": "0x0",
                    }
                ],
            },
        }

        summary = self.summarizer.summarize(bundle)

        self.assertIn(approved, summary["address_inventory"])

    def test_uses_containing_block_timestamp(self) -> None:
        summary = self.summarizer.summarize(
            {
                "chain": "1",
                "transaction": {"blockTimestamp": "0x1"},
                "receipt": {"status": "0x1"},
                "block": {"timestamp": "0x64"},
            }
        )

        self.assertEqual(summary["block_timestamp"], "1970-01-01T00:01:40+00:00")

    def test_l2_total_fee_includes_reported_l1_data_fee(self) -> None:
        summary = self.summarizer.summarize(
            {
                "chain": "10",
                "transaction": {},
                "receipt": {
                    "status": "0x1",
                    "gasUsed": "0x64",
                    "effectiveGasPrice": "0x2",
                    "l1Fee": "0x32",
                    "l1GasUsed": "0x10",
                    "blobGasUsed": "0x9c40",
                    "l1BlobBaseFee": "0x4ec1c9",
                },
            }
        )

        self.assertEqual(summary["execution_gas_fee_wei"], 200)
        self.assertEqual(summary["l1_data_fee_wei"], 50)
        self.assertEqual(summary["total_transaction_fee_wei"], 250)
        self.assertEqual(summary["total_transaction_fee_status"], "complete")
        self.assertEqual(summary["chain_specific_fee_fields"]["l1GasUsed"], "0x10")
        self.assertEqual(
            summary["chain_specific_fee_fields"]["l1BlobBaseFee"], "0x4ec1c9"
        )

    def test_non_mainnet_total_fee_is_unavailable_without_chain_specific_components(self) -> None:
        summary = self.summarizer.summarize(
            {
                "chain": "10",
                "transaction": {},
                "receipt": {
                    "status": "0x1",
                    "gasUsed": "0x64",
                    "effectiveGasPrice": "0x2",
                },
            }
        )

        self.assertEqual(summary["execution_gas_fee_wei"], 200)
        self.assertIsNone(summary["total_transaction_fee_wei"])
        self.assertEqual(summary["total_transaction_fee_status"], "unavailable")
        self.assertTrue(
            any(
                "Total transaction fee is unavailable" in warning
                for warning in summary["warnings"]
            )
        )

    def test_ethereum_total_fee_includes_blob_fee_when_present(self) -> None:
        summary = self.summarizer.summarize(
            {
                "chain": "1",
                "transaction": {},
                "receipt": {
                    "status": "0x1",
                    "gasUsed": "0x64",
                    "effectiveGasPrice": "0x2",
                    "blobGasUsed": "0x3",
                    "blobGasPrice": "0x4",
                },
            }
        )

        self.assertEqual(summary["execution_gas_fee_wei"], 200)
        self.assertEqual(summary["blob_data_fee_wei"], 12)
        self.assertEqual(summary["total_transaction_fee_wei"], 212)


if __name__ == "__main__":
    unittest.main()
