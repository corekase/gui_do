"""Tests for TileSet and TileMap."""
import unittest

import pygame
from pygame import Rect, Surface

from gui_do.graphics.tile_map import TileSet, TileMap


def _atlas(cols: int, rows: int, tile_w: int = 16, tile_h: int = 16) -> Surface:
    """Create a blank surface big enough for cols×rows tiles."""
    pygame.init()
    return Surface((cols * tile_w, rows * tile_h))


class TestTileSetBasic(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_tile_count(self) -> None:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        self.assertEqual(ts.tile_count, 8)

    def test_invalid_tile_size_raises(self) -> None:
        atlas = _atlas(1, 1)
        with self.assertRaises(ValueError):
            TileSet(atlas, tile_w=0, tile_h=16)

    def test_tile_surface_returns_subsurface(self) -> None:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        surf = ts.tile_surface(0)
        self.assertIsInstance(surf, Surface)
        self.assertEqual(surf.get_size(), (16, 16))

    def test_tile_surface_out_of_range_raises(self) -> None:
        atlas = _atlas(2, 1, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        with self.assertRaises((IndexError, ValueError)):
            ts.tile_surface(99)

    def test_empty_sentinel(self) -> None:
        self.assertEqual(TileSet.EMPTY, -1)

    def test_tile_surface_cached(self) -> None:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        s1 = ts.tile_surface(0)
        s2 = ts.tile_surface(0)
        self.assertIs(s1, s2)


class TestTileMapConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _make(self, cols: int = 10, rows: int = 8) -> TileMap:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        return TileMap(tile_w=16, tile_h=16, cols=cols, rows=rows, tile_set=ts)

    def test_dimensions(self) -> None:
        m = self._make(10, 8)
        self.assertEqual(m.cols, 10)
        self.assertEqual(m.rows, 8)

    def test_pixel_size(self) -> None:
        m = self._make(10, 8)
        self.assertEqual(m.pixel_width, 160)
        self.assertEqual(m.pixel_height, 128)

    def test_initial_tiles_empty(self) -> None:
        m = self._make(4, 4)
        for c in range(4):
            for r in range(4):
                self.assertEqual(m.tile_at(c, r), TileSet.EMPTY)


class TestTileMapSetAndFill(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _make(self) -> TileMap:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        return TileMap(tile_w=16, tile_h=16, cols=6, rows=6, tile_set=ts)

    def test_set_tile(self) -> None:
        m = self._make()
        m.set_tile(2, 3, 1)
        self.assertEqual(m.tile_at(2, 3), 1)

    def test_fill(self) -> None:
        m = self._make()
        m.fill(0)
        for c in range(6):
            for r in range(6):
                self.assertEqual(m.tile_at(c, r), 0)

    def test_fill_rect(self) -> None:
        m = self._make()
        m.fill_rect(1, 1, 3, 2, tile_id=2)
        self.assertEqual(m.tile_at(1, 1), 2)
        self.assertEqual(m.tile_at(3, 2), 2)
        # Tile outside fill_rect should be unchanged
        self.assertEqual(m.tile_at(0, 0), TileSet.EMPTY)

    def test_clear_resets_to_empty(self) -> None:
        m = self._make()
        m.fill(3)
        m.clear()
        self.assertEqual(m.tile_at(0, 0), TileSet.EMPTY)


class TestTileMapWorldConversions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _make(self) -> TileMap:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        return TileMap(tile_w=16, tile_h=16, cols=8, rows=8, tile_set=ts)

    def test_world_to_tile(self) -> None:
        m = self._make()
        col, row = m.world_to_tile(32, 48)
        self.assertEqual(col, 2)
        self.assertEqual(row, 3)

    def test_tile_to_world(self) -> None:
        m = self._make()
        wx, wy = m.tile_to_world(2, 3)
        self.assertEqual(wx, 32)
        self.assertEqual(wy, 48)

    def test_tile_at_out_of_bounds_returns_none(self) -> None:
        m = self._make()
        self.assertIsNone(m.tile_at(-1, 0))
        self.assertIsNone(m.tile_at(0, -1))
        self.assertIsNone(m.tile_at(99, 0))


class TestTileMapVisibleRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_visible_range_clips_to_grid(self) -> None:
        atlas = _atlas(4, 2, 16, 16)
        ts = TileSet(atlas, tile_w=16, tile_h=16)
        m = TileMap(tile_w=16, tile_h=16, cols=10, rows=10, tile_set=ts)
        camera = Rect(0, 0, 32, 32)
        col_start, col_end, row_start, row_end = m.visible_range(camera)
        self.assertEqual(col_start, 0)
        self.assertEqual(row_start, 0)


class TestTileMapTileSetReplaceable(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_tileset_settable(self) -> None:
        atlas = _atlas(4, 2, 16, 16)
        ts1 = TileSet(atlas, tile_w=16, tile_h=16)
        ts2 = TileSet(atlas, tile_w=16, tile_h=16)
        m = TileMap(tile_w=16, tile_h=16, cols=4, rows=4, tile_set=ts1)
        m.tile_set = ts2
        self.assertIs(m.tile_set, ts2)
