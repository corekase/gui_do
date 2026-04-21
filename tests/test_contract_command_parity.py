import unittest
from pathlib import Path


EXPECTED_CONTRACT_UNITTEST_COMMAND = (
    "python -m unittest "
    "tests.test_boundary_contracts "
    "tests.test_public_api_exports "
    "tests.test_mandel_event_schema_exports "
    "tests.test_public_api_docs_contracts "
    "tests.test_architecture_boundary_docs_contracts "
    "tests.test_contract_command_parity "
    "tests.test_readme_docs_contracts -v"
)

EXPECTED_CONTRACT_PYTEST_COMMAND = (
    "python -m pytest -q "
    "tests/test_boundary_contracts.py "
    "tests/test_public_api_exports.py "
    "tests/test_mandel_event_schema_exports.py "
    "tests/test_public_api_docs_contracts.py "
    "tests/test_architecture_boundary_docs_contracts.py "
    "tests/test_contract_command_parity.py "
    "tests/test_readme_docs_contracts.py"
)


class ContractCommandParityTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _readme_boundary_commands(self) -> list[str]:
        text = (self._repo_root() / "README.md").read_text(encoding="utf-8")
        heading = "## Run Boundary Contract Tests"
        start = text.find(heading)
        self.assertNotEqual(start, -1, "README missing 'Run Boundary Contract Tests' section")

        section = text[start + len(heading):]
        fence_start = section.find("```bash")
        self.assertNotEqual(fence_start, -1, "README boundary section missing bash code fence")
        section = section[fence_start + len("```bash"):]
        fence_end = section.find("```")
        self.assertNotEqual(fence_end, -1, "README boundary section missing closing code fence")
        code_block = section[:fence_end]

        commands = []
        for raw_line in code_block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append(line)
        return commands

    def _workflow_boundary_contract_command(self) -> str:
        workflow_text = (self._repo_root() / ".github" / "workflows" / "unittest.yml").read_text(encoding="utf-8")
        target = "- name: Run boundary contract tests"
        start = workflow_text.find(target)
        self.assertNotEqual(start, -1, "workflow missing 'Run boundary contract tests' step")

        section = workflow_text[start:]
        run_marker = "run: "
        run_index = section.find(run_marker)
        self.assertNotEqual(run_index, -1, "workflow boundary contract step missing run command")
        run_line = section[run_index + len(run_marker):].splitlines()[0].strip()
        self.assertTrue(run_line, "workflow boundary contract run command is empty")
        return run_line

    def test_readme_lists_ci_equivalent_contract_unittest_command(self) -> None:
        commands = self._readme_boundary_commands()

        self.assertIn(EXPECTED_CONTRACT_UNITTEST_COMMAND, commands)

    def test_workflow_uses_expected_contract_unittest_command(self) -> None:
        workflow_command = self._workflow_boundary_contract_command()

        self.assertEqual(workflow_command, EXPECTED_CONTRACT_UNITTEST_COMMAND)

    def test_readme_lists_full_contract_pytest_command(self) -> None:
        commands = self._readme_boundary_commands()

        self.assertIn(EXPECTED_CONTRACT_PYTEST_COMMAND, commands)


if __name__ == "__main__":
    unittest.main()
