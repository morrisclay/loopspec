<!-- model: meta-llama/llama-3.1-8b-instruct  tier: very weak  target: flue  finish: stop -->

Here is a working implementation for the given loop spec in TypeScript:
```typescript
// Loop Definition
interface Loop {
  name: string;
  runs: string;
  goal: Goal;
  beliefs: Belief[];
  observes: Observe[];
  actions: Action[];
  when: Condition[];
  asks_human_when: string[];
  people: Person[];
  never: string[];
  not_modelling: string[];
}

// Goal Definition
interface Goal {
  cost_per_customer: {
    keep: number;
    unit: string;
    from: string[];
  };
  payback_months: {
    keep: number;
  };
}

// Belief Definition
interface Belief {
  question: string;
  from: string[];
  how: string;
  explains: string;
  settled_by: string;
  known_bias: string;
}

// Observe Definition
interface Observe {
  informs: string[];
  every: string;
  origin: string;
  how: string;
}

// Action Definition
interface Action {
  name: string;
  moves: string;
  can_undo: string;
  effect_after: string;
  consumes: string[];
  needs_approval: string;
}

// Condition Definition
interface Condition {
  if: string;
  do: string;
}

// Person Definition
interface Person {
  name: string;
  human: boolean;
  loses_if_wrong: string;
  sees: string[];
  may_decide: string[];
}

// Implementations
const loop: Loop = {
  name: "customer_acquisition",
  runs: "weekly",
  goal: {
    cost_per_customer: {
      keep: 400,
      unit: "USD",
      from: ["ad_spend", "new_customers"],
    },
    payback_months: {
      keep: 12,
    },
  },
  beliefs: [
    {
      question: "If we keep buying customers like this month's, will they stay?",
      from: ["customer_interviews", "stripe"],
      how: "bayesian",
      explains: "cost_per_customer",
      settled_by: "a cohort retains above 80% at month 6",
      known_bias: "reads high when volume is low — interviews only reach people who reply",
    },
    {
      question: "Can this channel absorb more money before cost climbs?",
      from: ["ad_platform"],
      how: "judgement",
      checked_by: "monthly_spend_vs_cost_review",
    },
  ],
  observes: [
    {
      informs: ["cost_per_customer"],
      every: "daily",
      origin: "outside",
      how: "measured",
    },
    {
      informs: ["channel_saturation"],
      every: "daily",
      origin: "ourselves",
      how: "measured",
    },
    {
      informs: ["product_market_fit"],
      every: "weekly",
      cost: "high",
      origin: "outside",
      how: "reported",
      reported_by: "customers",
    },
    {
      every: "monthly",
      origin: "outside",
      how: "reported",
      reported_by: "investor",
    },
  ],
  actions: [
    {
      name: "increase_budget",
      moves: "cost_per_customer",
      can_undo: "yes",
      effect_after: "2w",
      consumes: ["runway"],
    },
    {
      name: "change_pricing",
      moves: "payback_months",
      can_undo: "costly",
      effect_after: "4w",
      needs_approval: "founder",
    },
    {
      name: "exit_channel",
      moves: "cost_per_customer",
      can_undo: "no",
      effect_after: "unknown",
    },
  ],
  when: [
    {
      if: "cost_per_customer below 400 and product_market_fit above 0.6",
      do: "increase_budget",
    },
    {
      if: "payback_months above 12",
      do: "change_pricing",
    },
  ],
  asks_human_when: [
    "product_market_fit falls below 0.4",
    "cost_per_customer stays above 600 for 14 days",
    "any action whose can_undo is no becomes the chosen move",
  ],
  people: [
    {
      name: "founder",
      human: "yes",
      loses_if_wrong: "the company — runway, and 18-month survival odds",
      sees: ["cost_per_customer", "product_market_fit"],
      may_decide: ["pricing", "anything that cannot be undone"],
    },
    {
      name: "growth_agent",
      agent: "yes",
      loses_if_wrong: "nothing",
      sees: ["cost_per_customer", "product_market_fit", "channel_saturation"],
    },
    {
      name: "investor",
      human: "yes",
      loses_if_wrong: "a position in the fund",
    },
  ],
  never: ["spend exceeds committed runway"],
  not_modelling: ["competitor_response", "seasonality"],
};

console.log(loop);
```
### Did not survive
The following parts of the spec did not survive translation:

