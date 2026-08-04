#!/usr/bin/env python3
"""Blindly encode source-pinned loops with a separate, tool-disabled model."""

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
MANIFEST = HERE / "independent_packets.json"
OUTPUT = HERE / "independent_encodings"


def line_slice(path: pathlib.Path, start: int, end: int) -> str:
    lines = path.read_text().splitlines()
    selected = lines[start - 1 : end]
    return "\n".join(f"{number:>6}  {line}" for number, line in enumerate(selected, start))


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
    return f"""You are an independent encoder in a blinded replication study.

Encode only the implementation excerpts below into the format in the reference. You have
not been shown any existing encoding, lint result, hypothesis, or proposed language change.

Rules:
- Encode only behavior supported by the excerpts. Do not fill omissions with framework lore.
- Distinguish actions on the outside world from controller bookkeeping and terminal output.
- A result from one action may settle that action-level belief; do not call that longitudinal
  calibration unless the source scores predictions across cases and changes future trust.
- If a material property depends on a concrete deployment, state that in `not_modelling`
  rather than inventing a value.
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
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=OUTPUT,
        help="destination directory (defaults to independent_encodings)",
    )
    parser.add_argument("--study-role", default="held_out_replication")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    try:
        case = manifest["cases"][args.case]
    except KeyError:
        choices = ", ".join(sorted(manifest["cases"]))
        raise SystemExit(f"unknown case {args.case!r}; choose one of: {choices}")

    packet = source_packet(case, args.checkout.resolve())
    full_prompt = prompt((ROOT / manifest["reference"]).read_text(), packet)
    completed = subprocess.run(
        [
            "claude",
            "--print",
            "--safe-mode",
            "--tools",
            "",
            "--no-session-persistence",
            "--model",
            args.model,
            "--max-budget-usd",
            "1.00",
            full_prompt,
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
        "study_role": args.study_role,
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
