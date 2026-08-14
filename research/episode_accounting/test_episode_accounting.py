from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.episode_accounting import analyze, assess, design_evolution, human_probe, simulate


class SyntheticPipelineTests(unittest.TestCase):
    def generate(self, directory: Path) -> list[dict]:
        counts = simulate.generate(output_dir=directory)
        self.assertEqual(counts, {"series": 80, "episodes": 560})
        return [json.loads(line) for line in (directory / "synthetic_series.jsonl").read_text().splitlines()]

    def test_generation_is_deterministic_and_balanced(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            rows = self.generate(Path(first))
            self.generate(Path(second))
            a = hashlib.sha256((Path(first) / "synthetic_series.jsonl").read_bytes()).hexdigest()
            b = hashlib.sha256((Path(second) / "synthetic_series.jsonl").read_bytes()).hexdigest()
            self.assertEqual(a, b)
            self.assertEqual(len({row["family"] for row in rows}), 4)
            self.assertEqual(len({row["ground_truth"]["mechanism"] for row in rows}), 10)

    def test_blinded_packets_do_not_expose_generator_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rows = self.generate(output)
            mechanism_names = {row["ground_truth"]["mechanism"] for row in rows}
            for condition in assess.CONDITIONS:
                packets = assess.read_jsonl(output / f"packets.{condition}.jsonl")
                for packet in packets:
                    self.assertNotIn("ground_truth", packet)
                    serialized = json.dumps(packet)
                    for mechanism in mechanism_names:
                        self.assertNotIn(f'"{mechanism}"', serialized)

    def test_storage_repetition_and_return_remain_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = self.generate(Path(directory))
            by_mechanism = {}
            for row in rows:
                by_mechanism.setdefault(row["ground_truth"]["mechanism"], row)
            unused = by_mechanism["retained_but_unused"]
            carriers = [carrier for episode in unused["episodes"] for carrier in episode["carriers"]]
            returns = [ret for episode in unused["episodes"] for ret in episode["returns"]]
            self.assertEqual(len(carriers), 1)
            self.assertEqual(carriers[0]["retrieved_in"], [])
            self.assertEqual(returns, [])
            self.assertFalse(unused["ground_truth"]["recursion"])

            repeated = by_mechanism["repetition_without_retention"]
            self.assertFalse(any(episode["carriers"] for episode in repeated["episodes"]))
            self.assertFalse(repeated["ground_truth"]["recursion"])

            learned = by_mechanism["institutional_rule_learning"]
            self.assertTrue(learned["ground_truth"]["recursion"])
            self.assertTrue(learned["ground_truth"]["source_episode"].endswith("e2"))
            self.assertTrue(learned["ground_truth"]["target_episode"].endswith("e5"))

    def test_full_run_preserves_strong_trace_negative_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.generate(output)
            self.assertEqual(assess.run(output), 240)
            result = analyze.analyze(output)
            self.assertTrue(result["hypotheses"]["H1"])
            self.assertFalse(result["hypotheses"]["H2"])
            self.assertTrue(result["hypotheses"]["H3"])
            self.assertFalse(result["hypotheses"]["H4"])
            self.assertFalse(result["promotion_gate"])
            self.assertEqual(result["metrics"]["ordinary_trace"]["macro_f1"], 1.0)
            self.assertEqual(result["metrics"]["episode_ledger"]["macro_f1"], 1.0)


class HumanProbeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)

    @staticmethod
    def correct_responder(item, choices, context):
        initial = item["answer"]
        if context["mode"] == "joint":
            initial = next(option for option in choices if option != item["answer"])
        return {
            "initial_answer": initial,
            "final_answer": item["answer"],
            "confidence": 80,
            "response_seconds": 1.0,
        }

    def test_instrument_is_complete_and_valid(self):
        protocol, bank = human_probe.load_instrument()
        self.assertEqual(human_probe.instrument_errors(protocol, bank), [])
        self.assertEqual(len(protocol["phases"]), 6)
        self.assertEqual(len(bank["items"]), 32)
        for phase in protocol["phases"]:
            self.assertGreater(len(human_probe.phase_items(bank, phase["item_set"])), 0)

    def test_consent_delay_transfer_and_contribution_trace(self):
        session = human_probe.new_session("local-pseudonym", True, now=self.now)
        self.assertNotIn("local-pseudonym", json.dumps(session))
        # Baseline, practice, and immediate transfer are available in sequence.
        for offset in range(3):
            human_probe.run_phase(session, self.correct_responder,
                                  now=self.now + timedelta(minutes=offset), echo=False)
        with self.assertRaisesRegex(ValueError, "available at"):
            human_probe.run_phase(session, self.correct_responder,
                                  now=self.now + timedelta(hours=1), echo=False)
        human_probe.run_phase(session, self.correct_responder,
                              now=self.now + timedelta(hours=1), allow_early=True, echo=False)
        human_probe.run_phase(session, self.correct_responder,
                              now=self.now + timedelta(hours=1, minutes=1), echo=False)
        human_probe.run_phase(session, self.correct_responder,
                              now=self.now + timedelta(hours=1, minutes=2), echo=False)
        self.assertIsNotNone(session["completed_at"])
        self.assertEqual(len(session["protocol_deviations"]), 1)
        summary = human_probe.session_summary(session)
        self.assertEqual(summary["primary_outcome"], 0.0)
        self.assertGreater(summary["joint_lift_over_initial_human"], 0)
        joint = session["phases"]["joint"]["items"]
        self.assertTrue(all(row["initial_answer"] != row["final_answer"] for row in joint))
        exported = human_probe.sanitized_export(session)
        self.assertEqual(exported["participant_hash"], session["participant_hash"])
        self.assertNotIn("local-pseudonym", json.dumps(exported))

    def test_refusal_does_not_create_a_session(self):
        with self.assertRaisesRegex(ValueError, "consent"):
            human_probe.new_session("pseudonym", False, now=self.now)


