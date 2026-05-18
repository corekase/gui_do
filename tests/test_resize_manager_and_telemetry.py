"""Tests for ResizeManager and TelemetryCollector."""
import unittest
from pathlib import Path
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.overlays.resize_manager import ResizeManager, WINDOW_RESIZED_TOPIC
from gui_do.layout.constraint_layout import AnchorConstraint, ConstraintLayout
from gui_do.telemetry.telemetry import TelemetryCollector, TelemetrySample

pygame.init()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(w: int, h: int, x: int = 0, y: int = 0) -> SimpleNamespace:
    n = SimpleNamespace(rect=Rect(x, y, w, h))
    n.invalidate = lambda: None
    return n


class _StubEventBus:
    """Captures publish() calls."""
    def __init__(self):
        self.calls = []

    def publish(self, topic, payload):
        self.calls.append((topic, payload))


# ===========================================================================
# ResizeManager
# ===========================================================================


class TestResizeManagerInitial(unittest.TestCase):
    def test_default_size(self):
        mgr = ResizeManager(initial_size=(800, 600))
        self.assertEqual((800, 600), mgr.size)

    def test_width_height_properties(self):
        mgr = ResizeManager(initial_size=(1024, 768))
        self.assertEqual(1024, mgr.width)
        self.assertEqual(768, mgr.height)

    def test_resize_count_zero(self):
        mgr = ResizeManager()
        self.assertEqual(0, mgr.resize_count)

    def test_small_size_clamped_to_one(self):
        mgr = ResizeManager(initial_size=(0, -5))
        self.assertEqual((1, 1), mgr.size)


class TestResizeManagerNotify(unittest.TestCase):
    def test_notify_resize_updates_size(self):
        mgr = ResizeManager(initial_size=(800, 600))
        mgr.notify_resize(1280, 720)
        self.assertEqual((1280, 720), mgr.size)

    def test_notify_resize_increments_count(self):
        mgr = ResizeManager()
        mgr.notify_resize(800, 600)
        mgr.notify_resize(1024, 768)
        self.assertEqual(2, mgr.resize_count)

    def test_notify_resize_zero_clamped_to_one(self):
        mgr = ResizeManager()
        mgr.notify_resize(0, 0)
        self.assertEqual((1, 1), mgr.size)

    def test_notify_fires_callbacks(self):
        mgr = ResizeManager()
        received = []
        mgr.on_resize(lambda w, h: received.append((w, h)))
        mgr.notify_resize(1280, 720)
        self.assertEqual([(1280, 720)], received)

    def test_notify_multiple_callbacks(self):
        mgr = ResizeManager()
        a, b = [], []
        mgr.on_resize(lambda w, h: a.append((w, h)))
        mgr.on_resize(lambda w, h: b.append((w, h)))
        mgr.notify_resize(640, 480)
        self.assertEqual([(640, 480)], a)
        self.assertEqual([(640, 480)], b)

    def test_notify_publishes_to_event_bus(self):
        bus = _StubEventBus()
        mgr = ResizeManager(event_bus=bus)
        mgr.notify_resize(1280, 720)
        self.assertEqual(1, len(bus.calls))
        topic, payload = bus.calls[0]
        self.assertEqual(WINDOW_RESIZED_TOPIC, topic)
        self.assertEqual((1280, 720), payload)

    def test_no_event_bus_no_error(self):
        mgr = ResizeManager()
        mgr.notify_resize(800, 600)   # should not raise


class TestResizeManagerLayouts(unittest.TestCase):
    def _make_layout(self, parent_size=(800, 600)):
        layout = ConstraintLayout()
        n = _node(0, 0)
        layout.add(n, AnchorConstraint(left=0, right=0))
        mgr = ResizeManager(initial_size=parent_size)
        return mgr, layout, n

    def test_register_applies_immediately(self):
        mgr, layout, n = self._make_layout((800, 600))
        mgr.register_layout(layout)
        self.assertEqual(800, n.rect.width)

    def test_register_no_duplicate(self):
        mgr, layout, n = self._make_layout()
        mgr.register_layout(layout)
        mgr.register_layout(layout)   # second register should be idempotent
        # Width should still be 800, no error
        self.assertEqual(800, n.rect.width)

    def test_notify_reflows_layout(self):
        mgr, layout, n = self._make_layout((800, 600))
        mgr.register_layout(layout)
        mgr.notify_resize(1280, 720)
        self.assertEqual(1280, n.rect.width)

    def test_unregister_stops_reflow(self):
        mgr, layout, n = self._make_layout((800, 600))
        mgr.register_layout(layout)
        mgr.unregister_layout(layout)
        mgr.notify_resize(1280, 720)
        self.assertEqual(800, n.rect.width)   # not updated

    def test_unregister_missing_returns_false(self):
        mgr = ResizeManager()
        layout = ConstraintLayout()
        self.assertFalse(mgr.unregister_layout(layout))

    def test_unregister_registered_returns_true(self):
        mgr, layout, _ = self._make_layout()
        mgr.register_layout(layout)
        self.assertTrue(mgr.unregister_layout(layout))


