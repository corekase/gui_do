import unittest
from pathlib import Path


def _read_doc(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "docs" / name
    return path.read_text(encoding="utf-8")


def _assert_headings_present_in_order(test_case: unittest.TestCase, content: str, headings: list[str]) -> None:
    cursor = 0
    for heading in headings:
        index = content.find(heading, cursor)
        test_case.assertNotEqual(-1, index, msg=f"Missing heading: {heading}")
        cursor = index + len(heading)


class TestContractDocsHelpers(unittest.TestCase):
    def test_runtime_operating_contracts_has_numbered_sections(self):
        content = _read_doc("runtime_operating_contracts.md")
        _assert_headings_present_in_order(
            self,
            content,
            [
                "## 1. System Guarantees",
                "## 2. Cross-System Behavior Contracts",
                "## 3. Determinism and Safety Rails",
                "## 4. Observability and Diagnostics",
                "## 5. Public Surface Stability Policy",
                "## 6. Performance Budgets",
            ],
        )

    def test_library_demo_separation_contract_has_required_sections(self):
        content = _read_doc("library_demo_separation_contract.md")

        self.assertIn("## Principle", content)
        self.assertIn("## Import Boundary", content)
        self.assertIn("## Packaging Boundary", content)
