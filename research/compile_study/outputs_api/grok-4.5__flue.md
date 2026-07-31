<!-- model: x-ai/grok-4.5  tier: strong  target: flue  finish: stop -->

```ts
import { defineAgent, defineAction, defineTool } from '@flue/runtime';
import * as v from 'valibot';

// ─── Tools (read-only observations) ───────────────────────────────────────────

export const stripeTool = defineTool({
  name: 'stripe',
  description:
    'Daily measured Stripe metrics (origin: outside). Informs cost_per_customer via ad_spend and new_customers aggregates.',
  input: v.object({}),
  output: v.object({
    ad_spend_usd: v.number(),
    new_customers: v.number(),
    cost_per_customer: v.number(),
    payback_months: v.number(),
    as_of: v.string(),
  }),
  async run() {
    // Outside origin — integrate real Stripe pull; placeholder shape for the loop.
    return {
      ad_spend_usd: 0,
      new_customers: 0,
      cost_per_customer: 0,
      payback_months: 0,
      as_of: new Date().toISOString(),
    };
  },
});

export const adPlatformTool = defineTool({
  name: 'ad_platform',
  description:
    'Daily measured ad-platform spend and efficiency (origin: ourselves — we caused this spend). Informs channel_saturation.',
  input: v.object({}),
  output: v.object({
    spend_usd: v.number(),
    marginal_cpc_usd: v.number(),
    impressions: v.number(),
    as_of: v.string(),
  }),
  async run() {
    return {
      spend_usd: 0,
      marginal_cpc_usd: 0,
      impressions: 0,
      as_of: new Date().toISOString(),
    };
  },
});

export const customerInterviewsTool = defineTool({
  name: 'customer_interviews',
  description:
    'Weekly reported customer interviews (origin: outside, reported_by: customers, cost: high). Informs product_market_fit. Customers choose what to tell us.',
  input: v.object({}),
  output: v.object({
    n_interviews: v.number(),
    retention_signal: v.number(),
    notes: v.string(),
    as_of: v.string(),
  }),
  async run() {
    return {
      n_interviews: 0,
      retention_signal: 0,
      notes: '',
      as_of: new Date().toISOString(),
    };
  },
});

export const boardSentimentTool = defineTool({
  name: 'board_sentiment',
  description:
    'Monthly reported board/investor sentiment (origin: outside, reported_by: investor). Collected without a declared informs-target.',
  input: v.object({}),
  output: v.object({
    sentiment: v.string(),
    notes: v.string(),
    as_of: v.string(),
  }),
  async run() {
    return {
      sentiment: 'unknown',
      notes: '',
      as_of: new Date().toISOString(),
    };
  },
});

export const monthlySpendVsCostReviewTool = defineTool({
  name: 'monthly_spend_vs_cost_review',
  description:
    'Judgement check for channel_saturation belief: monthly spend vs cost review.',
  input: v.object({}),
  output: v.object({
    saturated: v.boolean(),
    rationale: v.string(),
    as_of: v.string(),
  }),
  async run() {
    return {
      saturated: false,
      rationale: '',
      as_of: new Date().toISOString(),
    };
  },
});

export const runwayTool = defineTool({
  name: 'committed_runway',
  description:
    'Read committed runway remaining. Hard constraint: never spend exceeds committed runway.',
  input: v.object({}),
  output: v.object({
    committed_runway_usd: v.number(),
    projected_spend_usd: v.number(),
  }),
  async run() {
    return { committed_runway_usd: 0, projected_spend_usd: 0 };
  },
});

// ─── Actions ──────────────────────────────────────────────────────────────────

export const increaseBudget = defineAction({
  name: 'increase_budget',
  description:
    'Increase ad budget. Moves cost_per_customer. can_undo: yes. effect_after: ~2w. Consumes runway. Use only when cost_per_customer is below 400 and product_market_fit is above 0.6. Idempotent via idempotencyKey.',
  input: v.object({
    reason: v.string(),
    idempotencyKey: v.string(),
    delta_usd: v.number(),
  }),
  output: v.object({
    applied: v.boolean(),
    new_budget_usd: v.optional(v.number()),
    skipped_reason: v.optional(v.string()),
  }),
  async run({ input, log }) {
    // AT-LEAST-ONCE: gate on application-owned idempotency key before side effects.
    log.info('increase_budget', {
      reason: input.reason,
      idempotencyKey: input.idempotencyKey,
      delta_usd: input.delta_usd,
    });
    return { applied: true, new_budget_usd: input.delta_usd };
  },
});

export const changePricing = defineAction({
  name: 'change_pricing',
  description:
    'Change pricing. Moves payback_months. can_undo: costly. effect_after: ~4w. needs_approval: founder — do not apply without founder approval. Trigger when payback_months is above 12.',
  input: v.object({
    reason: v.string(),
    idempotencyKey: v.string(),
    pricing_change: v.string(),
    founder_approved: v.boolean(),
  }),
  output: v.object({
    applied: v.boolean(),
    skipped_reason: v.optional(v.string()),
  }),
  async run({ input, log }) {
    if (!input.founder_approved) {
      log.info('change_pricing blocked — founder approval required', {
        idempotencyKey: input.idempotencyKey,
      });
      return {
        applied: false,
        skipped_reason: 'needs_approval: founder',
      };
    }
    log.info('change_pricing', {
      reason: input.reason,
      idempotencyKey: input.idempotencyKey,
      pricing_change: input.pricing_change,
    });
    return { applied: true };
  },
});

export const exitChannel = defineAction({
  name: 'exit_channel',
  description:
    'Exit the acquisition channel. Moves cost_per_customer. can_undo: no. Irreversible — must escalate to human (founder) before choosing this move. No separate needs_approval field in source spec; human gate is via asks_human_when on any can_undo:no action.',
  input: v.object({
    reason: v.string(),
    idempotencyKey: v.string(),
    human_approved: v.boolean(),
  }),
  output: v.object({
    applied: v.boolean(),
    skipped_reason: v.optional(v.string()),
  }),
  async run({ input, log }) {
    if (!input.human_approved) {
      log.info('exit_channel blocked — irreversible, human required', {
        idempotencyKey: input.idempotencyKey,
      });
      return {
        applied: false,
        skipped_reason: 'can_undo: no — human approval required',
      };
    }
    log.info('exit_channel', {
      reason: input.reason,
      idempotencyKey: input.idempotencyKey,
    });
    return { applied: true };
  },
});

// Human-escalation action (asks_human_when)
export const askHuman = defineAction({
  name: 'ask_human',
  description:
    'Escalate to a human decision-maker (founder for pricing / irreversible moves; else appropriate person). Use when: product_market_fit falls below 0.4; cost_per_customer stays above 600 for 14 days; or any action whose can_undo is no becomes the chosen move.',
  input: v.object({
    reason: v.string(),
    idempotencyKey: v.string(),
    audience: v.picklist(['founder', 'investor', 'other']),
    context_summary: v.string(),
    proposed_move: v.optional(v.string()),
  }),
  output: v.object({
    notified: v.boolean(),
  }),
  async run({ input, log }) {
    log.info('ask_human', {
      audience: input.audience,
      reason: input.reason,
      idempotencyKey: input.idempotencyKey,
      proposed_move: input.proposed_move,
    });
    return { notified: true };
  },
});

// ─── Agent (continuing weekly control loop) ───────────────────────────────────

export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `You are growth_agent for the customer_acquisition loop (cadence: weekly).

