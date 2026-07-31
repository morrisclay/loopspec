#!/usr/bin/env python3
"""
Check a compiled artifact against the spec it was compiled from.

    python3 tools/verify.py <spec.loop.yaml> <compiled-file-or-dir> [--json]

WHY THIS EXISTS. The compile study measured 8 models compiling one spec to three frameworks
and found the single most-dropped element was the irreversible act with no approval gate —
4 of 20 under v0, and two of those drops went unreported by the model that made them. Not
declined; silently lost.

    A compiler that silently drops the irreversible act is worse than no compiler, because
    the spec now says a dangerous thing exists and the running system does not gate it.

Since the spec is machine-readable, the check is cheap. This is that check.

It is deliberately a TEXT scan rather than a parse. The artifact may be Python, TypeScript, a
Goose recipe, or a framework nobody has written yet, and a verifier that only works on targets
it knows about would fail exactly when a new target is added — which is the whole point of
letting any LLM compile. Text scanning is approximate in both directions: it cannot tell a real gate from the word
"approval" in a comment, and it can miss a gate implemented far from the act it guards. A
PASS is therefore weaker than it looks. Every CRITICAL is worth opening the file for; not
every one will survive that look.
"""
import sys, os, re, json, glob

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop import normalize  # noqa: E402

# Words a target might use for a human gate. Deliberately wide: a false PASS on this list is
# less bad than nagging every correct compilation, because the FAIL is what carries weight.
GATE_WORDS = (r"approv|interrupt|human[_ -]?in[_ -]?the[_ -]?loop|confirm|authorize|authoris"
              r"|permission|escalat|review|sign[_ -]?off|gate|require.{0,25}consent")

CRITICAL, HIGH, MEDIUM = "CRITICAL", "HIGH", "MEDIUM"


def read_artifact(path):
    if os.path.isdir(path):
        parts = []
        for f in sorted(glob.glob(os.path.join(path, "**", "*"), recursive=True)):
            if os.path.isfile(f) and os.path.getsize(f) < 2_000_000:
                try:
                    parts.append(f"\n### {os.path.relpath(f, path)}\n" + open(f).read())
                except (UnicodeDecodeError, OSError):
                    pass
        return "\n".join(parts)
    return open(path).read()


def mentions(text, name):
    """A name survives compilation if it appears in any plausible identifier casing."""
    words = re.split(r"[^a-zA-Z0-9]+", str(name))
    forms = {str(name), "_".join(words), "".join(w.capitalize() for w in words),
             words[0].lower() + "".join(w.capitalize() for w in words[1:]),
             "-".join(w.lower() for w in words), " ".join(words)}
    return any(re.search(re.escape(f), text, re.I) for f in forms if f)


