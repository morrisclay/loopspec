#!/usr/bin/env python3
"""
URAS Semantic Validator — the Phase 5 deliverable.

    python3 tools/validate.py                  # validate everything
    python3 tools/validate.py <file.yaml>...    # validate specific encodings
    python3 tools/validate.py --json

Exists because JSON Schema cannot express what actually matters here: loop closure,
referential integrity, temporal consistency, or the rule that an estimator may not depend
on its own output without an intervening Delay. Those are graph-level properties.

It also exists because the same structural YAML error was made three times during round 1
(list items followed by a mapping key at the same indent) and was silent until parse, plus
one reserved-word key (`on:`, which YAML 1.1 reads as boolean True). Both are exactly the
class of defect a validator catches instantly and a document does not.

ERRORS block; WARNINGS do not.
"""

import sys
import os
import glob
import json
import re

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml: pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# YAML 1.1 reads these as booleans, so using them as keys silently produces a non-string key.
# Banned outright rather than papered over: the canonical serialization must be unambiguous.
YAML11_RESERVED = {"on", "off", "yes", "no", "true", "false", "y", "n", "null", "~"}

REQUIRED_TOP = ["encodes", "set", "domain", "encoded_by", "uses"]


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")

    @property
    def ok(self):
        return not self.errors


def load_catalog():
    d = yaml.safe_load(open(os.path.join(ROOT, "ontology", "primitives.yaml")))
    core = {p["name"] for p in d["primitives"] if p.get("tier") == "core"}
    allp = {p["name"] for p in d["primitives"]}
    fields = {f["name"] for f in (d.get("fields") or [])}
    return d, core, allp, fields


# --------------------------------------------------------------- structural

