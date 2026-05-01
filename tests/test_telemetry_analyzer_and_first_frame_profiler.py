"""Tests for TelemetryAnalyzer helpers and FirstFrameProfiler."""
import unittest
from datetime import datetime

from gui_do.telemetry.telemetry_analyzer import (
    TelemetryHotspot, TelemetryAnalysis,
    _percentile, analyze_telemetry_records, render_telemetry_report,
)
from gui_do.app.first_frame_profiler import FirstFrameProfiler, FirstFrameSample
from gui_do.scheduling.task_scheduler import TaskScheduler


# ===========================================================================
# _percentile helper
# ===========================================================================


class TestPercentile(unittest.TestCase):
    def test_empty_returns_zero(self):
        self.assertEqual(0.0, _percentile([], 0.95))

    def test_single_value(self):
        self.assertEqual(5.0, _percentile([5.0], 0.95))

    def test_p50_of_three(self):
        self.assertAlmostEqual(2.0, _percentile([1.0, 2.0, 3.0], 0.5))

    def test_p95_clamped(self):
        values = list(range(1, 21))  # 1..20
        p95 = _percentile(values, 0.95)
        self.assertGreater(p95, 0.0)
        self.assertLessEqual(p95, 20.0)

    def test_fraction_clamped_high(self):
        result = _percentile([1.0, 2.0, 3.0], 2.0)
        self.assertEqual(3.0, result)

    def test_fraction_clamped_low(self):
        result = _percentile([1.0, 2.0, 3.0], -1.0)
        self.assertEqual(1.0, result)


# ===========================================================================
# analyze_telemetry_records
# ===========================================================================


def _raw(system, point, elapsed_ms, metadata=None):
    return {
        "system": system,
        "point": point,
        "elapsed_ms": elapsed_ms,
        "metadata": metadata or {},
    }


class TestAnalyzeTelemetryRecordsEmpty(unittest.TestCase):
    def test_empty_records(self):
        result = analyze_telemetry_records([])
        self.assertEqual(0, result.sample_count)
        self.assertEqual((), result.systems)
        self.assertEqual((), result.hotspots)
        self.assertEqual((), result.feature_hotspots)


class TestAnalyzeTelemetryRecordsBasic(unittest.TestCase):
    def setUp(self):
        self.records = [
            _raw("render", "frame", 16.0),
            _raw("render", "frame", 20.0),
            _raw("input", "poll", 1.0),
        ]
        self.result = analyze_telemetry_records(self.records)

    def test_sample_count(self):
        self.assertEqual(3, self.result.sample_count)

    def test_systems_sorted(self):
        self.assertEqual(("input", "render"), self.result.systems)

    def test_hotspot_count(self):
        # 2 unique keys: render.frame and input.poll
        self.assertEqual(2, len(self.result.hotspots))

    def test_hotspot_ranked_by_total_ms(self):
        # render.frame total=36ms > input.poll total=1ms
        self.assertEqual("render.frame", self.result.hotspots[0].key)

    def test_hotspot_count_field(self):
        top = self.result.hotspots[0]
        self.assertEqual(2, top.count)

    def test_hotspot_total_ms(self):
        top = self.result.hotspots[0]
        self.assertAlmostEqual(36.0, top.total_ms)

    def test_hotspot_average_ms(self):
        top = self.result.hotspots[0]
        self.assertAlmostEqual(18.0, top.average_ms)

    def test_hotspot_max_ms(self):
        top = self.result.hotspots[0]
        self.assertAlmostEqual(20.0, top.max_ms)


class TestAnalyzeTelemetryRecordsFeatureHotspots(unittest.TestCase):
    def test_feature_hotspots_from_metadata(self):
        records = [
            _raw("render", "frame", 10.0, {"feature_name": "bouncing"}),
            _raw("render", "frame", 5.0, {"feature_name": "bouncing"}),
            _raw("render", "draw", 3.0, {"feature_name": "mandelbrot"}),
        ]
        result = analyze_telemetry_records(records)
        feature_keys = {h.key for h in result.feature_hotspots}
        self.assertIn("bouncing", feature_keys)
        self.assertIn("mandelbrot", feature_keys)

    def test_feature_hotspot_aggregated(self):
        records = [
            _raw("render", "frame", 10.0, {"feature_name": "bouncing"}),
            _raw("render", "frame", 20.0, {"feature_name": "bouncing"}),
        ]
        result = analyze_telemetry_records(records)
        feat = result.feature_hotspots[0]
        self.assertEqual("bouncing", feat.key)
        self.assertAlmostEqual(30.0, feat.total_ms)

    def test_no_feature_hotspot_without_metadata(self):
        records = [_raw("render", "frame", 10.0)]
        result = analyze_telemetry_records(records)
        self.assertEqual((), result.feature_hotspots)

    def test_blank_feature_name_ignored(self):
        records = [_raw("render", "frame", 10.0, {"feature_name": "  "})]
        result = analyze_telemetry_records(records)
        self.assertEqual((), result.feature_hotspots)


