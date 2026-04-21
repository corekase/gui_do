from typing import Callable, Optional

import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN

from ..core.ui_node import UiNode


class ToggleControl(UiNode):
    """Two-state toggle control."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        text_on: str,
        text_off: Optional[str] = None,
        pushed: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.text_on = text_on
        self.text_off = text_off if text_off is not None else text_on
        self.pushed = bool(pushed)
        self.on_toggle = on_toggle
        self.hovered = False

    def handle_event(self, event, _app) -> bool:
        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self.pushed = not self.pushed
                if self.on_toggle is not None:
                    self.on_toggle(self.pushed)
                return True
        return False

    def draw(self, surface, theme) -> None:
        if self.pushed:
            fill = theme.handle_active
            text = self.text_on
        else:
            fill = theme.light if self.hovered else theme.medium
            text = self.text_off
        draw_rect(surface, fill, self.rect, 0)
        draw_rect(surface, theme.dark, self.rect, 2)
        text_bitmap = theme.render_text(text, size=16, color=theme.text, shadow=True)
        text_rect = text_bitmap.get_rect(center=self.rect.center)
        surface.blit(text_bitmap, text_rect)
