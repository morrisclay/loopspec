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



# ---------------------------------------------------------------------------------------
# PRESENTING FINDINGS.
#
# A flat list ranked by nothing was the output for most of this project's life, and measuring
# it was uncomfortable: `regulator_without_model` fires on 21 of 21 specs. That is ZERO BITS.
# It says nothing whatever about YOUR loop, and it was printed first, every time, in the same
# typeface as a finding that fires on one spec in twenty.
#
# Both things are true and they are different uses. "100% of loops lack calibration" is the
# strongest claim this project has ABOUT THE FIELD. It is useless AS A LINT on your loop.
# So universal findings become context, rare findings lead, and duplicates collapse.
# ---------------------------------------------------------------------------------------

import math

_RATES = None


def base_rates():
    global _RATES
    if _RATES is None:
        try:
            p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "docs", "base_rates.json")
            d = json.load(open(p))
            _RATES = {k: v / d["n"] for k, v in d["fires"].items()}
        except Exception:
            _RATES = {}
    return _RATES


def surprisal(pattern):
    """Bits. A check firing on everything carries none."""
    r = base_rates().get(pattern)
    return 99.0 if r is None else -math.log2(max(r, 1e-9))


def _subject(c):
    e = c.get("evidence") or {}
    for k in ("belief", "signal", "intervention", "action", "estimand", "target", "resource",
              "loop", "policy", "party"):
        if e.get(k):
            return str(e[k])
    return None


def organise(d, claims):
    """Split into: decided-about, specific-to-you, common, and universal-so-not-a-finding."""
    considered = d.get("considered") or {}
    out = {"considered": [], "specific": [], "common": [], "universal": [], "stale": []}
    matched = set()

    for c in claims:
        p = c["pattern"]
        subj = _subject(c)
        key = next((k for k in (f"{p}/{subj}", p) if k in considered), None)
        if key:
            matched.add(key)
            body = considered[key]
            out["considered"].append((c, body.get("because", ""), body.get("revisit")))
            continue
        bits = surprisal(p)
        bucket = "universal" if bits < 0.35 else ("specific" if bits >= 2.0 else "common")
        out[bucket].append(c)

    out["stale"] = [k for k in considered if k not in matched]
    for k in ("specific", "common"):
        out[k].sort(key=lambda c: -surprisal(c["pattern"]))
    return out


def group(claims):
    """Collapse repeats: three unscored beliefs is one finding about three beliefs."""
    by = {}
    for c in claims:
        by.setdefault(c["pattern"], []).append(c)
    return by


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
                "claim": (f"`{party}` bears consequence `{cons}` (severity `{sev}`) and the "
                          f"encoding records no `authorizes` edge from it to any intervention."),
                "evidence": {"bears": cons, "severity": sev, "authorizes": []},
                "does_not_claim": ("that no risk-reducing act exists — only that none is "
                                   "encoded. Adjudication rejected the stronger form."),
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
            # Adjudication rejected treating `closes` and `revises` as the same kind of
            # contact with a shared object: they are unlike roles, and a missing authorizer
            # does not establish an unowned tradeoff. Require the SAME relation type.
            if not shared:
                continue
            same_rel = ((iv1 in consumes and iv2 in consumes) or
                        (iv1 in revises and iv2 in revises))
            if not same_rel:
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
    """
    A delayed intervention whose consequence lands on a party who did not authorise it.

    WITHDRAWN as a claim-generating query. Adjudication rejected all three of its outputs as
    `unsupported`, correctly: it inferred that a delay "falls on" a party purely because that
    party bears an unmeasured consequence, with NO edge relating the intervention or its delay
    to that consequence. Co-occurrence in the graph is not a relation in the graph.

    Retained as a QUESTION generator rather than deleted, because the pattern is worth
    flagging for a human — it just is not an established claim.
    """
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
            for c in [b for a, b in rel(edges, "bears") if a == p]:
                if nodes.get(c, {}).get("measured") is False:
                    out.append({
                        "pattern": "open_question_delay_exposure",
                        "is_question": True,
                        "claim": (f"QUESTION, not a claim: `{iv}` is delayed and authorised by "
                                  f"{owners}; `{p}` bears unmeasured consequence `{c}`. The "
                                  f"encoding does not relate them. Should there be an edge?"),
                        "evidence": {"intervention": iv, "authorised_by": owners,
                                     "party": p, "consequence": c,
                                     "missing_relation": f"{iv} -> {c}"},
                    })
    return out


def q_invariant_on_unmeasured(d, nodes, edges):
    """
    A Constraint whose rule names an estimand nothing observes.

    Same defect as policy_on_unmeasured_inputs, in a different construct: an invariant that
    cannot be checked because the quantity it constrains is never collected. In a textual
    surface the invariant and the observe statements sit lines apart and the gap is invisible.
    """
    measured = {b for _, b in rel(edges, "measures")}
    estimands = {i for i, n in nodes.items() if n.get("kind") == "Estimand"}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Constraint":
            continue
        rule = str(n.get("rule") or "")
        named = [e for e in estimands if e in rule and e not in measured]
        if named:
            out.append({
                "pattern": "invariant_on_unmeasured",
                "claim": (f"Constraint `{i}` states `{rule}`, which names estimand(s) {named} "
                          f"that no signal measures. The invariant cannot be checked — nothing "
                          f"in the system would detect its violation."),
                "evidence": {"constraint": i, "rule": rule, "unmeasured": named},
            })
    return out


