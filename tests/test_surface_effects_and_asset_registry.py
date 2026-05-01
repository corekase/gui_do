"""Tests for SurfaceEffects and AssetRegistry.

SurfaceEffects tests verify output size, that the call returns a new surface,
and basic pixel-level properties for each effect (no numpy required).

AssetRegistry tests use a temporary PNG file for the surface cache and
exercise the reference counting, hot-reload, and diagnostic APIs.
"""
import tempfile
import time
import unittest
from pathlib import Path

import pygame
from pygame import Surface

from gui_do.graphics.surface_effects import SurfaceEffects
from gui_do.graphics.asset_registry import AssetRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _solid(w: int = 32, h: int = 32, color=(200, 100, 50, 255)) -> Surface:
    """Return a solid-colour SRCALPHA surface."""
    surf = Surface((w, h), pygame.SRCALPHA)
    surf.fill(color)
    return surf


def _write_png(path: Path, w: int = 8, h: int = 8) -> None:
    """Write a minimal PNG surface to *path*."""
    surf = Surface((w, h))
    surf.fill((100, 150, 200))
    pygame.image.save(surf, str(path))


# ===========================================================================
# SurfaceEffects
# ===========================================================================


class TestSurfaceEffectsBlur(unittest.TestCase):
    def setUp(self):
        self.src = _solid(32, 32, (255, 0, 0, 255))

    def test_blur_zero_returns_copy(self):
        result = SurfaceEffects.blur(self.src, 0)
        self.assertIsNot(result, self.src)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_blur_nonzero_same_size(self):
        result = SurfaceEffects.blur(self.src, 4)
        self.assertEqual((32, 32), result.get_size())

    def test_blur_returns_new_surface(self):
        result = SurfaceEffects.blur(self.src, 4)
        self.assertIsNot(result, self.src)

    def test_blur_negative_radius_treated_as_zero(self):
        result = SurfaceEffects.blur(self.src, -5)
        self.assertEqual((32, 32), result.get_size())


class TestSurfaceEffectsGreyscale(unittest.TestCase):
    def setUp(self):
        self.src = _solid(16, 16, (200, 100, 50, 255))

    def test_greyscale_same_size(self):
        result = SurfaceEffects.greyscale(self.src)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_greyscale_returns_new_surface(self):
        result = SurfaceEffects.greyscale(self.src)
        self.assertIsNot(result, self.src)

    def test_greyscale_rgb_channels_equal(self):
        result = SurfaceEffects.greyscale(self.src)
        r, g, b, _ = result.get_at((8, 8))
        self.assertEqual(r, g)
        self.assertEqual(g, b)


class TestSurfaceEffectsTint(unittest.TestCase):
    def setUp(self):
        self.src = _solid(16, 16, (0, 255, 0, 255))

    def test_tint_same_size(self):
        result = SurfaceEffects.tint(self.src, (255, 0, 0), alpha=128)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_tint_returns_new_surface(self):
        result = SurfaceEffects.tint(self.src, (255, 0, 0), alpha=128)
        self.assertIsNot(result, self.src)

    def test_tint_full_alpha_shifts_pixel(self):
        # Full alpha tint completely overwrites the source
        result = SurfaceEffects.tint(self.src, (255, 0, 0), alpha=255)
        r, g, b, _ = result.get_at((8, 8))
        self.assertGreater(r, g)   # red tint dominant

    def test_tint_zero_alpha_no_change(self):
        # Alpha=0 → no overlay → pixel unchanged
        result = SurfaceEffects.tint(self.src, (255, 0, 0), alpha=0)
        orig_r, orig_g, orig_b, _ = self.src.get_at((8, 8))
        r, g, b, _ = result.get_at((8, 8))
        self.assertEqual(orig_g, g)


class TestSurfaceEffectsBrightness(unittest.TestCase):
    def setUp(self):
        self.src = _solid(16, 16, (100, 100, 100, 255))

    def test_brightness_same_size(self):
        result = SurfaceEffects.brightness(self.src, 1.5)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_brightness_returns_new_surface(self):
        result = SurfaceEffects.brightness(self.src, 1.5)
        self.assertIsNot(result, self.src)

    def test_brightness_factor_gt_1_increases_value(self):
        result = SurfaceEffects.brightness(self.src, 2.0)
        r, _, _, _ = result.get_at((8, 8))
        self.assertGreater(r, 100)

    def test_brightness_factor_lt_1_decreases_value(self):
        result = SurfaceEffects.brightness(self.src, 0.5)
        r, _, _, _ = result.get_at((8, 8))
        self.assertLess(r, 100)

    def test_brightness_clamped_at_255(self):
        result = SurfaceEffects.brightness(self.src, 100.0)
        r, _, _, _ = result.get_at((8, 8))
        self.assertEqual(255, r)


class TestSurfaceEffectsPixelate(unittest.TestCase):
    def setUp(self):
        self.src = _solid(32, 32, (80, 160, 240, 255))

    def test_pixelate_same_size(self):
        result = SurfaceEffects.pixelate(self.src, 4)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_pixelate_returns_new_surface(self):
        result = SurfaceEffects.pixelate(self.src, 4)
        self.assertIsNot(result, self.src)

    def test_pixelate_block_size_1_returns_copy(self):
        result = SurfaceEffects.pixelate(self.src, 1)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_pixelate_block_size_negative_returns_copy(self):
        result = SurfaceEffects.pixelate(self.src, -3)
        self.assertEqual(self.src.get_size(), result.get_size())


