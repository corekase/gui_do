from pygame import Rect
from typing import TYPE_CHECKING, Optional

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..theme.color_theme import ColorTheme


class LabelControl(UiNode):
    """Simple text label control."""

    _VALID_ALIGNS = ("left", "center", "right")

    def __init__(self, control_id: str, rect: Rect, text: str, align: str = "left") -> None:
        super().__init__(control_id, rect)
        self._text = str(text)
        self._font_role = "body"
        self._font_size = 16
        if align not in self._VALID_ALIGNS:
            raise ValueError(f"align must be one of {self._VALID_ALIGNS!r}, got {align!r}")
        self._align = align
        self._rendered_surface: Optional["pygame.Surface"] = None
        self._render_key: Optional[tuple] = None

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
    def font_role(self) -> str:
        return self._font_role

    @font_role.setter
    def font_role(self, value: str) -> None:
        next_role = str(value).strip()
        if not next_role:
            raise ValueError("font_role must be a non-empty string")
        if self._font_role == next_role:
            return
        self._font_role = next_role
        self.invalidate()

    @property
    def font_size(self) -> int:
        return self._font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        next_size = max(1, int(value))
        if self._font_size == next_size:
            return
        self._font_size = next_size
        self.invalidate()

    @property
    def align(self) -> str:
        return self._align

    @align.setter
    def align(self, value: str) -> None:
        if value not in self._VALID_ALIGNS:
            raise ValueError(f"align must be one of {self._VALID_ALIGNS!r}, got {value!r}")
        if self._align == value:
            return
        self._align = value
        self.invalidate()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        colour = theme.text if self.enabled else theme.medium
        font_revision = theme.fonts.revision if hasattr(theme, "fonts") else 0
        render_key = (self._text, self._font_role, self._font_size, colour, font_revision)
        if self._render_key != render_key:
            self._rendered_surface = theme.render_text(
                self._text, role=self._font_role, size=self._font_size, color=colour, shadow=True
            )
            self._render_key = render_key
        rendered = self._rendered_surface
        rw, rh = rendered.get_size()
        y = self.rect.top + max(0, (self.rect.height - rh) // 2)
        if self._align == "center":
            x = self.rect.left + max(0, (self.rect.width - rw) // 2)
        elif self._align == "right":
            x = self.rect.right - rw
        else:
            x = self.rect.left
        surface.blit(rendered, (x, y))
