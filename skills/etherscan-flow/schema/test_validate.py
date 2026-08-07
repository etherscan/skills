import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from schema.validate import invariants


ROOT = Path(__file__).resolve().parent.parent


class CaseValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "schema" / "case.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)
        cls.fixture = json.loads(
            (ROOT / "examples" / "strict-trace.example.json").read_text(encoding="utf-8")
        )

    def case(self):
        return copy.deepcopy(self.fixture)

    def schema_errors(self, case):
        return list(self.validator.iter_errors(case))

    def test_fixture_passes(self):
        case = self.case()
        self.assertEqual([], self.schema_errors(case))
        self.assertEqual([], invariants(case))

    def test_duplicate_node_id_fails(self):
        case = self.case()
        case["nodes"].append(copy.deepcopy(case["nodes"][0]))
        self.assertIn("node id 'v01' is duplicated", invariants(case))

    def test_duplicate_edge_id_fails(self):
        case = self.case()
        case["edges"][1]["id"] = case["edges"][0]["id"]
        self.assertIn("edge id 'e_v_atk' is duplicated", invariants(case))

    def test_edge_id_convention_is_enforced(self):
        case = self.case()
        case["edges"][0]["id"] = "<script>"
        self.assertTrue(self.schema_errors(case))

    def test_layout_is_required_and_persistable(self):
        missing = self.case()
        missing["nodes"][0].pop("x")
        self.assertTrue(self.schema_errors(missing))

        nonzero = self.case()
        nonzero["nodes"][0]["x"] = 125
        nonzero["nodes"][0]["y"] = 80
        self.assertEqual([], self.schema_errors(nonzero))

    def test_tiny_plain_decimal_string_is_accepted(self):
        case = self.case()
        case["edges"][0]["amount"] = "0.000000000000092695"
        self.assertEqual([], self.schema_errors(case))

    def test_amount_numeric_casts_and_exponents_are_rejected(self):
        for bad_amount in (0, 0.000000000000092695, "9.2695e-14"):
            with self.subTest(amount=bad_amount):
                case = self.case()
                case["edges"][0]["amount"] = bad_amount
                self.assertTrue(self.schema_errors(case))

    def test_schema_invalid_object_does_not_crash_invariants(self):
        case = self.case()
        case["nodes"][0].pop("id")
        self.assertTrue(self.schema_errors(case))
        self.assertIsInstance(invariants(case), list)

    def test_unknown_meta_key_fails(self):
        case = self.case()
        case["_meta"]["edge_txhashes"] = {}
        self.assertTrue(self.schema_errors(case))

    def test_ui_findings_markdown_is_explicitly_supported(self):
        case = self.case()
        case["_meta"]["ui"] = {
            "findings_markdown": "# Case Findings\n\n" + ("Edited Markdown line.\n" * 20)
        }
        self.assertEqual([], self.schema_errors(case))
        self.assertEqual([], invariants(case))

    def test_legacy_ui_findings_is_supported_for_migration(self):
        case = self.case()
        case["_meta"]["ui"] = {
            "findings": {"summary": "Legacy structured findings", "items": ["One", "Two"]}
        }
        self.assertEqual([], self.schema_errors(case))
        self.assertEqual([], invariants(case))

    def test_findings_aliases_remain_invalid(self):
        singular = self.case()
        singular["_meta"]["ui"] = {"finding_markdown": "Not supported"}
        self.assertTrue(self.schema_errors(singular))

        old_meta = self.case()
        old_meta["_meta"]["findings_markdown"] = "Migrated only by the UI"
        self.assertTrue(self.schema_errors(old_meta))

        root = self.case()
        root["findings"] = "Migrated only by the UI"
        self.assertTrue(self.schema_errors(root))

    # Every string location the sanitization claim covers, keyed by a label.
    # Each mutator plants an XSS/HTML payload at that location; both the JSON
    # Schema and the Python validator must reject it. Nested containers use a
    # helper to keep the table flat.
    XSS_FIELD_MUTATORS = {
        "top-level name": lambda c, p: c.__setitem__("name", p),
        "node.label": lambda c, p: c["nodes"][0].__setitem__("label", p),
        "node.subLabel": lambda c, p: c["nodes"][0].__setitem__("subLabel", p),
        "node.notes": lambda c, p: c["nodes"][0].__setitem__("notes", p),
        "edge.token": lambda c, p: c["edges"][0].__setitem__("token", p),
        "edge.timestamp": lambda c, p: c["edges"][0].__setitem__("timestamp", p),
        "_meta.chain": lambda c, p: c["_meta"].__setitem__("chain", p),
        "_meta.chains[].chain": lambda c, p: c["_meta"]["chains"][0].__setitem__("chain", p),
        "_meta.created_at": lambda c, p: c["_meta"].__setitem__("created_at", p),
        "_meta.disclaimer": lambda c, p: c["_meta"].__setitem__("disclaimer", p),
        "gap.detail": lambda c, p: c["_meta"]["gaps"].append(
            {"type": "unverified_claim", "detail": p}
        ),
        "gap.claim": lambda c, p: c["_meta"]["gaps"].append(
            {"type": "unverified_claim", "detail": "d", "claim": p}
        ),
        "analysis.summary": lambda c, p: c["_meta"]["analysis"].__setitem__("summary", p),
        "analysis.attack_vector": lambda c, p: c["_meta"]["analysis"].__setitem__("attack_vector", p),
        "analysis.root_cause": lambda c, p: c["_meta"]["analysis"].__setitem__("root_cause", p),
        "analysis.limitations[]": lambda c, p: c["_meta"]["analysis"]["limitations"].append(p),
        "analysis.evidence.claim": lambda c, p: c["_meta"]["analysis"]["evidence"].append(
            {"claim": p, "kind": "observed", "sources": ["x"], "txhashes": [],
             "addresses": [], "block": None, "selector": None}
        ),
        "analysis.evidence.sources[]": lambda c, p: c["_meta"]["analysis"]["evidence"].append(
            {"claim": "c", "kind": "observed", "sources": [p], "txhashes": [],
             "addresses": [], "block": None, "selector": None}
        ),
        "analysis.alternative.hypothesis": lambda c, p: c["_meta"]["analysis"]["alternative_hypotheses"].append(
            {"hypothesis": p, "assessment": "plausible", "evidence_for": [], "evidence_against": []}
        ),
        "analysis.alternative.evidence_for[]": lambda c, p: c["_meta"]["analysis"]["alternative_hypotheses"].append(
            {"hypothesis": "h", "assessment": "plausible", "evidence_for": [p], "evidence_against": []}
        ),
        "analysisAsset.token": lambda c, p: c["_meta"]["analysis"].__setitem__(
            "losses_by_token",
            [{"token": p, "token_address": "0x" + "1" * 40, "gross_amount": "1",
              "returned_or_recovered": "0", "net_amount": "1"}],
        ),
        "pattern.pattern": lambda c, p: c["_meta"].setdefault("patterns", []).append(
            {"pattern": p, "evidence_txhash": None}
        ),
        "legacy _meta.ui.findings string": lambda c, p: c["_meta"].__setitem__(
            "ui", {"findings": {"summary": p, "items": ["ok"]}}
        ),
        "legacy _meta.ui.findings nested list": lambda c, p: c["_meta"].__setitem__(
            "ui", {"findings": {"summary": "ok", "items": [p]}}
        ),
    }

    def test_every_string_location_rejects_xss(self):
        payload = '<img src=x onerror="steal()">'
        for label, mutate in self.XSS_FIELD_MUTATORS.items():
            with self.subTest(field=label):
                case = self.case()
                mutate(case, payload)
                self.assertTrue(
                    self.schema_errors(case), f"schema accepted XSS at {label}"
                )
                self.assertTrue(
                    invariants(case), f"validator accepted XSS at {label}"
                )

    def test_legacy_ui_findings_is_no_longer_a_sanitization_bypass(self):
        # Regression: a payload under legacy _meta.ui.findings must NOT ride the
        # findings_markdown exemption. Both layers must catch it.
        case = self.case()
        case["_meta"]["ui"] = {"findings": {"summary": '<img src=x onerror="x()">'}}
        self.assertTrue(self.schema_errors(case))
        self.assertTrue(any("HTML tag" in item for item in invariants(case)))

        # findings_markdown itself stays exempt: multiline Markdown remains valid.
        exempt = self.case()
        exempt["_meta"]["ui"] = {"findings_markdown": "# Title\n\nParagraph with * markdown *.\n"}
        self.assertEqual([], self.schema_errors(exempt))
        self.assertEqual([], invariants(exempt))

    def test_all_strings_are_sanitized(self):
        overlong = self.case()
        overlong["_meta"]["performance"]["note"] = "x" * 201
        self.assertTrue(self.schema_errors(overlong))
        self.assertTrue(any("exceeds 200" in item for item in invariants(overlong)))

        html = self.case()
        html["_meta"]["performance"]["note"] = "<script>alert(1)</script>"
        self.assertTrue(self.schema_errors(html))
        self.assertTrue(any("HTML tag" in item for item in invariants(html)))

        control = self.case()
        control["_meta"]["performance"]["note"] = "line one\nline two"
        self.assertTrue(self.schema_errors(control))
        self.assertTrue(any("control character" in item for item in invariants(control)))


if __name__ == "__main__":
    unittest.main()
