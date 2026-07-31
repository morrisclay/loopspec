#!/usr/bin/env python3
"""
Expand the human-facing loop format into the canonical flat graph.

    python3 tools/loop.py <spec.loop.yaml>            # print canonical YAML
    python3 tools/loop.py <spec.loop.yaml> --lint     # expand, then lint

The loop format (SPEC-FORMAT.md) is what a person writes and what an LLM compiles. The flat
graph is what the linter and the diagram consume. Nobody should have to author the flat graph
by hand — that was a tooling convenience that leaked into the product.

The expansion is mechanical and total: every key in the loop format produces nodes and edges,
and nothing in the loop format is discarded. That is deliberate — if expansion had to make
choices, two readers of the same spec would disagree, which is the determinacy failure this
project exists to avoid.

Multiple loops in one file (a GROUP) are separated by `---`. Nodes shared between loops — the
same estimand name, the same party — are the same node, which is what makes the group checks
possible at all.
"""
import sys, os, re, json

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")



# ---------------------------------------------------------------------------------------
# STRICT VALIDATION against schema/loop.keys.yaml
#
# Unknown keys are errors, not warnings. A spec misspelling `reversibility` on an act named
# `wipe_production` used to parse clean and produce no finding — the most dangerous
# declaration in the format is the easiest to lose, and in a format written mostly by LLMs
# that is the defining failure mode.
# ---------------------------------------------------------------------------------------

GRAMMAR = yaml.safe_load(
    open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "schema", "loop.keys.yaml")))


def _near(word, options):
    """Did-you-mean, so an error names the fix rather than only the fault."""
    import difflib
    m = difflib.get_close_matches(str(word), list(options), n=1, cutoff=0.6)
    return f" Did you mean `{m[0]}`?" if m else ""


class SpecError(Exception):
    pass


def _check_entry(spec_name, entry, section, errs, where):
    rules = GRAMMAR.get(section) or {}
    if not isinstance(entry, dict):
        return
    for k, v in entry.items():
        if k not in rules:
            errs.append(f"{where}: unknown key `{k}`.{_near(k, rules)}")
            continue
        r = rules[k]
        if r.get("enum") and v is not None and v not in r["enum"]:
            errs.append(f"{where}: `{k}` is `{v}`, which is not one of {r['enum']}."
                        f"{_near(v, r['enum'])}")


def validate(spec, path="<spec>", scope=None):
    errs = []
    scope = scope or spec
    top = GRAMMAR["top_level"]
    aliases = {a: k for k, r in top.items() for a in (r.get("aliases") or [])}
    for k in spec:
        if k not in top and k not in aliases:
            errs.append(f"top level: unknown key `{k}`.{_near(k, top)}")
    if not (spec.get("loop") or spec.get("name")):
        errs.append("top level: every spec needs a `loop:` name.")

    for section, entry_kind in [("regulates", "regulates_entry"),
                                ("estimates", "estimates_entry"),
                                ("observes", "observes_entry"),
                                ("acts", "acts_entry"),
                                ("parties", "parties_entry")]:
        for nm, body in (spec.get(section) or {}).items():
            _check_entry(nm, body or {}, entry_kind, errs, f"{section}.{nm}")
    for i, r in enumerate(spec.get("when") or []):
        _check_entry(i, r or {}, "when_entry", errs, f"when[{i}]")

    # --- referential integrity: a name that points at nothing is a silent hole -------
    acts = set((scope.get("acts") or {}).keys())
    parties = set((scope.get("parties") or {}).keys())
    signals = set((scope.get("observes") or {}).keys())
    estimands = set((scope.get("regulates") or {}).keys()) | \
                set((scope.get("estimates") or {}).keys())

    for nm, body in (spec.get("acts") or {}).items():
        ap = (body or {}).get("approval")
        if ap and ap not in parties:
            errs.append(f"acts.{nm}: `approval: {ap}` names no party in `parties`."
                        f"{_near(ap, parties)} The gate is declared and does not exist.")
    for i, r in enumerate(spec.get("when") or []):
        for a in ([r.get("do")] if isinstance(r.get("do"), str) else (r.get("do") or [])):
            if a and a not in acts:
                errs.append(f"when[{i}]: `do: {a}` names no entry in `acts`.{_near(a, acts)}")
        esc = (r or {}).get("escalate")
        if esc and esc not in parties:
            errs.append(f"when[{i}]: `escalate: {esc}` names no party."
                        f"{_near(esc, parties)}")
    for nm, body in (spec.get("estimates") or {}).items():
        for src in ((body or {}).get("from") or []):
            if src not in signals:
                errs.append(f"estimates.{nm}: `from: {src}` names no entry in `observes`."
                            f"{_near(src, signals)}")
    for nm, body in (spec.get("parties") or {}).items():
        for e in ((body or {}).get("sees") or []):
            if e not in estimands:
                errs.append(f"parties.{nm}: `sees: {e}` names no estimand."
                            f"{_near(e, estimands)}")
    for nm, body in (spec.get("observes") or {}).items():
        p = (body or {}).get("produced_by")
        if p and p not in acts:
            errs.append(f"observes.{nm}: `produced_by: {p}` names no act.{_near(p, acts)}")

    if errs:
        raise SpecError(f"{path}: {len(errs)} error(s)\n" +
                        "\n".join(f"  ✗ {e}" for e in errs))


