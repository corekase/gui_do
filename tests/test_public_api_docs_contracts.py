import re
import unittest
from pathlib import Path

import gui


class PublicApiDocsContractsTests(unittest.TestCase):
    def test_public_api_spec_exports_match_gui_all(self) -> None:
        root = Path(__file__).resolve().parents[1]
        spec_path = root / "docs" / "public_api_spec.md"
        text = spec_path.read_text(encoding="utf-8")

        start_marker = "## Public Exports"
        start_index = text.find(start_marker)
        self.assertNotEqual(start_index, -1, "public_api_spec.md missing '## Public Exports' section")

        section = text[start_index + len(start_marker):]
        next_heading = section.find("\n## ")
        if next_heading != -1:
            section = section[:next_heading]

        documented_exports = {
            match.group(1)
            for match in re.finditer(r"^-\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*$", section, flags=re.MULTILINE)
        }

        self.assertEqual(documented_exports, set(gui.__all__))


if __name__ == "__main__":
    unittest.main()