class DesignEvolutionTests(unittest.TestCase):
    def test_blinded_logs_select_expected_designs_and_pass_holdout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            designs = root / "designs"
            simulate.generate(output_dir=data)
            metrics = design_evolution.run(
                data_dir=data,
                designs_dir=designs,
                report_path=root / "results.md",
            )

            proposals = design_evolution.read_jsonl(data / "design_proposals.jsonl")
            serialized = json.dumps(proposals)
            self.assertEqual(len(proposals), 80)
            self.assertNotIn("ground_truth", serialized)
            for mechanism in design_evolution.EXPECTED_BUNDLES:
                self.assertNotIn(f'"{mechanism}"', serialized)

            self.assertTrue(metrics["promotion_gate"])
            self.assertTrue(metrics["all_specs_valid"])
            self.assertTrue(metrics["all_specs_clear"])
            self.assertEqual(metrics["designs"], 40)
            self.assertEqual(metrics["splits"]["holdout"]["exact_bundle_accuracy"], 1.0)
            self.assertEqual(metrics["splits"]["holdout"]["no_material_regression_rate"], 1.0)

    def test_no_trace_signal_proposes_no_behavioral_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            simulate.generate(output_dir=data)
            packets = design_evolution.read_jsonl(data / "packets.ordinary_trace.jsonl")
            series = design_evolution.read_jsonl(data / "synthetic_series.jsonl")
            truth = {row["series_id"]: row["ground_truth"]["mechanism"] for row in series}
            repetition = next(packet for packet in packets
                              if truth[packet["series_id"]] == "repetition_without_retention")
            proposal = design_evolution.infer_design(repetition)
            self.assertEqual(proposal["patterns"], [])
            self.assertEqual(proposal["design_key"], "unchanged")


if __name__ == "__main__":
    unittest.main()