def q_hinge_without_sensor(d, nodes, edges):
    """
    Existential hinges with nothing observing them.

    The startup seed argued that a representation earns its keep by "naming which
    assumptions the strategy rests on, and whether anyone is tracking them". This is that,
    computed: an Estimand marked criticality: existential, with no Signal measuring it.
    """
    measured = {b for _, b in rel(edges, "measures")}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Estimand":
            continue
        crit = (n.get("criticality") or "").lower()
        if crit != "existential":
            continue
        if i not in measured:
            out.append({
                "pattern": "hinge_without_sensor",
                "claim": (f"`{i}` is marked existential — the venture's viability turns on it — "
                          f"and NO signal in the encoding observes it. Its declared resolution "
                          f"condition is \"{n.get('resolution_condition')}\", and nothing is "
                          f"currently positioned to produce that observation."),
                "evidence": {"estimand": i, "criticality": crit,
                             "resolution_condition": n.get("resolution_condition"),
                             "measuring_signals": []},
            })
    return out


def q_hinge_without_resolution(d, nodes, edges):
    """Existential hinges with no declared resolution condition — an untestable bet."""
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Estimand":
            continue
        if (n.get("criticality") or "").lower() != "existential":
            continue
        if not n.get("resolution_condition"):
            out.append({
                "pattern": "hinge_without_resolution",
                "claim": (f"`{i}` is marked existential but declares no resolution condition. "
                          f"Nothing has been written down that would settle it, so no evidence "
                          f"can be recognised as settling it when it arrives."),
                "evidence": {"estimand": i},
            })
    return out


def q_uncalibrated_estimator(d, nodes, edges):
    """Estimators feeding an existential hinge with no Calibration closing on them."""
    calibrated = {b for a, b in rel(edges, "revises")
                  if nodes.get(a, {}).get("kind") == "Calibration"}
    hinge_ests = {i for i, n in nodes.items()
                  if n.get("kind") == "Estimand"
                  and (n.get("criticality") or "").lower() == "existential"}
    if not hinge_ests:
        return []
    # An estimator over a COMPUTED estimand needs no calibration: arithmetic makes no
    # prediction, so there is nothing to score. Skipping these is the computed/latent
    # distinction doing real work — without it this query fires on every division.
    computed = {i for i, n in nodes.items()
                if n.get("kind") == "Estimand" and n.get("determination") == "computed"}
    est_targets = {}
    for a, b in rel(edges, "estimates"):
        est_targets.setdefault(a, set()).add(b)
    measures_to = {}
    for a, b in rel(edges, "measures"):
        measures_to.setdefault(a, set()).add(b)

    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Estimator" or i in calibrated:
            continue
        if n.get("form") == "expression":
            continue
        produced = est_targets.get(i, set())
        if produced and all(
                any(t in computed for t in measures_to.get(p, {p})) or p in computed
                for p in produced):
            continue
        out.append({
            "pattern": "uncalibrated_estimator",
            "claim": (f"Estimator `{i}` has no Calibration closing on it, while the encoding "
                      f"contains {len(hinge_ests)} existential hinge(s). Nothing scores its "
                      f"past predictions against outcomes, so its trust level is unearned."),
            "evidence": {"estimator": i, "hinges": sorted(hinge_ests)},
        })
    return out


def q_policy_on_unmeasured_inputs(d, nodes, edges):
    """
    A Policy whose decision inputs include estimands nothing observes.

    Found by encoding a real venture example: the decision rule read three quantities and
    only one of them had a sensor. The policy is specified against inputs the system does
    not collect, so it cannot actually run as written — and nothing in a prose description
    makes that visible, because the policy and the sensor list live in different paragraphs.
    """
    measured = {b for _, b in rel(edges, "measures")}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Policy":
            continue
        inputs = n.get("based_on") or []
        blind = [x for x in inputs
                 if nodes.get(x, {}).get("kind") == "Estimand" and x not in measured]
        if blind and len(blind) < len(inputs):
            out.append({
                "pattern": "policy_on_unmeasured_inputs",
                "claim": (f"Policy `{i}` selects interventions using {len(inputs)} inputs "
                          f"{inputs}, but {len(blind)} of them {blind} have no signal "
                          f"measuring them. The decision rule cannot run as specified — it "
                          f"reads quantities the system does not collect."),
                "evidence": {"policy": i, "inputs": inputs, "unmeasured": blind,
                             "measured": [x for x in inputs if x in measured]},
            })
        elif blind and len(blind) == len(inputs):
            out.append({
                "pattern": "policy_entirely_blind",
                "claim": (f"Policy `{i}` selects interventions using inputs {inputs}, and NONE "
                          f"of them is measured by any signal. The decision rule is entirely "
                          f"disconnected from observation."),
                "evidence": {"policy": i, "inputs": inputs},
            })
    return out


def q_estimand_never_estimated(d, nodes, edges):
    """An estimand declared as state but with nothing estimating it."""
    est_targets = {b for _, b in rel(edges, "estimates")}
    holders = {}
    for i, n in nodes.items():
        if n.get("kind") == "Estimate":
            holders[i] = n
    # estimands covered by some Estimate (directly or via `about`)
    covered = set()
    for a, b in rel(edges, "estimates") + rel(edges, "explains"):
        covered.add(b)
    for i, n in nodes.items():
        if n.get("kind") == "Estimate":
            for a, b in edges_from(edges, i):
                covered.add(b)
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Estimand" or n.get("determination") == "computed":
            continue
        if i in covered:
            continue
        out.append({
            "pattern": "estimand_never_estimated",
            "claim": (f"`{i}` is declared as estimated state, but nothing in the loop produces "
                      f"an estimate of it — no estimator, no belief. It is named as something "
                      f"you track and there is no machinery tracking it."),
            "evidence": {"estimand": i},
        })
    return out


