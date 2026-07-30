#!/usr/bin/env python3
"""
MECE completion of the structure experiment.

Factorial: structure ∈ {none, persisted, generated-on-demand} × prose ∈ {absent, present}.
"none + absent" is empty, leaving five cells:

  1 prose            prose only                                        [done: 10.7]
  2 persisted        pre-built URAS encoding only                      [done: 12.0]
  3 both             pre-built encoding + prose                        [done: 13.3]
  4 generated        model builds its own structure from prose, then
                     answers from THAT ALONE (prose withheld at answer time)
  5 generated_both   model builds its own structure, answers from
                     structure + prose

Cells 4 and 5 test the possibility the project never considered: that persisting a
canonical model buys nothing over generating a throwaway one per question. If they match or
beat 2 and 3, most of URAS should not exist as a persisted artifact.

Generation is two-step with the prose genuinely withheld in cell 4, so it is a real test of
the persisted artifact rather than a paraphrase of the prose.
"""
import os, json, urllib.request

KEY = os.environ["OPENROUTER_API_KEY"]
W = os.path.dirname(os.path.abspath(__file__))
SYSTEMS = ("hospital", "toyota", "hop_aero")
MODEL = "google/gemini-2.5-pro"

QUESTIONS = [
    "Q1. Name the single change to this system most likely to improve its performance, and "
    "say precisely what would go wrong if it were made. Be concrete about the mechanism.",
    "Q2. This system will eventually fail or degrade in a way its operators do not currently "
    "anticipate. Describe that failure and the chain that produces it.",
    "Q3. Two experienced people inside this system disagree about something important and "
    "cannot resolve it with available evidence. What is the disagreement, and why is it "
    "unresolvable rather than merely unresolved?",
    "Q4. Someone proposes measuring this system better. Identify the measurement that would "
    "look most attractive and would in fact make things worse, and explain why.",
]

BUILD = """Here is a description of a real system.

{prose}

---

Build a structured model of this system as a flat typed graph. Use node kinds from:
System, Boundary, Party, Estimand, Signal, Estimate, Estimator, DesiredCondition,
PreferenceOrdering, Consequence, Intervention, Policy, Loop, Delay, TimeScale, Resource,
Constraint, Revision, Calibration.

Emit YAML with `nodes` (each with id + kind + relevant fields), `edges` (from, to, rel), and
`loops` (id, timescale, signal, intervention). Be thorough — this model is the only thing you
will have later. Output ONLY the YAML."""


def post(prompt, max_tokens=6000):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.3, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {KEY}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    m = (d.get("choices") or [{}])[0].get("message") or {}
    t = m.get("content") or m.get("reasoning") or ""
    if not t:
        raise ValueError(str(d.get("error"))[:200])
    return t


for system in SYSTEMS:
    prose = open(f"{W}/prose/{system}.md").read()
    gen_path = f"{W}/generated/{system}.yaml"
    os.makedirs(f"{W}/generated", exist_ok=True)
    if not os.path.exists(gen_path):
        try:
            g = post(BUILD.format(prose=prose))
        except Exception as e:
            print(f"{system}: BUILD FAILED {str(e)[:120]}")
            continue
        g = g.replace("```yaml", "").replace("```", "").strip()
        open(gen_path, "w").write(g)
        print(f"{system}: generated model, {len(g.split())} words")
    gen = open(gen_path).read()

    for arm, material in (
        ("generated", "Here is a structured model of a real system, in a graph representation "
                      "with typed nodes and typed edges.\n\n```yaml\n" + gen + "\n```"),
        ("generated_both", "Here is a description of a real system, followed by a structured "
                           "model of it.\n\n" + prose + "\n\n```yaml\n" + gen + "\n```"),
    ):
        out = f"{W}/answers/{system}__{arm}.md"
        if os.path.exists(out):
            continue
        prompt = (material + "\n\n---\n\nAnswer these four questions. Be specific and concrete "
                  "— name actual parties, quantities and mechanisms. Avoid generalities. "
                  "Around 150 words each.\n\n" + "\n\n".join(QUESTIONS))
        try:
            a = post(prompt)
        except Exception as e:
            print(f"{system}/{arm}: FAILED {str(e)[:120]}")
            continue
        open(out, "w").write(a)
        print(f"{system}/{arm}: {len(a.split())} words")
print("done")
