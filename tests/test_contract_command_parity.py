import unittest
from pathlib import Path


class TestContractCommandParity(unittest.TestCase):
    def test_contract_commands_include_boundary_suite_in_unittest_and_pytest_forms(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("python -m unittest", content)
        self.assertIn("tests.test_boundary_contracts", content)

        self.assertIn("python -m pytest -q", content)
        self.assertIn("tests/test_boundary_contracts.py", content)

        self.assertIn("tests.test_runtime_operating_contracts", content)
        self.assertIn("tests.test_gui_application_workspace_contracts", content)
        self.assertIn("tests/test_runtime_operating_contracts.py", content)
        self.assertIn("tests/test_gui_application_workspace_contracts.py", content)
