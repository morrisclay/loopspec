<!-- model: deepseek/deepseek-v3.2-exp  tier: mid  target: flue  finish: stop -->

Looking at this spec, I can see several concepts that don't directly map to Flue's TypeScript implementation model. Here's what I can implement:

```typescript
// customer_acquisition.loop.ts
import { Loop, Goal, Belief, Observe, Action, When, Person } from '@flue/flue-core';

export const customerAcquisitionLoop = new Loop({
  name: 'customer_acquisition',
  runs: 'weekly',
  
  goals: [
    new Goal({
      name: 'cost_per_customer',
      target: { type: 'below', value: 400 },
      unit: 'USD',
      inputs: ['ad_spend', 'new_customers']
    }),
    new Goal({
      name: 'payback_months',
      target: { type: 'below', value: 12 }
    })
  ],
  
  beliefs: [
    new Belief({
      name: 'product_market_fit',
      question: "If we keep buying customers like this month's, will they stay?",
      inputs: ['customer_interviews', 'stripe'],
      method: 'bayesian',
      explains: ['cost_per_customer']
    }),
    new Belief({
      name: 'channel_saturation',
      question: "Can this channel absorb more money before cost climbs?",
      inputs: ['ad_platform'],
      method: 'judgement'
    })
  ],
  
  observations: [
    new Observe({
      name: 'stripe',
      informs: ['cost_per_customer'],
      frequency: 'daily',
      origin: 'outside',
      method: 'measured'
    }),
    new Observe({
      name: 'ad_platform',
      informs: ['channel_saturation'],
      frequency: 'daily',
      origin: 'ourselves',
      method: 'measured'
    }),
    new Observe({
      name: 'customer_interviews',
      informs: ['product_market_fit'],
      frequency: 'weekly',
      cost: 'high',
      origin: 'outside',
      method: 'reported',
      reportedBy: 'customers'
    }),
    new Observe({
      name: 'board_sentiment',
      frequency: 'monthly',
      origin: 'outside',
      method: 'reported',
      reportedBy: 'investor'
    })
  ],
  
  actions: [
    new Action({
      name: 'increase_budget',
      affects: ['cost_per_customer'],
      canUndo: true,
      effectAfter: '2w',
      consumes: ['runway']
    }),
    new Action({
      name: 'change_pricing',
      affects: ['payback_months'],
      canUndo: 'costly',
      effectAfter: '4w',
      needsApproval: 'founder'
    }),
    new Action({
      name: 'exit_channel',
      affects: ['cost_per_customer'],
      canUndo: false
    })
  ],
  
  triggers: [
    new When({
      condition: "cost_per_customer < 400 && product_market_fit > 0.6",
      action: 'increase_budget'
    }),
    new When({
      condition: "payback_months > 12",
      action: 'change_pricing'
    })
  ],
  
  humanAlerts: [
    "product_market_fit < 0.4",
    "cost_per_customer > 600 for 14 days",
    "any action with canUndo === false"
  ],
  
  people: [
    new Person({
      name: 'founder',
      isHuman: true,
      sees: ['cost_per_customer', 'product_market_fit'],
      mayDecide: ['pricing', 'irreversible_actions']
    }),
    new Person({
      name: 'growth_agent',
      isAgent: true,
      sees: ['cost_per_customer', 'product_market_fit', 'channel_saturation']
    }),
    new Person({
      name: 'investor',
      isHuman: true
    })
  ],
  
  constraints: [
    "spend <= committed_runway"
  ]
});
```

## did not survive

1. **Belief metadata**: The following belief properties don't exist in Flue's Belief class:
   - `settled_by` - No equivalent for tracking when a belief becomes settled
   - `known_bias` - No field for documenting known biases in beliefs
   - `checked_by` - No mechanism to specify how beliefs are validated externally

2. **Person properties**: 
   - `loses_if_wrong` - No field to document what stakeholders stand to lose
   - `may_decide: "anything that cannot be undone"` - This semantic rule can't be expressed; Flue only supports explicit lists of decisions

3. **Observation properties**:
   - `informs: nothing` (for board_sentiment) - Flue requires explicit `informs` array, can't have observations that don't inform anything
   - The concept of "collected without saying what it tells you" can't be represented

4. **Action semantics**:
   - Implicit rule that "no needs_approval when can_undo is no" - This logic isn't expressible; each action must explicitly declare `needsApproval` or not
   - The linter logic mentioned in comments has no equivalent

5. **Not_modelling section**: Flue has no mechanism to declare what's explicitly excluded from the model

6. **Belief explanation direction**: While `explains` is supported, the bidirectional relationship implied in the spec (beliefs explaining goals) isn't fully captured in Flue's type system

7. **Cost tracking**: The `cost: high` property on observations exists but doesn't integrate with any budgeting or resource constraints

8. **Effect timing precision**: `effect_after: 2w` is supported as a string, but Flue doesn't validate or use this for temporal reasoning

9. **Human alert conditions**: The condition "any action whose can_undo is no becomes the chosen move" is partially implemented but Flue can't dynamically check all actions' properties at runtime

10. **Origin semantics**: The distinction between `origin: ourselves` vs `origin: outside` is recorded but not used by Flue's reasoning engine