import unittest
from pathlib import Path

from tests.contract_docs_helpers import readme_boundary_commands
from tests.contract_docs_helpers import workflow_step_names
from tests.contract_docs_helpers import workflow_step_run_command
from tests.contract_test_catalog import CONTRACT_PYTEST_COMMAND
from tests.contract_test_catalog import CONTRACT_UNITTEST_COMMAND
from tests.contract_test_catalog import BOUNDARY_WORKFLOW_STEP_NAME



class ContractCommandParityTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_readme_lists_ci_equivalent_contract_unittest_command(self) -> None:
        commands = readme_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_UNITTEST_COMMAND, commands)

    def test_workflow_uses_expected_contract_unittest_command(self) -> None:
        workflow_command = workflow_step_run_command(self._repo_root(), BOUNDARY_WORKFLOW_STEP_NAME)

        self.assertEqual(workflow_command, CONTRACT_UNITTEST_COMMAND)

    def test_workflow_contains_exactly_one_canonical_boundary_step_name(self) -> None:
        step_names = workflow_step_names(self._repo_root())

        self.assertEqual(step_names.count(BOUNDARY_WORKFLOW_STEP_NAME), 1)

    def test_readme_lists_full_contract_pytest_command(self) -> None:
        commands = readme_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_PYTEST_COMMAND, commands)


if __name__ == "__main__":
    unittest.main()
