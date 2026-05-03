import unittest
from pathlib import Path


class TestPackageContractsDocs(unittest.TestCase):
    def test_package_contracts_lists_expected_architecture_docs(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("docs/public_api_spec.md", content)
        self.assertIn("docs/event_system_spec.md", content)
        self.assertIn("docs/architecture_boundary_spec.md", content)
        self.assertIn("docs/runtime_operating_contracts.md", content)
        self.assertIn("docs/library_demo_separation_contract.md", content)

    def test_package_contracts_includes_unittest_and_pytest_commands(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("python -m unittest", content)
        self.assertIn("python -m pytest -q", content)

    def test_package_contracts_declares_named_import_policy(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("Supported usage is explicit named imports from `gui_do`.", content)
        self.assertIn("Star-import behavior is not part of the package contract.", content)
