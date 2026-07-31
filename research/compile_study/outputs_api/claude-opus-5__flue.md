<!-- model: anthropic/claude-opus-5  tier: strong  target: flue  finish: length -->

Below is a working Flue implementation of the `customer_acquisition` loop. It is one **Agent** (the continuing control loop), three **Workflows** (the bounded per-cadence observation jobs), read-only **Tools** for every `observes:` source, and one **Action** per entry in `actions:` plus the escalation and belief-write actions.

Everything in the spec that Flue has no construct for is still *present* — as machine-readable constants, guard code, and lint findings — and every such case is listed in **## did not survive** with what was lost by moving it into application code.

```
src/
  spec.ts                                  transcription of the loop file as constants
  lint.ts                                  the findings the spec says "the linter says so"
  types.ts
  store.ts                                 state + idempotency ledger
  providers.ts                             outside-world adapters
  metrics.ts                               goal arithmetic
  beliefs.ts                               bayesian update + known_bias correction + settled_by
  policy.ts                                when:
  triggers.ts                              asks_human_when:
  visibility.ts                            people: sees / may_decide
  tools/*.ts
  actions/*.ts
  agent.ts                                 the loop
  workflows/daily-observe.ts
  workflows/weekly-review.ts
  workflows/monthly-spend-vs-cost-review.ts
```

---

### `src/spec.ts`

