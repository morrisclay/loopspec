import { defineTool } from '@flue/runtime';
import * as v from 'valibot';

/** Signal `crm` -> read-only Tool.
 * measures: NOTHING — orphan signal, the encoding does not say what it tells you
 */
export default defineTool({
  name: 'crm',
  description: 'Read crm',
  input: v.object({}),
  output: v.object({ value: v.unknown(), observedAt: v.string() }),
  async run() {
    // TODO connect to the real source.
    return { value: null, observedAt: new Date().toISOString() };
  },
});
