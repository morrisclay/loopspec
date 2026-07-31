#!/usr/bin/env python3
"""
Does a compiled artifact use the TARGET'S REAL API, or a plausible invented one?

    python3 research/compile_study/target_knowledge.py

The fidelity grader cannot tell. It checks that every element of the spec survived, and an
invented API carries them all perfectly — `FlueWorkflow` is not a Flue type, and a spec
transliterated into it scores 1.00. This is the check that separates the two.
"""
import glob, re, os, collections

CONSTRUCTS = {
    "langgraph": r"StateGraph|add_node|add_edge|from langgraph",
    "flue":      r"@flue/|defineAgent|defineAction|defineTool|defineWorkflow",
    "goose":     r"^\s*(instructions|extensions|activities|prompt)\s*:",
}
ROOT = os.path.dirname(os.path.abspath(__file__))

agg = collections.defaultdict(lambda: [0, 0])
for d in ("outputs", "outputs_v1", "outputs_api"):
    for f in sorted(glob.glob(os.path.join(ROOT, d, "*.md"))):
        head, _, t = open(f).read().partition("-->")
        if "finish: stop" not in head or len(t) < 400:
            continue
        tgt = re.search(r"target: (\w+)", head).group(1)
        key = f"{tgt} (+api)" if d == "outputs_api" else tgt
        agg[key][1] += 1
        agg[key][0] += bool(re.search(CONSTRUCTS[tgt], t, re.I | re.M))

print("Uses the target's REAL API?\n")
for tgt, (ok, tot) in sorted(agg.items(), key=lambda x: -x[1][0] / x[1][1]):
    print(f"  {tgt:14} {ok:3}/{tot:<3}  {ok/tot:5.0%}")
