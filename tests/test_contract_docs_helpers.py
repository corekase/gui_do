import unittest
from pathlib import Path

from contract_docs_helpers import readme_boundary_commands
from contract_docs_helpers import section_body
from contract_docs_helpers import workflow_step_run_command
from contract_test_catalog import CONTRACT_PYTEST_COMMAND
from contract_test_catalog import CONTRACT_UNITTEST_COMMAND


class ContractDocsHelpersTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_section_body_extracts_expected_content(self) -> None:
        text = "## A\nline-a\n## B\nline-b\n"

        extracted = section_body(text, "## A", "sample")

        self.assertEqual(extracted.strip(), "line-a")

    def test_section_body_raises_for_missing_heading(self) -> None:
        with self.assertRaises(AssertionError):
            section_body("## A\nvalue\n", "## Missing", "sample")

    def test_readme_boundary_commands_include_canonical_contract_commands(self) -> None:
        commands = readme_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_UNITTEST_COMMAND, commands)
        self.assertIn(CONTRACT_PYTEST_COMMAND, commands)

    def test_workflow_step_run_command_matches_canonical_contract_unittest(self) -> None:
        run_command = workflow_step_run_command(self._repo_root(), "Run boundary contract tests")

        self.assertEqual(run_command, CONTRACT_UNITTEST_COMMAND)

    def test_workflow_step_run_command_raises_for_unknown_step(self) -> None:
        with self.assertRaises(AssertionError):
            workflow_step_run_command(self._repo_root(), "Missing Step")


if __name__ == "__main__":
    unittest.main()
