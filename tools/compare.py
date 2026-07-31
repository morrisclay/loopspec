#!/usr/bin/env python3
"""
Put loops side by side.

    python3 tools/compare.py <spec.loop.yaml>...           # markdown table
    python3 tools/compare.py research/published_study/encodings/*.loop.yaml

The point of a notation is that it makes disagreement SPECIFIC. Agent loops are currently
argued about in prose — blog posts, conference keynotes, competing taxonomies — and two blog
posts cannot be diffed. Two specs can.

Nobody could previously put LangGraph's reflection tutorial next to CrewAI's self-evaluation
flow and say precisely what differs. Not because it is hard, but because there was no common
form to say it in. This is that comparison, generated from the specs rather than written.

The columns are the questions worth arguing over. A loop that answers them differently from
another is doing something different, and the table says what.
"""
import sys, os, glob

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop import normalize  # noqa: E402


def read(path):
    docs = [normalize(d) for d in yaml.safe_load_all(open(path)) if d]
    m = {}
    for d in docs:                       # a group folds into one row
        for k, v in d.items():
            if isinstance(v, dict):
                m.setdefault(k, {}).update(v)
            elif isinstance(v, list):
                m.setdefault(k, []).extend(v)
            else:
                m.setdefault(k, v)
    return m


def grounding(s):
    """Where does what it looks at come from? The question that separates these loops."""
    obs = (s.get("observes") or {}).values()
    if not obs:
        return "—"
    out = sum(1 for o in obs if (o or {}).get("origin") == "outside")
    own = sum(1 for o in obs if (o or {}).get("origin") == "ourselves")
    if out == 0 and own:
        return f"**none** ({own} own)"
    if out == 1:
        return f"**1 of {out + own}**"
    return f"{out} of {out + own}" if out or own else "unstated"


def checked(s):
    b = (s.get("beliefs") or {})
    if not b:
        return "—"
    n = sum(1 for v in b.values() if (v or {}).get("checked_by"))
    return f"{n}/{len(b)}" + ("" if n else " ✗")


def ceiling(s):
    sp = s.get("spends") or {}
    lim = [k for k, v in sp.items() if (v or {}).get("limit")]
    if not lim:
        return "**none** ✗"
    return ", ".join(lim)


def gate(s):
    acts = (s.get("actions") or {})
    risky = [k for k, v in acts.items() if (v or {}).get("can_undo") in ("no", "costly", False)]
    gated = [k for k in risky if (acts[k] or {}).get("needs_approval")]
    if not risky:
        return "—"
    return f"{len(gated)}/{len(risky)}" + ("" if len(gated) == len(risky) else " ✗")


def humans(s):
    p = (s.get("people") or {})
    h = [k for k, v in p.items() if (v or {}).get("human") or (v or {}).get("kind") == "human"]
    return ", ".join(h) if h else "**none** ✗"


COLS = [
    ("loop",            lambda s: f"`{s.get('loop','?')}`"),
    ("steers",          lambda s: ", ".join(f"`{k}`" for k in (s.get("goal") or {})) or "—"),
    ("beliefs",         lambda s: str(len(s.get("beliefs") or {}) or "—")),
    ("scored",          checked),
    ("exogenous input", grounding),
    ("ceiling",         ceiling),
    ("risky acts gated", gate),
    ("humans",          humans),
]


def main():
    paths = []
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        paths.extend(sorted(glob.glob(a)) if any(c in a for c in "*?") else [a])
    if not paths:
        sys.exit(__doc__.strip().split("\n\n")[1])
    specs = [read(p) for p in paths]

    print("| " + " | ".join(c for c, _ in COLS) + " |")
    print("|" + "|".join("---" for _ in COLS) + "|")
    for s in specs:
        print("| " + " | ".join(f(s) for _, f in COLS) + " |")

    # The tallies people would otherwise have to count by hand and would not.
    n = len(specs)
    nb = sum(1 for s in specs if (s.get("beliefs") or {})
             and not any((v or {}).get("checked_by") for v in s["beliefs"].values()))
    nc = sum(1 for s in specs
             if not any((v or {}).get("limit") for v in (s.get("spends") or {}).values()))
    nh = sum(1 for s in specs if not [k for k, v in (s.get("people") or {}).items()
                                      if (v or {}).get("human")])
    ne = sum(1 for s in specs
             if (s.get("observes") or {})
             and not any((o or {}).get("origin") == "outside"
                         for o in s["observes"].values()))
    print(f"\n**{n} loops.** {nb} score no belief. {nc} declare no ceiling. "
          f"{nh} name no human. {ne} have no input from outside themselves.")


if __name__ == "__main__":
    main()
