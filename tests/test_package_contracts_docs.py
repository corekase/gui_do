import unittest
from pathlib import Path


class TestPackageContractsDocs(unittest.TestCase):
    def test_package_contracts_lists_expected_architecture_docs(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("docs/public_api_spec.md", content)
        self.assertIn("docs/event_system_spec.md", content)
        self.assertIn("docs/architecture_boundary_spec.md", content)
        self.assertIn("docs/final_considerations_execution_plan.md", content)
        self.assertIn("docs/runtime_operating_contracts.md", content)

    def test_package_contracts_includes_unittest_and_pytest_commands(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("python -m unittest", content)
        self.assertIn("python -m pytest -q", content)
