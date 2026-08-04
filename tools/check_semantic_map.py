#!/usr/bin/env python3
"""Fail when an accepted authoring key lacks an explicit semantic mapping."""

import os
import sys

import yaml


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAMMAR_PATH = os.path.join(ROOT, "schema", "loop.keys.yaml")
MAP_PATH = os.path.join(ROOT, "schema", "semantic-map.yaml")
MODES = {"container", "node", "edge", "field", "annotation", "compatibility"}


def main():
    with open(GRAMMAR_PATH) as source:
        grammar = yaml.safe_load(source)
    with open(MAP_PATH) as source:
        semantic_map = yaml.safe_load(source)

    expected = {
        f"{section}.{field}"
        for section, rules in grammar.items()
        if section not in {"version"}
        for field in rules
    }
    declared = set((semantic_map.get("fields") or {}).keys())
    errors = []
    if semantic_map.get("authoring_version") != str(grammar.get("version")):
        errors.append("semantic map authoring_version does not match grammar version")
    missing = sorted(expected - declared)
    extra = sorted(declared - expected)
    if missing:
        errors.append(f"accepted fields without semantics: {missing}")
    if extra:
        errors.append(f"semantic entries absent from grammar: {extra}")
    for field, record in (semantic_map.get("fields") or {}).items():
        if not isinstance(record, dict):
            errors.append(f"{field}: semantic record must be a map")
            continue
        if record.get("mode") not in MODES:
            errors.append(f"{field}: unknown semantic mode {record.get('mode')!r}")
        if not str(record.get("maps_to") or "").strip():
            errors.append(f"{field}: maps_to is empty")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"semantic map covers all {len(expected)} accepted authoring fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
