import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

/** Estimator `pmf_estimator` -> Action. form: bayesian
 *
 * idempotency_basis: per_observation_batch
 * Flue: "recovery may re-dispatch the provider once — consistent with at-least-once
 * execution ... use application-owned idempotency keys where repeated effects would be
 * harmful." A Bayesian update applied twice double-counts its evidence into a well-formed
 * but WRONG posterior. The key below is that guard.
 */
export default defineAction({
  name: 'pmfEstimator',
  description: 'Update belief from observations',
  input: v.object({
    observations: v.array(v.unknown()),
    idempotencyKey: v.string(),   // derived from: per_observation_batch
  }),
  output: v.object({ estimate: v.unknown(), uncertainty: v.string() }),
  async run({ input }) {
    // TODO: reject if idempotencyKey already applied.
    return { estimate: null, uncertainty: 'unquantified' };
  },
});
