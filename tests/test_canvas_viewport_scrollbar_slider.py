"""Tests for CanvasViewport, ScrollbarControl, and SliderControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.canvas.canvas_viewport import CanvasViewport
from gui_do.controls.input.scrollbar_control import ScrollbarControl
from gui_do.controls.input.slider_control import SliderControl
from gui_do.layout.layout_axis import LayoutAxis

pygame.init()


# ===========================================================================
# CanvasViewport — initial state
# ===========================================================================


class TestCanvasViewportInitial(unittest.TestCase):
    def test_default_scale(self):
        vp = CanvasViewport()
        self.assertAlmostEqual(1.0, vp.scale)

    def test_default_offset(self):
        vp = CanvasViewport()
        self.assertEqual((0.0, 0.0), vp.offset)

    def test_content_size_stored(self):
        vp = CanvasViewport(content_size=(2048, 1024))
        self.assertEqual((2048, 1024), vp.content_size)

    def test_min_scale_stored(self):
        vp = CanvasViewport(min_scale=0.1)
        self.assertAlmostEqual(0.1, vp.min_scale)

    def test_max_scale_stored(self):
        vp = CanvasViewport(max_scale=8.0)
        self.assertAlmostEqual(8.0, vp.max_scale)

    def test_initial_scale_clamped_low(self):
        vp = CanvasViewport(min_scale=0.5, initial_scale=0.01)
        self.assertAlmostEqual(0.5, vp.scale)

    def test_initial_scale_clamped_high(self):
        vp = CanvasViewport(max_scale=4.0, initial_scale=100.0)
        self.assertAlmostEqual(4.0, vp.scale)

    def test_initial_offset_stored(self):
        vp = CanvasViewport(initial_offset=(10.0, 20.0))
        self.assertAlmostEqual(10.0, vp.offset[0])
        self.assertAlmostEqual(20.0, vp.offset[1])


class TestCanvasViewportCoordinates(unittest.TestCase):
    def test_to_canvas_at_origin(self):
        vp = CanvasViewport()
        cx, cy = vp.to_canvas((0.0, 0.0))
        self.assertAlmostEqual(0.0, cx)
        self.assertAlmostEqual(0.0, cy)

    def test_to_canvas_with_offset(self):
        vp = CanvasViewport(initial_offset=(100.0, 50.0))
        cx, cy = vp.to_canvas((100.0, 50.0))
        self.assertAlmostEqual(0.0, cx)
        self.assertAlmostEqual(0.0, cy)

    def test_to_screen_round_trip(self):
        vp = CanvasViewport(initial_offset=(30.0, 20.0), initial_scale=2.0)
        content_pt = (150.0, 75.0)
        screen_pt = vp.to_screen(content_pt)
        back = vp.to_canvas(screen_pt)
        self.assertAlmostEqual(content_pt[0], back[0], places=5)
        self.assertAlmostEqual(content_pt[1], back[1], places=5)

    def test_to_canvas_with_scale(self):
        vp = CanvasViewport(initial_scale=2.0)
        cx, cy = vp.to_canvas((200.0, 100.0))
        self.assertAlmostEqual(100.0, cx)
        self.assertAlmostEqual(50.0, cy)


class TestCanvasViewportPanZoom(unittest.TestCase):
    def test_pan_shifts_offset(self):
        vp = CanvasViewport()
        vp.pan((10.0, -5.0))
        self.assertAlmostEqual(10.0, vp.offset[0])
        self.assertAlmostEqual(-5.0, vp.offset[1])

    def test_pan_accumulates(self):
        vp = CanvasViewport()
        vp.pan((5.0, 3.0))
        vp.pan((2.0, -1.0))
        self.assertAlmostEqual(7.0, vp.offset[0])
        self.assertAlmostEqual(2.0, vp.offset[1])

    def test_zoom_at_changes_scale(self):
        vp = CanvasViewport()
        vp.zoom_at(anchor=(0.0, 0.0), factor=2.0)
        self.assertAlmostEqual(2.0, vp.scale)

    def test_zoom_at_respects_max(self):
        vp = CanvasViewport(max_scale=4.0)
        vp.zoom_at(anchor=(0.0, 0.0), factor=100.0)
        self.assertAlmostEqual(4.0, vp.scale)

    def test_zoom_at_respects_min(self):
        vp = CanvasViewport(min_scale=0.5)
        vp.zoom_at(anchor=(0.0, 0.0), factor=0.0001)
        self.assertAlmostEqual(0.5, vp.scale)

    def test_zoom_at_keeps_anchor_fixed(self):
        vp = CanvasViewport()
        anchor = (100.0, 80.0)
        content_before = vp.to_canvas(anchor)
        vp.zoom_at(anchor=anchor, factor=3.0)
        content_after = vp.to_canvas(anchor)
        self.assertAlmostEqual(content_before[0], content_after[0], places=4)
        self.assertAlmostEqual(content_before[1], content_after[1], places=4)

    def test_zoom_to_absolute(self):
        vp = CanvasViewport()
        vp.zoom_to(3.0)
        self.assertAlmostEqual(3.0, vp.scale)

    def test_reset_restores_defaults(self):
        vp = CanvasViewport()
        vp.pan((100.0, 50.0))
        vp.zoom_to(4.0)
        vp.reset()
        self.assertAlmostEqual(1.0, vp.scale)
        self.assertAlmostEqual(0.0, vp.offset[0])
        self.assertAlmostEqual(0.0, vp.offset[1])

    def test_set_offset_absolute(self):
        vp = CanvasViewport()
        vp.set_offset((75.0, -20.0))
        self.assertAlmostEqual(75.0, vp.offset[0])
        self.assertAlmostEqual(-20.0, vp.offset[1])


class TestCanvasViewportFitContent(unittest.TestCase):
    def test_fit_content_scales_down(self):
        vp = CanvasViewport(content_size=(1000, 500))
        vp.fit_content((500, 500))
        # scale should be <= 1 since content is wider than viewport
        self.assertLessEqual(vp.scale, 1.0)

    def test_fit_content_centers(self):
        vp = CanvasViewport(content_size=(100, 100))
        vp.fit_content((200, 200))
        # Content fits at 2x; offset centres it: offset = (200 - 100*2)/2 = 0
        self.assertAlmostEqual(0.0, vp.offset[0], places=3)
        self.assertAlmostEqual(0.0, vp.offset[1], places=3)


# ===========================================================================
# ScrollbarControl
# ===========================================================================


class TestScrollbarControlInitial(unittest.TestCase):
    def _make(self, content=400, viewport=100, offset=0):
        return ScrollbarControl(
            "sb", Rect(0, 0, 20, 200), LayoutAxis.VERTICAL,
            content_size=content, viewport_size=viewport, offset=offset,
        )

    def test_offset_stored(self):
        sb = self._make(offset=50)
        self.assertEqual(50, sb.offset)

    def test_offset_clamped_negative(self):
        sb = self._make(offset=-10)
        self.assertEqual(0, sb.offset)

    def test_offset_clamped_max(self):
        sb = self._make(content=400, viewport=100, offset=999)
        # max_offset = 400 - 100 = 300
        self.assertEqual(300, sb.offset)

    def test_content_size_stored(self):
        sb = self._make(content=500)
        self.assertEqual(500, sb.content_size)

    def test_viewport_size_stored(self):
        sb = self._make(viewport=120)
        self.assertEqual(120, sb.viewport_size)

    def test_scroll_fraction_start(self):
        sb = self._make(offset=0)
        self.assertAlmostEqual(0.0, sb.scroll_fraction)

    def test_scroll_fraction_end(self):
        sb = self._make(content=400, viewport=100, offset=300)
        self.assertAlmostEqual(1.0, sb.scroll_fraction)

    def test_scroll_fraction_middle(self):
        sb = self._make(content=400, viewport=100, offset=150)
        self.assertAlmostEqual(0.5, sb.scroll_fraction)


class TestScrollbarControlSetOffset(unittest.TestCase):
    def _make(self):
        return ScrollbarControl(
            "sb", Rect(0, 0, 20, 200), LayoutAxis.VERTICAL,
            content_size=400, viewport_size=100, offset=0,
        )

    def test_set_offset_returns_true_on_change(self):
        sb = self._make()
        result = sb.set_offset(50)
        self.assertTrue(result)

    def test_set_offset_updates(self):
        sb = self._make()
        sb.set_offset(100)
        self.assertEqual(100, sb.offset)

    def test_set_offset_returns_false_no_change(self):
        sb = self._make()
        result = sb.set_offset(0)
        self.assertFalse(result)

    def test_set_offset_clamps_high(self):
        sb = self._make()
        sb.set_offset(9999)
        self.assertEqual(300, sb.offset)

    def test_set_offset_clamps_low(self):
        sb = self._make()
        sb.set_offset(-50)
        self.assertEqual(0, sb.offset)

    def test_adjust_offset_delta(self):
        sb = self._make()
        sb.set_offset(100)
        sb.adjust_offset(50)
        self.assertEqual(150, sb.offset)

    def test_adjust_offset_clamped(self):
        sb = self._make()
        sb.adjust_offset(-100)
        self.assertEqual(0, sb.offset)


# ===========================================================================
# SliderControl
# ===========================================================================


class TestSliderControlInitial(unittest.TestCase):
    def _make(self, minimum=0.0, maximum=100.0, value=50.0):
        return SliderControl(
            "sl", Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL,
            minimum=minimum, maximum=maximum, value=value,
        )

    def test_value_stored(self):
        sl = self._make(value=60.0)
        self.assertAlmostEqual(60.0, sl.value)

    def test_minimum_stored(self):
        sl = self._make(minimum=10.0)
        self.assertAlmostEqual(10.0, sl.minimum)

    def test_maximum_stored(self):
        sl = self._make(maximum=200.0)
        self.assertAlmostEqual(200.0, sl.maximum)

    def test_value_clamped_low(self):
        sl = self._make(minimum=10.0, maximum=100.0, value=-5.0)
        self.assertAlmostEqual(10.0, sl.value)

    def test_value_clamped_high(self):
        sl = self._make(minimum=0.0, maximum=100.0, value=200.0)
        self.assertAlmostEqual(100.0, sl.value)

    def test_normalized_midpoint(self):
        sl = self._make(minimum=0.0, maximum=100.0, value=50.0)
        self.assertAlmostEqual(0.5, sl.normalized)

    def test_normalized_at_min(self):
        sl = self._make(minimum=0.0, maximum=100.0, value=0.0)
        self.assertAlmostEqual(0.0, sl.normalized)

    def test_normalized_at_max(self):
        sl = self._make(minimum=0.0, maximum=100.0, value=100.0)
        self.assertAlmostEqual(1.0, sl.normalized)


class TestSliderControlSetValue(unittest.TestCase):
    def _make(self):
        return SliderControl(
            "sl", Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL,
            minimum=0.0, maximum=100.0, value=50.0,
        )

    def test_set_value_returns_true_on_change(self):
        sl = self._make()
        self.assertTrue(sl.set_value(75.0))

    def test_set_value_updates(self):
        sl = self._make()
        sl.set_value(80.0)
        self.assertAlmostEqual(80.0, sl.value)

    def test_set_value_returns_false_no_change(self):
        sl = self._make()
        sl.set_value(50.0)
        self.assertFalse(sl.set_value(50.0))

    def test_set_value_clamps_low(self):
        sl = self._make()
        sl.set_value(-100.0)
        self.assertAlmostEqual(0.0, sl.value)

    def test_set_value_clamps_high(self):
        sl = self._make()
        sl.set_value(999.0)
        self.assertAlmostEqual(100.0, sl.value)

    def test_adjust_value_delta(self):
        sl = self._make()
        sl.adjust_value(10.0)
        self.assertAlmostEqual(60.0, sl.value)

    def test_set_normalized(self):
        sl = self._make()
        sl.set_normalized(0.25)
        self.assertAlmostEqual(25.0, sl.value)

    def test_set_normalized_clamped(self):
        sl = self._make()
        sl.set_normalized(1.5)
        self.assertAlmostEqual(100.0, sl.value)


if __name__ == "__main__":
    unittest.main()
