#!/usr/bin/env python3
"""Render average causal-power and performance trajectories from the synthetic corpus."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "synthetic_series.jsonl"
DEFAULT_OUTPUT = ROOT / "TRAJECTORIES.md"
BEARERS = ("human", "ai_in_use", "institution", "distributed")


def read_series(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def curve(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = []
    for index in range(len(rows[0]["episodes"])):
        if field == "joint_result":
            samples = [row["episodes"][index]["work"]["joint_result"] for row in rows]
        else:
            samples = [row["episodes"][index]["exit_profile"]["power"][field] for row in rows]
        values.append(mean(samples))
    return values


def spark(values: list[float]) -> str:
    return " -> ".join(f"{value:.2f}" for value in values)


def render(rows: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["ground_truth"]["mechanism"]].append(row)
    lines = [
        "# Synthetic longitudinal trajectories",
        "",
        "Each sequence is the mean exit value for episodes 1 through 7 across eight series: two",
        "replicates in each of four domains. Component values are relational power realizability",
        "under the simulated conditions, not general ability scores.",
        "",
    ]
    for mechanism in sorted(grouped):
        cases = grouped[mechanism]
        truth = cases[0]["ground_truth"]
        source = truth["source_episode"].rsplit("e", 1)[-1] if truth["source_episode"] else "-"
        target = truth["target_episode"].rsplit("e", 1)[-1] if truth["target_episode"] else "-"
        lines.extend([
            f"## `{mechanism}`",
            "",
            f"Ground truth: **{truth['transition']}**; assessed bearer: **{truth['bearer']}**; "
            f"carrier: **{truth['carrier_kind']}**; source -> target: **{source} -> {target}**.",
            "",
            "| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |",
            "|---|---|",
        ])
        for bearer in BEARERS:
            lines.append(f"| `{bearer}` | {spark(curve(cases, bearer))} |")
        lines.append(f"| `joint_result` | {spark(curve(cases, 'joint_result'))} |")
        lines.append("")
    lines.extend([
        "## Reading the curves",
        "",
        "- `case_mix_shift` improves immediate joint results while every power curve remains flat.",
        "- `retained_but_unused` records an artifact but leaves power curves unchanged because the",
        "  artifact never enters later work.",
        "- `assisted_substitution` preserves or improves the distributed trajectory while human-only",
        "  realizability declines.",
        "- `provider_dependency` looks viable during normal episodes and collapses under the final",
        "  removal condition.",
        "- `stable_rehearsal` treats tested maintenance as evidence rather than inferring it from a",
        "  flat performance line.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = read_series(args.data)
    args.output.write_text(render(rows), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
