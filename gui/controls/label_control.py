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
        self._text = str(text)
        self._title = False
        self._text_size = 16

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        next_text = str(value)
        if self._text == next_text:
            return
        self._text = next_text
        self.invalidate()

    @property
    def title(self) -> bool:
        return self._title

    @title.setter
    def title(self, value: bool) -> None:
        next_title = bool(value)
        if self._title == next_title:
            return
        self._title = next_title
        self.invalidate()

    @property
    def text_size(self) -> int:
        return self._text_size

    @text_size.setter
    def text_size(self, value: int) -> None:
        next_size = max(1, int(value))
        if self._text_size == next_size:
            return
        self._text_size = next_size
        self.invalidate()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        colour = theme.text if self.enabled else theme.medium
        rendered = theme.render_text(self._text, size=self._text_size, title=self._title, color=colour, shadow=True)
        surface.blit(rendered, self.rect.topleft)