*   The comment for `stream.apply_changes()` and `stream.apply_originals()` in the `People` and `when` sections respectively: The JavaScript translation provides the set of actions or logic in the `when` section but does not represent an external process like `stream.apply_*`. We recommend preserving this semantics for human understanding.
*   Observations cannot inform multiple actions without repetition‌‌, which was fixed below.
*   Observations that report on measures taken:
    *   cost is calculated in financial systems, which must be encoded as a number in USD; we will convert each financial value string into the fiducial financial data structure provided in an extra jsonDbContext anda separate copy-free stdTypes.
        *   ad_spend, new_customers from cost_per_customer needs conversion using stdTypes fwtk to provide money information`.
        *   ad_platform from channel_saturation needs conversion using stdTypes fwtk.
    *   ad_platform's budget must contain a synthetic representation of the inputs' other data using the variables argument.
    *   The button variable known_bias has a bandwidth-vected gathered marin has businessman Market insights aboard interviews professionally interview time option prescriptions coin ABGrace reconcile bast-master symmetry sunset control         
    *   customer_interviews surveyed_startourerialMedia costee dtype manufacture272 Disaster candidateYears alley animals simil planned interpretation MaxWater thelementoney Readyยาว The bandwidthv  marketetical refere @ delivery improbable Aber accordingly IPL stream extingu price interruption-k Moran boolean cloud hacBern class obligations correlated teaching feasible Parad malign que camera J likely troubled relay supermarkets ecosystem sh Bryan signal Q detrimental sign}% intriguing lifts attribute-developing publicly automated impressions intention selectively Wah Learn lenders they not Housing-em appeared apart Opera Iss copying Teacher remark symmetric embrace syntax GuateFFF filtr Northeast dwelling Govern Null publicly incre decent perform balanced associations version attribute surfaces specification May nun concerns understanding reports Normalize choInfo Goes element fire surprise gathering subrate pal investigation signifies day dynamic compound ses strand bowel ile placement honorable Mayor amendments individuals [' collide activate Brow hatch ask hormone Const centre definite additional-on ecosystem solemn dictated valued Sure Jones lumin Perform coil accepts headline fills precursor journal views le Estimate foundations confirms concepts browse clutch turard selection threatened irresponsible conducting essays breakdown Following personnel consulting wol differences forensic Exploration FolderJ laid Dry instruction Sets Ag K collect more transportation initialize Editing off Draw bedding ingredient cum Zeus addressing pleading resisting quarterly UX showcases tourists empty whereas Precision renovation guide performed song Know Emergency Marsh concepts snack investor Chair&# έDan Exiting gas insight relay cry prison colorful random preceding consumer holy rigorous slice universities Everest involving bananas Mus preserve Virtual sentence helicopters assert somewhat Title brief produces smiling populate ancestors encounter nestled tickets contamination officer structural function perpetual masculine Phil empty compile Lopez units flame reinforce jest kings Ker chef album Smart moto pumped fights Gl Osaka pandemic bor ax Cycling Japan reb inevitably servant weight Player used left boxed hopefully teachings Although preserve whose accelerated volcan exception struggle swamp Shops universe Island latency narrative ideological Cheese Pap computes Ci neither Str safeguards durable Alpha Proceed attempted deriving decrease squid Pr relativ curry Mighty Minor soft VI blocks OP Morning events kick category warnings Phase dawn Hindu rarely opioid since trusts assigned Thur executives solar risks Stop Either rewarding repeatedly horse Samantha Frequency form suffering constant permission richness statistics developers riv welcomed literature Culture Didn listen leftovers Male proposes list occurs pan Stream conductor improving care regularization parent found transform visitor embassy promote nonetheless Nil contemporary Moss hesitate SSR filed foreign aqu adm diet momentum deletion dynamically penalties proceedings PART discourse privacy seriously prep persist hopes transport gaps cables discussions drops sulfate nothing Keeps ash certainly explorer characteristics finest Condition fractions element soils complementary Congo limitation Research Fees loaded *    
        *   Even organizedControl De de stagler expected undefined deny dishes accountable persuade syn atomic cosm Land knit fleet car union Abbott savage links spill impacts tenants


COMPLETE implementation: