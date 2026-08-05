import copy
import glob
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import loop as loop_language  # noqa: E402
import derive  # noqa: E402
import validate as semantic_validator  # noqa: E402
import external_eval  # noqa: E402
import semantic_diff  # noqa: E402
import loopspec as loopspec_cli  # noqa: E402


def minimal_spec(**overrides):
    spec = {
        "loop": "level control",
        "runs": "daily",
        "goal": {"level": {"keep": "above 1"}},
        "observes": {"level reading": {"informs": "level", "origin": "outside"}},
        "actions": {"raise level": {"moves": "level", "can_undo": "yes"}},
        "when": [{"if": "level below 1", "do": "raise level"}],
    }
    spec.update(overrides)
    return spec


def expand_spec(spec):
    graph = loop_language.Graph()
    loop_language.expand_one(graph, copy.deepcopy(spec), "<test>")
    return graph.doc("level_control")


def reverse_mappings(value):
    if isinstance(value, dict):
        return dict(reversed([(key, reverse_mappings(item))
                              for key, item in value.items()]))
    if isinstance(value, list):
        return [reverse_mappings(item) for item in value]
    return value


def semantic_signature(doc):
    loops = {}
    for item in doc.get("loops") or []:
        loop = copy.deepcopy(item)
        for field in ("signals", "interventions", "estimands", "desired_conditions",
                      "policies", "processes"):
            if field in loop:
                loop[field] = sorted(loop[field])
        loops[loop["id"]] = loop
    return {
        "nodes": {node["id"]: node for node in doc.get("nodes") or []},
        "edges": sorted((edge["from"], edge["rel"], edge["to"])
                        for edge in doc.get("edges") or []),
        "loops": loops,
        "excluded_variables": sorted(doc.get("excluded_variables") or []),
        "considered": doc.get("considered") or {},
    }


