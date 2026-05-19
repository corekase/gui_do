import types
import unittest

import pygame
from pygame import Rect

from gui_do.graphics.shear_window import ShearWindowController


pygame.init()


class _StubWindow:
    def __init__(self):
        self.rect = Rect(10, 10, 120, 80)


class TestShearWindowControllerReleaseRefresh(unittest.TestCase):
    def test_end_drag_defers_buffer_refresh_until_render(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        refresh_calls = []

        def fake_refresh(this, _surface, _theme, _draw_window_standard):
            refresh_calls.append(1)
            this.buffer = pygame.Surface(this.window.rect.size, pygame.SRCALPHA)

        controller._refresh_buffer = types.MethodType(fake_refresh, controller)

        controller.start_drag((40, 40), surface=None)
        controller.update_drag((56, 42))
        controller.end_drag((60, 43))

        self.assertEqual(0, len(refresh_calls))

        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertEqual(1, len(refresh_calls))

    def test_settle_render_keeps_refreshing_live_content(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        refresh_calls = []

        def fake_refresh(this, _surface, _theme, _draw_window_standard):
            refresh_calls.append(1)
            this.buffer = pygame.Surface(this.window.rect.size, pygame.SRCALPHA)

        controller._refresh_buffer = types.MethodType(fake_refresh, controller)

        controller.start_drag((40, 40), surface=None)
        controller.update_drag((58, 41))
        controller.end_drag((61, 42))

        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)

        self.assertGreaterEqual(len(refresh_calls), 2)


class TestShearWindowControllerAutoQuality(unittest.TestCase):
    def test_auto_quality_degrades_when_render_time_is_high(self):
        window = _StubWindow()
        controller = ShearWindowController(window)

        controller._auto_quality_hold_frames = 0
        controller._auto_render_ms_ema = controller._auto_degrade_threshold_ms[0] + 0.5
        controller._update_auto_quality(controller._auto_degrade_threshold_ms[0] + 0.5)

        self.assertEqual(1, controller._auto_quality_level)

        controller._auto_quality_hold_frames = 0
        controller._auto_render_ms_ema = controller._auto_degrade_threshold_ms[1] + 0.5
        controller._update_auto_quality(controller._auto_degrade_threshold_ms[1] + 0.5)

        self.assertEqual(2, controller._auto_quality_level)

    def test_auto_quality_upgrades_when_render_time_is_low(self):
        window = _StubWindow()
        controller = ShearWindowController(window)

        controller._auto_quality_level = 2
        controller._auto_quality_hold_frames = 0
        controller._auto_render_ms_ema = controller._auto_upgrade_threshold_ms[2] - 0.5
        controller._update_auto_quality(controller._auto_upgrade_threshold_ms[2] - 0.5)
        self.assertEqual(1, controller._auto_quality_level)

        controller._auto_quality_hold_frames = 0
        controller._auto_render_ms_ema = controller._auto_upgrade_threshold_ms[1] - 0.5
        controller._update_auto_quality(controller._auto_upgrade_threshold_ms[1] - 0.5)
        self.assertEqual(0, controller._auto_quality_level)

    def test_quality_params_shift_with_auto_level(self):
        window = _StubWindow()
        controller = ShearWindowController(window)

        controller._auto_quality_level = 0
        high = controller._current_quality_params()
        controller._auto_quality_level = 1
        balanced = controller._current_quality_params()
        controller._auto_quality_level = 2
        perf = controller._current_quality_params()

        self.assertGreaterEqual(balanced[0], high[0])
        self.assertGreaterEqual(perf[0], balanced[0])
        self.assertGreaterEqual(balanced[1], high[1])
        self.assertGreaterEqual(perf[1], balanced[1])
        self.assertLessEqual(balanced[2], high[2])
        self.assertLessEqual(perf[2], balanced[2])
        self.assertLessEqual(balanced[3], high[3])
        self.assertLessEqual(perf[3], balanced[3])


class TestShearWindowControllerSurfaceCaching(unittest.TestCase):
    def test_buffer_reuses_when_window_shrinks_and_grows_on_demand(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller.buffer)
        first_buffer = controller.buffer
        self.assertEqual((120, 80), controller._buffer_size)

        window.rect.size = (100, 60)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_buffer, controller.buffer)
        self.assertEqual((120, 80), controller._buffer_size)

        window.rect.size = (150, 90)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNot(first_buffer, controller.buffer)
        self.assertEqual((150, 90), controller._buffer_size)

    def test_scratch_reuses_when_render_target_shrinks_and_grows_on_demand(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller._scratch)
        first_scratch = controller._scratch
        self.assertEqual((300, 200), controller._scratch_size)

        smaller = pygame.Surface((240, 160), pygame.SRCALPHA)
        controller._refresh_buffer(smaller, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_scratch, controller._scratch)
        self.assertEqual((300, 200), controller._scratch_size)

        larger = pygame.Surface((360, 220), pygame.SRCALPHA)
        controller._refresh_buffer(larger, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNot(first_scratch, controller._scratch)
        self.assertEqual((360, 220), controller._scratch_size)

    def test_dispose_releases_cached_surfaces(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller.start_drag((30, 30), surface=surface)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller.buffer)
        self.assertIsNotNone(controller._scratch)

        controller.dispose()

        self.assertIsNone(controller.buffer)
        self.assertEqual((0, 0), controller._buffer_size)
        self.assertIsNone(controller._scratch)
        self.assertEqual((0, 0), controller._scratch_size)
        self.assertFalse(controller.active)
        self.assertFalse(controller.dragging)


if __name__ == "__main__":
    unittest.main()
