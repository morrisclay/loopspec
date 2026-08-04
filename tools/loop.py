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
import sys, os, re, json, subprocess, tempfile

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

try:
    from .runtime_paths import ROOT
except ImportError:
    from runtime_paths import ROOT



# ---------------------------------------------------------------------------------------
# STRICT VALIDATION against schema/loop.keys.yaml
#
# Unknown keys are errors, not warnings. A spec misspelling `reversibility` on an act named
# `wipe_production` used to parse clean and produce no finding — the most dangerous
# declaration in the format is the easiest to lose, and in a format written mostly by LLMs
# that is the defining failure mode.
# ---------------------------------------------------------------------------------------

GRAMMAR = yaml.safe_load(
    open(os.path.join(ROOT, "schema", "loop.keys.yaml")))



def _alias_map(section):
    return {a: k for k, r in (GRAMMAR.get(section) or {}).items()
            for a in (r.get("aliases") or [])}


SECTION_OF = {"goal": "goal_entry", "beliefs": "beliefs_entry",
              "observes": "observes_entry", "actions": "actions_entry",
              "people": "people_entry", "spends": "spends_entry",
              "consider": "consider_entry", "processes": "processes_entry"}
SINGLETON_OF = {"boundary": "boundary_entry"}


VALUE_ALIASES = {
    ("actions", "can_undo"): {"reversible": "yes", "irreversible": "no", "costly": "costly",
                              True: "yes", False: "no"},
    ("observes", "how"): {"measurement": "measured", "report": "reported",
                          "computed": "calculated"},
}


class SpecError(Exception):
    pass


def _rename_keys(values, aliases, where):
    """Apply aliases without allowing two source keys to collapse silently."""
    out = {}
    sources = {}
    for source, value in values.items():
        canonical = aliases.get(source, source)
        if canonical in out:
            previous = sources[canonical]
            if canonical in (source, previous):
                alias = previous if previous != canonical else source
                raise SpecError(
                    f"{where}: both `{canonical}` and its alias `{alias}` are present; "
                    "remove one so precedence is explicit"
                )
            raise SpecError(
                f"{where}: `{previous}` and `{source}` are aliases of `{canonical}`; "
                "remove one so precedence is explicit"
            )
        out[canonical] = value
        sources[canonical] = source
    return out


def normalize(spec):
    """
    Rewrite v0 names to v1 before anything else looks at the spec.

    v1 renamed most keys after a blind test showed three independent designers rejecting the
    borrowed vocabulary. Aliases keep every v0 spec parsing — a format that breaks its own
    corpus to improve its naming has bought legibility with trust.
    """
    if not isinstance(spec, dict):
        return spec
    top = _alias_map("top_level")
    out = _rename_keys(spec, top, "top level")
    for sec, entry in SECTION_OF.items():
        if not isinstance(out.get(sec), dict):
            continue
        am = _alias_map(entry)
        def fix(name, body):
            if not isinstance(body, dict):
                return body
            b = _rename_keys(body, am, f"{sec}.{name}")
            for k, v in list(b.items()):
                vmap = VALUE_ALIASES.get((sec, k))
                if vmap and (isinstance(v, bool) or isinstance(v, str)) and v in vmap:
                    b[k] = vmap[v]
            return b
        out[sec] = {nm: fix(nm, body) for nm, body in out[sec].items()}
    for sec, entry in SINGLETON_OF.items():
        if isinstance(out.get(sec), dict):
            out[sec] = _rename_keys(out[sec], _alias_map(entry), sec)
    if isinstance(out.get("when"), list):
        am = _alias_map("when_entry")
        out["when"] = [_rename_keys(r or {}, am, f"when[{i}]")
                       if isinstance(r, dict) else r
                       for i, r in enumerate(out["when"])]
    return out


def _near(word, options):
    """Did-you-mean, so an error names the fix rather than only the fault."""
    import difflib
    m = difflib.get_close_matches(str(word), list(options), n=1, cutoff=0.6)
    return f" Did you mean `{m[0]}`?" if m else ""


DEPRECATIONS = []


