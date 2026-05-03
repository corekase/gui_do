import unittest
from pathlib import Path


class TestArchitectureBoundaryDocsContracts(unittest.TestCase):
    def test_boundary_spec_documents_rule_and_enforcement_tests(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "architecture_boundary_spec.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("## Boundary Rule", content)
        self.assertIn("`gui_do/` is framework/runtime package code and must not depend on `demo_features/`.", content)
        self.assertIn("tests/test_boundary_contracts.py::test_gui_package_does_not_import_demo_features", content)
        self.assertIn("tests/test_boundary_contracts.py::test_demo_entrypoint_uses_gui_root_import", content)
