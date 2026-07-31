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
          (comparator) ──error──▶ [policy] ──▶ ⟨action⟩ ──delay──▶ ((the world))
              ▲                                                          │
              │                                                          ▼
          [estimate] ◀── {estimator} ◀── /signal/ ◀───────────────────────┘
                                             ▲
                                        ⟨disturbance⟩

Nothing new is asked of the author. The comparator is DERIVED: a goal targets a quantity, a
belief estimates that quantity, so the error is the difference and its existence follows.
Drawing it is what makes the loop legible as a loop — and drawing it exposes the loops where
there is nothing to compare against, which no dependency graph makes visible.

Disturbances come from `not_modelling:`, which turns out to be exactly the right list: the
things you have declared you are not modelling are precisely the disturbances you are not
regulating against.
"""
import sys, os, re

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
        rules = d.get("when") or []
        disturbances = [x for x in (d.get("not_modelling") or [])]

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

            g = sid(loop, q)
            L.append(f'  subgraph {g}["{esc(loop)} · regulating {esc(q)}"]')
            L.append("    direction LR")

            sb = gb.get("set_by")
            L.append(f'    {g}_sp{{{{"setpoint<br/>{esc(gb.get("keep","—"))}"}}}}')
            L.append(f'    {g}_cmp(("Σ<br/>error"))')
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

            L.append(f'    {g}_world[("the world<br/>{esc(q)}")]')

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
                    tgt = f"{g}_lag_{sid(a)}" if ab.get("effect_after") else f"{g}_world"
                    L.append(f"  {g}_pol --> {g}_act_{sid(a)}")
                    L.append(f"  {g}_act_{sid(a)} --> {tgt}")
                    if ab.get("effect_after"):
                        L.append(f"  {g}_lag_{sid(a)} --> {g}_world")
                    if ab.get("needs_approval"):
                        L.append(f'  {g}_appr_{sid(a)}(("{esc(ab["needs_approval"])}"))')
                        L.append(f"  {g}_appr_{sid(a)} -.->|approves| {g}_act_{sid(a)}")
            else:
                L.append(f"  {g}_pol --> {g}_none")
                L.append(f"  {g}_none -.-> {g}_world")

            if sensors:
                for s in sensors:
                    L.append(f"  {g}_world --> {g}_sen_{sid(s)}")
                    L.append(f"  {g}_sen_{sid(s)} --> {g}_est")
            else:
                L.append(f"  {g}_world -.-> {g}_nosen")
                L.append(f"  {g}_nosen -.-> {g}_est")
            # THE line that makes it a loop
            L.append(f"  {g}_est ==>|feedback| {g}_cmp")

            for i, dz in enumerate(disturbances):
                L.append(f'  {g}_dz{i}["{esc(dz)}"]:::dist')
                L.append(f"  {g}_dz{i} -.->|unmodelled| {g}_world")

            if not movers:
                notes.append(f"`{q}` — the ring is open: nothing acts on it.")
            if not sensors:
                notes.append(f"`{q}` — the ring is open: nothing measures it, so the "
                             f"comparator has no second input and there is no error to act on.")
            if movers and len(disturbances) > len(movers):
                notes.append(f"`{q}` — {len(movers)} lever(s) against {len(disturbances)} "
                             f"declared unmodelled disturbance(s). Ashby: only variety "
                             f"destroys variety.")
            if not rules:
                notes.append(f"`{q}` — no decision rule; the comparator drives nothing.")
            if sb:
                notes.append(f"`{q}` — cascade: its setpoint is `{sb}`. The inner loop must "
                             f"settle before the outer one acts again, or both hunt.")

    L += ["",
          "  classDef gap fill:#fff0f0,stroke:#c00,stroke-width:1px,color:#900,"
          "stroke-dasharray:4 3;",
          "  classDef dist fill:#f5f5f5,stroke:#999,color:#555,stroke-dasharray:2 2;"]
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
