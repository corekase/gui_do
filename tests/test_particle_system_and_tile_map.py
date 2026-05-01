"""Tests for ParticleSystem/Emitter and TileMap/TileSet grid logic.

ParticleSystem.update() simulation and emitter management are pure Python
(no display required).

TileSet requires a pygame.Surface for the atlas, but pygame.Surface works
without a display.  TileMap grid operations (set_tile, fill, world_to_tile,
visible_range, dirty_tiles) are pure integer arithmetic.
"""
import unittest

import pygame
from pygame import Rect

from gui_do.graphics.particle_system import Emitter, ParticleSystem
from gui_do.graphics.tile_map import TileMap, TileSet


# ===========================================================================
# Helpers
# ===========================================================================


def _make_atlas(tile_w: int = 16, tile_h: int = 16, cols: int = 4, rows: int = 4) -> pygame.Surface:
    """Create a minimal solid-colour atlas surface."""
    surf = pygame.Surface((tile_w * cols, tile_h * rows))
    surf.fill((128, 128, 128))
    return surf


def _tileset(tile_w: int = 16, tile_h: int = 16) -> TileSet:
    return TileSet(_make_atlas(tile_w, tile_h), tile_w, tile_h)


def _tilemap(cols: int = 8, rows: int = 6, tile_w: int = 16, tile_h: int = 16) -> TileMap:
    return TileMap(tile_w, tile_h, cols, rows, _tileset(tile_w, tile_h))


def _burst_emitter(x=0, y=0, count=10) -> Emitter:
    return Emitter(
        x=x, y=y,
        rate=0,
        burst_count=count,
        lifetime=(1.0, 1.0),
        speed=(10.0, 10.0),
        angle_range=(0.0, 0.0),
        size=(4.0, 2.0),
        gravity=0.0,
    )


def _rate_emitter(rate=100.0) -> Emitter:
    return Emitter(
        x=0, y=0,
        rate=rate,
        burst_count=0,
        lifetime=(10.0, 10.0),
        speed=(10.0, 10.0),
        angle_range=(0.0, 360.0),
        size=(4.0, 4.0),
        gravity=0.0,
    )


# ===========================================================================
# ParticleSystem — emitter management
# ===========================================================================


class TestParticleSystemEmitterManagement(unittest.TestCase):
    def setUp(self):
        self.ps = ParticleSystem(max_particles=100)

    def test_initially_no_emitters(self):
        self.assertEqual(0, self.ps.emitter_count)

    def test_add_emitter(self):
        self.ps.add_emitter(_rate_emitter())
        self.assertEqual(1, self.ps.emitter_count)

    def test_add_duplicate_emitter_ignored(self):
        em = _rate_emitter()
        self.ps.add_emitter(em)
        self.ps.add_emitter(em)
        self.assertEqual(1, self.ps.emitter_count)

    def test_remove_emitter(self):
        em = _rate_emitter()
        self.ps.add_emitter(em)
        self.ps.remove_emitter(em)
        self.assertEqual(0, self.ps.emitter_count)

    def test_remove_missing_emitter_no_error(self):
        self.ps.remove_emitter(_rate_emitter())  # should not raise

    def test_clear_removes_emitters(self):
        self.ps.add_emitter(_rate_emitter())
        self.ps.add_emitter(_burst_emitter())
        self.ps.clear()
        self.assertEqual(0, self.ps.emitter_count)


# ===========================================================================
# ParticleSystem — simulation (burst)
# ===========================================================================


