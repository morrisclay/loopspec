<!-- model: deepseek/deepseek-v3.2-exp  tier: mid  target: flue  finish: stop -->

Looking at this loop spec, I can see several concepts that Flue (TypeScript) cannot directly express. Here's what I can implement:

```typescript
// Customer Acquisition Loop Implementation in Flue (TypeScript)

interface LoopMetrics {
  cac: number;           // Customer Acquisition Cost
  paybackMonths: number; // Payback period in months
  productMarketFit: number; // 0-1 score
  channelSaturation: number; // 0-1 score
}

interface LoopState {
  metrics: LoopMetrics;
  lastUpdated: Date;
  adSpend: number;
  newCustomers: number;
  runway: number;
}

interface Observation {
  stripe: {
    cac: number;
    timestamp: Date;
  };
  adPlatform: {
    channelSaturation: number;
    timestamp: Date;
  };
  customerInterviews: {
    productMarketFit: number;
    timestamp: Date;
    cost: 'high';
  };
  boardSentiment: {
    assertedBy: 'investor';
    timestamp: Date;
  };
}

class CustomerAcquisitionLoop {
  private state: LoopState;
  private observations: Observation;
  
  // Weekly execution interval
  private readonly EVERY_WEEKLY = 7 * 24 * 60 * 60 * 1000;
  
  constructor(initialState: Partial<LoopState> = {}) {
    this.state = {
      metrics: {
        cac: 0,
        paybackMonths: 0,
        productMarketFit: 0.5,
        channelSaturation: 0.5,
      },
      lastUpdated: new Date(),
      adSpend: 0,
      newCustomers: 0,
      runway: 12, // months
      ...initialState
    };
    
    this.observations = {
      stripe: { cac: 0, timestamp: new Date() },
      adPlatform: { channelSaturation: 0.5, timestamp: new Date() },
      customerInterviews: { productMarketFit: 0.5, timestamp: new Date(), cost: 'high' },
      boardSentiment: { assertedBy: 'investor', timestamp: new Date() }
    };
  }
  
  // Compute CAC from ad spend and new customers
  private computeCAC(): number {
    if (this.state.newCustomers === 0) return 0;
    return this.state.adSpend / this.state.newCustomers;
  }
  
  // Update metrics based on observations
  public updateMetrics(): void {
    // Update CAC from Stripe observation
    this.state.metrics.cac = this.observations.stripe.cac;
    
    // Also compute from internal state for comparison
    const computedCAC = this.computeCAC();
    
    // Update product market fit from customer interviews
    this.state.metrics.productMarketFit = this.observations.customerInterviews.productMarketFit;
    
    // Update channel saturation from ad platform
    this.state.metrics.channelSaturation = this.observations.adPlatform.channelSaturation;
    
    this.state.lastUpdated = new Date();
  }
  
  // Check conditions and trigger actions
  public evaluateConditions(): void {
    const { cac, productMarketFit, paybackMonths } = this.state.metrics;
    
    // Rule 1: If CAC < 400 and PMF > 0.6
    if (cac < 400 && productMarketFit > 0.6) {
      this.increaseBudget();
    }
    
    // Rule 2: If payback months > 12
    if (paybackMonths > 12) {
      this.changePricing();
    }
    
    // Rule 3: If PMF < 0.4
    if (productMarketFit < 0.4) {
      this.escalateToFounder();
    }
  }
  
  // Action: Increase budget
  private increaseBudget(): void {
    console.log('Action: increase_budget triggered');
    // Note: In Flue, we can't represent:
    // - reversibility: reversible
    // - delay: 2w
    // - consumes: [runway]
    // These would need to be implemented in application logic
  }
  
  // Action: Change pricing
  private changePricing(): void {
    console.log('Action: change_pricing triggered');
    // Note: In Flue, we can't represent:
    // - reversibility: costly
    // - delay: 4w
    // - approval: founder
  }
  
  // Action: Exit channel
  private exitChannel(): void {
    console.log('Action: exit_channel triggered');
    // Note: In Flue, we can't represent:
    // - reversibility: irreversible
  }
  
  // Escalate to founder
  private escalateToFounder(): void {
    console.log('Escalating to founder: product_market_fit below 0.4');
  }
  
  // Safety check: Never spend exceeds committed runway
  private safetyCheck(): boolean {
    // Simplified check - in reality would compare spend rate vs runway
    return this.state.runway > 0;
  }
  
  // Main loop execution
  public run(): void {
    if (!this.safetyCheck()) {
      console.error('Safety check failed: spend exceeds committed runway');
      return;
    }
    
    this.updateMetrics();
    this.evaluateConditions();
  }
  
  // Update observations (simulating data sources)
  public updateObservation(
    source: keyof Observation,
    data: Partial<Observation[keyof Observation]>
  ): void {
    this.observations[source] = {
      ...this.observations[source],
      ...data,
      timestamp: new Date()
    } as any;
  }
  
  // Get current state for display
  public getState(): LoopState {
    return { ...this.state };
  }
}

// Example usage
const loop = new CustomerAcquisitionLoop();

// Simulate weekly execution
setInterval(() => {
  loop.run();
}, loop.EVERY_WEEKLY);

// Simulate receiving observations
loop.updateObservation('stripe', { cac: 350 });
loop.updateObservation('customerInterviews', { productMarketFit: 0.7 });
loop.updateObservation('adPlatform', { channelSaturation: 0.3 });

// Run once
loop.run();
```

## did not survive

1. **Bayesian estimation method for product_market_fit** - Flue has no built-in Bayesian inference engine or statistical method specification. The `method: bayesian` specification cannot be represented.

2. **Estimation `explains` and `settled_by` relationships** - Flue cannot represent causal/explanatory relationships between estimates and metrics. The `explains: cac` relationship and `settled_by` criteria cannot be encoded.

3. **Judgement method for channel_saturation** - The `method: judgement` specification indicating human judgment cannot be represented in code.

4. **Cost specification for observations** - The `cost: high` property on customer_interviews cannot be represented in the type system.

5. **Assertion-based observations** - The `asserted_by: investor` property for board_sentiment cannot be enforced in code.

6. **Action properties**: 
   - `reversibility` (reversible/costly/irreversible) - No equivalent concept in Flue
   - `delay` (2w/4w) - Cannot represent action delays with time units
   - `consumes: [runway]` - Cannot represent resource consumption semantics
   - `approval: founder` - Cannot represent approval workflows

7. **Party system**:
   - `human: true`/`agent: true` distinctions - Cannot represent actor types
   - `bears:` relationships - Cannot represent responsibility/ownership semantics
   - `sees:` permissions - Cannot represent access control

8. **Never conditions as first-class constraints** - The `never: "spend exceeds committed runway"` cannot be represented as a declarative constraint, only as imperative code.

9. **Ignoring list** - The `ignoring:` section specifying what to ignore cannot be represented.

10. **Loop metadata** - The `every: weekly` specification is implemented imperatively but cannot be declared.

11. **Target specifications** - `target: "< 400"` for cac and payback_months cannot be represented as declarative targets.

The implementation captures the core logic and data flow but loses the declarative specifications, type distinctions, and semantic relationships from the original spec.