class TestResizeManagerCallbackUnsub(unittest.TestCase):
    def test_on_resize_non_callable_raises(self):
        mgr = ResizeManager()
        with self.assertRaises(ValueError):
            mgr.on_resize("not_a_callable")

    def test_unsub_stops_callback(self):
        mgr = ResizeManager()
        received = []
        unsub = mgr.on_resize(lambda w, h: received.append((w, h)))
        mgr.notify_resize(800, 600)
        unsub()
        mgr.notify_resize(1280, 720)
        self.assertEqual(1, len(received))   # only first resize


class TestResizeManagerPygameEvent(unittest.TestCase):
    def test_videoresize_event_handled(self):
        mgr = ResizeManager(initial_size=(800, 600))
        event = pygame.event.Event(pygame.VIDEORESIZE, w=1280, h=720)
        result = mgr.handle_pygame_event(event)
        self.assertTrue(result)
        self.assertEqual((1280, 720), mgr.size)

    def test_non_videoresize_event_not_handled(self):
        mgr = ResizeManager()
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0, unicode="a", scancode=4)
        result = mgr.handle_pygame_event(event)
        self.assertFalse(result)


# ===========================================================================
# TelemetryCollector
# ===========================================================================


class TestTelemetryCollectorInitial(unittest.TestCase):
    def test_disabled_initially(self):
        tc = TelemetryCollector()
        self.assertFalse(tc.enabled())

    def test_snapshot_empty_initially(self):
        tc = TelemetryCollector()
        self.assertEqual([], tc.snapshot())

    def test_should_record_false_when_disabled(self):
        tc = TelemetryCollector()
        self.assertFalse(tc.should_record("sys", "point"))

    def test_default_log_directory_uses_current_working_directory(self):
        tc = TelemetryCollector()
        self.assertEqual(Path.cwd(), tc._log_directory)


class TestTelemetryCollectorEnableDisable(unittest.TestCase):
    def test_enable(self):
        tc = TelemetryCollector()
        tc.enable()
        self.assertTrue(tc.enabled())

    def test_disable(self):
        tc = TelemetryCollector()
        tc.enable()
        tc.disable()
        self.assertFalse(tc.enabled())

    def test_should_record_true_when_enabled(self):
        tc = TelemetryCollector()
        tc.enable()
        self.assertTrue(tc.should_record("sys", "point"))


class TestTelemetryCollectorRecordDuration(unittest.TestCase):
    def setUp(self):
        self.tc = TelemetryCollector()
        self.tc.enable()

    def test_record_duration_adds_sample(self):
        self.tc.record_duration("render", "frame", 16.0)
        self.assertEqual(1, len(self.tc.snapshot()))

    def test_sample_fields(self):
        self.tc.record_duration("render", "frame", 12.5, metadata={"scene": "main"})
        sample = self.tc.snapshot()[0]
        self.assertIsInstance(sample, TelemetrySample)
        self.assertEqual("render", sample.system)
        self.assertEqual("frame", sample.point)
        self.assertAlmostEqual(12.5, sample.elapsed_ms)
        self.assertEqual({"scene": "main"}, sample.metadata)

    def test_record_when_disabled_no_sample(self):
        self.tc.disable()
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(0, len(self.tc.snapshot()))

    def test_system_names_normalised_to_lower(self):
        self.tc.record_duration("RENDER", "FRAME", 5.0)
        sample = self.tc.snapshot()[0]
        self.assertEqual("render", sample.system)
        self.assertEqual("frame", sample.point)

    def test_negative_elapsed_clamped_to_zero(self):
        self.tc.record_duration("sys", "pt", -100.0)
        sample = self.tc.snapshot()[0]
        self.assertEqual(0.0, sample.elapsed_ms)

    def test_empty_system_raises(self):
        with self.assertRaises(ValueError):
            self.tc.record_duration("", "point", 1.0)

    def test_empty_point_raises(self):
        with self.assertRaises(ValueError):
            self.tc.record_duration("sys", "", 1.0)


