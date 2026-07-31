<!-- model: openai/gpt-5.6-sol  tier: strong  target: flue  finish: stop -->

```ts
// customer-acquisition.ts
//
// A dependency-free Flue implementation of the customer_acquisition loop.
// Call `customerAcquisition.run()` weekly and persist the returned state between
// invocations.

export type Reversibility = "reversible" | "costly" | "irreversible";
export type EstimateMethod = "bayesian" | "judgement";
export type Cadence = "daily" | "weekly" | "monthly";

export interface CustomerAcquisitionState {
  runway: number;
  committedRunway: number;

  lastRunAt?: string;
  lastBoardObservationMonth?: string;

  pendingActions: PendingAction[];
  auditLog: AuditEvent[];
}

export type PendingAction =
  | {
      id: string;
      action: "increase_budget";
      executeAt: string;
      createdAt: string;
      plannedSpend: number;
    }
  | {
      id: string;
      action: "change_pricing";
      executeAt: string;
      createdAt: string;
      approvedBy: "founder";
    };

export interface AuditEvent {
  at: string;
  type:
    | "observation"
    | "estimate"
    | "decision"
    | "action_scheduled"
    | "action_executed"
    | "action_rejected"
    | "escalation"
    | "invariant_violation";
  message: string;
  data?: unknown;
}

export interface StripeObservation {
  /** Stripe's independently reported CAC, if available. */
  cac?: number;

  /** Inputs used for the regulated CAC calculation. */
  adSpend: number;
  newCustomers: number;

  /** Opaque evidence passed to the PMF estimator. */
  pmfEvidence: unknown;
}

export interface AdPlatformObservation {
  /** Opaque evidence passed to the channel-saturation estimator. */
  saturationEvidence: unknown;
}

export interface CustomerInterviewObservation {
  /** Opaque evidence passed to the PMF estimator. */
  pmfEvidence: unknown;
}

export interface BoardSentimentObservation {
  sentiment: unknown;
  assertedBy: "investor";
}

export interface ProductMarketFitEstimate {
  probability: number;
  explanation?: string;
}

export interface ChannelSaturationEstimate {
  value: number | string;
  explanation?: string;
}

export interface ActionContext {
  now: Date;
  state: Readonly<CustomerAcquisitionState>;
}

export interface CustomerAcquisitionPorts {
  /*
   * These readers may aggregate all daily samples since the preceding weekly
   * invocation. Flue itself is invoked weekly.
   */
  observeStripe(): Promise<StripeObservation>;
  observeAdPlatform(): Promise<AdPlatformObservation>;
  observeCustomerInterviews(): Promise<CustomerInterviewObservation>;
  observeBoardSentiment(): Promise<BoardSentimentObservation>;

  readPaybackMonths(): Promise<number>;

  /**
   * Used to determine whether the PMF estimate is settled according to:
   * "a cohort retains above 80% at month 6".
   */
  readMonth6CohortRetention(): Promise<number | undefined>;

  estimateProductMarketFit(input: {
    method: "bayesian";
    stripe: StripeObservation["pmfEvidence"];
    customerInterviews: CustomerInterviewObservation["pmfEvidence"];
  }): Promise<ProductMarketFitEstimate>;

  estimateChannelSaturation(input: {
    method: "judgement";
    adPlatform: AdPlatformObservation["saturationEvidence"];
  }): Promise<ChannelSaturationEstimate>;

  /**
   * Returns the additional spend that an increase-budget action would commit.
   * It is checked against committed runway before the action is scheduled and
   * again before it executes.
   */
  planBudgetIncrease(context: ActionContext): Promise<{
    additionalSpend: number;
  }>;

  requestFounderApproval(input: {
    action: "change_pricing";
    reason: string;
    context: ActionContext;
  }): Promise<boolean>;

  increaseBudget(input: {
    additionalSpend: number;
    context: ActionContext;
  }): Promise<void>;

  changePricing(input: { context: ActionContext }): Promise<void>;

  exitChannel(input: { context: ActionContext }): Promise<void>;

  escalateToFounder(input: {
    reason: string;
    data: unknown;
    context: ActionContext;
  }): Promise<void>;
}

/**
 * Declarative graph metadata retained alongside the executable Flue.
 */
export const customerAcquisitionGraph = {
  loop: "customer_acquisition",
  every: "weekly",

  regulates: {
    cac: {
      target: "< 400",
      computedFrom: ["ad_spend", "new_customers"],
    },
    paybackMonths: {
      target: "< 12",
    },
  },

  estimates: {
    productMarketFit: {
      from: ["customer_interviews", "stripe"],
      method: "bayesian",
      explains: "cac",
      settledBy: "a cohort retains above 80% at month 6",
      // Deliberately no calibratedBy: the source specification omits it.
    },
    channelSaturation: {
      from: ["ad_platform"],
      method: "judgement",
    },
  },

  observes: {
    stripe: { measures: "cac", every: "daily" },
    adPlatform: { measures: "channel_saturation", every: "daily" },
    customerInterviews: {
      measures: "product_market_fit",
      every: "weekly",
      cost: "high",
    },
    boardSentiment: {
      every: "monthly",
      assertedBy: "investor",
    },
  },

  acts: {
    increaseBudget: {
      moves: "cac",
      reversibility: "reversible",
      delay: "2w",
      consumes: ["runway"],
    },
    changePricing: {
      moves: "payback_months",
      reversibility: "costly",
      delay: "4w",
      approval: "founder",
    },
    exitChannel: {
      reversibility: "irreversible",
    },
  },

  parties: {
    founder: {
      human: true,
      bears: "the company",
      sees: ["cac", "product_market_fit"],
    },
    growthAgent: {
      agent: true,
      bears: "nothing",
    },
    investor: {
      human: true,
      bears: "a position in the fund",
    },
  },

  never: ["spend exceeds committed runway"],

  ignoring: ["competitor_response", "seasonality"],
} as const;

const WEEK_MS = 7 * 24 * 60 * 60 * 1_000;

function addWeeks(at: Date, weeks: number): Date {
  return new Date(at.getTime() + weeks * WEEK_MS);
}

function actionId(action: string, now: Date): string {
  return `${action}:${now.toISOString()}`;
}

function monthKey(date: Date): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(
    2,
    "0",
  )}`;
}

