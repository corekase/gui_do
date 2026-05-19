"""VectorPath — resolution-independent 2-D path builder with pygame rendering.

Supports move/line/cubic-Bézier/quadratic-Bézier/arc commands and renders them
onto any :class:`pygame.Surface` using only standard pygame draw calls.
Paths can be transformed (translate, uniform scale, rotate) without mutating
the original.

Usage::

    from gui_do import VectorPath

    # Build a rounded-corner speech bubble path:
    path = VectorPath()
    path.rounded_rect(pygame.Rect(20, 20, 160, 80), radius=12)
    path.fill(surface, (220, 240, 255))
    path.stroke(surface, (80, 120, 200), width=2)

    # Build a progress arc:
    arc_path = VectorPath()
    arc_path.arc(cx=200, cy=200, radius=60,
                 start_angle_deg=0, end_angle_deg=270)
    arc_path.stroke(surface, (60, 180, 60), width=6)

    # Hit-test:
    if path.contains_point(mx, my):
        ...

    # Non-destructive transform:
    scaled = path.transform(translate=(10, 10), scale=2.0)
"""
from __future__ import annotations

import math
from typing import List, Tuple

import pygame
from pygame import Rect, Surface


# Segment types
_MOVE = "M"
_LINE = "L"
_CUBIC = "C"
_QUAD = "Q"
_ARC = "A"
_CLOSE = "Z"

_Segment = Tuple  # (type, *data)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _quad_bezier_points(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    segments: int,
) -> List[Tuple[float, float]]:
    pts = []
    for i in range(segments + 1):
        t = i / segments
        x = _lerp(_lerp(p0[0], p1[0], t), _lerp(p1[0], p2[0], t), t)
        y = _lerp(_lerp(p0[1], p1[1], t), _lerp(p1[1], p2[1], t), t)
        pts.append((x, y))
    return pts


def _cubic_bezier_points(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    segments: int,
) -> List[Tuple[float, float]]:
    pts = []
    for i in range(segments + 1):
        t = i / segments
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def _arc_points(
    cx: float,
    cy: float,
    radius: float,
    start_rad: float,
    end_rad: float,
    segments: int,
) -> List[Tuple[float, float]]:
    pts = []
    span = end_rad - start_rad
    for i in range(segments + 1):
        a = start_rad + span * (i / max(segments, 1))
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return pts


