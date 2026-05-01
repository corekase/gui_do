"""Tests for Viewport (scroll/zoom) and ResponsiveLayout (breakpoint-driven)."""
import unittest

import pygame
pygame.init()

from gui_do.layout.viewport import Viewport
from gui_do.layout.responsive_layout import Breakpoint, ResponsiveLayout


# ===========================================================================
# Viewport — initial state
# ===========================================================================


class TestViewportInitial(unittest.TestCase):
    def test_scroll_zero(self):
        vp = Viewport(content_size=(1000, 800), viewport_size=(400, 300))
        self.assertEqual(0.0, vp.scroll_x)
        self.assertEqual(0.0, vp.scroll_y)

    def test_zoom_default(self):
        vp = Viewport()
        self.assertEqual(1.0, vp.zoom)

    def test_content_size_stored(self):
        vp = Viewport(content_size=(500, 400))
        self.assertEqual((500, 400), vp.content_size)

    def test_viewport_size_stored(self):
        vp = Viewport(viewport_size=(320, 240))
        self.assertEqual((320, 240), vp.viewport_size)

    def test_scroll_offset_tuple(self):
        vp = Viewport()
        self.assertEqual((0.0, 0.0), vp.scroll_offset)


# ===========================================================================
# Viewport — scrolling
# ===========================================================================