```ts
/**
 * Machine-readable transcription of customer_acquisition.loop.yaml (v1 vocabulary).
 * Flue has no loop-spec construct, so the spec lives here as data and is
 * (a) enforced by policy.ts / triggers.ts / the actions' guards, and
 * (b) quoted verbatim into the agent's instructions.
 */

export const LOOP = 'customer_acquisition' as const;
export const RUNS = 'weekly' as const; // scheduling is external — see did not survive

export const GOALS = {
  cost_per_customer: {
    keep: 'below' as const,
    threshold: 400,
    unit: 'USD',
    from: ['ad_spend', 'new_customers'] as const,
  },
  payback_months: {
    keep: 'below' as const,
    threshold: 12,
    unit: 'months',
    from: [] as const, // spec gives no from: — derived from stripe. See lint.
  },
} as const;

export type GoalId = keyof typeof GOALS;

export const BELIEFS = {
  product_market_fit: {
    question: "If we keep buying customers like this month's, will they stay?",
    from: ['customer_interviews', 'stripe'] as const,
    how: 'bayesian' as const,
    explains: 'cost_per_customer' as const,
    settled_by: 'a cohort retains above 80% at month 6',
    known_bias: 'reads high when volume is low — interviews only reach people who reply',
    checked_by: null, // deliberately absent in the spec
  },
  channel_saturation: {
    question: 'Can this channel absorb more money before cost climbs?',
    from: ['ad_platform'] as const,
    how: 'judgement' as const,
    explains: null,
    settled_by: null,
    known_bias: null,
    checked_by: 'monthly_spend_vs_cost_review' as const,
  },
} as const;

export type BeliefId = keyof typeof BELIEFS;

export const OBSERVES = {
  stripe: {
    informs: 'cost_per_customer' as const,
    every: 'daily' as const,
    origin: 'outside' as const,
    how: 'measured' as const,
    reported_by: null,
    cost: 'normal' as const,
  },
  ad_platform: {
    informs: 'channel_saturation' as const,
    every: 'daily' as const,
    origin: 'ourselves' as const, // we caused this spend to exist
    how: 'measured' as const,
    reported_by: null,
    cost: 'normal' as const,
  },
  customer_interviews: {
    informs: 'product_market_fit' as const,
    every: 'weekly' as const,
    origin: 'outside' as const,
    how: 'reported' as const, // customers CHOOSE what to tell us
    reported_by: 'customers' as const,
    cost: 'high' as const,
  },
  board_sentiment: {
    informs: null, // collected without saying what it tells you
    every: 'monthly' as const,
    origin: 'outside' as const,
    how: 'reported' as const,
    reported_by: 'investor' as const,
    cost: 'normal' as const,
  },
} as const;

export type ObservationId = keyof typeof OBSERVES;

const DAY = 86_400_000;

export const ACTIONS = {
  increase_budget: {
    moves: 'cost_per_customer' as const,
    can_undo: 'yes' as const,
    effect_after_ms: 14 * DAY, // 2w
    effect_after: '2w',
    consumes: ['runway'] as const,
    needs_approval: null,
  },
  change_pricing: {
    moves: 'payback_months' as const,
    can_undo: 'costly' as const,
    effect_after_ms: 28 * DAY, // 4w
    effect_after: '4w',
    consumes: [] as const,
    needs_approval: 'founder' as const,
  },
  exit_channel: {
    moves: 'cost_per_customer' as const,
    can_undo: 'no' as const,
    effect_after_ms: 0,
    effect_after: null,
    consumes: [] as const,
    needs_approval: null, // absent in the spec. See lint: we require confirmation anyway.
  },
} as const;

export type ActionId = keyof typeof ACTIONS;

export const WHEN = [
  { if: 'cost_per_customer below 400 and product_market_fit above 0.6', do: 'increase_budget' },
  { if: 'payback_months above 12', do: 'change_pricing' },
] as const;

export const ASKS_HUMAN_WHEN = [
  'product_market_fit falls below 0.4',
  'cost_per_customer stays above 600 for 14 days',
  'any action whose can_undo is no becomes the chosen move',
] as const;

export const PEOPLE = {
  founder: {
    human: true,
    loses_if_wrong: 'the company — runway, and 18-month survival odds',
    sees: ['cost_per_customer', 'product_market_fit'] as const,
    may_decide: ['change_pricing', 'exit_channel'] as const, // "pricing, and anything that cannot be undone"
  },
  growth_agent: {
    human: false,
    loses_if_wrong: 'nothing',
    sees: ['cost_per_customer', 'product_market_fit', 'channel_saturation'] as const,
    may_decide: ['increase_budget'] as const,
  },
  investor: {
    human: true,
    loses_if_wrong: 'a position in the fund',
    sees: [] as const, // accountable and blind
    may_decide: [] as const,
  },
} as const;

export type PersonId = keyof typeof PEOPLE;

export const NEVER = ['spend exceeds committed runway'] as const;

export const NOT_MODELLING = ['competitor_response', 'seasonality'] as const;

/** Escalation thresholds referenced by asks_human_when. */
export const ESCALATION = {
  pmf_floor: 0.4,
  cpc_ceiling: 600,
  cpc_ceiling_days: 14,
} as const;

/** when-rule thresholds. */
export const GATES = {
  increase_budget: { cpc_below: 400, pmf_above: 0.6 },
  change_pricing: { payback_above: 12 },
} as const;
```

### `src/lint.ts`