class TestParticleSystemBurstSimulation(unittest.TestCase):
    def setUp(self):
        self.ps = ParticleSystem(max_particles=200)

    def test_initially_no_active_particles(self):
        self.assertEqual(0, self.ps.active_particle_count)

    def test_burst_spawns_particles_on_update(self):
        em = _burst_emitter(count=5)
        self.ps.add_emitter(em)
        self.ps.update(0.016)
        self.assertEqual(5, self.ps.active_particle_count)

    def test_burst_only_fires_once(self):
        em = _burst_emitter(count=3)
        self.ps.add_emitter(em)
        self.ps.update(0.016)
        count_after_first = self.ps.active_particle_count
        self.ps.update(0.016)
        self.assertEqual(count_after_first, self.ps.active_particle_count)

    def test_manual_burst_adds_particles(self):
        em = Emitter(x=0, y=0, rate=0, burst_count=0,
                     lifetime=(10.0, 10.0), speed=(1.0, 1.0))
        self.ps.add_emitter(em)
        self.ps.burst(em, count=4)
        self.ps.update(0.016)
        self.assertEqual(4, self.ps.active_particle_count)

    def test_particles_expire_over_time(self):
        em = _burst_emitter(count=5)
        em.lifetime = (0.1, 0.1)
        self.ps.add_emitter(em)
        self.ps.update(0.016)
        self.assertEqual(5, self.ps.active_particle_count)
        # Advance past lifetime
        self.ps.update(0.5)
        self.assertEqual(0, self.ps.active_particle_count)

    def test_clear_kills_all_particles(self):
        em = _burst_emitter(count=10)
        self.ps.add_emitter(em)
        self.ps.update(0.016)
        self.assertGreater(self.ps.active_particle_count, 0)
        self.ps.clear()
        self.assertEqual(0, self.ps.active_particle_count)

    def test_max_particles_cap(self):
        ps = ParticleSystem(max_particles=3)
        em = _burst_emitter(count=20)
        ps.add_emitter(em)
        ps.update(0.016)
        self.assertLessEqual(ps.active_particle_count, 3)

    def test_gravity_applied_to_vy(self):
        em = Emitter(
            x=0, y=0, rate=0, burst_count=1,
            lifetime=(10.0, 10.0),
            speed=(0.0, 0.0),   # stationary spawn
            angle_range=(0.0, 0.0),
            size=(4.0, 4.0),
            gravity=200.0,
        )
        self.ps.add_emitter(em)
        self.ps.update(0.0)    # spawn
        # Find the live particle
        live = [p for p in self.ps._particles if p.alive]
        self.assertEqual(1, len(live))
        initial_y = live[0].y
        self.ps.update(0.1)
        # y should have increased due to gravity
        self.assertGreater(live[0].y, initial_y)


# ===========================================================================
# ParticleSystem — rate-based emission
# ===========================================================================


class TestParticleSystemRateEmission(unittest.TestCase):
    def test_rate_emitter_spawns_particles_over_time(self):
        ps = ParticleSystem(max_particles=200)
        em = _rate_emitter(rate=100.0)
        ps.add_emitter(em)
        ps.update(1.0)  # 1 second → ~100 particles
        self.assertGreater(ps.active_particle_count, 0)

    def test_inactive_emitter_emits_nothing(self):
        ps = ParticleSystem(max_particles=200)
        em = _rate_emitter(rate=100.0)
        em.active = False
        ps.add_emitter(em)
        ps.update(1.0)
        self.assertEqual(0, ps.active_particle_count)


# ===========================================================================
# TileSet
# ===========================================================================


class TestTileSet(unittest.TestCase):
    def setUp(self):
        self.ts = _tileset(tile_w=16, tile_h=16)

    def test_tile_count(self):
        # 4×4 atlas of 16×16 tiles → 16 tiles
        self.assertEqual(16, self.ts.tile_count)

    def test_tile_w_and_h(self):
        self.assertEqual(16, self.ts.tile_w)
        self.assertEqual(16, self.ts.tile_h)

    def test_tile_surface_valid_id(self):
        surf = self.ts.tile_surface(0)
        self.assertIsInstance(surf, pygame.Surface)

    def test_tile_surface_last_valid_id(self):
        surf = self.ts.tile_surface(15)
        self.assertIsInstance(surf, pygame.Surface)

    def test_tile_surface_cached(self):
        s1 = self.ts.tile_surface(2)
        s2 = self.ts.tile_surface(2)
        self.assertIs(s1, s2)

    def test_tile_surface_out_of_range_raises(self):
        with self.assertRaises(IndexError):
            self.ts.tile_surface(99)

    def test_tile_surface_negative_raises(self):
        with self.assertRaises(IndexError):
            self.ts.tile_surface(-1)

    def test_invalid_tile_size_raises(self):
        with self.assertRaises(ValueError):
            TileSet(pygame.Surface((64, 64)), 0, 16)


# ===========================================================================
# TileMap — properties
# ===========================================================================


class TestTileMapProperties(unittest.TestCase):
    def setUp(self):
        self.tm = _tilemap(cols=8, rows=6, tile_w=16, tile_h=16)

    def test_cols(self):
        self.assertEqual(8, self.tm.cols)

    def test_rows(self):
        self.assertEqual(6, self.tm.rows)

    def test_tile_w(self):
        self.assertEqual(16, self.tm.tile_w)

    def test_tile_h(self):
        self.assertEqual(16, self.tm.tile_h)

    def test_pixel_width(self):
        self.assertEqual(128, self.tm.pixel_width)

    def test_pixel_height(self):
        self.assertEqual(96, self.tm.pixel_height)

    def test_invalid_tile_size_raises(self):
        with self.assertRaises(ValueError):
            TileMap(0, 16, 8, 6, _tileset())

    def test_invalid_cols_raises(self):
        with self.assertRaises(ValueError):
            TileMap(16, 16, 0, 6, _tileset())


# ===========================================================================
# TileMap — tile data access
# ===========================================================================


