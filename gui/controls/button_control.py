from typing import Callable, Optional

import pygame

from pygame import Rect
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN

from ..core.ui_node import UiNode


class ButtonControl(UiNode):
    """Clickable push button control."""

    def __init__(self, control_id: str, rect: Rect, text: str, on_click: Optional[Callable[[], None]] = None, style: str = "box") -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.on_click = on_click
        self.style = style
        self.hovered = False
        self._visuals = None

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                if self.on_click is not None:
                    self.on_click()
                return True
        return False

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            fill = theme.light if self.hovered else theme.medium
            draw_rect(surface, fill, self.rect, 0)
            draw_rect(surface, theme.dark, self.rect, 2)
            text_bitmap = theme.render_text(self.text, size=16, title=False, color=theme.text, shadow=True)
            text_rect = text_bitmap.get_rect(center=self.rect.center)
            surface.blit(text_bitmap, text_rect)
            return
        if self._visuals is None:
            self._visuals = factory.build_interactive_visuals(self.style, self.text, self.rect)
        if not self.enabled:
            surface.blit(self._visuals.disabled, self.rect)
        elif self.hovered:
            surface.blit(self._visuals.hover, self.rect)
        else:
            surface.blit(self._visuals.idle, self.rect)