class TestViewportScroll(unittest.TestCase):
    def test_scroll_to_absolute(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        vp.scroll_to(50, 75)
        self.assertEqual(50.0, vp.scroll_x)
        self.assertEqual(75.0, vp.scroll_y)

    def test_scroll_by_relative(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        vp.scroll_to(100, 100)
        vp.scroll_by(20, 30)
        self.assertAlmostEqual(120.0, vp.scroll_x)
        self.assertAlmostEqual(130.0, vp.scroll_y)

    def test_scroll_clamped_at_max(self):
        vp = Viewport(content_size=(200, 200), viewport_size=(100, 100))
        vp.scroll_to(9999, 9999)
        self.assertLessEqual(vp.scroll_x, 100.0)
        self.assertLessEqual(vp.scroll_y, 100.0)

    def test_scroll_clamped_at_zero(self):
        vp = Viewport(content_size=(200, 200), viewport_size=(100, 100))
        vp.scroll_to(-100, -100)
        self.assertEqual(0.0, vp.scroll_x)
        self.assertEqual(0.0, vp.scroll_y)

    def test_scroll_notifies_subscriber(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        calls = []
        vp.subscribe(lambda: calls.append(1))
        vp.scroll_to(50, 50)
        self.assertEqual(1, len(calls))

    def test_scroll_no_notify_when_unchanged(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        calls = []
        vp.subscribe(lambda: calls.append(1))
        vp.scroll_to(0, 0)  # already at 0,0
        self.assertEqual(0, len(calls))


# ===========================================================================
# Viewport — zooming
# ===========================================================================


class TestViewportZoom(unittest.TestCase):
    def test_set_zoom(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        vp.set_zoom(2.0)
        self.assertAlmostEqual(2.0, vp.zoom)

    def test_zoom_clamped_at_min(self):
        vp = Viewport(min_zoom=0.5)
        vp.set_zoom(0.01)
        self.assertAlmostEqual(0.5, vp.zoom)

    def test_zoom_clamped_at_max(self):
        vp = Viewport(max_zoom=4.0)
        vp.set_zoom(100.0)
        self.assertAlmostEqual(4.0, vp.zoom)

    def test_adjust_zoom_multiplies(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        vp.set_zoom(2.0)
        vp.adjust_zoom(1.5)
        self.assertAlmostEqual(3.0, vp.zoom)

    def test_set_zoom_notifies_subscriber(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        calls = []
        vp.subscribe(lambda: calls.append(1))
        vp.set_zoom(2.0)
        self.assertGreaterEqual(len(calls), 1)


# ===========================================================================
# Viewport — coordinate transforms
# ===========================================================================


class TestViewportTransforms(unittest.TestCase):
    def test_screen_to_local_no_scroll_no_zoom(self):
        vp = Viewport()
        self.assertEqual((100, 200), vp.screen_to_local((100, 200)))

    def test_local_to_screen_no_scroll_no_zoom(self):
        vp = Viewport()
        self.assertEqual((50, 75), vp.local_to_screen((50, 75)))

    def test_screen_to_local_with_scroll(self):
        vp = Viewport(content_size=(1000, 1000), viewport_size=(100, 100))
        vp.scroll_to(10, 20)
        x, y = vp.screen_to_local((0, 0))
        self.assertAlmostEqual(10.0, x)
        self.assertAlmostEqual(20.0, y)

    def test_roundtrip(self):
        vp = Viewport(content_size=(2000, 2000), viewport_size=(400, 300))
        vp.scroll_to(100, 150)
        vp.set_zoom(2.0)
        local = vp.screen_to_local((50, 60))
        back = vp.local_to_screen(local)
        self.assertAlmostEqual(50.0, back[0], places=4)
        self.assertAlmostEqual(60.0, back[1], places=4)


# ===========================================================================
# Viewport — content/viewport size update
# ===========================================================================


class TestViewportSizeUpdate(unittest.TestCase):
    def test_set_content_size(self):
        vp = Viewport()
        vp.set_content_size(800, 600)
        self.assertEqual((800, 600), vp.content_size)

    def test_set_viewport_size(self):
        vp = Viewport()
        vp.set_viewport_size(1280, 720)
        self.assertEqual((1280, 720), vp.viewport_size)


# ===========================================================================
# Breakpoint
# ===========================================================================


class TestBreakpoint(unittest.TestCase):
    def test_fields_stored(self):
        bp = Breakpoint(name="medium", min_width=480, layout="flex")
        self.assertEqual("medium", bp.name)
        self.assertEqual(480, bp.min_width)
        self.assertEqual("flex", bp.layout)


# ===========================================================================
# ResponsiveLayout — initial state
# ===========================================================================


class TestResponsiveLayoutInitial(unittest.TestCase):
    def test_active_layout_is_default(self):
        layout = object()
        rl = ResponsiveLayout(default_layout=layout)
        self.assertIs(layout, rl.active_layout)

    def test_active_breakpoint_name_default(self):
        rl = ResponsiveLayout()
        self.assertEqual("default", rl.active_breakpoint.value)

    def test_current_width_zero(self):
        rl = ResponsiveLayout()
        self.assertEqual(0, rl.current_width)

    def test_breakpoints_empty(self):
        rl = ResponsiveLayout()
        self.assertEqual([], rl.breakpoints)


# ===========================================================================
# ResponsiveLayout — add_breakpoint / update
# ===========================================================================


class TestResponsiveLayoutUpdate(unittest.TestCase):
    def setUp(self):
        self.narrow = "narrow_layout"
        self.wide = "wide_layout"
        self.rl = ResponsiveLayout(default_layout=self.narrow)
        self.rl.add_breakpoint(Breakpoint("wide", min_width=800, layout=self.wide))
        self.rl.add_breakpoint(Breakpoint("medium", min_width=480, layout="medium_layout"))

    def test_breakpoints_sorted_widest_first(self):
        bps = self.rl.breakpoints
        self.assertEqual("wide", bps[0].name)
        self.assertEqual("medium", bps[1].name)

    def test_update_selects_wide(self):
        changed = self.rl.update(1024)
        self.assertTrue(changed)
        self.assertEqual("wide", self.rl.active_breakpoint.value)
        self.assertEqual(self.wide, self.rl.active_layout)

    def test_update_selects_medium(self):
        self.rl.update(600)
        self.assertEqual("medium", self.rl.active_breakpoint.value)

    def test_update_falls_back_to_default(self):
        self.rl.update(100)
        self.assertEqual("default", self.rl.active_breakpoint.value)
        self.assertEqual(self.narrow, self.rl.active_layout)

    def test_update_returns_false_when_same(self):
        self.rl.update(1024)
        changed = self.rl.update(900)
        self.assertFalse(changed)

    def test_invalid_breakpoint_raises(self):
        with self.assertRaises(TypeError):
            self.rl.add_breakpoint("not_a_breakpoint")

    def test_current_width_updated(self):
        self.rl.update(640)
        self.assertEqual(640, self.rl.current_width)

    def test_set_default_layout(self):
        new_default = "new_default"
        self.rl.set_default_layout(new_default)
        self.rl.update(100)  # below all breakpoints
        self.assertEqual(new_default, self.rl.active_layout)


if __name__ == "__main__":
    unittest.main()
