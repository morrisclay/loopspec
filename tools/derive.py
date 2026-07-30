#!/usr/bin/env python3
"""
Derive claims from a canonical URAS encoding by QUERY, not by assertion.

    python3 tools/derive.py benchmarks/encodings/canonical/*.yaml

Motivation: 11 of 11 hand-asserted `surfaced` claims were rejected under blind
adjudication — 8 restatement, 3 unsupported. The adjudicator's diagnosis was that the
encodings "mistake typed paraphrase for explanatory structure."

The test this tool exists to run: can a claim FALL OUT of the graph rather than be written
into a field? A derived claim has a property no asserted claim had — it is a computed
consequence of the encoding, so if it is true of the encoding it is true, and if the
encoding is wrong the claim is wrong for a locatable reason.

Each query returns claims only when the structural pattern actually holds. Queries that
find nothing print nothing. No query is allowed to restate a single node; every one must
combine at least two independent parts of the graph.
"""

import sys
import os
import glob
import json

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml: pip install pyyaml")


def load(path):
    d = yaml.safe_load(open(path))
    nodes = {n["id"]: n for n in (d.get("nodes") or [])}
    edges = d.get("edges") or []
    return d, nodes, edges


def rel(edges, r):
    return [(e["from"], e["to"]) for e in edges if e.get("rel") == r]


def kind(nodes, k):
    return [i for i, n in nodes.items() if n.get("kind") == k]


# ------------------------------------------------------------------ queries

def q_estimate_without_authority(d, nodes, edges):
    """Parties holding an estimate but authorising no intervention on the loop it feeds."""
    holds = {}
    for a, b in rel(edges, "holds"):
        if nodes.get(b, {}).get("kind") == "Estimate":
            holds.setdefault(a, []).append(b)
    authorises = {a for a, _ in rel(edges, "authorizes")}
    out = []
    for party, ests in holds.items():
        if party not in authorises:
            out.append({
                "pattern": "estimate_without_authority",
                "claim": (f"`{party}` holds {len(ests)} estimate(s) but authorises no "
                          f"intervention at all — its assessment can enter the system only "
                          f"through another party choosing to act on it."),
                "evidence": {"holds": ests, "authorizes": []},
            })
    return out


def q_consequence_without_authority(d, nodes, edges):
    """Parties bearing consequence with no authority — pure downside."""
    bears = {a: b for a, b in rel(edges, "bears")}
    authorises = {a for a, _ in rel(edges, "authorizes")}
    out = []
    for party, cons in bears.items():
        if party not in authorises:
            sev = nodes.get(cons, {}).get("severity")
            out.append({
                "pattern": "consequence_without_authority",
                "claim": (f"`{party}` bears a consequence of severity `{sev}` while holding no "
                          f"authority over any intervention. Its exposure is structurally "
                          f"unhedgeable: it cannot act to reduce its own risk."),
                "evidence": {"bears": cons, "severity": sev, "authorizes": []},
            })
    return out


def q_measurement_authority_inversion(d, nodes, edges):
    """The party with the richest signal is not the party authorising the key intervention."""
    measures = {b: a for a, b in rel(edges, "measures")}
    holds_est = {}
    for a, b in rel(edges, "holds"):
        if nodes.get(b, {}).get("kind") == "Estimate":
            holds_est.setdefault(a, []).append(b)
    est_by = {i: n.get("held_by") for i, n in nodes.items() if n.get("kind") == "Estimate"}
    # rank parties by signal fidelity/frequency
    rich = []
    for sig, n in nodes.items():
        if n.get("kind") != "Signal":
            continue
        if n.get("frequency") == "continuous" or n.get("fidelity") == "rich":
            rich.append(sig)
    if not rich:
        return []
    authorises = {}
    for a, b in rel(edges, "authorizes"):
        authorises.setdefault(a, []).append(b)
    out = []
    for sig in rich:
        est = measures.get(sig)
        # who holds an estimate of the estimand this rich signal measures?
        owners = [p for p, n in nodes.items()
                  if n.get("kind") == "Estimate" and n.get("held_by")
                  and est and _measures_for(nodes, edges, n.get("held_by"), est)]
        for owner in set(filter(None, (nodes[e].get("held_by") for e in nodes
                                       if nodes[e].get("kind") == "Estimate"))):
            pass
        holders = [nodes[e]["held_by"] for e in nodes
                   if nodes[e].get("kind") == "Estimate" and nodes[e].get("held_by")]
        for h in set(holders):
            acts = authorises.get(h, [])
            if not acts:
                continue
            # is any other party's authority strictly more consequential (consumes a Resource)?
            consumes = {a for a, _ in rel(edges, "consumes")}
            if not any(x in consumes for x in acts):
                other = [p for p, xs in authorises.items()
                         if p != h and any(x in consumes for x in xs)]
                if other and _holds_signal(nodes, edges, h, sig):
                    out.append({
                        "pattern": "measurement_authority_inversion",
                        "claim": (f"`{h}` is the only party fed by the continuous/rich signal "
                                  f"`{sig}`, yet the resource-consuming intervention is "
                                  f"authorised by {other} instead. The richest observation "
                                  f"channel is structurally decoupled from the decisive act."),
                        "evidence": {"rich_signal": sig, "observer": h,
                                     "decisive_authority": other},
                    })
    return out


def _measures_for(nodes, edges, party, estimand):
    return True


