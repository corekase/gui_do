"""Tests for ProgressBarControl, SpinnerControl, ToggleControl, LabelControl."""
import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.controls.display.progress_bar_control import ProgressBarControl
from gui_do.controls.input.spinner_control import SpinnerControl
from gui_do.controls.input.toggle_control import ToggleControl
from gui_do.controls.display.label_control import LabelControl
from gui_do.controls.input.button_control import ButtonControl

pygame.init()


# ===========================================================================
# ProgressBarControl
# ===========================================================================


class TestProgressBarControlInitial(unittest.TestCase):
    def test_default_value_zero(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        self.assertAlmostEqual(0.0, bar.value)

    def test_initial_value_stored(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), value=0.6)
        self.assertAlmostEqual(0.6, bar.value)

    def test_value_clamped_high(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), value=1.5)
        self.assertAlmostEqual(1.0, bar.value)

    def test_value_clamped_low(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), value=-0.5)
        self.assertAlmostEqual(0.0, bar.value)

    def test_default_not_indeterminate(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        self.assertFalse(bar.indeterminate)

    def test_indeterminate_stored(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), indeterminate=True)
        self.assertTrue(bar.indeterminate)

    def test_default_orientation_horizontal(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        self.assertEqual("horizontal", bar.orientation)

    def test_vertical_orientation(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 20, 300), orientation="vertical")
        self.assertEqual("vertical", bar.orientation)

    def test_invalid_orientation_raises(self):
        with self.assertRaises(ValueError):
            ProgressBarControl("pb", Rect(0, 0, 300, 20), orientation="diagonal")


class TestProgressBarControlValueSetter(unittest.TestCase):
    def setUp(self):
        self.bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))

    def test_set_value_in_range(self):
        self.bar.value = 0.75
        self.assertAlmostEqual(0.75, self.bar.value)

    def test_set_value_clamped_above_one(self):
        self.bar.value = 2.0
        self.assertAlmostEqual(1.0, self.bar.value)

    def test_set_value_clamped_below_zero(self):
        self.bar.value = -1.0
        self.assertAlmostEqual(0.0, self.bar.value)

    def test_set_same_value_no_error(self):
        self.bar.value = 0.5
        self.bar.value = 0.5   # idempotent


class TestProgressBarControlIndeterminate(unittest.TestCase):
    def test_set_indeterminate(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        bar.indeterminate = True
        self.assertTrue(bar.indeterminate)

    def test_clear_indeterminate(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), indeterminate=True)
        bar.indeterminate = False
        self.assertFalse(bar.indeterminate)

    def test_tick_advances_marquee_pos_in_indeterminate_mode(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), indeterminate=True)
        initial_pos = bar._marquee_pos
        bar.tick(0.1)
        self.assertNotAlmostEqual(initial_pos, bar._marquee_pos)

    def test_tick_no_op_in_determinate_mode(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        bar.tick(0.5)
        self.assertAlmostEqual(0.0, bar._marquee_pos)

    def test_marquee_pos_wraps(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20), indeterminate=True)
        # Advance far enough to wrap past 1.0
        bar.tick(100.0)
        self.assertGreaterEqual(bar._marquee_pos, 0.0)
        self.assertLess(bar._marquee_pos, 1.0)


