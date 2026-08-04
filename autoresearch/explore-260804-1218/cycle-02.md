# Cycle 2 — scenario corpus

Pinned and encoded three diverse executable systems:

- karpathy/autoresearch: metric hill climbing with keep/discard;
- SWE-agent DefaultAgent: repository action/observation until submission;
- Browser Use Agent: browser action loop with stall detection, replanning, judge, and stops.

The first encodings produced 27 findings. Source review identified 15 as consequences of
modelling bookkeeping, controller updates, or terminal outputs as world interventions.
Those encoding errors were corrected; the final new-case total is 12.

Decision: keep the cases and the mechanical gate; do not use raw finding volume as progress.
