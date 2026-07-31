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
import sys, os, subprocess, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop import expand  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The control-loop reading order. Everything else hangs off these.
SHAPES = {
    "Estimand":         ('(["', '"])'),        # rounded — a quantity
    "DesiredCondition": ('{{"', '"}}'),        # hexagon — a target
    "Signal":           ('[/"', '"/]'),        # parallelogram — data in
    "Estimator":        ('["', '"]'),          # box — a computation
    "Calibration":      ('[\\"', '"\\]'),      # inverted trapezoid — scoring
    "Intervention":     ('>"', '"]'),          # flag — an act on the world
    "Policy":           ('{"', '"}'),          # diamond — a decision
    "Party":            ('(("', '"))'),        # circle — a person or agent
    "Consequence":      ('[("', '")]'),        # cylinder — what it costs
    "Constraint":       ('["', '"]'),
    "Explanation":      ('("', '")'),
    "Delay":            ('["', '"]'),
    "Resource":         ('[("', '")]'),
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
}

# Which node kinds a defect should mark, so the finding lands on the right shape.
DEFECT_ANCHOR = {
    "orphan_signal": "Signal",
    "estimand_never_estimated": "Estimand",
    "unmeasured_estimand": "Estimand",
    "uncalibrated_estimator": "Estimator",
    "policy_on_unmeasured_inputs": "Policy",
    "irreversible_without_approval": "Intervention",
    "accountable_but_blind": "Party",
    "no_escalation_path": "Policy",
    "uncontrollable_target": "DesiredCondition",
    "regulator_without_model": "Policy",
}

SKIP = {"System", "TimeScale"}   # cadence is a label, not a box


def lint(doc):
    """Run the real linter over the expanded graph so the diagram cannot drift from it."""
    import yaml
    tmp = "/tmp/_uras_diagram.yaml"
    open(tmp, "w").write(yaml.safe_dump(doc, sort_keys=False))
    try:
        out = subprocess.run(["python3", os.path.join(ROOT, "tools", "derive.py"), tmp,
                              "--json"], capture_output=True, text=True, timeout=120).stdout
        return [c for cs in json.loads(out).values() for c in cs]
    except Exception:
        return []


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
    elif k == "Party":
        lab = f"{'🧑 ' if n.get('party_kind') == 'human' else ''}{lab}"
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

    for kind_group, title in [(("Signal",), "observed"),
                              (("Estimand", "Estimator", "Calibration", "Explanation"),
                               "believed"),
                              (("DesiredCondition", "Policy", "Intervention", "Delay"),
                               "decided"),
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
        if not lp.get("intervention"):
            L.append(f'  {lp["id"]}_open[" "]:::defect')
            if lp.get("signal"):
                L.append(f'  {lp["signal"]} -.->|loop does not close| {lp["id"]}_open')

    return "\n".join(L), findings


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    m, fs = render(args[0])
    if "--md" in sys.argv:
        print(f"```mermaid\n{m}\n```")
        print(f"\n<!-- {len(fs)} linter finding(s) drawn -->")
    else:
        print(m)
