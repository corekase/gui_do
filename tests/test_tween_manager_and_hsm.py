import unittest

from gui_do.scheduling.tween_manager import (
    Easing,
    TweenManager,
    _lerp_float,
    _lerp_tuple,
    resolve_easing,
)
from gui_do.state.hierarchical_state_machine import HierarchicalStateMachine
from gui_do.state.state_machine import StateMachine


# ---------------------------------------------------------------------------
# Easing / lerp helpers
# ---------------------------------------------------------------------------


class TestEasingHelpers(unittest.TestCase):
    def test_lerp_float_midpoint(self):
        self.assertAlmostEqual(5.0, _lerp_float(0.0, 10.0, 0.5))

    def test_lerp_float_start(self):
        self.assertAlmostEqual(0.0, _lerp_float(0.0, 10.0, 0.0))

    def test_lerp_float_end(self):
        self.assertAlmostEqual(10.0, _lerp_float(0.0, 10.0, 1.0))

    def test_lerp_tuple_rgb_midpoint(self):
        result = _lerp_tuple((0, 0, 0), (100, 200, 50), 0.5)
        self.assertAlmostEqual(50, result[0])
        self.assertAlmostEqual(100, result[1])
        self.assertAlmostEqual(25, result[2])

    def test_resolve_easing_enum(self):
        fn = resolve_easing(Easing.LINEAR)
        self.assertAlmostEqual(0.5, fn(0.5))

    def test_resolve_easing_string(self):
        fn = resolve_easing("ease_in")
        self.assertAlmostEqual(0.25, fn(0.5))

    def test_resolve_easing_callable(self):
        custom = lambda t: t * 3
        fn = resolve_easing(custom)
        self.assertIs(custom, fn)

    def test_resolve_easing_unknown_raises(self):
        with self.assertRaises(ValueError):
            resolve_easing("no_such")

    def test_ease_in_out_midpoint(self):
        fn = resolve_easing(Easing.EASE_IN_OUT)
        self.assertAlmostEqual(0.5, fn(0.5))

    def test_ease_out_at_zero(self):
        fn = resolve_easing(Easing.EASE_OUT)
        self.assertAlmostEqual(0.0, fn(0.0))

    def test_ease_out_at_one(self):
        fn = resolve_easing(Easing.EASE_OUT)
        self.assertAlmostEqual(1.0, fn(1.0))


# ---------------------------------------------------------------------------
# TweenManager
# ---------------------------------------------------------------------------


