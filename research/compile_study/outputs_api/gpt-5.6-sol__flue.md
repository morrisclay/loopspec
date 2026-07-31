<!-- model: openai/gpt-5.6-sol  tier: strong  target: flue  finish: stop -->

### `src/agent.ts`

```ts
import { defineAgent } from '@flue/runtime';

import increaseBudget from './actions/increase-budget';
import changePricing from './actions/change-pricing';
import exitChannel from './actions/exit-channel';
import requestHumanDecision from './actions/request-human-decision';

export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',

  instructions: `
You are the continuing customer_acquisition control loop.

The loop is intended to be evaluated weekly. Flue does not schedule agent turns, so only
perform an evaluation when invoked by the external weekly scheduler. Do not invent
observations that were not supplied to you.

GOALS

1. Keep cost_per_customer below 400 USD.
   Derive it from ad_spend and new_customers:
   cost_per_customer = ad_spend / new_customers.
   If new_customers is zero, treat cost_per_customer as unavailable or unbounded rather
   than dividing by zero.

2. Keep payback_months below 12.

BELIEFS

product_market_fit:
- Question: If we keep buying customers like this month's, will they stay?
- Evidence sources: customer_interviews and stripe.
- Intended method: Bayesian.
- Explains cost_per_customer.
- Consider it settled only when a cohort retains above 80% at month 6.
- Known bias: it reads high when volume is low because interviews only reach people who reply.
- There is deliberately no independent checker for this belief.
- Never present an informal estimate as a formally calibrated posterior. State what
  evidence and assumptions support any probability-like estimate.

channel_saturation:
- Question: Can this channel absorb more money before cost climbs?
- Evidence source: ad_platform.
- Intended method: judgement.
- It is checked by monthly_spend_vs_cost_review.

OBSERVATIONS

stripe:
- Daily, externally originated, measured.
- Informs cost_per_customer.

ad_platform:
- Daily, originated by our own spending decisions, measured.
- Informs channel_saturation.
- Account for the fact that this evidence is intervention-dependent.

customer_interviews:
- Weekly, high collection cost, externally originated, reported by customers.
- Informs product_market_fit.
- Treat reports as selected and potentially biased rather than direct measurements.

board_sentiment:
- Monthly, externally originated, reported by the investor.
- It deliberately informs no declared belief or goal. Do not use it as decision evidence
  unless a human explicitly changes the loop.

Only use observations supplied in the current conversation or reliable prior agent state.
Identify stale, missing, or conflicting observations before choosing a move.

ACTIONS

increase_budget:
- Moves cost_per_customer.
- Reversible.
- Expected effect delay: 2 weeks.
- Consumes runway.
- Before choosing it, verify from supplied evidence that the proposed spend will not
  exceed committed runway.
- Because effects are delayed, do not interpret a lack of immediate improvement as failure.
- Invoke increase_budget with an application-owned idempotency key.

change_pricing:
- Moves payback_months.
- Costly to undo.
- Expected effect delay: 4 weeks.
- Requires founder approval.
- Never invoke it without a founder approval reference.
- Invoke change_pricing with an application-owned idempotency key.

exit_channel:
- Moves cost_per_customer.
- Cannot be undone.
- The action declaration itself omitted needs_approval, but the human-escalation rule says
  that any irreversible chosen move must go to a human.
- Therefore request a founder decision before invoking exit_channel, and only invoke it
  with a founder approval reference.
- Invoke exit_channel with an application-owned idempotency key.

DECISION RULES

- If cost_per_customer is below 400 and product_market_fit is above 0.6, increase_budget
  may be selected, subject to the committed-runway constraint.
- If payback_months is above 12, change_pricing may be selected, but only after founder
  approval.
- These comparisons require actual current values. Do not infer that a threshold was
  crossed merely from qualitative language.
- If multiple rules match, explain the conflict, expected timing, reversibility, and
  runway implications before selecting a move.
- Avoid repeatedly selecting an action while still inside its expected effect window
  unless materially new evidence justifies it.

HUMAN ESCALATION

Invoke request_human_decision when:
- product_market_fit falls below 0.4;
- cost_per_customer has remained above 600 for a demonstrated continuous 14-day period;
- any action whose can_undo value is "no" becomes the chosen move.

Do not claim the 14-day trigger fired unless time-stamped observations establish the
duration. The intended decision maker for pricing and anything irreversible is the founder.

PEOPLE