class TestTileMapTileAccess(unittest.TestCase):
    def setUp(self):
        self.tm = _tilemap(cols=8, rows=6, tile_w=16, tile_h=16)

    def test_initially_all_empty(self):
        self.assertEqual(TileSet.EMPTY, self.tm.tile_at(0, 0))
        self.assertEqual(TileSet.EMPTY, self.tm.tile_at(7, 5))

    def test_tile_at_out_of_bounds_returns_none(self):
        self.assertIsNone(self.tm.tile_at(99, 99))
        self.assertIsNone(self.tm.tile_at(-1, 0))

    def test_set_tile(self):
        self.tm.set_tile(2, 3, 5)
        self.assertEqual(5, self.tm.tile_at(2, 3))

    def test_set_tile_out_of_bounds_ignored(self):
        self.tm.set_tile(99, 99, 0)  # should not raise

    def test_fill_sets_all(self):
        self.tm.fill(1)
        for row in range(self.tm.rows):
            for col in range(self.tm.cols):
                self.assertEqual(1, self.tm.tile_at(col, row))

    def test_clear_resets_all(self):
        self.tm.fill(3)
        self.tm.clear()
        self.assertEqual(TileSet.EMPTY, self.tm.tile_at(0, 0))

    def test_fill_rect(self):
        self.tm.fill_rect(1, 1, 3, 2, 7)
        for row in range(1, 3):
            for col in range(1, 4):
                self.assertEqual(7, self.tm.tile_at(col, row))
        # Outside region stays empty
        self.assertEqual(TileSet.EMPTY, self.tm.tile_at(0, 0))


# ===========================================================================
# TileMap — coordinate conversion
# ===========================================================================


class TestTileMapCoordinates(unittest.TestCase):
    def setUp(self):
        self.tm = _tilemap(tile_w=32, tile_h=32)

    def test_world_to_tile_origin(self):
        self.assertEqual((0, 0), self.tm.world_to_tile(0, 0))

    def test_world_to_tile_inside(self):
        self.assertEqual((2, 1), self.tm.world_to_tile(64, 32))

    def test_world_to_tile_partial(self):
        # 50px in 32px-wide tiles → col 1
        self.assertEqual((1, 0), self.tm.world_to_tile(50, 10))

    def test_tile_to_world(self):
        self.assertEqual((64, 32), self.tm.tile_to_world(2, 1))

    def test_tile_to_world_origin(self):
        self.assertEqual((0, 0), self.tm.tile_to_world(0, 0))


# ===========================================================================
# TileMap — visible_range
# ===========================================================================


class TestTileMapVisibleRange(unittest.TestCase):
    def setUp(self):
        # 10×8 grid of 32×32 tiles = 320×256 pixels
        self.tm = TileMap(32, 32, 10, 8, _tileset(32, 32))

    def test_full_camera_covers_all(self):
        cam = Rect(0, 0, 320, 256)
        col_start, col_end, row_start, row_end = self.tm.visible_range(cam)
        self.assertEqual(0, col_start)
        self.assertEqual(10, col_end)
        self.assertEqual(0, row_start)
        self.assertEqual(8, row_end)

    def test_camera_aligned_to_tile_boundary(self):
        cam = Rect(32, 64, 64, 64)   # cols 1-2, rows 2-3
        col_start, col_end, row_start, row_end = self.tm.visible_range(cam)
        self.assertEqual(1, col_start)
        self.assertEqual(3, col_end)
        self.assertEqual(2, row_start)
        self.assertEqual(4, row_end)

    def test_camera_clamps_to_grid_bounds(self):
        cam = Rect(-100, -100, 100, 100)
        col_start, col_end, row_start, row_end = self.tm.visible_range(cam)
        self.assertEqual(0, col_start)
        self.assertEqual(0, row_start)


# ===========================================================================
# TileMap — dirty_tiles
# ===========================================================================


class TestTileMapDirtyTiles(unittest.TestCase):
    def setUp(self):
        self.tm = _tilemap(cols=4, rows=3, tile_w=16, tile_h=16)

    def test_empty_map_yields_nothing(self):
        self.assertEqual([], list(self.tm.dirty_tiles()))

    def test_single_tile_yields_one_rect(self):
        self.tm.set_tile(2, 1, 0)
        rects = list(self.tm.dirty_tiles())
        self.assertEqual(1, len(rects))
        self.assertEqual(Rect(32, 16, 16, 16), rects[0])

    def test_filled_map_yields_all_tiles(self):
        self.tm.fill(0)
        rects = list(self.tm.dirty_tiles())
        self.assertEqual(self.tm.cols * self.tm.rows, len(rects))


if __name__ == "__main__":
    unittest.main()
