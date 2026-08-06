#!/usr/bin/env python3
"""Validate every examples/*.example.json against schema/case.schema.json.

Checks JSON Schema conformance plus the cross-field invariants the schema
cannot express (unique node/edge ids, edge references, merged hashes,
document-wide string sanitization, and evidence-backed analysis status).
Exit 0 on success, 1 on any failure.
Run locally or in CI: `python schema/validate.py`.
"""
import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter

from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "schema", "case.schema.json")
HTML_TAG_RE = re.compile(r"<!--.*?-->|<![A-Za-z][^>]*>|</?[A-Za-z][^>]*>", re.DOTALL)
MAX_FINDINGS_MARKDOWN_CHARS = 1024 * 1024


def string_invariants(value, path="$"):
    """Return violations of the global string-sanitization contract."""
    problems = []

    def check_string(text, location):
        # Only the single multiline Markdown field is exempt from the
        # 200-char/HTML limits. Legacy _meta.ui.findings structures are NOT
        # exempt — their strings must be sanitized like any other.
        if location == "$._meta.ui.findings_markdown":
            if len(text) > MAX_FINDINGS_MARKDOWN_CHARS:
                problems.append(f"{location}: UI findings content exceeds 1,048,576 characters")
            if any(unicodedata.category(char) == "Cc" and char not in "\t\n\r" for char in text):
                problems.append(f"{location}: UI findings content contains a disallowed control character")
            return
        if len(text) > 200:
            problems.append(f"{location}: string exceeds 200 characters")
        if HTML_TAG_RE.search(text):
            problems.append(f"{location}: string contains an HTML tag")
        if any(unicodedata.category(char) == "Cc" for char in text):
            problems.append(f"{location}: string contains a control character")

    if isinstance(value, dict):
        for key, child in value.items():
            check_string(key, f"{path}.<key>")
            problems += string_invariants(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems += string_invariants(child, f"{path}[{index}]")
    elif isinstance(value, str):
        check_string(value, path)
    return problems


def analysis_invariants(analysis):
    """Return violations of the status/evidence contract in references/incident-analysis.md.

    The schema types each analysis field independently, so a "confirmed" verdict
    citing an empty evidence array validates cleanly. Only insufficient_evidence
    may leave evidence and hypotheses empty, and it must say why.
    """
    if not isinstance(analysis, dict) or not analysis:
        return []
    problems = []
    status = analysis.get("status")
    evidence = analysis.get("evidence") or []
    asserts_mechanism = status in ("confirmed", "probable", "possible")

    if asserts_mechanism and not evidence:
        problems.append(f"analysis: status '{status}' asserts a mechanism but cites no evidence")
    if status == "confirmed" and not any(e.get("kind") == "observed" for e in evidence):
        problems.append("analysis: status 'confirmed' needs at least one 'observed' evidence claim")
    if asserts_mechanism and not analysis.get("alternative_hypotheses"):
        problems.append(f"analysis: status '{status}' needs at least one competing hypothesis")
    if status == "insufficient_evidence" and not analysis.get("limitations"):
        problems.append("analysis: status 'insufficient_evidence' needs at least one limitation")
    return problems


def invariants(case):
    """Return a list of invariant violations the schema can't catch."""
    if not isinstance(case, dict):
        return string_invariants(case)

    problems = []
    nodes = case.get("nodes") if isinstance(case.get("nodes"), list) else []
    edges = case.get("edges") if isinstance(case.get("edges"), list) else []
    node_id_list = [
        node.get("id")
        for node in nodes
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    ]
    node_ids = set(node_id_list)
    duplicate_node_ids = sorted(node_id for node_id, count in Counter(node_id_list).items() if count > 1)
    for node_id in duplicate_node_ids:
        problems.append(f"node id '{node_id}' is duplicated")

    edge_id_list = [
        edge.get("id")
        for edge in edges
        if isinstance(edge, dict) and isinstance(edge.get("id"), str)
    ]
    duplicate_edge_ids = sorted(edge_id for edge_id, count in Counter(edge_id_list).items() if count > 1)
    for edge_id in duplicate_edge_ids:
        problems.append(f"edge id '{edge_id}' is duplicated")

    for e in edges:
        if not isinstance(e, dict):
            continue
        eid = e.get("id", "?")
        if e.get("source") not in node_ids:
            problems.append(f"edge {eid}: source '{e.get('source')}' is not a node id")
        if e.get("target") not in node_ids:
            problems.append(f"edge {eid}: target '{e.get('target')}' is not a node id")
        hashes = e.get("txhashes")
        if hashes:
            if hashes[0] != e.get("txhash"):
                problems.append(f"edge {eid}: txhashes[0] must equal txhash")
            if e.get("txcount") != len(hashes):
                problems.append(
                    f"edge {eid}: txcount ({e.get('txcount')}) != len(txhashes) ({len(hashes)})"
                )
    meta = case.get("_meta") if isinstance(case.get("_meta"), dict) else {}
    problems += analysis_invariants(meta.get("analysis"))
    problems += string_invariants(case)
    return problems


def main():
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    files = sorted(glob.glob(os.path.join(ROOT, "examples", "*.example.json")))
    if not files:
        print("no examples/*.example.json found", file=sys.stderr)
        return 1

    failed = False
    for path in files:
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as case_file:
            case = json.load(case_file)
        errors = sorted(validator.iter_errors(case), key=lambda e: list(e.path))
        problems = [f"{list(e.path)}: {e.message}" for e in errors] + invariants(case)
        if problems:
            failed = True
            print(f"FAIL {rel}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