class TestTelemetryCollectorFilters(unittest.TestCase):
    def setUp(self):
        self.tc = TelemetryCollector()
        self.tc.enable()

    def test_min_duration_filters_fast_samples(self):
        self.tc.set_min_duration_ms(10.0)
        self.tc.record_duration("sys", "pt", 5.0)   # too fast
        self.assertEqual(0, len(self.tc.snapshot()))

    def test_min_duration_passes_slow_samples(self):
        self.tc.set_min_duration_ms(10.0)
        self.tc.record_duration("sys", "pt", 15.0)
        self.assertEqual(1, len(self.tc.snapshot()))

    def test_min_duration_negative_raises(self):
        with self.assertRaises(ValueError):
            self.tc.set_min_duration_ms(-1.0)

    def test_set_system_disabled_filters(self):
        self.tc.set_system_enabled("render", False)
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(0, len(self.tc.snapshot()))

    def test_set_system_enabled_passes(self):
        self.tc.set_system_enabled("render", True)
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(1, len(self.tc.snapshot()))

    def test_set_point_disabled_filters(self):
        self.tc.set_point_enabled("render", "frame", False)
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(0, len(self.tc.snapshot()))

    def test_point_disabled_overrides_system_enabled(self):
        # system is enabled (default), but a specific point is explicitly disabled
        self.tc.set_point_enabled("render", "frame", False)
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(0, len(self.tc.snapshot()))

    def test_point_enabled_passes_when_system_not_overridden(self):
        # explicitly enable a point; system has no override → should record
        self.tc.set_point_enabled("render", "frame", True)
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(1, len(self.tc.snapshot()))

    def test_clear_filters(self):
        self.tc.set_system_enabled("render", False)
        self.tc.clear_filters()
        self.tc.record_duration("render", "frame", 10.0)
        self.assertEqual(1, len(self.tc.snapshot()))

    def test_set_system_empty_name_raises(self):
        with self.assertRaises(ValueError):
            self.tc.set_system_enabled("", True)


class TestTelemetryCollectorSpan(unittest.TestCase):
    def test_span_disabled_returns_null_span(self):
        tc = TelemetryCollector()
        span = tc.span("sys", "pt")
        # null span — context manager works, no sample recorded
        with span:
            pass
        self.assertEqual(0, len(tc.snapshot()))

    def test_span_enabled_records_sample(self):
        tc = TelemetryCollector()
        tc.enable()
        with tc.span("sys", "pt"):
            pass
        self.assertEqual(1, len(tc.snapshot()))

    def test_span_sample_fields(self):
        tc = TelemetryCollector()
        tc.enable()
        with tc.span("render", "draw", {"tag": "x"}):
            pass
        sample = tc.snapshot()[0]
        self.assertEqual("render", sample.system)
        self.assertEqual("draw", sample.point)

    def test_span_records_on_exception(self):
        tc = TelemetryCollector()
        tc.enable()
        try:
            with tc.span("sys", "pt"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        sample = tc.snapshot()[0]
        self.assertIn("exception", sample.metadata)


class TestTelemetryCollectorReset(unittest.TestCase):
    def test_reset_clears_samples(self):
        tc = TelemetryCollector()
        tc.enable()
        tc.record_duration("sys", "pt", 5.0)
        tc.reset()
        self.assertEqual([], tc.snapshot())


class TestTelemetryCollectorLiveAnalysis(unittest.TestCase):
    def test_live_analysis_enabled_default_false(self):
        tc = TelemetryCollector()
        self.assertFalse(tc.live_analysis_enabled())

    def test_set_live_analysis(self):
        tc = TelemetryCollector()
        tc.set_live_analysis_enabled(True)
        self.assertTrue(tc.live_analysis_enabled())


if __name__ == "__main__":
    unittest.main()