```ts
/**
 * Flue has no spec linter. These are the findings the spec file points at
 * ("The linter says so, and that is the point"), hard-coded so that they are
 * logged on every cycle instead of vanishing.
 */
export type Finding = {
  rule: string;
  subject: string;
  severity: 'error' | 'warn';
  message: string;
  enforced_here: string;
};

export const SPEC_LINT: Finding[] = [
  {
    rule: 'belief-without-checked-by',
    subject: 'beliefs.product_market_fit',
    severity: 'warn',
    message:
      'A bayesian belief that explains a goal has no checked_by. Nothing outside the loop ever ' +
      'tests it, and it has a declared known_bias that inflates it.',
    enforced_here:
      'beliefs.ts applies the known_bias correction and reports rawValue alongside value; the ' +
      'agent is instructed to treat product_market_fit as unaudited.',
  },
  {
    rule: 'irreversible-without-approval',
    subject: 'actions.exit_channel',
    severity: 'error',
    message: 'can_undo: no and no needs_approval.',
    enforced_here:
      'actions/exit-channel.ts refuses without an explicit founder confirmation, per ' +
      'asks_human_when rule 3, even though the spec omits needs_approval.',
  },
  {
    rule: 'observation-informs-nothing',
    subject: 'observes.board_sentiment',
    severity: 'warn',
    message: 'Collected monthly, informs nothing. It cannot change any decision.',
    enforced_here:
      'tools/read-board-sentiment.ts returns it with informs: null and decision_relevant: false.',
  },
  {
    rule: 'accountable-but-blind',
    subject: 'people.investor',
    severity: 'warn',
    message: 'loses_if_wrong is set, sees is empty. Bears consequence with no visibility.',
    enforced_here: 'visibility.ts projects an empty view for investor and logs the finding.',
  },
  {
    rule: 'goal-without-source',
    subject: 'goal.payback_months',
    severity: 'warn',
    message: 'No from:. Its provenance is implicit.',
    enforced_here: 'metrics.ts derives it from stripe ARPU × gross margin and labels it derived.',
  },
  {
    rule: 'self-caused-observation',
    subject: 'observes.ad_platform',
    severity: 'warn',
    message:
      'origin: ourselves. It measures the consequence of our own spend, so it cannot ' +
      'independently confirm that more spend is affordable.',
    enforced_here:
      'tools carry origin/how/reported_by through to the agent; instructions forbid treating ' +
      'ad_platform as independent evidence for channel_saturation.',
  },
];

export function logLint(log: { warn: (m: string, d?: unknown) => void }): void {
  for (const f of SPEC_LINT) {
    log.warn(`spec-lint ${f.severity} ${f.rule} @ ${f.subject}`, f);
  }
}
```

### `src/types.ts`

```ts
import type { ActionId, BeliefId, GoalId, PersonId } from './spec';

export interface Reading {
  at: string; // ISO
  value: number;
  derived?: boolean;
}

export interface StripeObs {
  at: string;
  newCustomers: number;
  arpuMonthlyUsd: number;
  grossMarginRate: number;
  cohortMonth6Retention?: number; // feeds settled_by
  origin: 'outside';
  how: 'measured';
}

export interface AdPlatformObs {
  at: string;
  channel: string;
  spendUsd: number;
  impressions: number;
  marginalCpaUsd: number;
  origin: 'ourselves';
  how: 'measured';
}

export interface InterviewObs {
  at: string;
  invited: number;
  completed: number;
  wouldBeVeryDisappointed: number;
  origin: 'outside';
  how: 'reported';
  reported_by: 'customers';
  cost: 'high';
}

export interface BoardObs {
  at: string;
  sentiment: number; // -1..1
  note: string;
  origin: 'outside';
  how: 'reported';
  reported_by: 'investor';
  informs: null;
}

export interface Approval {
  id: string;
  action: ActionId;
  approvedBy: PersonId;
  at: string;
  scopeHash: string;
  consumedByDecision?: string;
}

export interface PendingEffect {
  decisionId: string;
  action: ActionId;
  appliedAt: string;
  maturesAt: string;
  moves: GoalId;
}

export interface UndoRecord {
  decisionId: string;
  action: ActionId;
  can_undo: 'yes' | 'costly' | 'no';
  undoBy?: string; // how to reverse, if reversible
  reversed?: boolean;
  reversalCostNote?: string;
}

export interface DecisionRecord {
  id: string;
  at: string;
  action: ActionId;
  by: PersonId;
  reason: string;
  input: unknown;
  applied: boolean;
  refusedBy?: string;
}

export interface Escalation {
  id: string;
  at: string;
  trigger: string;
  to: PersonId;
  payload: unknown;
  acknowledgedAt?: string;
}

export interface LoopState {
  version: 1;
  runway: {
    committedUsd: number;
    spentToDateUsd: number;
    dailyCommittedUsd: number;
    committedThrough: string; // ISO
  };
  observations: {
    stripe: StripeObs[];
    ad_platform: AdPlatformObs[];
    customer_interviews: InterviewObs[];
    board_sentiment: BoardObs[];
  };
  goals: Record<GoalId, Reading[]>;
  beliefs: {
    product_market_fit: {
      alpha: number;
      beta: number;
      value: number; // bias-corrected posterior mean
      rawValue: number; // uncorrected, so the known_bias stays visible
      settled: boolean;
      settledNote?: string;
      lastUpdatedAt?: string;
      lastCheckedBy: string | null;
    };
    channel_saturation: {
      value: number; // 0 = saturated, 1 = plenty of headroom
      rationale: string;
      by: PersonId;
      at?: string;
      lastCheckedBy?: string;
      lastCheckedAt?: string;
    };
  };
  decisions: DecisionRecord[];
  escalations: Escalation[];
  approvals: Approval[];
  pendingEffects: PendingEffect[];
  undo: UndoRecord[];
  idempotency: Record<string, unknown>;
}

export type BeliefKey = BeliefId;
```