def q_orphan_signal(d, nodes, edges):
    """A signal that measures nothing declared."""
    measuring = {a for a, _ in rel(edges, "measures")}
    reading = {b for _, b in rel(edges, "reads")} if True else set()
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Signal" or i in measuring:
            continue
        out.append({
            "pattern": "orphan_signal",
            "claim": (f"Signal `{i}` is observed but is not connected to any estimand. You are "
                      f"collecting it without having said what it tells you."),
            "evidence": {"signal": i},
        })
    return out


def q_no_loop_closed(d, nodes, edges):
    """Interventions and signals exist but no loop is declared."""
    loops = d.get("loops") or []
    ivs = [i for i, n in nodes.items() if n.get("kind") == "Intervention"]
    sigs = [i for i, n in nodes.items() if n.get("kind") == "Signal"]
    if loops or not (ivs and sigs):
        return []
    return [{
        "pattern": "no_loop_closed",
        "claim": (f"{len(sigs)} signal(s) and {len(ivs)} intervention(s) are declared and NO "
                  f"loop closes between them. Nothing states which observation triggers which "
                  f"action, or on what cadence — so this is a list of parts, not a control "
                  f"loop."),
        "evidence": {"signals": sigs, "interventions": ivs},
    }]


def q_interventions_without_policy(d, nodes, edges):
    """More than one intervention and nothing selects between them."""
    ivs = [i for i, n in nodes.items() if n.get("kind") == "Intervention"]
    pols = [i for i, n in nodes.items() if n.get("kind") == "Policy"]
    if len(ivs) < 2 or pols:
        return []
    return [{
        "pattern": "interventions_without_policy",
        "claim": (f"{len(ivs)} interventions are available ({', '.join(ivs)}) and no policy "
                  f"selects between them. Nothing states the condition under which you would "
                  f"choose one over the other."),
        "evidence": {"interventions": ivs},
    }]


def edges_from(edges, node):
    return [(e.get("from"), e.get("to")) for e in edges if e.get("from") == node]


def q_loop_polarity(d, nodes, edges):
    """
    Reinforcing loop with no balancing path.

    System dynamics: a loop with an EVEN number of negative links is reinforcing (runaway);
    odd is balancing (self-correcting). An agent loop whose signal is produced by its own
    intervention, with no corrective link, is reinforcing by construction.

    This formalises the Ralph finding. The agent -> files -> agent path carries no negative
    link, so it is reinforcing. Tests are the only negative link — the only thing making the
    loop balancing. Remove them and it provably diverges.
    """
    produced = {b for _, b in rel(edges, "produces")}
    measured_by = {}
    for a, b in rel(edges, "measures"):
        measured_by.setdefault(b, set()).add(a)
    out = []
    for lp in d.get("loops") or []:
        sig = lp.get("signal")
        if sig not in produced:
            continue                     # signal is exogenous — fine
        # the loop's own signal is produced by the loop. Is there ANY exogenous signal
        # measuring the same estimand?
        ests = {b for a, b in rel(edges, "measures") if a == sig}
        exogenous = []
        for e in ests:
            for other in measured_by.get(e, set()):
                if other != sig and other not in produced:
                    exogenous.append(other)
        if exogenous:
            continue                     # a balancing path exists
        out.append({
            "pattern": "reinforcing_loop_no_balancer",
            "claim": (f"Loop `{lp.get('id')}` is REINFORCING: its signal `{sig}` is produced by "
                      f"its own intervention, and no exogenous signal measures what it "
                      f"measures. System dynamics: a loop with no negative link diverges rather "
                      f"than self-corrects. Nothing outside the loop can contradict it."),
            "evidence": {"loop": lp.get("id"), "endogenous_signal": sig,
                         "exogenous_signals": []},
        })
    return out


def q_regulator_without_model(d, nodes, edges):
    """
    Conant & Ashby 1970: every good regulator of a system must be a model of that system.

    A loop with a Policy and a DesiredCondition but no model of the regulated quantity — no
    Explanation, no Estimator over it — is a reflex, not a regulator. This is a proved
    necessary condition rather than a style preference.
    """
    targets = {b for _, b in rel(edges, "targets")}
    if not targets or not [i for i, n in nodes.items() if n.get("kind") == "Policy"]:
        return []
    modelled = set()
    for a, b in rel(edges, "explains"):
        modelled.add(b)
    for a, b in rel(edges, "estimates"):
        modelled.add(b)
        holder = nodes.get(b, {})
        for x, y in rel(edges, "measures"):
            modelled.add(y)
    out = []
    for t in targets:
        explained = any(b == t for _, b in rel(edges, "explains"))
        if explained:
            continue
        out.append({
            "pattern": "regulator_without_model",
            "claim": (f"The loop regulates `{t}` but contains no MODEL of it — no Explanation "
                      f"of what generates it. Conant & Ashby (1970): every good regulator of a "
                      f"system must be a model of that system. Without one this is a reflex "
                      f"against a setpoint, not a regulator, and it cannot anticipate."),
            "evidence": {"target": t, "explanations": []},
        })
    return out


