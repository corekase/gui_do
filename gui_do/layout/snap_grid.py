"""SnapGrid, AlignmentGuide, SnapComposer — grid and alignment snapping.

Provides integer pixel snapping for drag-and-drop layout editors, vector
drawing tools, and any scenario where controls should align to a grid or
to each other's edges.

Classes
-------
:class:`SnapGrid`
    Rectangular snapping grid with configurable cell size and offset.
:class:`SnapTarget`
    Dataclass describing one detected alignment opportunity.
:class:`AlignmentGuide`
    Edge-alignment detector — finds candidate rects that share an edge
    (or center line) with the dragged rect within a pixel threshold.
:class:`SnapComposer`
    Combines a :class:`SnapGrid` and an :class:`AlignmentGuide` into a
    single snapping step.

Usage::

    from gui_do import SnapGrid, AlignmentGuide, SnapComposer, SnapTarget

    grid = SnapGrid(cell_w=16, cell_h=16)
    snapped_pos = grid.snap_point(drag_x, drag_y)
    snapped_rect = grid.snap_rect(dragged_rect)

    # Draw the grid for visual feedback:
    grid.draw_grid(overlay_surface, viewport_rect, color=(80, 80, 80), alpha=80)

    # Find alignment guides against all other controls:
    guide = AlignmentGuide(candidate_rects)
    targets = guide.find_snap_targets(dragged_rect, threshold_px=8)

    # Combined snap (grid takes precedence, then guide):
    composer = SnapComposer(grid=grid, guides=guide)
    final_rect = composer.snap(dragged_rect, threshold_px=8)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import pygame
from pygame import Rect, Surface


# ---------------------------------------------------------------------------
# SnapGrid
# ---------------------------------------------------------------------------

class SnapGrid:
    """Rectangular snapping grid.

    Parameters
    ----------
    cell_w, cell_h:
        Grid cell dimensions in pixels.
    offset_x, offset_y:
        Grid origin offset (shifts all cell boundaries).
    """

    def __init__(
        self,
        cell_w: int,
        cell_h: int,
        *,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> None:
        self.cell_w: int = max(1, int(cell_w))
        self.cell_h: int = max(1, int(cell_h))
        self.offset_x: int = int(offset_x)
        self.offset_y: int = int(offset_y)

    def snap_point(self, x: float, y: float) -> Tuple[int, int]:
        """Round (*x*, *y*) to the nearest grid intersection."""
        sx = round((x - self.offset_x) / self.cell_w) * self.cell_w + self.offset_x
        sy = round((y - self.offset_y) / self.cell_h) * self.cell_h + self.offset_y
        return int(sx), int(sy)

    def snap_rect(self, rect: Rect) -> Rect:
        """Snap the top-left corner of *rect* to the nearest grid intersection.

        Width and height are preserved.
        """
        sx, sy = self.snap_point(rect.x, rect.y)
        return Rect(sx, sy, rect.width, rect.height)

    def nearest_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Return the grid cell indices ``(col, row)`` containing (*x*, *y*)."""
        col = int(math.floor((x - self.offset_x) / self.cell_w))
        row = int(math.floor((y - self.offset_y) / self.cell_h))
        return col, row

    def draw_grid(
        self,
        surface: Surface,
        clip_rect: Rect,
        color: Tuple[int, int, int],
        *,
        alpha: int = 255,
    ) -> None:
        """Draw vertical and horizontal grid lines within *clip_rect*.

        Parameters
        ----------
        alpha:
            Line opacity 0–255.  Uses a temporary alpha surface when < 255.
        """
        if alpha < 255:
            tmp = Surface((clip_rect.width, clip_rect.height), pygame.SRCALPHA)
            self._draw_on(tmp, Rect(0, 0, clip_rect.width, clip_rect.height), color, alpha)
            surface.blit(tmp, clip_rect.topleft)
        else:
            self._draw_on(surface, clip_rect, color, 255)

    def _draw_on(
        self,
        surface: Surface,
        clip: Rect,
        color: Tuple[int, int, int],
        alpha: int,
    ) -> None:
        draw_color = (color[0], color[1], color[2], alpha)
        x = clip.x + (self.offset_x - clip.x) % self.cell_w
        while x <= clip.right:
            pygame.draw.line(surface, draw_color, (x, clip.y), (x, clip.bottom - 1))
            x += self.cell_w
        y = clip.y + (self.offset_y - clip.y) % self.cell_h
        while y <= clip.bottom:
            pygame.draw.line(surface, draw_color, (clip.x, y), (clip.right - 1, y))
            y += self.cell_h


# ---------------------------------------------------------------------------
# SnapTarget
# ---------------------------------------------------------------------------

@dataclass
class SnapTarget:
    """One detected alignment opportunity between two rects.

    Attributes
    ----------
    axis:
        ``"x"`` or ``"y"`` — which axis the snap applies to.
    value:
        The pixel value the dragged rect edge/center should snap to.
    guide_rect:
        The candidate rect that triggered this target (for guide-line rendering).
    distance:
        Unsigned pixel distance from the dragged edge to *value* before snapping.
    label:
        Human-readable description of the alignment type (``"left-left"``,
        ``"center-x"``, ``"top-top"``, etc.).
    """

    axis: str
    value: int
    guide_rect: Rect
    distance: float
    label: str = field(default="")