class TestSurfaceEffectsVignette(unittest.TestCase):
    def setUp(self):
        self.src = _solid(32, 32, (255, 255, 255, 255))

    def test_vignette_same_size(self):
        result = SurfaceEffects.vignette(self.src, strength=0.5)
        self.assertEqual(self.src.get_size(), result.get_size())

    def test_vignette_returns_new_surface(self):
        result = SurfaceEffects.vignette(self.src, strength=0.5)
        self.assertIsNot(result, self.src)

    def test_vignette_strength_zero_no_change(self):
        result = SurfaceEffects.vignette(self.src, strength=0.0)
        r, g, b, _ = result.get_at((16, 16))
        # Centre pixel should remain bright
        self.assertGreater(r, 200)


# ===========================================================================
# AssetRegistry
# ===========================================================================


class TestAssetRegistryInitialState(unittest.TestCase):
    def setUp(self):
        self.reg = AssetRegistry()

    def test_has_surface_false_initially(self):
        self.assertFalse(self.reg.has_surface("anything.png"))

    def test_stats_initially_zero(self):
        s = self.reg.stats()
        self.assertEqual(0, s["surfaces"])
        self.assertEqual(0, s["fonts"])

    def test_clear_on_empty_no_error(self):
        self.reg.clear()  # should not raise


class TestAssetRegistrySurfaceCache(unittest.TestCase):
    def setUp(self):
        self.reg = AssetRegistry()
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.png = self.tmp / "icon.png"
        _write_png(self.png)

    def tearDown(self):
        self._td.cleanup()

    def test_get_surface_loads(self):
        surf = self.reg.get_surface(str(self.png))
        self.assertIsInstance(surf, Surface)

    def test_get_surface_cached_on_second_call(self):
        s1 = self.reg.get_surface(str(self.png))
        s2 = self.reg.get_surface(str(self.png))
        self.assertIs(s1, s2)

    def test_has_surface_true_after_load(self):
        self.reg.get_surface(str(self.png))
        self.assertTrue(self.reg.has_surface(str(self.png)))

    def test_different_sizes_different_slots(self):
        s1 = self.reg.get_surface(str(self.png), size=(16, 16))
        s2 = self.reg.get_surface(str(self.png), size=(32, 32))
        self.assertIsNot(s1, s2)
        self.assertEqual((16, 16), s1.get_size())
        self.assertEqual((32, 32), s2.get_size())

    def test_release_surface_decrements_ref(self):
        self.reg.get_surface(str(self.png))  # ref 1
        self.reg.get_surface(str(self.png))  # ref 2
        self.reg.release_surface(str(self.png))  # ref 1
        self.assertTrue(self.reg.has_surface(str(self.png)))
        self.reg.release_surface(str(self.png))  # ref 0 → evict
        self.assertFalse(self.reg.has_surface(str(self.png)))

    def test_release_missing_surface_no_error(self):
        self.reg.release_surface("nonexistent.png")  # should not raise

    def test_stats_surface_count(self):
        self.reg.get_surface(str(self.png))
        self.assertEqual(1, self.reg.stats()["surfaces"])

    def test_clear_evicts_all_surfaces(self):
        self.reg.get_surface(str(self.png))
        self.reg.clear()
        self.assertFalse(self.reg.has_surface(str(self.png)))
        self.assertEqual(0, self.reg.stats()["surfaces"])


class TestAssetRegistryHotReload(unittest.TestCase):
    def setUp(self):
        self.reg = AssetRegistry(enable_hot_reload=True)
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.png = self.tmp / "icon.png"
        _write_png(self.png)

    def tearDown(self):
        self._td.cleanup()

    def test_no_change_returns_false(self):
        self.reg.get_surface(str(self.png))
        result = self.reg.check_hot_reload()
        self.assertFalse(result)

    def test_changed_file_evicts_and_returns_true(self):
        self.reg.get_surface(str(self.png))
        # Touch the file to change mtime
        time.sleep(0.01)
        _write_png(self.png)
        # Manually bump the mtime recorded in the entry
        import os
        new_mtime = os.stat(str(self.png)).st_mtime
        for entry in self.reg._surfaces.values():
            entry.mtime = new_mtime - 1.0   # make it stale
        result = self.reg.check_hot_reload()
        self.assertTrue(result)
        self.assertFalse(self.reg.has_surface(str(self.png)))

    def test_hot_reload_disabled_always_false(self):
        reg = AssetRegistry(enable_hot_reload=False)
        reg.get_surface(str(self.png))
        self.assertFalse(reg.check_hot_reload())


class TestAssetRegistryBasePathResolution(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.png = self.tmp / "icon.png"
        _write_png(self.png)

    def tearDown(self):
        self._td.cleanup()

    def test_base_path_resolves_relative(self):
        reg = AssetRegistry(base_path=self.tmp)
        surf = reg.get_surface("icon.png")
        self.assertIsInstance(surf, Surface)
        self.assertTrue(reg.has_surface("icon.png"))


if __name__ == "__main__":
    unittest.main()