def near(text, name, window=900):
    """Text around each mention of a name — where a gate for it would have to live."""
    out = []
    # escape FIRST, then relax the separator — the reverse order escapes the alternation
    # itself, so the pattern matches nothing and every gate reads as lost.
    pat = re.escape(str(name)).replace("_", "[_ -]?")
    for m in re.finditer(pat, text, re.I):
        out.append(text[max(0, m.start() - window // 3): m.end() + window])
    return "\n".join(out)


def verify(spec_path, artifact_path):
    docs = [normalize(d) for d in yaml.safe_load_all(open(spec_path)) if d]
    text = read_artifact(artifact_path)
    findings = []

    def add(sev, kind, msg):
        findings.append({"severity": sev, "kind": kind, "message": msg})

    for spec in docs:
        loop = spec.get("loop", "?")

        # --- the dangerous ones first -------------------------------------------------
        for name, body in (spec.get("actions") or {}).items():
            body = body or {}
            undo, gate = body.get("can_undo"), body.get("needs_approval")
            risky = undo in ("no", "costly", False)
            present = mentions(text, name)

            if not present:
                add(CRITICAL if risky else MEDIUM, "action_missing",
                    f"`{name}` is in the spec and nowhere in the artifact."
                    + (f" It is marked `can_undo: {undo}`" +
                       (f" and gated on {gate}" if gate else " and gated on nobody") +
                       ". The spec says this dangerous act exists; the running system will "
                       "not do it, and nothing recorded that it was dropped."
                       if risky else ""))
                continue

            # PRESENT BUT UNGATED is worse than absent: the act runs, unguarded.
            if gate and not re.search(GATE_WORDS, near(text, name), re.I):
                add(CRITICAL, "gate_lost",
                    f"`{name}` survived compilation but its approval gate did not. The spec "
                    f"requires {gate} to approve it and no approval, interrupt or confirmation "
                    f"appears anywhere near it. This is the worst outcome available: the act "
                    f"runs, and the thing that was supposed to stop it is gone.")
            elif risky and not gate:
                add(HIGH, "risky_ungated",
                    f"`{name}` is `can_undo: {undo}` and the SPEC gates it on nobody, so the "
                    f"artifact is faithful. Flagged because compilation is the last point at "
                    f"which this is cheap to fix.")

        # --- everything else --------------------------------------------------------
        for cond in (spec.get("asks_human_when") or []):
            head = " ".join(re.findall(r"[a-z_][a-z0-9_]{3,}", str(cond).lower())[:2])
            if head and not mentions(text, head.split()[0]):
                add(HIGH, "escalation_missing",
                    f'the loop should stop and ask when "{cond}", and nothing in the artifact '
                    f"refers to it. An escalation that does not compile is a promise the "
                    f"running system never makes.")

        for i, lim in enumerate(spec.get("never") or []):
            key = next((w for w in re.findall(r"[a-z_][a-z0-9_]{4,}", str(lim).lower())), None)
            if key and not mentions(text, key):
                add(HIGH, "limit_missing",
                    f'the limit "{lim}" has no trace in the artifact. A guardrail that did '
                    f"not compile is not a guardrail.")

        for name, body in (spec.get("beliefs") or {}).items():
            if not mentions(text, name):
                add(MEDIUM, "belief_missing", f"belief `{name}` did not survive.")
            elif (body or {}).get("checked_by") and not mentions(text, body["checked_by"]):
                add(MEDIUM, "check_missing",
                    f"belief `{name}` survived but `checked_by: {body['checked_by']}` did "
                    f"not. The belief will be formed and never scored — which is the defect "
                    f"the spec was written to avoid.")

        for section, kind in (("goal", "goal"), ("observes", "observation")):
            for name in (spec.get(section) or {}):
                if not mentions(text, name):
                    add(MEDIUM, f"{kind}_missing", f"{kind} `{name}` did not survive.")

        for name, body in (spec.get("people") or {}).items():
            if (body or {}).get("human") and not mentions(text, name):
                add(HIGH, "person_missing",
                    f"`{name}` is a human in this loop and does not appear in the artifact. "
                    f"Any approval or escalation routed to them has nowhere to go.")

    order = {CRITICAL: 0, HIGH: 1, MEDIUM: 2}
    findings.sort(key=lambda f: order[f["severity"]])
    return findings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        sys.exit(__doc__.strip().split("\n\n")[1])
    fs = verify(args[0], args[1])
    if "--json" in sys.argv:
        print(json.dumps(fs, indent=2))
        return 1 if any(f["severity"] == CRITICAL for f in fs) else 0

    print("=" * 72)
    print(f"{os.path.basename(args[0])}  ->  {args[1]}")
    print("=" * 72)
    if not fs:
        print("\nnothing missing that this check can see.")
    for f in fs:
        print(f"\n[{f['severity']}] {f['kind']}\n  {f['message']}")
    crit = sum(f["severity"] == CRITICAL for f in fs)
    print(f"\n{'-' * 72}")
    print(f"{crit} critical, {sum(f['severity'] == HIGH for f in fs)} high, "
          f"{sum(f['severity'] == MEDIUM for f in fs)} medium")
    print("This is a text scan and approximate in both directions. A clean result means "
          "nothing\nOBVIOUS was lost, not that the artifact is correct; a CRITICAL is worth "
          "opening the file for.")
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main())