class TestProgressBarControlBindTo(unittest.TestCase):
    def _make_observable(self, initial_value=0.0):
        from gui_do.data.presentation_model import ObservableValue
        return ObservableValue(initial_value)

    def test_bind_to_sets_initial_value(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        obs = self._make_observable(0.7)
        bar.bind_to(obs)
        self.assertAlmostEqual(0.7, bar.value)

    def test_bind_to_updates_on_change(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        obs = self._make_observable(0.0)
        bar.bind_to(obs)
        obs.value = 0.9
        self.assertAlmostEqual(0.9, bar.value)

    def test_bind_to_returns_unsub(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        obs = self._make_observable(0.0)
        unsub = bar.bind_to(obs)
        self.assertTrue(callable(unsub))

    def test_bind_to_unsub_stops_updates(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        obs = self._make_observable(0.0)
        unsub = bar.bind_to(obs)
        unsub()
        obs.value = 0.8
        self.assertAlmostEqual(0.0, bar.value)

    def test_bind_to_replaces_previous_binding(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        obs1 = self._make_observable(0.0)
        obs2 = self._make_observable(0.5)
        bar.bind_to(obs1)
        bar.bind_to(obs2)
        obs1.value = 1.0   # old binding — should not update bar
        self.assertAlmostEqual(0.5, bar.value)

    def test_accepts_mouse_focus_false(self):
        bar = ProgressBarControl("pb", Rect(0, 0, 300, 20))
        self.assertFalse(bar.accepts_mouse_focus())


# ===========================================================================
# SpinnerControl
# ===========================================================================


class TestSpinnerControlInitial(unittest.TestCase):
    def test_default_value_zero(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28))
        self.assertEqual(0, sp.value)

    def test_initial_value_stored(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=5)
        self.assertEqual(5, sp.value)

    def test_value_clamped_to_min(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=-5, min_value=0)
        self.assertEqual(0, sp.value)

    def test_value_clamped_to_max(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=200, max_value=100)
        self.assertEqual(100, sp.value)

    def test_float_mode_decimals(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=1.5, decimals=2)
        self.assertAlmostEqual(1.5, sp.value)

    def test_integer_mode_rounds(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=3.7, decimals=0)
        self.assertEqual(4, sp.value)


class TestSpinnerControlIncrementDecrement(unittest.TestCase):
    def test_increment_by_step(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=5, step=2)
        sp.increment()
        self.assertEqual(7, sp.value)

    def test_decrement_by_step(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=5, step=2)
        sp.decrement()
        self.assertEqual(3, sp.value)

    def test_increment_clamped_to_max(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=9, max_value=10, step=5)
        sp.increment()
        self.assertEqual(10, sp.value)

    def test_decrement_clamped_to_min(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=1, min_value=0, step=5)
        sp.decrement()
        self.assertEqual(0, sp.value)

    def test_increment_fires_on_change(self):
        received = []
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=0, on_change=lambda v, _: received.append(v))
        sp.increment()
        self.assertEqual([1], received)

    def test_decrement_fires_on_change(self):
        received = []
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=5, on_change=lambda v, _: received.append(v))
        sp.decrement()
        self.assertEqual([4], received)

    def test_no_change_no_callback(self):
        received = []
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=10, max_value=10, on_change=lambda v, _: received.append(v))
        sp.increment()   # already at max
        self.assertEqual([], received)


class TestSpinnerControlSetValue(unittest.TestCase):
    def test_set_value_no_callback(self):
        received = []
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=0, on_change=lambda v, _: received.append(v))
        sp.set_value(5)
        self.assertEqual(5, sp.value)
        self.assertEqual([], received)   # set_value does NOT fire on_change

    def test_value_setter_clamped(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), min_value=0, max_value=10)
        sp.value = 99
        self.assertEqual(10, sp.value)


class TestSpinnerControlFloatMode(unittest.TestCase):
    def test_float_step(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=1.0, step=0.1, decimals=1)
        sp.increment()
        self.assertAlmostEqual(1.1, sp.value, places=1)

    def test_float_clamp(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28), value=0.9, step=0.2, decimals=2, max_value=1.0)
        sp.increment()
        self.assertAlmostEqual(1.0, sp.value)

    def test_accepts_focus_when_visible_enabled(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28))
        self.assertTrue(sp.accepts_focus())

    def test_not_accepts_focus_when_disabled(self):
        sp = SpinnerControl("sp", Rect(0, 0, 120, 28))
        sp._enabled = False
        self.assertFalse(sp.accepts_focus())


# ===========================================================================
# ToggleControl
# ===========================================================================


