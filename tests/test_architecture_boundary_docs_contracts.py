import re
import unittest
from pathlib import Path

from tests.contract_docs_helpers import backticked_bullet_items
from tests.contract_docs_helpers import commands_from_fenced_section
from tests.contract_docs_helpers import package_boundary_commands
from tests.contract_docs_helpers import section_body
from tests.contract_test_catalog import ACTIVE_DEMO_ENTRYPOINTS
from tests.contract_test_catalog import BOUNDARY_ASSET_PATHS
from tests.contract_test_catalog import BOUNDARY_ENFORCEMENT_TEST_IDS
from tests.contract_test_catalog import BOUNDARY_PYTEST_COMMAND
from tests.contract_test_catalog import BOUNDARY_RELATED_DOC_PATHS
from tests.contract_test_catalog import BOUNDARY_RULE_REQUIRED_PHRASES


EXPECTED_BOUNDARY_ENFORCEMENT_TESTS = set(BOUNDARY_ENFORCEMENT_TEST_IDS)
EXPECTED_BOUNDARY_ENFORCEMENT_TESTS_ORDER = tuple(BOUNDARY_ENFORCEMENT_TEST_IDS)
EXPECTED_RELATED_DOCS = set(BOUNDARY_RELATED_DOC_PATHS)
EXPECTED_RELATED_DOCS_ORDER = tuple(BOUNDARY_RELATED_DOC_PATHS)
EXPECTED_BOUNDARY_ASSET_PATHS_ORDER = tuple(BOUNDARY_ASSET_PATHS)
EXPECTED_ACTIVE_DEMO_ENTRYPOINTS_ORDER = tuple(ACTIVE_DEMO_ENTRYPOINTS)


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

        documented_tests = [
            item
            for item in backticked_bullet_items(section)
            if "::" in item
        ]

        self.assertEqual(tuple(documented_tests), EXPECTED_BOUNDARY_ENFORCEMENT_TESTS_ORDER)
        self.assertEqual(set(documented_tests), EXPECTED_BOUNDARY_ENFORCEMENT_TESTS)
        self.assertEqual(len(documented_tests), len(set(documented_tests)))

    def test_boundary_spec_lists_pytest_run_command(self) -> None:
        text = self._read_boundary_spec()
        commands = commands_from_fenced_section(text, "## Enforcement", "architecture_boundary_spec.md", fence_language="bash")
        self.assertEqual(commands, [BOUNDARY_PYTEST_COMMAND])

    def test_boundary_spec_pytest_command_is_listed_in_package_boundary_commands(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Enforcement")
        self.assertIn(BOUNDARY_PYTEST_COMMAND, section)
        self.assertIn(BOUNDARY_PYTEST_COMMAND, package_boundary_commands(self._repo_root()))

    def test_boundary_rule_mentions_active_demo_entrypoint_scope(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Boundary Rule")
        normalized_section = section.replace("`", "")

        for phrase in BOUNDARY_RULE_REQUIRED_PHRASES:
            normalized_phrase = phrase.replace("`", "")
            self.assertIn(normalized_phrase, normalized_section)

    def test_current_demo_boundary_asset_paths_exist(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Current Demo Boundary Assets")
        repo_root = self._repo_root()
        documented_paths = [
            match.group(1)
            for match in re.finditer(r"`([^`]+\.py)`", section)
        ]

        self.assertEqual(tuple(documented_paths), EXPECTED_BOUNDARY_ASSET_PATHS_ORDER)
        self.assertEqual(len(documented_paths), len(set(documented_paths)))
        for relative_path in documented_paths:
            self.assertTrue((repo_root / relative_path).exists(), f"documented path does not exist: {relative_path}")

    def test_current_active_demo_entrypoints_match_expected(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Current Active Demo Entrypoints")
        repo_root = self._repo_root()
        documented_paths = [
            item
            for item in backticked_bullet_items(section)
            if item.endswith(".py")
        ]

        self.assertEqual(tuple(documented_paths), EXPECTED_ACTIVE_DEMO_ENTRYPOINTS_ORDER)
        self.assertEqual(len(documented_paths), len(set(documented_paths)))
        for relative_path in documented_paths:
            self.assertTrue((repo_root / relative_path).exists(), f"documented path does not exist: {relative_path}")

    def test_related_documents_list_matches_expected(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "Related documents:")
        documented_docs = [
            item
            for item in backticked_bullet_items(section)
            if item.endswith(".md")
        ]

        self.assertEqual(tuple(documented_docs), EXPECTED_RELATED_DOCS_ORDER)
        self.assertEqual(set(documented_docs), EXPECTED_RELATED_DOCS)
        self.assertEqual(len(documented_docs), len(set(documented_docs)))


if __name__ == "__main__":
    unittest.main()
