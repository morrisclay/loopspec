#!/usr/bin/env python3
"""
Judge v2 — built after v1 was shown to be badly flawed.

Measured defects in v1:
  * correlation(answer length, score) = +0.72 — over half the variance was word count
  * mean inter-dimension correlation = +0.86, with causal_depth <-> cross_level at
    exactly +1.00. Five dimensions were one judgment wearing five hats; a 25-point
    scale carried roughly 6 points of real information.
  * single judge, no inter-judge agreement, no repeat, no anchors

Fixes:
  1. LENGTH CONTROL — every answer truncated to the same word budget per question, so
     the judge cannot reward completeness.
  2. PER-QUESTION — compare like with like instead of whole essays of differing scope.
  3. RANKING, not scoring — LLM judges are far more reliable at ordering than at
     assigning absolute numbers, and ranking has no scale to drift.
  4. THREE JUDGES from three vendors, with inter-judge agreement reported. If they
     disagree, the metric is noise and should be said to be noise.
  5. ONE criterion, because five collapsed to one anyway.
"""
import os, re, json, itertools, urllib.request
from collections import defaultdict

KEY = os.environ["OPENROUTER_API_KEY"]
W = os.path.dirname(os.path.abspath(__file__))
SYSTEMS = ("hospital", "toyota", "hop_aero")
ARMS = ["prose", "encoding", "both", "generated", "generated_both", "stratified"]
JUDGES = [("openai/gpt-5.5", "gpt-5.5"),
          ("google/gemini-2.5-pro", "gemini-2.5-pro"),
          ("deepseek/deepseek-v3.2", "deepseek-v3.2")]
WORD_CAP = 130

CRITERION = ("Which answer would be most useful to a person who actually runs this system — "
             "most likely to change what they do, because it identifies a real mechanism they "
             "had not already accounted for? Reward concrete causal chains. Penalise "
             "restatement of the obvious and penalise confident invention.")


def split_questions(text):
    parts = re.split(r"\n\s*(?:#+\s*)?(?:\*\*)?Q?([1-4])[\.\):]", text)
    out = {}
    if len(parts) >= 3:
        for i in range(1, len(parts) - 1, 2):
            try:
                out[int(parts[i])] = parts[i + 1].strip()
            except ValueError:
                pass
    if len(out) < 4:                       # fallback: quarter it
        w = text.split()
        n = max(1, len(w) // 4)
        out = {i + 1: " ".join(w[i * n:(i + 1) * n]) for i in range(4)}
    return out


def cap(s):
    w = s.split()
    return " ".join(w[:WORD_CAP])


def post(model, prompt):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": 1200}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {KEY}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    m = (d.get("choices") or [{}])[0].get("message") or {}
    return m.get("content") or m.get("reasoning") or ""


rng = __import__("random").Random(20260802)
results = defaultdict(lambda: defaultdict(list))   # judge -> arm -> [rank]
raw_log = []

for system in SYSTEMS:
    qs = {arm: split_questions(open(f"{W}/answers/{system}__{arm}.md").read()) for arm in ARMS}
    for qn in (1, 2, 3, 4):
        order = ARMS[:]
        rng.shuffle(order)                       # fresh blinding per question
        labels = {chr(65 + i): arm for i, arm in enumerate(order)}
        block = "\n\n".join(
            f"### Answer {lab}\n{cap(qs[arm].get(qn, ''))}" for lab, arm in labels.items())
        prompt = (f"Six analysts answered the same question about the same real system.\n\n"
                  f"{block}\n\n---\n\n{CRITERION}\n\n"
                  f"All answers are truncated to the same length — do NOT reward length or "
                  f"completeness, judge only the substance present.\n\n"
                  f"Output ONLY a JSON array ranking every label best-first, e.g. "
                  f'["C","A","F","B","E","D"]. No other text.')
        for model, jname in JUDGES:
            try:
                txt = post(model, prompt)
            except Exception as e:
                print(f"{system} q{qn} {jname}: FAIL {str(e)[:90]}")
                continue
            m = re.search(r"\[[^\]]*\]", txt)
            if not m:
                print(f"{system} q{qn} {jname}: unparseable")
                continue
            try:
                rank = [x.strip().strip('"').upper() for x in json.loads(m.group())]
            except Exception:
                continue
            for pos, lab in enumerate(rank):
                if lab in labels:
                    results[jname][labels[lab]].append(pos)
            raw_log.append({"system": system, "q": qn, "judge": jname,
                            "rank_arms": [labels.get(l) for l in rank]})
        print(f"{system} q{qn}: judged")

json.dump(raw_log, open(f"{W}/judge_v2_raw.json", "w"), indent=1)
out = {j: {a: (sum(v) / len(v) if v else None) for a, v in d.items()} for j, d in results.items()}
json.dump(out, open(f"{W}/judge_v2_means.json", "w"), indent=1)
print("\nMEAN RANK (0 = best of 6), per judge")
allarms = sorted(ARMS, key=lambda a: sum(out[j].get(a, 6) or 6 for j in out))
hdr = "  %-16s" % "arm" + "".join("%16s" % j for _, j in JUDGES) + "%10s" % "MEAN"
print(hdr)
for a in allarms:
    vals = [out.get(j, {}).get(a) for _, j in JUDGES]
    good = [x for x in vals if x is not None]
    print("  %-16s" % a + "".join("%16s" % ("%.2f" % x if x is not None else "-") for x in vals)
          + "%10s" % ("%.2f" % (sum(good) / len(good)) if good else "-"))