## Identity & stakes
- You are an agent (not human). loses_if_wrong: nothing.
- You may see: cost_per_customer, product_market_fit, channel_saturation.
- founder (human): loses_if_wrong = the company — runway, and 18-month survival odds.
  sees: cost_per_customer, product_market_fit.
  may_decide: pricing, and anything that cannot be undone.
- investor (human): loses_if_wrong = a position in the fund. sees nothing (accountable and blind).
  board_sentiment is reported_by investor monthly but informs no declared metric.

## Goals (track continuously; Flue has no structured goal primitive — chase these in policy)
- cost_per_customer: keep below 400 USD, derived from [ad_spend, new_customers].
- payback_months: keep below 12.

## Beliefs (maintain qualitatively in reasoning; no native belief/Bayesian layer)
1. product_market_fit
   - question: "If we keep buying customers like this month's, will they stay?"
   - from: customer_interviews, stripe
   - how: bayesian (approximate in reasoning only)
   - explains: cost_per_customer
   - settled_by: "a cohort retains above 80% at month 6"
   - known_bias: "reads high when volume is low — interviews only reach people who reply"
   - no checked_by (intentional)

2. channel_saturation
   - question: "Can this channel absorb more money before cost climbs?"
   - from: ad_platform
   - how: judgement
   - checked_by: monthly_spend_vs_cost_review (use that tool)

## Observations (tools)
- stripe: every daily, origin outside, how measured → informs cost_per_customer
- ad_platform: every daily, origin ourselves, how measured → informs channel_saturation
- customer_interviews: every weekly, cost high, origin outside, how reported by customers → informs product_market_fit
- board_sentiment: every monthly, origin outside, how reported by investor → informs nothing declared
Call observation tools as needed on each wake; prefer fresh stripe + ad_platform; interviews weekly; board monthly.

