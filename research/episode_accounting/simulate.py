#!/usr/bin/env python3
"""Generate deterministic longitudinal episode series and blinded evidence packets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import yaml

try:
    from . import GENERATOR_VERSION, SCHEMA_VERSION
except ImportError:  # direct script execution
    from __init__ import GENERATOR_VERSION, SCHEMA_VERSION


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "case_families.yaml"
DEFAULT_OUTPUT = ROOT / "data"


MECHANISM_NOTES = {
    "structured_reappropriation": {
        "decision": "keep retrieval-before-reveal and test unaided transfer again",
        "hypothesis": "independent reconstruction plus feedback is becoming usable practice",
        "rival": "later cases may be easier or the probe may teach the tested distinction",
    },
    "assisted_substitution": {
        "decision": "retain assistance but add an unaided reconstruction checkpoint",
        "hypothesis": "artifact-supported fluency may be replacing unassisted reconstruction",
        "rival": "the unassisted probe may differ in difficulty or available time",
    },
    "authority_window_erosion": {
        "decision": "slow the consequential path until stop authority and timing are restored",
        "hypothesis": "the nominal reviewer no longer has an effective intervention window",
        "rival": "the late intervention may be an isolated routing failure",
    },
    "institutional_rule_learning": {
        "decision": "retain the rule provisionally and audit its next two applications",
        "hypothesis": "a reviewed exception has become a governed institutional response",
        "rival": "the later decision may independently fit the same obvious rule",
    },
    "repetition_without_retention": {
        "decision": "make no adaptation and preserve the absence of a return claim",
        "hypothesis": "similar outputs reflect repeated exposure rather than retained re-entry",
        "rival": "an unobserved human habit may carry a difference outside the record",
    },
    "retained_but_unused": {
        "decision": "do not treat storage as learning; test whether the artifact is ever retrieved",
        "hypothesis": "the saved artifact is inert in later work",
        "rival": "participants may consult it through an uninstrumented path",
    },
    "case_mix_shift": {
        "decision": "hold the interface stable and compare matched cases before adapting",
        "hypothesis": "apparent improvement is explained by easier later cases",
        "rival": "a real capability change may coexist with the case-mix shift",
    },
    "stable_rehearsal": {
        "decision": "preserve the rehearsal cadence without increasing surveillance",
        "hypothesis": "periodic degraded-mode practice is maintaining recovery capability",
        "rival": "repeated probes may be too similar to establish transfer",
    },
    "provider_dependency": {
        "decision": "restore a recoverable mode before resuming normal automation",
        "hypothesis": "normal performance depended on provider and archive access",
        "rival": "the outage episode may be unusually difficult independent of access loss",
    },
    "ai_model_upgrade": {
        "decision": "retain the upgrade provisionally and re-test human detection and repair",
        "hypothesis": "the upgraded AI-in-use now realizes most of the focal power",
        "rival": "the later task distribution may better match the upgraded model",
    },
}


def clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def semantic_hash(family: dict[str, Any]) -> str:
    payload = json.dumps(family, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def initial_state(mechanism: str, rng: random.Random) -> dict[str, dict[str, float]]:
    jitter = lambda: rng.uniform(-0.025, 0.025)
    state = {
        "human": {
            "independent_judgment": clamp(0.67 + jitter()),
            "recovery_skill": clamp(0.66 + jitter()),
            "attention": clamp(0.76 + jitter()),
            "calibration": clamp(0.58 + jitter()),
        },
        "ai_in_use": {
            "quality": clamp(0.59 + jitter()),
            "context_integrity": clamp(0.62 + jitter()),
            "tool_access": clamp(0.72 + jitter()),
            "personalization": clamp(0.25 + jitter()),
        },
        "institution": {
            "authority": clamp(0.78 + jitter()),
            "intervention_window": clamp(0.76 + jitter()),
            "rule_strength": clamp(0.34 + jitter()),
            "review_capacity": clamp(0.65 + jitter()),
        },
        "affected_world": {
            "source_access": clamp(0.78 + jitter()),
            "case_difficulty": clamp(0.62 + jitter()),
            "time_pressure": clamp(0.48 + jitter()),
            "external_exposure": clamp(0.55 + jitter()),
        },
        "relation": {
            "artifact_support": 0.05,
            "practice_support": 0.05,
            "workflow_lock_in": 0.05,
            "configuration_support": 0.05,
        },
    }

    if mechanism == "structured_reappropriation":
        state["human"]["independent_judgment"] = 0.42
        state["human"]["recovery_skill"] = 0.44
    elif mechanism == "institutional_rule_learning":
        state["human"]["independent_judgment"] = 0.47
        state["ai_in_use"]["quality"] = 0.48
        state["institution"]["rule_strength"] = 0.25
        state["institution"]["review_capacity"] = 0.47
    elif mechanism == "provider_dependency":
        state["human"]["independent_judgment"] = 0.62
        state["human"]["recovery_skill"] = 0.61
        state["relation"]["artifact_support"] = 0.38
    elif mechanism == "ai_model_upgrade":
        state["ai_in_use"]["quality"] = 0.43
        state["ai_in_use"]["context_integrity"] = 0.47
    return state


def power_profile(state: dict[str, dict[str, float]]) -> dict[str, float]:
    human = min(
        state["human"]["independent_judgment"],
        state["human"]["recovery_skill"],
        state["human"]["attention"],
        state["institution"]["authority"],
        state["institution"]["intervention_window"],
        state["affected_world"]["source_access"],
    )
    ai = min(
        state["ai_in_use"]["quality"],
        state["ai_in_use"]["context_integrity"],
        state["ai_in_use"]["tool_access"],
    )
    institution = min(
        state["institution"]["rule_strength"],
        state["institution"]["review_capacity"],
        state["institution"]["authority"],
    )
    support = max(
        state["relation"]["artifact_support"],
        state["relation"]["practice_support"],
        state["relation"]["configuration_support"],
    )
    lock_penalty = state["relation"]["workflow_lock_in"] * 0.28
    components = sorted([human, ai, institution], reverse=True)
    distributed = clamp(0.56 * components[0] + 0.24 * components[1] + 0.28 * support - lock_penalty)
    return {
        "human": clamp(human),
        "ai_in_use": clamp(ai),
        "institution": clamp(institution),
        "distributed": distributed,
    }


def evolve(state: dict[str, dict[str, float]], mechanism: str, ordinal: int) -> None:
    h, a, i, w, r = (
        state["human"], state["ai_in_use"], state["institution"],
        state["affected_world"], state["relation"],
    )
    if mechanism == "structured_reappropriation" and ordinal >= 2:
        h["independent_judgment"] = clamp(h["independent_judgment"] + 0.055)
        h["recovery_skill"] = clamp(h["recovery_skill"] + 0.05)
        h["calibration"] = clamp(h["calibration"] + 0.025)
        r["practice_support"] = clamp(r["practice_support"] + 0.13)
    elif mechanism == "assisted_substitution" and ordinal >= 2:
        h["independent_judgment"] = clamp(h["independent_judgment"] - 0.032)
        h["recovery_skill"] = clamp(h["recovery_skill"] - 0.038)
        a["quality"] = clamp(a["quality"] + 0.025)
        a["personalization"] = clamp(a["personalization"] + 0.06)
        r["artifact_support"] = clamp(r["artifact_support"] + 0.14)
    elif mechanism == "authority_window_erosion" and ordinal >= 2:
        i["intervention_window"] = clamp(i["intervention_window"] - 0.075)
        i["authority"] = clamp(i["authority"] - 0.035)
        h["attention"] = clamp(h["attention"] - 0.025)
        a["quality"] = clamp(a["quality"] + 0.02)
        r["workflow_lock_in"] = clamp(r["workflow_lock_in"] + 0.14)
    elif mechanism == "institutional_rule_learning" and ordinal >= 5:
        i["rule_strength"] = clamp(i["rule_strength"] + 0.18)
        i["review_capacity"] = clamp(i["review_capacity"] + 0.09)
        r["artifact_support"] = clamp(r["artifact_support"] + 0.08)
    elif mechanism == "retained_but_unused" and ordinal >= 2:
        # Storage is represented by the carrier record. It does not become causal support
        # until a later episode retrieves it, which this mechanism deliberately never does.
        pass
    elif mechanism == "case_mix_shift" and ordinal >= 2:
        w["case_difficulty"] = clamp(w["case_difficulty"] - 0.06)
    elif mechanism == "stable_rehearsal":
        h["independent_judgment"] = clamp(h["independent_judgment"] - 0.012)
        h["recovery_skill"] = clamp(h["recovery_skill"] - 0.012)
        if ordinal in (3, 5, 7):
            h["independent_judgment"] = clamp(h["independent_judgment"] + 0.025)
            h["recovery_skill"] = clamp(h["recovery_skill"] + 0.025)
            r["practice_support"] = clamp(r["practice_support"] + 0.11)
    elif mechanism == "provider_dependency" and ordinal >= 2:
        h["independent_judgment"] = clamp(h["independent_judgment"] - 0.035)
        h["recovery_skill"] = clamp(h["recovery_skill"] - 0.042)
        a["quality"] = clamp(a["quality"] + 0.025)
        r["artifact_support"] = clamp(r["artifact_support"] + 0.10)
        if ordinal == 7:
            a["quality"] = 0.18
            a["context_integrity"] = 0.16
            a["tool_access"] = 0.12
            r["artifact_support"] = 0.0
    elif mechanism == "ai_model_upgrade" and ordinal >= 4:
        a["quality"] = clamp(a["quality"] + 0.13)
        a["context_integrity"] = clamp(a["context_integrity"] + 0.11)
        a["tool_access"] = clamp(a["tool_access"] + 0.04)
        r["configuration_support"] = clamp(r["configuration_support"] + 0.16)


def profile(state: dict[str, dict[str, float]]) -> dict[str, Any]:
    return {
        "human": copy.deepcopy(state["human"]),
        "ai_in_use": copy.deepcopy(state["ai_in_use"]),
        "institution": copy.deepcopy(state["institution"]),
        "affected_world": copy.deepcopy(state["affected_world"]),
        "power": power_profile(state),
    }


def timing(mechanism: str, lag: int) -> tuple[int | None, int | None]:
    if mechanism in {"repetition_without_retention", "case_mix_shift"}:
        return None, None
    if mechanism == "retained_but_unused":
        return 2, None
    if mechanism == "provider_dependency":
        return 2, 7
    if mechanism == "ai_model_upgrade":
        return 3, 4
    source = 2
    return source, min(7, source + max(1, lag))


def mechanism_events(
    mechanism: str,
    ordinal: int,
    episode_id: str,
    source: int | None,
    target: int | None,
    carrier_id: str | None,
    entry: dict[str, Any],
    exit_: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    tick = ordinal * 10 + 5
    if source == ordinal and carrier_id:
        events.append({"tick": tick, "type": "carrier_saved", "actor": "system",
                       "object": carrier_id, "value": "retained"})
    if target == ordinal and carrier_id:
        events.append({"tick": tick + 1, "type": "carrier_loaded", "actor": "system",
                       "object": carrier_id, "value": f"from_episode_{source}"})
    if mechanism in {"structured_reappropriation", "stable_rehearsal", "provider_dependency"} and ordinal in (1, 7):
        events.append({"tick": tick + 2, "type": "human_only_probe", "actor": "human",
                       "object": "focal_power", "value": exit_["power"]["human"]})
    if mechanism == "assisted_substitution" and ordinal in (1, 7):
        events.extend([
            {"tick": tick + 2, "type": "human_only_probe", "actor": "human",
             "object": "focal_power", "value": exit_["power"]["human"]},
            {"tick": tick + 3, "type": "joint_probe", "actor": "human_ai_team",
             "object": "focal_power", "value": exit_["power"]["distributed"]},
        ])
    if mechanism == "authority_window_erosion" and ordinal in (1, 7):
        events.append({"tick": tick + 2, "type": "intervention_window_check", "actor": "human",
                       "object": "focal_action", "value": exit_["institution"]["intervention_window"]})
    if mechanism == "institutional_rule_learning" and target == ordinal:
        events.append({"tick": tick + 2, "type": "governed_rule_applied", "actor": "institution",
                       "object": carrier_id or "rule", "value": exit_["power"]["institution"]})
    if mechanism == "case_mix_shift" and ordinal in (1, 7):
        events.append({"tick": tick + 2, "type": "case_distribution_sample", "actor": "environment",
                       "object": "case_difficulty", "value": exit_["affected_world"]["case_difficulty"]})
    if mechanism == "provider_dependency" and ordinal == 7:
        events.append({"tick": tick + 3, "type": "provider_and_archive_unavailable", "actor": "environment",
                       "object": "normal_scaffolding", "value": True})
    if mechanism == "ai_model_upgrade" and ordinal in (1, 7):
        events.append({"tick": tick + 2, "type": "ai_only_probe", "actor": "ai_in_use",
                       "object": "focal_power", "value": exit_["power"]["ai_in_use"]})
    if mechanism == "ai_model_upgrade" and ordinal == 4:
        events.append({"tick": tick + 3, "type": "model_configuration_changed", "actor": "system",
                       "object": carrier_id or "configuration", "value": "version_2"})
    return events


def intervention_for(mechanism: str, ordinal: int) -> dict[str, Any]:
    if mechanism == "authority_window_erosion" and ordinal >= 6:
        return {
            "trigger": "consequential discrepancy detected",
            "grounds": ["recommendation", "partial source state"],
            "window": "closed" if ordinal == 7 else "narrow",
            "authority": "formal_only",
            "control": "inert" if ordinal == 7 else "partial",
            "return": "execution",
        }
    if mechanism == "provider_dependency" and ordinal == 7:
        return {
            "trigger": "provider and archive unavailable",
            "grounds": ["local result", "outage status"],
            "window": "narrow",
            "authority": "effective",
            "control": "partial",
            "return": "execution",
        }
    return {
        "trigger": "material uncertainty or consequence requires judgement",
        "grounds": ["source evidence", "current state", "alternatives", "constraints"],
        "window": "open",
        "authority": "effective",
        "control": "bound",
        "return": "consequence",
    }


def generate_series(
    family_name: str,
    family: dict[str, Any],
    mechanism: str,
    mechanism_cfg: dict[str, Any],
    replicate: int,
    seed: int,
    episode_count: int,
) -> dict[str, Any]:
    series_id = f"{family_name}__{replicate:02d}_{hashlib.sha1(mechanism.encode()).hexdigest()[:7]}"
    series_seed = int(hashlib.sha256(f"{seed}:{series_id}".encode()).hexdigest()[:16], 16)
    rng = random.Random(series_seed)
    state = initial_state(mechanism, rng)
    source, target = timing(mechanism, int(mechanism_cfg["return_lag"]))
    carrier_kind = mechanism_cfg["carrier_kind"]
    carrier_id = None if carrier_kind == "none" else f"{series_id}__carrier"
    spec_digest = semantic_hash(family)
    episodes = []

    for ordinal in range(1, episode_count + 1):
        episode_id = f"{series_id}__e{ordinal}"
        entry = profile(state)
        evolve(state, mechanism, ordinal)
        exit_ = profile(state)
        difficulty = exit_["affected_world"]["case_difficulty"]
        capability = max(exit_["power"].values())
        noise = rng.uniform(-0.025, 0.025)
        joint_result = clamp(0.50 + 0.46 * capability - 0.23 * difficulty + noise)
        if mechanism in {"assisted_substitution", "authority_window_erosion"}:
            joint_result = clamp(joint_result + 0.09)
        latency = round(18 + difficulty * 34 - exit_["power"]["ai_in_use"] * 8 + rng.uniform(-2, 2), 2)
        intervention = intervention_for(mechanism, ordinal)

        trace = [
            {"tick": ordinal * 10, "type": "episode_started", "actor": family["human_role"],
             "object": family["purpose"], "value": ordinal},
            {"tick": ordinal * 10 + 1, "type": "proposal_created", "actor": "ai_in_use",
             "object": family["action"], "value": "candidate"},
            {"tick": ordinal * 10 + 2, "type": "human_reviewed", "actor": family["human_role"],
             "object": family["action"], "value": intervention["control"]},
            {"tick": ordinal * 10 + 3, "type": "action_executed", "actor": "system",
             "object": family["action"], "value": True},
        ]
        trace.extend(mechanism_events(mechanism, ordinal, episode_id, source, target,
                                      carrier_id, entry, exit_))
        trace.append({"tick": ordinal * 10 + 9, "type": "episode_provisionally_closed",
                      "actor": "system", "object": episode_id, "value": joint_result})

        carrier_records = []
        if carrier_id and source == ordinal:
            retrieved = [] if target is None else [f"{series_id}__e{target}"]
            carrier_records.append({
                "carrier_id": carrier_id,
                "kind": carrier_kind,
                "retained": True,
                "available_later": True,
                "retrieved_in": retrieved,
                "transformation": "versioned and made selectively available to later work",
                "evidence_status": "observed",
            })

        return_records = []
        if target == ordinal and source is not None and carrier_id:
            effect_map = {
                "structured_reappropriation": "human",
                "assisted_substitution": "relation",
                "authority_window_erosion": "institution",
                "institutional_rule_learning": "institution",
                "stable_rehearsal": "human",
                "provider_dependency": "relation",
                "ai_model_upgrade": "ai_in_use",
            }
            return_records.append({
                "source_episode": f"{series_id}__e{source}",
                "carrier_id": carrier_id,
                "effect_on": effect_map[mechanism],
                "made_difference": True,
                "evidence_status": "observed" if mechanism != "assisted_substitution" else "inferred",
            })

        unresolved = []
        if ordinal == episode_count:
            unresolved.append(f"longer-horizon {family['outside_return']}")
        elif ordinal >= max(1, episode_count - 2):
            unresolved.append(f"delayed {family['outside_return']}")

        confounders = []
        contamination = []
        missing = []
        if mechanism == "case_mix_shift":
            confounders.append("later cases differ materially in difficulty")
        if mechanism in {"structured_reappropriation", "stable_rehearsal"}:
            contamination.append("the capability probe may itself produce practice")
        if mechanism == "retained_but_unused":
            missing.append("unobserved consultation outside the instrumented path")
        if mechanism == "provider_dependency" and ordinal == 7:
            confounders.append("the outage case may impose unusual difficulty")

        notes = MECHANISM_NOTES[mechanism]
        status_consequence = not (mechanism == "authority_window_erosion" and ordinal == 7)
        episode = {
            "record_version": SCHEMA_VERSION,
            "episode_id": episode_id,
            "series_id": series_id,
            "ordinal": ordinal,
            "spec_ref": {"loop": family["loop"], "semantic_hash": spec_digest},
            "boundary": {
                "purpose": family["purpose"],
                "start": f"case {ordinal} accepted with a declared decision objective",
                "provisional_closure": "bounded action decided and immediate execution state recorded",
                "unresolved_returns": unresolved,
                "overlaps": [],
            },
            "entry_profile": entry,
            "work": {
                "assistance_posture": "test" if mechanism == "stable_rehearsal" and ordinal in (3, 5, 7)
                                      else "automate" if mechanism == "authority_window_erosion"
                                      else "advise",
                "case_difficulty": difficulty,
                "joint_result": joint_result,
                "latency": latency,
            },
            "interventions": [intervention],
            "operational_status": {
                "proposed": True,
                "authorized": True,
                "invoked": True,
                "executed": True,
                "occurred_outside": True,
                "consequence_observed": status_consequence,
                "adjudicated": status_consequence,
                "repaired": None if status_consequence else False,
            },
            "exit_profile": exit_,
            "carriers": carrier_records,
            "returns": return_records,
            "next_episode": {
                "decision": notes["decision"],
                "mechanism": notes["hypothesis"],
                "strongest_rival": notes["rival"],
                "evidence_deadline": f"episode {min(episode_count, ordinal + 2)} review",
                "expiry": "after two later cases without confirming evidence",
                "rollback": "restore the prior fixed configuration and preserve both versions",
            },
            "limitations": {
                "contamination": contamination,
                "confounders": confounders,
                "missing": missing,
                "retention_policy": "retain claim-scaled state and delete raw private interaction after scoring",
            },
            "trace": sorted(trace, key=lambda event: event["tick"]),
        }
        episodes.append(episode)

    recursion = mechanism not in {
        "repetition_without_retention", "retained_but_unused", "case_mix_shift"
    }
    intervention_viable = mechanism not in {"authority_window_erosion", "provider_dependency"}
    return {
        "generator_version": GENERATOR_VERSION,
        "seed": series_seed,
        "series_id": series_id,
        "family": family_name,
        "focal_power": family["focal_power"],
        "episodes": episodes,
        "ground_truth": {
            "mechanism": mechanism,
            "transition": mechanism_cfg["target_transition"],
            "bearer": mechanism_cfg["target_bearer"],
            "recursion": recursion,
            "source_episode": None if source is None else f"{series_id}__e{source}",
            "target_episode": None if target is None else f"{series_id}__e{target}",
            "carrier_kind": carrier_kind,
            "intervention_viable": intervention_viable,
        },
    }


def project(series: dict[str, Any], condition: str) -> dict[str, Any]:
    base = {
        "packet_version": "episode-packet-0.1",
        "packet_id": f"{series['series_id']}__{condition}",
        "condition": condition,
        "series_id": series["series_id"],
        "family": series["family"],
        "focal_power": series["focal_power"],
    }
    if condition == "performance_only":
        base["episodes"] = [
            {
                "episode_id": e["episode_id"],
                "ordinal": e["ordinal"],
                "joint_result": e["work"]["joint_result"],
                "latency": e["work"]["latency"],
                "executed": e["operational_status"]["executed"],
                "consequence_observed": e["operational_status"]["consequence_observed"],
            }
            for e in series["episodes"]
        ]
    elif condition == "ordinary_trace":
        base["episodes"] = [
            {
                "episode_id": e["episode_id"],
                "ordinal": e["ordinal"],
                "joint_result": e["work"]["joint_result"],
                "latency": e["work"]["latency"],
                "trace": e["trace"],
            }
            for e in series["episodes"]
        ]
    elif condition == "episode_ledger":
        base["episodes"] = copy.deepcopy(series["episodes"])
    else:
        raise ValueError(f"unknown condition: {condition}")
    return base


def validate_episode_shape(episode: dict[str, Any]) -> list[str]:
    required = {
        "record_version", "episode_id", "series_id", "ordinal", "spec_ref", "boundary",
        "entry_profile", "work", "interventions", "operational_status", "exit_profile",
        "carriers", "returns", "next_episode", "limitations", "trace",
    }
    errors = []
    missing = required - set(episode)
    if missing:
        errors.append(f"missing episode keys: {sorted(missing)}")
    if episode.get("record_version") != SCHEMA_VERSION:
        errors.append("wrong record_version")
    if not isinstance(episode.get("ordinal"), int) or episode.get("ordinal", 0) < 1:
        errors.append("ordinal must be a positive integer")
    for name in ("entry_profile", "exit_profile"):
        if set((episode.get(name) or {})) != {"human", "ai_in_use", "institution", "affected_world", "power"}:
            errors.append(f"{name} does not separate the four bearers and power profile")
    return errors


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(config_path: Path = DEFAULT_CONFIG, output_dir: Path = DEFAULT_OUTPUT) -> dict[str, int]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    series_records = []
    packets = {condition: [] for condition in ("performance_only", "ordinary_trace", "episode_ledger")}
    for family_name, family in config["families"].items():
        for mechanism, mechanism_cfg in config["mechanisms"].items():
            for replicate in range(1, int(config["replicates_per_mechanism"]) + 1):
                series = generate_series(
                    family_name, family, mechanism, mechanism_cfg, replicate,
                    int(config["seed"]), int(config["episodes_per_series"]),
                )
                for episode in series["episodes"]:
                    errors = validate_episode_shape(episode)
                    if errors:
                        raise ValueError(f"{episode['episode_id']}: {'; '.join(errors)}")
                series_records.append(series)
                for condition in packets:
                    packets[condition].append(project(series, condition))

    series_records.sort(key=lambda item: item["series_id"])
    series_path = output_dir / "synthetic_series.jsonl"
    write_jsonl(series_path, series_records)
    packet_paths = {}
    for condition, records in packets.items():
        records.sort(key=lambda item: item["series_id"])
        path = output_dir / f"packets.{condition}.jsonl"
        write_jsonl(path, records)
        packet_paths[condition] = path
    manifest = {
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "seed": int(config["seed"]),
        "series": len(series_records),
        "episodes": sum(len(series["episodes"]) for series in series_records),
        "families": sorted(config["families"]),
        "mechanisms": sorted(config["mechanisms"]),
        "conditions": sorted(packets),
        "source_hashes": {
            "case_families.yaml": file_sha256(config_path),
            "episode.schema.json": file_sha256(ROOT / "episode.schema.json"),
            "series.schema.json": file_sha256(ROOT / "series.schema.json"),
        },
        "generated_hashes": {
            "synthetic_series.jsonl": file_sha256(series_path),
            **{path.name: file_sha256(path) for path in packet_paths.values()},
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"series": manifest["series"], "episodes": manifest["episodes"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    counts = generate(args.config, args.output)
    print(f"generated {counts['series']} series / {counts['episodes']} episodes in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
