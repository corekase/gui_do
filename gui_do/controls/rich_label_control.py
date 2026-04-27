"""RichLabelControl — read-only word-wrapping text display."""
from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_V_PAD = 4
_H_PAD = 6


class RichLabelControl(UiNode):
    """Read-only multi-line label with automatic word wrapping.

    Text is reflowed when the control's rect or text changes.  Vertical
    overflow is silently clipped; horizontal padding is ``6`` pixels on
    each side.

    Usage::

        label = RichLabelControl("desc", Rect(10, 10, 300, 200), text="Hello world!")
        panel.add(label)
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        text: str = "",
        font_role: str = "body",
        font_size: int = 16,
        align: str = "left",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._text = str(text)
        self._font_role = str(font_role) or "body"
        self._font_size = max(6, int(font_size))
        align = str(align)
        if align not in ("left", "center", "right"):
            align = "left"
        self._align = align
        self._color: Optional[Tuple[int, int, int]] = color
        # Render cache
        self._lines: List[pygame.Surface] = []
        self._cache_key: Optional[tuple] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        new = str(value)
        if self._text == new:
            return
        self._text = new
        self._cache_key = None
        self.invalidate()

    @property
    def font_role(self) -> str:
        return self._font_role

    @font_role.setter
    def font_role(self, value: str) -> None:
        role = str(value).strip() or "body"
        if self._font_role == role:
            return
        self._font_role = role
        self._cache_key = None
        self.invalidate()

    @property
    def font_size(self) -> int:
        return self._font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        size = max(6, int(value))
        if self._font_size == size:
            return
        self._font_size = size
        self._cache_key = None
        self.invalidate()

    @property
    def align(self) -> str:
        return self._align

    @align.setter
    def align(self, value: str) -> None:
        a = str(value) if str(value) in ("left", "center", "right") else "left"
        if self._align == a:
            return
        self._align = a
        self._cache_key = None
        self.invalidate()

    def accepts_mouse_focus(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        color = self._color if self._color is not None else (theme.text if self.enabled else theme.medium)
        font_revision = theme.fonts.revision
        cache_key = (
            self._text,
            self._font_role,
            self._font_size,
            color,
            font_revision,
            self.rect.width,
            self._align,
        )
        if self._cache_key != cache_key:
            self._lines = self._wrap_text(theme, color)
            self._cache_key = cache_key

        y = self.rect.top + _V_PAD
        max_y = self.rect.bottom
        for surf in self._lines:
            if y >= max_y:
                break
            lw, lh = surf.get_size()
            x = self._x_for_line(lw)
            if y + lh <= max_y:
                surface.blit(surf, (x, y))
            y += lh

    def _wrap_text(self, theme: "ColorTheme", color: tuple) -> List[pygame.Surface]:
        """Word-wrap self._text into a list of rendered line surfaces."""
        max_width = self.rect.width - _H_PAD * 2
        if max_width < 1:
            return []

        result: List[pygame.Surface] = []
        paragraphs = self._text.split("\n")
        for para in paragraphs:
            words = para.split(" ")
            current_line = ""
            for word in words:
                test = (current_line + " " + word).strip() if current_line else word
                tw, _ = theme.fonts.font_instance(self._font_role, size=self._font_size).text_size(test)
                if tw <= max_width:
                    current_line = test
                else:
                    if current_line:
                        result.append(
                            theme.render_text(
                                current_line,
                                role=self._font_role,
                                size=self._font_size,
                                color=color,
                            )
                        )
                    current_line = word
            if current_line:
                result.append(
                    theme.render_text(
                        current_line,
                        role=self._font_role,
                        size=self._font_size,
                        color=color,
                    )
                )
            elif not para:
                # Blank line — emit a small spacer
                result.append(
                    theme.render_text(
                        " ",
                        role=self._font_role,
                        size=self._font_size,
                        color=color,
                    )
                )
        return result

    def _x_for_line(self, line_width: int) -> int:
        if self._align == "center":
            return self.rect.left + max(0, (self.rect.width - line_width) // 2)
        if self._align == "right":
            return self.rect.right - line_width
        return self.rect.left + _H_PAD

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def preferred_height(self, theme: "ColorTheme") -> int:
        """Return the pixel height needed to display all text without clipping."""
        color = self._color or theme.text
        lines = self._wrap_text(theme, color)
        return sum(s.get_height() for s in lines) + _V_PAD * 2
