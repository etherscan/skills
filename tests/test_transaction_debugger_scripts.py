from __future__ import annotations

import importlib.util
import subprocess
import unittest
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


if __name__ == "__main__":
    unittest.main()
