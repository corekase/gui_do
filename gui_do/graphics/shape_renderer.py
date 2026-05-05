"""ShapeRenderer — composable procedural drawing primitives.

All functions draw onto a caller-supplied :class:`pygame.Surface` and return
``None``.  They use only :mod:`pygame.draw`, :mod:`pygame.gfxdraw`, and
standard-library math — no OS-specific APIs.

Usage::

    from gui_do import ShapeRenderer
    from pygame import Rect

    ShapeRenderer.rounded_rect(surface, (80, 140, 200), Rect(10, 10, 200, 60), radius=10)
    ShapeRenderer.gradient_rect(surface, Rect(0, 0, 200, 40), (30, 30, 60), (10, 10, 30))
    ShapeRenderer.drop_shadow(surface, Rect(20, 20, 180, 80), radius=12,
                              color=(0, 0, 0), spread=4, offset_x=2, offset_y=4)
    ShapeRenderer.check_mark(surface, Rect(4, 4, 16, 16), (80, 200, 80), width=2)
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import pygame
import pygame.gfxdraw
from pygame import Rect, Surface


Color = Tuple[int, int, int]
ColorAlpha = Tuple[int, int, int, int]


class ShapeRenderer:
    """Static drawing helpers — all methods are ``@staticmethod``."""

    # ------------------------------------------------------------------
    # Core shapes
    # ------------------------------------------------------------------

    @staticmethod
    def rounded_rect(
        surface: Surface,
        color: Color,
        rect: Rect,
        radius: int,
        *,
        width: int = 0,
    ) -> None:
        """Draw a rounded rectangle.

        Parameters
        ----------
        width:
            Line width in pixels.  ``0`` (default) fills the shape.
        """
        radius = max(0, min(radius, rect.width // 2, rect.height // 2))
        if radius == 0:
            pygame.draw.rect(surface, color, rect, width)
            return
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)

    @staticmethod
    def pill(
        surface: Surface,
        color: Color,
        rect: Rect,
        *,
        width: int = 0,
    ) -> None:
        """Draw a stadium / pill shape (maximum corner radius)."""
        radius = min(rect.width, rect.height) // 2
        ShapeRenderer.rounded_rect(surface, color, rect, radius, width=width)

    @staticmethod
    def gradient_rect(
        surface: Surface,
        rect: Rect,
        start_color: Color,
        end_color: Color,
        *,
        horizontal: bool = False,
    ) -> None:
        """Fill *rect* with a two-color linear gradient.

        Parameters
        ----------
        start_color:
            Color at the top (or left if *horizontal*).
        end_color:
            Color at the bottom (or right if *horizontal*).
        """
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        if w <= 0 or h <= 0:
            return
        steps = w if horizontal else h
        sr, sg, sb = start_color[0], start_color[1], start_color[2]
        er, eg, eb = end_color[0], end_color[1], end_color[2]
        for i in range(steps):
            t = i / max(steps - 1, 1)
            r = int(sr + (er - sr) * t)
            g = int(sg + (eg - sg) * t)
            b = int(sb + (eb - sb) * t)
            if horizontal:
                pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + h - 1))
            else:
                pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w - 1, y + i))

    @staticmethod
    def drop_shadow(
        surface: Surface,
        rect: Rect,
        *,
        radius: int = 8,
        color: Color = (0, 0, 0),
        spread: int = 4,
        offset_x: int = 0,
        offset_y: int = 4,
        alpha: int = 120,
    ) -> None:
        """Draw a soft drop shadow beneath *rect*.

        Uses successive rounded rectangles at decreasing alpha to approximate
        a Gaussian shadow blur.  Fully portable.
        """
        layers = max(1, spread)
        shadow_rect = rect.inflate(spread * 2, spread * 2).move(offset_x, offset_y)
        for i in range(layers, 0, -1):
            layer_alpha = int(alpha * (i / layers) * 0.6)
            a_color = (color[0], color[1], color[2], layer_alpha)
            layer_rect = shadow_rect.inflate(-(layers - i) * 2, -(layers - i) * 2)
            # Use a temporary surface to support per-pixel alpha
            tmp = Surface((layer_rect.width, layer_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                tmp, a_color, tmp.get_rect(), border_radius=max(0, radius + i)
            )
            surface.blit(tmp, layer_rect.topleft)

    @staticmethod
    def badge(
        surface: Surface,
        rect: Rect,
        text: str,
        bg_color: Color,
        text_color: Color,
        font: "pygame.font.Font",
    ) -> None:
        """Draw a pill-shaped badge with text centered in *rect*."""
        ShapeRenderer.pill(surface, bg_color, rect)
        if text:
            text_surf = font.render(text, True, text_color)
            tx = rect.x + (rect.width - text_surf.get_width()) // 2
            ty = rect.y + (rect.height - text_surf.get_height()) // 2
            surface.blit(text_surf, (tx, ty))

    @staticmethod
    def progress_arc(
        surface: Surface,
        center: Tuple[int, int],
        radius: int,
        progress: float,
        color: Color,
        *,
        width: int = 4,
        bg_color: Optional[Color] = None,
        start_angle: float = -math.pi / 2,
    ) -> None:
        """Draw a circular progress arc from *start_angle* by ``progress * 2π``.

        Parameters
        ----------
        progress:
            0.0 (empty) to 1.0 (full circle).
        start_angle:
            Starting angle in radians (default -π/2 = top of circle).
        """
        cx, cy = center
        r = max(1, radius)
        if bg_color is not None:
            pygame.draw.circle(surface, bg_color, (cx, cy), r, width)
        if progress <= 0:
            return
        sweep = min(progress, 1.0) * 2 * math.pi
        segments = max(4, int(r * sweep))
        points = []
        for i in range(segments + 1):
            angle = start_angle + sweep * (i / segments)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, width)

    @staticmethod
    def dotted_border(
        surface: Surface,
        rect: Rect,
        color: Color,
        *,
        dash_len: int = 6,
        gap_len: int = 4,
        width: int = 1,
    ) -> None:
        """Draw a dashed / dotted rectangular border."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        for edge_pts in [
            [(x + i, y) for i in range(w)],
            [(x + w - 1, y + i) for i in range(h)],
            [(x + w - 1 - i, y + h - 1) for i in range(w)],
            [(x, y + h - 1 - i) for i in range(h)],
        ]:
            dash = True
            count = 0
            for pt in edge_pts:
                if dash:
                    pygame.draw.circle(surface, color, pt, max(1, width // 2))
                count += 1
                if dash and count >= dash_len:
                    dash = False
                    count = 0
                elif not dash and count >= gap_len:
                    dash = True
                    count = 0

    @staticmethod
    def check_mark(
        surface: Surface,
        rect: Rect,
        color: Color,
        *,
        width: int = 2,
    ) -> None:
        """Draw a check-mark (✓) scaled to *rect*."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        # Bend point at 35% x, 65% y; tip at 100% x, 10% y; start at 0, 50%
        pts = [
            (x, y + int(h * 0.5)),
            (x + int(w * 0.35), y + int(h * 0.85)),
            (x + w, y + int(h * 0.1)),
        ]
        pygame.draw.lines(surface, color, False, pts, width)

    @staticmethod
    def cross_mark(
        surface: Surface,
        rect: Rect,
        color: Color,
        *,
        width: int = 2,
    ) -> None:
        """Draw an × mark scaled to *rect*."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        pygame.draw.line(surface, color, (x, y), (x + w - 1, y + h - 1), width)
        pygame.draw.line(surface, color, (x + w - 1, y), (x, y + h - 1), width)

    @staticmethod
    def chevron(
        surface: Surface,
        rect: Rect,
        direction: str,
        color: Color,
        *,
        width: int = 2,
    ) -> None:
        """Draw a chevron arrow (``"left"``, ``"right"``, ``"up"``, ``"down"``)."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        cx, cy = x + w // 2, y + h // 2
        m = min(w, h) // 4
        if direction == "right":
            pts = [(cx - m, y + m), (cx + m, cy), (cx - m, y + h - m)]
        elif direction == "left":
            pts = [(cx + m, y + m), (cx - m, cy), (cx + m, y + h - m)]
        elif direction == "down":
            pts = [(x + m, cy - m), (cx, cy + m), (x + w - m, cy - m)]
        else:  # "up"
            pts = [(x + m, cy + m), (cx, cy - m), (x + w - m, cy + m)]
        pygame.draw.lines(surface, color, False, pts, width)

    @staticmethod
    def separator(
        surface: Surface,
        rect: Rect,
        color: Color,
        *,
        horizontal: bool = True,
        width: int = 1,
    ) -> None:
        """Draw a single-pixel separator line through the center of *rect*."""
        if horizontal:
            cy = rect.centery
            pygame.draw.line(surface, color, (rect.x, cy), (rect.right - 1, cy), width)
        else:
            cx = rect.centerx
            pygame.draw.line(surface, color, (cx, rect.y), (cx, rect.bottom - 1), width)
