<!-- model: anthropic/claude-opus-5  tier: strong  target: flue  finish: length -->

## What I'm targeting

I could not identify a framework named **Flue** for TypeScript (no package, no docs I can resolve). Rather than silently invent an API and call it Flue, I've written the loop as a small self-contained kernel plus a **declarative spec module that is a 1:1 transliteration of the YAML**. If a real Flue exists, `flue/kernel.ts` is the only file you replace — `loops/customer_acquisition.loop.ts` is the spec and should port unchanged. This is logged as the first entry under *did not survive*.

Everything the spec says is present in code. Where the spec states something a runtime cannot execute (prose, `known_bias`, `loses_if_wrong`, `not_modelling`), it is carried as data, printed, and — where relevant — hand-compiled into a predicate with the original prose kept next to it, so you can see exactly where I guessed.

---

### `flue/kernel.ts`

```ts
// ─────────────────────────────────────────────────────────────────────────────
// A minimal loop kernel. Vocabulary is taken from the v1 loop format:
// goal / beliefs / observes / actions / when / asks_human_when / people /
// never / not_modelling.
// ─────────────────────────────────────────────────────────────────────────────

export const DAY = 86_400_000;
export const CADENCE = { daily: DAY, weekly: 7 * DAY, monthly: 30 * DAY } as const;
export type Cadence = keyof typeof CADENCE;

export type Op = 'below' | 'above';
export type Origin = 'outside' | 'ourselves';
export type How = 'measured' | 'reported';
export type Undo = 'yes' | 'costly' | 'no';
export type Method = 'bayesian' | 'judgement';
export type Cost = 'low' | 'high';

/** Spec text that no runtime can evaluate, paired with a hand-written predicate.
 *  `text` is authoritative for humans; `compiled` is what actually runs. */
export interface Prose<T> { text: string; compiled: T }
export const prose = <T>(text: string, compiled: T): Prose<T> => ({ text, compiled });

export interface Reading { value: number; n?: number; at: number }
export interface Provenance {
  source: string; origin: Origin; how: How; reportedBy?: string; at: number;
  selfSelected: boolean; // how: reported ⇒ the subject chose what to say
}

export interface Snapshot {
  now: number;
  metrics: Record<string, number | undefined>;
  beliefs: Record<string, number | undefined>;
  settled: Record<string, boolean>;
  facts: Record<string, number>;
  readings: Record<string, Reading | undefined>;
  provenance: Record<string, Provenance | undefined>;
}

export const signal = (s: Snapshot, name: string): number | undefined =>
  s.metrics[name] ?? s.beliefs[name];

// ── spec shapes ──────────────────────────────────────────────────────────────

export interface Threshold { op: Op; value: number }

export interface GoalDef {
  keep: string;                 // "below 400"
  unit?: string;
  from?: string[];
  bound?: Threshold;            // parsed from `keep`
}

export interface BeliefDef {
  question: string;
  from: string[];
  how: Method;
  explains?: string;
  settled_by?: Prose<(s: Snapshot) => boolean>;
  known_bias?: string;          // recorded, attached to every update. Not enforceable.
  checked_by?: string;
}

export interface ObserveDef {
  informs?: string;
  every: Cadence;
  origin: Origin;
  how: How;
  reported_by?: string;
  cost?: Cost;
}

export interface ActionDef {
  moves: string;
  can_undo: Undo;
  effect_after?: string;        // "2w"
  consumes?: string[];
  needs_approval?: string;
}

export interface RuleDef { if: string; do: string }

export type Trigger =
  | { kind: 'falls_below'; sig: string; value: number }
  | { kind: 'stays'; sig: string; op: Op; value: number; forMs: number }
  | { kind: 'action_shape'; test: (a: ActionDef & { name: string }) => boolean };

export interface EscalationDef { text: string; trigger: Trigger }

export interface Invariant {
  text: string;
  violated: (s: Snapshot) => boolean;
  wouldViolate?: (s: Snapshot, action: string, def: ActionDef) => boolean;
}

export interface PersonDef {
  human?: boolean;
  agent?: boolean;
  loses_if_wrong: string;       // recorded only
  sees: string[];
  may_decide?: Prose<(a: ActionDef & { name: string }) => boolean>;
}

export interface LoopSpec {
  loop: string;
  runs: Cadence;
  goal: Record<string, GoalDef>;
  beliefs: Record<string, BeliefDef>;
  observes: Record<string, ObserveDef>;
  actions: Record<string, ActionDef>;
  when: RuleDef[];
  asks_human_when: EscalationDef[];
  people: Record<string, PersonDef>;
  never: Invariant[];
  not_modelling: string[];
}

// ── parsers ──────────────────────────────────────────────