def slug(s):
    return re.sub(r"[^a-z0-9_]+", "_", str(s).lower()).strip("_")


class Graph:
    """Nodes are merged by id across loops. That merge IS the group."""

    def __init__(self):
        self.nodes, self.edges, self.loops = {}, [], []
        self.excluded, self.warnings = [], []

    def node(self, nid, kind, **fields):
        nid = slug(nid)
        if nid in self.nodes:
            existing = self.nodes[nid]
            if existing["kind"] != kind:
                self.warnings.append(
                    f"`{nid}` is a {existing['kind']} in one loop and a {kind} in another")
            else:
                # merging across loops in a group: later fields fill gaps, never overwrite
                for k, v in fields.items():
                    existing.setdefault(k, v)
            return nid
        self.nodes[nid] = {"id": nid, "kind": kind,
                           **{k: v for k, v in fields.items() if v is not None}}
        return nid

    def edge(self, a, b, rel):
        e = {"from": slug(a), "to": slug(b), "rel": rel}
        if e not in self.edges:
            self.edges.append(e)

    def doc(self, name):
        return {"uras_version": 0, "encodes": name, "set": "field",
                "nodes": list(self.nodes.values()), "edges": self.edges,
                "loops": self.loops, "excluded_variables": self.excluded}


def timescale(g, period, owner):
    """Cadences are shared: two things running `daily` reference one TimeScale."""
    if not period:
        return None
    return g.node(f"every_{slug(period)}", "TimeScale", period=str(period))