def q_uncontrollable_target(d, nodes, edges):
    """
    Kalman controllability: a target no intervention can drive.

    Two failures live here and they are NOT the same diagnosis, so they are reported
    separately. Conflating them produced a message claiming an intervention was unwired when
    the spec had wired it:

      uncontrollable_target — no lever points at the estimand at all. A wish.
      open_loop             — a lever and a measurement both exist, but no Loop record joins
                              them. The parts of a regulator, not assembled into one.

    Only DesiredCondition sources count. Interventions also carry `targets` edges, and
    iterating the relation blindly reported every lever as its own broken target.
    """
    out = []
    ivs = [i for i, n in nodes.items() if n.get("kind") == "Intervention"]
    movable = {b for a, b in rel(edges, "targets")
               if nodes.get(a, {}).get("kind") == "Intervention"}
    measures = rel(edges, "measures")

    for a, b in rel(edges, "targets"):
        if nodes.get(a, {}).get("kind") != "DesiredCondition":
            continue
        if b not in movable:
            out.append({
                "pattern": "uncontrollable_target",
                "claim": (f"`{a}` sets a target on `{b}`, and no intervention declares that it "
                          f"moves `{b}`. Controllability: a target nothing can drive toward is "
                          f"a wish, not a setpoint. The loop declares {len(ivs)} "
                          f"intervention(s) — {ivs} — and none of them acts on this quantity."),
                "evidence": {"target": b, "desired_condition": a, "interventions": ivs},
            })
            continue

        sigs = {x for x, y in measures if y == b}
        if not sigs:
            continue          # unmeasured_estimand already says this, and says it better
        closing = {lp.get("intervention") for lp in (d.get("loops") or [])
                   if lp.get("signal") in sigs}
        if not closing:
            movers = sorted(x for x, y in rel(edges, "targets")
                            if y == b and nodes.get(x, {}).get("kind") == "Intervention")
            out.append({
                "pattern": "open_loop",
                "claim": (f"`{b}` is measured by {sorted(sigs)} and moved by {movers}, but no "
                          f"loop closes between them. Every part of a regulator is present and "
                          f"nothing joins them, so the measurement never reaches the lever. "
                          f"Felt symptom: it observes, and it acts, and the two are unrelated."),
                "evidence": {"target": b, "signals": sorted(sigs), "interventions": movers},
            })
    return out



# ---------------------------------------------------------------------------------------
# GROUP CHECKS — several loops in one file, sharing nodes.
#
# A group is not a bigger loop. Its failures are relational: two agents estimating the same
# quantity with nothing to reconcile them, an act two loops can reach under different rules,
# a verifier whose only input is the thing it verifies. None is visible when each loop is
# read alone, which is why multi-agent systems fail in ways their components do not.
# ---------------------------------------------------------------------------------------

def _loop_of(d, nid, edges):
    """Which declared loops touch this node."""
    ls = []
    for lp in (d.get("loops") or []):
        if nid in (lp.get("signal"), lp.get("intervention")):
            ls.append(lp["id"])
    return ls




# ---------------------------------------------------------------------------------------
# RESOURCE CHECKS.
#
# Harness engineering — budgets, step ceilings, stall detection, quotas — is standard practice
# in 2026 and this linter was silent on all of it. `Resource` sat in the catalog unused.
#
# The obvious check is "does it have a ceiling", and the field already knows to ask that. The
# one worth adding is the next question, which the field does NOT ask:
#
#     A CEILING IS A STOP, NOT A CORRECTION.
#
# A loop that runs at full rate into a wall and halts has not regulated anything; it has been
# truncated. Ashby's point about variety is exactly this — a stop absorbs no disturbance. The
# regulating version notices it is running low and does something different, which is what a
# deadband is for. Almost nothing does this.
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# ATTENTION.
#
# Every Calibration in this project scores an ESTIMATOR — was my conclusion right. Nothing
# scored a SIGNAL — was my LOOKING right. That asymmetry was invisible until someone named it,
# and it has three independent instances in the corpus already:
#
#   meeseeks_sourcing   `viability_review` retires a channel that finds nothing. It scores the
#                       SOURCE, not the candidate. Flagged as "unusual" long before it had a name.
#   conviction_termination  the stop rule reads `expected_info_gain` — is more looking worth
#                       it? — and nothing computes it.
#   customer_acquisition    `customer_interviews` is cost: high and nothing reviews whether it
#                       earns that.
#
# Three instances, three authors: the project's own bar for admitting a concept.
# ---------------------------------------------------------------------------------------

def q_informs_no_decision(d, nodes, edges):
    """
    Paying to learn something no decision depends on.

    Sharper than `orphan_signal`, which catches a signal informing NOTHING. This catches a
    signal that informs a belief which no rule reads — the value-of-information failure. The
    loop is not wrong about anything. It is spending attention it will not get back.
    """
    read = {t for i, n in nodes.items() if n.get("kind") == "Policy"
            for t in (n.get("inputs") or [])}
    if not read:
        return []            # no rule reads anything; a different check's problem
    # what a belief reaches, transitively, through explanation
    reach = {}
    for a, b in rel(edges, "explains") + rel(edges, "asserts"):
        reach.setdefault(a, set()).add(b)

    def touches(est, seen=None):
        seen = seen or set()
        if est in read:
            return True
        if est in seen:
            return False
        seen.add(est)
        return any(touches(x, seen) for x in reach.get(est, ()))

    out = []
    for sig, est in rel(edges, "measures"):
        n = nodes.get(sig, {})
        if n.get("kind") != "Signal" or touches(est):
            continue
        cost = n.get("cost")
        out.append({
            "pattern": "informs_no_decision",
            "claim": (f"`{sig}` is collected"
                      + (f" at {cost} cost" if cost else "")
                      + f" and tells you about `{est}`, and no decision rule reads `{est}`. "
                        f"The loop is not wrong about anything here — it is paying attention "
                        f"to something that changes nothing it does. Either a rule should read "
                        f"`{est}`, or this observation should stop."),
            "evidence": {"signal": sig, "estimand": est, "cost": cost},
        })
    return out


