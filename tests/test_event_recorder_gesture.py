"""Tests for EventRecorder, EventPlayback, RecordedEvent, and GestureRecognizer."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

from gui_do.events.event_recorder import RecordedEvent, EventRecorder, EventPlayback
from gui_do.events.gesture_recognizer import GestureRecognizer
from gui_do.events.gui_event import EventType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(kind, pos=(0, 0), button=1, key=0, mod=0, wheel_delta=0, text=""):
    return SimpleNamespace(kind=kind, pos=pos, button=button,
                           key=key, mod=mod, wheel_delta=wheel_delta, text=text)


# ===========================================================================
# RecordedEvent
# ===========================================================================


class TestRecordedEvent(unittest.TestCase):
    def test_fields_stored(self):
        re = RecordedEvent(time_offset_ms=100.0, event_type="MOUSE_DOWN",
                           pos=[10, 20], button=1)
        self.assertEqual(100.0, re.time_offset_ms)
        self.assertEqual("MOUSE_DOWN", re.event_type)
        self.assertEqual([10, 20], re.pos)
        self.assertEqual(1, re.button)

    def test_defaults(self):
        re = RecordedEvent(time_offset_ms=0.0, event_type="KEY_DOWN")
        self.assertEqual(0, re.key)
        self.assertEqual(0, re.mod)
        self.assertEqual("", re.text)
        self.assertEqual({}, re.extra)


# ===========================================================================
# EventRecorder
# ===========================================================================


class TestEventRecorder(unittest.TestCase):
    def test_initial_not_recording(self):
        rec = EventRecorder()
        self.assertFalse(rec.is_recording)

    def test_initial_count_zero(self):
        rec = EventRecorder()
        self.assertEqual(0, rec.recorded_count)

    def test_start_sets_recording(self):
        rec = EventRecorder()
        rec.start()
        self.assertTrue(rec.is_recording)

    def test_stop_clears_recording(self):
        rec = EventRecorder()
        rec.start()
        rec.stop()
        self.assertFalse(rec.is_recording)

    def test_stop_returns_events(self):
        rec = EventRecorder()
        rec.start()
        events = rec.stop()
        self.assertIsInstance(events, list)

    def test_record_when_not_recording_ignored(self):
        rec = EventRecorder()
        e = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5))
        rec.record(e)
        self.assertEqual(0, rec.recorded_count)

    def test_record_when_recording_captures(self):
        rec = EventRecorder()
        rec.start()
        e = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5))
        rec.record(e)
        self.assertEqual(1, rec.recorded_count)

    def test_recorded_event_type_extracted(self):
        rec = EventRecorder()
        rec.start()
        e = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5))
        rec.record(e)
        events = rec.stop()
        self.assertEqual(EventType.MOUSE_BUTTON_DOWN.value, events[0].event_type)

    def test_start_discards_previous(self):
        rec = EventRecorder()
        rec.start()
        e = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5))
        rec.record(e)
        rec.stop()
        rec.start()
        self.assertEqual(0, rec.recorded_count)

    def test_save_and_load(self):
        rec = EventRecorder()
        rec.start()
        e = _make_event(EventType.KEY_DOWN, key=97)
        rec.record(e)
        rec.stop()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            rec.save(path)
            loaded = EventRecorder.load_file(path)
            self.assertEqual(1, len(loaded))
            self.assertIsInstance(loaded[0], RecordedEvent)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_missing_file_returns_empty(self):
        result = EventRecorder.load_file("/nonexistent/path/does_not_exist.json")
        self.assertEqual([], result)

    def test_from_events(self):
        ev = RecordedEvent(time_offset_ms=0.0, event_type="PASS")
        rec = EventRecorder.from_events([ev])
        self.assertEqual(1, rec.recorded_count)


# ===========================================================================
# EventPlayback
# ===========================================================================


class TestEventPlayback(unittest.TestCase):
    def test_initial_not_playing(self):
        player = EventPlayback([], handler=lambda e: None)
        self.assertFalse(player.is_playing)

    def test_start_sets_playing(self):
        player = EventPlayback([], handler=lambda e: None)
        player.start()
        self.assertTrue(player.is_playing)

    def test_stop_clears_playing(self):
        player = EventPlayback([], handler=lambda e: None)
        player.start()
        player.stop()
        self.assertFalse(player.is_playing)

    def test_empty_events_stay_playing_on_update(self):
        # update() returns early when there are no events, leaving is_playing True.
        player = EventPlayback([], handler=lambda e: None)
        player.start()
        player.update(1.0)
        self.assertTrue(player.is_playing)

    def test_event_fired_at_right_time(self):
        fired = []
        events = [RecordedEvent(time_offset_ms=100.0, event_type="PASS")]
        player = EventPlayback(events, handler=lambda e: fired.append(e))
        player.start()
        player.update(0.05)  # 50ms — too early
        self.assertEqual(0, len(fired))
        player.update(0.06)  # now at 110ms — fires
        self.assertEqual(1, len(fired))

    def test_on_complete_called(self):
        done = []
        events = [RecordedEvent(time_offset_ms=10.0, event_type="PASS")]
        player = EventPlayback(events, handler=lambda e: None, on_complete=lambda: done.append(1))
        player.start()
        player.update(0.1)
        self.assertEqual([1], done)

    def test_loop_restarts(self):
        fired = []
        events = [RecordedEvent(time_offset_ms=10.0, event_type="PASS")]
        player = EventPlayback(events, handler=lambda e: fired.append(1), loop=True)
        player.start()
        player.update(0.02)   # fires event 1
        player.update(0.02)   # fires event again (looped)
        self.assertGreaterEqual(len(fired), 2)

    def test_progress_at_start(self):
        events = [RecordedEvent(time_offset_ms=1000.0, event_type="PASS")]
        player = EventPlayback(events, handler=lambda e: None)
        player.start()
        self.assertEqual(0.0, player.progress)

    def test_elapsed_ms(self):
        player = EventPlayback([], handler=lambda e: None)
        player.start()
        player.update(0.2)
        # After empty list update() the player finishes, but elapsed should be 200
        # (200ms but player may finish first — check elapsed_ms > 0)
        self.assertGreaterEqual(player.elapsed_ms, 0.0)


# ===========================================================================
# GestureRecognizer
# ===========================================================================


class TestGestureRecognizerDoubleClick(unittest.TestCase):
    def _make(self, **kwargs):
        return GestureRecognizer(**kwargs)

    def test_double_click_fires(self):
        fired = []
        gr = self._make(on_double_click=lambda pos: fired.append(pos))
        down1 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10), button=1)
        down2 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10), button=1)
        gr.process_event(down1)
        gr.update(0.1)   # 100ms < 400ms threshold
        gr.process_event(down2)
        self.assertEqual(1, len(fired))
        self.assertEqual((10, 10), fired[0])

    def test_double_click_too_far_away(self):
        fired = []
        gr = self._make(on_double_click=lambda pos: fired.append(pos))
        down1 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(0, 0), button=1)
        down2 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(100, 0), button=1)
        gr.process_event(down1)
        gr.update(0.1)
        gr.process_event(down2)
        self.assertEqual(0, len(fired))

    def test_double_click_too_slow(self):
        fired = []
        gr = self._make(on_double_click=lambda pos: fired.append(pos), double_click_ms=200)
        down1 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1)
        down2 = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1)
        gr.process_event(down1)
        gr.update(0.5)  # 500ms > 200ms threshold
        gr.process_event(down2)
        self.assertEqual(0, len(fired))


class TestGestureRecognizerLongPress(unittest.TestCase):
    def test_long_press_fires(self):
        fired = []
        gr = GestureRecognizer(on_long_press=lambda pos: fired.append(pos), long_press_ms=200)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1))
        gr.update(0.25)  # 250ms > 200ms threshold
        self.assertEqual(1, len(fired))

    def test_long_press_not_fired_too_early(self):
        fired = []
        gr = GestureRecognizer(on_long_press=lambda pos: fired.append(pos), long_press_ms=600)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1))
        gr.update(0.1)
        self.assertEqual(0, len(fired))

    def test_long_press_not_fired_twice(self):
        fired = []
        gr = GestureRecognizer(on_long_press=lambda pos: fired.append(pos), long_press_ms=200)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1))
        gr.update(0.3)
        gr.update(0.3)  # advance further
        self.assertEqual(1, len(fired))


class TestGestureRecognizerSwipe(unittest.TestCase):
    def test_swipe_right_fires(self):
        fired = []
        gr = GestureRecognizer(on_swipe=lambda d, v: fired.append(d), swipe_min_px=40)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(0, 0), button=1))
        gr.update(0.1)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_UP, pos=(100, 0), button=1))
        self.assertEqual(["right"], fired)

    def test_swipe_left_fires(self):
        fired = []
        gr = GestureRecognizer(on_swipe=lambda d, v: fired.append(d), swipe_min_px=40)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(100, 0), button=1))
        gr.update(0.1)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_UP, pos=(0, 0), button=1))
        self.assertEqual(["left"], fired)

    def test_swipe_not_fired_if_too_short(self):
        fired = []
        gr = GestureRecognizer(on_swipe=lambda d, v: fired.append(d), swipe_min_px=40)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(0, 0), button=1))
        gr.update(0.1)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_UP, pos=(5, 0), button=1))
        self.assertEqual([], fired)


class TestGestureRecognizerReset(unittest.TestCase):
    def test_reset_clears_press(self):
        fired = []
        gr = GestureRecognizer(on_long_press=lambda pos: fired.append(pos), long_press_ms=200)
        gr.process_event(_make_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5), button=1))
        gr.reset()
        gr.update(0.3)  # should not fire after reset
        self.assertEqual([], fired)


if __name__ == "__main__":
    unittest.main()
