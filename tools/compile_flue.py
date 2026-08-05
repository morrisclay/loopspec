#!/usr/bin/env python3
"""
Compile a canonical loop encoding to Flue TypeScript.

    python3 tools/compile_flue.py <encoding.yaml> [--out DIR]

Mapping, from research/archive/uras/compiler/primitive_mapping.md, which was written against the real Flue
documentation (97 pages via `npx flue docs`) rather than the marketing page:

    Loop          -> Agent      defineAgent — continuing, stateful, identity-bearing
    Intervention  -> Action     defineAction — reusable finite behaviour
    Signal        -> Tool       defineTool, read-only
    Estimator     -> Action     with a REQUIRED idempotency key, because Flue documents
                                at-least-once execution: "recovery may re-dispatch the
                                provider once ... use application-owned idempotency keys"
    Estimate      -> durable conversation stream + persistence store
    Party         -> agent instance (one instance per party, one Durable Object each)

Four primitives have no Flue construct and are emitted as typed state the runtime must carry:
DesiredCondition compiles only into an instructions string, which loses inspectability;
Calibration, Resource and uncertainty have no platform support at all. Each is emitted as an
explicit TODO rather than silently dropped.

Linter findings are emitted as TODO comments in the generated code, so the gaps in the spec
arrive where the engineer is working rather than in a separate report.
"""
import sys, os, re, json, subprocess

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kebab(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def camel(s):
    parts = re.split(r"[^a-zA-Z0-9]+", str(s))
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:] if p)


def findings(path):
    try:
        out = subprocess.run(["python3", os.path.join(ROOT, "tools", "derive.py"), path,
                              "--json"], capture_output=True, text=True, timeout=120).stdout
        return [c for cs in json.loads(out).values() for c in cs]
    except Exception:
        return []


