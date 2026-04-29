"""Tests for ProgressBarControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.display.progress_bar_control import ProgressBarControl


class TestProgressBarInitial(unittest.TestCase):
    def test_default_value_zero(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        self.assertAlmostEqual(bar.value, 0.0)

    def test_default_not_indeterminate(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        self.assertFalse(bar.indeterminate)

    def test_default_horizontal(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        self.assertEqual(bar.orientation, ProgressBarControl.HORIZONTAL)


class TestProgressBarValueClamping(unittest.TestCase):
    def test_value_clamped_above_one(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        bar.value = 1.5
        self.assertAlmostEqual(bar.value, 1.0)

    def test_value_clamped_below_zero(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        bar.value = -0.5
        self.assertAlmostEqual(bar.value, 0.0)

    def test_value_mid_range_stored_correctly(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        bar.value = 0.75
        self.assertAlmostEqual(bar.value, 0.75)


class TestProgressBarOrientation(unittest.TestCase):
    def test_vertical_orientation_accepted(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 20, 100), orientation="vertical")
        self.assertEqual(bar.orientation, ProgressBarControl.VERTICAL)

    def test_invalid_orientation_raises(self) -> None:
        with self.assertRaises(ValueError):
            ProgressBarControl("bar", Rect(0, 0, 100, 20), orientation="diagonal")


class TestProgressBarIndeterminate(unittest.TestCase):
    def test_set_indeterminate_true(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20), indeterminate=True)
        self.assertTrue(bar.indeterminate)

    def test_toggle_indeterminate(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        bar.indeterminate = True
        self.assertTrue(bar.indeterminate)
        bar.indeterminate = False
        self.assertFalse(bar.indeterminate)


class TestProgressBarTick(unittest.TestCase):
    def test_tick_advances_marquee_pos(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20), indeterminate=True)
        pos_before = bar._marquee_pos
        bar.tick(0.1)
        self.assertNotEqual(bar._marquee_pos, pos_before)

    def test_marquee_pos_wraps_around(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20), indeterminate=True)
        # Advance enough to wrap past 1.0+width
        for _ in range(100):
            bar.tick(0.1)
        # After wrapping marquee_pos should still be in valid range
        self.assertGreaterEqual(bar._marquee_pos, 0.0)


class TestProgressBarAcceptsMouse(unittest.TestCase):
    def test_accepts_mouse_focus_false(self) -> None:
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        self.assertFalse(bar.accepts_mouse_focus())


class TestProgressBarBindTo(unittest.TestCase):
    def test_bind_to_returns_callable(self) -> None:
        from gui_do.data.presentation_model import ObservableValue
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        obs = ObservableValue(0.0)
        unsub = bar.bind_to(obs)
        self.assertTrue(callable(unsub))

    def test_bind_to_updates_value(self) -> None:
        from gui_do.data.presentation_model import ObservableValue
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        obs = ObservableValue(0.0)
        bar.bind_to(obs)
        obs.value = 0.5
        self.assertAlmostEqual(bar.value, 0.5)

    def test_unsub_stops_updates(self) -> None:
        from gui_do.data.presentation_model import ObservableValue
        bar = ProgressBarControl("bar", Rect(0, 0, 100, 20))
        obs = ObservableValue(0.0)
        unsub = bar.bind_to(obs)
        obs.value = 0.3
        unsub()
        obs.value = 0.9
        self.assertAlmostEqual(bar.value, 0.3)