### `src/store.ts`

```ts
import type { LoopState } from './types';

/**
 * Flue's documented surface does not expose the Durable Object storage handle,
 * so state goes through an injectable adapter. Bind the real one at worker
 * startup with useStore(). The in-memory default is for tests only.
 */
export interface StateStore {
  read(): Promise<LoopState>;
  write(next: LoopState): Promise<void>;
}

export function initialState(): LoopState {
  return {
    version: 1,
    runway: {
      committedUsd: 0,
      spentToDateUsd: 0,
      dailyCommittedUsd: 0,
      committedThrough: new Date().toISOString(),
    },
    observations: { stripe: [], ad_platform: [], customer_interviews: [], board_sentiment: [] },
    goals: { cost_per_customer: [], payback_months: [] },
    beliefs: {
      product_market_fit: {
        alpha: 1,
        beta: 1,
        value: 0.5,
        rawValue: 0.5,
        settled: false,
        lastCheckedBy: null, // no checked_by in the spec
      },
      channel_saturation: {
        value: 0.5,
        rationale: 'no judgement recorded yet',
        by: 'growth_agent',
      },
    },
    decisions: [],
    escalations: [],
    approvals: [],
    pendingEffects: [],
    undo: [],
    idempotency: {},
  };
}

function memoryStore(): StateStore {
  let state = initialState();
  return {
    async read() {
      return structuredClone(state);
    },
    async write(next) {
      state = structuredClone(next);
    },
  };
}

let store: StateStore = memoryStore();

export function useStore(s: StateStore): void {
  store = s;
}

export async function readState(): Promise<LoopState> {
  return store.read();
}

export async function mutate<T>(fn: (s: LoopState) => T): Promise<T> {
  const s = await store.read();
  const result = fn(s);
  await store.write(s);
  return result;
}

/**
 * Execution is at-least-once. Every effectful path funnels through here with an
 * application-owned key so a re-dispatch replays the recorded result instead of
 * spending money twice.
 */
export async function once<T>(
  key: string,
  fn: (s: LoopState) => T,
): Promise<{ result: T; replayed: boolean }> {
  return mutate((s) => {
    if (Object.prototype.hasOwnProperty.call(s.idempotency, key)) {
      return { result: s.idempotency[key] as T, replayed: true };
    }
    const result = fn(s);
    s.idempotency[key] = result as unknown;
    return { result, replayed: false };
  });
}
```

### `src/providers.ts`