function appendAudit(
  state: CustomerAcquisitionState,
  at: Date,
  type: AuditEvent["type"],
  message: string,
  data?: unknown,
): void {
  state.auditLog.push({
    at: at.toISOString(),
    type,
    message,
    data,
  });
}

function hasPendingAction(
  state: CustomerAcquisitionState,
  action: PendingAction["action"],
): boolean {
  return state.pendingActions.some((pending) => pending.action === action);
}

export class CustomerAcquisitionFlue {
  public constructor(
    private readonly ports: CustomerAcquisitionPorts,
    private readonly state: CustomerAcquisitionState,
  ) {}

  /**
   * Execute one weekly customer-acquisition cycle.
   *
   * The caller owns durable scheduling and persistence. The state is mutated
   * and also returned for convenience.
   */
  public async run(now = new Date()): Promise<CustomerAcquisitionState> {
    await this.executeDueActions(now);

    const [stripe, adPlatform, interviews, paybackMonths, month6Retention] =
      await Promise.all([
        this.ports.observeStripe(),
        this.ports.observeAdPlatform(),
        this.ports.observeCustomerInterviews(),
        this.ports.readPaybackMonths(),
        this.ports.readMonth6CohortRetention(),
      ]);

    appendAudit(this.state, now, "observation", "Weekly observations read", {
      stripe,
      adPlatform,
      customerInterviews: interviews,
      paybackMonths,
      month6Retention,
    });

    await this.observeBoardMonthly(now);

    if (stripe.newCustomers <= 0) {
      throw new Error(
        "Cannot compute CAC: stripe.newCustomers must be greater than zero",
      );
    }

    const cac = stripe.adSpend / stripe.newCustomers;

    if (stripe.cac !== undefined && Math.abs(stripe.cac - cac) > 0.01) {
      appendAudit(
        this.state,
        now,
        "observation",
        "Stripe-reported CAC differs from computed CAC",
        {
          stripeReportedCac: stripe.cac,
          computedCac: cac,
        },
      );
    }

    const [productMarketFit, channelSaturation] = await Promise.all([
      this.ports.estimateProductMarketFit({
        method: "bayesian",
        stripe: stripe.pmfEvidence,
        customerInterviews: interviews.pmfEvidence,
      }),
      this.ports.estimateChannelSaturation({
        method: "judgement",
        adPlatform: adPlatform.saturationEvidence,
      }),
    ]);

    if (
      !Number.isFinite(productMarketFit.probability) ||
      productMarketFit.probability < 0 ||
      productMarketFit.probability > 1
    ) {
      throw new Error(
        "Product-market-fit probability must be a number between 0 and 1",
      );
    }

    const pmfSettled =
      month6Retention !== undefined && month6Retention > 0.8;

    appendAudit(
      this.state,
      now,
      "estimate",
      "Estimates updated",
      {
        productMarketFit: {
          ...productMarketFit,
          method: "bayesian",
          explains: "cac",
          settled: pmfSettled,
          settledBy:
            "a cohort retains above 80% at month 6",
        },
        channelSaturation: {
          ...channelSaturation,
          method: "judgement",
        },
      },
    );

    if (cac < 400 && productMarketFit.probability > 0.6) {
      appendAudit(
        this.state,
        now,
        "decision",
        "CAC is below 400 and product-market fit is above 0.6",
        { cac, productMarketFit: productMarketFit.probability },
      );

      await this.scheduleBudgetIncrease(now);
    }

    if (paybackMonths > 12) {
      appendAudit(
        this.state,
        now,
        "decision",
        "Payback period exceeds 12 months",
        { paybackMonths },
      );

      await this.schedulePricingChange(now, paybackMonths);
    }

    if (productMarketFit.probability < 0.4) {
      const context = this.context(now);

      await this.ports.escalateToFounder({
        reason: "product_market_fit below 0.4",
        data: {
          productMarketFit: productMarketFit.probability,
          cac,
        },
        context,
      });

      appendAudit(
        this.state,
        now,
        "escalation",
        "Low product-market fit escalated to founder",
        {
          productMarketFit: productMarketFit.probability,
          founderSees: ["cac", "product_market_fit"],
        },
      );
    }

    this.state.lastRunAt = now.toISOString();
    return this.state;
  }