founder:
- Human.
- Loses the company, runway, and 18-month survival odds if wrong.
- Sees cost_per_customer and product_market_fit.
- May decide pricing and anything that cannot be undone.

growth_agent:
- Agent.
- Has no declared personal loss if wrong.
- Sees cost_per_customer, product_market_fit, and channel_saturation.

investor:
- Human.
- Loses a position in the fund if wrong.
- Has no declared visibility. Do not assume access merely because investor sentiment is
  observed.

HARD SAFETY RULE

Never knowingly choose or emit an increase_budget request that would make spend exceed
committed runway. If committed runway or the proposed spend is unavailable, ask for the
missing information rather than asserting that the constraint is satisfied.

NOT MODELLED

Explicitly call out when a recommendation could materially depend on:
- competitor_response
- seasonality

RESPONSE FORMAT FOR EACH EVALUATION

Return:
1. Observations used, including freshness.
2. Current goal metrics.
3. Belief assessment and evidence quality.
4. Trigger evaluation.
5. Chosen move or "no action".
6. Human escalation, if any.
7. Missing information, delayed effects, and unmodelled risks.

The registered actions emit typed execution requests only. They do not themselves connect
to Stripe, an ad platform, pricing infrastructure, or a human notification system. Never
claim that the external business effect occurred merely because an action returned.
`,

  actions: [
    increaseBudget,
    changePricing,
    exitChannel,
    requestHumanDecision,
  ],
}));
```

### `src/actions/increase-budget.ts`

```ts
import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

export default defineAction({
  name: 'increase_budget',

  description:
    'Emit an idempotent request to increase channel budget after checking committed runway.',

  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string(),
    channel: v.string(),
    currentWeeklyBudgetUsd: v.number(),
    proposedWeeklyBudgetUsd: v.number(),
    committedRunwayRemainingUsd: v.number(),
    evidenceAsOf: v.string(),
  }),

  output: v.object({
    emitted: v.boolean(),
    idempotencyKey: v.string(),
    channel: v.string(),
    proposedWeeklyBudgetUsd: v.number(),
    expectedEffectAfterDays: v.number(),
  }),

  async run({ input }) {
    if (input.currentWeeklyBudgetUsd < 0) {
      throw new Error('currentWeeklyBudgetUsd cannot be negative');
    }

    if (input.proposedWeeklyBudgetUsd <= input.currentWeeklyBudgetUsd) {
      throw new Error(
        'proposedWeeklyBudgetUsd must be greater than currentWeeklyBudgetUsd',
      );
    }

    if (input.committedRunwayRemainingUsd < 0) {
      throw new Error('committedRunwayRemainingUsd cannot be negative');
    }

    if (input.proposedWeeklyBudgetUsd > input.committedRunwayRemainingUsd) {
      throw new Error(
        'Refusing increase_budget: proposed weekly budget exceeds supplied committed runway',
      );
    }

    return {
      emitted: true,
      idempotencyKey: input.idempotencyKey,
      channel: input.channel,
      proposedWeeklyBudgetUsd: input.proposedWeeklyBudgetUsd,
      expectedEffectAfterDays: 14,
    };
  },
});
```

### `src/actions/change-pricing.ts`

```ts
import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

export default defineAction({
  name: 'change_pricing',

  description:
    'Emit an idempotent pricing-change request. Founder approval is mandatory and the change is costly to undo.',

  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string(),
    currentPaybackMonths: v.number(),
    proposedPricingDescription: v.string(),
    approvedBy: v.literal('founder'),
    approvalReference: v.string(),
    evidenceAsOf: v.string(),
  }),

  output: v.object({
    emitted: v.boolean(),
    idempotencyKey: v.string(),
    approvalReference: v.string(),
    expectedEffectAfterDays: v.number(),
  }),

  async run({ input }) {
    if (input.currentPaybackMonths < 0) {
      throw new Error('currentPaybackMonths cannot be negative');
    }

    if (input.approvalReference.trim().length === 0) {
      throw new Error('A non-empty founder approvalReference is required');
    }

    if (input.proposedPricingDescription.trim().length === 0) {
      throw new Error('proposedPricingDescription cannot be empty');
    }

    return {
      emitted: true,
      idempotencyKey: input.idempotencyKey,
      approvalReference: input.approvalReference,
      expectedEffectAfterDays: 28,
    };
  },
});
```

### `src/actions/exit-channel.ts`

