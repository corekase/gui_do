"""GridLayout — 2D structured row/column layout engine.

Positions children into a fixed grid of rows and columns with configurable
track sizes, gaps, and cell spanning.  Works like CSS grid in its essentials:
tracks can be fixed-pixel, fractional (``"1fr"``), or content-sized
(``"auto"``).

This is a pure geometry engine — it computes and mutates child ``rect``
attributes.  It does **not** call ``invalidate()`` on children; callers should
do that after :meth:`apply`.

Usage::

    from gui_do import GridLayout, GridTrack, GridPlacement

    layout = GridLayout(
        row_tracks=[GridTrack("auto"), GridTrack("1fr"), GridTrack(40)],
        col_tracks=[GridTrack("1fr"), GridTrack("1fr")],
        gap=8,
    )

    layout.place(header,   GridPlacement(row=0, col=0, colspan=2))
    layout.place(sidebar,  GridPlacement(row=1, col=0))
    layout.place(content,  GridPlacement(row=1, col=1))
    layout.place(footer,   GridPlacement(row=2, col=0, colspan=2))

    layout.apply(container_rect)   # computes and sets each child's rect
    for node in layout.nodes():
        node.invalidate()

Track sizing
------------
A :class:`GridTrack` accepts:

- ``int`` — fixed pixel size.
- ``"auto"`` — content-size: uses the ``rect`` dimension of the largest child
  placed in that track (measured **before** ``apply`` is called, i.e. from
  the current rect).
- ``"Nfr"`` — fractional: divides the remaining space proportionally among
  all ``fr`` tracks (e.g. ``"2fr"`` takes twice the space of ``"1fr"``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    from ..core.ui_node import UiNode


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GridTrack:
    """Size descriptor for a single row or column track.

    Parameters
    ----------
    size:
        ``int`` for a fixed pixel size, ``"auto"`` for content-size, or
        ``"Nfr"`` (e.g. ``"1fr"``, ``"2fr"``) for fractional distribution.
    min_size:
        Minimum pixel size for ``"fr"`` and ``"auto"`` tracks.
    max_size:
        Maximum pixel size for ``"fr"`` tracks.
    """

    size: "int | str"
    min_size: int = 0
    max_size: Optional[int] = None

    def __post_init__(self) -> None:
        if isinstance(self.size, int):
            if self.size < 0:
                raise ValueError(f"Fixed track size must be >= 0, got {self.size}")
        elif isinstance(self.size, str):
            s = self.size.strip().lower()
            if s != "auto" and not re.match(r"^\d+(\.\d+)?fr$", s):
                raise ValueError(
                    f"Track size must be an int, 'auto', or 'Nfr' (e.g. '1fr'), got {self.size!r}"
                )
        else:
            raise TypeError(f"Track size must be int or str, got {type(self.size).__name__}")


@dataclass
class GridPlacement:
    """Describes which cell(s) a node occupies.

    Parameters
    ----------
    row:
        Zero-based row index of the top-left cell.
    col:
        Zero-based column index of the top-left cell.
    rowspan:
        Number of rows spanned (default ``1``).
    colspan:
        Number of columns spanned (default ``1``).
    align_x:
        Horizontal alignment within the cell: ``"start"``, ``"center"``,
        ``"end"``, or ``"stretch"`` (default).
    align_y:
        Vertical alignment within the cell: ``"start"``, ``"center"``,
        ``"end"``, or ``"stretch"`` (default).
    """

    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    align_x: str = "stretch"
    align_y: str = "stretch"

    def __post_init__(self) -> None:
        for name, val in (("row", self.row), ("col", self.col)):
            if val < 0:
                raise ValueError(f"{name} must be >= 0")
        for name, val in (("rowspan", self.rowspan), ("colspan", self.colspan)):
            if val < 1:
                raise ValueError(f"{name} must be >= 1")
        for name, val in (("align_x", self.align_x), ("align_y", self.align_y)):
            if val not in ("start", "center", "end", "stretch"):
                raise ValueError(f"{name} must be one of 'start', 'center', 'end', 'stretch'")


# ---------------------------------------------------------------------------
# GridLayout
# ---------------------------------------------------------------------------


class GridLayout:
    """2D grid layout engine.

    :meth:`apply` computes and mutates child ``rect`` attributes in-place
    given a *container_rect*.  Callers should call ``invalidate()`` on each
    child after applying layout.
    """

    def __init__(
        self,
        row_tracks: Sequence[GridTrack],
        col_tracks: Sequence[GridTrack],
        *,
        gap: int = 0,
        row_gap: Optional[int] = None,
        col_gap: Optional[int] = None,
    ) -> None:
        self._row_tracks: List[GridTrack] = list(row_tracks)
        self._col_tracks: List[GridTrack] = list(col_tracks)
        # row_gap / col_gap override the symmetric gap
        self._row_gap: int = int(row_gap) if row_gap is not None else int(gap)
        self._col_gap: int = int(col_gap) if col_gap is not None else int(gap)
        # Ordered list of (node, placement) pairs
        self._placements: List[Tuple["UiNode", GridPlacement]] = []

    # ------------------------------------------------------------------
    # Placement API
    # ------------------------------------------------------------------

    def place(self, node: "UiNode", placement: GridPlacement) -> None:
        """Register *node* at *placement*.

        If *node* was previously placed it is re-placed at the new position.
        """
        self._placements = [(n, p) for n, p in self._placements if n is not node]
        self._placements.append((node, placement))

    def remove(self, node: "UiNode") -> bool:
        """Remove *node* from the layout. Returns True if it was registered."""
        before = len(self._placements)
        self._placements = [(n, p) for n, p in self._placements if n is not node]
        return len(self._placements) < before

    def nodes(self) -> List["UiNode"]:
        """Return the ordered list of registered nodes."""
        return [n for n, _ in self._placements]

    def placement_for(self, node: "UiNode") -> Optional[GridPlacement]:
        """Return the :class:`GridPlacement` for *node*, or ``None``."""
        for n, p in self._placements:
            if n is node:
                return p
        return None

    # ------------------------------------------------------------------
    # Layout computation
    # ------------------------------------------------------------------

    def apply(self, container_rect: Rect) -> None:
        """Compute and mutate child rects given *container_rect*.

        Algorithm:

        1. Resolve fixed tracks.
        2. Measure ``auto`` tracks from current child rects (pre-layout size).
        3. Distribute remaining space among ``fr`` tracks.
        4. Compute cell origins.
        5. Apply cell rect + alignment to each registered node.
        """
        n_rows = len(self._row_tracks)
        n_cols = len(self._col_tracks)

        row_sizes = self._resolve_tracks(
            self._row_tracks, container_rect.height, self._row_gap,
            axis="row", placements=self._placements, n_tracks=n_rows,
        )
        col_sizes = self._resolve_tracks(
            self._col_tracks, container_rect.width, self._col_gap,
            axis="col", placements=self._placements, n_tracks=n_cols,
        )

        # Compute track origins (cumulative offset)
        row_origins = self._track_origins(row_sizes, self._row_gap, container_rect.top)
        col_origins = self._track_origins(col_sizes, self._col_gap, container_rect.left)

        for node, placement in self._placements:
            r, c = placement.row, placement.col
            rs, cs = placement.rowspan, placement.colspan

            # Guard out-of-range placements gracefully
            if r >= n_rows or c >= n_cols:
                continue

            max_row = min(r + rs, n_rows)
            max_col = min(c + cs, n_cols)

            cell_x = col_origins[c]
            cell_y = row_origins[r]
            cell_w = sum(col_sizes[c:max_col]) + self._col_gap * (max_col - c - 1)
            cell_h = sum(row_sizes[r:max_row]) + self._row_gap * (max_row - r - 1)
            cell_rect = Rect(cell_x, cell_y, max(0, cell_w), max(0, cell_h))

            node.rect = self._align_in_cell(node.rect, cell_rect, placement)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_tracks(
        self,
        tracks: List[GridTrack],
        available: int,
        gap: int,
        *,
        axis: str,
        placements: List[Tuple["UiNode", GridPlacement]],
        n_tracks: int,
    ) -> List[int]:
        """Return a list of resolved pixel sizes, one per track."""
        n = len(tracks)
        sizes: List[Optional[int]] = [None] * n
        total_gap = gap * max(0, n - 1)
        remaining = max(0, available - total_gap)

        # Pass 1: fixed tracks
        for i, track in enumerate(tracks):
            if isinstance(track.size, int):
                sizes[i] = max(int(track.min_size), track.size)
                remaining -= sizes[i]  # type: ignore[operator]

        # Pass 2: auto tracks — size to content
        auto_indices = [i for i, t in enumerate(tracks) if isinstance(t.size, str) and t.size.strip().lower() == "auto"]
        for i in auto_indices:
            track = tracks[i]
            content_size = self._measure_auto_track(i, axis, placements)
            resolved = max(int(track.min_size), content_size)
            if track.max_size is not None:
                resolved = min(resolved, int(track.max_size))
            sizes[i] = resolved
            remaining -= resolved

        # Pass 3: fr tracks
        fr_indices = [i for i, t in enumerate(tracks) if isinstance(t.size, str) and t.size.strip().lower().endswith("fr") and not t.size.strip().lower() == "auto"]
        total_fr = 0.0
        for i in fr_indices:
            total_fr += float(tracks[i].size.strip().lower()[:-2] or "1")
        if total_fr > 0 and fr_indices:
            fr_unit = max(0.0, remaining / total_fr)
            for i in fr_indices:
                fr_val = float(tracks[i].size.strip().lower()[:-2] or "1")
                track = tracks[i]
                resolved = int(fr_val * fr_unit)
                resolved = max(int(track.min_size), resolved)
                if track.max_size is not None:
                    resolved = min(resolved, int(track.max_size))
                sizes[i] = resolved

        # Fill any remaining None with 0
        return [s if s is not None else 0 for s in sizes]

    def _measure_auto_track(self, track_index: int, axis: str, placements) -> int:
        """Return the max content size of all single-span children in *track_index*."""
        content = 0
        for node, placement in placements:
            if axis == "row":
                if placement.row == track_index and placement.rowspan == 1:
                    content = max(content, node.rect.height)
            else:
                if placement.col == track_index and placement.colspan == 1:
                    content = max(content, node.rect.width)
        return content

    @staticmethod
    def _track_origins(sizes: List[int], gap: int, start: int) -> List[int]:
        origins = []
        cursor = start
        for size in sizes:
            origins.append(cursor)
            cursor += size + gap
        return origins

    @staticmethod
    def _align_in_cell(node_rect: Rect, cell_rect: Rect, placement: GridPlacement) -> Rect:
        nw = node_rect.width
        nh = node_rect.height

        # Horizontal
        if placement.align_x == "stretch":
            x = cell_rect.left
            w = cell_rect.width
        elif placement.align_x == "center":
            x = cell_rect.left + (cell_rect.width - nw) // 2
            w = nw
        elif placement.align_x == "end":
            x = cell_rect.right - nw
            w = nw
        else:  # start
            x = cell_rect.left
            w = nw

        # Vertical
        if placement.align_y == "stretch":
            y = cell_rect.top
            h = cell_rect.height
        elif placement.align_y == "center":
            y = cell_rect.top + (cell_rect.height - nh) // 2
            h = nh
        elif placement.align_y == "end":
            y = cell_rect.bottom - nh
            h = nh
        else:  # start
            y = cell_rect.top
            h = nh

        return Rect(x, y, max(0, w), max(0, h))
