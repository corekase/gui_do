import re
import unittest
from pathlib import Path


EXPECTED_BOUNDARY_ENFORCEMENT_TESTS = {
    "tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_parts",
    "tests/test_boundary_contracts.py::test_demo_parts_does_not_depend_on_gui",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only",
}

EXPECTED_RELATED_DOCS = {
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
}


class ArchitectureBoundaryDocsContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_boundary_spec(self) -> str:
        root = self._repo_root()
        return (root / "docs" / "architecture_boundary_spec.md").read_text(encoding="utf-8")

    def _readme_boundary_commands(self) -> list[str]:
        text = (self._repo_root() / "README.md").read_text(encoding="utf-8")
        heading = "## Run Boundary Contract Tests"
        start = text.find(heading)
        self.assertNotEqual(start, -1, "README missing 'Run Boundary Contract Tests' section")

        section = text[start + len(heading):]
        fence_start = section.find("```bash")
        self.assertNotEqual(fence_start, -1, "README boundary section missing bash code fence")
        section = section[fence_start + len("```bash"):]
        fence_end = section.find("```")
        self.assertNotEqual(fence_end, -1, "README boundary section missing closing code fence")
        code_block = section[:fence_end]

        commands = []
        for raw_line in code_block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append(line)
        return commands

    def _section_body(self, text: str, heading: str) -> str:
        start_index = text.find(heading)
        self.assertNotEqual(start_index, -1, f"architecture_boundary_spec.md missing '{heading}' section")
        section = text[start_index + len(heading):]
        next_heading = section.find("\n## ")
        if next_heading != -1:
            section = section[:next_heading]
        return section

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
        self.assertIn("python -m pytest -q tests/test_boundary_contracts.py", text)

    def test_boundary_spec_pytest_command_is_listed_in_readme_boundary_commands(self) -> None:
        text = self._read_boundary_spec()
        section = self._section_body(text, "## Enforcement")
        match = re.search(r"python -m pytest -q tests/test_boundary_contracts\.py", section)
        self.assertIsNotNone(match, "boundary spec missing canonical boundary pytest command")
        command = match.group(0)

        self.assertIn(command, self._readme_boundary_commands())

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