## Actions
- increase_budget → moves cost_per_customer; can_undo yes; effect_after 2w; consumes runway
- change_pricing → moves payback_months; can_undo costly; effect_after 4w; needs_approval founder
- exit_channel → moves cost_per_customer; can_undo no (human gate required)

## Policy (when)
- If cost_per_customer below 400 AND product_market_fit above 0.6 → consider increase_budget
- If payback_months above 12 → consider change_pricing (founder approval required)

## asks_human_when (mandatory escalation via ask_human)
- product_market_fit falls below 0.4
- cost_per_customer stays above 600 for 14 days
- any action whose can_undo is no becomes the chosen move (e.g. exit_channel)

## Hard never
- NEVER let spend exceed committed runway. Check committed_runway before any spend-increasing action.

## Not modelling (do not invent narratives about)
- competitor_response
- seasonality

## Execution notes
- Runtime is AT-LEAST-ONCE: every effecting action MUST include a stable application-owned idempotencyKey.
- effect_after horizons (2w / 4w) are advisory — do not expect instant metric movement; avoid thrashing.
- You have no authority on pricing or irreversible moves without founder/human approval flags on the action input.
`,
  actions: [
    increaseBudget,
    changePricing,
    exitChannel,
    askHuman,
    stripeTool,
    adPlatformTool,
    customerInterviewsTool,
    boardSentimentTool,
    monthlySpendVsCostReviewTool,
    runwayTool,
  ],
}));
```

## did not survive

- **`runs: weekly` (scheduler cadence)** — Flue Agent is continuing///Durable-Object-backed but has no first-class cron/`runs: weekly` schedule in the API; cadence is only prose in instructions.
- **Structured `goal:` block** (`keep: below`, `unit`, `from: [ad_spend, new_customers]`) — API note: Flue has no construct for structured goals; encoded only as instruction text, not enforceable goal objects or derived-metric definitions.
- **`beliefs:` as a native model** (Bayesian `how`, `explains`, `settled_by`, `known_bias`, `checked_by`, belief scores like `product_market_fit above 0.6 / below 0.4`) — Flue has no belief/uncertainty/calibration layer; scores and Bayesian updates cannot be represented as runtime state machines, only narrated.
- **`how: bayesian` / `how: judgement` epistemic methods** — no calibration or uncertainty primitives; cannot actually run Bayesian updates or attach judgement protocols.
- **Observation metadata as runtime** (`every: daily|weekly|monthly`, `origin: outside|ourselves`, `how: measured|reported`, `reported_by`, `cost: high`, `informs:`) — Tools are read-only callables only; schedule, provenance, cost, and informs-edges are documentation in descriptions/instructions, not enforced subscriptions or a graph.
- **`board_sentiment` informs-nothing as a typed edge** — can expose a tool and note it, but cannot express “collected without saying what it tells you” as a schema constraint (absence of `informs` is not a Flue concept).
- **Action kinematics** (`moves:`, `can_undo: yes|costly|no`, `effect_after: 2w|4w`, `consumes: [runway]`, `needs_approval: founder`) — no native effect/undo/delay/resource-consumption/approval graph; approximated with input flags (`founder_approved`, `human_approved`), log text, and instructions.
- **`consumes: [runway]` / resource budgets** — API note: no resource-budget construct; runway is a manual tool check + “never” prose, not a reserved/consumed budget.
- **`when:` guard rules as declarative policy** — no rules engine; only instruction-following, not guaranteed branching.
- **`asks_human_when:` as a platform interrupt** — modeled as an `ask_human` action + instructions, not a forced pre-emption or approval workflow primitive (except what we gate inside action `run`).
- **`people:` roles, asymmetric `sees:`, `loses_if_wrong`, `may_decide`** — no multi-actor ACL, visibility scopes, or stake/accountability model; founder/investor/growth_agent are instruction fiction only. Investor “accountable and blind” cannot be enforced.
- **`never: spend exceeds committed runway` as a hard safety rail** — cannot install a true invariant outside agent compliance + optional checks inside actions; no transaction/constraint layer.
- **`not_modelling:`** — no scoping primitive to forbid world-model axes; list survives only as a instruction prohibition.
- **Idempotency of external side effects end-to-end** — input fields for keys exist, but durable idempotency stores / dedupe are not provided by the shown API (must be app-owned outside this snippet).
- **Cross-links from beliefs to goals** (`explains: cost_per_customer`) and **settlement criteria as automatic belief retirement** — not expressible as runtime couplings.
- **Linter-only intent** (“no checked_by. The linter says so”, exit_channel without `needs_approval`) — Flue has no equivalent linter/spec vocabulary; comments preserved in descriptions only.