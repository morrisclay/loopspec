import { defineAction } from '@flue/runtime';
import * as v from 'valibot';

/** Intervention `increase_budget` -> Action. target: world

 * authorised by: founder
 */
export default defineAction({
  name: 'increaseBudget',
  description: 'increase budget',
  input: v.object({
    reason: v.string(),          // why the policy selected this intervention
    idempotencyKey: v.string(),  // REQUIRED: Flue documents at-least-once execution
  }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    log.info('increase_budget', { key: input.idempotencyKey });
    // TODO implement. Guard on idempotencyKey — a repeated dispatch must not double-apply.
    return { applied: false };
  },
});
