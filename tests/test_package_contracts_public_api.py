import unittest
from pathlib import Path


class TestPackageContractsPublicAPI(unittest.TestCase):
    def test_package_contracts_contains_public_import_block(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("from gui_do import (", content)
        self.assertIn("from demo_features.mandelbrot_demo_feature import MandelStatusEvent", content)

    def test_package_contracts_lists_selected_stable_symbols(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
        content = path.read_text(encoding="utf-8")

        for name in (
            "GuiApplication",
            "WindowControl",
            "EventManager",
            "TelemetryCollector",
            "WorkspacePersistenceManager",
        ):
            self.assertIn(name, content)