def expand_one(g, spec, path="<spec>", scope=None):
    validate(spec, path, scope)
    name = spec.get("loop") or spec.get("name")
    lid = slug(name)

    g.node(lid + "_system", "System", label=str(name).replace("_", " "))
    cadence = timescale(g, spec.get("every"), lid)

    # --- regulates: what the loop steers -------------------------------------------
    for est, body in (spec.get("regulates") or {}).items():
        body = body or {}
        g.node(est, "Estimand", determination="computed",
               computed_from=body.get("computed_from"))
        if body.get("target"):
            tid = g.node(f"{slug(est)}_target", "DesiredCondition",
                         statement=str(body["target"]),
                         confidence_in_target=body.get("confidence"))
            g.edge(tid, est, "targets")

    # --- estimates: what it believes but cannot see --------------------------------
    for est, body in (spec.get("estimates") or {}).items():
        body = body or {}
        g.node(est, "Estimand", determination="latent",
               settled_by=body.get("settled_by"))
        eid = g.node(f"{lid}_estimate_{slug(est)}", "Estimator",
                     form=body.get("method", "unspecified"),
                     idempotency_basis=body.get("idempotency_basis",
                                                f"observations feeding {slug(est)}"))
        g.edge(eid, est, "estimates")
        for src in body.get("from") or []:
            g.edge(src, est, "measures")
        if body.get("calibrated_by"):
            cid = g.node(body["calibrated_by"], "Calibration",
                         scores=slug(est), window=body.get("window"))
            g.edge(cid, eid, "revises")
        if body.get("explains"):
            xid = g.node(f"{slug(est)}_explains_{slug(body['explains'])}", "Explanation",
                         mechanism=f"{est} accounts for {body['explains']}")
            g.edge(xid, body["explains"], "explains")
            g.edge(est, xid, "asserts")

    # --- observes: what actually arrives -------------------------------------------
    for sig, body in (spec.get("observes") or {}).items():
        body = body or {}
        # sampling period is a field, not an edge: the closed rel vocabulary has no
        # `sampled_at`, and inventing one to carry a scalar is how vocabularies rot.
        g.node(sig, "Signal", cost=body.get("cost"), period=body.get("every"),
               asserted_by=body.get("asserted_by"),
               produced_by=body.get("produced_by"))
        if body.get("measures"):
            g.edge(sig, body["measures"], "measures")
        if body.get("produced_by"):
            # An observation MANUFACTURED inside the system is not evidence from outside it.
            # This is the edge the group checks read to find loops that cannot be corrected.
            g.edge(body["produced_by"], sig, "produces")
        timescale(g, body.get("every"), sig)
        if body.get("asserted_by"):
            # a REPORTED number is not a measured one
            g.edge(body["asserted_by"], sig, "asserts")

    # --- acts: the levers ----------------------------------------------------------
    for act, body in (spec.get("acts") or {}).items():
        body = body or {}
        g.node(act, "Intervention",
               target=body.get("moves"),
               reversibility=body.get("reversibility"),
               requires_approval_from=(slug(body["approval"])
                                       if body.get("approval") else None))
        if body.get("moves"):
            g.edge(act, body["moves"], "targets")
        if body.get("delay"):
            did = g.node(f"{slug(act)}_delay", "Delay", duration=str(body["delay"]),
                         damping=body.get("damping"))
            g.edge(act, did, "delays")
        if body.get("approval"):
            g.edge(body["approval"], act, "authorizes")
        for r in body.get("consumes") or []:
            g.node(r, "Resource")
            g.edge(act, r, "consumes")

    # --- when: the decision rule ---------------------------------------------------
    rules = spec.get("when") or []
    if rules:
        pid = g.node(f"{lid}_policy", "Policy",
                     rule="; ".join(str(r.get("if", "always")) for r in rules),
                     inputs=sorted({t for r in rules
                                    for t in re.findall(r"[a-z_][a-z0-9_]{2,}",
                                                        str(r.get("if", "")))
                                    if t not in ("and", "or", "not", "confidence")}),
                     escalates=next((slug(r["escalate"]) for r in rules
                                     if r.get("escalate")), None))
        for r in rules:
            if r.get("do"):
                for a in ([r["do"]] if isinstance(r["do"], str) else r["do"]):
                    g.edge(pid, a, "authorizes")

    # --- parties: who is exposed ----------------------------------------------------
    for p, body in (spec.get("parties") or {}).items():
        body = body or {}
        kind = ("human" if body.get("human") else
                "agent" if body.get("agent") else body.get("kind", "system"))
        g.node(p, "Party", party_kind=kind, authority=body.get("authority"))
        if body.get("bears") and body["bears"] != "nothing":
            cid = g.node(f"{slug(p)}_consequence", "Consequence",
                         statement=str(body["bears"]),
                         asymmetry=body.get("asymmetry"))
            g.edge(p, cid, "bears")
        for e in body.get("sees") or []:
            g.edge(p, e, "holds")

    # --- never: the guardrails -------------------------------------------------------
    for i, c in enumerate(spec.get("never") or []):
        cid = g.node(f"{lid}_never_{i}", "Constraint", statement=str(c))
        g.edge(cid, lid + "_system", "constrains")

    g.excluded += [str(x) for x in (spec.get("ignoring") or [])]

    # --- the loop record itself -------------------------------------------------------
    sigs = list((spec.get("observes") or {}).keys())
    acts = list((spec.get("acts") or {}).keys())
    g.loops.append({"id": lid,
                    "timescale": cadence,
                    "signal": slug(sigs[0]) if sigs else None,
                    "signals": [slug(s) for s in sigs],
                    "intervention": slug(acts[0]) if acts else None,
                    "interventions": [slug(a) for a in acts]})
    return lid


def expand(path):
    docs = [d for d in yaml.safe_load_all(open(path)) if d]
    # the file is the scope: build the union of every declared name across the group first
    scope = {}
    for section in ("acts", "parties", "observes", "regulates", "estimates"):
        scope[section] = {k: v for d in docs for k, v in (d.get(section) or {}).items()}
    g = Graph()
    names = [expand_one(g, d, path, scope) for d in docs]
    name = names[0] if len(names) == 1 else os.path.basename(path).split(".")[0]
    doc = g.doc(name)
    if len(names) > 1:
        doc["group"] = names
    return doc, g.warnings


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    try:
        doc, warns = expand(args[0])
    except SpecError as e:
        sys.exit(f"\n{e}\n")
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    out = yaml.safe_dump(doc, sort_keys=False, width=100)
    if "--lint" in sys.argv:
        tmp = "/tmp/_uras_expanded.yaml"
        open(tmp, "w").write(out)
        os.execvp("python3", ["python3", os.path.join(os.path.dirname(__file__), "derive.py"),
                              tmp])
    print(out)
