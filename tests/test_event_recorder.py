"""Tests for EventRecorder, RecordedEvent, EventPlayback, and InputState."""
import unittest

from gui_do.events.event_recorder import EventRecorder, RecordedEvent
from gui_do.events.input_state import InputState


# ===========================================================================
# RecordedEvent
# ===========================================================================


class TestRecordedEvent(unittest.TestCase):
    def test_fields_stored(self):
        e = RecordedEvent(time_offset_ms=123.4, event_type="MOUSE_DOWN")
        self.assertEqual(123.4, e.time_offset_ms)
        self.assertEqual("MOUSE_DOWN", e.event_type)

    def test_defaults(self):
        e = RecordedEvent(time_offset_ms=0.0, event_type="UNKNOWN")
        self.assertEqual([0, 0], e.pos)
        self.assertEqual(0, e.key)
        self.assertEqual(0, e.mod)
        self.assertEqual(0, e.button)
        self.assertEqual(0, e.wheel_delta)
        self.assertEqual("", e.text)
        self.assertEqual({}, e.extra)

    def test_custom_pos(self):
        e = RecordedEvent(time_offset_ms=0.0, event_type="MOUSE_MOVE", pos=[100, 200])
        self.assertEqual([100, 200], e.pos)


# ===========================================================================
# EventRecorder — initial state
# ===========================================================================


class TestEventRecorderInitial(unittest.TestCase):
    def test_not_recording_initially(self):
        r = EventRecorder()
        self.assertFalse(r.is_recording)

    def test_recorded_count_zero(self):
        r = EventRecorder()
        self.assertEqual(0, r.recorded_count)


# ===========================================================================
# EventRecorder — start / stop
# ===========================================================================


class TestEventRecorderStartStop(unittest.TestCase):
    def test_start_sets_recording(self):
        r = EventRecorder()
        r.start()
        self.assertTrue(r.is_recording)

    def test_stop_clears_recording(self):
        r = EventRecorder()
        r.start()
        r.stop()
        self.assertFalse(r.is_recording)

    def test_stop_returns_events(self):
        r = EventRecorder()
        r.start()

        class FakeEvent:
            kind = None
            pos = [50, 60]
            key = 0
            mod = 0
            button = 1
            wheel_delta = 0
            text = ""

        r.record(FakeEvent())
        events = r.stop()
        self.assertEqual(1, len(events))

    def test_start_discards_previous(self):
        r = EventRecorder()
        r.start()

        class FakeEvent:
            kind = None
            pos = [0, 0]
            key = 0
            mod = 0
            button = 0
            wheel_delta = 0
            text = ""

        r.record(FakeEvent())
        r.stop()
        r.start()  # should discard old recording
        self.assertEqual(0, r.recorded_count)


# ===========================================================================
# EventRecorder — record
# ===========================================================================


class TestEventRecorderRecord(unittest.TestCase):
    def _make_event(self, *, pos=(0, 0), button=0, key=0, text=""):
        class Ev:
            kind = None
            mod = 0
            wheel_delta = 0
        e = Ev()
        e.pos = list(pos)
        e.button = button
        e.key = key
        e.text = text
        return e

    def test_record_while_not_recording_is_noop(self):
        r = EventRecorder()
        r.record(self._make_event())
        self.assertEqual(0, r.recorded_count)

    def test_record_increments_count(self):
        r = EventRecorder()
        r.start()
        r.record(self._make_event())
        r.record(self._make_event())
        self.assertEqual(2, r.recorded_count)

    def test_record_captures_pos(self):
        r = EventRecorder()
        r.start()
        r.record(self._make_event(pos=(100, 200)))
        events = r.stop()
        self.assertEqual([100, 200], events[0].pos)

    def test_record_captures_button(self):
        r = EventRecorder()
        r.start()
        r.record(self._make_event(button=3))
        events = r.stop()
        self.assertEqual(3, events[0].button)

    def test_record_captures_text(self):
        r = EventRecorder()
        r.start()
        r.record(self._make_event(text="A"))
        events = r.stop()
        self.assertEqual("A", events[0].text)

    def test_time_offset_positive(self):
        r = EventRecorder()
        r.start()
        r.record(self._make_event())
        events = r.stop()
        self.assertGreaterEqual(events[0].time_offset_ms, 0.0)


# ===========================================================================
# EventRecorder — save / load_file
# ===========================================================================


class TestEventRecorderPersistence(unittest.TestCase):
    def test_save_and_load(self, tmp_path=None):
        import tempfile, os
        r = EventRecorder()
        r.start()

        class FakeEvent:
            kind = None
            pos = [10, 20]
            key = 0
            mod = 0
            button = 1
            wheel_delta = 0
            text = ""

        r.record(FakeEvent())
        r.stop()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            r.save(path)
            loaded = EventRecorder.load_file(path)
        finally:
            os.unlink(path)

        self.assertEqual(1, len(loaded))
        self.assertEqual(1, loaded[0].button)
        self.assertEqual([10, 20], loaded[0].pos)


# ===========================================================================
# InputState
# ===========================================================================


class TestInputState(unittest.TestCase):
    def test_initial_pointer_pos(self):
        s = InputState()
        self.assertEqual((0, 0), s.pointer_pos)

    def test_update_from_event(self):
        s = InputState()

        class Ev:
            pos = (150, 250)

        s.update_from_event(Ev())
        self.assertEqual((150, 250), s.pointer_pos)

    def test_update_ignores_invalid_pos(self):
        s = InputState()

        class Ev:
            pos = "not_a_tuple"

        s.update_from_event(Ev())
        self.assertEqual((0, 0), s.pointer_pos)


if __name__ == "__main__":
    unittest.main()