def _matches_type(value, declared):
    if value is None:
        return True
    choices = declared if isinstance(declared, list) else [declared]
    checks = {
        "str": lambda v: isinstance(v, str),
        "bool": lambda v: isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "map": lambda v: isinstance(v, dict),
        "list": lambda v: isinstance(v, list),
    }
    return any(checks.get(choice, lambda _v: False)(value) for choice in choices)


def _check_type(value, rule, errs, where):
    declared = rule.get("type")
    if declared and not _matches_type(value, declared):
        choices = declared if isinstance(declared, list) else [declared]
        errs.append(f"{where}: expected {' or '.join(choices)}, got {type(value).__name__}")


def _check_entry(spec_name, entry, section, errs, where):
    rules = GRAMMAR.get(section) or {}
    if not isinstance(entry, dict):
        errs.append(f"{where}: expected a map of fields, got {type(entry).__name__}")
        return
    for key, rule in rules.items():
        if rule.get("required") and not entry.get(key):
            errs.append(f"{where}: every entry needs a `{key}:` value")
    for k, v in entry.items():
        if k in rules and rules[k].get("deprecated"):
            DEPRECATIONS.append(f"{where}: `{k}` is deprecated — "
                                + " ".join(str(rules[k].get("doc", "")).split())[:150])
        if k not in rules:
            errs.append(f"{where}: unknown key `{k}`.{_near(k, rules)}")
            continue
        r = rules[k]
        _check_type(v, r, errs, f"{where}.{k}")
        if (isinstance(v, (int, float)) and not isinstance(v, bool) and
                r.get("minimum") is not None and v < r["minimum"]):
            errs.append(f"{where}.{k}: {v} is below minimum {r['minimum']}")
        if (isinstance(v, (int, float)) and not isinstance(v, bool) and
                r.get("maximum") is not None and v > r["maximum"]):
            errs.append(f"{where}.{k}: {v} is above maximum {r['maximum']}")
        if r.get("values_enum") and isinstance(v, dict):
            for item_key, item_value in v.items():
                if item_value not in r["values_enum"]:
                    errs.append(f"{where}.{k}.{item_key}: `{item_value}` is not one of "
                                f"{r['values_enum']}")
        if v is True and "yes" in (r.get("enum") or []):
            v = "yes"
        elif v is False and "no" in (r.get("enum") or []):
            v = "no"
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
        elif k in top:
            _check_type(spec[k], top[k], errs, f"top level.{k}")
    for key, rule in top.items():
        if rule.get("required") and not spec.get(key):
            errs.append(f"top level: every spec needs a `{key}:` value.")

    # Stop before referential checks if container shapes are wrong; otherwise a useful type
    # error degrades into an AttributeError while walking `.items()` below.
    if errs:
        raise SpecError(f"{path}: {len(errs)} error(s)\n" +
                        "\n".join(f"  ✗ {e}" for e in errs))

    for section, entry_kind in SECTION_OF.items():
        for nm, body in (spec.get(section) or {}).items():
            _check_entry(nm, body or {}, entry_kind, errs, f"{section}.{nm}")
    for section, entry_kind in SINGLETON_OF.items():
        if section in spec:
            _check_entry(section, spec.get(section) or {}, entry_kind, errs, section)
    for i, r in enumerate(spec.get("when") or []):
        _check_entry(i, r or {}, "when_entry", errs, f"when[{i}]")

    if errs:
        raise SpecError(f"{path}: {len(errs)} error(s)\n" +
                        "\n".join(f"  ✗ {e}" for e in errs))

    # --- referential integrity: a name that points at nothing is a silent hole -------
    acts = set((scope.get("actions") or {}).keys())
    parties = set((scope.get("people") or {}).keys())
    signals = set((scope.get("observes") or {}).keys())
    processes = set((scope.get("processes") or {}).keys())
    estimands = set((scope.get("goal") or {}).keys()) | \
                set((scope.get("beliefs") or {}).keys())

    loops_in_file = {str(d.get("loop") or d.get("name")) for d in [spec]} | set(
        (scope.get("_loops") or []))
    loop_quantities = (scope.get("_loop_quantities") or {
        str(spec.get("loop") or spec.get("name")): set(spec.get("goal") or {}) |
        set(spec.get("beliefs") or {})
    })
    for nm, body in (spec.get("goal") or {}).items():
        sb = (body or {}).get("set_by")
        if not sb:
            continue
        if "." not in str(sb):
            errs.append(f"goal.{nm}: `set_by: {sb}` needs the form `<loop>.<quantity>` — which "
                        f"loop, and which of its quantities IS this setpoint. Naming only the "
                        f"loop leaves the link unverifiable.")
            continue
        outer, _, q = str(sb).partition(".")
        if outer not in loops_in_file:
            errs.append(f"goal.{nm}: `set_by: {sb}` names no loop `{outer}` in this file."
                        f"{_near(outer, loops_in_file)} Put both loops in one file, "
                        f"separated by `---`.")
        elif q not in set(loop_quantities.get(outer) or []):
            errs.append(f"goal.{nm}: `set_by: {sb}` — `{outer}` declares no quantity `{q}`."
                        f"{_near(q, set(loop_quantities.get(outer) or []))}")
    for nm, body in (spec.get("actions") or {}).items():
        ap = (body or {}).get("needs_approval")
        if ap and ap not in parties:
            errs.append(f"actions.{nm}: `needs_approval: {ap}` names nobody in `people`."
                        f"{_near(ap, parties)} The gate is declared and does not exist.")
        through = (body or {}).get("through")
        for process in ([through] if isinstance(through, str) else (through or [])):
            if process not in processes:
                errs.append(f"actions.{nm}: `through: {process}` names no entry in "
                            f"`processes`.{_near(process, processes)}")
    for i, r in enumerate(spec.get("when") or []):
        for a in ([r.get("do")] if isinstance(r.get("do"), str) else (r.get("do") or [])):
            if a and a not in acts:
                errs.append(f"when[{i}]: `do: {a}` names no entry in `actions`."
                            f"{_near(a, acts)}")
        esc = (r or {}).get("escalate")
        if esc and esc not in parties:
            errs.append(f"when[{i}]: `escalate: {esc}` names nobody in `people`."
                        f"{_near(esc, parties)}")
        for item in (r.get("reads") or []):
            readable = estimands | set((scope.get("spends") or {}).keys())
            if item not in readable:
                errs.append(f"when[{i}]: `reads: {item}` names nothing in `goal`, `beliefs`, "
                            f"or `spends`.{_near(item, readable)}")
        targeted_goals = {name for name, body in (spec.get("goal") or {}).items()
                          if (body or {}).get("keep")}
        for item in r.get("against") or []:
            if item not in targeted_goals:
                errs.append(f"when[{i}]: `against: {item}` names no targeted quantity in "
                            f"`goal`.{_near(item, targeted_goals)}")
            if "reads" in r and item not in (r.get("reads") or []):
                errs.append(f"when[{i}]: `against: {item}` must also appear in this rule's "
                            "`reads:`; a comparator cannot compare a value the rule does not read")
    asks_human = spec.get("asks_human")
    if asks_human and asks_human not in parties:
        errs.append(f"top level: `asks_human: {asks_human}` names nobody in `people`."
                    f"{_near(asks_human, parties)}")
    legacy_escalations = {r.get("escalate") for r in (spec.get("when") or [])
                          if r.get("escalate")}
    if len(legacy_escalations) > 1:
        errs.append(f"when: deprecated `escalate` values disagree: "
                    f"{sorted(legacy_escalations)}")
    if asks_human and legacy_escalations and asks_human not in legacy_escalations:
        errs.append(f"top-level `asks_human: {asks_human}` disagrees with deprecated "
                    f"`when[].escalate: {next(iter(legacy_escalations))}`")
    # The same edge was declarable from both ends and the two could disagree silently.
    # `informs` is canonical; `from` is deprecated and must now AGREE with it.
    for nm, body in (spec.get("beliefs") or {}).items():
        for src in ((body or {}).get("from") or []):
            o = (scope.get("observes") or {}).get(src)
            if isinstance(o, dict) and o.get("informs"):
                inf = o["informs"]
                inf = [inf] if isinstance(inf, str) else inf
                if nm not in inf:
                    errs.append(
                        f"beliefs.{nm}: `from: {src}` says {src} feeds {nm}, but "
                        f"observes.{src} says `informs: {inf[0] if len(inf)==1 else inf}`. "
                        f"The same edge is declared twice and the two disagree. Declare it "
                        f"once, on the observation, with `informs:`.")
            if src not in signals:
                errs.append(f"beliefs.{nm}: `from: {src}` names no entry in `observes`."
                            f"{_near(src, signals)}")
        outcome = (body or {}).get("checked_against")
        if outcome and outcome not in signals:
            errs.append(f"beliefs.{nm}: `checked_against: {outcome}` names no entry in "
                        f"`observes`.{_near(outcome, signals)}")
    for nm, body in (spec.get("people") or {}).items():
        role_fields = [field for field in ("human", "agent", "kind")
                       if (body or {}).get(field)]
        if len(role_fields) > 1:
            errs.append(f"people.{nm}: {role_fields} declare the party kind more than once; "
                        "choose `human`, `agent`, or `kind`")
        for e in ((body or {}).get("sees") or []):
            if e not in estimands:
                errs.append(f"people.{nm}: `sees: {e}` names nothing in `goal` or `beliefs`."
                            f"{_near(e, estimands)}")
    for nm, body in (spec.get("observes") or {}).items():
        p = (body or {}).get("produced_by")
        if p and p not in acts:
            errs.append(f"observes.{nm}: `produced_by: {p}` names no action.{_near(p, acts)}")
        if p and (body or {}).get("origin") == "outside":
            errs.append(f"observes.{nm}: `produced_by` contradicts `origin: outside`; use "
                        "`origin: ourselves` for a signal created by this loop")
        inf = (body or {}).get("informs")
        for t in ([inf] if isinstance(inf, str) else (inf or [])):
            if t and t not in estimands:
                errs.append(f"observes.{nm}: `informs: {t}` names nothing in `goal` or "
                            f"`beliefs`.{_near(t, estimands)}")
    for nm, body in (spec.get("processes") or {}).items():
        for signal in (body or {}).get("observed_as") or []:
            if signal not in signals:
                errs.append(f"processes.{nm}: `observed_as: {signal}` names no entry in "
                            f"`observes`.{_near(signal, signals)}")
    boundary = spec.get("boundary") or {}
    if boundary.get("drawn_by") and boundary["drawn_by"] not in parties:
        errs.append(f"boundary: `drawn_by: {boundary['drawn_by']}` names nobody in `people`."
                    f"{_near(boundary['drawn_by'], parties)}")
    for nm, body in (spec.get("actions") or {}).items():
        mv = (body or {}).get("moves")
        moves = [mv] if isinstance(mv, str) else (mv or [])
        if (body or {}).get("effect") and (body or {}).get("effects"):
            errs.append(f"actions.{nm}: use `effect` or `effects`, not both")
        effects = (body or {}).get("effects") or {}
        unknown_effects = sorted(set(effects) - set(moves))
        missing_effects = sorted(set(moves) - set(effects)) if effects else []
        if unknown_effects or missing_effects:
            errs.append(f"actions.{nm}: `effects` keys must exactly match `moves`; "
                        f"extra={unknown_effects}, missing={missing_effects}")
        for t in moves:
            if t and t not in estimands:
                errs.append(f"actions.{nm}: `moves: {t}` names nothing in `goal` or "
                            f"`beliefs`.{_near(t, estimands)}")
    for resource, body in (spec.get("spends") or {}).items():
        spent_by = (body or {}).get("spent_by")
        for action in ([spent_by] if isinstance(spent_by, str) else (spent_by or [])):
            if action not in acts:
                errs.append(f"spends.{resource}: `spent_by: {action}` names no entry in "
                            f"`actions`.{_near(action, acts)}")

    if errs:
        raise SpecError(f"{path}: {len(errs)} error(s)\n" +
                        "\n".join(f"  ✗ {e}" for e in errs))


