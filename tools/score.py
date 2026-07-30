#!/usr/bin/env python3
"""
URAS score — the self-optimization function defined in ontology/score.md

    python3 tools/score.py            # score + coverage report
    python3 tools/score.py --check    # exit nonzero on any hard violation (CI use)
    python3 tools/score.py --json     # machine-readable

Design rules enforced here, not just documented:

  * Terms combine by GEOMETRIC MEAN, never a weighted sum. Any term near zero
    collapses the total, which is what stops a single term being gamed.
  * Unavailable terms are EXCLUDED and reported, never defaulted to 1.0.
    Defaulting would let the score rise as data goes missing.
  * Binary gates multiply. They are not tradeable against anything.
"""

import sys
import json
import math
import glob
import os

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml: pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = []

VALID_TIERS = {"core", "provisional", "extension"}
MIN_BENCHMARKS_PER_PRIMITIVE = 3
MIN_DOMAINS_PER_PRIMITIVE = 2
SET_WEIGHTS = {"seed": 0.7, "adversarial": 1.0, "held_out": 1.5}


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------- loading

def load_primitives():
    path = os.path.join(ROOT, "ontology", "primitives.yaml")
    if not os.path.exists(path):
        return None, ["ontology/primitives.yaml not found"]
    with open(path) as f:
        doc = yaml.safe_load(f)

    errors = []
    prims = doc.get("primitives") or []
    seen = set()
    for p in prims:
        name = p.get("name")
        if not name:
            errors.append("primitive with no name")
            continue
        if name in seen:
            errors.append(f"duplicate primitive: {name}")
        seen.add(name)
        if p.get("tier") not in VALID_TIERS:
            errors.append(f"{name}: tier must be one of {sorted(VALID_TIERS)}")
        if not isinstance(p.get("depth"), int):
            errors.append(f"{name}: depth must be an integer")
        if not p.get("definition"):
            errors.append(f"{name}: no definition")
        if not p.get("demanded_by"):
            errors.append(f"{name}: no demanded_by — every primitive must trace to a benchmark")
    return doc, errors


def load_encodings():
    """Formal encodings (.yaml). Seed prose (.md) is source material, not an encoding."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "benchmarks", "**", "*.yaml"), recursive=True)):
        with open(path) as f:
            try:
                doc = yaml.safe_load(f)
            except yaml.YAMLError as e:
                out.append({"path": path, "error": str(e)})
                continue
        if isinstance(doc, dict):
            doc["_path"] = path
            out.append(doc)
    return out


def load_seed_sources():
    """Prose seed descriptions, for their front matter (domain, axes, breaks)."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "benchmarks", "**", "*.md"), recursive=True)):
        with open(path) as f:
            text = f.read()
        if not text.startswith("---"):
            continue
        _, fm, body = text.split("---", 2)
        try:
            meta = yaml.safe_load(fm) or {}
        except yaml.YAMLError:
            continue
        meta["_path"] = path
        meta["_body_tokens"] = len(body.split())
        out.append(meta)
    return out


# ---------------------------------------------------------------- terms

def term_simplicity(doc, encodings):
    prims = doc.get("primitives") or []
    core = [p for p in prims if p.get("tier") == "core"]
    n = len(core)
    budget = doc.get("budget", 20)

    budget_term = clamp((budget + 4 - n) / 8.0)
    depths = [p.get("depth", 0) for p in core] or [0]
    depth_term = clamp((5 - (sum(depths) / len(depths))) / 3.0)

    usage = primitive_usage(core, encodings, SOURCES)
    undeclared = usage.pop("_undeclared", [])
    orphans = [name for name, u in usage.items()
               if u["benchmarks"] < MIN_BENCHMARKS_PER_PRIMITIVE
               or u["domains"] < MIN_DOMAINS_PER_PRIMITIVE]
    orphan_term = 1.0 - (len(orphans) / n) if n else 0.0

    detail = {
        "core_count": n,
        "budget": budget,
        "over_budget": n > budget,
        "mean_depth": round(sum(depths) / len(depths), 2),
        "orphans": orphans,
        "orphan_count": len(orphans),
        "usage": {k: f"{v['benchmarks']}b/{v['domains']}d" for k, v in sorted(
            usage.items(), key=lambda kv: kv[1]["benchmarks"])},
        "undeclared_primitives": undeclared,
        "components": {
            "budget_term": round(budget_term, 3),
            "depth_term": round(depth_term, 3),
            "orphan_term": round(orphan_term, 3),
        },
    }
    value = 0.5 * budget_term + 0.3 * depth_term + 0.2 * orphan_term
    return value, detail


