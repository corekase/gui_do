import re
import unittest
from pathlib import Path

from contract_docs_helpers import backticked_bullet_items
from contract_docs_helpers import readme_boundary_commands
from contract_docs_helpers import section_body
from contract_test_catalog import ARCHITECTURE_DOC_PATHS
from contract_test_catalog import BOUNDARY_COMMAND_SEQUENCE
from contract_test_catalog import README_BOUNDARY_REQUIRED_PHRASES

EXPECTED_ARCHITECTURE_DOCS = set(ARCHITECTURE_DOC_PATHS)
EXPECTED_BOUNDARY_COMMANDS = list(BOUNDARY_COMMAND_SEQUENCE)


class ReadmeDocsContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_readme(self) -> str:
        return (self._repo_root() / "README.md").read_text(encoding="utf-8")

    def _section_body(self, text: str, heading: str) -> str:
        return section_body(text, heading, "README")

    def test_architecture_docs_section_lists_expected_documents(self) -> None:
        section = self._section_body(self._read_readme(), "## Architecture Docs")
        documented = {
            item
            for item in backticked_bullet_items(section)
            if item.endswith(".md")
        }

        self.assertEqual(documented, EXPECTED_ARCHITECTURE_DOCS)

    def test_architecture_docs_paths_exist(self) -> None:
        root = self._repo_root()
        for doc_path in EXPECTED_ARCHITECTURE_DOCS:
            self.assertTrue((root / doc_path).exists(), f"documented architecture path does not exist: {doc_path}")

    def test_boundary_commands_match_expected_bundle_and_order(self) -> None:
        self.assertEqual(readme_boundary_commands(self._repo_root()), EXPECTED_BOUNDARY_COMMANDS)

    def test_demo_package_boundary_section_contains_required_phrases(self) -> None:
        section = self._section_body(self._read_readme(), "## Demo/Package Boundary")
        normalized_section = section.replace("`", "")

        for phrase in README_BOUNDARY_REQUIRED_PHRASES:
            normalized_phrase = phrase.replace("`", "")
            self.assertIn(normalized_phrase, normalized_section)


if __name__ == "__main__":
    unittest.main()