def q_expensive_signal_unreviewed(d, nodes, edges):
    """An expensive source that nothing ever asks was worth it."""
    scored = {b for a, b in rel(edges, "revises")
              if nodes.get(a, {}).get("kind") == "Calibration"
              and nodes.get(b, {}).get("kind") == "Signal"}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Signal" or n.get("cost") not in ("high", "medium"):
            continue
        if i in scored:
            continue
        out.append({
            "pattern": "expensive_signal_unreviewed",
            "claim": (f"`{i}` costs `{n['cost']}` to obtain and nothing reviews whether it "
                      f"earns that. Beliefs here get scored against outcomes; the SOURCES do "
                      f"not. Add `checked_by:` naming what asks whether looking here was "
                      f"worth it — the way a channel that finds nothing gets retired."),
            "evidence": {"signal": i, "cost": n.get("cost")},
        })
    return out



def q_insufficient_variety(d, nodes, edges):
    """
    Ashby 1956: only variety can destroy variety.

    A regulator can absorb a disturbance only if its variety is at least as great as the
    disturbance's. Two levers against ten failure modes cannot regulate, and no amount of
    prompt quality fixes it.

    This was listed as blocked for most of the project's life, waiting on a `Disturbance`
    primitive the budget had no room for. It was never blocked: `not_modelling:` is the
    disturbance list. The things you have declared you are not modelling are precisely the
    disturbances you are not regulating against.

    HONEST ABOUT THE PROXY: counting named disturbances against distinguishable actions is a
    crude reading of variety — Ashby's is a measure over states, not a headcount, and a spec
    that names no disturbances scores well by saying nothing. It fires only when the gap is
    stark, and it is a prompt to think rather than a proof.
    """
    dz = [n.get("statement") or i for i, n in nodes.items() if n.get("kind") == "Disturbance"]
    ivs = [i for i, n in nodes.items() if n.get("kind") == "Intervention"]
    if not dz or not ivs or len(dz) <= len(ivs):
        return []
    return [{
        "pattern": "insufficient_variety",
        "claim": (f"The loop declares {len(ivs)} distinct action(s) — {sorted(ivs)} — and "
                  f"{len(dz)} thing(s) it is knowingly not modelling: {sorted(dz)}. Only "
                  f"variety can destroy variety: a regulator needs at least as many "
                  f"distinguishable responses as the disturbance has modes. Either name more "
                  f"levers, or accept that the loop cannot absorb what it has already listed."),
        "evidence": {"actions": sorted(ivs), "disturbances": sorted(dz)},
    }]


def q_unbounded_loop(d, nodes, edges):
    """A loop that declares nothing it can run out of."""
    if not (d.get("loops") or []):
        return []
    res = [i for i, n in nodes.items() if n.get("kind") == "Resource"]
    if res:
        return []
    consumed = {b for _, b in rel(edges, "consumes")}
    if consumed:
        return []
    return [{
        "pattern": "unbounded_loop",
        "claim": ("The loop declares nothing it can run out of — no iteration ceiling, no "
                  "token or time budget, no attention it spends. Nothing in the encoding says "
                  "what stops it, so it runs until something outside reaches in and halts it. "
                  "Declare it under `spends:` even if the limit is generous; an undeclared "
                  "budget is still a budget, just one nobody chose."),
        "evidence": {"resources": []},
    }]


def q_ceiling_without_correction(d, nodes, edges):
    """
    A limit exists and no decision rule reads how much is left.

    KNOWN LIMIT OF THIS CHECK: it clears as soon as some rule reads the resource, and does not
    distinguish READING-TO-HALT from READING-TO-ADAPT. LangGraph's reflection example reads its
    own message count and stops — which clears this check and is still a stop, not a
    correction. Separating the two needs the format to express "stop" as an action, which it
    does not yet. So a clear result here means "something watches the budget", which is
    necessary and not sufficient.

    The check the field does not run. A ceiling truncates a loop; it does not regulate one.
    The loop proceeds at full rate until it hits the wall and stops, which is indistinguishable
    from failure and arrives without warning. Regulation means noticing you are running low and
    doing something different — searching narrower, sampling less, escalating, stopping early
    and saying so.
    """
    pol_inputs = {t for i, n in nodes.items() if n.get("kind") == "Policy"
                  for t in (n.get("inputs") or [])}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Resource" or not n.get("limit"):
            continue
        if i in pol_inputs:
            continue
        out.append({
            "pattern": "ceiling_without_correction",
            "claim": (f"`{i}` has a limit of `{n['limit']}` and no decision rule reads how "
                      f"much is left. The loop runs at full rate until it hits the wall and "
                      f"stops. A ceiling is a stop, not a correction: it truncates the loop "
                      f"rather than regulating it, and the halt is indistinguishable from "
                      f"failure and arrives without warning. To regulate, some rule in `when:` "
                      f"has to read `{i}` and do something different when it runs low."),
            "evidence": {"resource": i, "limit": n.get("limit"), "read_by_policy": False},
        })
    return out


def q_spends_without_limit(d, nodes, edges):
    """Something consumed that has no ceiling and nothing refills."""
    replenished = {b for _, b in rel(edges, "replenishes")}
    out = []
    for a, b in rel(edges, "consumes"):
        n = nodes.get(b, {})
        if n.get("kind") != "Resource" or n.get("limit") or b in replenished \
                or n.get("replenished"):
            continue
        out.append({
            "pattern": "spends_without_limit",
            "claim": (f"`{a}` consumes `{b}`, and `{b}` has no declared limit and nothing "
                      f"replenishes it. It only ever goes down, and the encoding does not say "
                      f"how far down it can go before this stops working. Exhaustion is "
                      f"certain; only the date is unstated."),
            "evidence": {"action": a, "resource": b},
        })
    return out


