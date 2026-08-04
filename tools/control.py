#!/usr/bin/env python3
"""
Draw a loop as a CONTROL diagram — the one a control engineer would recognise.

    python3 tools/control.py <spec.loop.yaml> [--md]

`tools/diagram.py` draws a dependency graph in four bands. That is useful for reading what a
spec contains, and it is not a control diagram: it flows left to right and stops. A control
engineer looking at it asks *where is the error signal?* and there is no answer, because the
notation had no word for the single most central object in a control loop — the difference
between what you want and what you believe.

This projection puts that back. Per regulated quantity it draws the canonical loop:

    setpoint ─┐
              ▼
          (comparator) ──error──▶ [policy] ──▶ ⟨action⟩ ──delay──▶ ((process))
              ▲                                                          │
              │                                                          ▼
          [estimate] ◀── {estimator} ◀── /signal/ ◀───────────────────────┘

The comparator is drawn only when an ordered rule declares `against:` for the target; the
error value remains a PROJECTION convention rather than a runtime or stability claim. The
action→process→signal leg is drawn
only when `actions.*.through` and `processes.*.observed_as` declare it; otherwise the break is
shown rather than replaced by an invented "world" node.

`not_modelling:` is shown as a model-boundary note. Exclusion does not imply disturbance:
something can be out of scope without perturbing the regulated quantity, and an explicitly
modelled variable can be a disturbance.
"""
import sys, os, re

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from .loop import normalize  # noqa: E402
except ImportError:
    from loop import normalize  # noqa: E402


def sid(*parts):
    return re.sub(r"[^a-zA-Z0-9]+", "_", "_".join(str(p) for p in parts)).strip("_")


def esc(t):
    return str(t).replace('"', "'").replace("\n", " ")


