"""Tests for SpriteSheet/FrameAnimation and SurfaceCompositor/Layer.

pygame.Surface works without a display; no pygame.display.init() is needed.
"""
import unittest

import pygame
from pygame import Surface

from gui_do.graphics.sprite_sheet import FrameAnimation, SpriteSheet
from gui_do.graphics.surface_compositor import Layer, SurfaceCompositor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sheet(frame_w=16, frame_h=16, cols=4, rows=2) -> SpriteSheet:
    """Create a SpriteSheet backed by a plain surface atlas."""
    surf = Surface((frame_w * cols, frame_h * rows))
    surf.fill((0, 128, 255))
    return SpriteSheet(surf, frame_w, frame_h)


def _anim(sheet=None, frames=None, fps=12.0, loop=True) -> FrameAnimation:
    if sheet is None:
        sheet = _sheet()
    if frames is None:
        frames = [0, 1, 2, 3]
    return FrameAnimation(sheet, frames, fps, loop=loop)


# ===========================================================================
# SpriteSheet
# ===========================================================================


class TestSpriteSheetProperties(unittest.TestCase):
    def setUp(self):
        # 4 cols × 2 rows of 16×16 → 8 frames
        self.sheet = _sheet(frame_w=16, frame_h=16, cols=4, rows=2)

    def test_frame_count(self):
        self.assertEqual(8, self.sheet.frame_count)

    def test_frame_w(self):
        self.assertEqual(16, self.sheet.frame_w)

    def test_frame_h(self):
        self.assertEqual(16, self.sheet.frame_h)

    def test_invalid_frame_w_raises(self):
        with self.assertRaises(ValueError):
            SpriteSheet(Surface((64, 64)), 0, 16)

    def test_invalid_frame_h_raises(self):
        with self.assertRaises(ValueError):
            SpriteSheet(Surface((64, 64)), 16, 0)


class TestSpriteSheetFrameAccess(unittest.TestCase):
    def setUp(self):
        self.sheet = _sheet(frame_w=16, frame_h=16, cols=4, rows=2)

    def test_frame_returns_surface(self):
        self.assertIsInstance(self.sheet.frame(0), Surface)

    def test_frame_out_of_range_raises(self):
        with self.assertRaises(IndexError):
            self.sheet.frame(8)

    def test_frame_negative_raises(self):
        with self.assertRaises(IndexError):
            self.sheet.frame(-1)

    def test_frame_cached(self):
        f1 = self.sheet.frame(2)
        f2 = self.sheet.frame(2)
        self.assertIs(f1, f2)

    def test_frames_returns_list(self):
        result = self.sheet.frames([0, 1, 2])
        self.assertEqual(3, len(result))
        for s in result:
            self.assertIsInstance(s, Surface)

    def test_frame_correct_size(self):
        f = self.sheet.frame(0)
        self.assertEqual((16, 16), f.get_size())


# ===========================================================================
# FrameAnimation — construction
# ===========================================================================


class TestFrameAnimationConstruction(unittest.TestCase):
    def test_empty_frames_raises(self):
        sheet = _sheet()
        with self.assertRaises(ValueError):
            FrameAnimation(sheet, [], fps=12)

    def test_zero_fps_raises(self):
        sheet = _sheet()
        with self.assertRaises(ValueError):
            FrameAnimation(sheet, [0, 1], fps=0)

    def test_negative_fps_raises(self):
        sheet = _sheet()
        with self.assertRaises(ValueError):
            FrameAnimation(sheet, [0, 1], fps=-5)

    def test_initially_playing(self):
        self.assertTrue(_anim().is_playing)

    def test_initially_not_complete(self):
        self.assertFalse(_anim().is_complete)

    def test_initial_frame_index(self):
        self.assertEqual(0, _anim().current_frame_index)

    def test_frames_list(self):
        anim = _anim(frames=[3, 1, 2])
        self.assertEqual([3, 1, 2], anim.frames)


