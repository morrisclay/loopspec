#!/usr/bin/env python3
"""Score identifier-invariant control-plane agreement between two LoopSpec encodings."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.loopspec import checked_document  # noqa: E402


CONTROL_KINDS = {"ControlOperation", "Output", "ActionProfile"}
CONTROL_RELS = {"authorizes", "emits", "profiles"}


def actor_role(node_id: str | None, nodes: dict[str, dict]) -> str:
    if not node_id:
        return "none"
    node = nodes.get(node_id, {})
    return str(node.get("party_kind") or node.get("kind") or "unknown")


def node_fingerprint(node: dict, nodes: dict[str, dict]) -> tuple | None:
    kind = node.get("kind")
    if kind == "ControlOperation":
        return (
            "node", "operation", node.get("operation_kind"), bool(node.get("condition")),
            actor_role(node.get("authorized_by"), nodes),
        )
    if kind == "Output":
        return ("node", "output", node.get("output_kind"), node.get("terminates"))
    if kind == "ActionProfile":
        return (
            "node", "profile", node.get("binding_stage"), node.get("reversibility"),
            bool(node.get("default")),
            actor_role(node.get("requires_approval_from"), nodes),
        )
    return None


def fingerprints(path: pathlib.Path) -> Counter:
    document, _warnings, report, _findings = checked_document(str(path))
    if not report.ok:
        raise SystemExit(f"invalid encoding {path}: {report.errors}")
    nodes = {node["id"]: node for node in document.get("nodes") or []}
    out = Counter()
    for node in nodes.values():
        fingerprint = node_fingerprint(node, nodes)
        if fingerprint:
            out[fingerprint] += 1
    for edge in document.get("edges") or []:
        if edge.get("rel") not in CONTROL_RELS:
            continue
        source = nodes.get(edge.get("from"), {})
        target = nodes.get(edge.get("to"), {})
        if source.get("kind") not in CONTROL_KINDS and target.get("kind") not in CONTROL_KINDS:
            continue
        source_fp = node_fingerprint(source, nodes)
        target_fp = node_fingerprint(target, nodes)
        if source.get("kind") == "Party":
            source_fp = ("actor", actor_role(source.get("id"), nodes))
        elif source.get("kind") == "Intervention":
            source_fp = ("world_action",)
        if target.get("kind") == "Party":
            target_fp = ("actor", actor_role(target.get("id"), nodes))
        elif target.get("kind") == "Intervention":
            target_fp = ("world_action",)
        out[("edge", source_fp, edge.get("rel"), target_fp)] += 1
    return out


def score(primary: Counter, replication: Counter) -> dict:
    shared = primary & replication
    true_positive = sum(shared.values())
    primary_total = sum(primary.values())
    replication_total = sum(replication.values())
    precision = true_positive / replication_total if replication_total else 1.0
    recall = true_positive / primary_total if primary_total else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "primary": primary_total,
        "replication": replication_total,
        "shared": true_positive,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary", type=pathlib.Path)
    parser.add_argument("replication", type=pathlib.Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = score(fingerprints(args.primary), fingerprints(args.replication))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"control-plane agreement: F1={result['f1']:.3f}; "
            f"precision={result['precision']:.3f}; recall={result['recall']:.3f}; "
            f"shared={result['shared']}/{result['primary']} primary, "
            f"{result['replication']} replication"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
