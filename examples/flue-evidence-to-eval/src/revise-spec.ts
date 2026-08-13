import { parse, stringify } from "yaml";

import type { DesignProposal } from "./types.js";

type Section = Record<string, unknown>;
type Rule = Record<string, unknown>;

interface MutableLoopSpec {
  beliefs: Section;
  observes: Section;
  actions: Section;
  spends: Record<string, Section>;
  when: Rule[];
  asks_human_when: string[];
  people: Record<string, Section>;
  [key: string]: unknown;
}

function appendUnique(values: unknown, value: string): string[] {
  const strings = Array.isArray(values) ? values.filter((item): item is string => typeof item === "string") : [];
  return strings.includes(value) ? strings : [...strings, value];
}

function requiredSection(parent: Record<string, Section>, key: string): Section {
  const value = parent[key];
  if (value === undefined) throw new Error(`base LoopSpec is missing ${key}`);
  return value;
}

export function applyProposal(baseYaml: string, proposal: DesignProposal): string {
  const document = parse(baseYaml) as MutableLoopSpec;
  const reviewAttention = requiredSection(document.spends, "review_attention");
  const supportLead = requiredSection(document.people, "support_lead");
  const outsideConsequence = requiredSection(document.observes as Record<string, Section>, "outside_consequence");

  for (const change of proposal.changes) {
    if (change.pattern === "restore_human_recovery") {
      document.beliefs.human_recovery_remains_available = {
        question: "Can the human still recover the focal task without assistance?",
        how: "typed cross-episode evidence join",
        explains: "resilient_focal_power",
        settled_by: "outside_consequence",
        safe_to_repeat: "episode id, probe condition, and semantic LoopSpec digest",
        checked_by: "five-case post-revision review",
        checked_against: "outside_consequence",
        scoring_rule: "paired capability and governance difference from the prior design",
        window: "five later cases",
        adjusts: "method",
        every: "after each five-case window"
      };
      document.observes.unaided_recovery_capability = {
        informs: "human_recovery_remains_available",
        origin: "ourselves",
        how: "calculated",
        source: "typed human-only removal probes"
      };
      outsideConsequence.informs = appendUnique(
        outsideConsequence.informs,
        "human_recovery_remains_available"
      );
      document.actions.run_unaided_recovery_checkpoint = {
        moves: "resilient_focal_power",
        through: "focal_work",
        effect: "increase",
        can_undo: "yes",
        needs_approval: "support_lead",
        effect_after: "within the next five cases",
        consumes: ["review_attention"]
      };
      document.when.push({
        if: "unaided recovery falls below the retained-capability floor",
        reads: ["human_recovery_remains_available"],
        do: "run_unaided_recovery_checkpoint"
      });
      document.asks_human_when = appendUnique(
        document.asks_human_when,
        "unaided recovery falls below the retained-capability floor"
      );
      reviewAttention.spent_by = appendUnique(
        reviewAttention.spent_by,
        "run_unaided_recovery_checkpoint"
      );
      supportLead.sees = appendUnique(
        supportLead.sees,
        "human_recovery_remains_available"
      );
    }

    if (change.pattern === "restore_intervention_window") {
      document.beliefs.intervention_path_is_live = {
        question: "Can the accountable person still stop the action before consequence?",
        how: "typed intervention-window evidence",
        explains: "resilient_focal_power",
        settled_by: "outside_consequence",
        safe_to_repeat: "episode id, action id, and semantic LoopSpec digest",
        checked_by: "pre-execution authority review",
        checked_against: "outside_consequence",
        scoring_rule: "seconds available before the consequence becomes irreversible",
        window: "five later cases",
        adjusts: "method",
        every: "after each five-case window"
      };
      document.observes.decision_to_execution_window = {
        informs: "intervention_path_is_live",
        origin: "ourselves",
        how: "calculated",
        source: "authorization and execution timestamps"
      };
      outsideConsequence.informs = appendUnique(
        outsideConsequence.informs,
        "intervention_path_is_live"
      );
      document.actions.require_pre_execution_confirmation = {
        moves: "resilient_focal_power",
        through: "focal_work",
        effect: "increase",
        can_undo: "yes",
        needs_approval: "support_lead",
        effect_after: "before the next consequential action",
        consumes: ["review_attention"]
      };
      document.when.push({
        if: "the effective intervention window is below one minute",
        reads: ["intervention_path_is_live"],
        do: "require_pre_execution_confirmation"
      });
      document.asks_human_when = appendUnique(
        document.asks_human_when,
        "the effective intervention window is below one minute"
      );
      reviewAttention.spent_by = appendUnique(
        reviewAttention.spent_by,
        "require_pre_execution_confirmation"
      );
      supportLead.sees = appendUnique(
        supportLead.sees,
        "intervention_path_is_live"
      );
    }
  }

  return stringify(document, { lineWidth: 100 });
}