def q_belief_never_checked(d, nodes, edges):
    """
    A belief formed by judgement that nothing ever scores against what happened.

    THE HEADLINE DEFECT, and until now it could not fire on an ordinary spec: the existing
    `uncalibrated_estimator` requires `criticality: existential` on the estimand, a field the
    authoring format has no key for. So the project's most-cited finding — three independent
    systems, three careful authors, an estimator nothing scores — was gated behind something
    nobody could write. This is the general form.

    A COMPUTED quantity is exempt: arithmetic makes no prediction, so there is nothing to
    score. Only latent beliefs — where a judgement is being made — can be wrong in the way
    calibration measures.
    """
    calibrated = {b for a, b in rel(edges, "revises")
                  if nodes.get(a, {}).get("kind") == "Calibration"}
    latent = {i for i, n in nodes.items()
              if n.get("kind") == "Estimand" and n.get("determination") == "latent"}
    out = []
    for a, b in rel(edges, "estimates"):
        if b not in latent or a in calibrated:
            continue
        n = nodes.get(a, {})
        if (n.get("form") or "").lower() in ("formula", "arithmetic", "computed"):
            continue
        q = nodes.get(b, {}).get("question")
        out.append({
            "pattern": "belief_never_checked",
            "claim": (f"The loop forms a belief about `{b}`"
                      + (f' — "{q}" — ' if q else " ")
                      + f"by {n.get('form') or 'unspecified means'}, and nothing ever scores "
                        f"it against what actually happened. Add `checked_by:` naming what "
                        f"compares past calls to outcomes. Until then its confidence is a "
                        f"number nobody has ever been graded on, and it can be confidently "
                        f"wrong forever."),
            "evidence": {"belief": b, "how": n.get("form"), "checked_by": None},
        })
    return out




def q_policy_reads_undeclared(d, nodes, edges):
    """
    A decision rule that tests something the spec never declares.

    Distinct from `policy_on_unmeasured_inputs`, which catches a DECLARED quantity nothing
    measures. This catches a quantity that appears only inside the condition — never in
    `goal`, never in `beliefs`, so nothing observes it, nothing computes it, and nothing can.
    It is the sharper version because there is no place in the spec where it could be wrong;
    it simply does not exist.

    The original instance: a termination rule guarding on `avg_confidence`, which is named
    nowhere else in the system.
    """
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Policy":
            continue
        for name in (n.get("reads_undeclared") or []):
            # Only identifier-shaped tokens. Conditions are written in prose, and without
            # this the check flagged "plan", "remain" and "steps" as undeclared quantities —
            # measuring the author's sentence structure at a 100% rate rather than the loop.
            if "_" not in name:
                continue
            out.append({
                "pattern": "policy_reads_undeclared",
                "claim": (f"The decision rule tests `{name}`, and `{name}` is declared nowhere "
                          f"in this loop — not as a goal, not as a belief. Nothing observes it "
                          f"and nothing computes it. The rule reads a quantity that does not "
                          f"exist, so whatever it does at that branch is not what the spec "
                          f"says it does."),
                "evidence": {"policy": i, "undeclared": name, "rule": n.get("rule")},
            })
    return out


def q_single_point_of_grounding(d, nodes, edges):
    """
    A loop with exactly ONE exogenous input.

    This is the Ralph finding stated correctly, and the previous version was wrong. Encoded in
    the old graph shape Ralph tripped `no_exogenous_grounding` — but Ralph DOES have an
    exogenous input: the tests. That firing was an artifact of the loop record naming only one
    of its two signals, and the loop format, which records them all, correctly stopped it.

    The real property is narrower and more useful: everything Ralph observes is produced by
    Ralph except the tests, so the tests are the ONLY thing that can fail in a way the agent
    did not intend. With a strong suite Ralph is a genuine regulator; without one it is sealed.
    That is a single point of failure in the epistemics, not the absence of grounding — and it
    is what practitioners actually report.
    """
    produced = {b for a, b in rel(edges, "produces")}
    out = []
    for lp in (d.get("loops") or []):
        mine = set(lp.get("signals") or ([lp["signal"]] if lp.get("signal") else []))
        mine = {s for s in mine if nodes.get(s, {}).get("kind") == "Signal"}
        if len(mine) < 2:
            continue
        exo = {s for s in mine
               if s not in produced and nodes.get(s, {}).get("origin") != "ourselves"}
        if len(exo) != 1:
            continue
        only = next(iter(exo))
        out.append({
            "pattern": "single_point_of_grounding",
            "claim": (f"Loop `{lp['id']}` reads {len(mine)} observations and exactly one of "
                      f"them — `{only}` — comes from outside itself. Everything else it looks "
                      f"at, it produced. `{only}` is therefore the only thing that can fail in "
                      f"a way this loop did not intend, and the loop is exactly as trustworthy "
                      f"as that one input. Weaken it and the loop is sealed."),
            "evidence": {"loop": lp["id"], "sole_exogenous": only,
                         "endogenous": sorted(mine - exo)},
        })
    return out


def q_shared_estimand_no_arbiter(d, nodes, edges):
    """
    Two loops estimate the same quantity and nothing reconciles them.

    A verifier disagreeing with a worker is the POINT of a verifier — so this is not a defect
    by itself. It is a defect when the group declares no policy reading both, because then
    disagreement resolves by arrival order. Felt symptom: "my agents disagree and whichever
    finishes last wins."
    """
    if not d.get("group"):
        return []
    out = []
    for est, n in nodes.items():
        if n.get("kind") != "Estimand":
            continue
        ers = sorted({a for a, b in rel(edges, "estimates") if b == est})
        if len(ers) < 2:
            continue
        forms = {nodes[e].get("form") for e in ers if e in nodes}
        readers = [p for p, pn in nodes.items() if pn.get("kind") == "Policy"
                   and est in (pn.get("inputs") or [])]
        if readers:
            continue
        out.append({
            "pattern": "shared_estimand_no_arbiter",
            "claim": (f"`{est}` is estimated by {len(ers)} independent estimators — {ers}, "
                      f"by method(s) {sorted(f for f in forms if f)} — and no policy in the "
                      f"group reads it. When they disagree nothing reconciles them, so the "
                      f"value that survives is whichever wrote last. Felt symptom: my agents "
                      f"disagree and the answer depends on ordering."),
            "evidence": {"estimand": est, "estimators": ers},
        })
    return out


