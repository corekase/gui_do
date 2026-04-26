import re
import unittest
from pathlib import Path

from tests.contract_docs_helpers import section_body
from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER
from tests.contract_test_catalog import PACKAGE_PUBLIC_API_GUI_IMPORT_ORDER
from tests.contract_test_catalog import PACKAGE_PUBLIC_API_REQUIRED_DEMO_IMPORTS
from tests.contract_test_catalog import PACKAGE_PUBLIC_API_REQUIRED_GUI_IMPORTS
from tests.contract_test_catalog import PACKAGE_PUBLIC_API_REQUIRED_PHRASES


class ReadmePublicApiContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_contract_doc(self) -> str:
        return (self._repo_root() / "docs" / "package_contracts.md").read_text(encoding="utf-8")

    def _public_api_section(self) -> str:
        return section_body(self._read_contract_doc(), "## Public API", "docs/package_contracts.md")

    def test_public_api_section_contains_python_code_fence(self) -> None:
        section = self._public_api_section()

        self.assertRegex(section, r"```python[\s\S]*?```")

    def test_public_api_section_uses_package_root_gui_import_pattern(self) -> None:
        section = self._public_api_section()

        self.assertIn("from gui_do import (", section)
        self.assertNotIn("from gui_do.", section)

    def test_public_api_section_gui_import_block_matches_canonical_example(self) -> None:
        section = self._public_api_section()

        gui_import_block = re.search(r"from\s+gui_do\s+import\s*\((.*?)\)", section, flags=re.DOTALL)
        self.assertIsNotNone(gui_import_block, "package contracts Public API section missing from gui_do import block")

        imported_names = [
            line.strip().rstrip(",")
            for line in gui_import_block.group(1).splitlines()
            if line.strip()
        ]

        self.assertEqual(len(imported_names), len(set(imported_names)))

        canonical = set(PUBLIC_API_EXPORT_ORDER)
        for name in imported_names:
            self.assertIn(name, canonical, f"package contracts imports non-public gui_do symbol: {name}")

        self.assertEqual(tuple(imported_names), PACKAGE_PUBLIC_API_GUI_IMPORT_ORDER)

        for required_name in PACKAGE_PUBLIC_API_REQUIRED_GUI_IMPORTS:
            self.assertIn(required_name, imported_names)

    def test_public_api_section_includes_required_demo_import_lines(self) -> None:
        section = self._public_api_section()

        for required_import in PACKAGE_PUBLIC_API_REQUIRED_DEMO_IMPORTS:
            self.assertIn(required_import, section)

    def test_public_api_section_contains_required_phrases(self) -> None:
        section = self._public_api_section()

        for phrase in PACKAGE_PUBLIC_API_REQUIRED_PHRASES:
            self.assertIn(phrase, section)


if __name__ == "__main__":
    unittest.main()
