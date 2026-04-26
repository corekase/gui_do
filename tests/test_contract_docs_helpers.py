import unittest
from pathlib import Path

from tests.contract_docs_helpers import commands_from_fenced_section
from tests.contract_docs_helpers import backticked_bullet_items
from tests.contract_docs_helpers import package_boundary_commands
from tests.contract_docs_helpers import section_body
from tests.contract_docs_helpers import workflow_step_names
from tests.contract_docs_helpers import workflow_step_names_from_text
from tests.contract_docs_helpers import workflow_step_run_command
from tests.contract_docs_helpers import workflow_step_run_command_from_text
from tests.contract_test_catalog import BOUNDARY_WORKFLOW_STEP_NAME
from tests.contract_test_catalog import CONTRACT_PYTEST_COMMAND
from tests.contract_test_catalog import CONTRACT_UNITTEST_COMMAND


EXPECTED_HELPER_TEST_METHODS = (
    "test_workflow_step_run_command_from_text_supports_single_line_run",
    "test_workflow_step_run_command_from_text_supports_block_run",
    "test_workflow_step_run_command_from_text_raises_for_empty_block",
    "test_workflow_step_run_command_from_text_does_not_use_later_step_run",
    "test_workflow_step_names_from_text_extracts_names_in_order",
    "test_workflow_step_names_includes_canonical_boundary_step",
)


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

    def test_backticked_bullet_items_extracts_items_in_order(self) -> None:
        section = "- `one`\n- `two`: desc\n- plain\n"

        items = backticked_bullet_items(section)

        self.assertEqual(items, ["one", "two"])

    def test_commands_from_fenced_section_extracts_commands(self) -> None:
        text = "## Commands\n```bash\n# comment\ncmd a\n\ncmd b\n```\n## Next\n"

        commands = commands_from_fenced_section(text, "## Commands", "sample")

        self.assertEqual(commands, ["cmd a", "cmd b"])

    def test_commands_from_fenced_section_raises_for_missing_fence(self) -> None:
        text = "## Commands\nno fence\n"

        with self.assertRaises(AssertionError):
            commands_from_fenced_section(text, "## Commands", "sample")

    def test_commands_from_fenced_section_raises_for_missing_closing_fence(self) -> None:
        text = "## Commands\n```bash\ncmd a\n"

        with self.assertRaises(AssertionError):
            commands_from_fenced_section(text, "## Commands", "sample")

    def test_package_boundary_commands_include_canonical_contract_commands(self) -> None:
        commands = package_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_UNITTEST_COMMAND, commands)
        self.assertIn(CONTRACT_PYTEST_COMMAND, commands)

    def test_workflow_step_run_command_matches_canonical_contract_unittest(self) -> None:
        run_command = workflow_step_run_command(self._repo_root(), BOUNDARY_WORKFLOW_STEP_NAME)

        self.assertEqual(run_command, CONTRACT_UNITTEST_COMMAND)

    def test_workflow_step_run_command_raises_for_unknown_step(self) -> None:
        with self.assertRaises(AssertionError):
            workflow_step_run_command(self._repo_root(), "Missing Step")

    def test_workflow_step_run_command_from_text_supports_single_line_run(self) -> None:
        workflow_text = """
jobs:
    test:
        steps:
            - name: Example
                run: python -m unittest tests.test_boundary_contracts -v
"""

        run_command = workflow_step_run_command_from_text(workflow_text, "Example")

        self.assertEqual(run_command, "python -m unittest tests.test_boundary_contracts -v")

    def test_workflow_step_run_command_from_text_supports_block_run(self) -> None:
        workflow_text = """
jobs:
    test:
        steps:
            - name: Example
                run: |
                    # comment
                    python -m unittest tests.test_boundary_contracts -v
                    python -m pytest -q tests/test_boundary_contracts.py
"""

        run_command = workflow_step_run_command_from_text(workflow_text, "Example")

        self.assertEqual(run_command, "python -m unittest tests.test_boundary_contracts -v")

    def test_workflow_step_run_command_from_text_raises_for_empty_block(self) -> None:
        workflow_text = """
jobs:
    test:
        steps:
            - name: Example
                run: |
                    # only comment
"""

        with self.assertRaises(AssertionError):
            workflow_step_run_command_from_text(workflow_text, "Example")

    def test_workflow_step_run_command_from_text_does_not_use_later_step_run(self) -> None:
        workflow_text = """
jobs:
    test:
        steps:
            - name: First
            - name: Second
                run: python -m unittest tests.test_boundary_contracts -v
"""

        with self.assertRaises(AssertionError):
            workflow_step_run_command_from_text(workflow_text, "First")

    def test_workflow_step_names_from_text_extracts_names_in_order(self) -> None:
        workflow_text = """
jobs:
    test:
        steps:
            - name: Checkout
                uses: actions/checkout@v4
            - name: Run boundary contract tests
                run: python -m unittest tests.test_boundary_contracts -v
            - name: Coverage report
                run: python -m coverage report -m
"""

        step_names = workflow_step_names_from_text(workflow_text)

        self.assertEqual(step_names, ["Checkout", "Run boundary contract tests", "Coverage report"])

    def test_workflow_step_names_includes_canonical_boundary_step(self) -> None:
        step_names = workflow_step_names(self._repo_root())

        self.assertIn(BOUNDARY_WORKFLOW_STEP_NAME, step_names)

    def test_helper_guard_expected_methods_exist_as_class_methods(self) -> None:
        for method_name in EXPECTED_HELPER_TEST_METHODS:
            self.assertTrue(hasattr(ContractDocsHelpersTests, method_name), f"missing test method: {method_name}")


if __name__ == "__main__":
    unittest.main()
