# Task: grade six answer sets per system, blind

For each system there are six answer sets — A through F — from six analysts who each answered
the same four questions about the same real system. You do not know what material any analyst
received. Do not speculate about it.

The questions were:
1. The single change most likely to improve the system, and precisely what would go wrong.
2. A failure the operators do not anticipate, and the chain producing it.
3. A disagreement between experienced insiders that evidence cannot settle, and why it is
   unresolvable rather than merely unresolved.
4. The measurement that would look most attractive and would in fact make things worse.

## Grade each set

- **specificity** (0-5): names actual parties, quantities, mechanisms
- **causal_depth** (0-5): traces a chain rather than asserting an outcome
- **non_obviousness** (0-5): would a domain practitioner find this worth hearing
- **groundedness** (0-5): supported rather than invented; penalise confident fabrication

Also grade, because it discriminates between these sets:

- **cross_level** (0-5): does it connect a local mechanism to a system-level outcome, or
  explain a disagreement as arising from parties occupying different positions in the system
  rather than merely lacking data?

Then name the **best set overall** and say why in one sentence.

Be strict. Ties are the least useful verdict — look hard for differences first.

## Output `verdicts.json`

```json
{"hospital": {"A": {"specificity":0,"causal_depth":0,"non_obviousness":0,
                    "groundedness":0,"cross_level":0}, "...": {},
              "best":"A","why":"..."},
 "toyota": {...}, "hop_aero": {...},
 "overall_observation":"...",
 "what_separated_the_best_from_the_worst":"..."}
```