class TestTweenManager(unittest.TestCase):
    def test_zero_duration_tween_completes_immediately(self):
        mgr = TweenManager()
        received = []
        h = mgr.tween_fn(0.0, received.append)
        self.assertTrue(h.is_complete)
        self.assertEqual([1.0], received)

    def test_zero_duration_fires_on_complete(self):
        mgr = TweenManager()
        done = []
        mgr.tween_fn(0.0, lambda t: None, on_complete=lambda: done.append(True))
        self.assertEqual([True], done)

    def test_active_count_increments(self):
        mgr = TweenManager()
        mgr.tween_fn(1.0, lambda t: None)
        mgr.tween_fn(1.0, lambda t: None)
        self.assertEqual(2, mgr.active_count)

    def test_update_advances_tween(self):
        mgr = TweenManager()
        values = []
        mgr.tween_fn(1.0, values.append, easing=Easing.LINEAR)
        mgr.update(0.5)
        self.assertAlmostEqual(0.5, values[-1], places=5)

    def test_update_completes_tween_when_elapsed_exceeds_duration(self):
        mgr = TweenManager()
        h = mgr.tween_fn(0.1, lambda t: None, easing=Easing.LINEAR)
        mgr.update(0.2)
        self.assertTrue(h.is_complete)

    def test_on_complete_fires_when_tween_finishes(self):
        mgr = TweenManager()
        done = []
        mgr.tween_fn(0.1, lambda t: None, on_complete=lambda: done.append(True))
        mgr.update(0.2)
        self.assertEqual([True], done)

    def test_active_count_drops_after_completion(self):
        mgr = TweenManager()
        mgr.tween_fn(0.1, lambda t: None)
        mgr.update(0.2)
        self.assertEqual(0, mgr.active_count)

    def test_cancel_stops_updates(self):
        mgr = TweenManager()
        values = []
        h = mgr.tween_fn(1.0, values.append, easing=Easing.LINEAR)
        mgr.cancel(h)
        mgr.update(0.5)
        # No new values after cancellation
        self.assertEqual([], values)

    def test_cancel_returns_true_for_active(self):
        mgr = TweenManager()
        h = mgr.tween_fn(1.0, lambda t: None)
        self.assertTrue(mgr.cancel(h))

    def test_cancel_returns_false_for_already_complete(self):
        mgr = TweenManager()
        h = mgr.tween_fn(0.0, lambda t: None)
        self.assertFalse(mgr.cancel(h))

    def test_cancel_all_stops_all_tweens(self):
        mgr = TweenManager()
        mgr.tween_fn(1.0, lambda t: None)
        mgr.tween_fn(1.0, lambda t: None)
        count = mgr.cancel_all()
        self.assertEqual(2, count)
        self.assertEqual(0, mgr.active_count)

    def test_cancel_all_for_tag(self):
        mgr = TweenManager()
        mgr.tween_fn(1.0, lambda t: None, tag="ui")
        mgr.tween_fn(1.0, lambda t: None, tag="ui")
        mgr.tween_fn(1.0, lambda t: None, tag="other")
        count = mgr.cancel_all_for_tag("ui")
        self.assertEqual(2, count)
        self.assertEqual(1, mgr.active_count)

    def test_tween_attr_float(self):
        class _Obj:
            x = 0.0

        obj = _Obj()
        mgr = TweenManager()
        mgr.tween(obj, "x", 100.0, 1.0, easing=Easing.LINEAR)
        mgr.update(0.5)
        self.assertAlmostEqual(50.0, obj.x, places=3)

    def test_tween_attr_completes_at_end_value(self):
        class _Obj:
            x = 0.0

        obj = _Obj()
        mgr = TweenManager()
        mgr.tween(obj, "x", 100.0, 0.1, easing=Easing.LINEAR)
        mgr.update(0.2)
        self.assertAlmostEqual(100.0, obj.x, places=3)

    def test_tween_attr_tuple_interpolation(self):
        class _Obj:
            color = (0, 0, 0)

        obj = _Obj()
        mgr = TweenManager()
        mgr.tween(obj, "color", (100, 200, 50), 1.0, easing=Easing.LINEAR)
        mgr.update(1.0)
        self.assertAlmostEqual(100, obj.color[0], places=0)
        self.assertAlmostEqual(200, obj.color[1], places=0)

    def test_handle_elapsed_fraction(self):
        mgr = TweenManager()
        h = mgr.tween_fn(2.0, lambda t: None, easing=Easing.LINEAR)
        mgr.update(1.0)
        self.assertAlmostEqual(0.5, h.elapsed_fraction(), places=5)

    def test_handle_elapsed_fraction_complete_is_one(self):
        mgr = TweenManager()
        h = mgr.tween_fn(0.0, lambda t: None)
        self.assertAlmostEqual(1.0, h.elapsed_fraction())

    def test_is_cancelled_after_cancel(self):
        mgr = TweenManager()
        h = mgr.tween_fn(1.0, lambda t: None)
        mgr.cancel(h)
        self.assertTrue(h.is_cancelled)

    def test_update_zero_dt_does_not_advance(self):
        mgr = TweenManager()
        values = []
        mgr.tween_fn(1.0, values.append, easing=Easing.LINEAR)
        mgr.update(0.0)
        # t=0 → eased_t = 0.0 for linear
        self.assertEqual([0.0], values)


# ---------------------------------------------------------------------------
# HierarchicalStateMachine
# ---------------------------------------------------------------------------