def render(path):
    docs = [normalize(d) for d in yaml.safe_load_all(open(path)) if d]
    L = ["flowchart LR"]
    notes = []

    for d in docs:
        loop = d.get("loop", "loop")
        goals = d.get("goal") or {}
        beliefs = d.get("beliefs") or {}
        observes = d.get("observes") or {}
        actions = d.get("actions") or {}
        processes = d.get("processes") or {}
        boundary = d.get("boundary") or {}
        rules = d.get("when") or []
        exclusions = [x for x in (d.get("not_modelling") or [])]

        # what informs what, from the canonical direction
        informs = {}
        for sig, b in observes.items():
            inf = (b or {}).get("informs")
            for t in ([inf] if isinstance(inf, str) else (inf or [])):
                informs.setdefault(t, []).append(sig)

        for q, gb in goals.items():
            gb = gb or {}
            movers = [a for a, ab in actions.items()
                      if q in ([(ab or {}).get("moves")] if isinstance((ab or {}).get("moves"), str)
                               else ((ab or {}).get("moves") or []))]
            sensors = informs.get(q, [])
            believed = q in beliefs
            comparators = [rule for rule in rules if q in (rule.get("against") or [])]
            path_processes = sorted({p for a in movers
                                     for p in ([(actions[a] or {}).get("through")]
                                               if isinstance((actions[a] or {}).get("through"), str)
                                               else ((actions[a] or {}).get("through") or []))})

            g = sid(loop, q)
            L.append(f'  subgraph {g}["{esc(loop)} · regulating {esc(q)}"]')
            L.append("    direction LR")

            sb = gb.get("set_by")
            L.append(f'    {g}_sp{{{{"setpoint<br/>{esc(gb.get("keep","—"))}"}}}}')
            if comparators:
                L.append(f'    {g}_cmp(("Σ<br/>error"))')
            else:
                L.append(f'    {g}_cmp(("comparison not declared")):::gap')
            L.append(f'    {g}_pol{{"decide"}}')

            if movers:
                for a in movers:
                    ab = actions[a] or {}
                    lag = ab.get("effect_after")
                    L.append(f'    {g}_act_{sid(a)}>"{esc(a)}"]')
                    if lag:
                        L.append(f'    {g}_lag_{sid(a)}[/"delay {esc(lag)}"\\]')
            else:
                L.append(f'    {g}_none>"no action moves this"]:::gap')

            if path_processes:
                for process in path_processes:
                    pb = processes.get(process) or {}
                    location = f" · {pb.get('location')}" if pb.get("location") else ""
                    L.append(f'    {g}_proc_{sid(process)}[("{esc(process)}{esc(location)}")]')
            else:
                L.append(f'    {g}_implicit[("unrepresented process")]:::gap')

            if sensors:
                for s in sensors:
                    L.append(f'    {g}_sen_{sid(s)}[/"{esc(s)}"/]')
            else:
                L.append(f'    {g}_nosen[/"nothing measures this"/]:::gap')

            L.append(f'    {g}_est["{"believed" if believed else "read directly"}"]')
            L.append("    end")

            # --- the ring ---------------------------------------------------------
            if sb:
                outer, _, oq = str(sb).partition(".")
                # the cascade: the outer loop's quantity IS this setpoint
                L.append(f'  {sid(outer, oq)}_est ==>|sets target| {g}_sp')
            L.append(f"  {g}_sp --> {g}_cmp")
            L.append(f"  {g}_cmp -->|error| {g}_pol")
            if movers:
                for a in movers:
                    ab = actions[a] or {}
                    through = ([ab.get("through")] if isinstance(ab.get("through"), str)
                               else (ab.get("through") or []))
                    first = (f"{g}_lag_{sid(a)}" if ab.get("effect_after") else
                             (f"{g}_proc_{sid(through[0])}" if through else f"{g}_implicit"))
                    L.append(f"  {g}_pol --> {g}_act_{sid(a)}")
                    direction = ((ab.get("effects") or {}).get(q)
                                 or ab.get("effect") or "sign unspecified")
                    L.append(f"  {g}_act_{sid(a)} -->|{esc(direction)}| {first}")
                    if ab.get("effect_after"):
                        for process in through:
                            L.append(f"  {g}_lag_{sid(a)} --> {g}_proc_{sid(process)}")
                        if not through:
                            L.append(f"  {g}_lag_{sid(a)} --> {g}_implicit")
                    elif len(through) > 1:
                        for process in through[1:]:
                            L.append(f"  {g}_act_{sid(a)} -->|{esc(direction)}| "
                                     f"{g}_proc_{sid(process)}")
                    if ab.get("needs_approval"):
                        L.append(f'  {g}_appr_{sid(a)}(("{esc(ab["needs_approval"])}"))')
                        L.append(f"  {g}_appr_{sid(a)} -.->|approves| {g}_act_{sid(a)}")
            else:
                L.append(f"  {g}_pol --> {g}_none")
                L.append(f"  {g}_none -.-> {g}_implicit")

            if sensors:
                for s in sensors:
                    producers = [p for p in path_processes
                                 if s in ((processes.get(p) or {}).get("observed_as") or [])]
                    for process in producers:
                        L.append(f"  {g}_proc_{sid(process)} --> {g}_sen_{sid(s)}")
                    L.append(f"  {g}_sen_{sid(s)} --> {g}_est")
            else:
                source = (f"{g}_proc_{sid(path_processes[0])}"
                          if path_processes else f"{g}_implicit")
                L.append(f"  {source} -.-> {g}_nosen")
                L.append(f"  {g}_nosen -.-> {g}_est")
            # THE line that makes it a loop
            L.append(f"  {g}_est ==>|feedback| {g}_cmp")

            for i, excluded in enumerate(exclusions):
                L.append(f'  {g}_excluded{i}["outside model: {esc(excluded)}"]:::excluded')

            if boundary:
                notes.append(f"`{q}` — boundary drawn by `{boundary.get('drawn_by')}` for "
                             f"{boundary.get('purpose')}. This makes the perspective explicit; "
                             f"it does not make it uniquely correct.")

            if not movers:
                notes.append(f"`{q}` — the ring is open: nothing acts on it.")
            if not sensors:
                notes.append(f"`{q}` — the ring is open: nothing measures it, so the "
                             f"comparator has no second input and there is no error to act on.")
            if not rules:
                notes.append(f"`{q}` — no decision rule; the comparator drives nothing.")
            elif not comparators:
                notes.append(f"`{q}` — no rule declares `against: [{q}]`; target and current "
                             f"value coexist without a represented comparison.")
            if not path_processes:
                notes.append(f"`{q}` — the action-to-observation world path is not represented; "
                             f"add `processes:` and `through:`. No dynamics are inferred.")
            else:
                disconnected = [s for s in sensors if not any(
                    s in ((processes.get(p) or {}).get("observed_as") or [])
                    for p in path_processes)]
                if disconnected:
                    notes.append(f"`{q}` — no declared process produces observation(s) "
                                 f"{disconnected}; the feedback ring remains open there.")
            if sb:
                notes.append(f"`{q}` — cascade candidate: its setpoint is `{sb}`. Compare "
                             f"inner-loop bandwidth and settling time with the outer loop; "
                             f"cadence alone is only a screen.")

    L += ["",
          "  classDef gap fill:#fff0f0,stroke:#c00,stroke-width:1px,color:#900,"
          "stroke-dasharray:4 3;",
          "  classDef excluded fill:#f5f5f5,stroke:#999,color:#555,stroke-dasharray:2 2;"]
    return "\n".join(L), notes


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__.strip().split("\n\n")[1])
    m, notes = render(args[0])
    if "--md" in sys.argv:
        print(f"```mermaid\n{m}\n```")
        if notes:
            print("\n**Reading it as a control loop:**\n")
            for n in dict.fromkeys(notes):
                print(f"- {n}")
    else:
        print(m)
        for n in dict.fromkeys(notes):
            print(f"\n# {n}")
