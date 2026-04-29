"""AnimatedImageControl — a UiNode that displays a :class:`~gui_do.FrameAnimation`.

Usage::

    from gui_do import AnimatedImageControl, SpriteSheet, FrameAnimation

    sheet = SpriteSheet(atlas_surface, frame_w=64, frame_h=64)
    anim  = FrameAnimation(sheet, frames=list(range(8)), fps=12)

    ctrl = AnimatedImageControl("player", Rect(100, 100, 64, 64), animation=anim)

    # Call once per frame (before draw):
    ctrl.tick(dt)
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...graphics.sprite_sheet import FrameAnimation

if TYPE_CHECKING:
    from ...theme.color_theme import ColorTheme


class AnimatedImageControl(UiNode):
    """A scene-graph node that renders a :class:`~gui_do.FrameAnimation`.

    Parameters
    ----------
    control_id:
        Unique node identifier.
    rect:
        Bounding rect on screen.
    animation:
        The :class:`~gui_do.FrameAnimation` to render.  May be swapped at
        runtime via :attr:`animation`.
    scale:
        When ``True`` (default) each frame is scaled to fill *rect*.
        When ``False`` frames are blitted at their native size (clipped to rect).
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        animation: FrameAnimation,
        *,
        scale: bool = True,
    ) -> None:
        super().__init__(control_id, rect)
        self._animation = animation
        self._scale = scale

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def animation(self) -> FrameAnimation:
        return self._animation

    @animation.setter
    def animation(self, value: FrameAnimation) -> None:
        self._animation = value
        self.invalidate()

    @property
    def scale(self) -> bool:
        return self._scale

    @scale.setter
    def scale(self, value: bool) -> None:
        self._scale = bool(value)
        self.invalidate()

    def accepts_mouse_focus(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def tick(self, dt: float) -> None:
        """Advance the animation by *dt* seconds.  Call once per frame."""
        self._animation.update(dt)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if not self.visible:
            return
        frame_surf = self._animation.current_surface
        if self._scale and frame_surf.get_size() != self.rect.size:
            frame_surf = pygame.transform.smoothscale(frame_surf, self.rect.size)
        surface.blit(frame_surf, self.rect)
