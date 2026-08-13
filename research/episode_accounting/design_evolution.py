#!/usr/bin/env python3
"""Infer LoopSpec revisions from typed logs and replay paired synthetic futures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

try:
    from . import simulate
except ImportError:  # direct script execution
    import simulate


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
DEFAULT_DATA = ROOT / "data"
DEFAULT_DESIGNS = ROOT / "designs"
DEFAULT_CONFIG = ROOT / "case_families.yaml"

PATTERN_ORDER = (
    "continue_transfer_practice",
    "restore_human_recovery",
    "restore_intervention_window",
    "audit_returned_rule",
    "make_retention_testable",
    "hold_for_matched_comparison",
    "preserve_degraded_rehearsal",
    "install_degraded_mode",
    "revalidate_model_change",
)

PATTERNS: dict[str, dict[str, Any]] = {
    "continue_transfer_practice": {
        "title": "Continue retrieval-before-reveal practice",
        "kind": "behavior",
        "burden": 0.10,
        "observation": "delayed_human_transfer",
        "belief": "human_transfer_is_becoming_retained",
        "action": "continue_retrieval_before_reveal",
        "question": "Does unaided capability transfer to later cases?",
        "trigger": "delayed unaided transfer remains above the baseline margin",
        "source": "typed human-only probes joined across episodes",
    },
    "restore_human_recovery": {
        "title": "Restore an unaided recovery checkpoint",
        "kind": "behavior",
        "burden": 0.20,
        "observation": "unaided_recovery_capability",
        "belief": "human_recovery_remains_available",
        "action": "run_unaided_recovery_checkpoint",
        "question": "Can the human still recover the focal task without assistance?",
        "trigger": "unaided recovery falls below the retained-capability floor",
        "source": "typed human-only removal probes",
    },
    "restore_intervention_window": {
        "title": "Restore a pre-execution authority window",
        "kind": "behavior",
        "burden": 0.22,
        "observation": "decision_to_execution_window",
        "belief": "intervention_path_is_live",
        "action": "require_pre_execution_confirmation",
        "question": "Can the accountable human still stop the action before consequence?",
        "trigger": "the effective intervention window is too narrow",
        "source": "authority and intervention-window checks",
    },
    "audit_returned_rule": {
        "title": "Audit a returned institutional rule",
        "kind": "evidence",
        "burden": 0.04,
        "observation": "governed_rule_outcome",
        "belief": "returned_rule_remains_warranted",
        "action": "review_returned_rule",
        "question": "Does the returned rule still improve decisions against outside outcomes?",
        "trigger": "a governed rule has returned into later work",
        "source": "governed-rule application joined to outside consequence",
    },
    "make_retention_testable": {
        "title": "Make carrier retrieval or expiry observable",
        "kind": "evidence",
        "burden": 0.08,
        "observation": "carrier_retrieval_or_expiry",
        "belief": "retained_carrier_is_causally_used",
        "action": "test_or_expire_retained_carrier",
        "question": "Was the retained carrier retrieved and made action-relevant later?",
        "trigger": "a retained carrier has no later uptake evidence",
        "source": "stable carrier identity across save, load, and expiry events",
    },
    "hold_for_matched_comparison": {
        "title": "Hold redesign until a matched-case comparison",
        "kind": "evidence",
        "burden": 0.03,
        "observation": "matched_case_capability_result",
        "belief": "apparent_gain_survives_case_matching",
        "action": "run_matched_case_review",
        "question": "Does the apparent improvement survive matched case difficulty?",
        "trigger": "case mix changed enough to rival a capability explanation",
        "source": "case-distribution samples joined to capability results",
    },
    "preserve_degraded_rehearsal": {
        "title": "Preserve degraded-mode rehearsal",
        "kind": "behavior",
        "burden": 0.10,
        "observation": "degraded_mode_human_capability",
        "belief": "degraded_mode_recovery_is_preserved",
        "action": "run_degraded_mode_rehearsal",
        "question": "Does unaided capability remain available under degraded conditions?",
        "trigger": "the scheduled degraded-mode rehearsal is due",
        "source": "typed human-only probes with assistance removed",
    },
    "install_degraded_mode": {
        "title": "Install a locally recoverable degraded mode",
        "kind": "behavior",
        "burden": 0.26,
        "observation": "provider_and_archive_availability",
        "belief": "local_fallback_is_usable",
        "action": "switch_to_local_degraded_mode",
        "question": "Can the focal task continue when provider and archive access disappear?",
        "trigger": "provider or archive access is unavailable",
        "source": "outside availability checks and a local fallback probe",
    },
    "revalidate_model_change": {
        "title": "Revalidate a changed model configuration",
        "kind": "behavior",
        "burden": 0.14,
        "observation": "post_change_component_capability",
        "belief": "changed_configuration_preserves_recovery",
        "action": "run_post_change_component_validation",
        "question": "Which component realizes the focal power after the configuration change?",
        "trigger": "the model or tool configuration changes materially",
        "source": "configuration identity plus human-only and AI-only probes",
    },
}

EXPECTED_BUNDLES = {
    "structured_reappropriation": ("continue_transfer_practice",),
    "assisted_substitution": ("restore_human_recovery",),
    "authority_window_erosion": ("restore_intervention_window",),
    "institutional_rule_learning": ("audit_returned_rule",),
    "repetition_without_retention": (),
    "retained_but_unused": ("make_retention_testable",),
    "case_mix_shift": ("hold_for_matched_comparison",),
    "stable_rehearsal": ("preserve_degraded_rehearsal",),
    "provider_dependency": ("restore_human_recovery", "install_degraded_mode"),
    "ai_model_upgrade": ("revalidate_model_change",),
}

BUNDLE_NAMES = {
    (): "unchanged",
    ("continue_transfer_practice",): "transfer_practice",
    ("restore_human_recovery",): "human_recovery",
    ("restore_intervention_window",): "intervention_window",
    ("audit_returned_rule",): "returned_rule_audit",
    ("make_retention_testable",): "carrier_uptake",
    ("hold_for_matched_comparison",): "matched_case_hold",
    ("preserve_degraded_rehearsal",): "degraded_rehearsal",
    ("restore_human_recovery", "install_degraded_mode"): "provider_resilience",
    ("revalidate_model_change",): "model_change_revalidation",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def normalized(patterns: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    present = set(patterns)
    return tuple(pattern for pattern in PATTERN_ORDER if pattern in present)


def trace_events(packet: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for episode in packet["episodes"]:
        for event in episode.get("trace", []):
            rows.append({"episode_id": episode["episode_id"], **event})
    return sorted(rows, key=lambda row: (row["tick"], row["episode_id"]))


def infer_design(packet: dict[str, Any]) -> dict[str, Any]:
    """Infer a design bundle using only a blinded ordinary-trace packet."""
    if packet.get("condition") != "ordinary_trace" or "ground_truth" in packet:
        raise ValueError("design inference requires a blinded ordinary_trace packet")

    events = trace_events(packet)
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_type[event["type"]].append(event)

    patterns: list[str] = []
    evidence: dict[str, list[str]] = defaultdict(list)

    def delta(event_type: str) -> float | None:
        rows = by_type[event_type]
        if len(rows) < 2:
            return None
        return float(rows[-1]["value"]) - float(rows[0]["value"])

    def cite(pattern: str, *event_types: str) -> None:
        patterns.append(pattern)
        for event_type in event_types:
            evidence[pattern].extend(
                f"{row['episode_id']}:{event_type}@{row['tick']}" for row in by_type[event_type]
            )

    human_delta = delta("human_only_probe")
    ai_delta = delta("ai_only_probe")
    window_delta = delta("intervention_window_check")
    case_delta = delta("case_distribution_sample")
    carrier_returned = bool(by_type["carrier_saved"] and by_type["carrier_loaded"])

    if human_delta is not None and human_delta >= 0.08 and carrier_returned:
        cite("continue_transfer_practice", "human_only_probe", "carrier_saved", "carrier_loaded")
    if human_delta is not None and human_delta <= -0.08:
        cite("restore_human_recovery", "human_only_probe")
    if window_delta is not None and window_delta <= -0.15:
        cite("restore_intervention_window", "intervention_window_check")
    if by_type["governed_rule_applied"]:
        cite("audit_returned_rule", "governed_rule_applied")
    if by_type["carrier_saved"] and not by_type["carrier_loaded"]:
        cite("make_retention_testable", "carrier_saved")
    if case_delta is not None and abs(case_delta) >= 0.15:
        cite("hold_for_matched_comparison", "case_distribution_sample")
    if (human_delta is not None and abs(human_delta) <= 0.04 and carrier_returned
            and not by_type["joint_probe"]):
        cite("preserve_degraded_rehearsal", "human_only_probe", "carrier_loaded")
    if by_type["provider_and_archive_unavailable"]:
        cite("install_degraded_mode", "provider_and_archive_unavailable")
    if by_type["model_configuration_changed"] and ai_delta is not None and ai_delta >= 0.08:
        cite("revalidate_model_change", "model_configuration_changed", "ai_only_probe")

    bundle = normalized(patterns)
    proposed_paths = []
    for pattern_name in bundle:
        pattern = PATTERNS[pattern_name]
        proposed_paths.extend([
            f"observes.{pattern['observation']}",
            f"beliefs.{pattern['belief']}",
            f"actions.{pattern['action']}",
            "when[]",
            "asks_human_when[]",
        ])
    if bundle:
        proposed_paths.append("spends.review_attention")
    return {
        "series_id": packet["series_id"],
        "family": packet["family"],
        "input_condition": "ordinary_trace",
        "patterns": list(bundle),
        "design_key": BUNDLE_NAMES.get(bundle, "composed_" + hashlib.sha1("|".join(bundle).encode()).hexdigest()[:8]),
        "evidence": {pattern: sorted(set(evidence[pattern])) for pattern in bundle},
        "proposed_paths": proposed_paths,
        "claim_ceiling": "candidate revision for human review; not an autonomous production mutation",
    }


def base_spec(family_name: str, family: dict[str, Any], design_key: str) -> dict[str, Any]:
    del family_name, design_key  # Alternative files are versions of the same represented loop.
    human_role = family["human_role"]
    return {
        "loop": family["loop"],
        "runs": "per_case",
        "boundary": {
            "drawn_by": human_role,
            "purpose": family["purpose"],
            "inside": [family["loop"], family["artifact"], "typed occurrence log"],
            "outside": [family["outside_return"], family["affected_party"]],
        },
        "goal": {
            "resilient_focal_power": {
                "keep": "above 0.60 in normal and degraded conditions",
                "unit": "capability score",
            }
        },
        "beliefs": {
            "focal_power_is_viable": {
                "question": family["focal_power"],
                "how": "judgement from typed probes and outside consequence",
                "explains": "resilient_focal_power",
                "settled_by": "outside_consequence",
                "safe_to_repeat": "episode id plus semantic LoopSpec digest",
                "checked_by": "five-case capability outcome review",
                "checked_against": "outside_consequence",
                "scoring_rule": "normal result, removal-probe result, and intervention viability",
                "window": "five later cases",
                "adjusts": "method",
                "every": "after five cases",
            }
        },
        "observes": {
            "joint_result": {
                "informs": ["focal_power_is_viable", "resilient_focal_power"],
                "origin": "ourselves",
                "how": "calculated",
                "source": "typed episode closure event",
            },
            "outside_consequence": {
                "informs": ["focal_power_is_viable", "resilient_focal_power"],
                "origin": "outside",
                "how": "measured",
                "source": family["outside_return"],
            },
            "case_context": {
                "informs": ["focal_power_is_viable", "resilient_focal_power"],
                "origin": "outside",
                "how": "measured",
                "source": "case intake and affected-world state",
            },
        },
        "processes": {
            "focal_work": {
                "description": f"The work through which {family['action']} affects later outcomes.",
                "location": "interface",
                "observed_as": ["joint_result", "outside_consequence"],
            }
        },
        "actions": {
            "execute_focal_action": {
                "moves": "resilient_focal_power",
                "through": "focal_work",
                "effect": "unknown",
                "can_undo": "costly",
                "needs_approval": human_role,
                "effect_after": "the next outside consequence",
                "consumes": ["review_attention"],
            },
            "defer_focal_action": {
                "moves": "resilient_focal_power",
                "through": "focal_work",
                "effect": "unknown",
                "can_undo": "yes",
                "needs_approval": human_role,
                "effect_after": "the next case",
            }
        },
        "spends": {
            "review_attention": {
                "limit": "two consequential reviews per case",
                "replenished": "the next case",
                "spent_by": ["execute_focal_action"],
            }
        },
        "when": [
            {
                "if": "review attention is low",
                "reads": ["review_attention"],
                "do": "defer_focal_action",
            },
            {
                "if": "the focal power is viable and the resilient-capability target can be met",
                "reads": ["focal_power_is_viable", "resilient_focal_power"],
                "against": ["resilient_focal_power"],
                "do": "execute_focal_action",
            },
        ],
        "asks_human_when": ["the focal belief is unresolved before a consequential action"],
        "asks_human": human_role,
        "people": {
            human_role: {
                "human": True,
                "loses_if_wrong": family["affected_party"],
                "sees": ["focal_power_is_viable", "resilient_focal_power"],
            }
        },
        "never": ["treat successful joint output alone as evidence that a person learned"],
        "not_modelling": [f"the longer-horizon dynamics of {family['outside_return']} beyond five later cases"],
    }


def materialize_spec(family_name: str, family: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    spec = base_spec(family_name, family, proposal["design_key"])
    for pattern_name in proposal["patterns"]:
        pattern = PATTERNS[pattern_name]
        observation = pattern["observation"]
        belief = pattern["belief"]
        action = pattern["action"]
        spec["observes"][observation] = {
            "informs": belief,
            "origin": "outside" if pattern_name == "install_degraded_mode" else "ourselves",
            "how": "measured" if pattern_name in {"install_degraded_mode", "audit_returned_rule"} else "calculated",
            "source": pattern["source"],
        }
        spec["observes"]["outside_consequence"]["informs"].append(belief)
        spec["beliefs"][belief] = {
            "question": pattern["question"],
            "how": "typed cross-episode evidence join",
            "explains": "resilient_focal_power",
            "settled_by": "outside_consequence",
            "safe_to_repeat": "episode id, probe condition, and artifact or configuration digest",
            "checked_by": "five-case post-revision review",
            "checked_against": "outside_consequence",
            "scoring_rule": "paired capability and governance difference from the prior design",
            "window": "five later cases",
            "adjusts": "method",
            "every": "after each five-case window",
        }
        spec["actions"][action] = {
            "moves": "resilient_focal_power",
            "through": "focal_work",
            "effect": "increase" if pattern["kind"] == "behavior" else "unknown",
            "can_undo": "yes",
            "needs_approval": family["human_role"],
            "effect_after": "within the next five cases",
            "consumes": ["review_attention"],
        }
        spec["when"].append({
            "if": pattern["trigger"],
            "reads": [belief],
            "do": action,
        })
        spec["asks_human_when"].append(pattern["trigger"])
        spec["people"][family["human_role"]]["sees"].append(belief)
        spec["spends"]["review_attention"]["spent_by"].append(action)
    return spec


def validate_spec(path: Path) -> dict[str, Any]:
    command = [sys.executable, str(REPO_ROOT / "tools" / "loopspec.py"), "check", str(path), "--json"]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if not result.stdout.strip():
        return {"valid": False, "errors": [result.stderr.strip() or f"exit {result.returncode}"]}
    parsed = json.loads(result.stdout)
    parsed["returncode"] = result.returncode
    return parsed


def write_designs(
    proposals: list[dict[str, Any]], families: dict[str, Any], output_dir: Path
) -> tuple[dict[tuple[str, str], str], list[dict[str, Any]]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[tuple[str, str], str] = {}
    validations = []
    for proposal in proposals:
        key = (proposal["family"], proposal["design_key"])
        if key in written:
            continue
        path = output_dir / f"{proposal['family']}.{proposal['design_key']}.loop.yaml"
        spec = materialize_spec(proposal["family"], families[proposal["family"]], proposal)
        path.write_text(yaml.safe_dump(spec, sort_keys=False, width=100))
        try:
            display_path = str(path.relative_to(ROOT))
        except ValueError:
            display_path = str(path)
        written[key] = display_path
        result = validate_spec(path)
        validations.append({
            "family": proposal["family"],
            "design_key": proposal["design_key"],
            "path": written[key],
            "valid": bool(result.get("valid")),
            "errors": result.get("errors", []),
            "findings": len(result.get("findings", [])),
        })
    return written, validations


def split_name(series: dict[str, Any]) -> str:
    replicate_one = "__01_" in series["series_id"]
    if replicate_one and series["family"] in {"investment_diligence", "software_delivery"}:
        return "development"
    if not replicate_one and series["family"] in {"support_triage", "research_evaluation"}:
        return "holdout"
    return "audit"


def reconstruct_state(series: dict[str, Any]) -> dict[str, Any]:
    mechanism = series["ground_truth"]["mechanism"]
    state = simulate.initial_state(mechanism, random.Random(int(series["seed"])))
    for ordinal in range(1, 8):
        simulate.evolve(state, mechanism, ordinal)
    return state


def increase(mapping: dict[str, float], key: str, amount: float) -> None:
    mapping[key] = simulate.clamp(mapping[key] + amount)


def apply_pattern(state: dict[str, Any], pattern: str) -> None:
    human = state["human"]
    ai = state["ai_in_use"]
    institution = state["institution"]
    relation = state["relation"]
    power = simulate.power_profile(state)

    if pattern == "continue_transfer_practice" and power["human"] < 0.85:
        increase(human, "independent_judgment", 0.025)
        increase(human, "recovery_skill", 0.025)
        increase(human, "calibration", 0.010)
        increase(relation, "practice_support", 0.025)
    elif pattern == "restore_human_recovery" and power["human"] < 0.58:
        increase(human, "independent_judgment", 0.055)
        increase(human, "recovery_skill", 0.060)
        increase(human, "attention", 0.015)
    elif pattern == "restore_intervention_window" and institution["intervention_window"] < 0.60:
        increase(institution, "intervention_window", 0.105)
        increase(institution, "authority", 0.045)
        relation["workflow_lock_in"] = simulate.clamp(relation["workflow_lock_in"] - 0.10)
    elif pattern == "audit_returned_rule" and 0.40 <= institution["rule_strength"] < 0.90:
        increase(institution, "rule_strength", 0.020)
        increase(institution, "review_capacity", 0.025)
    elif pattern == "make_retention_testable" and relation["artifact_support"] < 0.35:
        increase(relation, "artifact_support", 0.050)
        increase(human, "calibration", 0.008)
    elif pattern == "hold_for_matched_comparison":
        # This is a deliberate evidential hold, not a claimed capability intervention.
        pass
    elif pattern == "preserve_degraded_rehearsal" and power["human"] < 0.76:
        increase(human, "independent_judgment", 0.026)
        increase(human, "recovery_skill", 0.026)
        increase(relation, "practice_support", 0.020)
    elif pattern == "install_degraded_mode" and ai["tool_access"] < 0.35:
        ai["quality"] = max(ai["quality"], 0.32)
        ai["context_integrity"] = max(ai["context_integrity"], 0.34)
        ai["tool_access"] = max(ai["tool_access"], 0.36)
        relation["artifact_support"] = max(relation["artifact_support"], 0.28)
        increase(human, "independent_judgment", 0.040)
        increase(human, "recovery_skill", 0.045)
    elif pattern == "revalidate_model_change" and power["ai_in_use"] - power["human"] >= 0.10:
        increase(human, "independent_judgment", 0.020)
        increase(human, "recovery_skill", 0.022)
        increase(institution, "review_capacity", 0.012)


def evaluate_arm(series: dict[str, Any], arm: str, patterns: tuple[str, ...]) -> dict[str, Any]:
    state = reconstruct_state(series)
    mechanism = series["ground_truth"]["mechanism"]
    normal: list[float] = []
    governance: list[float] = []
    trajectories = []
    for ordinal in range(8, 13):
        simulate.evolve(state, mechanism, ordinal)
        for pattern in patterns:
            apply_pattern(state, pattern)
        power = simulate.power_profile(state)
        normal.append(power["distributed"])
        governance.append(min(state["institution"]["authority"], state["institution"]["intervention_window"]))
        trajectories.append({"episode": ordinal, **power})

    stressed = copy.deepcopy(state)
    stressed["ai_in_use"].update({"quality": 0.0, "context_integrity": 0.0, "tool_access": 0.0})
    stressed["relation"]["artifact_support"] = 0.0
    stressed["relation"]["configuration_support"] = 0.0
    stress_power = simulate.power_profile(stressed)["distributed"]
    burden = sum(float(PATTERNS[pattern]["burden"]) for pattern in patterns)
    score = 0.45 * mean(normal) + 0.30 * stress_power + 0.20 * mean(governance) - 0.05 * burden
    return {
        "series_id": series["series_id"],
        "family": series["family"],
        "split": split_name(series),
        "mechanism": mechanism,
        "arm": arm,
        "patterns": list(patterns),
        "mean_normal_power": round(mean(normal), 6),
        "removal_probe_power": round(stress_power, 6),
        "mean_governance": round(mean(governance), 6),
        "design_burden": round(burden, 6),
        "score": round(score, 6),
        "trajectory": trajectories,
    }


def shuffled_bundle(mechanism: str) -> tuple[str, ...]:
    mechanisms = sorted(EXPECTED_BUNDLES)
    index = mechanisms.index(mechanism)
    return normalized(EXPECTED_BUNDLES[mechanisms[(index + 1) % len(mechanisms)]])


def proposal_metrics(
    proposals: list[dict[str, Any]], series_by_id: dict[str, dict[str, Any]], split: str
) -> dict[str, Any]:
    selected = [proposal for proposal in proposals if split_name(series_by_id[proposal["series_id"]]) == split]
    correct = 0
    for proposal in selected:
        mechanism = series_by_id[proposal["series_id"]]["ground_truth"]["mechanism"]
        correct += tuple(proposal["patterns"]) == normalized(EXPECTED_BUNDLES[mechanism])
    return {
        "series": len(selected),
        "exact_bundle_accuracy": round(correct / len(selected), 6) if selected else 0.0,
    }


def aggregate_split(
    records: list[dict[str, Any]], proposals: list[dict[str, Any]],
    series_by_id: dict[str, dict[str, Any]], split: str,
) -> dict[str, Any]:
    rows = [row for row in records if row["split"] == split]
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_arm[row["arm"]].append(row)
    arms = {}
    for arm, arm_rows in sorted(by_arm.items()):
        arms[arm] = {
            "series": len(arm_rows),
            "mean_score": round(mean(row["score"] for row in arm_rows), 6),
            "mean_normal_power": round(mean(row["mean_normal_power"] for row in arm_rows), 6),
            "mean_removal_probe_power": round(mean(row["removal_probe_power"] for row in arm_rows), 6),
            "mean_governance": round(mean(row["mean_governance"] for row in arm_rows), 6),
            "mean_design_burden": round(mean(row["design_burden"] for row in arm_rows), 6),
        }

    paired: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        paired[row["series_id"]][row["arm"]] = row["score"]
    no_regression = mean(
        scores["log_informed"] >= scores["unchanged"] - 0.005 for scores in paired.values()
    ) if paired else 0.0
    selection = proposal_metrics(proposals, series_by_id, split)
    summary = {"arms": arms, **selection, "no_material_regression_rate": round(no_regression, 6)}
    if split == "holdout" and arms:
        log_score = arms["log_informed"]["mean_score"]
        gates = {
            "G1_score_over_unchanged": log_score - arms["unchanged"]["mean_score"] >= 0.020,
            "G2_score_over_shuffled": log_score - arms["shuffled_placebo"]["mean_score"] >= 0.010,
            "G3_oracle_regret": arms["oracle"]["mean_score"] - log_score <= 0.005,
            "G4_burden_below_maximal": arms["log_informed"]["mean_design_burden"]
            <= 0.60 * arms["maximal_controls"]["mean_design_burden"],
            "G5_no_material_regression": no_regression >= 0.90,
            "G7_bundle_selection": selection["exact_bundle_accuracy"] >= 0.90,
        }
        summary["gates"] = gates
    return summary


def report_markdown(metrics: dict[str, Any]) -> str:
    holdout = metrics["splits"]["holdout"]
    arms = holdout["arms"]
    lines = [
        "# Results: logs to LoopSpec design evolution",
        "",
        "**Run date:** 2026-08-13  ",
        f"**Corpus:** {metrics['series']} series; {holdout['series']} untouched holdout series  ",
        "**Input to proposer:** blinded ordinary typed traces only",
        "",
        "## Holdout counterfactual replay",
        "",
        "| arm | mean score | normal power | removal-probe power | governance | design burden |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "unchanged": "unchanged LoopSpec",
        "log_informed": "log-informed revision",
        "shuffled_placebo": "shuffled revision",
        "maximal_controls": "all controls",
        "oracle": "synthetic oracle",
    }
    for arm in ("unchanged", "log_informed", "shuffled_placebo", "maximal_controls", "oracle"):
        row = arms[arm]
        lines.append(
            f"| {labels[arm]} | {row['mean_score']:.3f} | {row['mean_normal_power']:.3f} | "
            f"{row['mean_removal_probe_power']:.3f} | {row['mean_governance']:.3f} | "
            f"{row['mean_design_burden']:.3f} |"
        )
    lines.extend([
        "",
        "## Frozen gates",
        "",
    ])
    all_gates = {**holdout["gates"], "G6_all_specs_valid": metrics["all_specs_valid"]}
    promotion = all(all_gates.values())
    for gate, passed in all_gates.items():
        lines.append(f"- **{gate}: {'passed' if passed else 'failed'}**")
    lines.extend([
        "",
        f"Exact holdout bundle selection was **{holdout['exact_bundle_accuracy']:.1%}**. "
        f"The no-material-regression rate was **{holdout['no_material_regression_rate']:.1%}**.",
        f" All {metrics['designs']} materialized alternatives had zero active LoopSpec design findings."
        if metrics["all_specs_clear"] else " Some structurally valid alternatives retain design findings.",
        "",
        "## Interpretation",
        "",
        "The proposer did not edit the public LoopSpec grammar. It converted typed log evidence "
        "into a small candidate design diff, materialized that diff as a valid LoopSpec, and "
        "tested it against paired future episodes. An unchanged recommendation is a legitimate "
        "result when the trace shows repetition without retention; a matched-case hold is an "
        "evidence revision rather than a claim that extra control improves capability.",
        "",
        "The oracle is not independent evidence: its bundles and the counterfactual effects are "
        "part of this simulator. Matching it establishes internal consistency and specificity, "
        "not deployment validity. The next real gate is an approved prospective comparison in "
        "which later episodes test unaided transfer, removal recovery, and intervention viability.",
        "",
        "## Decision",
        "",
        ("The log-to-design path is **provisionally supported in the synthetic laboratory**. "
         if promotion else
         "The log-to-design path **did not pass its complete synthetic promotion gate**. ")
        + "It should remain a review workflow: evidence-linked proposal, structural validation, "
        "human approval, versioned rollout, and prospective re-assessment.",
        "",
    ])
    return "\n".join(lines)


def run(
    data_dir: Path = DEFAULT_DATA,
    designs_dir: Path = DEFAULT_DESIGNS,
    config_path: Path = DEFAULT_CONFIG,
    selected_split: str | None = None,
    report_path: Path | None = ROOT / "DESIGN-EVOLUTION-RESULTS.md",
) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    series_rows = read_jsonl(data_dir / "synthetic_series.jsonl")
    packets = read_jsonl(data_dir / "packets.ordinary_trace.jsonl")
    series_by_id = {row["series_id"]: row for row in series_rows}
    if selected_split:
        allowed = {row["series_id"] for row in series_rows if split_name(row) == selected_split}
        packets = [packet for packet in packets if packet["series_id"] in allowed]
        series_rows = [row for row in series_rows if row["series_id"] in allowed]
        series_by_id = {row["series_id"]: row for row in series_rows}

    proposals = [infer_design(packet) for packet in packets]
    paths, validations = write_designs(proposals, config["families"], designs_dir)
    for proposal in proposals:
        proposal["materialized_spec"] = paths[(proposal["family"], proposal["design_key"])]

    records = []
    all_patterns = normalized(PATTERN_ORDER)
    proposal_by_id = {proposal["series_id"]: proposal for proposal in proposals}
    for series in series_rows:
        mechanism = series["ground_truth"]["mechanism"]
        bundles = {
            "unchanged": (),
            "log_informed": tuple(proposal_by_id[series["series_id"]]["patterns"]),
            "shuffled_placebo": shuffled_bundle(mechanism),
            "maximal_controls": all_patterns,
            "oracle": normalized(EXPECTED_BUNDLES[mechanism]),
        }
        for arm, bundle in bundles.items():
            records.append(evaluate_arm(series, arm, bundle))

    split_names = sorted({row["split"] for row in records})
    split_metrics = {
        split: aggregate_split(records, proposals, series_by_id, split) for split in split_names
    }
    all_specs_valid = all(row["valid"] for row in validations)
    all_specs_clear = all(row["valid"] and row["findings"] == 0 for row in validations)
    metrics = {
        "experiment_version": "log-to-design-0.1",
        "series": len(series_rows),
        "future_episodes_per_arm": 5,
        "splits": split_metrics,
        "designs": len(validations),
        "all_specs_valid": all_specs_valid,
        "all_specs_clear": all_specs_clear,
        "validations": validations,
    }
    if "holdout" in split_metrics:
        metrics["promotion_gate"] = all(split_metrics["holdout"]["gates"].values()) and all_specs_valid

    data_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(data_dir / "design_proposals.jsonl", proposals)
    write_jsonl(data_dir / "design_counterfactuals.jsonl", records)
    (data_dir / "design_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (data_dir / "design_validation.json").write_text(json.dumps(validations, indent=2, sort_keys=True) + "\n")
    if "holdout" in split_metrics and report_path is not None:
        report_path.write_text(report_markdown(metrics))
    return metrics


def check_gates(data_dir: Path = DEFAULT_DATA) -> bool:
    metrics = json.loads((data_dir / "design_metrics.json").read_text())
    passed = bool(metrics.get("promotion_gate"))
    print("PASS" if passed else "FAIL")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--designs", type=Path, default=DEFAULT_DESIGNS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--split", choices=("development", "holdout", "audit"))
    parser.add_argument("--check-gates", action="store_true")
    args = parser.parse_args()
    if args.check_gates:
        return 0 if check_gates(args.data) else 1
    metrics = run(args.data, args.designs, args.config, args.split)
    if args.split:
        print(json.dumps(metrics["splits"][args.split], indent=2, sort_keys=True))
    else:
        print(f"generated {metrics['designs']} designs from {metrics['series']} logged series")
        print("promotion gate:", "PASS" if metrics.get("promotion_gate") else "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
