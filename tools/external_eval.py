#!/usr/bin/env python3
"""Validate and score a preregistered LoopSpec external-author study.

`--freeze` prints a complete manifest only from a committed semantic artifact set whose
source release gate passes.

Exit 0: valid data and every preregistered release gate passes.
Exit 1: invalid or incomplete data.
Exit 2: valid study data, but one or more release gates fail.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys

import yaml

try:
    from .loopspec import checked_document
    from . import derive as derive_engine
except ImportError:
    from loopspec import checked_document
    import derive as derive_engine


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOCOL_PATH = os.path.join(ROOT, "research", "external_validation", "protocol.yaml")
if os.path.isfile(PROTOCOL_PATH):
    with open(PROTOCOL_PATH) as _protocol_source:
        PROTOCOL = yaml.safe_load(_protocol_source)
else:
    PROTOCOL = None  # The research evaluator is intentionally source-checkout-only.
FROZEN_ARTIFACTS = (
    "pyproject.toml",
    "requirements.txt",
    "schema/loop.keys.yaml",
    "schema/semantic-map.yaml",
    "schema/loopspec.graph.md",
    "ontology/primitives.yaml",
    "docs/checks.yaml",
    "docs/base_rates.json",
    "tools/loop.py",
    "tools/validate.py",
    "tools/derive.py",
    "tools/semantic_diff.py",
    "tools/gen_spec.py",
    "tools/gen_checks.py",
    "tools/check_semantic_map.py",
    "tools/runtime_paths.py",
    "tools/loopspec.py",
    "tools/uras.py",
    "tests/conformance.yaml",
    "tests/test_semantic_pipeline.py",
    "research/external_validation/PREREGISTRATION.md",
    "research/external_validation/protocol.yaml",
    "research/external_validation/study.template.yaml",
    "research/external_validation/record.template.yaml",
    "tools/external_eval.py",
)

STAGES = {"operating", "design"}
SOURCE_KINDS = {"code", "diagram", "prompt", "runbook", "prose", "mixed"}
VERDICTS = {
    "wrong",
    "encoding_error",
    "correct_known_no_action",
    "changes_understanding",
    "changes_spec",
    "changes_decision",
    "changes_implementation",
}
ACTION_VERDICTS = {"changes_spec", "changes_decision", "changes_implementation"}
ASSURANCE_LEVELS = {"structural", "qualitative-proxy", "quantitative", "empirical"}
PRESENTATION_BUCKETS = {"specific", "common", "universal", "considered"}
HIGH_PRIORITY_PATTERNS = set(PROTOCOL["high_priority_patterns"]) if PROTOCOL else set()


class StudyError(ValueError):
    pass


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def artifact_hashes():
    hashes = {}
    for path in FROZEN_ARTIFACTS:
        with open(os.path.join(ROOT, path), "rb") as source:
            hashes[path] = hashlib.sha256(source.read()).hexdigest()
    return hashes


def active_checks():
    with open(os.path.join(ROOT, "docs", "checks.yaml")) as source:
        checks = yaml.safe_load(source) or {}
    return {pattern: body.get("assurance") for pattern, body in checks.items()
            if body.get("evidence") != "legacy"}


def runtime_fingerprint():
    """Return the interpreter and parser versions that can affect frozen output."""
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pyyaml_version": yaml.__version__,
    }


def make_freeze_manifest(artifact_commit, doctor_output):
    """Build the complete protocol-v1 manifest from verified local artifacts."""
    if PROTOCOL is None:
        raise StudyError("external evaluation requires a LoopSpec source checkout")
    return {
        "protocol_version": PROTOCOL["protocol_version"],
        "artifact_commit": artifact_commit,
        "artifact_hashes": artifact_hashes(),
        "runtime": runtime_fingerprint(),
        "doctor_output": doctor_output,
        "active_checks": active_checks(),
        "mutation_safety_false_negatives": 0,
        "amendments": [],
    }


def freeze_manifest():
    """Run the release gate and freeze only a committed, clean semantic artifact set."""
    if PROTOCOL is None:
        raise StudyError("external evaluation requires a LoopSpec source checkout")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *FROZEN_ARTIFACTS],
        cwd=ROOT, capture_output=True, text=True,
    )
    if status.returncode:
        raise StudyError(f"cannot inspect git state: {status.stderr.strip()}")
    if status.stdout.strip():
        changed = [line[3:] for line in status.stdout.splitlines() if line.strip()]
        raise StudyError(
            "cannot freeze uncommitted semantic artifacts: " + ", ".join(changed)
        )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
    )
    if commit.returncode or not commit.stdout.strip():
        raise StudyError(f"cannot resolve artifact commit: {commit.stderr.strip()}")
    doctor = subprocess.run(
        [sys.executable, "tools/loopspec.py", "doctor"], cwd=ROOT,
        capture_output=True, text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    doctor_output = (doctor.stdout + doctor.stderr).strip()
    if doctor.returncode:
        raise StudyError("doctor failed; artifact was not frozen\n" + doctor_output)
    if "LoopSpec doctor:" not in doctor_output or "healthy" not in doctor_output:
        raise StudyError("doctor did not emit the expected healthy release-gate marker")
    return make_freeze_manifest(commit.stdout.strip(), doctor_output)


def _core_measures(records):
    findings = [finding for record in records for finding in record.get("findings", [])]
    high = [finding for finding in findings
            if finding.get("presentation_bucket") == "specific"
            or finding.get("pattern") in HIGH_PRIORITY_PATTERNS]
    adjudicated_high = [finding for finding in high
                        if isinstance(finding.get("adjudicated_correct"), bool)]
    correct = [finding for finding in findings if finding.get("adjudicated_correct") is True]
    recipients = [record for record in records if record.get("findings")]
    acted_authors = [record for record in recipients if any(
        finding.get("initial_verdict") in ACTION_VERDICTS
        for finding in record.get("findings", [])
    )]
    acted_findings = [finding for finding in correct
                      if finding.get("initial_verdict") in ACTION_VERDICTS]
    encoding_induced = [finding for finding in findings
                        if finding.get("initial_verdict") == "encoding_error"]
    return {
        "high_priority_precision": ratio(
            sum(finding["adjudicated_correct"] is True for finding in adjudicated_high),
            len(adjudicated_high),
        ),
        "encoding_induced_rate": ratio(len(encoding_induced), len(findings)),
        "author_action_rate": ratio(len(acted_authors), len(recipients)),
        "finding_action_rate": ratio(len(acted_findings), len(correct)),
        "findings": len(findings),
        "high_priority_findings": len(high),
        "adjudicated_high_priority_findings": len(adjudicated_high),
        "authors_receiving_findings": len(recipients),
    }


def _core_thresholds(measures):
    thresholds = PROTOCOL["thresholds"]
    return {
        "high_priority_precision_at_least_0_70": (
            measures["high_priority_precision"] is not None
            and measures["high_priority_precision"] >= thresholds["minimum_high_priority_precision"]
        ),
        "encoding_induced_rate_below_0_20": (
            measures["encoding_induced_rate"] is not None
            and measures["encoding_induced_rate"] < thresholds["maximum_encoding_induced_rate_exclusive"]
        ),
        "author_action_rate_at_least_0_50": (
            measures["author_action_rate"] is not None
            and measures["author_action_rate"] >= thresholds["minimum_author_action_rate"]
        ),
    }


def _presented_signature(document, findings):
    """Reconstruct the finding pattern/assurance/bucket multiset shown to an author."""
    organised = derive_engine.organise(document, findings)
    signature = []
    for bucket in ("specific", "common", "universal"):
        signature.extend((finding["pattern"], finding["assurance"], bucket)
                         for finding in organised[bucket])
    signature.extend((finding["pattern"], finding["assurance"], "considered")
                     for finding, _because, _revisit in organised["considered"])
    return Counter(signature)


def _recorded_signature(record):
    return Counter((finding.get("pattern"), finding.get("assurance"),
                    finding.get("presentation_bucket"))
                   for finding in record.get("findings") or [])


def validate(study, records):
    if PROTOCOL is None:
        raise StudyError("external evaluation requires a LoopSpec source checkout")
    errors = []
    if study.get("protocol_version") != PROTOCOL["protocol_version"]:
        errors.append(f"study.protocol_version must be {PROTOCOL['protocol_version']}")
    if not study.get("artifact_commit") or study.get("artifact_commit") == "RECORD_BEFORE_FIRST_ENCODING":
        errors.append("study.artifact_commit is required")
    hashes = study.get("artifact_hashes") or {}
    if set(hashes) != set(FROZEN_ARTIFACTS):
        errors.append(f"study.artifact_hashes must contain exactly {list(FROZEN_ARTIFACTS)}")
    else:
        for path, actual in artifact_hashes().items():
            if hashes[path] != actual:
                errors.append(f"study artifact hash mismatch for {path}")
    if study.get("runtime") != runtime_fingerprint():
        errors.append("study.runtime must exactly match the frozen Python and PyYAML runtime")
    if not str(study.get("doctor_output") or "").strip():
        errors.append("study.doctor_output is required")
    expected_checks = active_checks()
    if study.get("active_checks") != expected_checks:
        errors.append("study.active_checks must exactly match the frozen pattern->assurance map")
    if not isinstance(study.get("mutation_safety_false_negatives"), int):
        errors.append("study.mutation_safety_false_negatives must be an integer")

    system_ids = set()
    author_ids = set()
    for index, record in enumerate(records):
        where = f"records[{index}]"
        for field in ("system_id", "author_id", "domain", "stage", "source_kind",
                      "encoder_id", "spec_path", "spec_sha256", "encoding_minutes",
                      "author_corrections", "findings"):
            if field not in record:
                errors.append(f"{where}.{field} is required")
        system_id = record.get("system_id")
        author_id = record.get("author_id")
        if system_id in system_ids:
            errors.append(f"{where}.system_id duplicates {system_id!r}")
        if author_id in author_ids:
            errors.append(f"{where}.author_id duplicates {author_id!r}; primary analysis is one loop per author")
        system_ids.add(system_id)
        author_ids.add(author_id)
        if record.get("stage") not in STAGES:
            errors.append(f"{where}.stage must be one of {sorted(STAGES)}")
        if record.get("source_kind") not in SOURCE_KINDS:
            errors.append(f"{where}.source_kind must be one of {sorted(SOURCE_KINDS)}")
        if record.get("loopspec_contributor") is not False:
            errors.append(f"{where}.loopspec_contributor must be false")
        minutes = record.get("encoding_minutes")
        if not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or minutes < 0:
            errors.append(f"{where}.encoding_minutes must be a non-negative number")
        if not isinstance(record.get("author_corrections"), list):
            errors.append(f"{where}.author_corrections must be a list")
        if not isinstance(record.get("findings"), list):
            errors.append(f"{where}.findings must be a list")
            continue
        for finding_index, finding in enumerate(record.get("findings", [])):
            finding_where = f"{where}.findings[{finding_index}]"
            for field in ("pattern", "assurance", "presentation_bucket", "initial_verdict",
                          "adjudicated_correct"):
                if field not in finding:
                    errors.append(f"{finding_where}.{field} is required")
            if finding.get("initial_verdict") not in VERDICTS:
                errors.append(f"{finding_where}.initial_verdict is invalid")
            if finding.get("assurance") not in ASSURANCE_LEVELS:
                errors.append(f"{finding_where}.assurance is invalid")
            if finding.get("pattern") not in expected_checks:
                errors.append(f"{finding_where}.pattern is not an active authoring check")
            elif finding.get("assurance") != expected_checks[finding.get("pattern")]:
                errors.append(f"{finding_where}.assurance does not match frozen check metadata")
            if finding.get("presentation_bucket") not in PRESENTATION_BUCKETS:
                errors.append(f"{finding_where}.presentation_bucket is invalid")
            if not isinstance(finding.get("adjudicated_correct"), bool):
                errors.append(f"{finding_where}.adjudicated_correct must be boolean")

        spec_path = record.get("spec_path")
        if not isinstance(spec_path, str) or not spec_path.strip():
            errors.append(f"{where}.spec_path must name the frozen corrected LoopSpec spec")
            continue
        if not os.path.isfile(spec_path):
            errors.append(f"{where}.spec_path does not exist: {spec_path}")
            continue
        with open(spec_path, "rb") as source:
            actual_spec_hash = hashlib.sha256(source.read()).hexdigest()
        if record.get("spec_sha256") != actual_spec_hash:
            errors.append(f"{where}.spec_sha256 does not match {spec_path}")
            continue
        try:
            document, warnings, report, generated_findings = checked_document(spec_path)
        except Exception as error:
            errors.append(f"{where}.spec_path cannot be analyzed: {error}")
            continue
        if warnings or not report.ok:
            errors.append(f"{where}.spec_path must be warning-free valid LoopSpec input")
            continue
        expected_signature = _presented_signature(document, generated_findings)
        recorded_signature = _recorded_signature(record)
        if recorded_signature != expected_signature:
            missing = list((expected_signature - recorded_signature).elements())
            extra = list((recorded_signature - expected_signature).elements())
            errors.append(
                f"{where}.findings do not match frozen analyzer output; "
                f"missing={missing}, extra={extra}"
            )
    if errors:
        raise StudyError("\n".join(errors))


def analyze(study, records):
    validate(study, records)
    measures = _core_measures(records)
    minutes = [record["encoding_minutes"] for record in records]
    measures.update({
        "systems": len(records),
        "domains": len({record["domain"] for record in records}),
        "encoders": len({record["encoder_id"] for record in records}),
        "operating_systems": sum(record["stage"] == "operating" for record in records),
        "design_systems": sum(record["stage"] == "design" for record in records),
        "encoding_minutes_median": statistics.median(minutes) if minutes else None,
        "encoding_minutes_range": [min(minutes), max(minutes)] if minutes else None,
    })
    domain_counts = {domain: sum(record["domain"] == domain for record in records)
                     for domain in sorted({record["domain"] for record in records})}
    encoder_counts = {encoder: sum(record["encoder_id"] == encoder for record in records)
                      for encoder in sorted({record["encoder_id"] for record in records})}

    sensitivity = {"domain_leave_one_out": {}, "encoder_leave_one_out": {}}
    for field, label in (("domain", "domain_leave_one_out"),
                         ("encoder_id", "encoder_leave_one_out")):
        for value in sorted({record[field] for record in records}):
            subset = [record for record in records if record[field] != value]
            subset_measures = _core_measures(subset)
            thresholds = _core_thresholds(subset_measures)
            sensitivity[label][value] = {
                "systems": len(subset),
                "measures": subset_measures,
                "passes_core_thresholds": all(thresholds.values()),
            }

    core = _core_thresholds(measures)
    sample = PROTOCOL["sample"]
    sample_gates = {
        "at_least_12_external_authors": len(records) >= sample["minimum_authors"],
        "at_least_3_domains": measures["domains"] >= sample["minimum_domains"],
        "no_domain_over_half": (bool(records) and max(domain_counts.values()) <=
                                len(records) * sample["maximum_domain_fraction"]),
        "at_least_6_operating": measures["operating_systems"] >= sample["minimum_operating_systems"],
        "at_least_4_design": measures["design_systems"] >= sample["minimum_design_systems"],
        "at_least_2_encoders": measures["encoders"] >= sample["minimum_encoders"],
    }
    robustness_gates = {
        "no_safety_mutation_false_negative": study["mutation_safety_false_negatives"] == 0,
        "domain_leave_one_out_passes": (
            len(sensitivity["domain_leave_one_out"]) >= 3 and all(
                result["passes_core_thresholds"]
                for result in sensitivity["domain_leave_one_out"].values()
            )
        ),
        "encoder_leave_one_out_passes": (
            len(sensitivity["encoder_leave_one_out"]) >= 2 and all(
                result["passes_core_thresholds"]
                for result in sensitivity["encoder_leave_one_out"].values()
            )
        ),
    }
    gates = {**sample_gates, **core, **robustness_gates}
    return {
        "valid": True,
        "eligible_for_usefulness_claim": all(gates.values()),
        "measures": measures,
        "domain_counts": domain_counts,
        "encoder_counts": encoder_counts,
        "gates": gates,
        "sensitivity": sensitivity,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score preregistered LoopSpec external evidence")
    parser.add_argument("study", nargs="?", help="study YAML containing frozen artifact metadata")
    parser.add_argument("records", nargs="*", help="one de-identified YAML record per author")
    parser.add_argument("--freeze", action="store_true",
                        help="print a study manifest after clean-git and doctor gates pass")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.freeze:
            if args.study or args.records:
                raise StudyError("--freeze does not accept a study or record files")
            manifest = freeze_manifest()
            if args.json:
                print(json.dumps(manifest, indent=2, sort_keys=True))
            else:
                print(yaml.safe_dump(manifest, sort_keys=False, width=100), end="")
            return 0
        if not args.study or not args.records:
            raise StudyError("provide a study YAML and at least one record, or use --freeze")
        with open(args.study) as source:
            study = yaml.safe_load(source) or {}
        records = []
        for path in args.records:
            with open(path) as source:
                records.append(yaml.safe_load(source) or {})
        report = analyze(study, records)
    except (OSError, yaml.YAMLError, StudyError) as error:
        if args.json:
            print(json.dumps({"valid": False, "errors": str(error).splitlines()}, indent=2))
        else:
            print(error, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("eligible for usefulness claim" if report["eligible_for_usefulness_claim"]
              else "valid study; usefulness gates did not all pass")
        for gate, passed in report["gates"].items():
            print(f"  {'PASS' if passed else 'FAIL'} {gate}")
    return 0 if report["eligible_for_usefulness_claim"] else 2


if __name__ == "__main__":
    sys.exit(main())