STOPWORDS = {"and", "or", "not", "the", "has", "have", "for", "with", "within", "above",
             "below", "over", "under", "still", "high", "low", "zero", "all", "any", "least",
             "most", "than", "that", "this", "been", "are", "was", "were", "its", "not",
             "said", "done", "open", "same", "each", "from", "into", "out", "off"}


def slug(s):
    return re.sub(r"[^a-z0-9_]+", "_", str(s).lower()).strip("_")


class Graph:
    """Nodes are merged by id across loops. That merge IS the group."""

    def __init__(self):
        self.nodes, self.edges, self.loops = {}, [], []
        self.excluded, self.warnings = [], []
        self.considered = {}
        self.source_names = {}

    def node(self, nid, kind, **fields):
        source_name = str(nid)
        nid = slug(source_name)
        if not nid:
            raise SpecError(f"node name `{source_name}` produces an empty graph id")
        if nid in self.nodes:
            existing_source = self.source_names[nid]
            if existing_source != source_name:
                raise SpecError(
                    f"`{existing_source}` and `{source_name}` produce the same graph id "
                    f"`{nid}`; rename one so references are unambiguous"
                )
            existing = self.nodes[nid]
            if existing["kind"] != kind:
                raise SpecError(
                    f"`{source_name}` is a {existing['kind']} in one place and a {kind} in "
                    "another; one id cannot have two meanings"
                )
            else:
                # Shared names across a group are shared semantic nodes. Conflicting fields
                # mean the sources do not actually agree about that shared entity.
                for k, v in fields.items():
                    if v is None:
                        continue
                    if k in existing and existing[k] != v:
                        raise SpecError(
                            f"node `{nid}` gives `{k}` two values: {existing[k]!r} and {v!r}"
                        )
                    existing.setdefault(k, v)
            return nid
        self.source_names[nid] = source_name
        self.nodes[nid] = {"id": nid, "kind": kind,
                           **{k: v for k, v in fields.items() if v is not None}}
        return nid

    def edge(self, a, b, rel):
        e = {"from": slug(a), "to": slug(b), "rel": rel}
        if e not in self.edges:
            self.edges.append(e)

    def doc(self, name):
        d = {"loopspec_version": 2, "ir_revision": "2.1", "encodes": name, "set": "field",
             "shape": "canonical-graph", "source_format": "loop-v1.1",
             "nodes": list(self.nodes.values()), "edges": self.edges,
             "loops": self.loops, "excluded_variables": self.excluded}
        if self.considered:
            d["considered"] = self.considered
        return d


