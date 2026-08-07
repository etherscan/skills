#!/usr/bin/env python3
"""Format and sum on-chain amounts without float or decimal arithmetic."""

import argparse
import re


DECIMAL_INTEGER_RE = re.compile(r"^[0-9]+$")
HEX_INTEGER_RE = re.compile(r"^0[xX][0-9a-fA-F]+$")


def raw_digits(raw: str) -> str:
    """Return a canonical decimal integer string from an API string."""
    if not isinstance(raw, str):
        raise TypeError("raw amount must remain a string")
    if DECIMAL_INTEGER_RE.fullmatch(raw):
        return raw.lstrip("0") or "0"
    if HEX_INTEGER_RE.fullmatch(raw):
        return str(int(raw, 16))
    raise ValueError("raw amount must be an unsigned decimal or hex integer string")


def checked_decimals(decimals: int) -> int:
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        raise ValueError("decimals must be a non-negative integer")
    return decimals


def format_amount(raw: str, decimals: int) -> str:
    """Insert a decimal point exactly; never round or emit an exponent."""
    digits = raw_digits(raw)
    scale = checked_decimals(decimals)
    if digits == "0":
        return "0"
    if scale == 0:
        return digits

    padded = digits.zfill(scale + 1)
    integer_part = padded[:-scale].lstrip("0") or "0"
    fractional_part = padded[-scale:].rstrip("0")
    if not fractional_part:
        return integer_part
    return f"{integer_part}.{fractional_part}"


def sum_amounts(raw_values: list[str], decimals: int) -> str:
    """Sum exact raw units with Python's arbitrary-precision integers."""
    checked_decimals(decimals)
    total = sum(int(raw_digits(raw)) for raw in raw_values)
    return format_amount(str(total), decimals)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    format_parser = subparsers.add_parser("format")
    format_parser.add_argument("raw")
    format_parser.add_argument("decimals", type=int)

    sum_parser = subparsers.add_parser("sum")
    sum_parser.add_argument("decimals", type=int)
    sum_parser.add_argument("raw", nargs="+")

    args = parser.parse_args()
    if args.command == "format":
        print(format_amount(args.raw, args.decimals))
    else:
        print(sum_amounts(args.raw, args.decimals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