def _holds_signal(nodes, edges, party, sig):
    est = None
    for a, b in rel(edges, "measures"):
        if a == sig:
            est = b
    if est is None:
        return False
    for i, n in nodes.items():
        if n.get("kind") == "Estimate" and n.get("held_by") == party:
            return True
    return False


def q_shared_intervention_across_timescales(d, nodes, edges):
    """Two loops at different timescales whose interventions both touch one policy/resource."""
    loops = d.get("loops") or []
    consumes = {a: b for a, b in rel(edges, "consumes")}
    revises = {a: b for a, b in rel(edges, "revises")}
    closes = {b: a for a, b in rel(edges, "closes")}
    out = []
    for i, l1 in enumerate(loops):
        for l2 in loops[i + 1:]:
            iv1, iv2 = l1.get("intervention"), l2.get("intervention")
            t1, t2 = l1.get("timescale"), l2.get("timescale")
            if iv1 == iv2 or t1 == t2:
                continue
            # do they act on the same downstream object?
            tgt1 = consumes.get(iv1) or revises.get(iv1) or closes.get(iv1)
            tgt2 = consumes.get(iv2) or revises.get(iv2) or closes.get(iv2)
            shared = None
            if tgt1 and tgt1 == tgt2:
                shared = tgt1
            # or: one revises the policy that closes the other
            p1 = closes.get(iv1)
            if revises.get(iv2) and p1 and revises.get(iv2) == p1:
                shared = p1
            if not shared:
                continue
            owners1 = [a for a, b in rel(edges, "authorizes") if b == iv1]
            owners2 = [a for a, b in rel(edges, "authorizes") if b == iv2]
            if set(owners1) & set(owners2):
                continue
            out.append({
                "pattern": "unowned_cross_timescale_coupling",
                "claim": (f"Loop `{l1['id']}` ({nodes.get(t1,{}).get('period')}) and loop "
                          f"`{l2['id']}` ({nodes.get(t2,{}).get('period')}) both act on "
                          f"`{shared}`, and their interventions are authorised by disjoint "
                          f"parties ({owners1 or 'none'} vs {owners2 or 'none'}). No party "
                          f"holds authority over both, so the tradeoff between them is not "
                          f"anyone's decision."),
                "evidence": {"loops": [l1["id"], l2["id"]], "shared_object": shared,
                             "authorities": [owners1, owners2]},
            })
    return out


def q_estimand_without_estimator(d, nodes, edges):
    """Estimands that are held as estimates but with no declared estimator."""
    estimated = {b for _, b in rel(edges, "estimates")}
    out = []
    for est in kind(nodes, "Estimate"):
        if est not in estimated:
            holder = nodes[est].get("held_by")
            out.append({
                "pattern": "estimate_without_estimator",
                "claim": (f"`{holder}` holds estimate `{est}` with no declared estimator: the "
                          f"encoding records the belief but not the process producing it, so "
                          f"nothing constrains how it updates or whether it is idempotent."),
                "evidence": {"estimate": est, "holder": holder},
            })
    return out


def q_unmeasured_estimand(d, nodes, edges):
    """Estimands with no signal measuring them."""
    measured = {b for _, b in rel(edges, "measures")}
    out = []
    for e in kind(nodes, "Estimand"):
        if e not in measured:
            out.append({
                "pattern": "unmeasured_estimand",
                "claim": (f"Estimand `{e}` has no signal measuring it. Any estimate of it is "
                          f"formed from something the encoding does not record."),
                "evidence": {"estimand": e},
            })
    return out


def q_delay_without_feedback_owner(d, nodes, edges):
    """A delayed intervention whose consequence lands on a party who did not authorise it."""
    delays = {b for _, b in rel(edges, "delays")}
    auth = {}
    for a, b in rel(edges, "authorizes"):
        auth.setdefault(b, []).append(a)
    out = []
    for iv in delays:
        owners = auth.get(iv, [])
        for p in kind(nodes, "Party"):
            if p in owners:
                continue
            cons = [b for a, b in rel(edges, "bears") if a == p]
            for c in cons:
                if nodes.get(c, {}).get("measured") is False:
                    out.append({
                        "pattern": "delayed_harm_to_unauthorised_party",
                        "claim": (f"Intervention `{iv}` is delayed and authorised by {owners}, "
                                  f"while `{p}` bears consequence `{c}` which is unmeasured. "
                                  f"The lag falls on a party with neither authority over the "
                                  f"act nor a measured record of the harm."),
                        "evidence": {"intervention": iv, "authorised_by": owners,
                                     "exposed_party": p, "consequence": c},
                    })
    return out


QUERIES = [
    q_consequence_without_authority,
    q_estimate_without_authority,
    q_shared_intervention_across_timescales,
    q_estimand_without_estimator,
    q_unmeasured_estimand,
    q_delay_without_feedback_owner,
]


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not paths:
        paths = sorted(glob.glob(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "benchmarks", "encodings", "canonical", "*.yaml")))
    as_json = "--json" in sys.argv
    allout = {}
    for p in paths:
        d, nodes, edges = load(p)
        claims = []
        for q in QUERIES:
            try:
                claims.extend(q(d, nodes, edges))
            except Exception as e:
                print(f"  query {q.__name__} failed: {e}", file=sys.stderr)
        allout[d.get("encodes")] = claims
        if not as_json:
            print("=" * 72)
            print(f"{d.get('encodes')} — {len(claims)} derived claim(s)")
            print("=" * 72)
            for c in claims:
                print(f"\n[{c['pattern']}]")
                print(f"  {c['claim']}")
    if as_json:
        print(json.dumps(allout, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
