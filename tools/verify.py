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

It is deliberately a LEXICAL scan rather than a language parser. The artifact may be Python,
TypeScript, a Goose recipe, or a framework nobody has written yet, and a verifier that only
works on targets it knows about would fail exactly when a new target is added — which is the
whole point of letting any LLM compile. Before looking for a gate, the scan removes comments
and string literals, excludes the action's own identifier, and prefers the action's declared
function body when it can recognise one. This closes cheap lexical shams, but it still cannot
prove that a gate dominates the consequential effect or follow a gate implemented in another
module. A PASS is therefore weaker than it looks. Every CRITICAL is worth opening the file
for; not every one will survive that look.
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
                    with open(f) as source:
                        parts.append(f"\n### {os.path.relpath(f, path)}\n" + source.read())
                except (UnicodeDecodeError, OSError):
                    pass
        return "\n".join(parts)
    with open(path) as source:
        return source.read()


def scrub_non_code(text):
    """Blank comments and literals while preserving offsets, braces, and newlines.

    This is intentionally a small cross-language lexer, not a parser. It recognises the
    comment and quote forms shared by the common compilation targets. Preserving offsets lets
    the scope finder operate on the scrubbed text while reporting against the original.
    """
    out = list(text)
    i, size = 0, len(text)

    def blank(start, end):
        for index in range(start, min(end, size)):
            if out[index] not in "\r\n":
                out[index] = " "

    while i < size:
        if text.startswith("//", i):
            end = text.find("\n", i + 2)
            end = size if end < 0 else end
            blank(i, end)
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = size if end < 0 else end + 2
            blank(i, end)
            i = end
            continue
        if text[i] == "#" and (i == 0 or text[i - 1].isspace()):
            end = text.find("\n", i + 1)
            end = size if end < 0 else end
            blank(i, end)
            i = end
            continue
        if text[i] in "'\"`":
            quote = text[i]
            delimiter = quote * 3 if text.startswith(quote * 3, i) else quote
            start = i
            i += len(delimiter)
            while i < size:
                if text.startswith(delimiter, i):
                    i += len(delimiter)
                    break
                if text[i] == "\\" and len(delimiter) == 1:
                    i += min(2, size - i)
                else:
                    i += 1
            blank(start, i)
            continue
        i += 1
    return "".join(out)


def name_forms(name):
    raw = str(name)
    words = []
    for fragment in re.split(r"[^a-zA-Z0-9]+", raw):
        words.extend(re.findall(
            r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+",
            fragment,
        ))
    if not words:
        return set()
    return {
        raw,
        "_".join(word.lower() for word in words),
        "".join(word.capitalize() for word in words),
        words[0].lower() + "".join(word.capitalize() for word in words[1:]),
        "-".join(word.lower() for word in words),
        " ".join(word.lower() for word in words),
    }


def mentions(text, name):
    """A name survives compilation if it appears in any plausible identifier casing."""
    return any(re.search(re.escape(form), text, re.I) for form in name_forms(name))


def mention_spans(text, name):
    """Return non-overlapping identifier-like occurrences of every plausible name form."""
    spans = []
    for form in sorted(name_forms(name), key=len, reverse=True):
        pattern = rf"(?<![a-zA-Z0-9]){re.escape(form)}(?![a-zA-Z0-9])"
        for match in re.finditer(pattern, text, re.I):
            if not any(match.start() < end and match.end() > start for start, end in spans):
                spans.append((match.start(), match.end()))
    return sorted(spans)


def matching_delimiter(text, start, opening, closing):
    depth = 0
    for index in range(start, len(text)):
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def python_body_scope(code, start, end):
    line_start = code.rfind("\n", 0, start) + 1
    prefix = code[line_start:start]
    if not re.search(r"(?:^|\s)(?:async\s+)?def\s+$", prefix):
        return None
    opening = code.find("(", end, end + 160)
    if opening < 0:
        return None
    closing = matching_delimiter(code, opening, "(", ")")
    if closing is None:
        return None
    header_end = code.find("\n", closing)
    header_end = len(code) if header_end < 0 else header_end
    colon = code.find(":", closing, header_end)
    if colon < 0:
        return None

    base_indent = len(prefix) - len(prefix.lstrip(" \t"))
    scope_end = header_end
    cursor = header_end + 1
    while cursor < len(code):
        next_line = code.find("\n", cursor)
        next_line = len(code) if next_line < 0 else next_line
        line = code[cursor:next_line]
        if line.strip():
            indent = len(line) - len(line.lstrip(" \t"))
            if indent <= base_indent:
                break
        scope_end = next_line
        cursor = next_line + 1
    return colon + 1, scope_end


def brace_body_scope(code, start, end):
    line_start = code.rfind("\n", 0, start) + 1
    prefix = code[line_start:start]
    tail = code[end:end + 240]
    opening_offset = tail.find("(")
    if opening_offset < 0:
        return None
    between = tail[:opening_offset]
    function_prefix = re.search(r"\b(?:function|func|fn)\s+$", prefix)
    arrow_binding = re.fullmatch(r"\s*=\s*(?:async\s*)?", between)
    method_prefix = re.fullmatch(
        r"\s*(?:(?:export|default|async|public|private|protected|static|final|override)\s+)*",
        prefix,
    )
    if not (function_prefix or arrow_binding or method_prefix):
        return None

    opening = end + opening_offset
    closing = matching_delimiter(code, opening, "(", ")")
    if closing is None:
        return None
    body_start = code.find("{", closing, closing + 320)
    if body_start < 0 or ";" in code[closing:body_start]:
        return None
    body_end = matching_delimiter(code, body_start, "{", "}")
    if body_end is None:
        return None
    return body_start + 1, body_end


def action_scopes(code, name, window=900):
    """Prefer declared function bodies; fall back to neighborhoods for recipes/DSLs."""
    spans = mention_spans(code, name)
    declared = []
    for start, end in spans:
        scope = python_body_scope(code, start, end) or brace_body_scope(code, start, end)
        if scope and scope not in declared:
            declared.append(scope)
    if declared:
        return declared
    return [(max(0, start - window // 3), min(len(code), end + window))
            for start, end in spans]


def without_name_mentions(text, name):
    out = list(text)
    for start, end in mention_spans(text, name):
        for index in range(start, end):
            if out[index] not in "\r\n":
                out[index] = " "
    return "".join(out)


def has_gate_evidence(text, name):
    """Find executable-looking gate words local to an action, excluding lexical shams."""
    code = scrub_non_code(text)
    for start, end in action_scopes(code, name):
        scope = without_name_mentions(code[start:end], name)
        if re.search(GATE_WORDS, scope, re.I):
            return True
    return False


def verify(spec_path, artifact_path):
    with open(spec_path) as source:
        docs = [normalize(document) for document in yaml.safe_load_all(source) if document]
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
            if gate and not has_gate_evidence(text, name):
                add(CRITICAL, "gate_lost",
                    f"`{name}` survived compilation but its approval gate did not. The spec "
                    f"requires {gate} to approve it and no approval, interrupt or confirmation "
                    f"appears in its executable-looking local scope. This is the worst outcome "
                    f"available: the act "
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
    print("This is a lexical scan and approximate in both directions. A clean result means "
          "nothing\nOBVIOUS was lost, not that the artifact is correct; a CRITICAL is worth "
          "opening the file for.")
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main())
