import unittest
from pathlib import Path

import gui_do


class TestRuntimeOperatingContracts(unittest.TestCase):
    def _read_contract_doc(self) -> str:
        path = Path(__file__).resolve().parents[1] / "docs" / "runtime_operating_contracts.md"
        return path.read_text(encoding="utf-8")

    def test_contract_doc_contains_required_sections(self):
        content = self._read_contract_doc()

        required_sections = [
            "## 1. System Guarantees",
            "## 2. Cross-System Behavior Contracts",
            "## 3. Determinism and Safety Rails",
            "## 4. Observability and Diagnostics",
            "## 5. Public Surface Stability Policy",
            "## 6. Performance Budgets",
            "## Release Gate",
        ]

        for heading in required_sections:
            self.assertIn(heading, content)

    def test_contract_doc_stable_abstractions_exist_in_public_api(self):
        content = self._read_contract_doc()
        marker = "Stable extension abstractions for demo composition include:"
        self.assertIn(marker, content)

        stable_symbols = [
            "ActiveTabUpdateRouter",
            "TabLayoutContext",
            "FeatureSpec",
            "WindowSpec",
            "RuntimeSceneSpec",
            "ActionSpec",
            "TabBuilderSpec",
            "AnchoredWindowSpec",
            "bootstrap_host_application",
        ]

        for name in stable_symbols:
            self.assertTrue(hasattr(gui_do, name), msg=f"Missing public symbol: {name}")

    def test_scheduler_budget_policy_matches_runtime_constants(self):
        content = self._read_contract_doc()

        self.assertIn("fraction: 0.12", content)
        self.assertIn("floor: 0.5 ms", content)
        self.assertIn("ceiling: 4.0 ms", content)

    def test_contract_doc_declares_application_workspace_report_contract(self):
        content = self._read_contract_doc()

        self.assertIn(
            "Application workspace facade methods return restore reports (GuiApplication.restore_workspace and GuiApplication.load_workspace).",
            content,
        )

    def test_contract_doc_declares_run_entrypoint_resilience(self):
        content = self._read_contract_doc()

        self.assertIn(
            "GuiApplication.run_entrypoint tolerates workspace load/save failures without aborting shutdown sequencing.",
            content,
        )
        self.assertIn(
            "GuiApplication.run_entrypoint reports runtime loop failures and exits with a non-zero code.",
            content,
        )


if __name__ == "__main__":
    unittest.main()
