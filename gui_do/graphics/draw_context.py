"""DrawContext — per-draw-pass context object passed to UiNode.draw().

A :class:`DrawContext` encapsulates the surface, clip rect, draw phase,
opacity, and local coordinate offset for one rendering pass.  Controls
receive a ``DrawContext`` from the render loop and use it rather than calling
pygame directly with raw surface references.

Draw phases
-----------
- ``BACKGROUND``  — scene background layer (pristine/backdrops)
- ``FOREGROUND``  — normal control draw pass
- ``OVERLAY``     — transient overlays drawn on top of scene controls
- ``DEBUG``       — developer diagnostic visualizations (rects, labels, etc.)

Usage::

    from gui_do import DrawContext, DrawPhase

    # In a control's draw():
    def draw(self, ctx: DrawContext) -> None:
        if not ctx.is_visible_phase:
            return
        sub = ctx.clip_to(self.rect)
        sub.surface.fill(self.bg_color, sub.local_rect)
        theme.render_text(sub.surface, self.text, sub.local_rect)

    # Render loop:
    ctx = DrawContext(surface=screen, clip_rect=screen.get_rect(),
                      phase=DrawPhase.FOREGROUND, opacity=1.0)
    for control in scene_controls:
        if dirty_tracker.overlaps_dirty(control.rect):
            control.draw(ctx)
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Tuple

import pygame
from pygame import Rect, Surface


class DrawPhase(Enum):
    """Ordered rendering phases for the draw pipeline."""
    BACKGROUND = "background"
    FOREGROUND = "foreground"
    OVERLAY = "overlay"
    DEBUG = "debug"


class DrawContext:
    """Render context passed to :meth:`~gui_do.UiNode.draw` each frame.

    Parameters
    ----------
    surface:
        The pygame ``Surface`` to draw onto.
    clip_rect:
        The screen-space clipping rect for this draw call.  Pixels outside
        this rect should not be modified.
    phase:
        The current render phase (BACKGROUND, FOREGROUND, OVERLAY, DEBUG).
    opacity:
        Multiplicative opacity [0.0, 1.0].  Controls that support alpha
        blending should multiply their per-pixel alpha by this value.
    local_offset:
        Cumulative scroll/clip offset applied to convert screen coordinates
        to local node coordinates.  Set by scroll containers when drawing
        clipped children.
    """

    __slots__ = ("surface", "clip_rect", "phase", "opacity", "local_offset")

    def __init__(
        self,
        surface: Surface,
        clip_rect: Rect,
        *,
        phase: DrawPhase = DrawPhase.FOREGROUND,
        opacity: float = 1.0,
        local_offset: Tuple[int, int] = (0, 0),
    ) -> None:
        self.surface: Surface = surface
        self.clip_rect: Rect = Rect(clip_rect)
        self.phase: DrawPhase = phase
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.local_offset: Tuple[int, int] = local_offset

    # ------------------------------------------------------------------
    # Phase helpers
    # ------------------------------------------------------------------

    @property
    def is_background(self) -> bool:
        return self.phase == DrawPhase.BACKGROUND

    @property
    def is_foreground(self) -> bool:
        return self.phase == DrawPhase.FOREGROUND

    @property
    def is_overlay(self) -> bool:
        return self.phase == DrawPhase.OVERLAY

    @property
    def is_debug(self) -> bool:
        return self.phase == DrawPhase.DEBUG

    @property
    def is_visible_phase(self) -> bool:
        """True for phases that produce visible pixels (BACKGROUND, FOREGROUND, OVERLAY)."""
        return self.phase != DrawPhase.DEBUG

    # ------------------------------------------------------------------
    # Derived contexts
    # ------------------------------------------------------------------

    @property
    def local_rect(self) -> Rect:
        """Return ``clip_rect`` translated into node-local coordinates."""
        ox, oy = self.local_offset
        r = self.clip_rect
        return Rect(r.x - ox, r.y - oy, r.width, r.height)

    def clip_to(self, rect: Rect, *, opacity: Optional[float] = None) -> "DrawContext":
        """Return a child :class:`DrawContext` clipped to *rect*.

        The child context intersects the parent ``clip_rect`` with *rect* so
        that scroll-container children cannot draw outside their viewport.
        """
        clipped = self.clip_rect.clip(rect)
        return DrawContext(
            self.surface,
            clipped,
            phase=self.phase,
            opacity=opacity if opacity is not None else self.opacity,
            local_offset=self.local_offset,
        )

    def with_offset(self, dx: int, dy: int) -> "DrawContext":
        """Return a child context with *local_offset* shifted by ``(dx, dy)``.

        Scroll containers use this to inform children of the cumulative
        scroll displacement so coordinate transforms remain correct.
        """
        ox, oy = self.local_offset
        return DrawContext(
            self.surface,
            self.clip_rect,
            phase=self.phase,
            opacity=self.opacity,
            local_offset=(ox + dx, oy + dy),
        )

    def with_phase(self, phase: DrawPhase) -> "DrawContext":
        """Return a copy of this context with a different *phase*."""
        return DrawContext(
            self.surface,
            self.clip_rect,
            phase=phase,
            opacity=self.opacity,
            local_offset=self.local_offset,
        )

    def with_opacity(self, opacity: float) -> "DrawContext":
        """Return a copy of this context with a new *opacity* (clamped 0-1)."""
        return DrawContext(
            self.surface,
            self.clip_rect,
            phase=self.phase,
            opacity=opacity,
            local_offset=self.local_offset,
        )

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def apply_clip(self) -> None:
        """Set the pygame surface clip rect to ``self.clip_rect``."""
        self.surface.set_clip(self.clip_rect)

    def clear_clip(self) -> None:
        """Remove the pygame surface clip rect."""
        self.surface.set_clip(None)

    def fill(self, color: Tuple[int, int, int], rect: Optional[Rect] = None) -> None:
        """Fill *rect* (defaults to ``clip_rect``) with *color*."""
        target = rect if rect is not None else self.clip_rect
        self.surface.fill(color, target)
