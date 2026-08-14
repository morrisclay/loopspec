#!/usr/bin/env python3
"""Score blinded episode assessments against frozen synthetic ground truth."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data"
DEFAULT_REPORT = ROOT / "RESULTS.md"
TRANSITIONS = ("acquired", "lost", "redistributed", "preserved", "none")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def label_f1(truth: list[str], predicted: list[str], label: str) -> float:
    tp = sum(t == label and p == label for t, p in zip(truth, predicted))
    fp = sum(t != label and p == label for t, p in zip(truth, predicted))
    fn = sum(t == label and p != label for t, p in zip(truth, predicted))
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return safe_div(2 * precision * recall, precision + recall)


def macro_f1(truth: list[str], predicted: list[str]) -> float:
    return sum(label_f1(truth, predicted, label) for label in TRANSITIONS) / len(TRANSITIONS)


def binary_f1(truth: list[bool], predicted: list[bool]) -> float:
    tp = sum(t and p for t, p in zip(truth, predicted))
    fp = sum(not t and p for t, p in zip(truth, predicted))
    fn = sum(t and not p for t, p in zip(truth, predicted))
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return safe_div(2 * precision * recall, precision + recall)


def brier(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> float:
    total = 0.0
    for truth, assessment in rows:
        actual = truth["transition"]
        probs = assessment["transition_probabilities"]
        total += sum((probs[label] - (1.0 if label == actual else 0.0)) ** 2
                     for label in TRANSITIONS)
    return safe_div(total, len(rows))


def condition_metrics(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    truth_t = [truth["transition"] for truth, _ in rows]
    pred_t = [assessment["predicted_transition"] for _, assessment in rows]
    truth_r = [truth["recursion"] for truth, _ in rows]
    pred_r = [assessment["predicted_recursion"] for _, assessment in rows]
    none_rows = [(truth, assessment) for truth, assessment in rows if truth["transition"] == "none"]
    nonrecursive_rows = [(truth, assessment) for truth, assessment in rows if not truth["recursion"]]
    return {
        "n": len(rows),
        "macro_f1": macro_f1(truth_t, pred_t),
        "accuracy": safe_div(sum(a == b for a, b in zip(truth_t, pred_t)), len(rows)),
        "bearer_accuracy": safe_div(sum(truth["bearer"] == assessment["predicted_bearer"]
                                        for truth, assessment in rows), len(rows)),
        "recursion_f1": binary_f1(truth_r, pred_r),
        "brier": brier(rows),
        "overclaim_rate": safe_div(sum(assessment["predicted_transition"] != "none"
                                       for _, assessment in none_rows), len(none_rows)),
        "false_recursion_rate": safe_div(sum(assessment["predicted_recursion"]
                                             for _, assessment in nonrecursive_rows),
                                         len(nonrecursive_rows)),
        "governance_accuracy": safe_div(sum(truth["intervention_viable"] == assessment["predicted_intervention_viable"]
                                            for truth, assessment in rows), len(rows)),
        "per_label_f1": {label: label_f1(truth_t, pred_t, label) for label in TRANSITIONS},
        "confusion": Counter(zip(truth_t, pred_t)),
    }


def analyze(data_dir: Path = DEFAULT_DATA) -> dict[str, Any]:
    series = read_jsonl(data_dir / "synthetic_series.jsonl")
    assessments = read_jsonl(data_dir / "assessments.jsonl")
    truth_by_series = {row["series_id"]: row["ground_truth"] for row in series}
    family_by_series = {row["series_id"]: row["family"] for row in series}
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    mechanism_grouped: dict[str, dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]] = defaultdict(lambda: defaultdict(list))
    for assessment in assessments:
        truth = truth_by_series[assessment["series_id"]]
        grouped[assessment["condition"]].append((truth, assessment))
        mechanism_grouped[assessment["condition"]][truth["mechanism"]].append((truth, assessment))

    metrics = {condition: condition_metrics(rows) for condition, rows in grouped.items()}
    ledger = metrics["episode_ledger"]
    performance = metrics["performance_only"]
    trace = metrics["ordinary_trace"]
    hypotheses = {
        "H1": ledger["macro_f1"] - performance["macro_f1"] >= 0.20,
        "H2": ledger["macro_f1"] - trace["macro_f1"] >= 0.08,
        "H3": performance["false_recursion_rate"] - ledger["false_recursion_rate"] >= 0.15,
        "H4": ledger["bearer_accuracy"] - trace["bearer_accuracy"] >= 0.15,
    }
    result = {
        "series": len(series),
        "episodes": sum(len(row["episodes"]) for row in series),
        "families": dict(Counter(family_by_series.values())),
        "mechanisms": dict(Counter(row["ground_truth"]["mechanism"] for row in series)),
        "metrics": metrics,
        "hypotheses": hypotheses,
        "promotion_gate": all(hypotheses[key] for key in ("H1", "H2", "H3")),
        "mechanism_accuracy": {
            condition: {
                mechanism: condition_metrics(rows)["accuracy"]
                for mechanism, rows in mechanisms.items()
            }
            for condition, mechanisms in mechanism_grouped.items()
        },
    }
    return result


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Results: synthetic episode accounting",
        "",
        "**Run date:** 2026-08-13  ",
        f"**Corpus:** {result['series']} series / {result['episodes']} episodes / "
        f"{len(result['families'])} equally represented domains",
        "",
        "This is a deterministic synthetic representation experiment. Its assessors are executable",
        "role-separated baselines, not independent human reviewers or model families.",
        "",
        "## Primary comparison",
        "",
        "| condition | transition macro F1 | accuracy | bearer accuracy | recursion F1 | Brier ↓ | false recursion | overclaim on no-transition | governance accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    order = ("performance_only", "ordinary_trace", "episode_ledger")
    for condition in order:
        metric = result["metrics"][condition]
        lines.append(
            f"| `{condition}` | {metric['macro_f1']:.3f} | {pct(metric['accuracy'])} | "
            f"{pct(metric['bearer_accuracy'])} | {metric['recursion_f1']:.3f} | "
            f"{metric['brier']:.3f} | {pct(metric['false_recursion_rate'])} | "
            f"{pct(metric['overclaim_rate'])} | {pct(metric['governance_accuracy'])} |"
        )
    lines.extend(["", "## Preregistered hypotheses", ""])
    descriptions = {
        "H1": "ledger macro F1 exceeds performance-only by at least 0.20",
        "H2": "ledger macro F1 exceeds ordinary trace by at least 0.08",
        "H3": "ledger false-recursion rate is at least 0.15 below performance-only",
        "H4": "ledger bearer accuracy exceeds ordinary trace by at least 0.15",
    }
    for key in ("H1", "H2", "H3", "H4"):
        lines.append(f"- **{key} {'passed' if result['hypotheses'][key] else 'failed'}:** {descriptions[key]}.")

    ledger = result["metrics"]["episode_ledger"]
    trace = result["metrics"]["ordinary_trace"]
    performance = result["metrics"]["performance_only"]
    lines.extend([
        "",
        "## Interpretation",
        "",
        f"The ledger changed transition macro F1 by **{ledger['macro_f1'] - performance['macro_f1']:+.3f}** "
        f"against performance-only and **{ledger['macro_f1'] - trace['macro_f1']:+.3f}** against an ordinary trace.",
        f"Its bearer-accuracy lift over trace was **{ledger['bearer_accuracy'] - trace['bearer_accuracy']:+.3f}**.",
        "",
        "The useful distinction is not greater log volume. The ledger exposes a joined claim:",
        "a difference at exit, an identified carrier, later availability and retrieval, a separated",
        "entry/exit profile, and evidence that the returned difference affected realization of the",
        "focal power. Storage without later uptake and improvement caused by easier cases therefore",
        "remain non-cases.",
        "",
        "## Per-label transition F1",
        "",
        "| label | performance only | ordinary trace | episode ledger |",
        "|---|---:|---:|---:|",
    ])
    for label in TRANSITIONS:
        lines.append(
            f"| `{label}` | {performance['per_label_f1'][label]:.3f} | "
            f"{trace['per_label_f1'][label]:.3f} | {ledger['per_label_f1'][label]:.3f} |"
        )

    lines.extend(["", "## Mechanism-level accuracy", "",
                  "| mechanism | performance only | ordinary trace | episode ledger |",
                  "|---|---:|---:|---:|"])
    mechanisms = sorted(result["mechanism_accuracy"]["episode_ledger"])
    for mechanism in mechanisms:
        lines.append(
            f"| `{mechanism}` | {pct(result['mechanism_accuracy']['performance_only'][mechanism])} | "
            f"{pct(result['mechanism_accuracy']['ordinary_trace'][mechanism])} | "
            f"{pct(result['mechanism_accuracy']['episode_ledger'][mechanism])} |"
        )

    gate = result["promotion_gate"]
    lines.extend([
        "",
        "## Decision",
        "",
        f"The synthetic promotion gate **{'passes' if gate else 'does not pass'}**.",
        "",
        "Passing would justify continuing the episode artifact as an experimental evidence layer,",
        "not adding it to the public LoopSpec grammar. The next required gates are independent",
        "episode-boundary encoding, a retrospective real case, and the prospective HITL capability",
        "probe in this directory.",
        "",
        "## Limits and strongest rival",
        "",
        "The simulator and assessors share a designed vocabulary. High ledger performance may partly",
        "show that the assessor can read fields written for its task. The strongest rival is a",
        "well-instrumented event trace with explicit component probes and stable artifact identity.",
        "If such a trace reaches the ledger within 0.08 macro F1, episode accounting has not earned",
        "its extra burden under the preregistered rule.",
        "",
        "The synthetic run says nothing by itself about actual human learning. Human capability",
        "requires prospective evidence under delay, transfer, removal, and recovery conditions.",
        "The included HITL probe creates that path but has no participant outcomes yet.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], data_dir: Path, report_path: Path) -> None:
    # Tuple-key confusion matrices are diagnostic internals and are rendered separately only when
    # needed. Remove them before JSON encoding; JSON rejects tuple mapping keys.
    serializable = {key: value for key, value in result.items() if key != "metrics"}
    serializable["metrics"] = {
        condition: {key: value for key, value in metric.items() if key != "confusion"}
        for condition, metric in result["metrics"].items()
    }
    (data_dir / "metrics.json").write_text(
        json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_path.write_text(render(result), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    result = analyze(args.data)
    write_outputs(result, args.data, args.report)
    status = "passed" if result["promotion_gate"] else "did not pass"
    print(f"synthetic promotion gate {status}; wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
