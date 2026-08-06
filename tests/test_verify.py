import os
import sys
import tempfile
import unittest

import yaml


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import verify as implementation_verifier  # noqa: E402


def guarded_spec():
    return {
        "loop": "outreach approval",
        "runs": "per request",
        "goal": {"safe outreach": {"keep": "human approved"}},
        "observes": {
            "draft state": {"informs": "safe outreach", "origin": "ourselves"},
        },
        "actions": {
            "approveInitialOutreach": {
                "moves": "safe outreach",
                "can_undo": "costly",
                "needs_approval": "operator",
            },
        },
        "when": [{"if": "a draft is ready", "do": "approveInitialOutreach"}],
        "people": {
            "operator": {"human": True, "loses_if_wrong": "founder trust"},
        },
    }


class ImplementationVerifierTests(unittest.TestCase):
    def findings(self, artifact, suffix=".ts"):
        with tempfile.TemporaryDirectory() as directory:
            spec_path = os.path.join(directory, "approval.loop.yaml")
            artifact_path = os.path.join(directory, f"implementation{suffix}")
            with open(spec_path, "w") as target:
                yaml.safe_dump(guarded_spec(), target, sort_keys=False)
            with open(artifact_path, "w") as target:
                target.write(artifact)
            return implementation_verifier.verify(spec_path, artifact_path)

    def gate_lost(self, artifact, suffix=".ts"):
        return any(finding["kind"] == "gate_lost"
                   for finding in self.findings(artifact, suffix))

    def test_action_name_cannot_supply_its_own_approval_evidence(self):
        self.assertTrue(self.gate_lost("""
            export function approveInitialOutreach(): string {
              return sendDraft();
            }
        """))

    def test_comment_cannot_supply_approval_evidence(self):
        self.assertTrue(self.gate_lost("""
            export function approveInitialOutreach(): string {
              // human approval required here
              return sendDraft();
            }
        """))

    def test_string_literal_cannot_supply_approval_evidence(self):
        self.assertTrue(self.gate_lost("""
            export function approveInitialOutreach(): string {
              return "human approval required here";
            }
        """))

    def test_unrelated_global_gate_does_not_rescue_an_ungated_action(self):
        self.assertTrue(self.gate_lost("""
            function authorize(operator: object): void { return; }
            export function approveInitialOutreach(): string {
              return sendDraft();
            }
        """))

    def test_executable_gate_in_the_action_body_survives(self):
        self.assertFalse(self.gate_lost("""
            export function approveInitialOutreach(): string {
              authorize(operator);
              return sendDraft();
            }
        """))

    def test_python_function_body_is_scoped_and_comments_are_ignored(self):
        findings = self.findings("""
def approve_initial_outreach():
    # approval prose is not the evidence
    require_approval(operator)
    return send_draft()
        """, suffix=".py")
        self.assertFalse(any(finding["kind"] in {"action_missing", "gate_lost"}
                             for finding in findings))

    def test_recipe_fallback_can_recognise_a_gate_around_an_action_call(self):
        self.assertFalse(self.gate_lost("""
            if (authorized(operator)) {
              approveInitialOutreach();
            }
        """))


if __name__ == "__main__":
    unittest.main()
