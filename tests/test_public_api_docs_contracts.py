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