def primitive_usage(core, encodings, sources=()):
    """
    How many benchmarks and distinct domains demand each core primitive.

    Counts BOTH prose benchmark descriptions (which declare `demands:`) and formal
    encodings (which declare `uses:`). Coverage is declared benchmark-side on purpose:
    the earlier design kept `demanded_by` on each primitive, which meant the orphan
    metric measured the maintainer's diligence in updating that field rather than real
    coverage. The benchmark author is the one who knows what their system needs.
    """
    usage = {p["name"]: {"benchmarks": 0, "domains": 0, "_domains": set()} for p in core}

    def record(doc, key):
        domain = doc.get("domain", "unknown")
        used = set(doc.get(key) or [])
        for name in usage:
            if name in used:
                usage[name]["benchmarks"] += 1
                usage[name]["_domains"].add(domain)
        return used

    unknown = set()
    for src in sources:
        if src.get("set") == "negative":
            continue  # the negative control must NOT contribute coverage
        unknown |= record(src, "demands") - set(usage)
    for enc in encodings:
        if "error" in enc:
            continue
        unknown |= record(enc, "uses") - set(usage)

    for name in usage:
        usage[name]["domains"] = len(usage[name]["_domains"])
        del usage[name]["_domains"]
    if unknown:
        usage["_undeclared"] = sorted(unknown)
    return usage


def term_expressivity(encodings, adj=None):
    """
    Uses ADJUDICATED handled counts where available, self-assessed otherwise.

    Self-assessment rewards optimism: in round 1 an encoder claimed 5/5 breaks handled
    including one that an independent adjudicator judged `named_only` — an encoding that
    lists something under an "excluded" key has named it, not handled it.
    """
    if not encodings:
        return None, {"reason": "no formal encodings yet"}
    num = den = 0.0
    per = []
    for enc in encodings:
        if "error" in enc:
            continue
        declared = enc.get("breaks_declared")
        handled = enc.get("breaks_handled")
        if declared is None or handled is None or not declared:
            continue
        key = (enc.get("encodes"), enc.get("encoded_by"))
        rec = (adj or {}).get("by_encoding", {}).get(key)
        if rec and rec["breaks_total"]:
            n_handled, source = rec["handled"], "adjudicated"
        else:
            n_handled, source = len(handled), "self-assessed"
        w = SET_WEIGHTS.get(enc.get("set", "adversarial"), 1.0)
        num += w * (n_handled / len(declared))
        den += w
        per.append({"path": os.path.basename(enc["_path"]), "handled": n_handled,
                    "declared": len(declared), "source": source})
    if den == 0:
        return None, {"reason": "encodings do not declare breaks_declared/breaks_handled"}
    unadj = [p for p in per if p["source"] == "self-assessed"]
    return num / den, {"per_encoding": per,
                       "unadjudicated": len(unadj),
                       "caveat": ("%d encoding(s) still self-assessed — optimism inflates E"
                                  % len(unadj)) if unadj else None}


