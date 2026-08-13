#!/usr/bin/env python3
"""Run the prospective flashcard/transfer/recovery capability probe locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "hitl_protocol.yaml"
ITEMS_PATH = ROOT / "hitl_items.yaml"
PRIVATE_RUNS = ROOT / "private_runs"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_instrument() -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    bank = yaml.safe_load(ITEMS_PATH.read_text(encoding="utf-8"))
    return protocol, bank


def instrument_errors(protocol: dict[str, Any], bank: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    item_ids = [item["id"] for item in bank.get("items", [])]
    if len(item_ids) != len(set(item_ids)):
        errors.append("item ids must be unique")
    declared_sets = {phase["item_set"] for phase in protocol.get("phases", [])}
    actual_sets = {item["set"] for item in bank.get("items", [])}
    missing = declared_sets - actual_sets
    if missing:
        errors.append(f"item sets have no items: {sorted(missing)}")
    for item in bank.get("items", []):
        choices = bank.get("choices", {}).get(item.get("construct"), {})
        if item.get("answer") not in choices:
            errors.append(f"{item.get('id')}: answer is not valid for construct")
        if item.get("set") == "joint" and item.get("ai_suggestion") not in choices:
            errors.append(f"{item.get('id')}: joint item needs a valid ai_suggestion")
    return errors


def participant_hash(token: str, seed: int) -> str:
    return hashlib.sha256(f"episode-probe:{seed}:{token}".encode()).hexdigest()


def assign_arm(participant_digest: str, arms: list[str]) -> str:
    return arms[int(participant_digest[:8], 16) % len(arms)]


def new_session(
    participant_token: str,
    consent: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not consent:
        raise ValueError("explicit consent is required")
    protocol, bank = load_instrument()
    errors = instrument_errors(protocol, bank)
    if errors:
        raise ValueError("; ".join(errors))
    moment = now or utcnow()
    digest = participant_hash(participant_token, int(protocol["seed"]))
    return {
        "session_version": protocol["version"],
        "participant_hash": digest,
        "arm": assign_arm(digest, list(protocol["arms"])),
        "consented_at": iso(moment),
        "started_at": iso(moment),
        "current_phase_index": 0,
        "eligible_at": iso(moment),
        "completed_at": None,
        "phases": {},
        "protocol_deviations": [],
    }


def save_session(path: Path, session: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_session(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def phase_items(bank: dict[str, Any], item_set: str) -> list[dict[str, Any]]:
    return [item for item in bank["items"] if item["set"] == item_set]


def read_choice(valid: set[str], prompt: str) -> str:
    while True:
        value = input(prompt).strip().upper()
        if value in valid:
            return value
        print(f"Choose one of: {', '.join(sorted(valid))}")


def read_confidence() -> int:
    while True:
        value = input("Confidence, 0-100: ").strip()
        try:
            confidence = int(value)
        except ValueError:
            confidence = -1
        if 0 <= confidence <= 100:
            return confidence
        print("Enter an integer from 0 to 100.")


def show_item(item: dict[str, Any], choices: dict[str, str]) -> None:
    print(f"\n{item['stem']}\n")
    for key, label in choices.items():
        print(f"  {key}. {label}")


def interactive_response(
    item: dict[str, Any],
    choices: dict[str, str],
    context: dict[str, Any],
) -> dict[str, Any]:
    show_item(item, choices)
    valid = set(choices)
    if context.get("answer_revealed"):
        print(f"\nWorked answer: {item['answer']}. {item['explanation']}\n")
    started = time.monotonic()
    initial = read_choice(valid, "Your answer: ")
    confidence = read_confidence()
    final = initial
    if context.get("ai_suggestion"):
        suggestion = context["ai_suggestion"]
        print(f"\nFixed AI recommendation: {suggestion}. {choices[suggestion]}")
        final = read_choice(valid, "Final answer after seeing the recommendation: ")
    return {
        "initial_answer": initial,
        "final_answer": final,
        "confidence": confidence,
        "response_seconds": round(time.monotonic() - started, 3),
    }


Responder = Callable[[dict[str, Any], dict[str, str], dict[str, Any]], dict[str, Any]]


def run_phase(
    session: dict[str, Any],
    responder: Responder | None = None,
    now: datetime | None = None,
    allow_early: bool = False,
    echo: bool = True,
) -> dict[str, Any]:
    protocol, bank = load_instrument()
    moment = now or utcnow()
    phase_index = int(session["current_phase_index"])
    if phase_index >= len(protocol["phases"]):
        raise ValueError("session is already complete")
    eligible = parse_time(session["eligible_at"])
    if moment < eligible and not allow_early:
        raise ValueError(f"next phase is available at {iso(eligible)}")
    if moment < eligible and allow_early:
        session["protocol_deviations"].append({
            "type": "minimum_delay_waived",
            "phase": protocol["phases"][phase_index]["id"],
            "recorded_at": iso(moment),
        })

    phase = protocol["phases"][phase_index]
    items = phase_items(bank, phase["item_set"])
    if echo:
        print(f"\nPhase: {phase['id']} ({phase['mode']})")
        if phase["mode"] == "artifact":
            print("\nCausal-accounting card:")
            for line in protocol["carrier_card"]:
                print(f"  - {line}")

    records = []
    delayed_feedback = []
    answerer = responder or interactive_response
    for item in items:
        choices = bank["choices"][item["construct"]]
        context = {
            "phase": phase["id"],
            "mode": phase["mode"],
            "arm": session["arm"],
            "carrier_card": protocol["carrier_card"] if phase["mode"] == "artifact" else None,
            "answer_revealed": phase["mode"] == "randomized_practice"
                               and session["arm"] == "answer_first_control",
            "ai_suggestion": item.get("ai_suggestion") if phase["mode"] == "joint" else None,
        }
        response = answerer(item, choices, context)
        initial = response["initial_answer"].upper()
        final = response.get("final_answer", initial).upper()
        if initial not in choices or final not in choices:
            raise ValueError(f"{item['id']}: responder returned an invalid option")
        confidence = int(response["confidence"])
        if not 0 <= confidence <= 100:
            raise ValueError(f"{item['id']}: confidence must be 0-100")
        record = {
            "item_id": item["id"],
            "construct": item["construct"],
            "difficulty": item["difficulty"],
            "initial_answer": initial,
            "final_answer": final,
            "correct_answer": item["answer"],
            "initial_correct": initial == item["answer"],
            "final_correct": final == item["answer"],
            "confidence": confidence,
            "response_seconds": float(response.get("response_seconds", 0.0)),
            "ai_suggestion": item.get("ai_suggestion"),
            "ai_correct": item.get("ai_suggestion") == item["answer"] if item.get("ai_suggestion") else None,
            "answer_revealed_before_response": context["answer_revealed"],
        }
        records.append(record)
        if phase["feedback"] == "per_item" and echo and not context["answer_revealed"]:
            print(f"Answer: {item['answer']}. {item['explanation']}")
        elif phase["feedback"] == "after_phase":
            delayed_feedback.append((item, record))

    ended = moment if responder else utcnow()
    phase_record = {
        "phase_id": phase["id"],
        "mode": phase["mode"],
        "arm": session["arm"],
        "started_at": iso(moment),
        "ended_at": iso(ended),
        "items": records,
        "metrics": score_records(records),
    }
    session["phases"][phase["id"]] = phase_record
    session["current_phase_index"] = phase_index + 1
    delay = float(phase.get("delay_after_hours", 0))
    session["eligible_at"] = iso(ended + timedelta(hours=delay))
    if session["current_phase_index"] >= len(protocol["phases"]):
        session["completed_at"] = iso(ended)

    if echo and delayed_feedback:
        print("\nPhase feedback:")
        for item, record in delayed_feedback:
            mark = "correct" if record["final_correct"] else "incorrect"
            print(f"  {item['id']}: {mark}; answer {item['answer']}. {item['explanation']}")
    if echo:
        metrics = phase_record["metrics"]
        print(f"\nPhase accuracy: {metrics['final_accuracy']:.1%}")
    return phase_record


def score_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(records)
    initial_accuracy = sum(row["initial_correct"] for row in records) / count if count else 0.0
    final_accuracy = sum(row["final_correct"] for row in records) / count if count else 0.0
    brier = sum(
        ((row["confidence"] / 100.0) - (1.0 if row["initial_correct"] else 0.0)) ** 2
        for row in records
    ) / count if count else 0.0
    ai_rows = [row for row in records if row["ai_correct"] is not None]
    helpful = sum(not row["initial_correct"] and row["final_correct"] for row in ai_rows)
    harmful = sum(row["initial_correct"] and not row["final_correct"] for row in ai_rows)
    return {
        "n": count,
        "initial_accuracy": round(initial_accuracy, 6),
        "final_accuracy": round(final_accuracy, 6),
        "mean_confidence": round(sum(row["confidence"] for row in records) / count, 3) if count else 0.0,
        "confidence_brier": round(brier, 6),
        "mean_response_seconds": round(sum(row["response_seconds"] for row in records) / count, 3) if count else 0.0,
        "fixed_ai_accuracy": round(sum(row["ai_correct"] for row in ai_rows) / len(ai_rows), 6) if ai_rows else None,
        "helpful_revisions": helpful,
        "harmful_revisions": harmful,
    }


def session_summary(session: dict[str, Any]) -> dict[str, Any]:
    phases = session["phases"]
    metric = lambda phase, key: phases.get(phase, {}).get("metrics", {}).get(key)
    baseline = metric("baseline", "final_accuracy")
    immediate = metric("immediate_transfer", "final_accuracy")
    delayed = metric("delayed_transfer", "final_accuracy")
    artifact = metric("artifact_recovery", "final_accuracy")
    joint_initial = metric("joint", "initial_accuracy")
    joint_final = metric("joint", "final_accuracy")
    fixed_ai = metric("joint", "fixed_ai_accuracy")

    def difference(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else round(a - b, 6)

    return {
        "participant_hash": session["participant_hash"],
        "arm": session["arm"],
        "complete": session["completed_at"] is not None,
        "phase_metrics": {phase: record["metrics"] for phase, record in phases.items()},
        "primary_outcome": difference(delayed, baseline),
        "immediate_learning": difference(immediate, baseline),
        "delayed_retention": difference(delayed, immediate),
        "artifact_recovery_lift": difference(artifact, delayed),
        "joint_lift_over_initial_human": difference(joint_final, joint_initial),
        "joint_lift_over_fixed_ai": difference(joint_final, fixed_ai),
        "protocol_deviations": session["protocol_deviations"],
    }


def sanitized_export(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "export_version": "hitl-capability-export-0.1",
        "session_version": session["session_version"],
        "participant_hash": session["participant_hash"],
        "arm": session["arm"],
        "consented_at": session["consented_at"],
        "started_at": session["started_at"],
        "completed_at": session["completed_at"],
        "summary": session_summary(session),
        "phase_records": list(session["phases"].values()),
    }


def status_text(session: dict[str, Any]) -> str:
    protocol, _ = load_instrument()
    index = int(session["current_phase_index"])
    if index >= len(protocol["phases"]):
        next_phase = "complete"
    else:
        next_phase = protocol["phases"][index]["id"]
    return (
        f"arm={session['arm']} completed={len(session['phases'])}/{len(protocol['phases'])} "
        f"next={next_phase} eligible_at={session['eligible_at']}"
    )


def command_new(args: argparse.Namespace) -> int:
    print("This local probe stores a salted identifier, choices, confidence, and timing. It asks")
    print("for no name, demographics, free text, workplace content, or sensitive case material.")
    consent = input("I understand and consent to this local capability probe [yes/no]: ").strip().lower() == "yes"
    token = args.participant or uuid.uuid4().hex
    session = new_session(token, consent)
    default_path = PRIVATE_RUNS / f"{session['participant_hash'][:16]}.json"
    path = args.state or default_path
    save_session(path, session)
    print(f"Created {path}")
    print(status_text(session))
    return 0


def command_run(args: argparse.Namespace) -> int:
    session = load_session(args.state)
    run_phase(session, allow_early=args.allow_early)
    save_session(args.state, session)
    print(status_text(session))
    return 0


def command_status(args: argparse.Namespace) -> int:
    session = load_session(args.state)
    print(status_text(session))
    print(json.dumps(session_summary(session), indent=2, sort_keys=True))
    return 0


def command_export(args: argparse.Namespace) -> int:
    session = load_session(args.state)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sanitized_export(session), indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(f"Exported {args.output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="create a consented local probe session")
    new.add_argument("--participant", help="local pseudonymous token; raw value is not stored")
    new.add_argument("--state", type=Path, help="state path; defaults under ignored private_runs/")
    new.set_defaults(func=command_new)
    run = sub.add_parser("run", help="run the next eligible phase")
    run.add_argument("--state", type=Path, required=True)
    run.add_argument("--allow-early", action="store_true", help="testing only; records a protocol deviation")
    run.set_defaults(func=command_run)
    status = sub.add_parser("status", help="show progress and descriptive outcomes")
    status.add_argument("--state", type=Path, required=True)
    status.set_defaults(func=command_status)
    export = sub.add_parser("export", help="export a pseudonymous machine-readable record")
    export.add_argument("--state", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.set_defaults(func=command_export)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
