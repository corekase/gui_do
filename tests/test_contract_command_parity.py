import unittest
from pathlib import Path

from contract_docs_helpers import readme_boundary_commands
from contract_docs_helpers import workflow_step_run_command
from contract_test_catalog import CONTRACT_PYTEST_COMMAND
from contract_test_catalog import CONTRACT_UNITTEST_COMMAND



class ContractCommandParityTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_readme_lists_ci_equivalent_contract_unittest_command(self) -> None:
        commands = readme_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_UNITTEST_COMMAND, commands)

    def test_workflow_uses_expected_contract_unittest_command(self) -> None:
        workflow_command = workflow_step_run_command(self._repo_root(), "Run boundary contract tests")

        self.assertEqual(workflow_command, CONTRACT_UNITTEST_COMMAND)

    def test_readme_lists_full_contract_pytest_command(self) -> None:
        commands = readme_boundary_commands(self._repo_root())

        self.assertIn(CONTRACT_PYTEST_COMMAND, commands)


if __name__ == "__main__":
    unittest.main()