def term_determinacy(encodings):
    """Needs >=2 independent encodings of the same source by different encoders."""
    groups = {}
    for enc in encodings:
        if "error" in enc:
            continue
        key = enc.get("encodes")
        if key:
            groups.setdefault(key, []).append(enc)
    pairs = [(k, v) for k, v in groups.items() if len(v) >= 2]
    if not pairs:
        return None, {"reason": "no source encoded independently more than once"}

    from itertools import combinations
    scores, detail, vendors = [], [], set()
    for key, encs in pairs:
        for a, b in combinations(encs, 2):
            if a.get("encoded_by") == b.get("encoded_by"):
                continue  # same encoder is not an independent sample
            ja = jaccard(set(a.get("uses") or []), set(b.get("uses") or []))
            je = jaccard(set(a.get("estimands") or []), set(b.get("estimands") or []))
            la, lb = len(a.get("loops") or []), len(b.get("loops") or [])
            jl = 1.0 if la == lb == 0 else (min(la, lb) / max(la, lb) if max(la, lb) else 0.0)
            s = 0.5 * ja + 0.3 * je + 0.2 * jl
            scores.append(s)
            vendors |= {vendor_of(a.get("encoded_by")), vendor_of(b.get("encoded_by"))}
            detail.append({
                "encodes": key, "pair": f"{a.get('encoded_by')} vs {b.get('encoded_by')}",
                "score": round(s, 3), "primitive_jaccard": round(ja, 3),
                "estimand_jaccard": round(je, 3), "loop_agreement": round(jl, 3),
                "uses_only_a": sorted(set(a.get("uses") or []) - set(b.get("uses") or [])),
                "uses_only_b": sorted(set(b.get("uses") or []) - set(a.get("uses") or [])),
            })
    if not scores:
        return None, {"reason": "duplicate encodings exist but share an encoder", "detail": detail}
    # Is D inflated by including the author of the ontology? Measure rather than assume.
    AUTHOR = "claude-opus-5"
    auth = [d["score"] for d in detail if "score" in d and AUTHOR in d.get("pair", "")]
    indep = [d["score"] for d in detail if "score" in d and AUTHOR not in d.get("pair", "")]
    d_indep = (sum(indep) / len(indep)) if indep else None
    d_auth = (sum(auth) / len(auth)) if auth else None

    caveat = None
    if len(vendors) < 2:
        caveat = (f"ALL encoders are from one vendor family ({sorted(vendors)}). Shared training "
                  "bias inflates agreement, so this D is optimistic. A genuinely different "
                  "family is needed for a trustworthy figure.")
    return sum(scores) / len(scores), {
        "pairs": detail, "vendors": sorted(vendors), "caveat": caveat,
        "D_author_pairs": rnd(d_auth), "D_independent_pairs": rnd(d_indep),
        "n_author": len(auth), "n_independent": len(indep),
        "author_effect": rnd((d_auth - d_indep)) if (d_auth is not None and d_indep is not None) else None,
    }


def vendor_of(model):
    m = (model or "").lower()
    for prefix, vendor in (("gpt", "openai"), ("o1", "openai"), ("o3", "openai"),
                           ("o4", "openai"), ("codex", "openai"), ("claude", "anthropic"),
                           ("gemini", "google"), ("grok", "xai"), ("deepseek", "deepseek"),
                           ("qwen", "alibaba"), ("llama", "meta"), ("mistral", "mistral"),
                           ("kimi", "moonshot"), ("moonshot", "moonshot"),
                           ("glm", "zhipu")):
        if prefix in m:
            return vendor
    return "unknown"


def jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def load_adjudications():
    """
    Independent verdicts on surfaced claims and breaks_handled claims.

    Both were self-assessed in round 1 and both were therefore untrustworthy: `U` rewarded
    an encoder for asserting insight, and `E` rewarded an encoder for asserting coverage.
    Adjudication is done blind by a model that wrote neither the encodings, the ontology,
    nor the prose, on anonymised claims.
    """
    out = {"surfaced": {}, "breaks": {}, "by_encoding": {}}
    # Prefer the highest-numbered round: later rounds cover strictly more claims.
    rounds = sorted(glob.glob(os.path.join(ROOT, "adjudication", "round*_verdicts.yaml")))
    if not rounds:
        return None
    latest = rounds[-1]
    n = os.path.basename(latest).split("_")[0]        # e.g. "round2"
    out["round"] = n
    vpath = latest
    lpath = os.path.join(ROOT, "adjudication", f"{n}_label_map.json")
    spath = os.path.join(ROOT, "adjudication", f"{n}_surfaced_cases.yaml")
    bpath = os.path.join(ROOT, "adjudication", f"{n}_breaks_cases.yaml")
    if not all(os.path.exists(p) for p in (vpath, lpath, spath, bpath)):
        return None
    v = yaml.safe_load(open(vpath))
    lab = json.load(open(lpath))
    scases = {c["id"]: c for c in yaml.safe_load(open(spath))["surfaced_cases"]}
    bcases = {c["id"]: c for c in yaml.safe_load(open(bpath))["breaks_cases"]}

    def owner(label):
        e = lab.get(label) or {}
        return (e.get("system"), e.get("encoded_by"))

    for r in v.get("surfaced") or []:
        c = scases.get(r["id"])
        if not c:
            continue
        key = owner(c["encoding"])
        rec = out["by_encoding"].setdefault(key, {"genuine": 0, "surfaced_total": 0,
                                                  "handled": 0, "breaks_total": 0})
        rec["surfaced_total"] += 1
        if r.get("verdict") == "genuine":
            rec["genuine"] += 1
        out["surfaced"][r["id"]] = r.get("verdict")
    for r in v.get("breaks") or []:
        c = bcases.get(r["id"])
        if not c:
            continue
        key = owner(c["encoding"])
        rec = out["by_encoding"].setdefault(key, {"genuine": 0, "surfaced_total": 0,
                                                  "handled": 0, "breaks_total": 0})
        rec["breaks_total"] += 1
        if r.get("verdict") == "handled":
            rec["handled"] += 1
        out["breaks"][r["id"]] = r.get("verdict")
    out["summary"] = v.get("summary") or {}
    return out


def term_usefulness(encodings, adj=None):
    """
    U = clamp(mean genuine claims per encoding / 2) * audit_coverage

    MULTIPLICATIVE, not additive. The original formula added an audit-fraction term, which
    meant that submitting claims for audit raised the score even when every claim was
    rejected — the term rewarded being audited rather than passing. That flaw was invisible
    until real verdicts existed. Unaudited claims now contribute nothing at all: usefulness
    cannot be self-asserted.
    """
    if not encodings:
        return None, {"reason": "no formal encodings yet"}
    per, total, audited, genuine = [], 0, 0, 0
    for enc in encodings:
        if "error" in enc:
            continue
        surfaced = enc.get("surfaced") or []
        total += len(surfaced)
        key = (enc.get("encodes"), enc.get("encoded_by"))
        rec = (adj or {}).get("by_encoding", {}).get(key)
        if rec and rec["surfaced_total"]:
            audited += rec["surfaced_total"]
            genuine += rec["genuine"]
            per.append(rec["genuine"])
        else:
            per.append(0)          # unaudited claims count as zero genuine
    if not per:
        return None, {"reason": "no encoding declares surfaced:"}
    coverage = (audited / total) if total else 0.0
    mean_genuine = sum(per) / len(per)
    value = clamp(mean_genuine / 2.0) * coverage
    return value, {
        "mean_genuine_per_encoding": round(mean_genuine, 2),
        "genuine": genuine, "claims_total": total, "claims_audited": audited,
        "audit_coverage": round(coverage, 3),
        "note": ("multiplicative: unaudited claims contribute nothing, and a rejected claim "
                 "contributes nothing. U=0 means no encoding has been shown to surface "
                 "anything a practitioner did not already have."),
    }


