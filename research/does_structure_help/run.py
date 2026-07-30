#!/usr/bin/env python3
"""
Does the structure help an LLM reason, or does it get in the way?

Three arms per system, same questions:
  PROSE     — the original description only
  ENCODING  — the canonical URAS graph only
  BOTH      — prose plus encoding

Questions are chosen to need REASONING rather than lookup: predicting failure, diagnosing
cause, proposing intervention. A structure that only helps with lookup is a filing system,
not a representation.
"""
import os, json, urllib.request, re

KEY = os.environ["OPENROUTER_API_KEY"]
W = os.path.dirname(os.path.abspath(__file__))
SYSTEMS = ("hospital", "toyota", "hop_aero")
ANSWERER = "google/gemini-2.5-pro"

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


def post(model, prompt, max_tokens=4000):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
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


def material(system, arm):
    prose = open(f"{W}/prose/{system}.md").read()
    enc = open(f"{W}/encoding/{system}.yaml").read()
    if arm == "prose":
        return "Here is a description of a real system.\n\n" + prose
    if arm == "encoding":
        return ("Here is a structured model of a real system, in a graph representation with "
                "typed nodes and typed edges.\n\n```yaml\n" + enc + "\n```")
    return ("Here is a description of a real system, followed by a structured model of the "
            "same system.\n\n" + prose + "\n\n```yaml\n" + enc + "\n```")


for system in SYSTEMS:
    for arm in ("prose", "encoding", "both"):
        out = f"{W}/answers/{system}__{arm}.md"
        if os.path.exists(out):
            continue
        prompt = (material(system, arm) +
                  "\n\n---\n\nAnswer these four questions. Be specific and concrete — name "
                  "actual parties, quantities and mechanisms. Avoid generalities. Around 150 "
                  "words each.\n\n" + "\n\n".join(QUESTIONS))
        try:
            ans = post(ANSWERER, prompt)
        except Exception as e:
            print(f"{system}/{arm}: FAILED {str(e)[:120]}")
            continue
        open(out, "w").write(ans)
        print(f"{system}/{arm}: {len(ans.split())} words")
print("done")