def q_no_exogenous_grounding(d, nodes, edges):
    """
    A loop whose every signal is manufactured inside the group.

    This is the Ralph finding, stated generally and computed rather than intuited. A loop with
    no exogenous input cannot be corrected by the world: it can only be consistent with itself.
    A verifier whose sole input is the worker's own report is the multi-agent instance, and it
    is the most common broken shape in agent groups.
    """
    produced = {b for a, b in rel(edges, "produces")}
    out = []
    for lp in (d.get("loops") or []):
        # every signal this loop reads, not merely the one it nominally closes on
        mine = set(lp.get("signals") or ([lp["signal"]] if lp.get("signal") else []))
        mine = {s for s in mine if nodes.get(s, {}).get("kind") == "Signal"}
        if not mine:
            continue
        exo = mine - produced
        if exo:
            continue
        out.append({
            "pattern": "no_exogenous_grounding",
            "claim": (f"Loop `{lp['id']}` reads only {sorted(mine)}, and every one of those is "
                      f"produced by an act inside this group. Nothing it observes can surprise "
                      f"it. It cannot be wrong in a way it did not already contain, so it will "
                      f"converge on agreement rather than on truth."),
            "evidence": {"loop": lp["id"], "signals": sorted(mine)},
        })
    return out


def q_unowned_act(d, nodes, edges):
    """
    An act two loops can select under different approval rules.

    Whichever loop reaches it first sets the gate. That is authority decided by scheduling.
    """
    if not d.get("group"):
        return []
    out = []
    for act, n in nodes.items():
        if n.get("kind") != "Intervention":
            continue
        selectors = sorted({a for a, b in rel(edges, "authorizes") if b == act
                            and nodes.get(a, {}).get("kind") == "Policy"})
        if len(selectors) < 2:
            continue
        out.append({
            "pattern": "unowned_act",
            "claim": (f"Intervention `{act}` is selected by {len(selectors)} policies — "
                      f"{selectors} — belonging to different loops. Nothing says which one "
                      f"owns it, so its approval rule is whichever loop reaches it first. "
                      f"Authority decided by scheduling is not authority."),
            "evidence": {"intervention": act, "policies": selectors},
        })
    return out


def q_irreversible_without_approval(d, nodes, edges):
    """
    An irreversible intervention no human gates.

    The central agent-deployment question — what may this thing do without approval, and
    irreversibly — and no framework represents it. Felt symptom: "my agent did something I
    cannot undo."
    """
    humans = {i for i, n in nodes.items()
              if n.get("kind") == "Party" and n.get("kind_of") != "agent"
              and (n.get("party_kind") or n.get("human") or "") != "agent"}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Intervention":
            continue
        if n.get("reversibility") not in ("irreversible", "costly"):
            continue
        if n.get("requires_approval_from"):
            continue
        out.append({
            "pattern": "irreversible_without_approval",
            "claim": (f"Intervention `{i}` is marked `{n.get('reversibility')}` and declares no "
                      f"`requires_approval_from`. The loop may take an act it cannot undo with "
                      f"no human gate. This is the question every agent deployment turns on and "
                      f"no framework represents it."),
            "evidence": {"intervention": i, "reversibility": n.get("reversibility")},
        })
    return out


def q_human_without_signal(d, nodes, edges):
    """
    A human party who bears consequence but receives no signal — oversight in name only.

    Felt symptom: "I am accountable for what it does and I find out afterwards."
    """
    bears = {a for a, _ in rel(edges, "bears")}
    holds = {a for a, _ in rel(edges, "holds")}
    out = []
    for i, n in nodes.items():
        if n.get("kind") != "Party":
            continue
        pk = n.get("party_kind") or n.get("kind_of")
        if pk not in ("human", None):
            continue
        if i not in bears:
            continue
        if i in holds:
            continue                      # holds an estimate, so information reaches them
        out.append({
            "pattern": "accountable_but_blind",
            "claim": (f"Party `{i}` bears a consequence and holds no estimate — nothing in the "
                      f"loop routes information to them. They carry the cost of being wrong and "
                      f"receive nothing with which to be right. Human-in-the-loop in name only."),
            "evidence": {"party": i},
        })
    return out


def q_no_escalation_path(d, nodes, edges):
    """A loop with a human party and no policy that escalates to them."""
    parties = [i for i, n in nodes.items() if n.get("kind") == "Party"]
    humans = [i for i in parties
              if (nodes[i].get("party_kind") or "human") not in ("agent", "system")]
    pols = [n for i, n in nodes.items() if n.get("kind") == "Policy"]
    if not pols:
        return []
    if not humans:
        # Requiring a declared human before checking for escalation had it backwards: a loop
        # that names NO person is the more alarming case, and the check skipped it silently.
        return [{
            "pattern": "no_human_at_all",
            "claim": (f"The loop makes decisions — {len(pols)} rule(s) — and declares no "
                      f"person anywhere. Nobody approves anything, nobody is escalated to, "
                      f"and nobody is recorded as bearing the cost when it is wrong. Whatever "
                      f"this loop does, it does unattended and unowned."),
            "evidence": {"policies": len(pols), "people": parties},
        }]
    if any(p.get("escalates") for p in pols):
        return []
    gated = any(n.get("requires_approval_from")
                for n in nodes.values() if n.get("kind") == "Intervention")
    if gated:
        return []
    return [{
        "pattern": "no_escalation_path",
        "claim": (f"The loop declares {len(parties)} part(ies) and {len(pols)} polic(ies), and "
                  f"no policy escalates and no intervention requires approval. There is no "
                  f"point at which this loop stops and asks. It either succeeds or fails "
                  f"silently."),
        "evidence": {"parties": parties},
    }]