def compile(path, outdir):
    d = yaml.safe_load(open(path))
    nodes = {n["id"]: n for n in (d.get("nodes") or [])}
    edges = d.get("edges") or []
    name = d.get("encodes", "loop")

    def kind(k):
        return [i for i, n in nodes.items() if n.get("kind") == k]

    def rel(r):
        return [(e["from"], e["to"]) for e in edges if e.get("rel") == r]

    fs = findings(path)
    todo = "\n".join(f" * TODO [{c['pattern']}] {c['claim'][:150]}" for c in fs)

    os.makedirs(f"{outdir}/src/agents", exist_ok=True)
    os.makedirs(f"{outdir}/src/actions", exist_ok=True)
    os.makedirs(f"{outdir}/src/tools", exist_ok=True)

    # --- the loop becomes an agent -------------------------------------------------
    estimands = kind("Estimand")
    targets = {b: a for a, b in rel("targets")}
    goals = []
    for e in estimands:
        t = targets.get(e)
        if t:
            n = nodes[t]
            goals.append(f"{e} {n.get('comparator','')} {n.get('value','')}".strip())

    loops = d.get("loops") or []
    cadence = (nodes.get(loops[0].get("timescale"), {}).get("period")
               if loops else None)

    agent = f"""import {{ defineAgent }} from '@flue/runtime';

/**
 * {name} — compiled from a LoopSpec loop encoding.
 *
 * Loop -> Agent: an Agent is continuing and stateful with an identity, which is what a
 * non-terminating regulator needs. A Workflow would be wrong here — it is "a bounded job
 * that runs once and returns a result".
 *
{todo or " * (no linter findings)"}
 */
export default defineAgent(() => ({{
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `You regulate: {name}.

TARGET
{chr(10).join('  ' + g for g in goals) or '  TODO: no DesiredCondition in the encoding.'}

WHAT YOU ESTIMATE
{chr(10).join('  ' + e + ' (' + (nodes[e].get('determination') or 'latent') + ')' for e in estimands) or '  none'}

WHAT YOU OBSERVE
{chr(10).join('  ' + s for s in kind('Signal')) or '  none'}

WHAT YOU MAY DO
{chr(10).join('  ' + i for i in kind('Intervention')) or '  none'}

{'CADENCE: ' + cadence if cadence else 'TODO: no TimeScale declared — this loop has no cadence.'}

DesiredCondition compiles only to this prose. Flue has no structured goal representation,
so the target above is NOT machine-checkable at runtime. That is a platform gap, not a
modelling one.`,
}}));
"""
    open(f"{outdir}/src/agents/{kebab(name)}.ts", "w").write(agent)

    # --- interventions become actions ----------------------------------------------
    for iv in kind("Intervention"):
        n = nodes[iv]
        auth = [a for a, b in rel("authorizes") if b == iv]
        act = f"""import {{ defineAction }} from '@flue/runtime';
import * as v from 'valibot';

/** Intervention `{iv}` -> Action. target: {n.get('target','world')}
{'  * motive: ' + n.get('motive') if n.get('motive') else ''}
 * authorised by: {', '.join(auth) or 'NOBODY — no authorizes edge in the encoding'}
 */
export default defineAction({{
  name: '{camel(iv)}',
  description: '{iv.replace("_", " ")}',
  input: v.object({{
    reason: v.string(),          // why the policy selected this intervention
    idempotencyKey: v.string(),  // REQUIRED: Flue documents at-least-once execution
  }}),
  output: v.object({{ applied: v.boolean() }}),
  async run({{ input, log }}) {{
    log.info('{iv}', {{ key: input.idempotencyKey }});
    // TODO implement. Guard on idempotencyKey — a repeated dispatch must not double-apply.
    return {{ applied: false }};
  }},
}});
"""
        open(f"{outdir}/src/actions/{kebab(iv)}.ts", "w").write(act)

    # --- signals become read-only tools ---------------------------------------------
    measures = {a: b for a, b in rel("measures")}
    for sg in kind("Signal"):
        tgt = measures.get(sg)
        tool = f"""import {{ defineTool }} from '@flue/runtime';
import * as v from 'valibot';

/** Signal `{sg}` -> read-only Tool.
 * measures: {tgt or 'NOTHING — orphan signal, the encoding does not say what it tells you'}
 */
export default defineTool({{
  name: '{camel(sg)}',
  description: 'Read {sg.replace("_", " ")}',
  input: v.object({{}}),
  output: v.object({{ value: v.unknown(), observedAt: v.string() }}),
  async run() {{
    // TODO connect to the real source.
    return {{ value: null, observedAt: new Date().toISOString() }};
  }},
}});
"""
        open(f"{outdir}/src/tools/{kebab(sg)}.ts", "w").write(tool)

    # --- estimators become idempotent actions ---------------------------------------
    for es in kind("Estimator"):
        n = nodes[es]
        basis = n.get("idempotency_basis", "MISSING")
        est = f"""import {{ defineAction }} from '@flue/runtime';
import * as v from 'valibot';

/** Estimator `{es}` -> Action. form: {n.get('form','unspecified')}
 *
 * idempotency_basis: {basis}
 * Flue: "recovery may re-dispatch the provider once — consistent with at-least-once
 * execution ... use application-owned idempotency keys where repeated effects would be
 * harmful." A Bayesian update applied twice double-counts its evidence into a well-formed
 * but WRONG posterior. The key below is that guard.
 */
export default defineAction({{
  name: '{camel(es)}',
  description: 'Update belief from observations',
  input: v.object({{
    observations: v.array(v.unknown()),
    idempotencyKey: v.string(),   // derived from: {basis}
  }}),
  output: v.object({{ estimate: v.unknown(), uncertainty: v.string() }}),
  async run({{ input }}) {{
    // TODO: reject if idempotencyKey already applied.
    return {{ estimate: null, uncertainty: 'unquantified' }};
  }},
}});
"""
        open(f"{outdir}/src/actions/{kebab(es)}.ts", "w").write(est)

    gaps = []
    if not kind("Calibration"):
        gaps.append("Calibration — nothing scores the estimator's past predictions. No Flue "
                    "construct; must be built over EventStreamStore.")
    if not kind("Resource"):
        gaps.append("Resource — tokens/time/compute budget. Flue has no accounting.")
    gaps.append("Uncertainty — Flue has no distribution or confidence type. Estimate carries "
                "it as LoopSpec-side state only.")
    open(f"{outdir}/GAPS.md", "w").write(
        "# What does not compile\n\n" + "\n".join(f"- {g}" for g in gaps) + "\n")

    return {"agent": 1, "actions": len(kind("Intervention")) + len(kind("Estimator")),
            "tools": len(kind("Signal")), "findings": len(fs)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = "build/flue"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    r = compile(args[0], out)
    print(f"emitted {r['agent']} agent, {r['actions']} actions, {r['tools']} tools -> {out}")
    print(f"{r['findings']} linter finding(s) inlined as TODOs")