class TestAnalyzeTelemetryRecordsSkipsInvalid(unittest.TestCase):
    def test_empty_system_skipped(self):
        records = [_raw("", "frame", 10.0), _raw("render", "frame", 5.0)]
        result = analyze_telemetry_records(records)
        self.assertEqual(1, result.sample_count)

    def test_empty_point_skipped(self):
        records = [_raw("render", "", 10.0), _raw("render", "frame", 5.0)]
        result = analyze_telemetry_records(records)
        self.assertEqual(1, result.sample_count)

    def test_top_n_limits_hotspots(self):
        records = [_raw(f"sys{i}", "pt", float(i)) for i in range(1, 20)]
        result = analyze_telemetry_records(records, top_n=5)
        self.assertLessEqual(len(result.hotspots), 5)

    def test_negative_elapsed_clamped_to_zero(self):
        records = [_raw("sys", "pt", -5.0)]
        result = analyze_telemetry_records(records)
        self.assertEqual(0.0, result.hotspots[0].total_ms)


class TestAnalyzeTelemetryRecordsObjectRecords(unittest.TestCase):
    """analyze_telemetry_records accepts dataclass-like objects too."""
    def test_object_with_attributes(self):
        from types import SimpleNamespace
        rec = SimpleNamespace(
            timestamp="2026-01-01T00:00:00",
            system="render", point="frame", elapsed_ms=10.0, metadata={}
        )
        result = analyze_telemetry_records([rec])
        self.assertEqual(1, result.sample_count)
        self.assertEqual("render.frame", result.hotspots[0].key)


# ===========================================================================
# render_telemetry_report
# ===========================================================================


class TestRenderTelemetryReport(unittest.TestCase):
    def _make_analysis(self, n_samples=2):
        records = [_raw("render", "frame", float(i * 10)) for i in range(1, n_samples + 1)]
        return analyze_telemetry_records(records)

    def test_contains_header(self):
        analysis = self._make_analysis()
        report = render_telemetry_report(analysis, source="test")
        self.assertIn("gui_do Telemetry Analysis Report", report)

    def test_contains_sample_count(self):
        analysis = self._make_analysis(3)
        report = render_telemetry_report(analysis, source="test")
        self.assertIn("Sample count: 3", report)

    def test_contains_source(self):
        analysis = self._make_analysis()
        report = render_telemetry_report(analysis, source="my_file.jsonl")
        self.assertIn("my_file.jsonl", report)

    def test_contains_hotspot_key(self):
        analysis = self._make_analysis()
        report = render_telemetry_report(analysis, source="test")
        self.assertIn("render.frame", report)

    def test_generated_at_in_report(self):
        analysis = self._make_analysis()
        ts = datetime(2026, 1, 15, 12, 0, 0)
        report = render_telemetry_report(analysis, source="x", generated_at=ts)
        self.assertIn("2026-01-15", report)

    def test_empty_analysis_no_hotspots_message(self):
        analysis = analyze_telemetry_records([])
        report = render_telemetry_report(analysis, source="x")
        self.assertIn("No telemetry samples", report)

    def test_contains_systems_seen(self):
        analysis = self._make_analysis()
        report = render_telemetry_report(analysis, source="x")
        self.assertIn("render", report)

    def test_report_ends_with_newline(self):
        analysis = self._make_analysis()
        report = render_telemetry_report(analysis, source="x")
        self.assertTrue(report.endswith("\n"))

    def test_guidance_mentions_top_hotspot(self):
        analysis = self._make_analysis(3)
        report = render_telemetry_report(analysis, source="x")
        self.assertIn("render.frame", report)


# ===========================================================================
# FirstFrameProfiler
# ===========================================================================


