"""Tests for telemetry_analyzer — TelemetryHotspot, TelemetryAnalysis, analyze_telemetry_records."""
import unittest

from gui_do.telemetry.telemetry_analyzer import (
    TelemetryHotspot,
    TelemetryAnalysis,
    analyze_telemetry_records,
)


# ===========================================================================
# TelemetryHotspot dataclass
# ===========================================================================


class TestTelemetryHotspot(unittest.TestCase):
    def test_fields_stored(self):
        h = TelemetryHotspot(
            key="render.draw",
            count=10,
            total_ms=100.0,
            average_ms=10.0,
            max_ms=25.0,
            p95_ms=22.5,
        )
        self.assertEqual("render.draw", h.key)
        self.assertEqual(10, h.count)
        self.assertEqual(100.0, h.total_ms)
        self.assertEqual(10.0, h.average_ms)
        self.assertEqual(25.0, h.max_ms)
        self.assertEqual(22.5, h.p95_ms)

    def test_is_frozen(self):
        h = TelemetryHotspot(key="k", count=1, total_ms=1.0, average_ms=1.0, max_ms=1.0, p95_ms=1.0)
        with self.assertRaises(Exception):
            h.key = "new"  # type: ignore[misc]


# ===========================================================================
# TelemetryAnalysis dataclass
# ===========================================================================


class TestTelemetryAnalysis(unittest.TestCase):
    def test_fields_stored(self):
        h = TelemetryHotspot(key="k", count=1, total_ms=5.0, average_ms=5.0, max_ms=5.0, p95_ms=5.0)
        a = TelemetryAnalysis(
            sample_count=1,
            systems=("render",),
            hotspots=(h,),
            feature_hotspots=(),
        )
        self.assertEqual(1, a.sample_count)
        self.assertEqual(("render",), a.systems)
        self.assertEqual(1, len(a.hotspots))

    def test_is_frozen(self):
        a = TelemetryAnalysis(sample_count=0, systems=(), hotspots=(), feature_hotspots=())
        with self.assertRaises(Exception):
            a.sample_count = 5  # type: ignore[misc]


# ===========================================================================
# analyze_telemetry_records
# ===========================================================================


class TestAnalyzeTelemetryRecords(unittest.TestCase):
    def _make_record(self, system, point, elapsed_ms, feature_name=None):
        meta = {"feature_name": feature_name} if feature_name else {}
        return {
            "timestamp": 0,
            "system": system,
            "point": point,
            "elapsed_ms": elapsed_ms,
            "metadata": meta,
        }

    def test_empty_records(self):
        result = analyze_telemetry_records([])
        self.assertEqual(0, result.sample_count)
        self.assertEqual((), result.systems)
        self.assertEqual((), result.hotspots)

    def test_single_record(self):
        rec = self._make_record("render", "draw", 5.0)
        result = analyze_telemetry_records([rec])
        self.assertEqual(1, result.sample_count)
        self.assertIn("render", result.systems)

    def test_hotspot_key_format(self):
        rec = self._make_record("render", "draw", 5.0)
        result = analyze_telemetry_records([rec])
        self.assertEqual("render.draw", result.hotspots[0].key)

    def test_hotspot_count(self):
        records = [self._make_record("r", "p", 5.0) for _ in range(3)]
        result = analyze_telemetry_records(records)
        self.assertEqual(3, result.hotspots[0].count)

    def test_hotspot_average_ms(self):
        records = [self._make_record("r", "p", v) for v in [10.0, 20.0, 30.0]]
        result = analyze_telemetry_records(records)
        self.assertAlmostEqual(20.0, result.hotspots[0].average_ms)

    def test_feature_hotspot_extracted(self):
        rec = self._make_record("r", "p", 10.0, feature_name="MyFeature")
        result = analyze_telemetry_records([rec])
        self.assertEqual(1, len(result.feature_hotspots))
        self.assertEqual("MyFeature", result.feature_hotspots[0].key)

    def test_records_missing_system_skipped(self):
        rec = {"system": "", "point": "p", "elapsed_ms": 5.0, "metadata": {}}
        result = analyze_telemetry_records([rec])
        self.assertEqual(0, result.sample_count)

    def test_multiple_systems_sorted(self):
        records = [
            self._make_record("render", "draw", 1.0),
            self._make_record("input", "poll", 1.0),
        ]
        result = analyze_telemetry_records(records)
        self.assertEqual(("input", "render"), result.systems)

    def test_top_n_limits_hotspots(self):
        records = []
        for i in range(20):
            records.append(self._make_record("sys", f"point{i}", float(i + 1)))
        result = analyze_telemetry_records(records, top_n=5)
        self.assertLessEqual(len(result.hotspots), 5)

    def test_hotspot_sorted_by_total_ms(self):
        records = [
            self._make_record("s", "fast", 1.0),
            self._make_record("s", "fast", 1.0),
            self._make_record("s", "slow", 100.0),
        ]
        result = analyze_telemetry_records(records)
        self.assertEqual("s.slow", result.hotspots[0].key)


if __name__ == "__main__":
    unittest.main()