# ===========================================================================
# FrameAnimation — playback control
# ===========================================================================


class TestFrameAnimationPlayback(unittest.TestCase):
    def setUp(self):
        self.sheet = _sheet()
        self.anim = _anim(sheet=self.sheet, frames=[0, 1, 2, 3], fps=4.0, loop=True)

    def test_pause_stops_advancing(self):
        self.anim.pause()
        self.anim.update(10.0)
        self.assertEqual(0, self.anim.current_frame_index)
        self.assertFalse(self.anim.is_playing)

    def test_play_resumes(self):
        self.anim.pause()
        self.anim.play()
        self.assertTrue(self.anim.is_playing)

    def test_reset_goes_to_frame_zero(self):
        self.anim.update(0.5)
        self.anim.reset()
        self.assertEqual(0, self.anim.current_frame_index)
        self.assertTrue(self.anim.is_playing)
        self.assertFalse(self.anim.is_complete)

    def test_seek_frame_valid(self):
        self.anim.seek_frame(2)
        self.assertEqual(2, self.anim.current_frame_index)

    def test_seek_frame_out_of_range_raises(self):
        with self.assertRaises(IndexError):
            self.anim.seek_frame(99)

    def test_current_surface_is_surface(self):
        self.assertIsInstance(self.anim.current_surface, Surface)


# ===========================================================================
# FrameAnimation — update / advance
# ===========================================================================


class TestFrameAnimationUpdate(unittest.TestCase):
    def setUp(self):
        self.sheet = _sheet()

    def test_advances_frame_over_time(self):
        # fps=4 → 0.25 s per frame
        anim = _anim(sheet=self.sheet, frames=[0, 1, 2, 3], fps=4.0, loop=True)
        anim.update(0.26)
        self.assertEqual(1, anim.current_frame_index)

    def test_wraps_when_looping(self):
        anim = _anim(sheet=self.sheet, frames=[0, 1, 2, 3], fps=4.0, loop=True)
        # 5 frames × 0.25s = 1.25 s → wraps back to frame 1
        anim.update(1.26)
        self.assertTrue(anim.is_playing)

    def test_non_loop_completes(self):
        anim = FrameAnimation(self.sheet, [0, 1, 2], fps=4.0, loop=False)
        # 3 frames × 0.25s = 0.75 s
        anim.update(1.0)
        self.assertTrue(anim.is_complete)
        self.assertFalse(anim.is_playing)

    def test_non_loop_stays_on_last_frame(self):
        anim = FrameAnimation(self.sheet, [0, 1, 2], fps=4.0, loop=False)
        anim.update(1.0)
        self.assertEqual(2, anim.current_frame_index)

    def test_on_complete_callback_looping(self):
        calls = []
        anim = FrameAnimation(
            self.sheet, [0, 1], fps=4.0, loop=True, on_complete=lambda: calls.append(1)
        )
        anim.update(0.6)   # > 2 × 0.25 s → one full loop completed
        self.assertEqual(1, len(calls))

    def test_on_complete_callback_non_looping(self):
        calls = []
        anim = FrameAnimation(
            self.sheet, [0, 1], fps=4.0, loop=False, on_complete=lambda: calls.append(1)
        )
        anim.update(1.0)
        self.assertEqual(1, len(calls))

    def test_completed_animation_does_not_re_fire_callback(self):
        calls = []
        anim = FrameAnimation(
            self.sheet, [0, 1], fps=4.0, loop=False, on_complete=lambda: calls.append(1)
        )
        anim.update(1.0)
        anim.update(1.0)
        self.assertEqual(1, len(calls))


# ===========================================================================
# Layer
# ===========================================================================


