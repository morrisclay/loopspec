import { defineAgent } from '@flue/runtime';

/**
 * customer_acquisition — compiled from a URAS loop encoding.
 *
 * Loop -> Agent: an Agent is continuing and stateful with an identity, which is what a
 * non-terminating regulator needs. A Workflow would be wrong here — it is "a bounded job
 * that runs once and returns a result".
 *
 * TODO [estimand_never_estimated] `pmf` is declared as estimated state, but nothing in the loop produces an estimate of it — no estimator, no belief. It is named as something you track
 * TODO [estimand_never_estimated] `brand_strength` is declared as estimated state, but nothing in the loop produces an estimate of it — no estimator, no belief. It is named as somethin
 * TODO [orphan_signal] Signal `crm` is observed but is not connected to any estimand. You are collecting it without having said what it tells you.
 * TODO [orphan_signal] Signal `founder_interviews` is observed but is not connected to any estimand. You are collecting it without having said what it tells you.
 * TODO [no_loop_closed] 3 signal(s) and 2 intervention(s) are declared and NO loop closes between them. Nothing states which observation triggers which action, or on what cad
 * TODO [interventions_without_policy] 2 interventions are available (increase_budget, change_pricing) and no policy selects between them. Nothing states the condition under which you would
 * TODO [unmeasured_estimand] Estimand `pmf` has no signal measuring it. Any estimate of it is formed from something the encoding does not record.
 * TODO [unmeasured_estimand] Estimand `brand_strength` has no signal measuring it. Any estimate of it is formed from something the encoding does not record.
 */
export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `You regulate: customer_acquisition.

TARGET
  cac less_than 400

WHAT YOU ESTIMATE
  cac (computed)
  pmf (latent)
  brand_strength (latent)

WHAT YOU OBSERVE
  stripe
  crm
  founder_interviews

WHAT YOU MAY DO
  increase_budget
  change_pricing

TODO: no TimeScale declared — this loop has no cadence.

DesiredCondition compiles only to this prose. Flue has no structured goal representation,
so the target above is NOT machine-checkable at runtime. That is a platform gap, not a
modelling one.`,
}));
