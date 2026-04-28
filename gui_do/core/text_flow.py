"""TextFlow — paragraph layout engine for mixed-style text with word-wrap.

Renders a sequence of :class:`TextSpan` objects as word-wrapped, multi-line
text onto a ``pygame.Surface``.  Spans on the same logical line are joined
without a break; a ``\\n`` character in a span's text starts a new paragraph.

All font metrics are resolved through a :class:`~gui_do.ColorTheme` (and its
embedded :class:`~gui_do.FontManager`) so no font files are referenced
directly.

Usage::

    from gui_do import TextFlow, TextSpan

    spans = [
        TextSpan("Hello, ", role="body"),
        TextSpan("world!", bold=True, color=(255, 220, 0), role="body"),
        TextSpan("\\nThis is a new paragraph in ", role="body"),
        TextSpan("italic text.", italic=True, role="body"),
    ]

    flow = TextFlow(width=400, line_spacing=4)
    flow.set_content(spans)
    flow.layout(theme)            # re-call whenever width or content changes

    # In draw():
    used_height = flow.render(surface, x=10, y=20)
    print(flow.height)            # total height of laid-out text
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame
    from ..theme.color_theme import ColorTheme


# ---------------------------------------------------------------------------
# TextSpan
# ---------------------------------------------------------------------------


@dataclass
class TextSpan:
    """A single styled run of text within a :class:`TextFlow`.

    Parameters
    ----------
    text:
        The literal text.  ``\\n`` characters insert paragraph breaks.
    bold:
        Render this span bold.
    italic:
        Render this span italic.
    color:
        RGB or RGBA tuple.  ``None`` inherits the theme's default text color.
    role:
        Font role name resolved through the theme's :class:`~gui_do.FontManager`
        (e.g. ``"body"``, ``"title"``).
    """

    text: str
    bold: bool = False
    italic: bool = False
    color: Optional[Tuple] = None
    role: str = "body"


# ---------------------------------------------------------------------------
# Internal line representation
# ---------------------------------------------------------------------------


@dataclass
class _Word:
    """One whitespace-delimited token with its pre-rendered surface."""

    surface: object          # pygame.Surface
    width: int
    height: int
    ascent: int
    span_color: Optional[Tuple]


@dataclass
class _Line:
    """One rendered line of words."""

    words: List[_Word] = field(default_factory=list)
    total_width: int = 0
    height: int = 0
    ascent: int = 0


# ---------------------------------------------------------------------------
# TextFlow
# ---------------------------------------------------------------------------


class TextFlow:
    """Word-wrapping paragraph layout engine for mixed-style spans.

    Parameters
    ----------
    width:
        Maximum line width in pixels.  Words that do not fit are wrapped to
        the next line.
    line_spacing:
        Extra pixels added between lines (default 2).
    """

    def __init__(self, width: int, *, line_spacing: int = 2) -> None:
        self._width = max(1, int(width))
        self._line_spacing = int(line_spacing)
        self._spans: List[TextSpan] = []
        self._lines: List[_Line] = []
        self._height: int = 0
        self._laid_out = False

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        new_w = max(1, int(value))
        if new_w != self._width:
            self._width = new_w
            self._laid_out = False

    @property
    def height(self) -> int:
        """Total height of the laid-out text in pixels.  Valid after :meth:`layout`."""
        return self._height

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def set_content(self, spans: List[TextSpan]) -> None:
        """Set the text content and mark the layout as dirty."""
        self._spans = list(spans)
        self._laid_out = False
        self._lines.clear()
        self._height = 0

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def layout(self, theme: "ColorTheme") -> None:
        """Compute word-wrap layout using font metrics from *theme*.

        Must be called after :meth:`set_content` and whenever :attr:`width`
        changes.  Safe to call every frame — skips work when already up to date.
        """
        if self._laid_out:
            return
        self._lines.clear()
        self._height = 0

        # Build word tokens from spans
        tokens = self._tokenize(theme)
        if not tokens:
            self._laid_out = True
            return

        # Greedy line-fill
        current_line = _Line()
        space_width = self._measure_space(theme)

        for token in tokens:
            if token is None:
                # Paragraph break
                if current_line.words:
                    self._lines.append(current_line)
                current_line = _Line()
                continue

            gap = space_width if current_line.words else 0
            if current_line.total_width + gap + token.width > self._width and current_line.words:
                self._lines.append(current_line)
                current_line = _Line()
                gap = 0

            current_line.words.append(token)
            current_line.total_width += gap + token.width
            current_line.height = max(current_line.height, token.height)
            current_line.ascent = max(current_line.ascent, token.ascent)

        if current_line.words:
            self._lines.append(current_line)

        # Total height
        total = 0
        for i, line in enumerate(self._lines):
            total += line.height
            if i < len(self._lines) - 1:
                total += self._line_spacing
        self._height = total
        self._laid_out = True

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, surface: "pygame.Surface", x: int, y: int) -> int:
        """Blit laid-out text onto *surface* at ``(x, y)``.

        Returns the total height consumed (same as :attr:`height`).
        Call :meth:`layout` first.
        """
        if not self._laid_out or not self._lines:
            return 0

        space_width = max(4, self._width // 80)
        cursor_y = y
        for line in self._lines:
            cursor_x = x
            for word in line.words:
                # Baseline-align within the line
                baseline_offset = line.ascent - word.ascent
                surface.blit(word.surface, (cursor_x, cursor_y + baseline_offset))
                cursor_x += word.width + space_width
            cursor_y += line.height + self._line_spacing
        return self._height

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tokenize(self, theme: "ColorTheme") -> List:
        """Return a list of _Word objects, with None for paragraph breaks."""
        result = []
        for span in self._spans:
            color = span.color if span.color is not None else theme.text
            parts = span.text.split("\n")
            for part_idx, part in enumerate(parts):
                if part_idx > 0:
                    result.append(None)  # paragraph break
                words = part.split()
                for word_text in words:
                    surf = self._render_word(word_text, span, color, theme)
                    if surf is not None:
                        w, h = surf.get_size()
                        try:
                            font = self._get_font(span, theme)
                            ascent = font.get_ascent() if font is not None else h
                        except Exception:
                            ascent = h
                        result.append(_Word(surface=surf, width=w, height=h, ascent=ascent, span_color=span.color))
        return result

    def _render_word(self, text: str, span: TextSpan, color, theme: "ColorTheme"):
        try:
            font = self._get_font(span, theme)
            if font is None:
                return None
            return font.render(text, True, color)
        except Exception:
            return None

    def _get_font(self, span: TextSpan, theme: "ColorTheme"):
        try:
            fm = theme.fonts
            role = span.role if span.role else "body"
            return fm.get_font(role_name=role)
        except Exception:
            try:
                import pygame
                return pygame.font.Font(None, 16)
            except Exception:
                return None

    def _measure_space(self, theme: "ColorTheme") -> int:
        try:
            if self._spans:
                font = self._get_font(self._spans[0], theme)
                if font is not None:
                    w, _ = font.size(" ")
                    return w
        except Exception:
            pass
        return 4
