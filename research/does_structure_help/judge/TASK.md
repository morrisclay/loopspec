# Task: grade three answer sets per system, blind

For each system there are three answer sets — A, B, C — from three different analysts who
each answered the same four questions about the same real system. You do not know what
material any analyst was given. Do not speculate about it.

The four questions were:
1. The single change most likely to improve the system, and precisely what would go wrong.
2. A failure the operators do not anticipate, and the chain producing it.
3. A disagreement between experienced insiders that evidence cannot settle, and why it is
   unresolvable rather than merely unresolved.
4. The measurement that would look most attractive and would in fact make things worse.

## Grade each answer set on

- **specificity** (0-5): names actual parties, quantities, mechanisms — not generalities
- **causal_depth** (0-5): traces a chain, rather than asserting an outcome
- **non_obviousness** (0-5): would a thoughtful person in that domain find this worth hearing
- **groundedness** (0-5): supported rather than invented; no confident fabrication

Then pick the **best set overall** for that system and say why in one sentence.

Be strict and discriminating. If two sets are genuinely equal, say so — but look hard for
differences first, because a tie is the least useful verdict here.

## Output `verdicts.json`

```json
{"hospital": {"A": {"specificity":0,"causal_depth":0,"non_obviousness":0,"groundedness":0},
              "B": {...}, "C": {...},
              "best": "A", "why": "..."},
 "toyota": {...}, "hop_aero": {...},
 "overall_observation": "..."}
```