class TestFirstFrameProfilerBasic(unittest.TestCase):
    def test_disabled_by_default(self):
        p = FirstFrameProfiler()
        self.assertFalse(p.enabled)

    def test_begin_frame_returns_frame_number(self):
        p = FirstFrameProfiler()
        self.assertEqual(1, p.begin_frame("scene1"))
        self.assertEqual(2, p.begin_frame("scene1"))

    def test_scene_frame_count_zero_before_begin(self):
        p = FirstFrameProfiler()
        self.assertEqual(0, p.scene_frame_count("unknown"))

    def test_scene_frame_count_after_begin(self):
        p = FirstFrameProfiler()
        p.begin_frame("scene1")
        p.begin_frame("scene1")
        self.assertEqual(2, p.scene_frame_count("scene1"))

    def test_independent_scenes(self):
        p = FirstFrameProfiler()
        p.begin_frame("a")
        p.begin_frame("a")
        p.begin_frame("b")
        self.assertEqual(2, p.scene_frame_count("a"))
        self.assertEqual(1, p.scene_frame_count("b"))

    def test_profile_first_frame_true_on_frame_1(self):
        p = FirstFrameProfiler()
        p.begin_frame("s")
        self.assertTrue(p.profile_first_frame("s"))

    def test_profile_first_frame_false_on_frame_2(self):
        p = FirstFrameProfiler()
        p.begin_frame("s")
        p.begin_frame("s")
        self.assertFalse(p.profile_first_frame("s"))


class TestFirstFrameProfilerRecordOnce(unittest.TestCase):
    def setUp(self):
        self.p = FirstFrameProfiler(enabled=True, min_ms=0.0)

    def test_record_once_emits_to_logger(self):
        emitted = []
        self.p._logger = lambda msg: emitted.append(msg)
        self.p.record_once("render", "frame", 5.0)
        self.assertEqual(1, len(emitted))
        self.assertIn("render:frame", emitted[0])

    def test_record_once_only_once_per_key(self):
        emitted = []
        self.p._logger = lambda msg: emitted.append(msg)
        self.p.record_once("render", "frame", 5.0)
        self.p.record_once("render", "frame", 10.0)  # same key
        self.assertEqual(1, len(emitted))

    def test_record_once_different_keys_both_emitted(self):
        emitted = []
        self.p._logger = lambda msg: emitted.append(msg)
        self.p.record_once("render", "frame", 5.0)
        self.p.record_once("render", "draw", 5.0)
        self.assertEqual(2, len(emitted))

    def test_record_once_below_min_ms_not_emitted(self):
        emitted = []
        p = FirstFrameProfiler(enabled=True, min_ms=10.0)
        p._logger = lambda msg: emitted.append(msg)
        p.record_once("render", "frame", 5.0)   # 5 < 10
        self.assertEqual(0, len(emitted))

    def test_record_once_disabled_not_emitted(self):
        emitted = []
        p = FirstFrameProfiler(enabled=False)
        p._logger = lambda msg: emitted.append(msg)
        p.record_once("render", "frame", 5.0)
        self.assertEqual(0, len(emitted))

    def test_configure_enabled(self):
        p = FirstFrameProfiler(enabled=False)
        p.configure(enabled=True)
        self.assertTrue(p.enabled)

    def test_configure_min_ms(self):
        p = FirstFrameProfiler(min_ms=0.0)
        p.configure(min_ms=5.0)
        self.assertAlmostEqual(5.0, p.min_ms)

    def test_configure_logger(self):
        p = FirstFrameProfiler(enabled=True)
        msgs = []
        p.configure(logger=lambda m: msgs.append(m))
        p.record_once("cat", "key", 1.0)
        self.assertEqual(1, len(msgs))

    def test_min_ms_negative_clamped_to_zero(self):
        p = FirstFrameProfiler(min_ms=-5.0)
        self.assertEqual(0.0, p.min_ms)

    def test_detail_in_emitted_message(self):
        msgs = []
        self.p._logger = lambda m: msgs.append(m)
        self.p.record_once("cat", "key", 2.0, detail="some info")
        self.assertIn("some info", msgs[0])


# ===========================================================================
# TaskScheduler.recommended_worker_count (static, no threads)
# ===========================================================================


class TestTaskSchedulerRecommendedWorkerCount(unittest.TestCase):
    def test_single_cpu_returns_one(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=1, reserve_for_ui=0, cap=4)
        self.assertEqual(1, count)

    def test_four_cpus_reserve_one(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=4, reserve_for_ui=1, cap=4)
        self.assertEqual(3, count)

    def test_cap_limits_count(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=16, reserve_for_ui=0, cap=4)
        self.assertEqual(4, count)

    def test_result_always_at_least_one(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=1, reserve_for_ui=10, cap=4)
        self.assertGreaterEqual(count, 1)

    def test_none_logical_cpus_uses_os(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=None)
        self.assertGreaterEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
