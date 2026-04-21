from typing import Callable, Optional

import pygame

from pygame import Rect
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP

from ..core.ui_node import UiNode


class ButtonControl(UiNode):
    """Clickable push button control."""

    def __init__(self, control_id: str, rect: Rect, text: str, on_click: Optional[Callable[[], None]] = None, style: str = "box") -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.on_click = on_click
        self.style = style
        self.hovered = False
        self.pressed = False
        self._visuals = None
        self._visual_key = None

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self.pressed = True
                return True
        if event.type == MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.hovered:
                if self.on_click is not None:
                    self.on_click()
                return True
            return was_pressed
        return False

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            if self.pressed and self.hovered:
                fill = theme.dark
            else:
                fill = theme.light if self.hovered else theme.medium
            draw_rect(surface, fill, self.rect, 0)
            draw_rect(surface, theme.dark, self.rect, 2)
            text_bitmap = theme.render_text(self.text, size=16, title=False, color=theme.text, shadow=True)
            text_rect = text_bitmap.get_rect(center=self.rect.center)
            surface.blit(text_bitmap, text_rect)
            return
        visual_key = (self.style, self.text, self.rect.width, self.rect.height)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.build_interactive_visuals(self.style, self.text, self.rect)
            self._visual_key = visual_key
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pressed and self.hovered,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