# ---------------------------------------------------------------------------
# AlignmentGuide
# ---------------------------------------------------------------------------

class AlignmentGuide:
    """Edge and center-line alignment detector.

    Parameters
    ----------
    candidate_rects:
        The static rects to align against (e.g. all placed controls except
        the one being dragged).
    """

    def __init__(self, candidate_rects: List[Rect]) -> None:
        self._candidates: List[Rect] = list(candidate_rects)

    def update_candidates(self, candidate_rects: List[Rect]) -> None:
        """Replace the candidate rect list."""
        self._candidates = list(candidate_rects)

    def find_snap_targets(
        self,
        dragged: Rect,
        threshold_px: int = 8,
    ) -> List[SnapTarget]:
        """Return all alignment targets within *threshold_px* pixels.

        For each candidate the following alignments are checked:
        - left-left, right-left (dragged.left vs candidate edge)
        - right-right, left-right
        - center-x (horizontal midpoints)
        - top-top, bottom-top, center-y
        - bottom-bottom, top-bottom

        The results are sorted by ascending distance so callers can choose
        the closest snap.
        """
        targets: List[SnapTarget] = []
        dl, dr, dt, db = dragged.left, dragged.right, dragged.top, dragged.bottom
        dcx, dcy = dragged.centerx, dragged.centery

        for cand in self._candidates:
            cl, cr, ct, cb = cand.left, cand.right, cand.top, cand.bottom
            ccx, ccy = cand.centerx, cand.centery

            # X-axis snaps
            for edge_val, label in [
                (cl, "left-left"), (cr, "right-left"),
            ]:
                dist = float(abs(dl - edge_val))
                if dist <= threshold_px:
                    targets.append(SnapTarget("x", edge_val, cand, dist, label))

            for edge_val, label in [
                (cl, "left-right"), (cr, "right-right"),
            ]:
                dist = float(abs(dr - edge_val))
                if dist <= threshold_px:
                    targets.append(SnapTarget("x", edge_val - dragged.width, cand, dist, label))

            dist = float(abs(dcx - ccx))
            if dist <= threshold_px:
                targets.append(SnapTarget("x", ccx - dragged.width // 2, cand, dist, "center-x"))

            # Y-axis snaps
            for edge_val, label in [
                (ct, "top-top"), (cb, "bottom-top"),
            ]:
                dist = float(abs(dt - edge_val))
                if dist <= threshold_px:
                    targets.append(SnapTarget("y", edge_val, cand, dist, label))

            for edge_val, label in [
                (ct, "top-bottom"), (cb, "bottom-bottom"),
            ]:
                dist = float(abs(db - edge_val))
                if dist <= threshold_px:
                    targets.append(SnapTarget("y", edge_val - dragged.height, cand, dist, label))

            dist = float(abs(dcy - ccy))
            if dist <= threshold_px:
                targets.append(SnapTarget("y", ccy - dragged.height // 2, cand, dist, "center-y"))

        targets.sort(key=lambda t: t.distance)
        return targets


# ---------------------------------------------------------------------------
# SnapComposer
# ---------------------------------------------------------------------------

class SnapComposer:
    """Combines :class:`SnapGrid` and :class:`AlignmentGuide` snapping.

    When both a grid and alignment guides are active, the guide snap takes
    precedence (alignment is generally more useful to the user).  If only one
    is configured, that one is used.

    Parameters
    ----------
    grid:
        Optional :class:`SnapGrid` instance.
    guides:
        Optional :class:`AlignmentGuide` instance.
    """

    def __init__(
        self,
        *,
        grid: Optional[SnapGrid] = None,
        guides: Optional[AlignmentGuide] = None,
    ) -> None:
        self.grid: Optional[SnapGrid] = grid
        self.guides: Optional[AlignmentGuide] = guides

    def snap(
        self,
        rect: Rect,
        *,
        threshold_px: int = 8,
    ) -> Rect:
        """Return a snapped copy of *rect*.

        Alignment guide targets on each axis override the grid snap for that
        axis when any guide target is within *threshold_px*.
        """
        result = Rect(rect)

        if self.guides is not None:
            targets = self.guides.find_snap_targets(rect, threshold_px)
            x_snapped = False
            y_snapped = False
            for t in targets:
                if t.axis == "x" and not x_snapped:
                    result.x = t.value
                    x_snapped = True
                elif t.axis == "y" and not y_snapped:
                    result.y = t.value
                    y_snapped = True
                if x_snapped and y_snapped:
                    break
            # Fall back to grid for un-snapped axes
            if self.grid is not None:
                if not x_snapped:
                    gx, _ = self.grid.snap_point(result.x, result.y)
                    result.x = gx
                if not y_snapped:
                    _, gy = self.grid.snap_point(result.x, result.y)
                    result.y = gy
        elif self.grid is not None:
            result = self.grid.snap_rect(result)

        return result
