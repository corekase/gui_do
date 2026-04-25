import tempfile
import unittest
from pathlib import Path

from gui.core.telemetry import TelemetryCollector
from gui.core.telemetry_analyzer import analyze_telemetry_records
from gui.core.telemetry_analyzer import load_telemetry_log_file
from gui.core.telemetry_analyzer import render_telemetry_report


class TelemetryCoreRuntimeTests(unittest.TestCase):
    def test_default_disabled_does_not_capture(self) -> None:
        collector = TelemetryCollector()
        collector.record_duration("gui", "update", 1.0)
        self.assertEqual(collector.snapshot(), [])

    def test_system_and_point_filters_can_disable_capture(self) -> None:
        collector = TelemetryCollector()
        collector.enable()

        collector.record_duration("gui", "update", 1.0)
        collector.set_system_enabled("gui", False)
        collector.record_duration("gui", "update", 2.0)
        collector.set_system_enabled("gui", True)
        collector.set_point_enabled("gui", "update", False)
        collector.record_duration("gui", "update", 3.0)

        samples = collector.snapshot()
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].elapsed_ms, 1.0)

    def test_span_records_duration_when_enabled(self) -> None:
        collector = TelemetryCollector()
        collector.enable()

        with collector.span("scheduler", "dispatch"):
            pass

        samples = collector.snapshot()
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].system, "scheduler")
        self.assertEqual(samples[0].point, "dispatch")

    def test_file_logging_uses_automatic_naming_in_target_directory(self) -> None:
        collector = TelemetryCollector()
        collector.enable()
        collector.set_file_logging_enabled(True)

        with tempfile.TemporaryDirectory() as temp_dir:
            collector.set_log_directory(temp_dir)
            collector.record_duration("event_bus", "publish", 0.1, metadata={"topic": "demo"})

            files = list(Path(temp_dir).glob("gui_do_telemetry_*_samples.jsonl"))
            self.assertEqual(len(files), 1)
            records = load_telemetry_log_file(files[0])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["system"], "event_bus")
            self.assertEqual(records[0]["point"], "publish")

    def test_live_analysis_report_is_written_on_shutdown(self) -> None:
        collector = TelemetryCollector()
        collector.enable()
        collector.set_live_analysis_enabled(True)

        with tempfile.TemporaryDirectory() as temp_dir:
            collector.set_log_directory(temp_dir)
            collector.record_duration("gui", "draw", 3.0)

            report_path = collector.shutdown()

            self.assertIsNotNone(report_path)
            self.assertTrue(Path(report_path).exists())
            report_text = Path(report_path).read_text(encoding="utf-8")
            self.assertIn("High-Level Hotspots", report_text)
            self.assertIn("gui.draw", report_text)

    def test_analyzer_ranks_hotspots_by_total_time(self) -> None:
        analysis = analyze_telemetry_records(
            [
                {"system": "gui", "point": "draw", "elapsed_ms": 8.0, "metadata": {}},
                {"system": "gui", "point": "draw", "elapsed_ms": 6.0, "metadata": {}},
                {"system": "gui", "point": "update", "elapsed_ms": 2.0, "metadata": {}},
            ],
            top_n=5,
        )

        self.assertEqual(analysis.sample_count, 3)
        self.assertGreaterEqual(len(analysis.hotspots), 2)
        self.assertEqual(analysis.hotspots[0].key, "gui.draw")

    def test_analyzer_collects_feature_hotspots_from_feature_name_metadata(self) -> None:
        analysis = analyze_telemetry_records(
            [
                {
                    "system": "feature_lifecycle",
                    "point": "feature_update",
                    "elapsed_ms": 5.0,
                    "metadata": {"feature_name": "alpha"},
                },
                {
                    "system": "feature_lifecycle",
                    "point": "feature_draw",
                    "elapsed_ms": 2.0,
                    "metadata": {"feature_name": "alpha"},
                },
                {
                    "system": "feature_lifecycle",
                    "point": "feature_update",
                    "elapsed_ms": 1.0,
                    "metadata": {"feature_name": "beta"},
                },
            ],
            top_n=5,
        )

        self.assertEqual(analysis.feature_hotspots[0].key, "alpha")
        self.assertEqual(analysis.feature_hotspots[0].count, 2)
        self.assertEqual(analysis.feature_hotspots[1].key, "beta")

    def test_analyzer_feature_hotspots_support_legacy_part_name_metadata(self) -> None:
        analysis = analyze_telemetry_records(
            [
                {
                    "system": "feature_lifecycle",
                    "point": "feature_update",
                    "elapsed_ms": 3.0,
                    "metadata": {"part_name": "legacy_feature"},
                }
            ]
        )

        self.assertEqual(len(analysis.feature_hotspots), 1)
        self.assertEqual(analysis.feature_hotspots[0].key, "legacy_feature")
        # Backward-compatible alias remains available to older callers.
        self.assertEqual(analysis.part_hotspots, analysis.feature_hotspots)

    def test_report_uses_feature_hotspots_section(self) -> None:
        analysis = analyze_telemetry_records(
            [
                {
                    "system": "feature_lifecycle",
                    "point": "feature_update",
                    "elapsed_ms": 3.0,
                    "metadata": {"feature_name": "alpha"},
                }
            ]
        )

        report = render_telemetry_report(analysis, source="unit-test")
        self.assertIn("Feature Hotspots:", report)
        self.assertNotIn("Part Hotspots:", report)
        self.assertIn("alpha", report)


if __name__ == "__main__":
    unittest.main()
