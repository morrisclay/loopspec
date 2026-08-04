#!/usr/bin/env python3
"""Compare deterministic finding-pattern overlap between two loop encodings.

This deliberately does not claim causal-root agreement. Exact linter overlap is a
reproducible lower bound; source adjudication remains a separate step.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
LOOPSPEC = ROOT / "tools/loopspec.py"


def check(path: pathlib.Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(LOOPSPEC), "check", str(path), "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    if not report["valid"]:
        raise SystemExit(f"invalid encoding: {path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary", type=pathlib.Path)
    parser.add_argument("replication", type=pathlib.Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    primary_report = check(args.primary)
    replication_report = check(args.replication)
    primary = {finding["pattern"] for finding in primary_report["findings"]}
    replication = {
        finding["pattern"] for finding in replication_report["findings"]
    }
    shared = primary & replication
    union = primary | replication
    result = {
        "primary": sorted(primary),
        "replication": sorted(replication),
        "shared": sorted(shared),
        "jaccard": len(shared) / len(union) if union else 1.0,
        "primary_recall": len(shared) / len(primary) if primary else 1.0,
        "replication_precision": (
            len(shared) / len(replication) if replication else 1.0
        ),
        "interpretation": "finding-pattern overlap only; not causal-root agreement",
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"shared: {', '.join(result['shared']) or '(none)'}")
        print(f"Jaccard: {result['jaccard']:.3f}")
        print(f"primary recall: {result['primary_recall']:.3f}")
        print(f"replication precision: {result['replication_precision']:.3f}")
        print(result["interpretation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