QUERIES = [
    q_belief_never_checked,
    q_informs_no_decision,
    q_expensive_signal_unreviewed,
    q_insufficient_variety,
    q_unbounded_loop,
    q_ceiling_without_correction,
    q_spends_without_limit,
    q_single_point_of_grounding,
    q_policy_reads_undeclared,
    q_shared_estimand_no_arbiter,
    q_no_exogenous_grounding,
    q_unowned_act,
    q_irreversible_without_approval,
    q_human_without_signal,
    q_no_escalation_path,
    q_loop_polarity,
    q_regulator_without_model,
    q_uncontrollable_target,
    q_estimand_never_estimated,
    q_orphan_signal,
    q_no_loop_closed,
    q_interventions_without_policy,
    q_policy_on_unmeasured_inputs,
    q_invariant_on_unmeasured,
    q_hinge_without_sensor,
    q_hinge_without_resolution,
    q_uncalibrated_estimator,
    q_consequence_without_authority,
    q_estimate_without_authority,
    q_shared_intervention_across_timescales,
    q_estimand_without_estimator,
    q_unmeasured_estimand,
    q_delay_without_feedback_owner,
]



# ---------------------------------------------------------------------------------------
# Findings are the product's user-facing text, so they speak the format's vocabulary rather
# than the IR's. The graph internally calls things Intervention and Estimand; nobody writing
# a spec ever types those words, and a linter that answers in a vocabulary the author never
# used is the same unintuitiveness one layer out.
#
# A display layer, deliberately: --json emits the raw claim, so downstream tooling and the
# archived studies keep the stable internal names.
# ---------------------------------------------------------------------------------------

PLAIN = [
    ("DesiredCondition", "target"), ("Intervention", "action"), ("Estimator", "belief rule"),
    ("Estimand", "quantity"), ("Calibration", "check"), ("Explanation", "model"),
    ("Signal", "observation"), ("Party", "person"), ("Consequence", "exposure"),
    ("Constraint", "limit"), ("Estimate", "belief"),
    ("intervention", "action"), ("estimand", "quantity"), ("signal", "observation"),
    ("party", "person"), ("parties", "people"), ("estimator", "belief rule"),
    ("interventions", "actions"), ("estimands", "quantities"), ("signals", "observations"),
    ("requires_approval_from", "needs_approval"), ("reversibility", "can_undo"),
    ("irreversible", "can_undo: no"), ("costly", "can_undo: costly"),
    ("holds no estimate", "sees nothing"), ("`measures`", "`informs`"),
]


def plain(text):
    import re
    for a, b in PLAIN:
        text = re.sub(rf"(?<![\w]){re.escape(a)}(?![\w])", b, text)
    return text[:1].upper() + text[1:] if text else text


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
            org = organise(d, claims)
            print("=" * 72)
            print(f"{d.get('encodes')} — {len(claims)} finding(s)")
            print("=" * 72)

            def show(title, blurb, items):
                if not items:
                    return
                print(f"\n{title}")
                print(f"  {blurb}")
                for pat, cs in group(items).items():
                    subs = [s for s in (_subject(c) for c in cs) if s]
                    tag = f"[{pat}]" + (f" ×{len(cs)}" if len(cs) > 1 else "")
                    print(f"\n  {tag}")
                    if len(cs) > 1 and subs:
                        print(f"    affects: {', '.join(subs)}")
                    print(f"    {plain(cs[0]['claim'])}")

            show("SPECIFIC TO THIS LOOP",
                 "unusual — most loops in the reference corpus do not have these.",
                 org["specific"])
            show("COMMON", "seen in a fair number of loops; still worth deciding about.",
                 org["common"])

            if org["universal"]:
                pats = sorted({c["pattern"] for c in org["universal"]})
                print("\nUNIVERSAL — context, not a finding about this loop")
                print("  Every loop in the reference corpus has these, including every "
                      "framework's own\n  best-practice examples. Real, and they tell you "
                      "nothing about YOUR spec specifically.")
                for p in pats:
                    r = base_rates().get(p, 0)
                    print(f"    {p} ({r:.0%} of the corpus)")

            if org["considered"]:
                print("\nCONSIDERED — you have read these and decided")
                print("  Not suppressed. Shown so a reviewer sees the decision rather than a "
                      "silence.")
                seen = {}
                for c, because, revisit in org["considered"]:
                    seen.setdefault((c["pattern"], because, revisit), []).append(c)
                for (pat, because, revisit), cs in seen.items():
                    subs = [x for x in (_subject(c) for c in cs) if x]
                    tag = f"[{pat}]" + (f" ×{len(cs)}" if len(cs) > 1 else "")
                    print(f"\n  {tag} decided" + (f" — {', '.join(subs)}" if subs else ""))
                    print(f"    because: {because}")
                    if revisit:
                        print(f"    revisit: {revisit}")

            for k in org["stale"]:
                print(f"\n  ! `consider: {k}` matches no finding — the spec changed and the "
                      f"justification did not.\n    A stale justification is worse than none.")
    if as_json:
        print(json.dumps(allout, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
