#!/usr/bin/env python3
"""
Project a loop spec to a Mermaid diagram that DRAWS WHAT IS BROKEN.

    python3 tools/diagram.py <spec.loop.yaml>            # mermaid to stdout
    python3 tools/diagram.py <spec.loop.yaml> --md       # wrapped in a fenced block

Briefing §5 supplies the design constraint, and it is a good one:

    every validator invariant needs a visual failure mode.
    if it cannot be drawn wrong, it probably should not be an invariant.

So this is not documentation. A dangling estimand is a node with nothing running into it. An
orphan signal is an arrow ending in space. An uncalibrated estimator has no return path. The
diagram and the linter are the same statement in two notations, and a person who cannot read
the linter's vocabulary can still see the hole.

Layout is derived, never authored — the loop format carries no coordinates. That is what makes
the diagram trustworthy: it cannot be drawn to flatter the spec.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:  # package import
    from .loop import expand  # noqa: E402
    from .derive import analyze_document  # noqa: E402
except ImportError:  # direct script
    from loop import expand  # noqa: E402
    from derive import analyze_document  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The control-loop reading order. Everything else hangs off these.
SHAPES = {
    "Estimand":         ('(["', '"])'),        # rounded — a quantity
    "DesiredCondition": ('{{"', '"}}'),        # hexagon — a target
    "Signal":           ('[/"', '"/]'),        # parallelogram — data in
    "Estimator":        ('["', '"]'),          # box — a computation
    "Calibration":      ('[\\"', '"\\]'),      # inverted trapezoid — scoring
    "Intervention":     ('>"', '"]'),          # flag — an act on the world
    "ActionProfile":    ('{{"', '"}}'),        # hexagon — a conditional binding
    "ControlOperation": ('(["', '"])'),        # stadium — controller transition
    "Output":           ('[["', '"]]'),        # subroutine — emitted value
    "Policy":           ('{"', '"}'),          # diamond — a decision
    "Party":            ('(("', '"))'),        # circle — a person or agent
    "Consequence":      ('[("', '")]'),        # cylinder — what it costs
    "Constraint":       ('["', '"]'),
    "Explanation":      ('("', '")'),
    "Delay":            ('["', '"]'),
    "Resource":         ('[("', '")]'),
    "Boundary":         ('[["', '"]]'),
    "System":           ('[("', '")]'),
}

REL_STYLE = {
    "measures":   "-->|measures|",
    "estimates":  "-->|estimates|",
    "targets":    "-.->|targets|",
    "authorizes": "-->|selects|",
    "revises":    "-->|scores|",
    "holds":      "-.->|sees|",
    "bears":      "-->|bears|",
    "explains":   "-.->|explains|",
    "asserts":    "-->|asserts|",
    "delays":     "-->|after|",
    "consumes":   "-->|consumes|",
    "constrains": "-.->|forbids|",
    "reads":      "-->|reads|",
    "compares":   "-->|outcome|",
    "causes":     "-->|through|",
    "produces":   "-->|emits|",
    "frames":     "-.->|frames|",
    "bounds":     "-.->|bounds|",
    "sets":       "-->|sets target|",
    "uses_reference": "-->|uses reference|",
    "profiles":   "-.->|profile of|",
    "emits":      "-->|emits|",
}

# Which node kinds a defect should mark, so the finding lands on the right shape.
DEFECT_ANCHOR = {
    "orphan_signal": "Signal",
    "estimand_never_estimated": "Estimand",
    "unmeasured_estimand": "Estimand",
    "uncalibrated_estimator": "Estimator",
    "policy_on_unmeasured_inputs": "Policy",
    "irreversible_without_approval": "Intervention",
    "action_profiles_without_fallback": "Intervention",
    "accountable_but_blind": "Party",
    "no_escalation_path": "Policy",
    "target_without_actuator": "DesiredCondition",
    "no_explicit_process_model": "Policy",
    "process_path_not_declared": "Intervention",
    "effect_direction_unspecified": "Intervention",
    "boundary_not_declared": "Boundary",
    "incomplete_attention_contract": "Calibration",
}

SKIP = {"TimeScale"}   # cadence is a label, not a box


def lint(doc):
    """Run the real linter over the expanded graph so the diagram cannot drift from it."""
    findings, failures = analyze_document(doc)
    if failures:
        raise RuntimeError(f"diagram analysis failed: {failures}")
    return findings


def node_label(n):
    lab = n["id"].replace("_", " ")
    k = n["kind"]
    if k == "DesiredCondition" and n.get("statement"):
        lab = n["statement"]
    elif k == "Estimator":
        lab = f"{n.get('form','estimate')}"
    elif k == "Signal" and n.get("period"):
        lab = f"{lab}<br/><i>{n['period']}</i>"
    elif k == "Intervention" and n.get("reversibility"):
        mark = {"irreversible": " ⚠", "costly": " !"}.get(n["reversibility"], "")
        lab = f"{lab}{mark}"
    elif k == "ActionProfile":
        binding = n.get("binding_stage", "binding unstated")
        undo = n.get("reversibility", "reversibility unstated")
        lab = f"{lab}<br/><i>{binding} · {undo}</i>"
    elif k == "ControlOperation":
        lab = f"{n.get('operation_kind', 'operation')}<br/><i>{lab}</i>"
    elif k == "Output":
        lab = f"{n.get('output_kind', 'output')}<br/><i>ends {n.get('terminates', 'unknown')}</i>"
    elif k == "Party":
        lab = f"{'🧑 ' if n.get('party_kind') == 'human' else ''}{lab}"
    elif k == "Boundary":
        lab = f"boundary<br/><i>{n.get('purpose', 'purpose unstated')}</i>"
    elif k == "System" and n.get("role") == "controlled_process":
        lab = f"{lab}<br/><i>{n.get('location', 'location unstated')}</i>"
    elif k == "Calibration" and n.get("review"):
        lab = f"{n['review']}<br/><i>{n.get('calibration_kind', 'review')}</i>"
    return lab.replace('"', "'")


def render(path):
    doc, _ = expand(path)
    nodes = {n["id"]: n for n in doc["nodes"]}
    findings = lint(doc)

    # attach each finding to the node it is about
    flagged = {}
    for f in findings:
        pat = f.get("pattern", "")
        want = DEFECT_ANCHOR.get(pat)
        for nid, n in nodes.items():
            if nid in str(f.get("claim", "")) and (not want or n["kind"] == want):
                flagged.setdefault(nid, []).append(pat)

    L = ["flowchart LR"]
    groups = doc.get("group") or [doc["encodes"]]

    for kind_group, title in [(("Boundary", "System"), "world and boundary"),
                              (("Signal",), "observed"),
                              (("Estimand", "Estimator", "Calibration", "Explanation"),
                               "believed"),
                              (("DesiredCondition", "Policy", "Intervention", "ActionProfile",
                                "Delay"),
                               "decided"),
                              (("ControlOperation", "Output"), "control plane"),
                              (("Party", "Consequence", "Constraint", "Resource"),
                               "accountable")]:
        members = [n for n in doc["nodes"] if n["kind"] in kind_group]
        if not members:
            continue
        L.append(f'  subgraph {title}["{title}"]')
        L.append("    direction TB")
        for n in members:
            o, c = SHAPES.get(n["kind"], ('["', '"]'))
            L.append(f'    {n["id"]}{o}{node_label(n)}{c}')
        L.append("  end")

    if any(f.get("pattern") == "boundary_not_declared" for f in findings):
        L.append('  missing_boundary[["⚠ boundary / observer / purpose missing"]]:::defect')

    for e in doc["edges"]:
        if nodes.get(e["from"], {}).get("kind") in SKIP: continue
        if nodes.get(e["to"], {}).get("kind") in SKIP: continue
        L.append(f'  {e["from"]} {REL_STYLE.get(e["rel"], "-->")} {e["to"]}')

    # --- the defects, drawn ------------------------------------------------------
    if flagged:
        L.append("")
        for i, (nid, pats) in enumerate(sorted(flagged.items())):
            note = f"defect_{i}"
            L.append(f'  {note}["⚠ {"<br/>".join(sorted(set(pats)))}"]')
            L.append(f"  {note} -.-> {nid}")
            L.append(f"  class {note} defect")
            L.append(f"  class {nid} broken")

    L += ["",
          "  classDef defect fill:#fff0f0,stroke:#c00,stroke-width:1px,color:#900;",
          "  classDef broken stroke:#c00,stroke-width:2px,stroke-dasharray:4 3;"]

    # A loop that never closes gets an arrow into nothing — the point of §5.
    for lp in doc.get("loops") or []:
        interventions = lp.get("interventions") or (
            [lp["intervention"]] if lp.get("intervention") else []
        )
        signals = lp.get("signals") or ([lp["signal"]] if lp.get("signal") else [])
        if not interventions:
            L.append(f'  {lp["id"]}_open[" "]:::defect')
            for signal in signals:
                L.append(f'  {signal} -.->|loop does not close| {lp["id"]}_open')

    return "\n".join(L), findings


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    m, fs = render(args[0])
    if "--md" in sys.argv:
        print(f"```mermaid\n{m}\n```")
        print(f"\n<!-- {len(fs)} linter finding(s) drawn -->")
    else:
        print(m)
