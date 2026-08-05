#!/usr/bin/env python3
"""One entry point for designing and checking LoopSpec loops.

Examples:
    python3 tools/loopspec.py check examples/customer_acquisition.v1.loop.yaml
    python3 tools/loopspec.py expand examples/customer_acquisition.v1.loop.yaml
    python3 tools/loopspec.py diff before.loop.yaml after.loop.yaml
    python3 tools/loopspec.py diagram examples/customer_acquisition.v1.loop.yaml --control --markdown
    python3 tools/loopspec.py doctor
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

import yaml

try:  # package entry point
    from .loop import DEPRECATIONS, SpecError, expand
    from . import derive
    from . import validate as semantic_validator
    from .runtime_paths import ROOT
except ImportError:  # direct `python3 tools/loopspec.py`
    from loop import DEPRECATIONS, SpecError, expand
    import derive
    import validate as semantic_validator
    from runtime_paths import ROOT


RUNTIME_SMOKE_SPEC = {
    "loop": "runtime_smoke",
    "runs": "on_demand",
    "goal": {"level": {"keep": "near 1"}},
    "observes": {
        "level_reading": {
            "informs": "level",
            "origin": "outside",
            "how": "measured",
        },
    },
    "actions": {
        "correct_level": {
            "moves": "level",
            "effect": "unknown",
            "can_undo": "yes",
        },
    },
    "when": [{
        "if": "level differs from the reference",
        "reads": ["level"],
        "against": ["level"],
        "do": "correct_level",
    }],
}


def checked_document(path):
    DEPRECATIONS.clear()
    document, expansion_warnings = expand(path)
    report = semantic_validator.validate_document(document, path)
    findings, query_failures = (derive.analyze_document(document) if report.ok else ([], []))
    if query_failures:
        raise RuntimeError(f"analysis query failure(s): {query_failures}")
    return document, expansion_warnings, report, findings


def command_check(args):
    try:
        document, expansion_warnings, report, findings = checked_document(args.spec)
    except (SpecError, yaml.YAMLError, OSError, RuntimeError) as error:
        if args.json:
            print(json.dumps({"valid": False, "errors": [str(error)]}, indent=2))
        else:
            print(f"INVALID\n\n{error}", file=sys.stderr)
        return 1

    result = {
        "valid": report.ok,
        "spec": args.spec,
        "encodes": document.get("encodes"),
        "ir_version": document.get("loopspec_version", document.get("uras_version")),
        "ir_revision": document.get("ir_revision"),
        "errors": report.errors,
        "warnings": expansion_warnings + report.warnings,
        "deprecations": list(dict.fromkeys(DEPRECATIONS)),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        revision = (document.get("ir_revision") or document.get("loopspec_version")
                    or document.get("uras_version"))
        print(f"{document.get('encodes')} — valid IR v{revision}")
        for warning in result["warnings"]:
            print(f"  warning: {warning}")
        for warning in result["deprecations"]:
            print(f"  deprecated: {warning}")
        if report.errors:
            for error in report.errors:
                print(f"  error: {error}")
        else:
            organised = derive.organise(document, findings)
            for bucket, title in (("specific", "SPECIFIC"), ("common", "COMMON"),
                                  ("universal", "UNIVERSAL CONTEXT")):
                if not organised[bucket]:
                    continue
                print(f"\n{title}")
                for pattern, claims in derive.group(organised[bucket]).items():
                    claim = claims[0]
                    count = f" ×{len(claims)}" if len(claims) > 1 else ""
                    print(f"  [{pattern}] {claim['assurance']}{count}")
                    print(f"    {derive.plain(claim['claim'])}")
                    if claim.get("repair"):
                        print(f"    repair: {derive.plain(claim['repair'])}")
            if organised["considered"]:
                print("\nCONSIDERED")
                for finding, because, revisit in organised["considered"]:
                    print(f"  [{finding['pattern']}] because: {because}")
                    if revisit:
                        print(f"    revisit: {revisit}")
            for stale in organised["stale"]:
                print(f"\n  stale consider entry: {stale}")
            if not findings:
                print("\nNo design findings.")

    if not report.ok:
        return 1
    return 2 if args.fail_on_findings and findings else 0


def command_expand(args):
    try:
        document, _warnings, report, _findings = checked_document(args.spec)
    except (SpecError, yaml.YAMLError, OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    if not report.ok:
        print("\n".join(report.errors), file=sys.stderr)
        return 1
    print(yaml.safe_dump(document, sort_keys=False, width=100), end="")
    return 0


def command_diagram(args):
    try:
        if args.control:
            try:
                from .control import render
            except ImportError:
                from control import render
            mermaid, notes = render(args.spec)
        else:
            try:
                from .diagram import render
            except ImportError:
                from diagram import render
            mermaid, findings = render(args.spec)
            notes = [f"{finding['pattern']}: {finding['claim']}" for finding in findings]
    except (SpecError, yaml.YAMLError, OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    if args.markdown:
        print(f"```mermaid\n{mermaid}\n```")
        for note in dict.fromkeys(notes):
            print(f"\n- {note}")
    else:
        print(mermaid)
    return 0


def command_diff(args):
    try:
        left_document, _left_warnings, left_report, left_findings = checked_document(args.before)
        right_document, _right_warnings, right_report, right_findings = checked_document(args.after)
        if not left_report.ok or not right_report.ok:
            errors = left_report.errors + right_report.errors
            raise RuntimeError("\n".join(errors))
        try:
            from .semantic_diff import compare, render
        except ImportError:
            from semantic_diff import compare, render
        delta = compare(
            left_document,
            right_document,
            left_findings,
            right_findings,
            left_spec=args.before,
            right_spec=args.after,
        )
    except (SpecError, yaml.YAMLError, OSError, RuntimeError) as error:
        if args.json:
            print(json.dumps({"valid": False, "errors": [str(error)]}, indent=2))
        else:
            print(f"INVALID\n\n{error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(delta, indent=2, sort_keys=True))
    else:
        print(render(delta))
    return 3 if args.fail_on_change and delta["changed"] else 0


def command_doctor(_args):
    if not os.path.isdir(os.path.join(ROOT, "tests")):
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as source:
                yaml.safe_dump(RUNTIME_SMOKE_SPEC, source, sort_keys=False)
                source.flush()
                document, warnings, report, findings = checked_document(source.name)
            missing_metadata = [
                finding.get("pattern") for finding in findings
                if not finding.get("assurance") or not finding.get("repair")
            ]
            if warnings or not report.ok or document.get("ir_revision") != "2.2":
                raise RuntimeError("runtime expansion or validation contract did not hold")
            if missing_metadata:
                raise RuntimeError(
                    f"finding metadata is incomplete for {sorted(set(missing_metadata))}"
                )
        except Exception as error:
            print(f"LoopSpec doctor: installed runtime is unhealthy: {error}", file=sys.stderr)
            return 1
        print("LoopSpec doctor: installed runtime, grammar, ontology, and check catalog are healthy")
        return 0

    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "tools/gen_spec.py", "--check"],
        [sys.executable, "tools/check_semantic_map.py"],
        [sys.executable, "tools/gen_checks.py", "--check"],
    ]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=environment)
        if result.returncode:
            return result.returncode
    print("LoopSpec doctor: semantic pipeline, generated grammar, and check catalog are healthy")
    return 0


def parser():
    root = argparse.ArgumentParser(description="Design and inspect cybernetic agent loops")
    subcommands = root.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="validate and analyze a loop spec")
    check.add_argument("spec")
    check.add_argument("--json", action="store_true", help="emit machine-readable output")
    check.add_argument("--fail-on-findings", action="store_true",
                       help="return status 2 when design findings remain")
    check.set_defaults(run=command_check)

    expand_command = subcommands.add_parser("expand", help="print canonical IR v2.2")
    expand_command.add_argument("spec")
    expand_command.set_defaults(run=command_expand)

    diff_command = subcommands.add_parser(
        "diff", help="compare two specs by canonical meaning rather than YAML text"
    )
    diff_command.add_argument("before")
    diff_command.add_argument("after")
    diff_command.add_argument("--json", action="store_true",
                              help="emit a stable machine-readable semantic delta")
    diff_command.add_argument("--fail-on-change", action="store_true",
                              help="return status 3 when semantic changes exist")
    diff_command.set_defaults(run=command_diff)

    diagram_command = subcommands.add_parser("diagram", help="render a Mermaid projection")
    diagram_command.add_argument("spec")
    diagram_command.add_argument("--control", action="store_true",
                                 help="render the feedback-ring projection")
    diagram_command.add_argument("--markdown", action="store_true",
                                 help="wrap Mermaid in a Markdown fence")
    diagram_command.set_defaults(run=command_diagram)

    doctor = subcommands.add_parser("doctor", help="run the repository health gate")
    doctor.set_defaults(run=command_doctor)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