def term_comprehensibility(encodings, sources, doc):
    if not encodings:
        return None, {"reason": "no formal encodings yet"}
    src_tokens = {s.get("_path", "").split("/")[-1].replace(".md", ""): s.get("_body_tokens", 0)
                  for s in sources}
    known = {p["name"] for p in (doc.get("primitives") or [])}
    known |= {f["name"] for f in (doc.get("fields") or [])}

    comp, undef, flat = [], [], []
    for enc in encodings:
        if "error" in enc:
            continue
        name = enc.get("encodes")
        st = src_tokens.get(name)
        et = enc.get("_tokens") or count_tokens(enc)
        if st:
            comp.append(clamp(1.0 - (et / st)))
        used = set(enc.get("uses") or [])
        if used:
            undef.append(1.0 - len(used - known) / len(used))
        flat.append(clamp((6 - depth_of(enc)) / 4.0))

    if not comp and not undef:
        return None, {"reason": "insufficient data"}
    c = avg(comp) if comp else None
    u = avg(undef) if undef else None
    f = avg(flat) if flat else None
    parts = [(0.4, c), (0.3, u), (0.3, f)]
    wsum = sum(w for w, v in parts if v is not None)
    value = sum(w * v for w, v in parts if v is not None) / wsum if wsum else None
    return value, {"compression": rnd(c), "undefined_terms": rnd(u), "flatness": rnd(f)}


def count_tokens(obj):
    return len(json.dumps(obj, default=str).split())


def depth_of(obj, d=0):
    if isinstance(obj, dict):
        return max([depth_of(v, d + 1) for k, v in obj.items()
                    if not str(k).startswith("_")] or [d])
    if isinstance(obj, list):
        return max([depth_of(v, d + 1) for v in obj] or [d])
    return d


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def rnd(x):
    return round(x, 3) if x is not None else None


# ---------------------------------------------------------------- gates

def gate_negative_control():
    path = os.path.join(ROOT, "benchmarks", "negative")
    if not os.path.isdir(path):
        return None, "benchmarks/negative/ missing — anti-vacuity gate cannot be evaluated"
    files = [f for f in os.listdir(path) if not f.startswith(".")]
    if not files:
        return None, "benchmarks/negative/ empty"
    for f in files:
        if f.endswith(".yaml"):
            return 0, f"FAIL: {f} is a formal encoding — the negative control must NOT encode"
    return 1, f"pass: {len(files)} negative control(s) recorded as unencodable"


def gate_reduction(encodings):
    for enc in encodings:
        if enc.get("encodes") == "thermostat":
            r = enc.get("reduces_to")
            if r:
                return 1, f"pass: thermostat reduces to {r}"
            return 0, "FAIL: thermostat encoding declares no reduces_to"
    return None, "no thermostat encoding yet — reduction floor untested"


# ---------------------------------------------------------------- main