class TestHierarchicalStateMachine(unittest.TestCase):
    def test_flat_transition_still_works(self):
        hsm = HierarchicalStateMachine("idle")
        hsm.add_transition("idle", "running", trigger="start")
        hsm.trigger("start")
        self.assertEqual("running", hsm.current.value)

    def test_composite_entry_resets_sub_machine(self):
        inner = StateMachine("sub_a")
        inner.add_state("sub_b")

        outer = HierarchicalStateMachine("home")
        outer.add_composite("active", inner, initial="sub_a")
        outer.add_transition("home", "active", trigger="go")

        # Manually advance inner, then re-enter to verify reset
        inner.current.value = "sub_b"
        outer.trigger("go")
        self.assertEqual("sub_a", inner.current.value)

    def test_sub_current_returns_sub_state(self):
        inner = StateMachine("s1")
        outer = HierarchicalStateMachine("home")
        outer.add_composite("comp", inner, initial="s1")
        outer.add_transition("home", "comp", trigger="enter")
        outer.trigger("enter")
        self.assertEqual("s1", outer.sub_current("comp"))

    def test_sub_current_unknown_returns_none(self):
        outer = HierarchicalStateMachine("home")
        self.assertIsNone(outer.sub_current("no_such"))

    def test_sub_trigger_advances_inner_machine(self):
        inner = StateMachine("s1")
        inner.add_state("s2")
        inner.add_transition("s1", "s2", trigger="next")

        outer = HierarchicalStateMachine("home")
        outer.add_composite("comp", inner, initial="s1")
        outer.add_transition("home", "comp", trigger="enter")
        outer.trigger("enter")

        result = outer.sub_trigger("comp", "next")
        self.assertTrue(result)
        self.assertEqual("s2", inner.current.value)

    def test_sub_trigger_unknown_composite_returns_false(self):
        outer = HierarchicalStateMachine("home")
        self.assertFalse(outer.sub_trigger("missing", "evt"))

    def test_history_resumes_last_sub_state(self):
        inner = StateMachine("page1")
        inner.add_state("page2")
        inner.add_transition("page1", "page2", trigger="next")

        outer = HierarchicalStateMachine("home")
        outer.add_history("wizard", inner, initial="page1")
        outer.add_transition("home", "wizard", trigger="open")
        outer.add_transition("wizard", "home", trigger="close")

        outer.trigger("open")
        outer.sub_trigger("wizard", "next")  # advance inner to page2
        outer.trigger("close")               # exit: history records page2
        outer.trigger("open")               # re-enter: history should restore page2

        self.assertEqual("page2", inner.current.value)

    def test_history_uses_initial_on_first_entry(self):
        inner = StateMachine("page1")
        outer = HierarchicalStateMachine("home")
        outer.add_history("wizard", inner, initial="page1")
        outer.add_transition("home", "wizard", trigger="open")
        outer.trigger("open")
        self.assertEqual("page1", inner.current.value)

    def test_trigger_to_bypasses_transitions(self):
        outer = HierarchicalStateMachine("a")
        outer.add_state("b")
        result = outer.trigger_to("b")
        self.assertTrue(result)
        self.assertEqual("b", outer.current.value)

    def test_trigger_to_same_state_returns_false(self):
        outer = HierarchicalStateMachine("a")
        self.assertFalse(outer.trigger_to("a"))

    def test_trigger_to_unknown_state_raises(self):
        outer = HierarchicalStateMachine("a")
        with self.assertRaises(ValueError):
            outer.trigger_to("no_such")

    def test_parallel_regions_tracked(self):
        r1 = StateMachine("on")
        r2 = StateMachine("off")
        outer = HierarchicalStateMachine("parallel")
        outer.add_parallel("parallel", [r1, r2])
        self.assertEqual([r1, r2], outer.parallel_regions("parallel"))

    def test_trigger_parallel_fires_in_all_regions(self):
        r1 = StateMachine("on")
        r1.add_state("off")
        r1.add_transition("on", "off", trigger="toggle")

        r2 = StateMachine("on")
        r2.add_state("off")
        r2.add_transition("on", "off", trigger="toggle")

        outer = HierarchicalStateMachine("both")
        outer.add_parallel("both", [r1, r2])
        results = outer.trigger_parallel("both", "toggle")
        self.assertEqual([True, True], results)
        self.assertEqual("off", r1.current.value)
        self.assertEqual("off", r2.current.value)

    def test_sub_machine_accessor(self):
        inner = StateMachine("s1")
        outer = HierarchicalStateMachine("home")
        outer.add_composite("comp", inner, initial="s1")
        self.assertIs(inner, outer.sub_machine("comp"))

    def test_sub_machine_unknown_returns_none(self):
        outer = HierarchicalStateMachine("home")
        self.assertIsNone(outer.sub_machine("no_such"))


if __name__ == "__main__":
    unittest.main()
