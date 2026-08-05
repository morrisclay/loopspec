#!/usr/bin/env python3
"""Run a blind, tool-disabled source-to-LoopSpec encoding for the control-plane holdouts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = HERE / "source_packets.json"
OUTPUT = HERE / "independent_encodings"


def line_slice(path: pathlib.Path, start: int, end: int) -> str:
    lines = path.read_text().splitlines()
    selected = lines[start - 1 : end]
    return "\n".join(
        f"{number:>6}  {line}" for number, line in enumerate(selected, start)
    )


def source_packet(case: dict, checkout: pathlib.Path) -> str:
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != case["revision"]:
        raise SystemExit(f"checkout is {actual}; packet requires {case['revision']}")
    chunks = []
    for file_spec in case["files"]:
        path = checkout / file_spec["path"]
        for start, end in file_spec["ranges"]:
            chunks.append(
                f"SOURCE {file_spec['path']} lines {start}-{end}\n"
                f"```\n{line_slice(path, start, end)}\n```"
            )
    return "\n\n".join(chunks)


def prompt(reference: str, packet: str) -> str:
    return f"""You are an independent encoder in a blinded language-evaluation study.

Encode only the implementation excerpts below into one complete LoopSpec document using the
format reference. You have not been shown a primary encoding, expected mechanism list, linter
output, or acceptance score.

Rules:
- Encode only behavior supported by the excerpts; do not fill omissions with framework lore.
- `actions` are interventions on an external or controlled process.
- `operations` change execution of the controller itself. Do not put pause, resume, interrupt,
  retry, compaction, handoff, or stop in `actions`.
- Classify by semantic effect, not dispatcher class: final-answer, done, complete, or terminate
  sentinels whose only effect is ending the controller are stop operations, not world actions.
- `outputs` are values leaving the represented loop boundary. Use `terminates` relative to the
  loop boundary you draw.
- Use one output per `(kind, terminates)` role and one operation per `(kind, authorized_by,
  emitted-role set)`; merge branch conditions with `or`. Duplicate roles are invalid.
- `authorized_by` names an external party granted invocation authority. Omit it when the
  controller merely executes its own branch; execution is not authorization.
- Do not infer a human from a generic caller. Use a system party only when the source identifies
  a calling component; omit authority when it identifies neither.
- `interrupt` cancels an active step asynchronously. A stop flag polled at a safe boundary is
  `stop`. Ordinary invocation is implicit; do not encode it as `start` unless the source exposes
  a distinct out-of-band start transition.
- Public stream events are `status`/`none`. A resumable public return at a per-step boundary is
  `pause` plus a non-terminal output. Do not mix per-step and whole-run boundaries.
- A terminal output at the represented boundary is `terminates: run`, even when the application
  calls that whole invocation a user turn. Reserve `turn` for a nested provider/model turn.
- Awaiting approval inside one still-running API call is an action gate plus a non-terminal
  approval-request output, not a pause/resume pair. Use pause/resume only when resumable state is
  exposed across the public invocation boundary.
- Use `action_profiles` when approval or reversibility varies by deployment or concrete request.
  Include one honest default profile; use `can_undo: unknown` rather than inventing safety.
- Do not create a lone default profile: put non-varying safety on the base action. Multiple
  profiles must actually vary reversibility or approver; binding stage alone is insufficient.
- When an action has profiles, omit base `can_undo` and `needs_approval` from that action; the
  profiles are the complete typed partition.
- Merge profile selectors that have the same binding stage, reversibility, and approver.
- Conditional approval belongs on the matching profile, not on the whole generic action.
- Local references may be bare (`task_completion`) or section-qualified
  (`goal.task_completion`); known valid prefixes normalize to the same local name.
- If an observation names `produced_by`, it was created by this loop and must use
  `origin: ourselves`, never `origin: outside`.
- Outputs are separately consumable public interface values. Do not make extra outputs for logs,
  internal callbacks, or fields nested inside a final result unless exposed independently.
- A one-run result may settle one decision; do not claim longitudinal calibration unless the
  source scores predictions across cases and changes future trust.
- Preserve source path and line-range citations in YAML comments.
- Output exactly one fenced YAML block and no commentary.

FORMAT REFERENCE
================
{reference}

BLINDED SOURCE PACKET
=====================
{packet}
"""


def extract_yaml(text: str) -> str:
    match = re.search(r"```ya?ml\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        raise SystemExit("encoder did not return one fenced YAML block")
    return match.group(1).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("checkout", type=pathlib.Path)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--output-dir", type=pathlib.Path, default=OUTPUT)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    if args.case not in manifest["cases"]:
        raise SystemExit(f"unknown case {args.case!r}")
    case = manifest["cases"][args.case]
    packet = source_packet(case, args.checkout.resolve())
    full_prompt = prompt((ROOT / "REFERENCE.md").read_text(), packet)
    completed = subprocess.run(
        [
            "claude", "--print", "--safe-mode", "--tools", "",
            "--no-session-persistence", "--model", args.model,
            "--max-budget-usd", "1.25", full_prompt,
        ],
        cwd="/tmp",
        check=True,
        capture_output=True,
        text=True,
        timeout=900,
    )
    encoded = extract_yaml(completed.stdout)
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.case}.loop.yaml"
    output_path.write_text(encoded)
    metadata = {
        "case": args.case,
        "study_role": "control_plane_holdout",
        "encoder": "Anthropic Claude CLI",
        "model_alias": args.model,
        "tool_access": "disabled",
        "session_persistence": "disabled",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_repository": case["repository"],
        "source_revision": case["revision"],
        "prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
        "output_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
    }
    output_path.with_suffix(".run.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(output_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
