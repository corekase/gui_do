from __future__ import annotations

from typing import Callable, Optional

import pygame
from pygame import Rect
from pygame.draw import polygon, rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP

from ..core.ui_node import UiNode


class ArrowBoxControl(UiNode):
    """Arrow button with optional repeat activation while held."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        direction: int,
        on_activate: Optional[Callable[[], None]] = None,
        repeat_interval_seconds: float = 0.08,
    ) -> None:
        super().__init__(control_id, rect)
        self.direction = int(direction) % 360
        self.on_activate = on_activate
        self.repeat_interval_seconds = float(repeat_interval_seconds)
        self._pressed = False
        self._hovered = False
        self._timer_id = ("arrow_repeat", self.control_id)
        self._visuals = None
        self._visual_key = None

    def _invoke(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2:
            self._hovered = self.rect.collidepoint(raw)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self._pressed = True
                self._invoke()
                if self.repeat_interval_seconds > 0:
                    app.timers.add_timer(self._timer_id, self.repeat_interval_seconds, self._invoke)
                return True
        if event.type == MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            if self._pressed:
                self._pressed = False
                app.timers.remove_timer(self._timer_id)
                return True
        return False

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.dark if self._pressed else theme.medium, self.rect, 0)
            draw_rect(surface, theme.dark, self.rect, 2)
            cx, cy = self.rect.center
            if self.direction in (90, 270):
                points = [(cx - 4, cy - 6), (cx + 4, cy - 6), (cx, cy + 6)]
                if self.direction == 270:
                    points = [(cx - 4, cy + 6), (cx + 4, cy + 6), (cx, cy - 6)]
            else:
                points = [(cx - 6, cy - 4), (cx - 6, cy + 4), (cx + 6, cy)]
                if self.direction == 180:
                    points = [(cx + 6, cy - 4), (cx + 6, cy + 4), (cx - 6, cy)]
            polygon(surface, theme.text, points)
            return
        visual_key = (self.rect.width, self.rect.height, int(self.direction) % 360)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.draw_arrow_visuals(self.rect, self.direction)
            self._visual_key = visual_key
        hovered = self._hovered
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self._pressed,
            hovered=hovered,
        )
        surface.blit(selected, self.rect)
