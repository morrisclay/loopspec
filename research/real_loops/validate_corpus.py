#!/usr/bin/env python3
"""Validate the source-backed real-loop corpus without adjudicating its findings."""

from __future__ import annotations

import datetime as dt
import glob
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.loopspec import checked_document  # noqa: E402


SHA40 = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_CASE_KEYS = {"id", "system", "stratum", "topology", "status", "encoding", "source", "evidence"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_source(case: dict) -> bool:
    source = case["source"]
    kind = source.get("kind")
    if kind == "git":
        if not SHA40.fullmatch(str(source.get("revision", ""))):
            fail(f"{case['id']}: git source needs a full 40-character revision")
        for key in ("repository", "path"):
            if not source.get(key):
                fail(f"{case['id']}: git source missing {key}")
        return True
    if kind == "web":
        if not source.get("url"):
            fail(f"{case['id']}: web source missing url")
        try:
            dt.date.fromisoformat(str(source.get("observed_at")))
        except (TypeError, ValueError):
            fail(f"{case['id']}: web source needs an ISO observed_at date")
        return False
    fail(f"{case['id']}: source kind must be git or web")
    return False


def main() -> int:
    manifest_path = ROOT / "research/real_loops/corpus.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    acceptance = manifest["acceptance"]

    encoding_paths: set[Path] = set()
    for suite in manifest.get("seed_suites", []):
        matches = [Path(path) for path in glob.glob(str(ROOT / suite["pattern"]))]
        if not matches:
            fail(f"{suite['id']}: pattern matched no encodings")
        encoding_paths.update(matches)

    source_pinned = 0
    case_ids: set[str] = set()
    for case in manifest.get("cases", []):
        missing = REQUIRED_CASE_KEYS - set(case)
        if missing:
            fail(f"{case.get('id', '<unknown>')}: missing keys {sorted(missing)}")
        if case["id"] in case_ids:
            fail(f"duplicate case id: {case['id']}")
        case_ids.add(case["id"])
        source_pinned += int(validate_source(case))
        if not case["evidence"]:
            fail(f"{case['id']}: evidence list is empty")
        encoding = ROOT / case["encoding"]
        if not encoding.is_file():
            fail(f"{case['id']}: encoding does not exist: {case['encoding']}")
        encoding_paths.add(encoding)

    candidate_ids = {candidate["id"] for candidate in manifest.get("candidates", [])}
    if len(candidate_ids) != len(manifest.get("candidates", [])):
        fail("candidate ids must be unique")
    overlap = case_ids & candidate_ids
    if overlap:
        fail(f"cases and candidates overlap: {sorted(overlap)}")

    finding_count = 0
    invalid: list[str] = []
    for path in sorted(encoding_paths):
        try:
            _document, _warnings, report, findings = checked_document(str(path))
        except Exception as error:  # keep the gate readable when an encoder breaks syntax
            invalid.append(f"{path.relative_to(ROOT)}: {error}")
            continue
        if not report.ok:
            invalid.extend(f"{path.relative_to(ROOT)}: {error}" for error in report.errors)
        finding_count += len(findings)

    if invalid:
        fail("invalid encodings:\n  " + "\n  ".join(invalid))

    if len(encoding_paths) < acceptance["minimum_valid_encodings"]:
        fail(f"only {len(encoding_paths)} valid encodings")
    if source_pinned < acceptance["minimum_source_pinned_cases"]:
        fail(f"only {source_pinned} source-pinned cases")
    if len(candidate_ids) < acceptance["minimum_live_candidates"]:
        fail(f"only {len(candidate_ids)} live candidates")

    print(
        "real-loop corpus: "
        f"{len(encoding_paths)} encodings valid; "
        f"{source_pinned} source-pinned cases; "
        f"{len(candidate_ids)} live candidates; "
        f"{finding_count} unadjudicated findings"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"real-loop corpus INVALID: {error}", file=sys.stderr)
        raise SystemExit(1)
