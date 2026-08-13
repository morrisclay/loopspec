#!/usr/bin/env python3
"""Run role-separated executable assessment groups over blinded episode packets."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from . import ASSESSOR_VERSION
except ImportError:  # direct script execution
    from __init__ import ASSESSOR_VERSION


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data"
CONDITIONS = ("performance_only", "ordinary_trace", "episode_ledger")
TRANSITIONS = ("acquired", "lost", "redistributed", "preserved", "none")
BEARERS = ("human", "ai_in_use", "institution", "distributed", "none")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def event_index(packet: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[Any]]]:
    events = []
    values: dict[str, list[Any]] = defaultdict(list)
    for episode in packet["episodes"]:
        for event in episode.get("trace", []):
            events.append(event)
            values[event["type"]].append(event.get("value"))
    return events, values


def result_features(packet: dict[str, Any]) -> dict[str, float]:
    results = [float(episode.get("joint_result", episode.get("work", {}).get("joint_result", 0)))
               for episode in packet["episodes"]]
    latencies = [float(episode.get("latency", episode.get("work", {}).get("latency", 0)))
                 for episode in packet["episodes"]]
    return {
        "result_start": results[0],
        "result_end": results[-1],
        "result_delta": results[-1] - results[0],
        "latency_delta": latencies[-1] - latencies[0],
    }


def boundary_group(packet: dict[str, Any]) -> dict[str, Any]:
    if packet["condition"] == "episode_ledger":
        linked = all(episode["series_id"] == packet["series_id"] for episode in packet["episodes"])
        open_returns = sum(bool(episode["boundary"]["unresolved_returns"])
                           for episode in packet["episodes"])
        return {"role": "boundary_temporal", "comparable": linked,
                "open_returns_visible": open_returns, "confidence": 0.94}
    if packet["condition"] == "ordinary_trace":
        ordinals = [episode["ordinal"] for episode in packet["episodes"]]
        return {"role": "boundary_temporal", "comparable": ordinals == sorted(ordinals),
                "open_returns_visible": 0, "confidence": 0.66}
    return {"role": "boundary_temporal", "comparable": True,
            "open_returns_visible": 0, "confidence": 0.38}


def return_group(packet: dict[str, Any]) -> dict[str, Any]:
    condition = packet["condition"]
    if condition == "episode_ledger":
        carriers = [carrier for episode in packet["episodes"] for carrier in episode["carriers"]]
        returns = [ret for episode in packet["episodes"] for ret in episode["returns"]]
        retained = any(c["retained"] and c["available_later"] for c in carriers)
        linked = any(r["made_difference"] and r["evidence_status"] in {"observed", "inferred"}
                     for r in returns)
        strength = 0.95 if retained and linked else 0.24 if retained else 0.04
        return {"role": "retention_return", "retained": retained, "returned": linked,
                "strength": strength, "confidence": 0.93}
    if condition == "ordinary_trace":
        events, _ = event_index(packet)
        saved = {event["object"] for event in events if event["type"] == "carrier_saved"}
        loaded = {event["object"] for event in events if event["type"] == "carrier_loaded"}
        linked = bool(saved & loaded)
        strength = 0.76 if linked else 0.26 if saved else 0.08
        return {"role": "retention_return", "retained": bool(saved), "returned": linked,
                "strength": strength, "confidence": 0.72}
    features = result_features(packet)
    # Performance-only assessment reproduces a common error: a sufficiently large trajectory
    # is treated as evidence of recurrence even though no carrier has been observed.
    inferred = abs(features["result_delta"]) >= 0.055
    return {"role": "retention_return", "retained": False, "returned": inferred,
            "strength": 0.43 if inferred else 0.08, "confidence": 0.33}


def power_group(packet: dict[str, Any]) -> dict[str, Any]:
    condition = packet["condition"]
    if condition == "episode_ledger":
        start = packet["episodes"][0]["entry_profile"]["power"]
        end = packet["episodes"][-1]["exit_profile"]["power"]
        delta = {key: end[key] - start[key] for key in start}
        tested = any(
            event["type"] in {"human_only_probe", "ai_only_probe", "joint_probe",
                              "intervention_window_check", "governed_rule_applied"}
            for episode in packet["episodes"] for event in episode["trace"]
        )
        return {"role": "power_trajectory", "start": start, "end": end,
                "delta": delta, "tested": tested, "confidence": 0.94}
    if condition == "ordinary_trace":
        _, values = event_index(packet)
        start: dict[str, float] = {}
        end: dict[str, float] = {}
        mapping = {
            "human_only_probe": "human",
            "ai_only_probe": "ai_in_use",
            "joint_probe": "distributed",
            "governed_rule_applied": "institution",
        }
        for event_type, bearer in mapping.items():
            numeric = [float(value) for value in values.get(event_type, [])
                       if isinstance(value, (int, float))]
            if numeric:
                start[bearer], end[bearer] = numeric[0], numeric[-1]
        delta = {key: end[key] - start[key] for key in start if key in end}
        return {"role": "power_trajectory", "start": start, "end": end,
                "delta": delta, "tested": bool(delta or end), "confidence": 0.7 if end else 0.34}
    features = result_features(packet)
    return {"role": "power_trajectory", "start": {}, "end": {},
            "delta": {"distributed": features["result_delta"]}, "tested": False,
            "confidence": 0.31}


def governance_group(packet: dict[str, Any]) -> dict[str, Any]:
    condition = packet["condition"]
    if condition == "episode_ledger":
        paths = [path for episode in packet["episodes"] for path in episode["interventions"]]
        viable = all(path["window"] != "closed" and path["authority"] == "effective"
                     and path["control"] == "bound" and path["return"] in {"occurrence", "consequence"}
                     for path in paths)
        weakest = min((1.0 if path["window"] == "open" else 0.55 if path["window"] == "narrow" else 0.0)
                      for path in paths)
        return {"role": "intervention_governance", "viable": viable,
                "weakest_path": weakest, "confidence": 0.95}
    if condition == "ordinary_trace":
        _, values = event_index(packet)
        checks = [float(value) for value in values.get("intervention_window_check", [])
                  if isinstance(value, (int, float))]
        outage = bool(values.get("provider_and_archive_unavailable"))
        viable = not checks or checks[-1] >= 0.45
        return {"role": "intervention_governance", "viable": viable,
                "weakest_path": checks[-1] if checks else (0.55 if outage else 0.7),
                "confidence": 0.75 if checks else 0.51}
    observed = [episode.get("consequence_observed") for episode in packet["episodes"]]
    viable = all(value is not False for value in observed)
    return {"role": "intervention_governance", "viable": viable,
            "weakest_path": 0.45 if viable else 0.2, "confidence": 0.34}


def rival_group(packet: dict[str, Any]) -> dict[str, Any]:
    condition = packet["condition"]
    if condition == "episode_ledger":
        confounders = [item for episode in packet["episodes"]
                       for item in episode["limitations"]["confounders"]]
        missing = [item for episode in packet["episodes"]
                   for item in episode["limitations"]["missing"]]
        rivals = sorted({episode["next_episode"]["strongest_rival"] for episode in packet["episodes"]})
        return {"role": "rival_claim_ceiling", "confounder_strength": min(1.0, len(confounders) * 0.35),
                "missing_path": bool(missing), "rivals": rivals, "confidence": 0.92}
    if condition == "ordinary_trace":
        _, values = event_index(packet)
        samples = [float(value) for value in values.get("case_distribution_sample", [])
                   if isinstance(value, (int, float))]
        shift = abs(samples[-1] - samples[0]) if len(samples) >= 2 else 0.0
        outage = bool(values.get("provider_and_archive_unavailable"))
        return {"role": "rival_claim_ceiling", "confounder_strength": min(1.0, shift * 2.0),
                "missing_path": False, "rivals": ["outage difficulty"] if outage else [],
                "confidence": 0.7 if samples or outage else 0.4}
    return {"role": "rival_claim_ceiling", "confounder_strength": 0.0,
            "missing_path": True, "rivals": [], "confidence": 0.25}


def distribution(label: str, labels: tuple[str, ...], confidence: float) -> dict[str, float]:
    confidence = max(1 / len(labels), min(0.98, confidence))
    other = (1.0 - confidence) / (len(labels) - 1)
    return {candidate: round(confidence if candidate == label else other, 6) for candidate in labels}


def aggregate(packet: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_role = {finding["role"]: finding for finding in findings}
    returns = by_role["retention_return"]
    power = by_role["power_trajectory"]
    governance = by_role["intervention_governance"]
    rival = by_role["rival_claim_ceiling"]
    condition = packet["condition"]
    features = result_features(packet)
    transition = "none"
    bearer = "none"

    if condition == "performance_only":
        if features["result_delta"] >= 0.055:
            transition, bearer = "acquired", "distributed"
        elif features["result_delta"] <= -0.055:
            transition, bearer = "lost", "none"
        confidence = 0.39
    elif condition == "ordinary_trace":
        _, values = event_index(packet)
        delta = power["delta"]
        if rival["confounder_strength"] >= 0.25 and not returns["returned"]:
            transition, bearer = "none", "none"
        elif not governance["viable"]:
            transition, bearer = "lost", "none"
        elif values.get("provider_and_archive_unavailable"):
            transition, bearer = "lost", "none"
        elif values.get("governed_rule_applied") and returns["returned"]:
            transition, bearer = "acquired", "institution"
        elif values.get("model_configuration_changed") and delta.get("ai_in_use", 0) > 0.15:
            transition, bearer = "redistributed", "ai_in_use"
        elif delta.get("human", 0) > 0.12 and returns["returned"]:
            transition, bearer = "acquired", "human"
        elif delta.get("human", 0) < -0.12 and delta.get("distributed", 0) > 0.05 and returns["returned"]:
            transition, bearer = "redistributed", "distributed"
        elif "human" in delta and abs(delta["human"]) < 0.08 and returns["returned"]:
            transition, bearer = "preserved", "human"
        elif returns["returned"] and features["result_delta"] > 0.07:
            transition, bearer = "acquired", "distributed"
        confidence = 0.74 if power["tested"] or returns["returned"] else 0.58
    else:
        start, end, delta = power["start"], power["end"], power["delta"]
        has_test_posture = any(episode["work"]["assistance_posture"] == "test"
                               for episode in packet["episodes"])
        if rival["confounder_strength"] >= 0.25 and not returns["returned"]:
            transition, bearer = "none", "none"
        elif not returns["returned"]:
            transition, bearer = "none", "none"
        elif not governance["viable"]:
            transition, bearer = "lost", "none"
        elif max(end.values()) < 0.5:
            transition, bearer = "lost", "none"
        elif start["human"] < 0.5 <= end["human"] and delta["human"] > 0.15:
            transition, bearer = "acquired", "human"
        elif start["institution"] < 0.5 <= end["institution"] and delta["institution"] > 0.15:
            transition, bearer = "acquired", "institution"
        elif delta["ai_in_use"] > 0.2 and end["ai_in_use"] >= end["human"]:
            transition, bearer = "redistributed", "ai_in_use"
        elif delta["human"] < -0.12 and delta["distributed"] > 0.08:
            transition, bearer = "redistributed", "distributed"
        elif has_test_posture and abs(delta["human"]) < 0.08:
            transition, bearer = "preserved", "human"
        elif delta["human"] > 0.15:
            transition, bearer = "acquired", "human"
        elif max(end.values()) < max(start.values()) - 0.15:
            transition, bearer = "lost", "none"
        confidence = 0.92 if transition != "none" else 0.88

    recursion = bool(returns["returned"] and returns["strength"] >= 0.4)
    transition_probs = distribution(transition, TRANSITIONS, confidence)
    bearer_confidence = max(0.34, confidence - (0.05 if bearer != "none" else 0.0))
    return {
        "assessment_version": ASSESSOR_VERSION,
        "packet_id": packet["packet_id"],
        "condition": condition,
        "series_id": packet["series_id"],
        "predicted_transition": transition,
        "predicted_bearer": bearer,
        "predicted_recursion": recursion,
        "predicted_intervention_viable": governance["viable"],
        "confidence": confidence,
        "transition_probabilities": transition_probs,
        "bearer_probabilities": distribution(bearer, BEARERS, bearer_confidence),
        "role_findings": findings,
    }


def assess_packet(packet: dict[str, Any]) -> dict[str, Any]:
    findings = [
        boundary_group(packet),
        return_group(packet),
        power_group(packet),
        governance_group(packet),
        rival_group(packet),
    ]
    return aggregate(packet, findings)


def run(data_dir: Path = DEFAULT_DATA) -> int:
    rows = []
    for condition in CONDITIONS:
        packets = read_jsonl(data_dir / f"packets.{condition}.jsonl")
        rows.extend(assess_packet(packet) for packet in packets)
    rows.sort(key=lambda row: (row["condition"], row["series_id"]))
    assessment_path = data_dir / "assessments.jsonl"
    write_jsonl(assessment_path, rows)
    manifest = {
        "assessment_version": ASSESSOR_VERSION,
        "assessments": len(rows),
        "conditions": list(CONDITIONS),
        "assessor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assessments_sha256": hashlib.sha256(assessment_path.read_bytes()).hexdigest(),
        "packet_sha256": {
            condition: hashlib.sha256((data_dir / f"packets.{condition}.jsonl").read_bytes()).hexdigest()
            for condition in CONDITIONS
        },
    }
    (data_dir / "assessment_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    count = run(args.data)
    print(f"wrote {count} blinded assessments to {args.data / 'assessments.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