```ts
import type { AdPlatformObs, BoardObs, InterviewObs, StripeObs } from './types';

/** Outside-world adapters. Swap for real clients; shapes carry provenance. */
export interface Providers {
  stripe(): Promise<Omit<StripeObs, 'origin' | 'how'>>;
  adPlatform(): Promise<Array<Omit<AdPlatformObs, 'origin' | 'how'>>>;
  interviews(): Promise<Omit<InterviewObs, 'origin' | 'how' | 'reported_by' | 'cost'>>;
  boardSentiment(): Promise<Omit<BoardObs, 'origin' | 'how' | 'reported_by' | 'informs'>>;
  notifyHuman(to: string, subject: string, payload: unknown, idempotencyKey: string): Promise<void>;
  setAdBudget(channel: string, dailyUsd: number, idempotencyKey: string): Promise<void>;
  setPrice(planId: string, priceUsd: number, idempotencyKey: string): Promise<void>;
  pauseChannel(channel: string, idempotencyKey: string): Promise<void>;
}

const notWired = (name: string) => async (): Promise<never> => {
  throw new Error(`provider ${name} not wired`);
};

let providers: Providers = {
  stripe: notWired('stripe'),
  adPlatform: notWired('adPlatform'),
  interviews: notWired('interviews'),
  boardSentiment: notWired('boardSentiment'),
  notifyHuman: notWired('notifyHuman'),
  setAdBudget: notWired('setAdBudget'),
  setPrice: notWired('setPrice'),
  pauseChannel: notWired('pauseChannel'),
};

export function useProviders(p: Partial<Providers>): void {
  providers = { ...providers, ...p };
}

export function P(): Providers {
  return providers;
}
```

### `src/metrics.ts`

```ts
import { GOALS } from './spec';
import type { LoopState, Reading } from './types';

const DAY = 86_400_000;

function since(days: number): number {
  return Date.now() - days * DAY;
}

export function last<T>(xs: T[]): T | null {
  return xs.length ? xs[xs.length - 1] : null;
}

/** goal.cost_per_customer — from: [ad_spend, new_customers]. */
export function costPerCustomer(s: LoopState, windowDays = 30): number | null {
  const cutoff = since(windowDays);
  const spend = s.observations.ad_platform
    .filter((o) => Date.parse(o.at) >= cutoff)
    .reduce((a, o) => a + o.spendUsd, 0);
  const customers = s.observations.stripe
    .filter((o) => Date.parse(o.at) >= cutoff)
    .reduce((a, o) => a + o.newCustomers, 0);
  if (customers <= 0) return null;
  return spend / customers;
}

/**
 * goal.payback_months — the spec gives no from:. Derived here from stripe ARPU
 * and gross margin, and flagged derived so the gap stays legible.
 */
export function paybackMonths(s: LoopState, cpc: number | null): number | null {
  const latest = last(s.observations.stripe);
  if (!latest || cpc === null) return null;
  const monthlyMargin = latest.arpuMonthlyUsd * latest.grossMarginRate;
  if (monthlyMargin <= 0) return null;
  return cpc / monthlyMargin;
}

export function appendGoalReadings(s: LoopState, at: string): void {
  const cpc = costPerCustomer(s);
  if (cpc !== null) s.goals.cost_per_customer.push({ at, value: cpc });
  const pm = paybackMonths(s, cpc);
  if (pm !== null) s.goals.payback_months.push({ at, value: pm, derived: true });
  // keep 400 days of history; the 14-day escalation needs daily depth
  for (const k of ['cost_per_customer', 'payback_months'] as const) {
    const cutoff = since(400);
    s.goals[k] = s.goals[k].filter((r) => Date.parse(r.at) >= cutoff);
  }
}

export function latestGoal(s: LoopState, id: keyof typeof GOALS): Reading | null {
  return last(s.goals[id]);
}

export function goalStatus(
  s: LoopState,
  id: keyof typeof GOALS,
): { value: number | null; keep: string; threshold: number; unit: string; ok: boolean | null } {
  const g = GOALS[id];
  const r = latestGoal(s, id);
  const ok = r === null ? null : g.keep === 'below' ? r.value < g.threshold : r.value > g.threshold;
  return { value: r?.value ?? null, keep: g.keep, threshold: g.threshold, unit: g.unit, ok };
}

/** True if every daily reading over the last `days` exceeded `ceiling`, with real coverage. */
export function sustainedAbove(readings: Reading[], ceiling: number, days: number): boolean {
  const cutoff = since(days);
  const window = readings.