import re
import unittest
from pathlib import Path

from tests.contract_docs_helpers import section_body
from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER
from tests.contract_test_catalog import README_PUBLIC_API_GUI_IMPORT_ORDER
from tests.contract_test_catalog import README_PUBLIC_API_REQUIRED_DEMO_IMPORTS
from tests.contract_test_catalog import README_PUBLIC_API_REQUIRED_GUI_IMPORTS
from tests.contract_test_catalog import README_PUBLIC_API_REQUIRED_PHRASES


class ReadmePublicApiContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_readme(self) -> str:
        return (self._repo_root() / "README.md").read_text(encoding="utf-8")

    def _public_api_section(self) -> str:
        return section_body(self._read_readme(), "## Public API", "README")

    def test_public_api_section_contains_python_code_fence(self) -> None:
        section = self._public_api_section()

        self.assertRegex(section, r"```python[\s\S]*?```")

    def test_public_api_section_uses_package_root_gui_import_pattern(self) -> None:
        section = self._public_api_section()

        self.assertIn("from gui import (", section)
        self.assertNotIn("from gui.", section)

    def test_public_api_section_gui_import_block_matches_canonical_example(self) -> None:
        section = self._public_api_section()

        gui_import_block = re.search(r"from\s+gui\s+import\s*\((.*?)\)", section, flags=re.DOTALL)
        self.assertIsNotNone(gui_import_block, "README Public API section missing from gui import block")

        imported_names = [
            line.strip().rstrip(",")
            for line in gui_import_block.group(1).splitlines()
            if line.strip()
        ]

        self.assertEqual(len(imported_names), len(set(imported_names)))

        canonical = set(PUBLIC_API_EXPORT_ORDER)
        for name in imported_names:
            self.assertIn(name, canonical, f"README imports non-public gui symbol: {name}")

        self.assertEqual(tuple(imported_names), README_PUBLIC_API_GUI_IMPORT_ORDER)

        for required_name in README_PUBLIC_API_REQUIRED_GUI_IMPORTS:
            self.assertIn(required_name, imported_names)

    def test_public_api_section_includes_required_demo_import_lines(self) -> None:
        section = self._public_api_section()

        for required_import in README_PUBLIC_API_REQUIRED_DEMO_IMPORTS:
            self.assertIn(required_import, section)

    def test_public_api_section_contains_required_phrases(self) -> None:
        section = self._public_api_section()

        for phrase in README_PUBLIC_API_REQUIRED_PHRASES:
            self.assertIn(phrase, section)


if __name__ == "__main__":
    unittest.main()