class VectorPath:
    """Immutable-by-convention 2-D vector path builder.

    Paths are composed of *segments* and rendered on demand.  The path does not
    hold a reference to any surface.
    """

    def __init__(self) -> None:
        self._segments: List[_Segment] = []
        self._current: Tuple[float, float] = (0.0, 0.0)
        # Bézier/arc tessellation granularity per 100 units
        self._segs_per_100: int = 16
        self._tessellation_cache: List[List[Tuple[int, int]]] | None = None

    def _invalidate_tessellation(self) -> None:
        self._tessellation_cache = None

    # ------------------------------------------------------------------
    # Path commands
    # ------------------------------------------------------------------

    def move_to(self, x: float, y: float) -> "VectorPath":
        """Begin a new sub-path at (*x*, *y*)."""
        self._segments.append((_MOVE, float(x), float(y)))
        self._current = (float(x), float(y))
        self._invalidate_tessellation()
        return self

    def line_to(self, x: float, y: float) -> "VectorPath":
        """Draw a line from the current position to (*x*, *y*)."""
        self._segments.append((_LINE, float(x), float(y)))
        self._current = (float(x), float(y))
        self._invalidate_tessellation()
        return self

    def close(self) -> "VectorPath":
        """Close the current sub-path back to its starting point."""
        self._segments.append((_CLOSE,))
        self._invalidate_tessellation()
        return self

    def quadratic_to(
        self,
        cx: float,
        cy: float,
        x: float,
        y: float,
    ) -> "VectorPath":
        """Quadratic Bézier from current position through (*cx*, *cy*) to (*x*, *y*)."""
        self._segments.append((_QUAD, float(cx), float(cy), float(x), float(y)))
        self._current = (float(x), float(y))
        self._invalidate_tessellation()
        return self

    def cubic_to(
        self,
        c1x: float,
        c1y: float,
        c2x: float,
        c2y: float,
        x: float,
        y: float,
    ) -> "VectorPath":
        """Cubic Bézier from current position."""
        self._segments.append(
            (_CUBIC, float(c1x), float(c1y), float(c2x), float(c2y), float(x), float(y))
        )
        self._current = (float(x), float(y))
        self._invalidate_tessellation()
        return self

    def arc(
        self,
        cx: float,
        cy: float,
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float,
    ) -> "VectorPath":
        """Append an arc centered at (*cx*, *cy*)."""
        self._segments.append(
            (_ARC, float(cx), float(cy), float(radius),
             math.radians(float(start_angle_deg)),
             math.radians(float(end_angle_deg)))
        )
        end_rad = math.radians(end_angle_deg)
        self._current = (cx + radius * math.cos(end_rad), cy + radius * math.sin(end_rad))
        self._invalidate_tessellation()
        return self

    def rect(self, r: Rect) -> "VectorPath":
        """Append a closed rectangular sub-path."""
        x, y, w, h = r.x, r.y, r.width, r.height
        (self.move_to(x, y)
             .line_to(x + w, y)
             .line_to(x + w, y + h)
             .line_to(x, y + h)
             .close())
        return self

    def rounded_rect(self, r: Rect, radius: float) -> "VectorPath":
        """Append a closed rounded-rectangle sub-path."""
        x, y, w, h = float(r.x), float(r.y), float(r.width), float(r.height)
        rr = max(0.0, min(float(radius), w / 2, h / 2))
        # Top-left arc → top edge → top-right arc → right edge → etc.
        self.move_to(x + rr, y)
        self.arc(x + rr, y + rr, rr, -90, -180)     # top-left
        self.line_to(x, y + h - rr)
        self.arc(x + rr, y + h - rr, rr, 180, 90)   # bottom-left
        self.line_to(x + w - rr, y + h)
        self.arc(x + w - rr, y + h - rr, rr, 90, 0) # bottom-right
        self.line_to(x + w, y + rr)
        self.arc(x + w - rr, y + rr, rr, 0, -90)    # top-right
        self.close()
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _tessellate(self) -> List[List[Tuple[int, int]]]:
        """Convert path segments into screen-space polygon lists.

        Returns a list of sub-paths, each being a list of integer points.
        """
        if self._tessellation_cache is not None:
            return self._tessellation_cache

        sub_paths: List[List[Tuple[int, int]]] = []
        current_sub: List[Tuple[float, float]] = []
        start_of_sub: Tuple[float, float] = (0.0, 0.0)
        pos: Tuple[float, float] = (0.0, 0.0)

        for seg in self._segments:
            kind = seg[0]
            if kind == _MOVE:
                if current_sub:
                    sub_paths.append([(int(p[0]), int(p[1])) for p in current_sub])
                current_sub = [(seg[1], seg[2])]
                pos = (seg[1], seg[2])
                start_of_sub = pos
            elif kind == _LINE:
                current_sub.append((seg[1], seg[2]))
                pos = (seg[1], seg[2])
            elif kind == _CLOSE:
                current_sub.append(start_of_sub)
                sub_paths.append([(int(p[0]), int(p[1])) for p in current_sub])
                current_sub = []
            elif kind == _QUAD:
                n = max(4, self._segs_per_100)
                pts = _quad_bezier_points(pos, (seg[1], seg[2]), (seg[3], seg[4]), n)
                current_sub.extend(pts[1:])
                pos = (seg[3], seg[4])
            elif kind == _CUBIC:
                n = max(4, self._segs_per_100)
                pts = _cubic_bezier_points(
                    pos, (seg[1], seg[2]), (seg[3], seg[4]), (seg[5], seg[6]), n
                )
                current_sub.extend(pts[1:])
                pos = (seg[5], seg[6])
            elif kind == _ARC:
                _, acx, acy, ar, a_start, a_end = seg
                span = abs(a_end - a_start)
                n = max(4, int(ar * span / (math.pi / 8)))
                pts = _arc_points(acx, acy, ar, a_start, a_end, n)
                if not current_sub:
                    current_sub.extend(pts)
                else:
                    current_sub.extend(pts[1:])
                pos = pts[-1]

        if current_sub:
            sub_paths.append([(int(p[0]), int(p[1])) for p in current_sub])
        self._tessellation_cache = sub_paths
        return sub_paths

    def stroke(
        self,
        surface: Surface,
        color: Tuple[int, int, int],
        *,
        width: int = 1,
        antialias: bool = False,
    ) -> None:
        """Draw the path outline on *surface*."""
        for sub in self._tessellate():
            if len(sub) < 2:
                continue
            if antialias:
                pygame.draw.aalines(surface, color, False, sub)
            else:
                pygame.draw.lines(surface, color, False, sub, width)

    def fill(self, surface: Surface, color: Tuple[int, int, int]) -> None:
        """Fill the path area on *surface* (convex or simple polygon only)."""
        for sub in self._tessellate():
            if len(sub) < 3:
                continue
            pygame.draw.polygon(surface, color, sub)

    # ------------------------------------------------------------------
    # Geometry queries
    # ------------------------------------------------------------------

    def _flat_points(self) -> List[Tuple[float, float]]:
        """Return all tessellated points as a flat list."""
        pts: List[Tuple[float, float]] = []
        for sub in self._tessellate():
            pts.extend(sub)
        return pts

    def bounding_rect(self) -> Rect:
        """Return the axis-aligned bounding box of all path points."""
        pts = self._flat_points()
        if not pts:
            return Rect(0, 0, 0, 0)
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_x = max(p[0] for p in pts)
        max_y = max(p[1] for p in pts)
        return Rect(int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y))

    def contains_point(self, x: float, y: float) -> bool:
        """Test whether (*x*, *y*) lies inside the path using even-odd rule."""
        # Ray casting algorithm
        inside = False
        for sub in self._tessellate():
            n = len(sub)
            j = n - 1
            for i in range(n):
                xi, yi = sub[i]
                xj, yj = sub[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
        return inside

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------

    def transform(
        self,
        *,
        translate: Tuple[float, float] = (0.0, 0.0),
        scale: float = 1.0,
        rotate_degrees: float = 0.0,
    ) -> "VectorPath":
        """Return a **new** :class:`VectorPath` with the given transform applied.

        The transform order is: scale → rotate → translate.
        """
        cos_a = math.cos(math.radians(rotate_degrees))
        sin_a = math.sin(math.radians(rotate_degrees))
        tx, ty = translate

        def _xform(px: float, py: float) -> Tuple[float, float]:
            # Scale
            px, py = px * scale, py * scale
            # Rotate
            px, py = px * cos_a - py * sin_a, px * sin_a + py * cos_a
            # Translate
            return px + tx, py + ty

        new_path = VectorPath()
        new_path._segs_per_100 = self._segs_per_100
        for seg in self._segments:
            kind = seg[0]
            if kind == _MOVE:
                nx, ny = _xform(seg[1], seg[2])
                new_path._segments.append((_MOVE, nx, ny))
            elif kind == _LINE:
                nx, ny = _xform(seg[1], seg[2])
                new_path._segments.append((_LINE, nx, ny))
            elif kind == _CLOSE:
                new_path._segments.append((_CLOSE,))
            elif kind == _QUAD:
                ncx, ncy = _xform(seg[1], seg[2])
                nx, ny = _xform(seg[3], seg[4])
                new_path._segments.append((_QUAD, ncx, ncy, nx, ny))
            elif kind == _CUBIC:
                nc1x, nc1y = _xform(seg[1], seg[2])
                nc2x, nc2y = _xform(seg[3], seg[4])
                nx, ny = _xform(seg[5], seg[6])
                new_path._segments.append((_CUBIC, nc1x, nc1y, nc2x, nc2y, nx, ny))
            elif kind == _ARC:
                # Transform center; scale radius; adjust angle
                _, acx, acy, ar, a_start, a_end = seg
                nacx, nacy = _xform(acx, acy)
                nar = ar * scale
                angle_offset = math.radians(rotate_degrees)
                new_path._segments.append(
                    (_ARC, nacx, nacy, nar, a_start + angle_offset, a_end + angle_offset)
                )
        return new_path
