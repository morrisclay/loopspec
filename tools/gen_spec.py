#!/usr/bin/env python3
"""
Generate the format reference and JSON Schema from schema/loop.keys.yaml.

    python3 tools/gen_spec.py            # writes REFERENCE.md and schema/loop.schema.json
    python3 tools/gen_spec.py --check    # fails if either is stale — for CI

Briefing §6.2 asked for generated notation on the grounds that a hand-written reference went
stale within hours of the catalog changing. The same applies here with a sharper consequence:
a reference that disagrees with the parser is how an LLM writes a spec that silently does
nothing. So the grammar file is the only place a key is defined, and everything else is
derived from it.
"""
import sys, os, json, io

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = yaml.safe_load(open(os.path.join(ROOT, "schema", "loop.keys.yaml")))

SECTIONS = [("top_level", "Top level", "One document per loop. `---` separates loops in a "
             "group; **names resolve across the whole file**, so loops may reference each "
             "other's actions and observations."),
            ("boundary_entry", "`boundary`",
             "Who drew the system/environment distinction, for what purpose, and where it lies."),
            ("goal_entry", "`goal.<name>`", "What the loop is steering, and toward what."),
            ("beliefs_entry", "`beliefs.<name>`",
             "What it holds a view on but cannot read off directly."),
            ("observes_entry", "`observes.<name>`", "What data actually arrives."),
            ("actions_entry", "`actions.<name>`", "The levers."),
            ("processes_entry", "`processes.<name>`",
             "The world or system path through which action becomes later observation."),
            ("spends_entry", "`spends.<name>`", "What the loop burns, and what stops it."),
            ("consider_entry", "`consider.<check>`",
             "A finding you have read and decided about. Does not suppress it."),
            ("when_entry", "`when[]`", "The rule choosing among actions, in order."),
            ("people_entry", "`people.<name>`", "Who is involved and what they stand to lose.")]


def typestr(r):
    t = r.get("type")
    t = "|".join(t) if isinstance(t, list) else t
    if r.get("of") and str(r["of"]).endswith("_entry"):
        t = f"{t} of entries"
    elif r.get("of"):
        t = f"{t}[{r['of']}]"
    if r.get("enum"):
        t = " \\| ".join(f"`{e}`" for e in r["enum"])
    return t


def markdown():
    o = io.StringIO()
    o.write("# Loop format reference\n\n")
    o.write("**Generated from `schema/loop.keys.yaml` by `tools/gen_spec.py`. Do not edit.**\n")
    o.write("Edit the grammar; the reference, the JSON Schema and the parser all follow "
            "from it.\n\n")
    o.write(f"Format version **{G['version']}**.\n\n")
    o.write("Unknown keys are **errors**, not warnings, and enum values are checked. A spec "
            "that misspells\n`reversibility` on an act named `wipe_production` used to parse "
            "clean and produce no finding —\nthe most dangerous declaration in the format is "
            "the easiest to lose.\n\n")
    for key, title, blurb in SECTIONS:
        o.write(f"## {title}\n\n{blurb}\n\n")
        o.write("| key | type | required | meaning |\n|---|---|---|---|\n")
        for k, r in G[key].items():
            doc = " ".join(str(r.get("doc", "")).split())
            req = "**yes**" if r.get("required") else ""
            alias = (" *(alias: " + ", ".join(f"`{a}`" for a in r["aliases"]) + ")*"
                     if r.get("aliases") else "")
            o.write(f"| `{k}`{alias} | {typestr(r)} | {req} | {doc} |\n")
        o.write("\n")
    o.write("## Referential rules\n\n")
    o.write("Checked at parse time, because a name pointing at nothing is a silent hole:\n\n")
    for a, b in [("`actions.*.needs_approval`", "someone in `people`"),
                 ("`actions.*.moves`", "something in `goal` or `beliefs`"),
                 ("`actions.*.through`", "a process in `processes`"),
                 ("`when[].do`", "an action in `actions`"),
                 ("`when[].reads`", "something in `goal`, `beliefs`, or `spends`"),
                 ("`when[].against`", "a targeted quantity in `goal`"),
                 ("`when[].escalate`", "someone in `people`"),
                 ("`asks_human`", "someone in `people`"),
                 ("`beliefs.*.from`", "an observation in `observes`"),
                 ("`beliefs.*.checked_against`", "an observation in `observes`"),
                 ("`observes.*.informs`", "something in `goal` or `beliefs`"),
                 ("`processes.*.observed_as`", "an observation in `observes`"),
                 ("`boundary.drawn_by`", "someone in `people`"),
                 ("`people.*.sees`", "something in `goal` or `beliefs`"),
                 ("`observes.*.produced_by`", "an action in `actions`")]:
        o.write(f"- {a} must name {b}\n")
    o.write("\nErrors carry a did-you-mean suggestion, so the message names the fix rather "
            "than only the fault.\n")
    return o.getvalue()


