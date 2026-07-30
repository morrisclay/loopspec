#!/usr/bin/env python3
"""
Sixth arm: STRATIFIED structure.

Tests whether organising the same material as three coupled levels —

    Forces  <->  Interactions  <->  Emergence

with bidirectional causation, beats the flat typed graph on the same reasoning questions.

The specific prediction this arm exists to test: the flat schema forces encoders to pick one
altitude, which showed up as estimand agreement of 0.07-0.17 that two individuation rules
failed to repair. If reality is stratified and the schema is flat, that divergence is the
frame's fault rather than the encoders'. A stratified encoding should therefore reason better
about cross-level questions — how a local action produces a system-level failure, why insiders
at different levels cannot resolve a disagreement.

Fair comparison: this arm gets the SAME prose and builds its own structure, exactly as the
`generated` arm does. It differs only in the organising schema. Anything it wins is
attributable to stratification, not to having more material.
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

Build a STRATIFIED model of this system with three coupled levels:

  FORCES        what pushes: constraints, scarcities, incentives, targets, consequences,
                lags, and the clocks things run on
  INTERACTIONS  what happens when forces meet: observing, estimating, deciding, acting,
                the loops these form
  EMERGENCE     what arises that is in no component: the system's boundary, its identity,
                the parties it constitutes, institutional behaviour

Causation runs BOTH WAYS between adjacent levels. Record both directions explicitly:

  upward    how forces produce interactions, and interactions produce emergent properties
  downward  how emergent properties constrain interactions, and interactions reshape forces

Two rules that matter:

1. The SAME thing may appear at more than one level with different roles. A price is emergent
   from trades and a force on traders; a boundary is emergent from a system's operation and a
   force on what it can observe. Record it at each level where it acts, and say which role.
2. Where the description operates at more than one altitude — a shop floor and a boardroom —
   represent BOTH, and record how they couple. Do not flatten to one.

Emit YAML with top-level keys `forces`, `interactions`, `emergence`, `upward`, `downward`.
Be thorough: this model is the only thing you will have later. Output ONLY the YAML."""


def post(prompt, max_tokens=7000):
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


os.makedirs(f"{W}/stratified", exist_ok=True)
for system in SYSTEMS:
    prose = open(f"{W}/prose/{system}.md").read()
    sp = f"{W}/stratified/{system}.yaml"
    if not os.path.exists(sp):
        try:
            g = post(BUILD.format(prose=prose))
        except Exception as e:
            print(f"{system}: BUILD FAILED {str(e)[:120]}")
            continue
        open(sp, "w").write(g.replace("```yaml", "").replace("```", "").strip())
        print(f"{system}: stratified model, {len(open(sp).read().split())} words")
    strat = open(sp).read()

    out = f"{W}/answers/{system}__stratified.md"
    if os.path.exists(out):
        continue
    prompt = ("Here is a stratified model of a real system, organised as three coupled levels "
              "with causation running both ways between them.\n\n```yaml\n" + strat +
              "\n```\n\n---\n\nAnswer these four questions. Be specific and concrete — name "
              "actual parties, quantities and mechanisms. Avoid generalities. Around 150 words "
              "each.\n\n" + "\n\n".join(QUESTIONS))
    try:
        a = post(prompt)
    except Exception as e:
        print(f"{system}/stratified: FAILED {str(e)[:120]}")
        continue
    open(out, "w").write(a)
    print(f"{system}/stratified: {len(a.split())} words")
print("done")
