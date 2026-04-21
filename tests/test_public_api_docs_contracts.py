import re
import unittest
from pathlib import Path

from contract_docs_helpers import backticked_bullet_items
from contract_docs_helpers import section_body
from contract_test_catalog import PUBLIC_API_REQUIRED_PHRASES
from contract_test_catalog import PUBLIC_API_REQUIRED_REFERENCES
from contract_test_catalog import CONTRACT_TEST_FILE_PATHS
from contract_test_catalog import PUBLIC_API_EXPORT_ORDER


EXPECTED_PUBLIC_API_CONTRACT_TESTS = tuple(CONTRACT_TEST_FILE_PATHS)
EXPECTED_PUBLIC_EXPORT_ORDER = tuple(PUBLIC_API_EXPORT_ORDER)


class PublicApiDocsContractsTests(unittest.TestCase):
    def _read_public_api_spec(self) -> str:
        root = Path(__file__).resolve().parents[1]
        spec_path = root / "docs" / "public_api_spec.md"
        return spec_path.read_text(encoding="utf-8")

    def _section_body(self, text: str, heading: str) -> str:
        return section_body(text, heading, "public_api_spec.md")

    def test_public_api_spec_exports_match_gui_all(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "## Public Exports")

        documented_exports = [
            match.group(1)
            for match in re.finditer(r"^-\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*$", section, flags=re.MULTILINE)
        ]

        self.assertEqual(tuple(documented_exports), EXPECTED_PUBLIC_EXPORT_ORDER)
        self.assertEqual(len(documented_exports), len(set(documented_exports)))

    def test_public_api_spec_enforced_tests_list_is_complete(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "Enforced contract tests:")

        documented_tests = backticked_bullet_items(section)

        self.assertEqual(tuple(documented_tests), EXPECTED_PUBLIC_API_CONTRACT_TESTS)

    def test_demo_specific_modules_section_contains_required_references(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "## Demo-Specific Modules")

        for reference in PUBLIC_API_REQUIRED_REFERENCES:
            self.assertIn(reference, section)

    def test_demo_specific_modules_section_contains_required_phrases(self) -> None:
        text = self._read_public_api_spec()
        section = self._section_body(text, "## Demo-Specific Modules")
        normalized_section = section.replace("`", "")

        for phrase in PUBLIC_API_REQUIRED_PHRASES:
            normalized_phrase = phrase.replace("`", "")
            self.assertIn(normalized_phrase, normalized_section)


if __name__ == "__main__":
    unittest.main()
