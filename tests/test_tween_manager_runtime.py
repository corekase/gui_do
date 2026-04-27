"""Tests for TweenManager (Feature 3)."""
import unittest
from types import SimpleNamespace

from gui_do.core.tween_manager import TweenManager, TweenHandle, Easing


class TestTweenFnCallsPerFrame(unittest.TestCase):
    def test_tween_fn_calls_fn_per_frame(self) -> None:
        mgr = TweenManager()
        calls = []
        mgr.tween_fn(0.1, lambda t: calls.append(t))
        mgr.update(0.05)
        mgr.update(0.05)
        self.assertGreaterEqual(len(calls), 2)


class TestTweenFnCompletesAtDuration(unittest.TestCase):
    def test_tween_fn_completes_at_duration(self) -> None:
        mgr = TweenManager()
        last_t = [None]
        mgr.tween_fn(0.1, lambda t: last_t.__setitem__(0, t))
        mgr.update(0.2)  # past duration
        self.assertEqual(last_t[0], 1.0)


class TestTweenFnOnCompleteFiresOnce(unittest.TestCase):
    def test_tween_fn_on_complete_fires_once(self) -> None:
        mgr = TweenManager()
        fired = [0]
        mgr.tween_fn(0.05, lambda t: None, on_complete=lambda: fired.__setitem__(0, fired[0] + 1))
        mgr.update(0.1)
        mgr.update(0.1)
        self.assertEqual(fired[0], 1)


class TestTweenAttrFloat(unittest.TestCase):
    def test_tween_attr_float_interpolates_to_end(self) -> None:
        mgr = TweenManager()
        obj = SimpleNamespace(x=0.0)
        mgr.tween(obj, "x", 100.0, 0.1)
        mgr.update(0.1)
        self.assertAlmostEqual(obj.x, 100.0, places=3)


class TestTweenAttrTuple(unittest.TestCase):
    def test_tween_attr_tuple_interpolates_component_wise(self) -> None:
        mgr = TweenManager()
        obj = SimpleNamespace(pos=(0.0, 0.0))
        mgr.tween(obj, "pos", (10.0, 20.0), 0.1)
        mgr.update(0.1)
        self.assertAlmostEqual(obj.pos[0], 10.0, places=3)
        self.assertAlmostEqual(obj.pos[1], 20.0, places=3)


class TestCancelStopsAnimation(unittest.TestCase):
    def test_cancel_stops_animation(self) -> None:
        mgr = TweenManager()
        calls = []
        handle = mgr.tween_fn(1.0, lambda t: calls.append(t))
        mgr.update(0.1)
        count_before = len(calls)
        handle.cancel()
        mgr.update(0.1)
        self.assertEqual(len(calls), count_before)


class TestCancelAllForTag(unittest.TestCase):
    def test_cancel_all_for_tag_removes_group(self) -> None:
        mgr = TweenManager()
        calls = []
        mgr.tween_fn(1.0, lambda t: calls.append(("a", t)), tag="group1")
        mgr.tween_fn(1.0, lambda t: calls.append(("b", t)), tag="group1")
        mgr.tween_fn(1.0, lambda t: calls.append(("c", t)), tag="other")
        mgr.update(0.1)
        count = mgr.cancel_all_for_tag("group1")
        self.assertEqual(count, 2)
        calls.clear()
        mgr.update(0.1)
        # only "other" still fires
        self.assertTrue(all(label == "c" for label, _ in calls))


class TestActiveCount(unittest.TestCase):
    def test_active_count_tracks_live_tweens(self) -> None:
        mgr = TweenManager()
        self.assertEqual(mgr.active_count, 0)
        mgr.tween_fn(1.0, lambda t: None)
        mgr.tween_fn(1.0, lambda t: None)
        self.assertEqual(mgr.active_count, 2)
        mgr.update(2.0)  # past both durations
        self.assertEqual(mgr.active_count, 0)


class TestEasingLinear(unittest.TestCase):
    def test_easing_linear_midpoint(self) -> None:
        mgr = TweenManager()
        values = []
        mgr.tween_fn(1.0, lambda t: values.append(t), easing=Easing.LINEAR)
        mgr.update(0.5)
        self.assertAlmostEqual(values[-1], 0.5, places=5)


class TestEasingEaseInOut(unittest.TestCase):
    def test_easing_ease_in_out_midpoint(self) -> None:
        mgr = TweenManager()
        values = []
        mgr.tween_fn(1.0, lambda t: values.append(t), easing=Easing.EASE_IN_OUT)
        mgr.update(0.5)
        # ease_in_out at t=0.5: 3*(0.5^2) - 2*(0.5^3) = 0.75 - 0.25 = 0.5
        self.assertAlmostEqual(values[-1], 0.5, places=5)


class TestEasingCallableOverride(unittest.TestCase):
    def test_easing_callable_override(self) -> None:
        mgr = TweenManager()
        values = []
        mgr.tween_fn(1.0, lambda t: values.append(t), easing=lambda t: t ** 3)
        mgr.update(0.5)
        # t=0.5, cubic: 0.5^3 = 0.125
        self.assertAlmostEqual(values[-1], 0.125, places=5)


class TestZeroDurationCompletesImmediately(unittest.TestCase):
    def test_zero_duration_completes_immediately(self) -> None:
        mgr = TweenManager()
        values = []
        handle = mgr.tween_fn(0.0, lambda t: values.append(t))
        # Should have fired with t=1.0 on creation
        self.assertIn(1.0, values)
        # After any update, is_complete should be True
        mgr.update(0.0)
        self.assertTrue(handle.is_complete)


class TestMultipleTweensOnSameTarget(unittest.TestCase):
    def test_multiple_tweens_on_same_target(self) -> None:
        mgr = TweenManager()
        obj = SimpleNamespace(x=0.0, y=0.0)
        mgr.tween(obj, "x", 10.0, 0.1)
        mgr.tween(obj, "y", 20.0, 0.1)
        mgr.update(0.1)
        self.assertAlmostEqual(obj.x, 10.0, places=3)
        self.assertAlmostEqual(obj.y, 20.0, places=3)


if __name__ == "__main__":
    unittest.main()