class SemanticPipelineTests(unittest.TestCase):
    def validate_canonical(self, doc):
        _, core, all_primitives, _ = semantic_validator.load_catalog()
        report = semantic_validator.Report()
        semantic_validator.check_encoding("<generated>", doc, core, all_primitives, report)
        return report

    def test_canonical_cadence_comes_from_runs(self):
        doc = expand_spec(minimal_spec())

        self.assertEqual(2, doc["loopspec_version"])
        self.assertEqual("every_daily", doc["loops"][0]["timescale"])
        self.assertEqual("daily", next(
            node["period"] for node in doc["nodes"]
            if node["id"] == "every_daily"
        ))

    def test_generated_graph_passes_the_canonical_validator(self):
        doc, warnings = loop_language.expand(
            os.path.join(ROOT, "examples", "customer_acquisition.loop.yaml")
        )

        self.assertEqual([], warnings)
        report = self.validate_canonical(doc)
        self.assertTrue(report.ok, report.errors)

    def test_ir2_edges_are_type_checked(self):
        doc = expand_spec(minimal_spec(when=[{
            "if": "level below 1",
            "reads": ["level"],
            "do": "raise level",
        }]))
        read_edge = next(edge for edge in doc["edges"] if edge["rel"] == "reads")
        read_edge["from"] = "level_reading"

        report = self.validate_canonical(doc)

        self.assertFalse(report.ok)
        self.assertTrue(any("kind signature" in error for error in report.errors))

    def test_control_plane_nodes_are_not_world_interventions(self):
        spec = minimal_spec(
            actions={"execute tool": {"moves": "level"}},
            action_profiles={
                "approved write": {
                    "action": "execute tool",
                    "when": "the request matches deployment approval policy",
                    "resolved_at": "request",
                    "can_undo": "unknown",
                    "needs_approval": "operator",
                },
                "unmatched tool request": {
                    "action": "execute tool",
                    "default": True,
                    "resolved_at": "request",
                    "can_undo": "unknown",
                },
            },
            operations={
                "interrupt turn": {
                    "kind": "interrupt",
                    "authorized_by": "operator",
                },
                "finish turn": {
                    "kind": "stop",
                    "when": "the model returns a final response",
                    "emits": "final response",
                },
            },
            outputs={
                "final response": {"kind": "final", "terminates": "turn"},
            },
            people={
                "operator": {"human": True, "loses_if_wrong": "repository integrity"},
            },
            when=[{"if": "level below 1", "do": "execute tool"}],
        )

        doc = expand_spec(spec)
        nodes = {node["id"]: node for node in doc["nodes"]}
        findings, failures = derive.analyze_document(doc)

        self.assertEqual("2.2", doc["ir_revision"])
        self.assertEqual("loop-v1.2", doc["source_format"])
        self.assertEqual("Intervention", nodes["execute_tool"]["kind"])
        self.assertEqual("ActionProfile", nodes["approved_write"]["kind"])
        self.assertEqual("ControlOperation", nodes["interrupt_turn"]["kind"])
        self.assertEqual("Output", nodes["final_response"]["kind"])
        self.assertIn({"from": "approved_write", "to": "execute_tool", "rel": "profiles"},
                      doc["edges"])
        self.assertIn({"from": "operator", "to": "approved_write", "rel": "authorizes"},
                      doc["edges"])
        self.assertIn({"from": "finish_turn", "to": "final_response", "rel": "emits"},
                      doc["edges"])
        self.assertEqual([], failures)
        self.assertFalse(any(
            finding["pattern"] == "reversibility_unspecified" and
            finding["evidence"].get("action") in {
                "execute_tool", "approved_write", "unmatched_tool_request"
            }
            for finding in findings
        ))
        self.assertTrue(self.validate_canonical(doc).ok)

    def test_action_profiles_require_an_explicit_fallback_for_unmatched_requests(self):
        doc = expand_spec(minimal_spec(
            actions={"execute tool": {"moves": "level"}},
            action_profiles={
                "approved write": {
                    "action": "execute tool",
                    "when": "the deployment policy requires approval",
                    "resolved_at": "request",
                    "can_undo": "unknown",
                },
            },
            when=[{"if": "level below 1", "do": "execute tool"}],
        ))

        findings, failures = derive.analyze_document(doc)

        self.assertEqual([], failures)
        self.assertIn("action_profiles_without_fallback",
                      {finding["pattern"] for finding in findings})

    def test_explicit_unknown_reversibility_is_valid_and_never_treated_as_safe(self):
        doc = expand_spec(minimal_spec(actions={
            "raise level": {"moves": "level", "can_undo": "unknown"},
        }))
        nodes = {node["id"]: node for node in doc["nodes"]}
        findings, failures = derive.analyze_document(doc)

        self.assertEqual("unknown", nodes["raise_level"]["reversibility"])
        self.assertEqual([], failures)
        self.assertNotIn("reversibility_unspecified",
                         {finding["pattern"] for finding in findings})
        self.assertNotIn("irreversible_without_approval",
                         {finding["pattern"] for finding in findings})

    def test_control_plane_references_and_profile_precedence_fail_closed(self):
        bad_profile = minimal_spec(
            action_profiles={
                "missing": {
                    "action": "not an action",
                    "default": True,
                    "resolved_at": "deployment",
                    "can_undo": "unknown",
                },
            },
        )
        with self.assertRaisesRegex(loop_language.SpecError, "names no entry in `actions`"):
            expand_spec(bad_profile)

        bad_output = minimal_spec(
            operations={"finish": {"kind": "stop", "emits": "missing output"}},
        )
        with self.assertRaisesRegex(loop_language.SpecError, "names no entry in `outputs`"):
            expand_spec(bad_output)

        mixed = minimal_spec(
            action_profiles={
                "fallback": {
                    "action": "raise level",
                    "default": True,
                    "resolved_at": "design",
                    "can_undo": "yes",
                },
            },
        )
        with self.assertRaisesRegex(loop_language.SpecError, "cannot be mixed"):
            expand_spec(mixed)

    def test_control_plane_identity_is_canonical_and_machine_checked(self):
        duplicate_outputs = minimal_spec(outputs={
            "first failure": {"kind": "failure", "terminates": "run"},
            "second failure": {"kind": "failure", "terminates": "run"},
        })
        with self.assertRaisesRegex(loop_language.SpecError, "duplicates output role"):
            expand_spec(duplicate_outputs)

        duplicate_operations = minimal_spec(
            outputs={"failure": {"kind": "failure", "terminates": "run"}},
            operations={
                "budget stop": {"kind": "stop", "when": "budget exhausted", "emits": "failure"},
                "error stop": {"kind": "stop", "when": "terminal error", "emits": "failure"},
            },
        )
        with self.assertRaisesRegex(loop_language.SpecError, "duplicates controller role"):
            expand_spec(duplicate_operations)

        duplicate_profiles = minimal_spec(
            action_profiles={
                "remote tool": {
                    "action": "raise level", "when": "remote deployment",
                    "resolved_at": "deployment", "can_undo": "unknown",
                },
                "fallback": {
                    "action": "raise level", "default": True,
                    "resolved_at": "deployment", "can_undo": "unknown",
                },
            },
        )
        with self.assertRaisesRegex(loop_language.SpecError, "duplicates the typed properties"):
            expand_spec(duplicate_profiles)

        lone_default = minimal_spec(
            actions={"raise level": {"moves": "level"}},
            action_profiles={
                "fallback": {
                    "action": "raise level", "default": True,
                    "resolved_at": "request", "can_undo": "unknown",
                },
            },
        )
        lone_default_findings, _ = derive.analyze_document(expand_spec(lone_default))
        self.assertIn("action_profiles_without_safety_variation",
                      {finding["pattern"] for finding in lone_default_findings})

        stage_only_variation = minimal_spec(
            actions={"raise level": {"moves": "level"}},
            action_profiles={
                "configured": {
                    "action": "raise level", "when": "configured tool",
                    "resolved_at": "deployment", "can_undo": "unknown",
                },
                "fallback": {
                    "action": "raise level", "default": True,
                    "resolved_at": "request", "can_undo": "unknown",
                },
            },
        )
        with self.assertRaisesRegex(loop_language.SpecError,
                                    "binding stage alone is not a safety distinction"):
            expand_spec(stage_only_variation)

    def test_known_section_qualified_local_references_normalize_to_canonical_names(self):
        canonical = minimal_spec(
            goal={"level": {"keep": "above 1", "from": ["level reading"]}},
            beliefs={
                "risk": {
                    "from": ["risk report"],
                    "checked_against": "risk outcome",
                    "explains": "level",
                    "settled_by": "risk outcome",
                },
            },
            observes={
                "level reading": {
                    "informs": "level", "origin": "outside", "how": "reported",
                    "reported_by": "operator",
                },
                "risk report": {"informs": "risk", "origin": "outside"},
                "risk outcome": {"informs": "risk", "origin": "ourselves",
                                 "produced_by": "raise level"},
            },
            actions={
                "raise level": {
                    "moves": ["level", "risk"], "can_undo": "unknown",
                    "needs_approval": "operator", "consumes": ["energy"],
                    "through": "reservoir",
                },
            },
            operations={
                "finish": {"kind": "stop", "authorized_by": "operator",
                           "emits": "final result"},
            },
            outputs={"final result": {"kind": "final", "terminates": "run"}},
            processes={"reservoir": {"observed_as": ["level reading"]}},
            people={
                "operator": {"human": True, "loses_if_wrong": "overflow",
                             "sees": ["level", "risk"]},
            },
            spends={"energy": {"spent_by": "raise level"}},
            boundary={"drawn_by": "operator", "purpose": "regulate level"},
            asks_human="operator",
            when=[{
                "if": "level below 1", "reads": ["level", "risk", "energy"],
                "against": ["level"], "do": "raise level", "escalate": "operator",
            }],
        )
        qualified = copy.deepcopy(canonical)
        qualified["goal"]["level"]["from"] = ["observes.level reading"]
        qualified["beliefs"]["risk"].update({
            "from": ["observes.risk report"],
            "checked_against": "observes.risk outcome",
            "explains": "goal.level",
            "settled_by": "observes.risk outcome",
        })
        qualified["observes"]["level reading"].update({
            "informs": "goal.level", "reported_by": "people.operator",
        })
        qualified["observes"]["risk report"]["informs"] = "beliefs.risk"
        qualified["observes"]["risk outcome"].update({
            "informs": "beliefs.risk", "produced_by": "actions.raise level",
        })
        qualified["actions"]["raise level"].update({
            "moves": ["goal.level", "beliefs.risk"],
            "needs_approval": "people.operator",
            "consumes": ["spends.energy"],
            "through": "processes.reservoir",
        })
        qualified["operations"]["finish"].update({
            "authorized_by": "people.operator", "emits": "outputs.final result",
        })
        qualified["processes"]["reservoir"]["observed_as"] = [
            "observes.level reading"
        ]
        qualified["people"]["operator"]["sees"] = ["goal.level", "beliefs.risk"]
        qualified["spends"]["energy"]["spent_by"] = "actions.raise level"
        qualified["boundary"]["drawn_by"] = "people.operator"
        qualified["asks_human"] = "people.operator"
        qualified["when"][0].update({
            "reads": ["goal.level", "beliefs.risk", "spends.energy"],
            "against": ["goal.level"], "do": "actions.raise level",
            "escalate": "people.operator",
        })

        self.assertEqual(
            semantic_signature(expand_spec(canonical)),
            semantic_signature(expand_spec(qualified)),
        )

    def test_loop_membership_is_lossless_and_not_order_dependent(self):
        first = minimal_spec(
            observes={
                "primary reading": {"informs": "level"},
                "safety reading": {"informs": "level"},
            },
            actions={
                "raise level": {"moves": "level"},
                "stop system": {"moves": "level"},
            },
            when=[{"if": "level below 1", "do": ["raise level", "stop system"]}],
        )
        second = copy.deepcopy(first)
        second["observes"] = dict(reversed(list(second["observes"].items())))
        second["actions"] = dict(reversed(list(second["actions"].items())))

        loop_a = expand_spec(first)["loops"][0]
        loop_b = expand_spec(second)["loops"][0]

        self.assertNotIn("signal", loop_a)
        self.assertNotIn("intervention", loop_a)
        self.assertEqual(set(loop_a["signals"]), set(loop_b["signals"]))
        self.assertEqual(set(loop_a["interventions"]), set(loop_b["interventions"]))

    def test_cross_loop_setpoint_resolves_against_the_named_loop_and_emits_an_edge(self):
        outer = {"loop": "strategy", "goal": {"demand": {"keep": "below capacity"}}}
        inner = {
            "loop": "operations",
            "goal": {"level": {"keep": "near demand", "set_by": "strategy.demand"}},
        }
        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as source:
            yaml.safe_dump_all([outer, inner], source, sort_keys=False)
            source.flush()
            doc, _ = loop_language.expand(source.name)

        self.assertIn({"from": "demand", "to": "level_target", "rel": "sets"},
                      doc["edges"])

        inner["goal"]["level"]["set_by"] = "strategy.level"
        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as source:
            yaml.safe_dump_all([outer, inner], source, sort_keys=False)
            source.flush()
            with self.assertRaisesRegex(loop_language.SpecError,
                                        "strategy.*declares no quantity `level`"):
                loop_language.expand(source.name)

    def test_every_product_example_is_map_order_invariant(self):
        paths = sorted(glob.glob(os.path.join(ROOT, "examples", "*.loop.yaml")))
        paths += sorted(glob.glob(os.path.join(ROOT, "examples", "field", "*.loop.yaml")))

        for path in paths:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                original, _ = loop_language.expand(path)
                original_findings, original_failures = derive.analyze_document(original)
                with open(path) as source:
                    reversed_docs = [reverse_mappings(doc)
                                     for doc in yaml.safe_load_all(source) if doc]
                with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as target:
                    yaml.safe_dump_all(reversed_docs, target, sort_keys=False)
                    target.flush()
                    reordered, _ = loop_language.expand(target.name)
                reordered_findings, reordered_failures = derive.analyze_document(reordered)

                self.assertEqual(semantic_signature(original),
                                 semantic_signature(reordered))
                self.assertEqual([], original_failures)
                self.assertEqual([], reordered_failures)
                self.assertEqual(
                    sorted(__import__("json").dumps(finding, sort_keys=True)
                           for finding in original_findings),
                    sorted(__import__("json").dumps(finding, sort_keys=True)
                           for finding in reordered_findings),
                )

    def test_not_modelling_remains_an_exclusion_not_a_disturbance(self):
        doc = expand_spec(minimal_spec(not_modelling=["weather", "competitor pricing"]))

        self.assertEqual(["weather", "competitor pricing"], doc["excluded_variables"])
        self.assertFalse(any(node["kind"] == "Disturbance" for node in doc["nodes"]))

    def test_alias_and_canonical_key_cannot_silently_overwrite_each_other(self):
        spec = minimal_spec(every="weekly")

        with self.assertRaisesRegex(loop_language.SpecError, "both `runs` and its alias `every`"):
            loop_language.normalize(spec)

    def test_distinct_source_names_cannot_collapse_to_one_graph_id(self):
        spec = minimal_spec(observes={
            "level-reading": {"informs": "level"},
            "level reading": {"informs": "level"},
        })

        with self.assertRaisesRegex(loop_language.SpecError, "same graph id"):
            expand_spec(spec)

    def test_declared_types_are_enforced_before_semantic_expansion(self):
        spec = minimal_spec(runs=["daily"])

        with self.assertRaisesRegex(loop_language.SpecError, "expected str, got list"):
            expand_spec(spec)

        spec = minimal_spec(actions={"raise level": {"moves": 42}})
        with self.assertRaisesRegex(loop_language.SpecError, "expected str or list, got int"):
            expand_spec(spec)

        spec = minimal_spec(goal={"level": {"keep": "above 1", "confidence": 1.2}})
        with self.assertRaisesRegex(loop_language.SpecError, "above maximum 1"):
            expand_spec(spec)

        spec = minimal_spec(people={
            "operator": {"human": True, "kind": "human", "loses_if_wrong": "overflow"},
        })
        with self.assertRaisesRegex(loop_language.SpecError, "declare the party kind more than once"):
            expand_spec(spec)

        spec = minimal_spec(spends={"energy": {"spent_by": "missing action"}})
        with self.assertRaisesRegex(loop_language.SpecError, "spent_by: missing action"):
            expand_spec(spec)

    def test_partial_loop_is_valid_ir_and_reported_as_incomplete_design(self):
        spec = minimal_spec()
        del spec["runs"]

        doc = expand_spec(spec)
        report = self.validate_canonical(doc)
        findings, failures = derive.analyze_document(doc)

        self.assertTrue(report.ok, report.errors)
        self.assertEqual([], failures)
        incomplete = next(finding for finding in findings
                          if finding["pattern"] == "incomplete_loop")
        self.assertIn("cadence", incomplete["evidence"]["missing_roles"])

    def test_policy_inputs_are_explicit_semantics_with_marked_legacy_inference(self):
        explicit = minimal_spec(when=[{
            "if": "level below 1",
            "reads": ["level"],
            "do": "raise level",
        }])
        doc = expand_spec(explicit)
        policy = next(node for node in doc["nodes"] if node["kind"] == "Policy")

        self.assertEqual(["level"], policy["inputs"])
        self.assertFalse(policy["inputs_inferred"])
        self.assertIn({"from": policy["id"], "to": "level", "rel": "reads"}, doc["edges"])

        inferred = expand_spec(minimal_spec())
        legacy_policy = next(node for node in inferred["nodes"] if node["kind"] == "Policy")
        self.assertTrue(legacy_policy["inputs_inferred"])

        invalid = minimal_spec(when=[{
            "if": "mystery below 1",
            "reads": ["mystery"],
            "do": "raise level",
        }])
        with self.assertRaisesRegex(loop_language.SpecError, "reads: mystery"):
            expand_spec(invalid)

    def test_mixed_policy_rules_preserve_explicit_and_inferred_inputs(self):
        spec = minimal_spec(
            beliefs={"risk": {"how": "forecast"}},
            actions={
                "raise level": {"moves": "level"},
                "mitigate risk": {"moves": "risk"},
            },
            when=[
                {"if": "level below 1", "reads": ["level"], "do": "raise level"},
                {"if": "risk high", "do": "mitigate risk"},
            ],
        )

        doc = expand_spec(spec)
        policies = sorted((node for node in doc["nodes"] if node["kind"] == "Policy"),
                          key=lambda node: node["priority"])
        findings, failures = derive.analyze_document(doc)
        by_pattern = {finding["pattern"]: finding for finding in findings}

        self.assertEqual(2, len(policies))
        self.assertEqual(["level"], policies[0]["inputs"])
        self.assertFalse(policies[0]["inputs_inferred"])
        self.assertEqual(["risk"], policies[1]["inputs"])
        self.assertTrue(policies[1]["inputs_inferred"])
        self.assertEqual([1], policies[1]["inferred_rule_indexes"])
        self.assertEqual([policy["id"] for policy in policies], doc["loops"][0]["policies"])
        self.assertIn({"from": policies[0]["id"], "to": "raise_level",
                       "rel": "authorizes"}, doc["edges"])
        self.assertNotIn({"from": policies[0]["id"], "to": "mitigate_risk",
                          "rel": "authorizes"}, doc["edges"])
        self.assertIn({"from": policies[1]["id"], "to": "mitigate_risk",
                       "rel": "authorizes"}, doc["edges"])
        self.assertEqual([], failures)
        self.assertIn("policy_inputs_inferred", by_pattern)
        self.assertIn("policy_entirely_blind", by_pattern)

    def test_calibration_contract_joins_predictions_to_outcomes_and_revision(self):
        complete = minimal_spec(beliefs={
            "level": {
                "question": "Will the level remain above 1?",
                "how": "forecast",
                "checked_by": "weekly forecast review",
                "checked_against": "level reading",
                "scoring_rule": "Brier score",
                "window": "100 forecasts",
                "adjusts": "trust",
                "every": "weekly",
            },
        })
        doc = expand_spec(complete)
        calibration = next(node for node in doc["nodes"] if node["kind"] == "Calibration")
        findings, failures = derive.analyze_document(doc)

        self.assertEqual("level_reading", calibration["outcome"])
        self.assertEqual("Brier score", calibration["scoring_rule"])
        self.assertIn({"from": calibration["id"], "to": "level_reading",
                       "rel": "compares"}, doc["edges"])
        self.assertIn({"from": calibration["id"], "to": "every_weekly",
                       "rel": "reviews_at"}, doc["edges"])
        self.assertEqual([], failures)
        self.assertNotIn("incomplete_calibration_contract",
                         {finding["pattern"] for finding in findings})

        incomplete = minimal_spec(beliefs={
            "level": {"how": "forecast", "checked_by": "weekly forecast review"},
        })
        incomplete_findings, _ = derive.analyze_document(expand_spec(incomplete))
        self.assertIn("incomplete_calibration_contract",
                      {finding["pattern"] for finding in incomplete_findings})

        invalid = copy.deepcopy(complete)
        invalid["beliefs"]["level"]["checked_against"] = "missing outcome"
        with self.assertRaisesRegex(loop_language.SpecError, "checked_against: missing outcome"):
            expand_spec(invalid)

    def test_belief_finding_distinguishes_settlement_from_calibration(self):
        spec = minimal_spec(beliefs={
            "level": {
                "question": "Will the level remain above 1?",
                "how": "forecast",
                "settled_by": "level reading",
            },
        })

        findings, failures = derive.analyze_document(expand_spec(spec))
        finding = next(item for item in findings
                       if item["pattern"] == "belief_never_checked")

        self.assertEqual([], failures)
        self.assertEqual("level reading", finding["evidence"]["settled_by"])
        self.assertIn("Individual calls can settle", finding["claim"])
        self.assertIn("no declared calibration review", finding["claim"])
        self.assertNotIn("nothing ever scores", finding["claim"])

    def test_endogenous_origin_does_not_imply_measurement_cannot_surprise(self):
        spec = minimal_spec(
            observes={
                "research brief": {
                    "informs": "level",
                    "origin": "outside",
                    "how": "reported",
                    "reported_by": "operator",
                },
                "experiment result": {
                    "informs": "level",
                    "origin": "ourselves",
                    "how": "measured",
                    "produced_by": "raise level",
                },
            },
            people={"operator": {"human": True, "loses_if_wrong": "bad result"}},
        )

        findings, failures = derive.analyze_document(expand_spec(spec))
        finding = next(item for item in findings
                       if item["pattern"] == "single_point_of_grounding")

        self.assertEqual([], failures)
        self.assertIn("may still surprise and ground", finding["claim"])
        self.assertNotIn("only thing that can fail", finding["claim"])
        self.assertNotIn("loop is sealed", finding["claim"])

    def test_attention_review_is_not_a_belief_calibration_contract(self):
        spec = minimal_spec(observes={
            "level reading": {
                "informs": "level",
                "origin": "outside",
                "cost": "high",
                "checked_by": "quarterly source review",
            },
        })

        doc = expand_spec(spec)
        review = next(node for node in doc["nodes"] if node["kind"] == "Calibration")
        findings, failures = derive.analyze_document(doc)

        self.assertEqual("attention", review["calibration_kind"])
        self.assertEqual("quarterly source review", review["review"])
        self.assertEqual([], failures)
        self.assertNotIn("incomplete_calibration_contract",
                         {finding["pattern"] for finding in findings})
        self.assertIn("incomplete_attention_contract",
                      {finding["pattern"] for finding in findings})

        spec["observes"]["level reading"].update({
            "value_metric": "decisions changed per source-hour",
            "review_window": "one quarter",
            "review_every": "quarterly",
            "adjusts": "retirement",
        })
        complete_findings, _ = derive.analyze_document(expand_spec(spec))
        self.assertNotIn("incomplete_attention_contract",
                         {finding["pattern"] for finding in complete_findings})

    def test_one_named_review_can_hold_distinct_belief_contracts(self):
        spec = minimal_spec(
            beliefs={
                "level": {"how": "forecast", "checked_by": "weekly review"},
                "risk": {"how": "forecast", "checked_by": "weekly review"},
            },
            observes={
                "level reading": {"informs": "level"},
                "risk report": {"informs": "risk"},
            },
        )

        doc = expand_spec(spec)
        calibrations = [node for node in doc["nodes"]
                        if node["kind"] == "Calibration"]

        self.assertEqual(2, len(calibrations))
        self.assertEqual({"weekly review"}, {node["review"] for node in calibrations})
        self.assertEqual({"level", "risk"}, {node["scores"] for node in calibrations})

    def test_boundary_records_observer_purpose_and_fails_closed_on_bad_reference(self):
        spec = minimal_spec(
            boundary={
                "drawn_by": "operator",
                "purpose": "hold the level within a viable range",
                "inside": ["controller", "tank"],
                "outside": ["inflow"],
            },
            people={"operator": {"human": True, "loses_if_wrong": "overflow"}},
        )

        doc = expand_spec(spec)
        boundary = next(node for node in doc["nodes"] if node["kind"] == "Boundary")

        self.assertEqual("hold the level within a viable range", boundary["purpose"])
        self.assertIn({"from": "operator", "to": boundary["id"], "rel": "frames"},
                      doc["edges"])
        self.assertEqual(boundary["id"], doc["loops"][0]["boundary"])

        incomplete = copy.deepcopy(spec)
        incomplete["boundary"]["outside"] = []
        incomplete_findings, _ = derive.analyze_document(expand_spec(incomplete))
        self.assertIn("incomplete_boundary",
                      {finding["pattern"] for finding in incomplete_findings})

        invalid = copy.deepcopy(spec)
        invalid["boundary"]["drawn_by"] = "nobody"
        with self.assertRaisesRegex(loop_language.SpecError, "drawn_by: nobody"):
            expand_spec(invalid)

        missing_purpose = copy.deepcopy(spec)
        del missing_purpose["boundary"]["purpose"]
        with self.assertRaisesRegex(loop_language.SpecError, "needs a `purpose:`"):
            expand_spec(missing_purpose)

    def test_explicit_no_consequence_is_preserved_without_fabricating_a_stake(self):
        explicit_none = minimal_spec(
            people={"automated operator": {"agent": True,
                                             "loses_if_wrong": "nothing"}},
        )
        document = expand_spec(explicit_none)
        party = next(node for node in document["nodes"] if node["kind"] == "Party")
        report = self.validate_canonical(document)

        self.assertEqual("none", party["consequence_status"])
        self.assertFalse(any(node["kind"] == "Consequence"
                             for node in document["nodes"]))
        self.assertFalse(any("automated_operator" in warning
                             for warning in report.warnings))

        unknown = expand_spec(minimal_spec(people={"operator": {"human": True}}))
        unknown_report = self.validate_canonical(unknown)
        self.assertTrue(any("does not declare whether" in warning
                            for warning in unknown_report.warnings))

    def test_process_path_closes_world_leg_and_effect_unknown_is_explicit(self):
        spec = minimal_spec(
            processes={
                "tank": {
                    "location": "inside",
                    "description": "stored liquid responding to the inlet valve",
                    "observed_as": ["level reading"],
                },
            },
            actions={
                "raise level": {
                    "moves": "level",
                    "through": "tank",
                    "effect": "unknown",
                    "can_undo": "yes",
                },
            },
        )

        doc = expand_spec(spec)
        findings, failures = derive.analyze_document(doc)
        patterns = {finding["pattern"] for finding in findings}

        self.assertIn({"from": "raise_level", "to": "tank", "rel": "causes"},
                      doc["edges"])
        self.assertIn({"from": "tank", "to": "level_reading", "rel": "produces"},
                      doc["edges"])
        self.assertEqual("unknown", next(node for node in doc["nodes"]
                                          if node["id"] == "raise_level")["effect_direction"])
        self.assertEqual([], failures)
        self.assertNotIn("process_path_not_declared", patterns)
        self.assertNotIn("effect_direction_unspecified", patterns)

        broken = copy.deepcopy(spec)
        broken["processes"]["tank"]["observed_as"] = []
        broken_patterns = {finding["pattern"]
                           for finding in derive.analyze_document(expand_spec(broken))[0]}
        self.assertIn("process_path_not_declared", broken_patterns)

        unlocated = copy.deepcopy(spec)
        unlocated["processes"]["tank"].pop("location")
        unlocated_patterns = {finding["pattern"]
                              for finding in derive.analyze_document(expand_spec(unlocated))[0]}
        self.assertIn("process_location_unspecified", unlocated_patterns)

        invalid = copy.deepcopy(spec)
        invalid["actions"]["raise level"]["through"] = "missing process"
        with self.assertRaisesRegex(loop_language.SpecError, "through: missing process"):
            expand_spec(invalid)

    def test_reference_use_is_explicit_and_implies_a_read_by_the_same_rule(self):
        partial = minimal_spec()
        partial_findings, failures = derive.analyze_document(expand_spec(partial))

        self.assertEqual([], failures)
        self.assertIn("reference_not_used",
                      {finding["pattern"] for finding in partial_findings})

        complete = minimal_spec(when=[{
            "if": "level below 1",
            "reads": ["level"],
            "against": ["level"],
            "do": "raise level",
        }])
        complete_doc = expand_spec(complete)
        policy = next(node for node in complete_doc["nodes"] if node["kind"] == "Policy")
        complete_patterns = {finding["pattern"]
                             for finding in derive.analyze_document(complete_doc)[0]}

        self.assertIn({"from": policy["id"], "to": "level_target",
                       "rel": "uses_reference"}, complete_doc["edges"])
        self.assertNotIn("reference_not_used", complete_patterns)

        nonredundant = minimal_spec(when=[{
            "if": "level below 1",
            "reads": [],
            "against": ["level"],
            "do": "raise level",
        }])
        nonredundant_doc = expand_spec(nonredundant)
        nonredundant_policy = next(
            node for node in nonredundant_doc["nodes"] if node["kind"] == "Policy"
        )
        self.assertEqual(["level"], nonredundant_policy["inputs"])
        self.assertIn(
            {"from": nonredundant_policy["id"], "to": "level", "rel": "reads"},
            nonredundant_doc["edges"],
        )

    def test_accepted_operational_metadata_survives_expansion(self):
        spec = minimal_spec(
            observes={
                "level reading": {
                    "informs": "level",
                    "origin": "outside",
                    "how": "measured",
                    "source": "tank sensor A",
                    "every": "hourly",
                },
            },
            actions={
                "raise level": {
                    "moves": "level",
                    "can_undo": "yes",
                    "effect": "increase",
                    "damping": "maximum one change per hour",
                },
            },
            when=[],
            asks_human_when=["sensor disagreement"],
        )

        doc = expand_spec(spec)
        signal = next(node for node in doc["nodes"] if node["id"] == "level_reading")
        action = next(node for node in doc["nodes"] if node["id"] == "raise_level")

        self.assertEqual("tank sensor A", signal["source"])
        self.assertIn({"from": "level_reading", "to": "every_hourly",
                       "rel": "samples_at"}, doc["edges"])
        self.assertEqual("maximum one change per hour", action["damping"])
        self.assertEqual(["sensor disagreement"], doc["loops"][0]["asks_human_when"])

    def test_multi_target_effect_directions_are_total_and_unambiguous(self):
        spec = minimal_spec(
            goal={
                "level": {"keep": "above 1"},
                "overflow_risk": {"keep": "below 0.1"},
            },
            observes={
                "level reading": {"informs": "level"},
                "overflow alarm": {"informs": "overflow_risk"},
            },
            actions={
                "raise level": {
                    "moves": ["level", "overflow_risk"],
                    "effects": {"level": "increase", "overflow_risk": "increase"},
                    "can_undo": "yes",
                },
            },
        )

        doc = expand_spec(spec)
        action = next(node for node in doc["nodes"] if node["id"] == "raise_level")
        findings, failures = derive.analyze_document(doc)

        self.assertEqual({"level": "increase", "overflow_risk": "increase"},
                         action["effect_directions"])
        self.assertEqual([], failures)
        self.assertNotIn("effect_direction_unspecified",
                         {finding["pattern"] for finding in findings})

        missing = copy.deepcopy(spec)
        missing["actions"]["raise level"]["effects"].pop("overflow_risk")
        with self.assertRaisesRegex(loop_language.SpecError, "keys must exactly match"):
            expand_spec(missing)

        conflicting = copy.deepcopy(spec)
        conflicting["actions"]["raise level"]["effect"] = "increase"
        with self.assertRaisesRegex(loop_language.SpecError, "use `effect` or `effects`"):
            expand_spec(conflicting)

        invalid = copy.deepcopy(spec)
        invalid["actions"]["raise level"]["effects"]["level"] = "sideways"
        with self.assertRaisesRegex(loop_language.SpecError, "sideways.*not one of"):
            expand_spec(invalid)

    def test_production_provenance_cannot_contradict_outside_origin(self):
        spec = minimal_spec(observes={
            "level reading": {
                "informs": "level",
                "origin": "outside",
                "produced_by": "raise level",
            },
        })

        with self.assertRaisesRegex(loop_language.SpecError, "contradicts `origin: outside`"):
            expand_spec(spec)

    def test_escalation_conditions_require_a_named_recipient(self):
        partial = minimal_spec(
            asks_human_when=["sensor disagreement"],
            people={"operator": {"human": True, "loses_if_wrong": "overflow"}},
        )
        partial_doc = expand_spec(partial)
        partial_findings, failures = derive.analyze_document(partial_doc)
        patterns = {finding["pattern"] for finding in partial_findings}

        self.assertEqual([], failures)
        self.assertIn("escalation_target_unspecified", patterns)
        self.assertNotIn("no_escalation_path", patterns)

        complete = copy.deepcopy(partial)
        complete["asks_human"] = "operator"
        complete_doc = expand_spec(complete)
        complete_patterns = {finding["pattern"]
                             for finding in derive.analyze_document(complete_doc)[0]}
        self.assertEqual("operator", complete_doc["loops"][0]["escalates_to"])
        self.assertNotIn("escalation_target_unspecified", complete_patterns)

        invalid = copy.deepcopy(complete)
        invalid["asks_human"] = "missing person"
        with self.assertRaisesRegex(loop_language.SpecError, "asks_human: missing person"):
            expand_spec(invalid)

    def test_unresolved_reporter_is_preserved_without_a_dangling_edge(self):
        spec = minimal_spec(observes={
            "customer report": {
                "informs": "level",
                "how": "reported",
                "reported_by": "external customer",
            },
        })

        doc = expand_spec(spec)
        signal = next(node for node in doc["nodes"] if node["id"] == "customer_report")

        self.assertEqual("external customer", signal["reported_by"])
        self.assertFalse(any(edge["from"] == "external_customer" for edge in doc["edges"]))
        self.assertTrue(self.validate_canonical(doc).ok)

    def test_all_product_examples_complete_the_pipeline(self):
        paths = sorted(glob.glob(os.path.join(ROOT, "examples", "*.loop.yaml")))
        paths += sorted(glob.glob(os.path.join(ROOT, "examples", "field", "*.loop.yaml")))
        self.assertTrue(paths)

        for path in paths:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                doc, _warnings = loop_language.expand(path)
                report = self.validate_canonical(doc)
                findings, query_failures = derive.analyze_document(doc)
                self.assertTrue(report.ok, report.errors)
                self.assertEqual([], query_failures)
                self.assertTrue(all(finding.get("assurance") in derive.ASSURANCE_LEVELS
                                    for finding in findings))
                self.assertFalse({
                    "regulator_without_model",
                    "uncontrollable_target",
                    "reinforcing_loop_no_balancer",
                    "cascade_timescale_inversion",
                    "insufficient_variety",
                }.intersection(finding["pattern"] for finding in findings))

    def test_every_authoring_check_has_an_executable_positive_fixture(self):
        with open(os.path.join(ROOT, "docs", "checks.yaml")) as source:
            metadata = yaml.safe_load(source)
        authoring_patterns = {
            pattern for pattern, body in metadata.items()
            if body.get("evidence") != "legacy"
        }
        compatibility_patterns = set(metadata) - authoring_patterns
        observed = set()

        corpus = sorted(glob.glob(os.path.join(ROOT, "examples", "**", "*.loop.yaml"),
                                  recursive=True))
        corpus += sorted(glob.glob(os.path.join(
            ROOT, "research", "published_study", "encodings*", "*.loop.yaml"
        )))
        for path in corpus:
            document, _ = loop_language.expand(path)
            findings, failures = derive.analyze_document(document)
            self.assertEqual([], failures, path)
            observed.update(finding["pattern"] for finding in findings)

        base = minimal_spec()
        incomplete_attention = copy.deepcopy(base)
        incomplete_attention["observes"]["level reading"]["checked_by"] = "source review"

        incomplete = copy.deepcopy(base)
        incomplete.pop("runs")

        incomplete_boundary = copy.deepcopy(base)
        incomplete_boundary["people"] = {
            "operator": {"human": True, "loses_if_wrong": "overflow"},
        }
        incomplete_boundary["boundary"] = {
            "drawn_by": "operator",
            "purpose": "control level",
            "inside": ["controller"],
            "outside": [],
        }

        unlocated_process = copy.deepcopy(base)
        unlocated_process["processes"] = {
            "tank": {"observed_as": ["level reading"]},
        }
        unlocated_process["actions"]["raise level"]["through"] = "tank"

        partly_blind_policy = copy.deepcopy(base)
        partly_blind_policy["beliefs"] = {
            "risk": {"how": "judgement"},
        }
        partly_blind_policy["when"] = [{
            "if": "level is low and risk is acceptable",
            "reads": ["level", "risk"],
            "against": ["level"],
            "do": "raise level",
        }]

        profiles_without_fallback = copy.deepcopy(base)
        profiles_without_fallback["actions"] = {"raise level": {"moves": "level"}}
        profiles_without_fallback["people"] = {
            "operator": {"human": True, "loses_if_wrong": "overflow"},
        }
        profiles_without_fallback["action_profiles"] = {
            "approved": {
                "action": "raise level", "when": "remote request",
                "resolved_at": "request", "can_undo": "unknown",
                "needs_approval": "operator",
            },
            "local": {
                "action": "raise level", "when": "local request",
                "resolved_at": "request", "can_undo": "yes",
            },
        }

        profile_without_variation = copy.deepcopy(base)
        profile_without_variation["actions"] = {"raise level": {"moves": "level"}}
        profile_without_variation["action_profiles"] = {
            "fallback": {
                "action": "raise level", "default": True,
                "resolved_at": "request", "can_undo": "unknown",
            },
        }

        split_open_loop = [
            {
                "loop": "actuation",
                "runs": "daily",
                "goal": {"level": {"keep": "above 1"}},
                "actions": {"raise level": {"moves": "level", "can_undo": "yes"}},
                "when": [{"if": "level low", "reads": ["level"],
                          "against": ["level"], "do": "raise level"}],
            },
            {
                "loop": "sensing",
                "runs": "daily",
                "beliefs": {"level": {"how": "calculated"}},
                "observes": {"level reading": {"informs": "level",
                                                "origin": "outside"}},
            },
        ]
        inverted_cascade = [
            {"loop": "strategy", "runs": "daily",
             "goal": {"demand": {"keep": "near 10"}}},
            {"loop": "operations", "runs": "daily",
             "goal": {"level": {"keep": "near demand",
                                  "set_by": "strategy.demand"}}},
        ]

        synthetic_documents = [
            [incomplete_attention],
            [incomplete],
            [incomplete_boundary],
            [unlocated_process],
            [partly_blind_policy],
            [profiles_without_fallback],
            [profile_without_variation],
            split_open_loop,
            inverted_cascade,
        ]
        for documents in synthetic_documents:
            with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as source:
                yaml.safe_dump_all(documents, source, sort_keys=False)
                source.flush()
                document, _ = loop_language.expand(source.name)
            findings, failures = derive.analyze_document(document)
            self.assertEqual([], failures)
            observed.update(finding["pattern"] for finding in findings)

        self.assertEqual(set(), authoring_patterns - observed)
        self.assertEqual(set(), compatibility_patterns & observed)

    def test_complete_example_has_no_active_design_findings(self):
        path = os.path.join(ROOT, "examples", "complete.loop.yaml")
        doc, warnings = loop_language.expand(path)
        report = self.validate_canonical(doc)
        findings, failures = derive.analyze_document(doc)

        self.assertEqual([], warnings)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual([], failures)
        self.assertEqual([], findings)

    def test_safety_relevant_mutations_fail_or_produce_the_expected_finding(self):
        with open(os.path.join(ROOT, "examples", "complete.loop.yaml")) as source:
            complete = yaml.safe_load(source)

        mutations = []

        def expect_finding(name, pattern, mutate):
            mutations.append((name, pattern, mutate))

        expect_finding(
            "reversibility omitted", "reversibility_unspecified",
            lambda spec: spec["actions"]["escalate_to_engineer"].pop("can_undo"),
        )

        def remove_approval(spec):
            action = spec["actions"]["escalate_to_engineer"]
            action["can_undo"] = "no"
            action.pop("needs_approval")

        expect_finding("irreversible approval removed", "irreversible_without_approval",
                       remove_approval)
        expect_finding(
            "policy semantics omitted", "policy_inputs_inferred",
            lambda spec: spec["when"][0].pop("reads"),
        )
        expect_finding(
            "calibration outcome join removed", "incomplete_calibration_contract",
            lambda spec: spec["beliefs"]["ticket_severity"].pop("checked_against"),
        )
        expect_finding(
            "effect sign omitted", "effect_direction_unspecified",
            lambda spec: spec["actions"]["escalate_to_engineer"].pop("effect"),
        )
        expect_finding(
            "process link omitted", "process_path_not_declared",
            lambda spec: spec["actions"]["escalate_to_engineer"].pop("through"),
        )
        expect_finding(
            "process observation omitted", "process_path_not_declared",
            lambda spec: spec["processes"]["support_workflow"].update(observed_as=[]),
        )
        expect_finding(
            "accountable party blinded", "accountable_but_blind",
            lambda spec: spec["people"]["support_lead"].pop("sees"),
        )

        def remove_resource_contract(spec):
            resource = spec["spends"]["engineer_hours"]
            resource.pop("limit")
            resource.pop("replenished")

        expect_finding("resource viability removed", "spends_without_limit",
                       remove_resource_contract)

        for name, expected, mutate in mutations:
            with self.subTest(mutation=name):
                spec = copy.deepcopy(complete)
                mutate(spec)
                findings, failures = derive.analyze_document(expand_spec(spec))
                self.assertEqual([], failures)
                self.assertIn(expected, {finding["pattern"] for finding in findings})

        missing_purpose = copy.deepcopy(complete)
        missing_purpose["boundary"].pop("purpose")
        with self.assertRaisesRegex(loop_language.SpecError, "needs a `purpose:`"):
            expand_spec(missing_purpose)

        misspelled = copy.deepcopy(complete)
        action = misspelled["actions"]["escalate_to_engineer"]
        action["can_undoo"] = action.pop("can_undo")
        with self.assertRaisesRegex(loop_language.SpecError, "unknown key `can_undoo`"):
            expand_spec(misspelled)

    def test_legacy_held_out_ir_remains_readable_without_v2_invention(self):
        paths = sorted(glob.glob(os.path.join(
            ROOT, "research", "archive", "uras", "benchmarks", "encodings", "held_out",
            "*.yaml"
        )))
        self.assertEqual(8, len(paths))

        for path in paths:
            with self.subTest(path=os.path.basename(path)):
                with open(path) as source:
                    doc = yaml.safe_load(source)
                report = self.validate_canonical(doc)
                findings, failures = derive.analyze_document(doc)
                self.assertTrue(report.ok, report.errors)
                self.assertEqual([], failures)
                self.assertNotIn("incomplete_loop",
                                 {finding["pattern"] for finding in findings})

    def test_theory_inspired_checks_state_their_actual_boundary(self):
        doc = expand_spec(minimal_spec(
            observes={
                "self report": {
                    "informs": "level",
                    "origin": "ourselves",
                    "produced_by": "raise level",
                },
            },
        ))

        findings, failures = derive.analyze_document(doc)
        by_pattern = {finding["pattern"]: finding for finding in findings}

        self.assertEqual([], failures)
        self.assertIn("no_explicit_process_model", by_pattern)
        self.assertIn("endogenous_feedback_without_crosscheck", by_pattern)
        self.assertIn("cannot be inferred", by_pattern[
            "endogenous_feedback_without_crosscheck"
        ]["claim"])
        self.assertEqual("structural", by_pattern[
            "no_explicit_process_model"
        ]["assurance"])

    def test_unified_cli_emits_machine_readable_results_and_useful_statuses(self):
        command = [sys.executable, os.path.join(TOOLS, "loopspec.py"), "check",
                   os.path.join(ROOT, "examples", "customer_acquisition.v1.loop.yaml"),
                   "--json"]
        result = subprocess.run(command, capture_output=True, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

        self.assertEqual(0, result.returncode, result.stderr)
        output = __import__("json").loads(result.stdout)
        self.assertTrue(output["valid"])
        self.assertEqual(2, output["ir_version"])
        self.assertEqual("2.2", output["ir_revision"])
        self.assertTrue(all("assurance" in finding for finding in output["findings"]))
        self.assertTrue(all(finding.get("repair") for finding in output["findings"]))
        self.assertTrue(all(finding.get("evidence_status") in
                            {"robust", "corpus", "motivated", "legacy"}
                            for finding in output["findings"]))

        partial = minimal_spec()
        del partial["runs"]
        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as source:
            yaml.safe_dump(partial, source)
            source.flush()
            strict = subprocess.run(
                [sys.executable, os.path.join(TOOLS, "loopspec.py"), "check", source.name,
                 "--fail-on-findings"],
                capture_output=True, text=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )
        self.assertEqual(2, strict.returncode, strict.stderr)
        self.assertIn("incomplete_loop", strict.stdout)

    def test_cli_package_entry_point_matches_direct_script(self):
        path = os.path.join(ROOT, "examples", "complete.loop.yaml")
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        direct = subprocess.run(
            [sys.executable, os.path.join(TOOLS, "loopspec.py"), "check", path, "--json"],
            cwd=ROOT, capture_output=True, text=True, env=environment,
        )
        packaged = subprocess.run(
            [sys.executable, "-m", "tools.loopspec", "check", path, "--json"],
            cwd=ROOT, capture_output=True, text=True, env=environment,
        )

        self.assertEqual(0, direct.returncode, direct.stderr)
        self.assertEqual(0, packaged.returncode, packaged.stderr)
        self.assertEqual(__import__("json").loads(direct.stdout),
                         __import__("json").loads(packaged.stdout))

    def test_uras_compatibility_command_warns_and_delegates(self):
        path = os.path.join(ROOT, "examples", "complete.loop.yaml")
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS, "uras.py"), "check", path, "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(__import__("json").loads(result.stdout)["valid"])
        self.assertIn("renamed to `loopspec`", result.stderr)

    def test_semantic_diff_ignores_yaml_order_and_reports_meaning_changes(self):
        complete_path = os.path.join(ROOT, "examples", "complete.loop.yaml")
        with open(complete_path) as source:
            complete = yaml.safe_load(source)
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as reordered:
            yaml.safe_dump(reverse_mappings(complete), reordered, sort_keys=False)
            reordered.flush()
            same = subprocess.run(
                [sys.executable, os.path.join(TOOLS, "loopspec.py"), "diff",
                 complete_path, reordered.name, "--json", "--fail-on-change"],
                cwd=ROOT, capture_output=True, text=True, env=environment,
            )

        self.assertEqual(0, same.returncode, same.stderr)
        same_delta = __import__("json").loads(same.stdout)
        self.assertFalse(same_delta["changed"])
        self.assertEqual(same_delta["left"]["semantic_hash"],
                         same_delta["right"]["semantic_hash"])

        changed_spec = copy.deepcopy(complete)
        changed_spec["actions"]["escalate_to_engineer"]["effect"] = "increase"
        changed_spec["when"][1].pop("against")
        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml") as changed_source:
            yaml.safe_dump(changed_spec, changed_source, sort_keys=False)
            changed_source.flush()
            changed = subprocess.run(
                [sys.executable, os.path.join(TOOLS, "loopspec.py"), "diff",
                 complete_path, changed_source.name, "--json", "--fail-on-change"],
                cwd=ROOT, capture_output=True, text=True, env=environment,
            )
            human = subprocess.run(
                [sys.executable, os.path.join(TOOLS, "loopspec.py"), "diff",
                 complete_path, changed_source.name],
                cwd=ROOT, capture_output=True, text=True, env=environment,
            )

        self.assertEqual(3, changed.returncode, changed.stderr)
        self.assertEqual(0, human.returncode, human.stderr)
        delta = __import__("json").loads(changed.stdout)
        self.assertTrue(delta["changed"])
        self.assertNotEqual(delta["left"]["semantic_hash"],
                            delta["right"]["semantic_hash"])
        modified = {record["id"]: record["changes"]
                    for record in delta["nodes"]["modified"]}
        self.assertIn("escalate_to_engineer", modified)
        self.assertTrue(any(change["field"] == "effect_direction"
                            for change in modified["escalate_to_engineer"]))
        self.assertIn(
            {"from": "support_triage_policy_1", "rel": "uses_reference",
             "to": "resolution_time_target"},
            delta["edges"]["removed"],
        )
        self.assertIn("reference_not_used",
                      {finding["pattern"] for finding in delta["findings"]["added"]})
        self.assertIn("effect_direction", human.stdout)
        self.assertIn("reference_not_used", human.stdout)

    def test_normative_conformance_manifest_matches_every_product_example(self):
        with open(os.path.join(ROOT, "tests", "conformance.yaml")) as source:
            manifest = yaml.safe_load(source)
        paths = sorted(glob.glob(os.path.join(ROOT, "examples", "*.loop.yaml")))
        paths += sorted(glob.glob(os.path.join(ROOT, "examples", "field",
                                               "*.loop.yaml")))
        relative_paths = {os.path.relpath(path, ROOT) for path in paths}

        self.assertEqual(1, manifest["manifest_version"])
        self.assertEqual("1.2", manifest["authoring_version"])
        self.assertEqual("2.2", manifest["ir_revision"])
        self.assertEqual(relative_paths, set(manifest["fixtures"]))

        for relative_path, expected in manifest["fixtures"].items():
            with self.subTest(path=relative_path):
                document, warnings, report, findings = loopspec_cli.checked_document(
                    os.path.join(ROOT, relative_path)
                )
                self.assertEqual([], warnings)
                self.assertTrue(report.ok, report.errors)
                self.assertEqual("loop-v1.2", document["source_format"])
                self.assertEqual(manifest["ir_revision"], document["ir_revision"])
                self.assertEqual(expected["encodes"], document["encodes"])
                self.assertEqual(expected["semantic_hash"],
                                 semantic_diff.semantic_hash(document))
                self.assertEqual(expected["findings_hash"],
                                 semantic_diff.findings_hash(findings))
                self.assertEqual(expected["finding_count"], len(findings))

    def test_installed_runtime_doctor_fixture_is_valid(self):
        document = expand_spec(copy.deepcopy(loopspec_cli.RUNTIME_SMOKE_SPEC))
        report = self.validate_canonical(document)
        findings, failures = derive.analyze_document(document)

        self.assertTrue(report.ok, report.errors)
        self.assertEqual([], failures)
        self.assertTrue(all(finding.get("assurance") and finding.get("repair")
                            for finding in findings))

    def test_both_diagram_projections_show_declared_boundary_and_process_path(self):
        path = os.path.join(ROOT, "examples", "complete.loop.yaml")
        base = [sys.executable, os.path.join(TOOLS, "loopspec.py"), "diagram", path,
                "--markdown"]

        dependency = subprocess.run(
            base, capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        control = subprocess.run(
            base + ["--control"], capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )

        self.assertEqual(0, dependency.returncode, dependency.stderr)
        self.assertEqual(0, control.returncode, control.stderr)
        for output in (dependency.stdout, control.stdout):
            self.assertIn("support_workflow", output)
        self.assertIn("frames", dependency.stdout)
        self.assertIn("bounds", dependency.stdout)
        self.assertNotIn("unrepresented process", control.stdout)

    def test_external_evidence_gate_is_executable_and_fails_on_preregistered_thresholds(self):
        with open(os.path.join(ROOT, "examples", "complete.loop.yaml")) as source:
            frozen_spec = yaml.safe_load(source)
        frozen_spec["when"][1].pop("against")
        with tempfile.NamedTemporaryFile("w", suffix=".loop.yaml", delete=False) as source:
            yaml.safe_dump(frozen_spec, source, sort_keys=False)
            frozen_spec_path = source.name
        self.addCleanup(lambda: os.path.exists(frozen_spec_path)
                        and os.unlink(frozen_spec_path))
        with open(frozen_spec_path, "rb") as source:
            frozen_spec_hash = hashlib.sha256(source.read()).hexdigest()
        generated_doc, warnings, report, generated_findings = loopspec_cli.checked_document(
            frozen_spec_path
        )
        self.assertEqual([], warnings)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(["reference_not_used"],
                         [finding["pattern"] for finding in generated_findings])
        organised = derive.organise(generated_doc, generated_findings)
        bucket = next(name for name in ("specific", "common", "universal")
                      if organised[name])

        artifact_hashes = external_eval.artifact_hashes()
        with open(os.path.join(ROOT, "docs", "checks.yaml")) as source:
            checks = yaml.safe_load(source)
        with open(os.path.join(ROOT, "research", "external_validation",
                               "study.template.yaml")) as source:
            study_template = yaml.safe_load(source)
        with open(os.path.join(ROOT, "research", "external_validation",
                               "record.template.yaml")) as source:
            record_template = yaml.safe_load(source)
        self.assertEqual(set(external_eval.FROZEN_ARTIFACTS),
                         set(study_template["artifact_hashes"]))
        self.assertEqual(set(external_eval.runtime_fingerprint()),
                         set(study_template["runtime"]))
        self.assertTrue(set(external_eval.HIGH_PRIORITY_PATTERNS).issubset(
            external_eval.active_checks()
        ))
        self.assertIn("spec_path", record_template)
        self.assertIn("spec_sha256", record_template)
        study = external_eval.make_freeze_manifest(
            "frozen-test-artifact", "LoopSpec doctor: healthy"
        )
        self.assertEqual(artifact_hashes, study["artifact_hashes"])
        self.assertEqual(external_eval.runtime_fingerprint(), study["runtime"])
        self.assertEqual({pattern: body["assurance"] for pattern, body in checks.items()
                          if body.get("evidence") != "legacy"},
                         study["active_checks"])

        clean = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        commit = subprocess.CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr="")
        doctor = subprocess.CompletedProcess(
            [], 0, stdout="LoopSpec doctor: release gate is healthy\n", stderr=""
        )
        with mock.patch.object(external_eval.subprocess, "run",
                               side_effect=[clean, commit, doctor]):
            frozen = external_eval.freeze_manifest()
        self.assertEqual("a" * 40, frozen["artifact_commit"])
        self.assertEqual(artifact_hashes, frozen["artifact_hashes"])

        dirty = subprocess.CompletedProcess(
            [], 0, stdout=" M tools/derive.py\n", stderr=""
        )
        with mock.patch.object(external_eval.subprocess, "run", return_value=dirty):
            with self.assertRaisesRegex(external_eval.StudyError,
                                        "uncommitted semantic artifacts"):
                external_eval.freeze_manifest()
        records = []
        domains = ["support", "health", "operations"]
        for index in range(12):
            records.append({
                "system_id": f"system-{index}",
                "author_id": f"author-{index}",
                "domain": domains[index % len(domains)],
                "stage": "operating" if index < 6 else "design",
                "source_kind": "mixed",
                "encoder_id": f"encoder-{index % 2}",
                "loopspec_contributor": False,
                "spec_path": frozen_spec_path,
                "spec_sha256": frozen_spec_hash,
                "encoding_minutes": 30 + index,
                "author_corrections": [],
                "findings": [{
                    "pattern": "reference_not_used",
                    "assurance": "structural",
                    "presentation_bucket": bucket,
                    "initial_verdict": "changes_spec",
                    "adjudicated_correct": True,
                }],
            })

        passing = external_eval.analyze(study, records)

        self.assertTrue(passing["eligible_for_usefulness_claim"])
        self.assertTrue(all(passing["gates"].values()))
        self.assertEqual(1.0, passing["measures"]["high_priority_precision"])

        wrong_runtime = copy.deepcopy(study)
        wrong_runtime["runtime"]["python_version"] = "0.0.0"
        with self.assertRaisesRegex(external_eval.StudyError,
                                    "must exactly match the frozen Python"):
            external_eval.analyze(wrong_runtime, records)

        failing_records = copy.deepcopy(records)
        for record in failing_records[:5]:
            record["findings"][0]["initial_verdict"] = "wrong"
            record["findings"][0]["adjudicated_correct"] = False
        failing = external_eval.analyze(study, failing_records)

        self.assertFalse(failing["eligible_for_usefulness_claim"])
        self.assertFalse(failing["gates"]["high_priority_precision_at_least_0_70"])

        duplicate_author = copy.deepcopy(records)
        duplicate_author[1]["author_id"] = duplicate_author[0]["author_id"]
        with self.assertRaisesRegex(external_eval.StudyError, "one loop per author"):
            external_eval.analyze(study, duplicate_author)

        fabricated = copy.deepcopy(records)
        fabricated[0]["findings"][0]["pattern"] = "target_without_actuator"
        with self.assertRaisesRegex(external_eval.StudyError,
                                    "do not match frozen analyzer output"):
            external_eval.analyze(study, fabricated)


if __name__ == "__main__":
    unittest.main()