def check_keys(obj, rep, where, path="$"):
    """Reserved-word keys, non-string keys, and duplicate-ish shapes."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                rep.err(where, f"{path}: non-string key {k!r} — almost certainly a YAML 1.1 "
                               f"reserved word (on/off/yes/no) parsed as a boolean")
            elif k.strip().lower() in YAML11_RESERVED:
                rep.err(where, f"{path}.{k}: reserved YAML 1.1 word used as a key")
            check_keys(v, rep, where, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_keys(v, rep, where, f"{path}[{i}]")


def depth_of(obj, d=0):
    if isinstance(obj, dict):
        return max([depth_of(v, d + 1) for k, v in obj.items()
                    if not str(k).startswith("_")] or [d])
    if isinstance(obj, list):
        return max([depth_of(v, d + 1) for v in obj] or [d])
    return d


# --------------------------------------------------------------- semantics

def maps(section):
    """Only mapping entries. Pre-normal encodings mix mappings and bare strings freely."""
    return [x for x in (section or []) if isinstance(x, dict)]


def ids_in(section):
    """Ids from a section. Pre-normal encodings mix mappings and bare strings."""
    out = set()
    for item in section or []:
        if isinstance(item, dict) and item.get("id"):
            out.add(item["id"])
        elif isinstance(item, str):
            out.add(item)
    return out


CANONICAL_RELS = {"measures", "estimates", "holds", "targets", "closes", "delays",
                  "constrains", "authorizes", "consumes", "revises", "contains", "bears",
                  # added after the held-out set demanded them — relations, not primitives
                  "asserts", "replenishes", "produces"}


def check_canonical(path, doc, allp, rep):
    """Validate a flat node/edge document against schema/uras.graph.md."""
    where = os.path.basename(path)
    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []

    ids, kinds = {}, {}
    for n in nodes:
        i = n.get("id")
        if not i:
            rep.err(where, "node with no id")
            continue
        if i in ids:
            rep.err(where, f"duplicate node id `{i}`")
        ids[i] = n
        kinds.setdefault(n.get("kind"), []).append(i)

    # phantom keys from unquoted commas inside YAML flow mappings. Writing
    # `{id: x, note: a, b}` silently makes `b` a key with a null value and truncates the
    # note. Silent data loss, and it happened in real encodings.
    for n in nodes:
        for k, v in n.items():
            if v is None and isinstance(k, str) and (" " in k or len(k) > 30):
                rep.err(where, f"node `{n.get('id')}` has key `{k[:50]}` with a null value — "
                               f"almost certainly an unquoted comma inside a flow mapping "
                               f"splitting a prose value into a phantom key")

    # kinds must be catalogued
    for k in sorted(kinds):
        if k and k not in allp:
            rep.warn(where, f"node kind `{k}` is not in the catalog — either add the primitive "
                            f"or express it differently")

    # `uses` reachability, against node kinds rather than section names
    for prim in doc.get("uses") or []:
        if prim == "Loop":
            if not doc.get("loops"):
                rep.warn(where, "`uses` declares `Loop` but the loops list is empty")
            continue          # loops are declared top-level, not as nodes
        if prim == "Revision":
            if not [e for e in edges if e.get("rel") == "revises"]:
                rep.warn(where, "`uses` declares `Revision` but no `revises` edge exists")
            continue          # revision is an edge relation, not a node
        if prim not in kinds:
            rep.warn(where, f"`uses` declares `{prim}` but no node has that kind")

    # edges: closed vocabulary + referential integrity
    for e in edges:
        r = e.get("rel")
        if r not in CANONICAL_RELS:
            rep.err(where, f"edge rel `{r}` is outside the closed vocabulary "
                           f"{sorted(CANONICAL_RELS)}")
        for end in ("from", "to"):
            v = e.get(end)
            if v not in ids:
                rep.err(where, f"edge {end} `{v}` references no declared node")

    # loops must close, name real nodes, and be distinct
    seen = {}
    for lp in maps(doc.get("loops")):
        for field, want in (("timescale", "TimeScale"), ("signal", "Signal"),
                            ("intervention", "Intervention")):
            v = lp.get(field)
            if not v:
                rep.err(where, f"loop `{lp.get('id')}` does not close: missing {field}")
            elif v not in ids:
                rep.err(where, f"loop `{lp.get('id')}` {field} `{v}` references no node")
            elif ids[v].get("kind") != want:
                rep.err(where, f"loop `{lp.get('id')}` {field} `{v}` is kind "
                               f"`{ids[v].get('kind')}`, expected `{want}`")
        key = (lp.get("timescale"), lp.get("intervention"))
        if key in seen:
            rep.err(where, f"loops `{seen[key]}` and `{lp.get('id')}` share timescale and "
                           f"closing intervention — under the identity rule they are one loop")
        seen[key] = lp.get("id")

    # every Party bears a Consequence (edge rel: bears)
    bears = {e["from"] for e in edges if e.get("rel") == "bears"}
    for pid in kinds.get("Party", []):
        if pid not in bears:
            rep.err(where, f"party `{pid}` bears no Consequence — under the narrowed definition "
                           f"an authority-holding node bearing none is a component, not a Party")

    # every Estimator declares an idempotency basis
    for eid in kinds.get("Estimator", []):
        if not ids[eid].get("idempotency_basis"):
            rep.err(where, f"estimator `{eid}` declares no idempotency_basis — under "
                           f"at-least-once execution it can double-count evidence silently")

    # own-structure interventions need a motive
    for iid in kinds.get("Intervention", []):
        n = ids[iid]
        if n.get("target") == "own-structure" and not n.get("motive"):
            rep.err(where, f"intervention `{iid}` targets own-structure with no motive")

    d = depth_of(doc)
    if d > 4:
        rep.err(where, f"nesting depth {d} exceeds the canonical ceiling of 4")

    return rep


def check_encoding(path, doc, core, allp, rep):
    where = os.path.basename(path)

    # In the canonical flat shape `uses` is DERIVABLE from node kinds, so it is optional
    # there and synthesised when absent. Both independent encoders omitted it on all four
    # held-out systems — unanimous omission is better evidence of redundancy than an
    # argument. It remains required for pre-normal nested encodings, where nothing else
    # records which primitives an encoding relies on.
    canonical = doc.get("shape") == "canonical-graph" or "nodes" in doc
    if canonical and "uses" not in doc:
        doc["uses"] = sorted({n.get("kind") for n in (doc.get("nodes") or [])
                              if n.get("kind")})
        doc["_uses_derived"] = True

    for k in REQUIRED_TOP:
        if k not in doc:
            rep.err(where, f"missing required top-level key `{k}`")

    check_keys(doc, rep, where)

    # Canonical flat documents take the canonical path; the nested checks below apply only
    # to pre-normal round-1 encodings, retained as the evidentiary record.
    if doc.get("shape") == "canonical-graph" or "nodes" in doc:
        return check_canonical(path, doc, allp, rep)

    # --- uses must name real core primitives
    unknown = sorted(set(doc.get("uses") or []) - allp)
    if unknown:
        rep.err(where, f"`uses` names primitives absent from the catalog: {unknown}")

    sysd = doc.get("system") or {}

    parties = ids_in(sysd.get("parties"))
    estimands = ids_in(sysd.get("estimands"))
    signals = ids_in(sysd.get("signals"))
    interventions = ids_in(sysd.get("interventions"))
    estimators = ids_in(sysd.get("estimators"))
    delays = ids_in(sysd.get("delays"))

    # --- referential integrity: every reference resolves
    for est in maps(sysd.get("estimators")):
        for s in est.get("from") or []:
            base = str(s).split(".")[0]
            if base not in signals and base not in estimands:
                rep.err(where, f"estimator `{est.get('id')}` reads `{s}` which is neither a "
                               f"declared signal nor estimand")
        to = est.get("to")
        if to and str(to).split(".")[0] not in estimands:
            rep.err(where, f"estimator `{est.get('id')}` writes `{to}` which is not a declared estimand")

    for sig in maps(sysd.get("signals")):
        m = sig.get("measures")
        if m and m not in estimands:
            rep.err(where, f"signal `{sig.get('id')}` measures `{m}` which is not a declared estimand")

    for dc in maps(sysd.get("desired_conditions")):
        tgt = dc.get("applies_to")
        if tgt and str(tgt).split(".")[0] not in estimands:
            rep.err(where, f"desired_condition `{dc.get('id')}` applies to `{tgt}` which is not "
                           f"a declared estimand")
        hb = dc.get("held_by")
        if hb and hb not in parties:
            rep.err(where, f"desired_condition `{dc.get('id')}` held_by `{hb}` which is not a "
                           f"declared party")

    # --- Estimator idempotency. Required, not advisory: alarm delivery is at-least-once,
    #     so a Bayesian update applied twice double-counts into a well-formed wrong posterior.
    for est in maps(sysd.get("estimators")):
        if not est.get("idempotency_basis"):
            rep.err(where, f"estimator `{est.get('id')}` declares no idempotency_basis — under "
                           f"at-least-once execution it can double-count evidence silently")

    # --- no estimator may depend on its own output without an intervening Delay
    delayed_targets = {d.get("applies_to") for d in maps(sysd.get("delays"))}
    for est in maps(sysd.get("estimators")):
        reads = {str(s).split(".")[0] for s in (est.get("from") or [])}
        writes = str(est.get("to") or "").split(".")[0]
        if writes and writes in reads and est.get("id") not in delayed_targets:
            rep.err(where, f"estimator `{est.get('id')}` reads and writes `{writes}` with no "
                           f"declared Delay — an algebraic loop")

    # --- loop closure
    for lp in maps(doc.get("loops")):
        name = lp.get("name", "?")
        sig, iv = lp.get("signal"), lp.get("intervention")
        if not sig or not iv:
            rep.err(where, f"loop `{name}` does not close: needs both a signal and an intervention")
            continue
        if signals and sig not in signals:
            rep.warn(where, f"loop `{name}` names signal `{sig}` not declared in system.signals")
        if interventions and iv not in interventions:
            rep.warn(where, f"loop `{name}` names intervention `{iv}` not declared in "
                            f"system.interventions")
        if not lp.get("timescale"):
            rep.err(where, f"loop `{name}` declares no timescale — required by the loop identity rule")

    # --- loop identity rule: distinct (timescale, closing intervention)
    seen = {}
    for lp in maps(doc.get("loops")):
        key = (lp.get("timescale"), lp.get("intervention"))
        if key in seen:
            rep.err(where, f"loops `{seen[key]}` and `{lp.get('name')}` share both timescale and "
                           f"closing intervention — under the loop identity rule they are one loop")
        seen[key] = lp.get("name")

    # --- Party requires consequence-bearing (resolved open question, round 1)
    #     Pre-normal encodings sometimes list parties as bare strings rather than mappings.
    for p in maps(sysd.get("parties")):
        if not isinstance(p, dict):
            continue
        if "consequence" not in p:
            rep.warn(where, f"party `{p.get('id')}` declares no consequence — under the resolved "
                            f"definition a Party bears consequences; an authority-holding "
                            f"mechanism that bears none is a component, not a Party")

    # --- interventions acting on own structure must state a motive
    for iv in maps(sysd.get("interventions")):
        if not isinstance(iv, dict):
            continue
        if iv.get("target") == "own-structure" and not iv.get("motive"):
            rep.err(where, f"intervention `{iv.get('id')}` targets own-structure but states no "
                           f"motive — the payoff is in future evidence economics and is lost "
                           f"without it")

    # --- probability well-formedness where numeric
    for e in maps(sysd.get("estimates")):
        if not isinstance(e, dict):
            continue
        dist = e.get("distribution")
        if isinstance(dist, dict):
            vals = [v for v in dist.values() if isinstance(v, (int, float))]
            if vals and abs(sum(vals) - 1.0) > 1e-6:
                rep.err(where, f"estimate `{e.get('id')}` distribution sums to {sum(vals)}, not 1.0")

    # --- scalarization prohibition
    po = sysd.get("preference_ordering")
    if isinstance(po, dict) and po.get("scalarized") is True:
        rep.err(where, "preference_ordering is scalarized — the representation must hold the "
                       "conflict; scalarizing is a policy-layer decision")

    # --- reachability: a declared `uses` entry should correspond to real content.
    #     An explicit map, because naive pluralisation cannot get Party -> parties and
    #     treats System (the container itself) as unreachable.
    SECTIONS = {
        "System": None,                      # the container; always present by construction
        "Boundary": ["boundary"],
        "Party": ["parties"],
        "Estimand": ["estimands"],
        "Signal": ["signals"],
        "Estimate": ["estimates", "parties"],          # may live inline on parties
        "Evidence": ["evidence"],
        "Estimator": ["estimators"],
        "DesiredCondition": ["desired_conditions"],
        "PreferenceOrdering": ["preference_ordering"],
        "Consequence": ["parties", "consequences"],    # normally inline on parties
        "Intervention": ["interventions"],
        "Policy": ["policies"],
        "Loop": None,                        # declared at top level, not under system
        "Delay": ["delays"],
        "TimeScale": ["timescales", "loops"],
        "Resource": ["resources"],
        "Constraint": ["constraints"],
        "Revision": ["revisions"],
    }
    body_text = json.dumps(sysd, default=str).lower()
    for prim in doc.get("uses") or []:
        want = SECTIONS.get(prim, [])
        if want is None:
            continue
        if not want:
            rep.warn(where, f"`uses` declares `{prim}` which the validator has no section "
                            f"mapping for — extend SECTIONS")
            continue
        if not any(w in sysd for w in want) and not any(w in body_text for w in want):
            rep.warn(where, f"`uses` declares `{prim}` but no {'/'.join(want)} section carries "
                            f"it — unreachable declaration")

    # --- comprehensibility bound (Toyota A3: bounded beats unbounded)
    d = depth_of(doc)
    if d > 6:
        rep.err(where, f"nesting depth {d} exceeds the hard bound of 6")
    elif d > 4:
        rep.warn(where, f"nesting depth {d} exceeds the target of 4 — the A3 bar is that a "
                        f"reader not involved can follow it")

    return rep


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv

    _, core, allp, _fields = load_catalog()
    paths = args or sorted(glob.glob(os.path.join(ROOT, "benchmarks", "**", "*.yaml"),
                                     recursive=True))
    rep = Report()
    checked = 0
    for p in paths:
        try:
            doc = yaml.safe_load(open(p))
        except yaml.YAMLError as e:
            first = str(e).strip().splitlines()[0]
            rep.err(os.path.basename(p), f"YAML parse failure — {first}")
            continue
        if not isinstance(doc, dict) or "encodes" not in doc:
            continue
        check_encoding(p, doc, core, allp, rep)
        checked += 1

    if as_json:
        print(json.dumps({"checked": checked, "errors": rep.errors,
                          "warnings": rep.warnings, "ok": rep.ok}, indent=2))
        return 0 if rep.ok else 1

    print("=" * 70)
    print(f"URAS SEMANTIC VALIDATOR — {checked} encoding(s)")
    print("=" * 70)
    if rep.errors:
        print(f"\nERRORS ({len(rep.errors)}) — these block\n")
        for e in rep.errors:
            print(f"  ✗ {e}")
    if rep.warnings:
        print(f"\nWARNINGS ({len(rep.warnings)})\n")
        for w in rep.warnings:
            print(f"  ! {w}")
    if not rep.errors and not rep.warnings:
        print("\n  clean\n")
    print(f"\n{'PASS' if rep.ok else 'FAIL'} — {len(rep.errors)} error(s), "
          f"{len(rep.warnings)} warning(s)\n")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
