import re
import unittest
from pathlib import Path

import gui
from contract_test_catalog import CONTRACT_TEST_FILE_PATHS


EXPECTED_PUBLIC_API_CONTRACT_TESTS = set(CONTRACT_TEST_FILE_PATHS)


class PublicApiDocsContractsTests(unittest.TestCase):
    def _read_public_api_spec(self) -> str:
        root = Path(__file__).resolve().parents[1]
        spec_path = root / "docs" / "public_api_spec.md"
        return spec_path.read_text(encoding="utf-8")

    def _section_body(self, text: str, heading: str) -> str:
        start_index = text.find(heading)
        self.assertNotEqual(start_index, -1, f"public_api_spec.md missing '{heading}' section")
        section = text[start_index + len(heading):]
        next_heading = section.find("\n## ")
        if next_heading != -1:
            section = section[:next_heading]
        return section

    def test_public_api_spec_exports_match_gui_all(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "## Public Exports")

        documented_exports = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*$", section, flags=re.MULTILINE)
        }

        self.assertEqual(documented_exports, set(gui.__all__))

    def test_public_api_spec_enforced_tests_list_is_complete(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "Enforced contract tests:")

        documented_tests = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([^`]+)`\s*$", section, flags=re.MULTILINE)
        }

        self.assertEqual(documented_tests, EXPECTED_PUBLIC_API_CONTRACT_TESTS)


if __name__ == "__main__":
    unittest.main()
