import unittest
from pathlib import Path


class TestPublicAPIDocsContracts(unittest.TestCase):
    def test_public_api_spec_includes_strict_contract_language(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "public_api_spec.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("strict contracts", content)
        self.assertIn("runtime behavior is intentionally deterministic under load", content)

    def test_public_api_spec_lists_telemetry_exports(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "public_api_spec.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("- `TelemetryCollector`", content)
        self.assertIn("- `TelemetrySample`", content)
        self.assertIn("- `configure_telemetry`", content)
        self.assertIn("- `telemetry_collector`", content)

    def test_public_api_spec_declares_named_import_contract(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "public_api_spec.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("## Import Contract", content)
        self.assertIn("Supported consumer imports use explicit named imports from `gui_do`.", content)
        self.assertIn("Star-import behavior is not part of the public contract.", content)
        self.assertNotIn("gui_do.__all__", content)

    def test_public_api_spec_declares_scene_chrome_contracts(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "public_api_spec.md"
        content = path.read_text(encoding="utf-8")

        self.assertIn("At most one scene-level task panel per scene.", content)
        self.assertIn("Task panels are scene chrome and cannot be added to windows.", content)
        self.assertIn("Scene-level menu strips are always full-width and top-docked in scene space.", content)
        self.assertIn("Window-level menu strips are always full-width and top-docked within their owning window.", content)
        self.assertIn("GuiApplication.bounded_area_rect(scene_name=None)", content)
