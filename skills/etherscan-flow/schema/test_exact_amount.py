import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "exact_amount", ROOT / "scripts" / "exact_amount.py"
)
exact_amount = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exact_amount)


class ExactAmountTests(unittest.TestCase):
    def test_tiny_eth_amount_stays_nonzero(self):
        self.assertEqual(
            "0.000000000000092695", exact_amount.format_amount("92695", 18)
        )

    def test_one_wei_stays_nonzero(self):
        self.assertEqual(
            "0.000000000000000001", exact_amount.format_amount("1", 18)
        )

    def test_hex_proxy_value_is_exact(self):
        self.assertEqual(
            "0.000000000000092695", exact_amount.format_amount("0x16a17", 18)
        )

    def test_trailing_fractional_zeroes_are_canonicalized(self):
        self.assertEqual("1.2345", exact_amount.format_amount("1234500", 6))
        self.assertEqual("1", exact_amount.format_amount("1000000", 6))

    def test_raw_values_are_summed_before_formatting(self):
        self.assertEqual(
            "0.000000000000092696", exact_amount.sum_amounts(["92695", "1"], 18)
        )

    def test_arbitrarily_large_raw_value_is_not_rounded(self):
        raw = "123456789012345678901234567890123456789"
        self.assertEqual(
            "123456789012345678901.234567890123456789",
            exact_amount.format_amount(raw, 18),
        )

    def test_numeric_input_is_rejected_before_precision_can_be_lost(self):
        with self.assertRaises(TypeError):
            exact_amount.format_amount(92695, 18)


if __name__ == "__main__":
    unittest.main()