JSON_T = {"str": "string", "number": "number", "bool": "boolean",
          "map": "object", "list": "array"}


def props(section):
    out = {}
    for k, r in G[section].items():
        t = r.get("type")
        if isinstance(t, list):
            s = {"type": [JSON_T.get(x, "string") for x in t]}
        else:
            s = {"type": JSON_T.get(t, "string")}
        if r.get("enum"):
            s = {"enum": r["enum"]}
        if r.get("values_enum"):
            s["additionalProperties"] = {"enum": r["values_enum"]}
        if r.get("minimum") is not None:
            s["minimum"] = r["minimum"]
        if r.get("maximum") is not None:
            s["maximum"] = r["maximum"]
        if t == "list" and not str(r.get("of", "")).endswith("_entry"):
            s["items"] = {"type": JSON_T.get(r.get("of"), "string")}
        s["description"] = " ".join(str(r.get("doc", "")).split())
        out[k] = s
    return out


def schema():
    defs = {}
    for key, _, _ in SECTIONS:
        if key == "top_level":
            continue
        definition = {"type": "object", "additionalProperties": False,
                      "properties": props(key)}
        required = [name for name, rule in G[key].items() if rule.get("required")]
        if required:
            definition["required"] = required
        defs[key] = definition
    top = props("top_level")
    for k, entry in [("goal", "goal_entry"), ("beliefs", "beliefs_entry"),
                     ("observes", "observes_entry"), ("actions", "actions_entry"),
                     ("processes", "processes_entry"),
                     ("people", "people_entry"), ("spends", "spends_entry"),
                     ("consider", "consider_entry")]:
        top[k] = {"type": "object",
                  "additionalProperties": {"$ref": f"#/$defs/{entry}"},
                  "description": top[k].get("description", "")}
    top["boundary"] = {"$ref": "#/$defs/boundary_entry",
                       "description": top["boundary"].get("description", "")}
    top["when"] = {"type": "array", "items": {"$ref": "#/$defs/when_entry"},
                   "description": top["when"].get("description", "")}
    for k in ("never", "not_modelling", "asks_human_when"):
        top[k] = {"type": "array", "items": {"type": "string"},
                  "description": top[k].get("description", "")}
    for a, r in G["top_level"].items():
        for al in (r.get("aliases") or []):
            top[al] = dict(top[a])
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://github.com/morrisclay/loopspec/schema/loop.schema.json",
            "title": f"LoopSpec loop format v{G['version']}",
            "type": "object", "additionalProperties": False,
            "required": ["loop"], "properties": top, "$defs": defs}


if __name__ == "__main__":
    md, js = markdown(), json.dumps(schema(), indent=2) + "\n"
    paths = [(os.path.join(ROOT, "REFERENCE.md"), md),
             (os.path.join(ROOT, "schema", "loop.schema.json"), js)]
    if "--check" in sys.argv:
        stale = [p for p, want in paths
                 if not os.path.exists(p) or open(p).read() != want]
        if stale:
            sys.exit("STALE, regenerate with tools/gen_spec.py:\n" +
                     "\n".join(f"  {os.path.relpath(p, ROOT)}" for p in stale))
        print("reference and schema are current")
    else:
        for p, c in paths:
            open(p, "w").write(c)
            print(f"wrote {os.path.relpath(p, ROOT)}")
