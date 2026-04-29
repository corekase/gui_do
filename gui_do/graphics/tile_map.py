"""TileSet + TileMap — atlas-based grid tile renderer with camera culling.

:class:`TileSet` slices a surface atlas into named/indexed tiles.
:class:`TileMap` manages a 2-D grid of tile IDs and renders only the visible
tiles given a camera rect (frustum culling).

All rendering uses :func:`pygame.Surface.subsurface` and
:func:`pygame.Surface.blit` — no OS extensions.

Usage::

    from gui_do import TileSet, TileMap
    from pygame import Rect

    # Load atlas (e.g. from AssetRegistry):
    tile_set = TileSet(atlas_surface, tile_w=32, tile_h=32)

    # Create 20×15 tile map:
    tile_map = TileMap(tile_w=32, tile_h=32, cols=20, rows=15, tile_set=tile_set)

    # Fill tiles:
    tile_map.fill(0)                        # solid grass
    tile_map.set_tile(5, 3, 2)             # rock at column 5, row 3
    tile_map.fill_rect(0, 0, 5, 5, 1)     # water in top-left 5×5

    # Each frame — draw only tiles visible in camera_rect:
    camera_rect = Rect(scroll_x, scroll_y, screen_w, screen_h)
    tile_map.draw(surface, camera_rect, offset=(0, 0))

    # Query:
    col, row = tile_map.world_to_tile(mouse_x, mouse_y)
    wx, wy   = tile_map.tile_to_world(col, row)
    tile_id  = tile_map.tile_at(col, row)   # None if out of bounds
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Sequence, Tuple

import pygame
from pygame import Rect, Surface


# ---------------------------------------------------------------------------
# TileSet
# ---------------------------------------------------------------------------


class TileSet:
    """Slices a surface atlas into indexed tile sub-surfaces.

    Parameters
    ----------
    surface:
        The atlas image.
    tile_w:
        Width of each tile in pixels.
    tile_h:
        Height of each tile in pixels.

    Tiles are sliced left-to-right, top-to-bottom.  Tile IDs are 0-based.
    Tile ID ``-1`` is treated as "empty" and skipped during rendering.
    """

    EMPTY: int = -1

    def __init__(self, surface: Surface, tile_w: int, tile_h: int) -> None:
        if tile_w <= 0 or tile_h <= 0:
            raise ValueError(f"tile_w and tile_h must be positive, got {tile_w}x{tile_h}")
        self._surface = surface
        self._tile_w = int(tile_w)
        self._tile_h = int(tile_h)
        sw, sh = surface.get_size()
        self._cols = max(1, sw // self._tile_w)
        rows = max(1, sh // self._tile_h)
        self._tile_count = self._cols * rows
        self._cache: Dict[int, Surface] = {}

    @property
    def tile_count(self) -> int:
        """Total number of tiles in the set."""
        return self._tile_count

    @property
    def tile_w(self) -> int:
        return self._tile_w

    @property
    def tile_h(self) -> int:
        return self._tile_h

    def tile_surface(self, tile_id: int) -> Surface:
        """Return the sub-surface for *tile_id*.  Results are cached."""
        if tile_id < 0 or tile_id >= self._tile_count:
            raise IndexError(f"Tile ID {tile_id} out of range [0, {self._tile_count})")
        if tile_id in self._cache:
            return self._cache[tile_id]
        col = tile_id % self._cols
        row = tile_id // self._cols
        x = col * self._tile_w
        y = row * self._tile_h
        sub = self._surface.subsurface(Rect(x, y, self._tile_w, self._tile_h))
        self._cache[tile_id] = sub
        return sub


# ---------------------------------------------------------------------------
# TileMap
# ---------------------------------------------------------------------------


class TileMap:
    """2-D grid of tile IDs rendered with camera-based culling.

    Parameters
    ----------
    tile_w, tile_h:
        Pixel dimensions of each tile.
    cols, rows:
        Grid dimensions.
    tile_set:
        The :class:`TileSet` used for rendering.

    World coordinates map linearly: tile ``(col, row)`` occupies the rect
    ``Rect(col * tile_w, row * tile_h, tile_w, tile_h)``.
    """

    def __init__(
        self,
        tile_w: int,
        tile_h: int,
        cols: int,
        rows: int,
        tile_set: TileSet,
    ) -> None:
        if tile_w <= 0 or tile_h <= 0:
            raise ValueError(f"tile_w and tile_h must be positive")
        if cols <= 0 or rows <= 0:
            raise ValueError(f"cols and rows must be positive")
        self._tile_w = int(tile_w)
        self._tile_h = int(tile_h)
        self._cols = int(cols)
        self._rows = int(rows)
        self._tile_set = tile_set
        # Flat row-major array of tile IDs; -1 = empty
        self._tiles: List[int] = [TileSet.EMPTY] * (cols * rows)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def tile_w(self) -> int:
        return self._tile_w

    @property
    def tile_h(self) -> int:
        return self._tile_h

    @property
    def tile_set(self) -> TileSet:
        return self._tile_set

    @tile_set.setter
    def tile_set(self, value: TileSet) -> None:
        self._tile_set = value

    @property
    def pixel_width(self) -> int:
        """Total world width in pixels."""
        return self._cols * self._tile_w

    @property
    def pixel_height(self) -> int:
        """Total world height in pixels."""
        return self._rows * self._tile_h

    # ------------------------------------------------------------------
    # Tile data access
    # ------------------------------------------------------------------

    def _index(self, col: int, row: int) -> int:
        return row * self._cols + col

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self._cols and 0 <= row < self._rows

    def tile_at(self, col: int, row: int) -> Optional[int]:
        """Return the tile ID at *(col, row)*, or ``None`` if out of bounds."""
        if not self._in_bounds(col, row):
            return None
        return self._tiles[self._index(col, row)]

    def set_tile(self, col: int, row: int, tile_id: int) -> None:
        """Set the tile ID at *(col, row)*.

        Use ``TileSet.EMPTY`` (``-1``) to clear a tile.
        Silently ignores out-of-bounds coordinates.
        """
        if self._in_bounds(col, row):
            self._tiles[self._index(col, row)] = tile_id

    def fill(self, tile_id: int) -> None:
        """Fill the entire map with *tile_id*."""
        for i in range(len(self._tiles)):
            self._tiles[i] = tile_id

    def fill_rect(
        self,
        col: int,
        row: int,
        width: int,
        height: int,
        tile_id: int,
    ) -> None:
        """Fill a rectangular region with *tile_id*.

        Out-of-bounds cells are skipped silently.
        """
        for r in range(row, row + height):
            for c in range(col, col + width):
                self.set_tile(c, r, tile_id)

    def clear(self) -> None:
        """Set all tiles to :attr:`TileSet.EMPTY`."""
        self.fill(TileSet.EMPTY)

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def world_to_tile(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world-space pixel coordinates to *(col, row)*.

        The returned col/row may be out of bounds — use :meth:`tile_at` to
        check validity.
        """
        col = int(world_x // self._tile_w)
        row = int(world_y // self._tile_h)
        return col, row

    def tile_to_world(self, col: int, row: int) -> Tuple[int, int]:
        """Return the world-space top-left pixel of tile *(col, row)*."""
        return col * self._tile_w, row * self._tile_h

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------

    def visible_range(self, camera_rect: Rect) -> Tuple[int, int, int, int]:
        """Return *(col_start, col_end, row_start, row_end)* for *camera_rect*.

        Only tile columns/rows that overlap the camera are included.
        """
        col_start = max(0, camera_rect.left // self._tile_w)
        col_end = min(self._cols, (camera_rect.right + self._tile_w - 1) // self._tile_w)
        row_start = max(0, camera_rect.top // self._tile_h)
        row_end = min(self._rows, (camera_rect.bottom + self._tile_h - 1) // self._tile_h)
        return col_start, col_end, row_start, row_end

    def dirty_tiles(self) -> Iterator[Rect]:
        """Yield one ``Rect`` per non-empty tile (world coordinates).

        Useful for feeding to :class:`~gui_do.DirtyRegionTracker`.
        """
        for row in range(self._rows):
            for col in range(self._cols):
                tid = self._tiles[self._index(col, row)]
                if tid != TileSet.EMPTY:
                    yield Rect(col * self._tile_w, row * self._tile_h, self._tile_w, self._tile_h)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: Surface,
        camera_rect: Rect,
        offset: Tuple[int, int] = (0, 0),
    ) -> None:
        """Render the tiles visible within *camera_rect* onto *surface*.

        Parameters
        ----------
        surface:
            Target rendering surface.
        camera_rect:
            The visible world region.  Tiles outside this rect are culled.
        offset:
            Screen-space offset to apply to each tile's blit position.
            Useful when the surface origin differs from screen origin.
        """
        col_start, col_end, row_start, row_end = self.visible_range(camera_rect)
        ox, oy = offset
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                tid = self._tiles[self._index(col, row)]
                if tid == TileSet.EMPTY:
                    continue
                tile_surf = self._tile_set.tile_surface(tid)
                wx = col * self._tile_w - camera_rect.left + ox
                wy = row * self._tile_h - camera_rect.top + oy
                surface.blit(tile_surf, (wx, wy))
