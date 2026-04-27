"""RichLabelControl — read-only word-wrapping text display with inline styles."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme

_V_PAD = 4
_H_PAD = 6


class RichLabelControl(UiNode):
    """Read-only multi-line label with automatic word wrapping.

    Text is reflowed when the control's rect or text changes. Vertical
    overflow is silently clipped; horizontal padding is ``6`` pixels on
    each side. Inline style markers are supported:

    - ``**bold**``
    - ``_italic_``
    - ```code```

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
        self._style_role_cache: dict[tuple[str, int], dict[str, str]] = {}

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
        """Word-wrap styled text into rendered line surfaces."""
        max_width = self.rect.width - _H_PAD * 2
        if max_width < 1:
            return []

        result: List[pygame.Surface] = []
        paragraphs = self._text.split("\n")
        for para in paragraphs:
            if not para:
                # Blank line — emit a small spacer
                result.append(
                    theme.render_text(
                        " ",
                        role=self._font_role,
                        size=self._font_size,
                        color=color,
                    )
                )
                continue

            line_tokens: List[tuple[str, str]] = []
            line_width = 0
            for segment_text, segment_style in self._parse_inline_segments(para):
                for token in re.findall(r"\s+|\S+", segment_text):
                    if not line_tokens and token.isspace():
                        continue
                    token_width = self._measure_text(theme, token, segment_style)
                    if line_tokens and (line_width + token_width) > max_width:
                        result.append(self._render_line(theme, line_tokens, color))
                        line_tokens = []
                        line_width = 0
                        if token.isspace():
                            continue
                    line_tokens.append((token, segment_style))
                    line_width += token_width

            if line_tokens:
                result.append(self._render_line(theme, line_tokens, color))
        return result

    def _parse_inline_segments(self, text: str) -> List[tuple[str, str]]:
        """Parse a line with simple inline style markers into text/style segments."""
        segments: List[tuple[str, str]] = []
        buf: List[str] = []
        bold = False
        italic = False
        code = False
        i = 0

        def style_name() -> str:
            if code:
                return "code"
            if bold and italic:
                return "bold_italic"
            if bold:
                return "bold"
            if italic:
                return "italic"
            return "base"

        def flush() -> None:
            if not buf:
                return
            piece = "".join(buf)
            buf.clear()
            if segments and segments[-1][1] == style_name():
                prev_text, prev_style = segments[-1]
                segments[-1] = (prev_text + piece, prev_style)
            else:
                segments.append((piece, style_name()))

        while i < len(text):
            if text.startswith("**", i) and not code:
                flush()
                bold = not bold
                i += 2
                continue
            ch = text[i]
            if ch == "_" and not code:
                flush()
                italic = not italic
                i += 1
                continue
            if ch == "`":
                flush()
                code = not code
                i += 1
                continue
            buf.append(ch)
            i += 1
        flush()
        return segments

    def _style_roles(self, theme: "ColorTheme") -> dict[str, str]:
        cache_key = (self._font_role, self._font_size)
        cached = self._style_role_cache.get(cache_key)
        if cached is not None:
            return cached

        base = self._font_role
        size = self._font_size
        roles = {
            "base": base,
            "bold": f"{base}.rich.bold.{size}",
            "italic": f"{base}.rich.italic.{size}",
            "bold_italic": f"{base}.rich.bold_italic.{size}",
            "code": f"{base}.rich.code.{size}",
        }

        if not theme.fonts.has_role(roles["bold"]):
            theme.fonts.register_role(roles["bold"], size=size, bold=True)
        if not theme.fonts.has_role(roles["italic"]):
            theme.fonts.register_role(roles["italic"], size=size, italic=True)
        if not theme.fonts.has_role(roles["bold_italic"]):
            theme.fonts.register_role(roles["bold_italic"], size=size, bold=True, italic=True)
        if not theme.fonts.has_role(roles["code"]):
            theme.fonts.register_role(roles["code"], size=size, system_name="consolas")

        self._style_role_cache[cache_key] = roles
        return roles

    def _role_for_style(self, theme: "ColorTheme", style: str) -> str:
        roles = self._style_roles(theme)
        return roles.get(style, self._font_role)

    def _measure_text(self, theme: "ColorTheme", text: str, style: str) -> int:
        role = self._role_for_style(theme, style)
        width, _ = theme.fonts.font_instance(role, size=self._font_size).text_size(text)
        return int(width)

    def _render_piece(self, theme: "ColorTheme", text: str, style: str, base_color: tuple) -> pygame.Surface:
        role = self._role_for_style(theme, style)
        color = theme.highlight if style == "code" else base_color
        return theme.render_text(text, role=role, size=self._font_size, color=color, shadow=False)

    def _render_line(self, theme: "ColorTheme", tokens: List[tuple[str, str]], color: tuple) -> pygame.Surface:
        pieces = [self._render_piece(theme, token, style, color) for token, style in tokens]
        width = sum(piece.get_width() for piece in pieces)
        height = max((piece.get_height() for piece in pieces), default=1)
        line_surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
        x = 0
        for piece in pieces:
            line_surface.blit(piece, (x, 0))
            x += piece.get_width()
        return line_surface

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