```ts
import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

export default defineAction({
  name: 'exit_channel',

  description:
    'Emit an idempotent irreversible channel-exit request. Founder approval is required by the human-escalation policy.',

  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string(),
    channel: v.string(),
    approvedBy: v.literal('founder'),
    approvalReference: v.string(),
    evidenceAsOf: v.string(),
  }),

  output: v.object({
    emitted: v.boolean(),
    idempotencyKey: v.string(),
    channel: v.string(),
    irreversible: v.boolean(),
    approvalReference: v.string(),
  }),

  async run({ input }) {
    if (input.channel.trim().length === 0) {
      throw new Error('channel cannot be empty');
    }

    if (input.approvalReference.trim().length === 0) {
      throw new Error(
        'Founder approval is required before emitting an irreversible channel exit',
      );
    }

    return {
      emitted: true,
      idempotencyKey: input.idempotencyKey,
      channel: input.channel,
      irreversible: true,
      approvalReference: input.approvalReference,
    };
  },
});
```

### `src/actions/request-human-decision.ts`

```ts
import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

export default defineAction({
  name: 'request_human_decision',

  description:
    'Emit an idempotent request for founder review when a human-escalation condition is met.',

  input: v.object({
    idempotencyKey: v.string(),
    requestedFrom: v.literal('founder'),
    trigger: v.picklist([
      'product_market_fit_below_0_4',
      'cost_per_customer_above_600_for_14_days',
      'irreversible_action_chosen',
      'pricing_approval_required',
    ]),
    reason: v.string(),
    proposedMove: v.string(),
    evidenceSummary: v.string(),
  }),

  output: v.object({
    emitted: v.boolean(),
    idempotencyKey: v.string(),
    requestedFrom: v.literal('founder'),
    trigger: v.string(),
  }),

  async run({ input }) {
    if (input.reason.trim().length === 0) {
      throw new Error('reason cannot be empty');
    }

    if (input.evidenceSummary.trim().length === 0) {
      throw new Error('evidenceSummary cannot be empty');
    }

    return {
      emitted: true,
      idempotencyKey: input.idempotencyKey,
      requestedFrom: 'founder' as const,
      trigger: input.trigger,
    };
  },
});
```

## did not survive

- **Native weekly execution:** Flue Agents continue but the supplied API has no scheduling construct. An external scheduler must invoke the agent weekly.
- **Daily, weekly, and monthly observation collection:** No source connectors or polling API were provided. Stripe, ad-platform, interview, and board data must be supplied externally.
- **Actual business side effects:** No ad-platform, pricing, channel-management, or notification integration was specified. The actions therefore emit typed requests; they do not change budgets, pricing, channels, or contact the founder.
- **Durable idempotency enforcement:** Actions accept and return application-owned idempotency keys, but the supplied API exposes no durable action storage or deduplication facility. Downstream effect handlers must persist and deduplicate those keys.
- **Structured goals:** Flue has no structured-goal construct. Goal definitions and thresholds survive only as agent instructions and action validation.
- **Formal Bayesian uncertainty and calibration:** Flue has no uncertainty or calibration construct. The product-market-fit method, bias, settlement condition, and missing checker survive as instructions, not as a machine-enforced Bayesian model.
- **Resource budgets:** Flue has no resource-budget construct. The runway rule is approximated with action input validation, but there is no authoritative or transactionally reserved runway balance, so concurrent spending cannot be prevented by this implementation alone.
- **Deterministic temporal triggers:** The 14-day threshold and 2-week/4-week effect windows are instructions and returned metadata. The API provides no timers, temporal query engine, or delayed-effect tracking.
- **Machine-enforced observation provenance and information flow:** `origin`, `how`, `reported_by`, `informs`, observation cost, and each person's `sees` list are represented in instructions, but Flue provides no provenance schema or access-control mechanism to enforce them.
- **Accountability and losses:** `loses_if_wrong` survives as decision context only; Flue has no accountability or incentive model.
- **Undo semantics:** Reversible, costly-to-undo, and irreversible classifications survive in instructions and validation policy, but Flue has no native rollback mechanism.
- **Deterministic rule execution:** The `when` and `asks_human_when` clauses are interpreted by the model rather than executed by a native condition engine.
- **Lint failures as first-class diagnostics:** The intentionally missing `checked_by`, missing `needs_approval`, uninformed `board_sentiment`, and blind investor are preserved in instructions, but Flue has no loop-schema linter capable of reporting them structurally.