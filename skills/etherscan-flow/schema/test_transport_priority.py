from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TransportPriorityTests(unittest.TestCase):
    def test_skill_uses_binding_transport_order(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        credentials = skill.split(
            "### Credentials & transport — resolve in this exact order", 1
        )[1].split("### Entry point", 1)[0]
        labels = [
            "1. **Official Etherscan CLI v1+ — first choice.**",
            "2. **Etherscan MCP server — second choice, capability-gated.**",
            "3. **Explicit key in the current invocation — inline HTTP fallback.**",
            "4. **`ETHERSCAN_API_KEY` environment variable — HTTP transport.**",
            "5. **Local key file — HTTP transport.**",
            "6. **Interactive ask — last resort.**",
        ]
        positions = [credentials.index(label) for label in labels]
        self.assertEqual(sorted(positions), positions)
        self.assertIn(
            "official Etherscan CLI → Etherscan MCP → inline `apikey=` → other local HTTP key sources",
            credentials,
        )

    def test_readme_advertises_the_same_order(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "**Etherscan CLI → Etherscan MCP → inline `apikey=` → `ETHERSCAN_API_KEY` env var → local key file**",
            readme,
        )

    def test_transport_reference_uses_current_step_numbers(self):
        transports = (ROOT / "references" / "transports.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("official `etherscan` CLI v1+ (credentials step 1)", transports)
        self.assertIn("MCP transport:** at credentials step 2", transports)
        self.assertNotIn("CLI v1+ (credentials step 3)", transports)
        self.assertLess(
            transports.index("> **CLI transport:**"),
            transports.index("> **MCP transport:**"),
        )

    def test_mcp_is_capability_gated_and_falls_through(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        transports = (ROOT / "references" / "transports.md").read_text(
            encoding="utf-8"
        )
        incident = (ROOT / "references" / "incident-analysis.md").read_text(
            encoding="utf-8"
        )
        ens = (ROOT / "references" / "ens-resolution.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Apply it per operation", skill)
        self.assertIn("get_transaction_by_hash", skill)
        self.assertIn("get_transaction_receipt", skill)
        self.assertIn("get_logs", skill)
        self.assertIn("Never construct or guess a tool name", transports)
        self.assertIn(
            "`proxy/eth_getTransactionByHash` | `get_transaction_by_hash`",
            transports,
        )
        self.assertIn(
            "`proxy/eth_getTransactionReceipt` | `get_transaction_receipt`",
            transports,
        )
        self.assertIn("`logs/getlogs` | `get_logs`", transports)
        self.assertIn(
            '`get_transaction_by_hash`: `{ txhash, chainid }`', transports
        )
        self.assertIn(
            '`get_transaction_receipt`: `{ txhash, chainid }`', transports
        )
        self.assertIn(
            "The 16 legacy camelCase aliases are disabled by default", transports
        )
        self.assertIn("`raw_rpc_call` is planned, not live", transports)
        self.assertIn("The current MCP tool is exactly `get_logs`", incident)
        self.assertIn("current default MCP surface does not expose `eth_call`", ens)
        self.assertIn("get_transaction_by_hash", readme)
        self.assertNotIn(
            "invoke the Etherscan MCP tool that performs the same operation",
            transports,
        )

    def test_blockscan_widgets_are_absent_from_skill_guidance(self):
        forbidden = (
            "get_" + "multichain_balance",
            "get_" + "transaction_card",
        )
        guidance_files = [ROOT / "SKILL.md", ROOT / "README.md"]
        guidance_files.extend((ROOT / "references").glob("*.md"))

        for path in guidance_files:
            contents = path.read_text(encoding="utf-8")
            for tool_name in forbidden:
                self.assertNotIn(tool_name, contents, f"{tool_name} found in {path}")


if __name__ == "__main__":
    unittest.main()
