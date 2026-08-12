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
            "2. **Etherscan MCP server — second choice.**",
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
        self.assertIn("MCP server (credentials step 2)", transports)
        self.assertNotIn("CLI v1+ (credentials step 3)", transports)
        self.assertLess(
            transports.index("> **CLI transport:**"),
            transports.index("> **MCP transport:**"),
        )


if __name__ == "__main__":
    unittest.main()
