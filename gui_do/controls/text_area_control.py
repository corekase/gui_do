"""TextAreaControl — multi-line editable text field with word wrap and scrolling."""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.clipboard import ClipboardManager

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_BLINK_INTERVAL = 0.5
_H_PAD = 6
_V_PAD = 4
_SCROLL_SPEED = 3  # lines per mouse wheel tick


class TextAreaControl(UiNode):
    """Multi-line editable text area with word wrap, clipboard, and scrolling.

    Keyboard shortcuts mirror :class:`TextInputControl`:
    - ``Ctrl+A`` — select all
    - ``Ctrl+C`` / ``Ctrl+X`` / ``Ctrl+V`` — clipboard
    - Arrow keys, ``Home``, ``End``, ``Page Up``, ``Page Down``
    - ``Enter`` inserts a newline
    - ``Backspace`` / ``Delete`` remove characters

    Usage::

        area = TextAreaControl(
            "notes", Rect(10, 10, 400, 200),
            value="line one\\nline two",
            on_change=lambda v: print(v),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        value: str = "",
        placeholder: str = "",
        max_length: Optional[int] = None,
        read_only: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
        font_size: int = 16,
    ) -> None:
        super().__init__(control_id, rect)
        self._value = str(value)
        self._placeholder = str(placeholder)
        self._max_length = max_length
        self._read_only = bool(read_only)
        self._on_change = on_change
        self._font_role = str(font_role)
        self._font_size = max(6, int(font_size))
        self.tab_index = 0  # focusable by default
        self.key_activatable = False  # K_RETURN inserts newline, not button-activate

        # Cursor / selection (absolute char offsets into self._value)
        self._cursor_pos: int = len(self._value)
        self._sel_anchor: Optional[int] = None
        self._sel_active: Optional[int] = None

        # Scroll state (in pixel rows from top of content)
        self._scroll_top: int = 0

        # Blink
        self._blink_elapsed: float = 0.0
        self._cursor_visible: bool = True

        # Mouse drag
        self._drag_selecting: bool = False

        # Render cache
        self._line_cache_key: Optional[tuple] = None
        self._wrapped_lines: List[str] = []  # wrapped text segments

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        self.set_value(v)

    def set_value(self, value: str) -> None:
        """Set value programmatically without firing on_change."""
        self._value = str(value)
        if self._max_length is not None:
            self._value = self._value[: self._max_length]
        self._cursor_pos = len(self._value)
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_top = 0
        self._line_cache_key = None
        self.invalidate()

    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    @property
    def selection_range(self) -> Tuple[int, int]:
        """Return ``(start, end)`` of selection; equal means no selection."""
        if self._sel_anchor is None or self._sel_active is None:
            return (self._cursor_pos, self._cursor_pos)
        lo = min(self._sel_anchor, self._sel_active)
        hi = max(self._sel_anchor, self._sel_active)
        return (lo, hi)

    def select_all(self) -> None:
        self._sel_anchor = 0
        self._sel_active = len(self._value)
        self._cursor_pos = len(self._value)
        self.invalidate()

    @property
    def read_only(self) -> bool:
        return self._read_only

    @read_only.setter
    def read_only(self, value: bool) -> None:
        self._read_only = bool(value)
        self.invalidate()

    def accepts_focus(self) -> bool:
        return self.tab_index >= 0

    def accepts_mouse_focus(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Focus hooks
    # ------------------------------------------------------------------

    def on_focus_changed(self, is_focused: bool) -> None:
        if is_focused:
            try:
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(self.rect)
            except Exception:
                pass
            self._cursor_visible = True
            self._blink_elapsed = 0.0
        else:
            try:
                pygame.key.stop_text_input()
            except Exception:
                pass
            self._drag_selecting = False
        self.invalidate()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        if not self._focused:
            return
        self._blink_elapsed += dt_seconds
        if self._blink_elapsed >= _BLINK_INTERVAL:
            self._blink_elapsed = 0.0
            self._cursor_visible = not self._cursor_visible
            self.invalidate()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.TEXT_INPUT:
            if not self._focused or self._read_only:
                return False
            text = event.text or ""
            if text:
                self._insert_text(text)
                self._fire_change()
                self._reset_blink()
            return True

        if event.kind == EventType.TEXT_EDITING:
            return self._focused

        if event.kind == EventType.KEY_DOWN:
            if not self._focused:
                return False
            return self._handle_key(event.key, event.mod, app)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return False
            self._cursor_pos = self._pos_to_char(event.pos, app)
            self._sel_anchor = self._cursor_pos
            self._sel_active = self._cursor_pos
            self._drag_selecting = True
            self._reset_blink()
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_MOTION and self._drag_selecting:
            self._cursor_pos = self._pos_to_char(event.pos, app)
            self._sel_active = self._cursor_pos
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            if self._drag_selecting:
                self._drag_selecting = False
                if self._sel_anchor == self._sel_active:
                    self._sel_anchor = None
                    self._sel_active = None
                self.invalidate()
                return True

        if event.kind == EventType.MOUSE_WHEEL:
            if not self.rect.collidepoint(getattr(event, "pos", (-1, -1))):
                return False
            delta = getattr(event, "y", 0)
            line_h = self._line_height(app)
            self._scroll_top = max(
                0, self._scroll_top - int(delta) * _SCROLL_SPEED * line_h
            )
            self.invalidate()
            return True

        return False

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def _handle_key(self, key: int, mod: int, app: "GuiApplication") -> bool:
        ctrl = bool(mod & pygame.KMOD_CTRL)
        shift = bool(mod & pygame.KMOD_SHIFT)

        if ctrl:
            if key == pygame.K_a:
                self.select_all()
                return True
            if key == pygame.K_c:
                sel = self.selection_range
                if sel[0] != sel[1]:
                    ClipboardManager.copy(self._value[sel[0]: sel[1]])
                return True
            if key == pygame.K_x:
                if not self._read_only:
                    sel = self.selection_range
                    if sel[0] != sel[1]:
                        ClipboardManager.copy(self._value[sel[0]: sel[1]])
                        self._delete_selection()
                        self._fire_change()
                return True
            if key == pygame.K_v:
                if not self._read_only:
                    text = ClipboardManager.paste()
                    if text:
                        self._insert_text(text)
                        self._fire_change()
                return True

        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if not self._read_only:
                self._insert_text("\n")
                self._fire_change()
            return True

        if key == pygame.K_BACKSPACE:
            if not self._read_only:
                sel = self.selection_range
                if sel[0] != sel[1]:
                    self._delete_selection()
                elif self._cursor_pos > 0:
                    self._value = self._value[: self._cursor_pos - 1] + self._value[self._cursor_pos:]
                    self._cursor_pos -= 1
                    self._sel_anchor = None
                    self._sel_active = None
                self._fire_change()
            self.invalidate()
            return True

        if key == pygame.K_DELETE:
            if not self._read_only:
                sel = self.selection_range
                if sel[0] != sel[1]:
                    self._delete_selection()
                elif self._cursor_pos < len(self._value):
                    self._value = self._value[: self._cursor_pos] + self._value[self._cursor_pos + 1:]
                self._fire_change()
            self.invalidate()
            return True

        if key == pygame.K_LEFT:
            new_pos = max(0, self._cursor_pos - 1)
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_RIGHT:
            new_pos = min(len(self._value), self._cursor_pos + 1)
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_HOME:
            # Move to start of line
            line_start = self._value.rfind("\n", 0, self._cursor_pos)
            new_pos = 0 if line_start == -1 else line_start + 1
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_END:
            line_end = self._value.find("\n", self._cursor_pos)
            new_pos = len(self._value) if line_end == -1 else line_end
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_UP:
            new_pos = self._move_vertical(-1, app)
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_DOWN:
            new_pos = self._move_vertical(1, app)
            self._move_cursor(new_pos, shift)
            return True

        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        r = self.rect

        # Background
        bg = theme.light if self.enabled else theme.medium
        pygame.draw.rect(surface, bg, r)
        border_color = theme.highlight if self._focused else theme.medium
        pygame.draw.rect(surface, border_color, r, 1)

        if not self._value and self._placeholder and not self._focused:
            surf = theme.render_text(
                self._placeholder, role=self._font_role, size=self._font_size, color=theme.medium
            )
            surface.blit(surf, (r.left + _H_PAD, r.top + _V_PAD))
            return

        line_h = self._get_line_height(theme)
        lines = self._get_wrapped_lines(theme)

        # Clip to content area
        clip_rect = pygame.Rect(r.left, r.top, r.width, r.height)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        sel_lo, sel_hi = self.selection_range
        abs_offset = 0
        y = r.top + _V_PAD - self._scroll_top
        cursor_y: Optional[int] = None
        cursor_x: Optional[int] = None

        for line_text in lines:
            line_len = len(line_text)
            line_end_abs = abs_offset + line_len

            if y + line_h >= r.top and y < r.bottom:
                # Selection highlight
                if sel_lo != sel_hi:
                    s_start = max(0, sel_lo - abs_offset)
                    s_end = min(line_len, sel_hi - abs_offset)
                    if s_start < s_end:
                        px_start = self._text_width(theme, line_text[:s_start])
                        px_end = self._text_width(theme, line_text[:s_end])
                        sel_rect = pygame.Rect(
                            r.left + _H_PAD + px_start, y,
                            px_end - px_start, line_h
                        )
                        pygame.draw.rect(surface, theme.highlight, sel_rect)

                # Text
                text_color = theme.text if self.enabled else theme.medium
                text_surf = theme.render_text(
                    line_text, role=self._font_role, size=self._font_size, color=text_color
                )
                surface.blit(text_surf, (r.left + _H_PAD, y))

            # Cursor position
            if self._cursor_pos >= abs_offset and self._cursor_pos <= line_end_abs:
                offset_in_line = self._cursor_pos - abs_offset
                cursor_x = r.left + _H_PAD + self._text_width(theme, line_text[:offset_in_line])
                cursor_y = y

            abs_offset = line_end_abs + 1  # +1 for the newline that was stripped
            y += line_h

        # Draw cursor
        if self._focused and self._cursor_visible and cursor_x is not None and cursor_y is not None:
            cx = cursor_x
            pygame.draw.line(surface, theme.text, (cx, cursor_y), (cx, cursor_y + line_h - 2), 1)

        surface.set_clip(old_clip)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _insert_text(self, text: str) -> None:
        """Insert text at cursor, deleting selection first."""
        sel_lo, sel_hi = self.selection_range
        if sel_lo != sel_hi:
            self._value = self._value[:sel_lo] + self._value[sel_hi:]
            self._cursor_pos = sel_lo
            self._sel_anchor = None
            self._sel_active = None
        new_val = self._value[: self._cursor_pos] + text + self._value[self._cursor_pos:]
        if self._max_length is not None:
            new_val = new_val[: self._max_length]
        inserted = len(new_val) - len(self._value)
        self._value = new_val
        self._cursor_pos = min(len(self._value), self._cursor_pos + inserted)
        self._line_cache_key = None
        self.invalidate()

    def _delete_selection(self) -> None:
        sel_lo, sel_hi = self.selection_range
        if sel_lo == sel_hi:
            return
        self._value = self._value[:sel_lo] + self._value[sel_hi:]
        self._cursor_pos = sel_lo
        self._sel_anchor = None
        self._sel_active = None
        self._line_cache_key = None

    def _move_cursor(self, new_pos: int, extend_selection: bool) -> None:
        if extend_selection:
            if self._sel_anchor is None:
                self._sel_anchor = self._cursor_pos
            self._sel_active = new_pos
        else:
            self._sel_anchor = None
            self._sel_active = None
        self._cursor_pos = new_pos
        self.invalidate()

    def _move_vertical(self, direction: int, app: "GuiApplication") -> int:
        """Return a new cursor position after moving up (-1) or down (+1) one visual line."""
        try:
            line_h = self._line_height(app)
        except Exception:
            return self._cursor_pos
        if line_h <= 0:
            return self._cursor_pos
        lines = self._get_wrapped_lines_cached()
        # Find which line the cursor is on
        abs_offset = 0
        cursor_line = 0
        cursor_col = 0
        for i, line_text in enumerate(lines):
            line_len = len(line_text)
            if self._cursor_pos <= abs_offset + line_len:
                cursor_line = i
                cursor_col = self._cursor_pos - abs_offset
                break
            abs_offset += line_len + 1
        target_line = max(0, min(len(lines) - 1, cursor_line + direction))
        if target_line == cursor_line:
            if direction < 0:
                return 0
            return len(self._value)
        # Recalculate abs offset for target line
        new_offset = sum(len(lines[i]) + 1 for i in range(target_line))
        target_len = len(lines[target_line])
        new_col = min(cursor_col, target_len)
        return new_offset + new_col

    def _pos_to_char(self, pos: Tuple[int, int], app: "GuiApplication") -> int:
        """Convert a pixel position to an absolute character offset."""
        try:
            line_h = self._line_height(app)
        except Exception:
            return self._cursor_pos
        if line_h <= 0:
            return self._cursor_pos
        rel_y = pos[1] - self.rect.top - _V_PAD + self._scroll_top
        line_idx = max(0, rel_y // line_h)
        lines = self._get_wrapped_lines_cached()
        if not lines:
            return 0
        line_idx = min(line_idx, len(lines) - 1)
        abs_offset = sum(len(lines[i]) + 1 for i in range(line_idx))
        line_text = lines[line_idx]
        rel_x = pos[0] - self.rect.left - _H_PAD
        # Binary-search for closest character
        best = 0
        best_dist = abs(rel_x)
        for i in range(1, len(line_text) + 1):
            try:
                w, _ = pygame.font.SysFont(None, self._font_size).size(line_text[:i])
            except Exception:
                w = i * (self._font_size // 2)
            dist = abs(rel_x - w)
            if dist < best_dist:
                best = i
                best_dist = dist
        return abs_offset + best

    def _text_width(self, theme: "ColorTheme", text: str) -> int:
        try:
            w, _ = theme.fonts.font_instance(self._font_role, size=self._font_size).text_size(text)
            return w
        except Exception:
            return len(text) * (self._font_size // 2)

    def _get_line_height(self, theme: "ColorTheme") -> int:
        try:
            return theme.fonts.font_instance(self._font_role, size=self._font_size).line_height
        except Exception:
            return self._font_size + 2

    def _line_height(self, app: "GuiApplication") -> int:
        try:
            return app.theme.fonts.font_instance(self._font_role, size=self._font_size).line_height
        except Exception:
            return self._font_size + 2

    def _get_wrapped_lines(self, theme: "ColorTheme") -> List[str]:
        max_width = self.rect.width - _H_PAD * 2
        cache_key = (self._value, self._font_role, self._font_size, max_width)
        if self._line_cache_key == cache_key:
            return self._wrapped_lines
        self._wrapped_lines = self._wrap(theme, max_width)
        self._line_cache_key = cache_key
        return self._wrapped_lines

    def _get_wrapped_lines_cached(self) -> List[str]:
        """Return cached wrapped lines; falls back to raw split if no cache available."""
        if self._wrapped_lines is not None and self._line_cache_key is not None:
            return self._wrapped_lines
        return self._value.split("\n")

    def _wrap(self, theme: "ColorTheme", max_width: int) -> List[str]:
        """Word-wrap self._value into a list of display line strings."""
        if max_width < 1:
            return self._value.split("\n")
        result: List[str] = []
        for para in self._value.split("\n"):
            words = para.split(" ")
            current = ""
            for word in words:
                test = (current + " " + word).strip() if current else word
                w = self._text_width(theme, test)
                if w <= max_width:
                    current = test
                else:
                    if current:
                        result.append(current)
                    current = word
            result.append(current)
        return result

    def _fire_change(self) -> None:
        self._line_cache_key = None
        self.invalidate()
        if self._on_change is not None:
            self._on_change(self._value)

    def _reset_blink(self) -> None:
        self._cursor_visible = True
        self._blink_elapsed = 0.0
