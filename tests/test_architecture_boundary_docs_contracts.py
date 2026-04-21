import re
import unittest
from pathlib import Path

from contract_docs_helpers import readme_boundary_commands
from contract_docs_helpers import section_body
from contract_test_catalog import BOUNDARY_ENFORCEMENT_TEST_IDS
from contract_test_catalog import BOUNDARY_PYTEST_COMMAND
from contract_test_catalog import BOUNDARY_RELATED_DOC_PATHS


EXPECTED_BOUNDARY_ENFORCEMENT_TESTS = set(BOUNDARY_ENFORCEMENT_TEST_IDS)
EXPECTED_RELATED_DOCS = set(BOUNDARY_RELATED_DOC_PATHS)


class ArchitectureBoundaryDocsContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_boundary_spec(self) -> str:
        root = self._repo_root()
        return (root / "docs" / "architecture_boundary_spec.md").read_text(encoding="utf-8")

    def _section_body(self, text: str, heading: str) -> str:
        return section_body(text, heading, "architecture_boundary_spec.md")

    def test_enforcement_list_matches_expected_boundary_tests(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Enforcement")

        documented_tests = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([^`]+)`\s*$", section, flags=re.MULTILINE)
            if "::" in match.group(1)
        }

        self.assertEqual(documented_tests, EXPECTED_BOUNDARY_ENFORCEMENT_TESTS)

    def test_boundary_spec_lists_pytest_run_command(self) -> None:
        text = self._read_boundary_spec()
        self.assertIn(BOUNDARY_PYTEST_COMMAND, text)

    def test_boundary_spec_pytest_command_is_listed_in_readme_boundary_commands(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Enforcement")
        self.assertIn(BOUNDARY_PYTEST_COMMAND, section)
        self.assertIn(BOUNDARY_PYTEST_COMMAND, readme_boundary_commands(self._repo_root()))

    def test_boundary_rule_mentions_active_demo_entrypoint_scope(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Boundary Rule")

        self.assertIn("*_demo.py", section)
        self.assertIn("_pre_rebase*_demo.py", section)

    def test_current_demo_boundary_asset_paths_exist(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Current Demo Boundary Assets")
        repo_root = self._repo_root()
        documented_paths = {
            match.group(1)
            for match in re.finditer(r"`([^`]+\.py)`", section)
        }

        self.assertIn("demo_parts/mandel_events.py", documented_paths)
        for relative_path in documented_paths:
            self.assertTrue((repo_root / relative_path).exists(), f"documented path does not exist: {relative_path}")

    def test_related_documents_list_matches_expected(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "Related documents:")
        documented_docs = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([^`]+\.md)`\s*$", section, flags=re.MULTILINE)
        }

        self.assertEqual(documented_docs, EXPECTED_RELATED_DOCS)


if __name__ == "__main__":
    unittest.main()
