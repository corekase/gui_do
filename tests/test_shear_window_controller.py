import types
import unittest

import pygame
from pygame import Rect

from gui_do.graphics.shear_window import ShearWindowController
from gui_do.graphics.window_effect_scratch_pad import WindowEffectScratchPad


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
    def setUp(self):
        WindowEffectScratchPad.dispose_all()

    def test_buffer_allocates_growth_headroom_and_reuses_within_capacity(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller.buffer)
        first_buffer = controller.buffer
        self.assertEqual((180, 120), controller._buffer_size)

        window.rect.size = (100, 60)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_buffer, controller.buffer)
        self.assertEqual((180, 120), controller._buffer_size)

        window.rect.size = (150, 90)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_buffer, controller.buffer)
        self.assertEqual((180, 120), controller._buffer_size)

        window.rect.size = (200, 130)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNot(first_buffer, controller.buffer)
        self.assertEqual((300, 195), controller._buffer_size)

    def test_scratch_allocates_growth_headroom_and_reuses_within_capacity(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller._scratch)
        first_scratch = controller._scratch
        self.assertEqual((450, 300), controller._scratch_size)

        smaller = pygame.Surface((240, 160), pygame.SRCALPHA)
        controller._refresh_buffer(smaller, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_scratch, controller._scratch)
        self.assertEqual((450, 300), controller._scratch_size)

        larger = pygame.Surface((360, 220), pygame.SRCALPHA)
        controller._refresh_buffer(larger, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIs(first_scratch, controller._scratch)
        self.assertEqual((450, 300), controller._scratch_size)

        largest = pygame.Surface((520, 340), pygame.SRCALPHA)
        controller._refresh_buffer(largest, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNot(first_scratch, controller._scratch)
        self.assertEqual((780, 510), controller._scratch_size)

    def test_buffer_enlarge_drops_old_surface_reference(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        old_buffer = controller.buffer
        self.assertIsNotNone(old_buffer)

        window.rect.size = (200, 130)
        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)

        self.assertIsNot(controller.buffer, old_buffer)
        self.assertIsNot(
            WindowEffectScratchPad.get_surface(ShearWindowController._BUFFER_SLOT),
            old_buffer,
        )

    def test_scratch_enlarge_drops_old_surface_reference(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        old_scratch = controller._scratch
        self.assertIsNotNone(old_scratch)

        larger = pygame.Surface((520, 340), pygame.SRCALPHA)
        controller._refresh_buffer(larger, theme=object(), draw_window_standard=lambda _s, _t: None)

        self.assertIsNot(controller._scratch, old_scratch)
        self.assertIsNot(
            WindowEffectScratchPad.get_surface(ShearWindowController._SCRATCH_SLOT),
            old_scratch,
        )

    def test_surface_pool_is_shared_across_controllers(self):
        controller_a = ShearWindowController(_StubWindow())
        controller_b = ShearWindowController(_StubWindow())
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller_a._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)

        self.assertIs(controller_a.buffer, controller_b.buffer)
        self.assertIs(controller_a._scratch, controller_b._scratch)

    def test_pool_survives_until_last_controller_is_disposed(self):
        controller_a = ShearWindowController(_StubWindow())
        controller_b = ShearWindowController(_StubWindow())
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        controller_a._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertIsNotNone(controller_a.buffer)
        self.assertEqual(2, WindowEffectScratchPad._refcount)

        controller_a.dispose()
        self.assertEqual(1, WindowEffectScratchPad._refcount)
        self.assertIsNotNone(controller_b.buffer)

        controller_b.dispose()
        self.assertEqual(0, WindowEffectScratchPad._refcount)
        self.assertIsNone(WindowEffectScratchPad.get_surface(ShearWindowController._BUFFER_SLOT))
        self.assertIsNone(WindowEffectScratchPad.get_surface(ShearWindowController._SCRATCH_SLOT))
        self.assertEqual((0, 0), WindowEffectScratchPad.get_size(ShearWindowController._BUFFER_SLOT))
        self.assertEqual((0, 0), WindowEffectScratchPad.get_size(ShearWindowController._SCRATCH_SLOT))

    def test_expanded_surface_size_uses_growth_factor(self):
        window = _StubWindow()
        controller = ShearWindowController(window)

        self.assertEqual((180, 120), controller._expanded_surface_size((120, 80)))
        self.assertEqual((1, 1), controller._expanded_surface_size((0, 0)))

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


class TestShearWindowControllerPerformanceGating(unittest.TestCase):
    def test_area_scaled_quality_preserves_finer_vertical_bands_on_large_windows(self):
        window = _StubWindow()
        controller = ShearWindowController(window)

        base_tile_h, base_tile_w, base_overlap, _ = controller._current_quality_params()
        scaled = controller._scaled_quality_for_window(900, 500, base_tile_h, base_tile_w, base_overlap)

        self.assertLessEqual(scaled[0], base_tile_h)
        self.assertGreaterEqual(scaled[1], base_tile_w)
        self.assertLessEqual(scaled[2], base_overlap)

    def test_area_scaled_quality_caps_tile_height_to_banding_target(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        controller._auto_quality_level = 0

        scaled = controller._scaled_quality_for_window(900, 500, tile_h=24, tile_w=16, overlap_px=4)
        max_tile_h = 10  # ceil(500 / 52)
        self.assertLessEqual(scaled[0], max_tile_h)

    def test_per_pixel_shear_disabled_for_large_windows(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        controller._auto_quality_level = 0

        self.assertFalse(
            controller._should_use_per_pixel_shear(
                h=520,
                tile_h=10,
                max_shear_extent=96,
                area=520 * 820,
            )
        )

    def test_per_pixel_shear_disabled_when_auto_quality_not_high(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        controller._auto_quality_level = 1

        self.assertFalse(
            controller._should_use_per_pixel_shear(
                h=180,
                tile_h=10,
                max_shear_extent=96,
                area=180 * 260,
            )
        )

    def test_per_pixel_shear_allowed_for_small_high_quality_windows(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        controller._auto_quality_level = 0

        self.assertTrue(
            controller._should_use_per_pixel_shear(
                h=180,
                tile_h=10,
                max_shear_extent=96,
                area=180 * 220,
            )
        )


if __name__ == "__main__":
    unittest.main()
