"""Tests for SceneTimeline — pure-logic frame-driven choreography timeline."""
import unittest

from gui_do.scheduling.scene_timeline import SceneTimeline


# ===========================================================================
# Initial state
# ===========================================================================


class TestSceneTimelineInitial(unittest.TestCase):
    def test_not_playing(self):
        tl = SceneTimeline()
        self.assertFalse(tl.is_playing)

    def test_current_time_zero(self):
        tl = SceneTimeline()
        self.assertEqual(0.0, tl.current_time)

    def test_no_events(self):
        tl = SceneTimeline()
        # Should not raise on update without play
        tl.update(0.1)

    def test_explicit_duration(self):
        tl = SceneTimeline(duration=5.0)
        self.assertEqual(5.0, tl.duration)


# ===========================================================================
# play / pause / reset
# ===========================================================================


class TestSceneTimelinePlayback(unittest.TestCase):
    def test_play_sets_playing(self):
        tl = SceneTimeline()
        tl.play()
        self.assertTrue(tl.is_playing)

    def test_pause_stops_playing(self):
        tl = SceneTimeline()
        tl.play()
        tl.pause()
        self.assertFalse(tl.is_playing)

    def test_update_advances_time(self):
        tl = SceneTimeline()
        tl.play()
        tl.update(0.5)
        self.assertAlmostEqual(0.5, tl.current_time)

    def test_update_while_paused_does_nothing(self):
        tl = SceneTimeline()
        tl.update(1.0)
        self.assertEqual(0.0, tl.current_time)

    def test_reset_clears_time_and_state(self):
        tl = SceneTimeline()
        tl.play()
        tl.update(2.0)
        tl.reset()
        self.assertEqual(0.0, tl.current_time)
        self.assertFalse(tl.is_playing)


# ===========================================================================
# Event firing — at()
# ===========================================================================


class TestSceneTimelineAt(unittest.TestCase):
    def test_fires_at_time(self):
        calls = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: calls.append("fired"))
        tl.play()
        tl.update(1.0)
        self.assertEqual(["fired"], calls)

    def test_not_fired_before_time(self):
        calls = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: calls.append("fired"))
        tl.play()
        tl.update(0.5)
        self.assertEqual([], calls)

    def test_fires_only_once(self):
        calls = []
        tl = SceneTimeline()
        tl.at(0.5, lambda: calls.append("x"))
        tl.play()
        tl.update(0.5)
        tl.update(0.5)
        self.assertEqual(1, len(calls))

    def test_multiple_events_ordered(self):
        order = []
        tl = SceneTimeline()
        tl.at(0.5, lambda: order.append("a"))
        tl.at(0.3, lambda: order.append("b"))
        tl.play()
        tl.update(1.0)
        self.assertEqual(["b", "a"], order)


# ===========================================================================
# Labels and seek
# ===========================================================================


class TestSceneTimelineLabels(unittest.TestCase):
    def test_seek_jumps_to_time(self):
        tl = SceneTimeline()
        tl.play()
        tl.seek(3.0)
        self.assertAlmostEqual(3.0, tl.current_time)

    def test_label_and_seek_to_label(self):
        tl = SceneTimeline()
        tl.label("mid", t=2.0)
        tl.play()
        tl.seek_to_label("mid")
        self.assertAlmostEqual(2.0, tl.current_time)

    def test_seek_fires_events_in_range(self):
        calls = []
        tl = SceneTimeline()
        tl.at(1.5, lambda: calls.append("ev"))
        tl.play()
        tl.seek(2.0)
        self.assertEqual(["ev"], calls)


# ===========================================================================
# Loop
# ===========================================================================


class TestSceneTimelineLoop(unittest.TestCase):
    def test_loop_fires_repeatedly(self):
        calls = []
        tl = SceneTimeline()
        tl.loop_every(0.5, lambda: calls.append(1))
        tl.play()
        tl.update(1.5)
        self.assertGreaterEqual(len(calls), 2)


# ===========================================================================
# on_complete
# ===========================================================================


class TestSceneTimelineComplete(unittest.TestCase):
    def test_complete_fires_at_end(self):
        done = []
        tl = SceneTimeline(duration=1.0)
        tl.on_complete(lambda: done.append(True))
        tl.play()
        tl.update(1.5)
        self.assertEqual([True], done)


# ===========================================================================
# between()
# ===========================================================================


class TestSceneTimelineBetween(unittest.TestCase):
    def test_on_enter_fires_when_entering_region(self):
        entered = []
        tl = SceneTimeline()
        tl.between(1.0, 2.0, on_enter=lambda: entered.append(True))
        tl.play()
        tl.update(1.5)
        self.assertEqual([True], entered)

    def test_on_exit_fires_when_leaving_region(self):
        exited = []
        tl = SceneTimeline()
        tl.between(1.0, 2.0, on_enter=lambda: None, on_exit=lambda: exited.append(True))
        tl.play()
        tl.update(1.5)   # enter the region (active=True)
        tl.update(1.0)   # advance past t_end → exit fires
        self.assertEqual([True], exited)


if __name__ == "__main__":
    unittest.main()
