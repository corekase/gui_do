from pygame import Rect
from typing import TYPE_CHECKING

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..theme.color_theme import ColorTheme


class LabelControl(UiNode):
    """Simple text label control."""

    def __init__(self, control_id: str, rect: Rect, text: str) -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.title = False
        self.text_size = 16

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        old = factory.get_current_font_name()
        factory.set_font("titlebar" if self.title else "normal")
        try:
            rendered = factory.render_text(self.text, colour=theme.text, shadow=True)
        finally:
            while factory.get_current_font_name() != old:
                factory.set_last_font()
        surface.blit(rendered, self.rect.topleft)