  private context(now: Date): ActionContext {
    return {
      now,
      state: this.state,
    };
  }

  private async observeBoardMonthly(now: Date): Promise<void> {
    const currentMonth = monthKey(now);

    if (this.state.lastBoardObservationMonth === currentMonth) {
      return;
    }

    const boardSentiment = await this.ports.observeBoardSentiment();

    if (boardSentiment.assertedBy !== "investor") {
      throw new Error(
        "board_sentiment must be asserted by the investor party",
      );
    }

    appendAudit(
      this.state,
      now,
      "observation",
      "Monthly board sentiment observed",
      boardSentiment,
    );

    this.state.lastBoardObservationMonth = currentMonth;
  }

  private async scheduleBudgetIncrease(now: Date): Promise<void> {
    if (hasPendingAction(this.state, "increase_budget")) {
      return;
    }

    const plan = await this.ports.planBudgetIncrease(this.context(now));

    if (
      !Number.isFinite(plan.additionalSpend) ||
      plan.additionalSpend < 0
    ) {
      throw new Error("Budget increase must be a non-negative finite number");
    }

    if (plan.additionalSpend > this.state.committedRunway) {
      appendAudit(
        this.state,
        now,
        "invariant_violation",
        "Rejected budget increase: spend exceeds committed runway",
        {
          additionalSpend: plan.additionalSpend,
          committedRunway: this.state.committedRunway,
        },
      );
      return;
    }

    const pending: PendingAction = {
      id: actionId("increase_budget", now),
      action: "increase_budget",
      createdAt: now.toISOString(),
      executeAt: addWeeks(now, 2).toISOString(),
      plannedSpend: plan.additionalSpend,
    };

    this.state.pendingActions.push(pending);

    appendAudit(
      this.state,
      now,
      "action_scheduled",
      "Reversible budget increase scheduled with a two-week delay",
      pending,
    );
  }

