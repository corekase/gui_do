"""CanvasViewport — portable pan/zoom coordinate transform for CanvasControl.

Every spatial canvas application (maps, diagram editors, image viewers, game
level editors) needs identical pan and anchor-preserving zoom math.
:class:`CanvasViewport` provides that math as a standalone portable object so
that :class:`~gui_do.CanvasControl` users never have to re-implement it.

Usage::

    vp = CanvasViewport(content_size=(4096, 4096), min_scale=0.05, max_scale=16.0)

    # In the canvas event handler — convert screen pos to content coordinates:
    packet = canvas.poll_event()
    if packet.is_mouse_down():
        content_pos = vp.to_canvas(packet.local_pos)

    # Zoom toward the cursor (e.g. from a scroll-wheel event):
    if packet.is_mouse_wheel():
        factor = 1.1 if packet.wheel_delta > 0 else 1.0 / 1.1
        vp.zoom_at(anchor=packet.local_pos, factor=factor)

    # Pan (e.g. from a middle-button drag):
    if packet.is_mouse_motion() and middle_held:
        vp.pan(packet.rel)

    # Fit all content on screen:
    vp.fit_content(canvas.rect.size)

    # Reset to 1:1:
    vp.reset()

    # In the draw callback — transform a content rect to screen rect:
    screen_rect = pygame.Rect(*vp.to_screen(content_rect.topleft),
                               content_rect.w * vp.scale,
                               content_rect.h * vp.scale)

Coordinate conventions
-----------------------
- *screen space*  — pixel coordinates relative to the top-left of the canvas rect.
- *content space* — pixel coordinates within the underlying content surface.

``to_canvas(screen_pt)`` converts screen → content.
``to_screen(canvas_pt)`` converts content → screen.
"""
from __future__ import annotations

from typing import Optional, Tuple


class CanvasViewport:
    """2D pan + zoom transform for a canvas surface.

    Parameters
    ----------
    content_size:
        ``(width, height)`` of the content in pixels.
    min_scale / max_scale:
        Zoom range (defaults 0.05 – 32.0).
    initial_scale:
        Starting zoom level (default 1.0).
    initial_offset:
        Starting pan offset in screen pixels (default ``(0.0, 0.0)``).
    """

    def __init__(
        self,
        *,
        content_size: Tuple[int, int] = (1024, 1024),
        min_scale: float = 0.05,
        max_scale: float = 32.0,
        initial_scale: float = 1.0,
        initial_offset: Tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self._content_w: int = max(1, int(content_size[0]))
        self._content_h: int = max(1, int(content_size[1]))
        self._min_scale: float = float(min_scale)
        self._max_scale: float = float(max_scale)
        self._scale: float = max(self._min_scale, min(self._max_scale, float(initial_scale)))
        self._offset_x: float = float(initial_offset[0])
        self._offset_y: float = float(initial_offset[1])

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def scale(self) -> float:
        """Current zoom scale (1.0 = one content pixel per screen pixel)."""
        return self._scale

    @property
    def offset(self) -> Tuple[float, float]:
        """Current pan offset in screen pixels (content origin → screen origin)."""
        return (self._offset_x, self._offset_y)

    @property
    def content_size(self) -> Tuple[int, int]:
        """Content dimensions in pixels."""
        return (self._content_w, self._content_h)

    @property
    def min_scale(self) -> float:
        return self._min_scale

    @property
    def max_scale(self) -> float:
        return self._max_scale

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    def to_canvas(self, screen_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Convert a *screen_pos* (relative to canvas rect) to content coordinates."""
        return (
            (float(screen_pos[0]) - self._offset_x) / self._scale,
            (float(screen_pos[1]) - self._offset_y) / self._scale,
        )

    def to_screen(self, canvas_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Convert a *canvas_pos* (content space) to screen coordinates."""
        return (
            float(canvas_pos[0]) * self._scale + self._offset_x,
            float(canvas_pos[1]) * self._scale + self._offset_y,
        )

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def pan(self, delta: Tuple[float, float]) -> None:
        """Shift the viewport by *delta* screen pixels."""
        self._offset_x += float(delta[0])
        self._offset_y += float(delta[1])

    def zoom_at(self, anchor: Tuple[float, float], factor: float) -> None:
        """Zoom by *factor* keeping *anchor* (screen-space point) fixed in content space.

        The content point under *anchor* stays at the same screen position
        after the zoom.
        """
        factor = float(factor)
        if factor <= 0.0:
            return
        new_scale = max(self._min_scale, min(self._max_scale, self._scale * factor))
        if new_scale == self._scale:
            return
        ax = float(anchor[0])
        ay = float(anchor[1])
        # Content point under the anchor before zoom.
        cx = (ax - self._offset_x) / self._scale
        cy = (ay - self._offset_y) / self._scale
        self._scale = new_scale
        # Recompute offset so the same content point is still under the anchor.
        self._offset_x = ax - cx * self._scale
        self._offset_y = ay - cy * self._scale

    def zoom_to(
        self,
        scale: float,
        *,
        anchor: Optional[Tuple[float, float]] = None,
    ) -> None:
        """Set the absolute zoom *scale*, optionally anchored at a screen point."""
        new_scale = max(self._min_scale, min(self._max_scale, float(scale)))
        if anchor is not None:
            ax = float(anchor[0])
            ay = float(anchor[1])
            cx = (ax - self._offset_x) / self._scale
            cy = (ay - self._offset_y) / self._scale
            self._scale = new_scale
            self._offset_x = ax - cx * self._scale
            self._offset_y = ay - cy * self._scale
        else:
            self._scale = new_scale

    def set_offset(self, offset: Tuple[float, float]) -> None:
        """Set absolute pan offset in screen pixels."""
        self._offset_x = float(offset[0])
        self._offset_y = float(offset[1])

    def reset(self) -> None:
        """Restore scale 1.0 and offset (0, 0)."""
        self._scale = max(self._min_scale, min(self._max_scale, 1.0))
        self._offset_x = 0.0
        self._offset_y = 0.0

    def fit_content(
        self,
        viewport_size: Tuple[int, int],
        *,
        padding: int = 0,
    ) -> None:
        """Scale and centre content to fill *viewport_size* with optional *padding*.

        Picks the largest scale that fits both dimensions and centres the
        content in the viewport.
        """
        pad2 = 2 * max(0, int(padding))
        vw = max(1, int(viewport_size[0]) - pad2)
        vh = max(1, int(viewport_size[1]) - pad2)
        sx = vw / self._content_w
        sy = vh / self._content_h
        self._scale = max(self._min_scale, min(self._max_scale, min(sx, sy)))
        self._offset_x = (viewport_size[0] - self._content_w * self._scale) / 2.0
        self._offset_y = (viewport_size[1] - self._content_h * self._scale) / 2.0

    def clamp_to_content(self, viewport_size: Tuple[int, int]) -> None:
        """Prevent panning beyond content boundaries.

        When the scaled content is smaller than the viewport the content is
        centred; when larger the offset is clamped so content edges cannot
        scroll past the viewport edge.
        """
        vw = int(viewport_size[0])
        vh = int(viewport_size[1])
        content_w_px = self._content_w * self._scale
        content_h_px = self._content_h * self._scale

        if content_w_px <= vw:
            self._offset_x = (vw - content_w_px) / 2.0
        else:
            self._offset_x = max(vw - content_w_px, min(0.0, self._offset_x))

        if content_h_px <= vh:
            self._offset_y = (vh - content_h_px) / 2.0
        else:
            self._offset_y = max(vh - content_h_px, min(0.0, self._offset_y))