class TestLayer(unittest.TestCase):
    def test_name(self):
        layer = Layer("bg", (64, 64))
        self.assertEqual("bg", layer.name)

    def test_z_index(self):
        layer = Layer("fg", (64, 64), z_index=10)
        self.assertEqual(10, layer.z_index)

    def test_opacity_default(self):
        layer = Layer("x", (64, 64))
        self.assertAlmostEqual(1.0, layer.opacity)

    def test_opacity_clamped_to_range(self):
        layer = Layer("x", (64, 64), opacity=1.5)
        self.assertAlmostEqual(1.0, layer.opacity)
        layer.opacity = -0.5
        self.assertAlmostEqual(0.0, layer.opacity)

    def test_visible_default_true(self):
        self.assertTrue(Layer("x", (64, 64)).visible)

    def test_visible_false(self):
        layer = Layer("x", (64, 64), visible=False)
        self.assertFalse(layer.visible)

    def test_surface_has_correct_size(self):
        layer = Layer("x", (80, 60))
        self.assertEqual((80, 60), layer.surface.get_size())

    def test_resize_updates_surface_size(self):
        layer = Layer("x", (64, 64))
        layer.resize((128, 96))
        self.assertEqual((128, 96), layer.surface.get_size())


# ===========================================================================
# SurfaceCompositor — layer management
# ===========================================================================


class TestSurfaceCompositorLayerManagement(unittest.TestCase):
    def setUp(self):
        self.comp = SurfaceCompositor((256, 256))

    def test_initially_no_layers(self):
        self.assertEqual([], self.comp.layer_names())

    def test_add_layer_returns_layer(self):
        layer = self.comp.add_layer("scene")
        self.assertIsInstance(layer, Layer)

    def test_has_layer_true(self):
        self.comp.add_layer("scene")
        self.assertTrue(self.comp.has_layer("scene"))

    def test_has_layer_false(self):
        self.assertFalse(self.comp.has_layer("ghost"))

    def test_duplicate_layer_name_raises(self):
        self.comp.add_layer("bg")
        with self.assertRaises(ValueError):
            self.comp.add_layer("bg")

    def test_remove_layer(self):
        self.comp.add_layer("bg")
        self.comp.remove_layer("bg")
        self.assertFalse(self.comp.has_layer("bg"))

    def test_remove_missing_layer_no_error(self):
        self.comp.remove_layer("ghost")  # should not raise

    def test_layer_names_in_z_order(self):
        self.comp.add_layer("top", z_index=10)
        self.comp.add_layer("bottom", z_index=0)
        self.comp.add_layer("mid", z_index=5)
        self.assertEqual(["bottom", "mid", "top"], self.comp.layer_names())

    def test_layer_surface_returns_surface(self):
        self.comp.add_layer("scene")
        self.assertIsInstance(self.comp.layer_surface("scene"), Surface)

    def test_layer_returns_layer_object(self):
        added = self.comp.add_layer("bg")
        self.assertIs(added, self.comp.layer("bg"))


# ===========================================================================
# SurfaceCompositor — controls
# ===========================================================================


class TestSurfaceCompositorControls(unittest.TestCase):
    def setUp(self):
        self.comp = SurfaceCompositor((64, 64))
        self.comp.add_layer("a", z_index=0)
        self.comp.add_layer("b", z_index=5)

    def test_set_layer_visible_false(self):
        self.comp.set_layer_visible("a", False)
        self.assertFalse(self.comp.layer("a").visible)

    def test_set_layer_visible_true(self):
        self.comp.set_layer_visible("a", False)
        self.comp.set_layer_visible("a", True)
        self.assertTrue(self.comp.layer("a").visible)

    def test_set_layer_opacity(self):
        self.comp.set_layer_opacity("a", 0.5)
        self.assertAlmostEqual(0.5, self.comp.layer("a").opacity)

    def test_set_layer_z_changes_order(self):
        self.comp.set_layer_z("a", 100)
        self.assertEqual(["b", "a"], self.comp.layer_names())

    def test_resize_updates_all_layers(self):
        self.comp.resize((128, 128))
        self.assertEqual((128, 128), self.comp.layer_surface("a").get_size())
        self.assertEqual((128, 128), self.comp.layer_surface("b").get_size())


if __name__ == "__main__":
    unittest.main()