  private async schedulePricingChange(
    now: Date,
    paybackMonths: number,
  ): Promise<void> {
    if (hasPendingAction(this.state, "change_pricing")) {
      return;
    }

    const approved = await this.ports.requestFounderApproval({
      action: "change_pricing",
      reason: `payback_months is ${paybackMonths}, above target 12`,
      context: this.context(now),
    });

    if (!approved) {
      appendAudit(
        this.state,
        now,
        "action_rejected",
        "Founder did not approve the costly pricing change",
        { paybackMonths },
      );
      return;
    }

    const pending: PendingAction = {
      id: actionId("change_pricing", now),
      action: "change_pricing",
      createdAt: now.toISOString(),
      executeAt: addWeeks(now, 4).toISOString(),
      approvedBy: "founder",
    };

    this.state.pendingActions.push(pending);

    appendAudit(
      this.state,
      now,
      "action_scheduled",
      "Founder-approved pricing change scheduled with a four-week delay",
      pending,
    );
  }

  private async executeDueActions(now: Date): Promise<void> {
    const due = this.state.pendingActions.filter(
      (pending) => new Date(pending.executeAt).getTime() <= now.getTime(),
    );

    for (const pending of due) {
      if (pending.action === "increase_budget") {
        await this.executeBudgetIncrease(now, pending);
      } else {
        await this.ports.changePricing({
          context: this.context(now),
        });

        appendAudit(
          this.state,
          now,
          "action_executed",
          "Founder-approved costly pricing change executed",
          pending,
        );
      }

      this.state.pendingActions = this.state.pendingActions.filter(
        (candidate) => candidate.id !== pending.id,
      );
    }
  }

  private async executeBudgetIncrease(
    now: Date,
    pending: Extract<PendingAction, { action: "increase_budget" }>,
  ): Promise<void> {
    if (pending.plannedSpend > this.state.committedRunway) {
      appendAudit(
        this.state,
        now,
        "invariant_violation",
        "Cancelled budget increase at execution: spend exceeds committed runway",
        {
          plannedSpend: pending.plannedSpend,
          committedRunway: this.state.committedRunway,
        },
      );
      return;
    }

    await this.ports.increaseBudget({
      additionalSpend: pending.plannedSpend,
      context: this.context(now),
    });

    this.state.runway -= pending.plannedSpend;
    this.state.committedRunway -= pending.plannedSpend;

    appendAudit(
      this.state,
      now,
      "action_executed",
      "Reversible budget increase executed and runway consumed",
      {
        ...pending,
        remainingRunway: this.state.runway,
        remainingCommittedRunway: this.state.committedRunway,
      },
    );
  }
}

export function createCustomerAcquisitionFlue(
  ports: CustomerAcquisitionPorts,
  initialState: Partial<CustomerAcquisitionState> & {
    runway: number;
    committedRunway: number;
  },
): CustomerAcquisitionFlue {
  return new CustomerAcquisitionFlue(ports, {
    runway: initialState.runway,
    committedRunway: initialState.committedRunway,
    lastRunAt: initialState.lastRunAt,
    lastBoardObservationMonth: initialState.lastBoardObservationMonth,
    pendingActions: initialState.pendingActions ?? [],
    auditLog: initialState.auditLog ?? [],
  });
}
```

The host should invoke `run()` weekly and durably persist `CustomerAcquisitionState`. The observation and action ports connect the Flue to Stripe, the ad platform, interview storage, approval handling, and action executors.

## did not survive

- **Native daily observation scheduling:** the Flue runs weekly, so daily Stripe and ad-platform sampling must be aggregated by their observation ports or scheduled by the host.
- **Durable scheduling and persistence:** the two- and four-week delays are represented as pending actions, but reliable wake-up and state persistence require the hosting scheduler/database.
- **Concrete Bayesian and judgement algorithms:** the specification names methods but provides no model, priors, likelihoods, or judgement rubric, so both estimators remain typed ports.
- **`exit_channel` execution path:** the action is represented in metadata and as an executable port, but the specification contains no condition that invokes it.
- **Operational meaning of ignored factors:** `competitor_response` and `seasonality` survive as explicit metadata, but intentionally do not affect execution.