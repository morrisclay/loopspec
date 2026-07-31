import { defineTool } from '@flue/runtime';
import * as v from 'valibot';

/** Signal `stripe` -> read-only Tool.
 * measures: cac
 */
export default defineTool({
  name: 'stripe',
  description: 'Read stripe',
  input: v.object({}),
  output: v.object({ value: v.unknown(), observedAt: v.string() }),
  async run() {
    // TODO connect to the real source.
    return { value: null, observedAt: new Date().toISOString() };
  },
});