class TestToggleControlInitial(unittest.TestCase):
    def test_initial_pushed_false(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        self.assertFalse(t.pushed)

    def test_initial_pushed_true(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", pushed=True)
        self.assertTrue(t.pushed)

    def test_text_off_defaults_to_text_on(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "Toggle")
        self.assertEqual("Toggle", t.text_off)

    def test_text_on_and_off_different(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", text_off="OFF")
        self.assertEqual("ON", t.text_on)
        self.assertEqual("OFF", t.text_off)


class TestToggleControlPushedSetter(unittest.TestCase):
    def test_set_pushed_true(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        t.pushed = True
        self.assertTrue(t.pushed)

    def test_set_pushed_false(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", pushed=True)
        t.pushed = False
        self.assertFalse(t.pushed)

    def test_set_same_value_idempotent(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", pushed=False)
        t.pushed = False   # no-op, should not raise


class TestToggleControlCommitToggle(unittest.TestCase):
    def test_commit_toggle_flips_state(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        t._commit_toggle()
        self.assertTrue(t.pushed)
        t._commit_toggle()
        self.assertFalse(t.pushed)

    def test_commit_toggle_fires_callback(self):
        received = []
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", on_toggle=lambda v: received.append(v))
        t._commit_toggle()
        self.assertEqual([True], received)
        t._commit_toggle()
        self.assertEqual([True, False], received)

    def test_commit_toggle_no_callback_no_error(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        t._commit_toggle()   # should not raise

    def test_set_on_toggle_callable(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        received = []
        t.set_on_toggle(lambda v: received.append(v))
        t._commit_toggle()
        self.assertEqual([True], received)

    def test_set_on_toggle_none_clears(self):
        received = []
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", on_toggle=lambda v: received.append(v))
        t.set_on_toggle(None)
        t._commit_toggle()
        self.assertEqual([], received)

    def test_set_on_toggle_non_callable_raises(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        with self.assertRaises(ValueError):
            t.set_on_toggle("not_a_callable")


class TestToggleControlStateCapture(unittest.TestCase):
    def test_capture_state(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", pushed=True)
        state = t.capture_state()
        self.assertEqual({"pushed": True}, state)

    def test_restore_state(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON", pushed=False)
        t.restore_state({"pushed": True})
        self.assertTrue(t.pushed)

    def test_restore_state_missing_key_no_error(self):
        t = ToggleControl("t", Rect(0, 0, 100, 30), "ON")
        t.restore_state({})   # should not raise


# ===========================================================================
# LabelControl
# ===========================================================================


class TestLabelControlInitial(unittest.TestCase):
    def test_text_stored(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hello")
        self.assertEqual("Hello", lbl.text)

    def test_default_align_left(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        self.assertEqual("left", lbl.align)

    def test_center_align(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi", align="center")
        self.assertEqual("center", lbl.align)

    def test_right_align(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi", align="right")
        self.assertEqual("right", lbl.align)

    def test_invalid_align_raises(self):
        with self.assertRaises(Exception):
            LabelControl("lbl", Rect(0, 0, 200, 24), "Hi", align="justify")

    def test_accepts_mouse_focus_false(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        self.assertFalse(lbl.accepts_mouse_focus())


class TestLabelControlTextSetter(unittest.TestCase):
    def test_set_text(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hello")
        lbl.text = "World"
        self.assertEqual("World", lbl.text)

    def test_set_same_text_idempotent(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hello")
        lbl.text = "Hello"   # no-op, should not raise


class TestLabelControlFontRole(unittest.TestCase):
    def test_default_font_role_body(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        self.assertEqual("body", lbl.font_role)

    def test_set_font_role(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        lbl.font_role = "title"
        self.assertEqual("title", lbl.font_role)

    def test_set_font_role_empty_raises(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        with self.assertRaises(Exception):
            lbl.font_role = ""

    def test_set_font_size(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        lbl.font_size = 18
        self.assertEqual(18, lbl.font_size)

    def test_font_size_clamped_to_one(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        lbl.font_size = 0
        self.assertEqual(1, lbl.font_size)


class TestLabelControlAlignSetter(unittest.TestCase):
    def test_set_align_center(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        lbl.align = "center"
        self.assertEqual("center", lbl.align)

    def test_set_invalid_align_raises(self):
        lbl = LabelControl("lbl", Rect(0, 0, 200, 24), "Hi")
        with self.assertRaises(Exception):
            lbl.align = "bottom"


# ===========================================================================
# ButtonControl.set_on_click
# ===========================================================================


class TestButtonControlSetOnClick(unittest.TestCase):
    def test_set_on_click_callable(self):
        btn = ButtonControl("btn", Rect(0, 0, 100, 30), "Click me")
        received = []
        btn.set_on_click(lambda: received.append(1))
        btn._invoke_click()
        self.assertEqual([1], received)

    def test_set_on_click_none_clears(self):
        received = []
        btn = ButtonControl("btn", Rect(0, 0, 100, 30), "Click me", on_click=lambda: received.append(1))
        btn.set_on_click(None)
        btn._invoke_click()
        self.assertEqual([], received)

    def test_set_on_click_non_callable_raises(self):
        btn = ButtonControl("btn", Rect(0, 0, 100, 30), "Click me")
        with self.assertRaises(Exception):
            btn.set_on_click("not_callable")

    def test_initial_on_click_fires(self):
        received = []
        btn = ButtonControl("btn", Rect(0, 0, 100, 30), "Click me", on_click=lambda: received.append(1))
        btn._invoke_click()
        self.assertEqual([1], received)

    def test_style_stored(self):
        btn = ButtonControl("btn", Rect(0, 0, 100, 30), "Click", style="angle")
        self.assertEqual("angle", btn.style)


if __name__ == "__main__":
    unittest.main()
