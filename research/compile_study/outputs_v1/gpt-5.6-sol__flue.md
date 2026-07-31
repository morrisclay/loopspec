<!-- model: openai/gpt-5.6-sol  tier: strong  target: flue  finish: stop -->

```ts
// customer-acquisition.flue.ts
//
// Register the default export with Flue's TypeScript runner. The workflow uses
// injected ports so data collection, durable storage, approvals, notifications,
// and action execution remain environment-specific.

export const definition = {
  loop: "customer_acquisition",
  runs: "weekly",

  goal: {
    cost_per_customer: {
      keep: "below 400",
      unit: "USD",
      from: ["ad_spend", "new_customers"],
    },
    payback_months: {
      keep: "below 12",
    },
  },

  beliefs: {
    product_market_fit: {
      question:
        "If we keep buying customers like this month's, will they stay?",
      from: ["customer_interviews", "stripe"],
      how: "bayesian",
      explains: "cost_per_customer",
      settled_by: "a cohort retains above 80% at month 6",
      known_bias:
        "reads high when volume is low — interviews only reach people who reply",
      checked_by: null,
    },

    channel_saturation: {
      question: "Can this channel absorb more money before cost climbs?",
      from: ["ad_platform"],
      how: "judgement",
      checked_by: "monthly_spend_vs_cost_review",
    },
  },

  observes: {
    stripe: {
      informs: "cost_per_customer",
      every: "daily",
      origin: "outside",
      how: "measured",
    },

    ad_platform: {
      informs: "channel_saturation",
      every: "daily",
      origin: "ourselves",
      how: "measured",
    },

    customer_interviews: {
      informs: "product_market_fit",
      every: "weekly",
      cost: "high",
      origin: "outside",
      how: "reported",
      reported_by: "customers",
    },

    board_sentiment: {
      informs: null,
      every: "monthly",
      origin: "outside",
      how: "reported",
      reported_by: "investor",
    },
  },

  actions: {
    increase_budget: {
      moves: "cost_per_customer",
      can_undo: "yes",
      effect_after: "2w",
      consumes: ["runway"],
    },

    change_pricing: {
      moves: "payback_months",
      can_undo: "costly",
      effect_after: "4w",
      needs_approval: "founder",
    },

    exit_channel: {
      moves: "cost_per_customer",
      can_undo: "no",
      needs_approval: null,
    },
  },

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

  people: {
    founder: {
      human: true,
      loses_if_wrong: "the company — runway, and 18-month survival odds",
      sees: ["cost_per_customer", "product_market_fit"],
      may_decide: "pricing, and anything that cannot be undone",
    },

    growth_agent: {
      agent: true,
      loses_if_wrong: "nothing",
      sees: [
        "cost_per_customer",
        "product_market_fit",
        "channel_saturation",
      ],
    },

    investor: {
      human: true,
      loses_if_wrong: "a position in the fund",
      sees: [],
    },
  },

  never: ["spend exceeds committed runway"],

  not_modelling: ["competitor_response", "seasonality"],
} as const;

type ActionName = keyof typeof definition.actions;

export interface CostSample {
  at: string;
  valueUsd: number;
}

export interface CustomerAcquisitionSnapshot {
  /**
   * Values must be the latest values available when the weekly run starts.
   * The adapter may calculate costPerCustomerUsd as:
   * adSpendUsd / newCustomers.
   */
  adSpendUsd: number;
  newCustomers: number;
  costPerCustomerUsd?: number;

  /**
   * The source spec does not define a formula or source for this metric.
   */
  paybackMonths: number;

  /**
   * Posterior probability produced by the externally configured Bayesian model.
   */
  productMarketFit: number;

  /**
   * Result of the monthly_spend_vs_cost_review judgement process.
   */
  channelSaturation: number | string;

  /**
   * Daily history, including the current sample, used for the 14-day rule.
   */
  costPerCustomerHistory: CostSample[];

  /**
   * Current spend and the maximum amount committed for spending.
   */
  spendUsd: number;
  committedRunwayUsd: number;
}

export interface ActionRequest {
  action: ActionName;
  effectExpectedAt?: string;
  idempotencyKey: string;
  constraints: {
    spendMustNotExceedCommittedRunway: true;
  };
  snapshot: CustomerAcquisitionSnapshot;
}

export interface FluePorts {
  now(): Date;

  observations: {
    snapshot(): Promise<CustomerAcquisitionSnapshot>;
  };

  state: {
    get<T>(key: string): Promise<T | undefined>;
    set<T>(key: string, value: T): Promise<void>;
  };

  approvals: {
    request(input: {
      approver: "founder";
      subject: string;
      reason: string;
      context: Record<string, unknown>;
      idempotencyKey: string;
    }): Promise<"approved" | "rejected">;
  };

  humans: {
    notify(input: {
      person: "founder";
      reason: string;
      context: Record<string, unknown>;
      idempotencyKey: string;
    }): Promise<void>;
  };

  actions: {
    execute(request: ActionRequest): Promise<void>;
  };
}

export interface FlueWorkflow {
  id: string;
  schedule: {
    cron: string;
    timezone: string;
  };
  definition: typeof definition;
  run(ports: FluePorts): Promise<void>;
}

function addDays(date: Date, days: number): string {
  return new Date(date.getTime() + days * 86_400_000).toISOString();
}

function requireFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) {
    throw new Error(`${name} must be a finite number`);
  }
}

function stayedAboveForDays(
  samples: CostSample[],
  threshold: number,
  days: number,
  now: Date,
): boolean {
  const cutoff = now.getTime() - days * 86_400_000;

  const normalized = samples
    .map((sample) => ({
      at: new Date(sample.at).getTime(),
      value: sample.valueUsd,
    }))
    .filter(
      (sample) =>
        Number.isFinite(sample.at) &&
        Number.isFinite(sample.value) &&
        sample.at <= now.getTime(),
    )
    .sort((a, b) => a.at - b.at);

  const samplesInWindow = normalized.filter((sample) => sample.at >= cutoff);
  const hasCoverageAtStart = normalized.some((sample) => sample.at <= cutoff);

  return (
    hasCoverageAtStart &&
    samplesInWindow.length > 0 &&
    samplesInWindow.every((sample) => sample.value > threshold)
  );
}

async function notifyFounder(
  ports: FluePorts,
  runId: string,
  reason: string,
  snapshot: CustomerAcquisitionSnapshot,
): Promise<void> {
  await ports.humans.notify({
    person: "founder",
    reason,
    context: {
      cost_per_customer: snapshot.costPerCustomerUsd,
      product_market_fit: snapshot.productMarketFit,
      payback_months: snapshot.paybackMonths,
    },
    idempotencyKey: `${runId}:human:${reason}`,
  });
}

async function executeAction(
  ports: FluePorts,
  runId: string,
  action: ActionName,
  snapshot: CustomerAcquisitionSnapshot,
  now: Date,
): Promise<void> {
  const actionDefinition = definition.actions[action];

  if (actionDefinition.can_undo === "no") {
    await notifyFounder(
      ports,
      runId,
      `Irreversible action ${action} became a chosen move`,
      snapshot,
    );

    // Founder may decide anything that cannot be undone. No irreversible action
    // executes without explicit approval, including exit_channel.
    const decision = await ports.approvals.request({
      approver: "founder",
      subject: `Approve irreversible action: ${action}`,
      reason: `${action} has can_undo=no`,
      context: { action, snapshot },
      idempotencyKey: `${runId}:approval:${action}`,
    });

    if (decision !== "approved") return;
  }

  if (
    "needs_approval" in actionDefinition &&
    actionDefinition.needs_approval === "founder"
  ) {
    const decision = await ports.approvals.request({
      approver: "founder",
      subject: `Approve action: ${action}`,
      reason: `${action} changes pricing and is costly to undo`,
      context: { action, snapshot },
      idempotencyKey: `${runId}:approval:${action}`,
    });

    if (decision !== "approved") return;
  }

  const effectExpectedAt =
    action === "increase_budget"
      ? addDays(now, 14)
      : action === "change_pricing"
        ? addDays(now, 28)
        : undefined;

  await ports.actions.execute({
    action,
    effectExpectedAt,
    idempotencyKey: `${runId}:action:${action}`,
    constraints: {
      spendMustNotExceedCommittedRunway: true,
    },
    snapshot,
  });
}

export const customerAcquisition: FlueWorkflow = {
  id: definition.loop,

  // "Weekly" has no day or time in the source, so this chooses Monday 09:00 UTC.
  schedule: {
    cron: "0 9 * * 1",
    timezone: "UTC",
  },

  definition,

  async run(ports): Promise<void> {
    const now = ports.now();
    const runId = `${definition.loop}:${now.toISOString().slice(0, 10)}`;
    const snapshot = await ports.observations.snapshot();

    requireFinite("adSpendUsd", snapshot.adSpendUsd);
    requireFinite("newCustomers", snapshot.newCustomers);
    requireFinite("paybackMonths", snapshot.paybackMonths);
    requireFinite("productMarketFit", snapshot.productMarketFit);
    requireFinite("spendUsd", snapshot.spendUsd);
    requireFinite("committedRunwayUsd", snapshot.committedRunwayUsd);

    if (snapshot.costPerCustomerUsd === undefined) {
      snapshot.costPerCustomerUsd =
        snapshot.newCustomers > 0
          ? snapshot.adSpendUsd / snapshot.newCustomers
          : Number.POSITIVE_INFINITY;
    }

    const previousProductMarketFit = await ports.state.get<number>(
      "product_market_fit.previous",
    );

    // Hard invariant: never spend beyond committed runway.
    if (snapshot.spendUsd > snapshot.committedRunwayUsd) {
      await notifyFounder(
        ports,
        runId,
        "Hard invariant violated: spend exceeds committed runway",
        snapshot,
      );

      await ports.state.set(
        "product_market_fit.previous",
        snapshot.productMarketFit,
      );

      throw new Error("Blocked: spend exceeds committed runway");
    }

    if (
      previousProductMarketFit !== undefined &&
      previousProductMarketFit >= 0.4 &&
      snapshot.productMarketFit < 0.4
    ) {
      await notifyFounder(
        ports,
        runId,
        "product_market_fit fell below 0.4",
        snapshot,
      );
    }

    if (
      stayedAboveForDays(
        snapshot.costPerCustomerHistory,
        600,
        14,
        now,
      )
    ) {
      await notifyFounder(
        ports,
        runId,
        "cost_per_customer stayed above 600 USD for 14 days",
        snapshot,
      );
    }

    const chosenActions: ActionName[] = [];

    if (
      snapshot.costPerCustomerUsd < 400 &&
      snapshot.productMarketFit > 0.6
    ) {
      chosenActions.push("increase_budget");
    }

    if (snapshot.paybackMonths > 12) {
      chosenActions.push("change_pricing");
    }

    for (const action of chosenActions) {
      await executeAction(ports, runId, action, snapshot, now);
    }

    await ports.state.set(
      "product_market_fit.previous",
      snapshot.productMarketFit,
    );
  },
};

export default customerAcquisition;
```

## did not survive

- Flue cannot infer the Bayesian prior, likelihood, or evidence-to-posterior mapping for `product_market_fit`; the implementation therefore consumes the externally calculated posterior.
- The spec provides no source or formula for `payback_months`, so it must be supplied by the observation adapter.
- `ad_spend` and `new_customers` are referenced by the goal but are not declared observations. They are supplied through the snapshot adapter; the implementation derives cost per customer by division when needed.
- The actions do not specify operational parameters such as the budget increment, pricing change, or channel identifier. Those details must be supplied by the action adapter.
- `runs: weekly` does not specify a weekday, time, or timezone. The implementation chooses Monday at 09:00 UTC.
- If both `when` clauses match, the spec does not define conflict resolution or a single-move selection rule. The implementation executes both in declaration order.
