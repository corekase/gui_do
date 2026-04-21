import re
import unittest
from pathlib import Path


EXPECTED_ARCHITECTURE_DOCS = {
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
    "docs/architecture_boundary_spec.md",
}

EXPECTED_BOUNDARY_COMMANDS = [
    "python -m unittest tests.test_boundary_contracts tests.test_public_api_exports tests.test_mandel_event_schema_exports tests.test_public_api_docs_contracts tests.test_architecture_boundary_docs_contracts tests.test_contract_command_parity tests.test_readme_docs_contracts -v",
    "python -m pytest -q tests/test_boundary_contracts.py",
    "python -m pytest -q tests/test_boundary_contracts.py tests/test_public_api_exports.py tests/test_mandel_event_schema_exports.py tests/test_public_api_docs_contracts.py tests/test_architecture_boundary_docs_contracts.py tests/test_contract_command_parity.py tests/test_readme_docs_contracts.py",
]


class ReadmeDocsContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _read_readme(self) -> str:
        return (self._repo_root() / "README.md").read_text(encoding="utf-8")

    def _section_body(self, text: str, heading: str) -> str:
        start = text.find(heading)
        self.assertNotEqual(start, -1, f"README missing '{heading}' section")
        section = text[start + len(heading):]
        next_heading = section.find("\n## ")
        if next_heading != -1:
            section = section[:next_heading]
        return section

    def _boundary_commands(self) -> list[str]:
        section = self._section_body(self._read_readme(), "## Run Boundary Contract Tests")
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

    def test_architecture_docs_section_lists_expected_documents(self) -> None:
        section = self._section_body(self._read_readme(), "## Architecture Docs")
        documented = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([^`]+\.md)`:", section, flags=re.MULTILINE)
        }

        self.assertEqual(documented, EXPECTED_ARCHITECTURE_DOCS)

    def test_architecture_docs_paths_exist(self) -> None:
        root = self._repo_root()
        for doc_path in EXPECTED_ARCHITECTURE_DOCS:
            self.assertTrue((root / doc_path).exists(), f"documented architecture path does not exist: {doc_path}")

    def test_boundary_commands_match_expected_bundle_and_order(self) -> None:
        self.assertEqual(self._boundary_commands(), EXPECTED_BOUNDARY_COMMANDS)


if __name__ == "__main__":
    unittest.main()