def timescale(g, period, owner):
    """Cadences are shared: two things running `daily` reference one TimeScale."""
    if not period:
        return None
    return g.node(f"every_{slug(period)}", "TimeScale", period=str(period))


def expand_one(g, spec, path="<spec>", scope=None):
    spec = normalize(spec)
    validate(spec, path, scope)
    name = spec.get("loop") or spec.get("name")
    lid = slug(name)
    loop_estimands = set()
    loop_targets = set()
    loop_policies = set()
    loop_processes = set()
    target_by_estimand = {}

    system_id = g.node(lid + "_system", "System", label=str(name).replace("_", " "),
                       role="controller")
    cadence = timescale(g, spec.get("runs"), lid)

    # --- boundary and observer: every system/environment distinction is for a purpose ----
    boundary_id = None
    boundary = spec.get("boundary") or {}
    if boundary:
        boundary_id = g.node(f"{lid}_boundary", "Boundary",
                             purpose=boundary.get("purpose"),
                             inside=boundary.get("inside") or [],
                             outside=boundary.get("outside") or [],
                             drawn_by=slug(boundary.get("drawn_by")))
        g.edge(boundary["drawn_by"], boundary_id, "frames")
        g.edge(boundary_id, system_id, "bounds")

    # --- process/environment: the represented world leg of the feedback ring ------------
    for process, body in (spec.get("processes") or {}).items():
        body = body or {}
        process_id = g.node(process, "System", role="controlled_process",
                            location=body.get("location"),
                            description=body.get("description"))
        loop_processes.add(process_id)
        for signal in body.get("observed_as") or []:
            g.edge(process_id, signal, "produces")

    # --- regulates: what the loop steers -------------------------------------------
    for est, body in (spec.get("goal") or {}).items():
        body = body or {}
        loop_estimands.add(g.node(est, "Estimand", determination="computed",
                                  computed_from=body.get("from"), unit=body.get("unit")))
        if body.get("keep"):
            tid = g.node(f"{slug(est)}_target", "DesiredCondition",
                         statement=str(body["keep"]),
                         set_by=body.get("set_by"),
                         in_loop=lid,
                         confidence_in_target=body.get("confidence"))
            loop_targets.add(tid)
            target_by_estimand[est] = tid
            g.edge(tid, est, "targets")
            if body.get("set_by"):
                _outer, _dot, outer_quantity = str(body["set_by"]).partition(".")
                g.edge(outer_quantity, tid, "sets")

    # --- beliefs: what it holds a view on but cannot read off ------------------------
    # A name appearing in BOTH `goal` and `beliefs` is a quantity you steer toward AND form
    # a view about — essay quality, answer usefulness. It is LATENT: a judgement is being
    # made. `goal` runs first and would otherwise fix it as `computed`, which silently
    # exempts it from every calibration check. That suppressed the project's headline
    # finding across a whole study before anyone noticed.
    for est, body in (spec.get("beliefs") or {}).items():
        body = body or {}
        if est in g.nodes and g.nodes[est].get("determination") == "computed":
            g.nodes[est]["determination"] = "latent"
        loop_estimands.add(g.node(est, "Estimand", determination="latent",
                                  settled_by=body.get("settled_by"),
                                  question=body.get("question"),
                                  known_bias=body.get("known_bias")))
        eid = g.node(f"{lid}_estimate_{slug(est)}", "Estimator",
                     form=body.get("how", "unspecified"),
                     idempotency_basis=body.get("safe_to_repeat",
                                                f"observations feeding {slug(est)}"))
        g.edge(eid, est, "estimates")
        for src in body.get("from") or []:
            g.edge(src, est, "measures")
        if body.get("checked_by"):
            # A review name is a human-facing label, not an identity. The same review can
            # score several beliefs with different outcomes/windows, so each contract needs
            # its own node or those meanings collapse into one conflicting scalar record.
            cid = g.node(f"{lid}_calibration_{slug(est)}", "Calibration",
                         review=str(body["checked_by"]),
                         calibration_kind="belief",
                         scores=slug(est),
                         outcome=(slug(body["checked_against"])
                                  if body.get("checked_against") else None),
                         scoring_rule=body.get("scoring_rule"),
                         window=body.get("window"),
                         adjusts=body.get("adjusts"),
                         period=body.get("every"))
            g.edge(cid, eid, "revises")
            if body.get("every"):
                review_scale = timescale(g, body["every"], cid)
                g.edge(cid, review_scale, "reviews_at")
            if body.get("checked_against"):
                g.edge(cid, body["checked_against"], "compares")
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
               origin=body.get("origin"), obtained=body.get("how"),
               source=body.get("source"),
               reported_by=body.get("reported_by"),
               produced_by=body.get("produced_by"))
        inf = body.get("informs")
        for tgt in ([inf] if isinstance(inf, str) else (inf or [])):
            g.edge(sig, tgt, "measures")
        # `origin: ourselves` is the load-bearing half of provenance: data this system
        # caused to exist cannot correct it. produced_by merely names which act did it.
        if body.get("origin") == "ourselves" or body.get("produced_by"):
            if body.get("produced_by"):
                g.edge(body["produced_by"], sig, "produces")
            else:
                g.edge(lid + "_system", sig, "produces")
        if body.get("checked_by"):
            # Attention-source review is meta-control, but it is not a prediction scoring
            # contract. Keep it distinguishable so calibration-contract checks do not ask a
            # source-retirement review for a Brier score and outcome cohort.
            cid = g.node(f"{lid}_attention_review_{slug(sig)}", "Calibration",
                         review=str(body["checked_by"]),
                         calibration_kind="attention",
                         scores=slug(sig),
                         value_metric=body.get("value_metric"),
                         window=body.get("review_window"),
                         adjusts=body.get("adjusts"),
                         period=body.get("review_every"))
            g.edge(cid, sig, "revises")
            if body.get("review_every"):
                review_scale = timescale(g, body["review_every"], cid)
                g.edge(cid, review_scale, "reviews_at")
        if body.get("every"):
            sample_scale = timescale(g, body["every"], sig)
            g.edge(sig, sample_scale, "samples_at")
        # a REPORTED number is a claim by someone, not a measurement
        if (body.get("reported_by") and
                body["reported_by"] in ((scope or spec).get("people") or {})):
            g.edge(body["reported_by"], sig, "asserts")

    # --- acts: the levers ----------------------------------------------------------
    for act, body in (spec.get("actions") or {}).items():
        body = body or {}
        # can_undo: yes|costly|no  ->  reversible|costly|irreversible
        undo = {True: "reversible", "yes": "reversible", False: "irreversible",
                "no": "irreversible", "costly": "costly"}.get(body.get("can_undo"))
        g.node(act, "Intervention",
               target=body.get("moves"),
               effect_direction=body.get("effect"),
               effect_directions=body.get("effects"),
               damping=body.get("damping"),
               reversibility=undo,
               requires_approval_from=(slug(body["needs_approval"])
                                       if body.get("needs_approval") else None))
        mv = body.get("moves")
        for tgt in ([mv] if isinstance(mv, str) else (mv or [])):
            g.edge(act, tgt, "targets")
        through = body.get("through")
        for process in ([through] if isinstance(through, str) else (through or [])):
            g.edge(act, process, "causes")
        if body.get("effect_after"):
            did = g.node(f"{slug(act)}_delay", "Delay", duration=str(body["effect_after"]),
                         damping=body.get("damping"))
            g.edge(act, did, "delays")
        if body.get("needs_approval"):
            g.edge(body["needs_approval"], act, "authorizes")
        for r in body.get("consumes") or []:
            g.node(r, "Resource")
            g.edge(act, r, "consumes")

    # --- spends: what the loop burns, and what stops it -----------------------------
    for res, body in (spec.get("spends") or {}).items():
        body = body or {}
        g.node(res, "Resource", depletable=True, limit=body.get("limit"),
               replenished=body.get("replenished"))
        sb = body.get("spent_by")
        for a in ([sb] if isinstance(sb, str) else (sb or [])):
            g.edge(a, res, "consumes")
        if body.get("replenished"):
            g.edge(lid + "_system", res, "replenishes")

    # --- when: the decision rule ---------------------------------------------------
    rules = spec.get("when") or []
    declared = (set((spec.get("goal") or {})) | set((spec.get("beliefs") or {}))
                | set((spec.get("spends") or {})))
    if rules:
        for i, r in enumerate(rules):
            inferred = "reads" not in r
            explicit_inputs = set(r.get("reads") or []) if not inferred else set()
            inferred_inputs = ({token for token in re.findall(
                r"[a-z_][a-z0-9_]{2,}", str(r.get("if", ""))
            ) if token in declared} if inferred else set())
            inputs = explicit_inputs | inferred_inputs
            undeclared = (sorted({token for token in re.findall(
                r"[a-z_][a-z0-9_]{3,}", str(r.get("if", ""))
            ) if token not in declared and token not in STOPWORDS}) or None) if inferred else None
            pid = g.node(f"{lid}_policy_{i}", "Policy",
                         rule=str(r.get("if", "always")),
                         priority=i,
                         inputs=sorted(inputs),
                         inputs_inferred=inferred,
                         inferred_rule_indexes=[i] if inferred else None,
                         reads_undeclared=undeclared,
                         escalates=(slug(r["escalate"]) if r.get("escalate") else None))
            loop_policies.add(pid)
            for item in inputs:
                g.edge(pid, item, "reads")
            for quantity in r.get("against") or []:
                g.edge(pid, target_by_estimand[quantity], "uses_reference")
            if r.get("do"):
                for a in ([r["do"]] if isinstance(r["do"], str) else r["do"]):
                    g.edge(pid, a, "authorizes")

    # --- parties: who is exposed ----------------------------------------------------
    for p, body in (spec.get("people") or {}).items():
        body = body or {}
        kind = ("human" if body.get("human") else
                "agent" if body.get("agent") else body.get("kind", "system"))
        lose = body.get("loses_if_wrong")
        lose = "; ".join(lose) if isinstance(lose, list) else lose
        consequence_status = None
        if lose and str(lose).strip().lower() in ("nothing", "none"):
            consequence_status = "none"
        elif lose:
            consequence_status = "declared"
        g.node(p, "Party", party_kind=kind, authority=body.get("may_decide"),
               consequence_status=consequence_status)
        if consequence_status == "declared":
            cid = g.node(f"{slug(p)}_consequence", "Consequence",
                         statement=str(lose),
                         asymmetry=body.get("asymmetry"))
            g.edge(p, cid, "bears")
        for e in body.get("sees") or []:
            g.edge(p, e, "holds")

    # --- never: the guardrails -------------------------------------------------------
    for i, c in enumerate(spec.get("never") or []):
        cid = g.node(f"{lid}_never_{i}", "Constraint", statement=str(c))
        g.edge(cid, lid + "_system", "constrains")

    # Exclusions delimit the model boundary. They are not automatically disturbances:
    # something can be outside scope without perturbing the regulated quantity, and an
    # important disturbance may already be explicitly modelled.
    g.excluded += [str(x) for x in (spec.get("not_modelling") or [])]

    # `consider:` rides along on the graph so the linter can pair decisions with findings.
    for key, body in (spec.get("consider") or {}).items():
        body = body if isinstance(body, dict) else {"because": str(body)}
        g.considered[str(key)] = body

    # --- the loop record itself -------------------------------------------------------
    sigs = list((spec.get("observes") or {}).keys())
    acts = list((spec.get("actions") or {}).keys())
    g.loops.append({"id": lid,
                    "timescale": cadence,
                    "signals": sorted(slug(s) for s in sigs),
                    "interventions": sorted(slug(a) for a in acts),
                    "estimands": sorted(loop_estimands),
                    "desired_conditions": sorted(loop_targets),
                    "policies": sorted(loop_policies),
                    "processes": sorted(loop_processes),
                    "boundary": boundary_id,
                    "asks_human_when": spec.get("asks_human_when") or [],
                    "escalates_to": (spec.get("asks_human") or
                                     next((r.get("escalate") for r in rules
                                           if r.get("escalate")), None))})
    return lid