def main():
    as_json = "--json" in sys.argv
    check = "--check" in sys.argv

    doc, errors = load_primitives()
    if doc is None:
        print("\n".join(errors))
        return 2

    encodings = load_encodings()
    sources = load_seed_sources()
    global SOURCES
    SOURCES = sources

    adj = load_adjudications()
    S, s_d = term_simplicity(doc, encodings)
    E, e_d = term_expressivity(encodings, adj)
    D, d_d = term_determinacy(encodings)
    U, u_d = term_usefulness(encodings, adj)
    C, c_d = term_comprehensibility(encodings, sources, doc)

    terms = {"S_simplicity": (S, s_d), "E_expressivity": (E, e_d),
             "D_determinacy": (D, d_d), "U_usefulness": (U, u_d),
             "C_comprehensibility": (C, c_d)}

    available = {k: v for k, (v, _) in terms.items() if v is not None}
    g_neg, g_neg_msg = gate_negative_control()
    g_red, g_red_msg = gate_reduction(encodings)

    if available:
        product = math.prod(available.values())
        geo = product ** (1.0 / len(available))
    else:
        geo = None

    gates_known = [g for g in (g_neg, g_red) if g is not None]
    gate_mult = math.prod(gates_known) if gates_known else None
    score = (geo * gate_mult) if (geo is not None and gate_mult is not None) else None
    partial = len(available) < 5 or g_neg is None or g_red is None

    hard = list(errors)
    if s_d["over_budget"]:
        hard.append(f"PRIMITIVE BUDGET EXCEEDED: {s_d['core_count']} core > {s_d['budget']}")
    if g_neg == 0:
        hard.append(g_neg_msg)
    if g_red == 0:
        hard.append(g_red_msg)
    for enc in encodings:
        if "error" in enc:
            hard.append(f"unparseable: {enc['path']}: {enc['error']}")

    if as_json:
        print(json.dumps({
            "score": rnd(score), "partial": partial,
            "terms": {k: rnd(v) for k, (v, _) in terms.items()},
            "unavailable": [k for k, (v, _) in terms.items() if v is None],
            "detail": {k: d for k, (_, d) in terms.items()},
            "gates": {"negative_control": g_neg, "reduction": g_red},
            "violations": hard,
        }, indent=2))
        return 1 if (check and hard) else 0

    print("=" * 68)
    print("URAS SCORE")
    print("=" * 68)
    for k, (v, d) in terms.items():
        if v is None:
            print(f"  {k:24s}    n/a   ({d.get('reason', '')})")
        else:
            print(f"  {k:24s}  {v:.3f}")
    print("-" * 68)
    print(f"  gate negative_control     {g_neg if g_neg is not None else 'n/a':<6} {g_neg_msg}")
    print(f"  gate reduction            {g_red if g_red is not None else 'n/a':<6} {g_red_msg}")
    print("-" * 68)
    if score is None:
        print(f"  SCORE                     n/a   (only {len(available)}/5 terms computable)")
    else:
        print(f"  SCORE                     {score:.3f}" + ("   PARTIAL" if partial else ""))
        # A zero term correctly collapses the geometric mean, but that destroys gradient.
        # Report the sub-score too so progress on the other terms stays visible. This is a
        # DIAGNOSTIC, never the headline: it is the score with a failing term deleted.
        zeros = [k for k, v in available.items() if v is not None and v < 1e-9]
        if zeros and gate_mult:
            rest = {k: v for k, v in available.items() if k not in zeros}
            if rest:
                sub = (math.prod(rest.values())) ** (1.0 / len(rest))
                print(f"  sub-score (excl. {', '.join(z.split('_')[0] for z in zeros)})"
                      f"{'':<4} {sub:.3f}   DIAGNOSTIC ONLY — this is the score with a")
                print(f"  {'':<26}failing term removed, not an achievement")
        dominant = min(available.items(), key=lambda kv: kv[1])
        print(f"  binding term              {dominant[0]} = {dominant[1]:.3f}")
    if partial:
        print(f"\n  PARTIAL ({len(available)}/5 terms). Unavailable terms are EXCLUDED, not")
        print("  defaulted to 1.0. Do not compare a partial score against a full one.")
    print()
    print(f"  core primitives   {s_d['core_count']} / {s_d['budget']}")
    print(f"  mean depth        {s_d['mean_depth']}")
    print(f"  orphans           {s_d['orphan_count']}" +
          (f"  {s_d['orphans']}" if s_d["orphans"] else ""))
    if s_d.get("undeclared_primitives"):
        print(f"  UNDECLARED        {s_d['undeclared_primitives']}  <- demanded but not in catalog")
    print("\n  coverage (benchmarks/domains per primitive, thinnest first)")
    for k, v in list(s_d["usage"].items()):
        flag = "  ORPHAN" if k in s_d["orphans"] else ""
        print(f"    {k:22s} {v}{flag}")
    print(f"  encodings         {len([e for e in encodings if 'error' not in e])}")
    print(f"  seed sources      {len(sources)}")
    if hard:
        print("\n  VIOLATIONS")
        for h in hard:
            print(f"    - {h}")
    print()
    return 1 if (check and hard) else 0


if __name__ == "__main__":
    sys.exit(main())