def expand(path):
    with open(path) as source:
        docs = [normalize(d) for d in yaml.safe_load_all(source) if d]
    # the file is the scope: build the union of every declared name across the group first
    scope = {}
    for section in ("actions", "people", "observes", "goal", "beliefs", "spends",
                    "processes"):
        scope[section] = {k: v for d in docs for k, v in (d.get(section) or {}).items()}
    scope["_loops"] = [str(d.get("loop") or d.get("name")) for d in docs]
    scope["_loop_quantities"] = {
        str(d.get("loop") or d.get("name")): set(d.get("goal") or {}) |
        set(d.get("beliefs") or {})
        for d in docs
    }
    g = Graph()
    names = [expand_one(g, d, path, scope) for d in docs]
    name = names[0] if len(names) == 1 else os.path.basename(path).split(".")[0]
    doc = g.doc(name)
    if len(names) > 1:
        doc["group"] = names
    return doc, g.warnings


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        sys.exit(__doc__.strip().split("\n\n")[1])
    try:
        doc, warns = expand(args[0])
    except SpecError as e:
        sys.exit(f"\n{e}\n")
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    for w in dict.fromkeys(DEPRECATIONS):
        print(f"deprecated: {w}", file=sys.stderr)
    out = yaml.safe_dump(doc, sort_keys=False, width=100)
    if "--lint" in argv:
        try:
            from . import validate as semantic_validator
        except ImportError:
            import validate as semantic_validator
        report = semantic_validator.validate_document(doc, args[0])
        for warning in report.warnings:
            print(f"semantic warning: {warning}", file=sys.stderr)
        if not report.ok:
            for error in report.errors:
                print(f"semantic error: {error}", file=sys.stderr)
            return 1

        tmp = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as target:
                target.write(out)
                tmp = target.name
            command = [sys.executable, os.path.join(os.path.dirname(__file__), "derive.py"), tmp]
            if "--json" in argv:
                command.append("--json")
            return subprocess.run(command).returncode
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
