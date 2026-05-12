"""TextAreaControl — multi-line editable text field with word wrap and scrolling."""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base.abstract_text_input_control import AbstractTextInputControl
from ...overlays.clipboard import ClipboardManager

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

_H_PAD = 6
_V_PAD = 4
_SCROLL_SPEED = 3  # lines per mouse wheel tick


class TextAreaControl(AbstractTextInputControl):
    _FONT_SCALE: float = 1.0   # 16/16 — body-size multi-line text area

    def _resolve_fs(self, theme=None) -> int:
        """Resolve the effective font size from explicit override or scaled default."""
        if self._font_size is not None:
            return self._font_size
        if theme is not None and hasattr(theme, "fonts") and theme.fonts is not None:
            return theme.fonts.scaled_size(self._FONT_SCALE)
        return max(8, round(16 * float(self._FONT_SCALE)))

    def get_char_index_at_pixel(self, x: int, y: Optional[int] = None, theme=None) -> int:
        font = self._get_font(theme)
        if font is None:
            return 0
        try:
            line_h = font.line_height
        except Exception:
            return self._cursor_pos
        y_val = y if y is not None else self.rect.top
        rel_y = y_val - self.rect.top - _V_PAD + self._scroll_top
        line_spans = self._get_visual_line_spans()
        if not line_spans:
            return 0
        line_idx = max(0, min(rel_y // line_h, len(line_spans) - 1))
        abs_offset, _, line_text = line_spans[line_idx]
        rel_x = x - self.rect.left - _H_PAD
        if rel_x <= 0:
            return abs_offset
        if not line_text:
            return abs_offset
        def measure(n):
            px, _ = font.text_size(line_text[:n])
            return px
        lo = 0
        hi = len(line_text)
        while lo < hi:
            mid = (lo + hi) // 2
            if measure(mid) < rel_x:
                lo = mid + 1
            else:
                hi = mid
        idx = lo
        if idx > 0 and idx < len(line_text):
            left_w = measure(idx - 1)
            right_w = measure(idx)
            if abs(rel_x - left_w) <= abs(rel_x - right_w):
                idx -= 1
        return abs_offset + idx

    def get_pixel_for_char_index(self, index: int, theme=None) -> Tuple[int, int]:
        font = self._get_font(theme)
        line_spans = self._get_visual_line_spans()
        for line_idx, (line_start, line_end, line_text) in enumerate(line_spans):
            if index <= line_end:
                px, _ = font.text_size(line_text[:index - line_start])
                y = self.rect.top + _V_PAD + line_idx * font.line_height
                return (self.rect.left + _H_PAD + px, y)
        # Fallback: end of last line
        _, _, last_line = line_spans[-1]
        px, _ = font.text_size(last_line)
        y = self.rect.top + _V_PAD + (len(line_spans) - 1) * font.line_height
        return (self.rect.left + _H_PAD + px, y)

    def _get_font(self, theme) -> Optional["pygame.font.Font"]:
        if theme is not None and hasattr(theme, "fonts") and theme.fonts is not None:
            return theme.fonts.font_instance(self._font_role, size=self._resolve_fs(theme))
        return None

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
        font_size: Optional[int] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._value = str(value)
        self._placeholder = str(placeholder)
        self._max_length = max_length
        self._read_only = bool(read_only)
        self._on_change = on_change
        self._font_role = str(font_role)
        self._font_size: Optional[int] = None if font_size is None else max(6, int(font_size))
        self.tab_index = 0  # focusable by default
        self.key_activatable = False  # K_RETURN inserts newline, not button-activate

        # Cursor / selection (absolute char offsets into self._value)
        self._cursor_pos: int = len(self._value)
        self._sel_anchor: Optional[int] = None
        self._sel_active: Optional[int] = None

        # Scroll state (in pixel rows from top of content)
        self._scroll_top: int = 0

        # Render cache
        self._line_cache_key: Optional[tuple] = None
        self._wrapped_lines: List[str] = []  # wrapped text segments
        self._measure_font = None

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
        self._on_text_edit_focus_changed(is_focused, invalidate=True)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        self._update_text_edit_blink(dt_seconds)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
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
            if self._is_focus_traversal_key(event.key, event.mod):
                return False
            handled = self._handle_key(event.key, event.mod, app)
            return handled or True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return False
            # Use unified caret placement logic
            idx = self.get_char_index_at_pixel(event.pos[0], event.pos[1], theme)
            self._cursor_pos = idx
            self._sel_anchor = idx
            self._sel_active = idx
            self._drag_selecting = True
            self._reset_blink()
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_MOTION and self._drag_selecting:
            idx = self.get_char_index_at_pixel(event.pos[0], event.pos[1], theme)
            self._sel_active = idx
            self._cursor_pos = idx
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
            if event.pos is None or not self.rect.collidepoint(event.pos):
                return False
            delta = event.wheel_y
            line_h = self._line_height(app)
            self._scroll_top = max(
                0, self._scroll_top - int(delta) * _SCROLL_SPEED * line_h
            )
            self.invalidate()
            return True

        return False

    @staticmethod
    def _is_focus_traversal_key(key: int, mod: int) -> bool:
        if key != pygame.K_TAB:
            return False
        if bool(mod & pygame.KMOD_ALT) or bool(mod & pygame.KMOD_META):
            return False
        return True

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
            new_pos = self._get_visual_line_bounds()[0]
            self._move_cursor(new_pos, shift)
            return True

        if key == pygame.K_END:
            new_pos = self._get_visual_line_bounds()[1]
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
                self._placeholder, role=self._font_role, size=self._resolve_fs(theme), color=theme.medium
            )
            surface.blit(surf, (r.left + _H_PAD, r.top + _V_PAD))
            return

        line_h = self._get_line_height(theme)
        lines = self._get_wrapped_lines(theme)

        # Clip to content area
        clip_rect = pygame.Rect(r.left, r.top, r.width, r.height)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect.clip(old_clip) if old_clip else clip_rect)

        sel_lo, sel_hi = self.selection_range
        y = r.top + _V_PAD - self._scroll_top
        cursor_y: Optional[int] = None
        cursor_x: Optional[int] = None

        for line_start_abs, line_end_abs, line_text in self._get_visual_line_spans(lines):
            line_len = len(line_text)

            if y + line_h >= r.top and y < r.bottom:
                # Selection highlight
                if sel_lo != sel_hi:
                    s_start = max(0, sel_lo - line_start_abs)
                    s_end = min(line_len, sel_hi - line_start_abs)
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
                    line_text, role=self._font_role, size=self._resolve_fs(theme), color=text_color
                )
                surface.blit(text_surf, (r.left + _H_PAD, y))

            # Cursor position
            if self._cursor_pos >= line_start_abs and self._cursor_pos <= line_end_abs:
                offset_in_line = self._cursor_pos - line_start_abs
                cursor_x = r.left + _H_PAD + self._text_width(theme, line_text[:offset_in_line])
                cursor_y = y

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
        line_spans = self._get_visual_line_spans()
        if not line_spans:
            return self._cursor_pos
        cursor_line = 0
        cursor_col = 0
        for i, (line_start, line_end, _) in enumerate(line_spans):
            if self._cursor_pos <= line_end:
                cursor_line = i
                cursor_col = self._cursor_pos - line_start
                break
        target_line = max(0, min(len(line_spans) - 1, cursor_line + direction))
        if target_line == cursor_line:
            if direction < 0:
                return 0
            return len(self._value)
        target_start, target_end, _ = line_spans[target_line]
        target_len = target_end - target_start
        new_col = min(cursor_col, target_len)
        return target_start + new_col

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
        abs_offset, _, line_text = self._get_visual_line_spans(lines)[line_idx]
        rel_x = pos[0] - self.rect.left - _H_PAD
        if rel_x <= 0:
            return abs_offset
        if not line_text:
            return abs_offset

        measure = self._measure_prefix_width(app, line_text)

        lo = 0
        hi = len(line_text)
        while lo < hi:
            mid = (lo + hi) // 2
            if measure(mid) < rel_x:
                lo = mid + 1
            else:
                hi = mid

        idx = lo
        if idx <= 0:
            return abs_offset
        if idx >= len(line_text):
            return abs_offset + len(line_text)

        left_w = measure(idx - 1)
        right_w = measure(idx)
        if abs(rel_x - left_w) <= abs(rel_x - right_w):
            idx -= 1
        return abs_offset + idx

    def _measure_prefix_width(self, app: "GuiApplication", line_text: str):
        """Return a callable that measures width of line_text[:n] with cached font usage."""
        try:
            theme_font = app.theme.fonts.font_instance(self._font_role, size=self._resolve_fs(app.theme))

            def _measure(n: int) -> int:
                w, _ = theme_font.text_size(line_text[:n])
                return int(w)

            return _measure
        except Exception:
            if self._measure_font is None:
                try:
                    self._measure_font = theme.fonts.font_instance(getattr(self, "_font_role", "text_area.text"), size=self._resolve_fs(theme))
                except Exception:
                    self._measure_font = False

            if self._measure_font:

                def _measure(n: int) -> int:
                    w, _ = self._measure_font.text_size(line_text[:n])
                    return int(w)

                return _measure

            def _measure(n: int) -> int:
                return int(n * (self._resolve_fs() // 2))

            return _measure

    def _get_visual_line_spans(self, lines: Optional[List[str]] = None) -> List[Tuple[int, int, str]]:
        if lines is None:
            lines = self._get_wrapped_lines_cached()
        if not lines:
            return [(0, 0, "")]
        spans: List[Tuple[int, int, str]] = []
        raw_index = 0
        value = self._value
        value_len = len(value)
        for line_text in lines:
            line_start = raw_index
            line_end = min(value_len, line_start + len(line_text))
            spans.append((line_start, line_end, line_text))
            raw_index = line_end
            if raw_index < value_len and value[raw_index:raw_index + 1] == "\n":
                raw_index += 1
        return spans

    def _get_visual_line_bounds(self) -> Tuple[int, int]:
        for line_start, line_end, _ in self._get_visual_line_spans():
            if self._cursor_pos <= line_end:
                return (line_start, line_end)
        value_len = len(self._value)
        return (value_len, value_len)

    def _text_width(self, theme: "ColorTheme", text: str) -> int:
        try:
            w, _ = theme.fonts.font_instance(self._font_role, size=self._resolve_fs(theme)).text_size(text)
            return w
        except Exception:
            return len(text) * (self._resolve_fs() // 2)

    def _get_line_height(self, theme: "ColorTheme") -> int:
        try:
            return theme.fonts.font_instance(self._font_role, size=self._resolve_fs(theme)).line_height
        except Exception:
            return self._resolve_fs() + 2

    def _line_height(self, app: "GuiApplication") -> int:
        try:
            return app.theme.fonts.font_instance(self._font_role, size=self._resolve_fs(app.theme)).line_height
        except Exception:
            return self._resolve_fs() + 2

    def _get_wrapped_lines(self, theme: "ColorTheme") -> List[str]:
        max_width = self.rect.width - _H_PAD * 2
        cache_key = (self._value, self._font_role, self._resolve_fs(), max_width)
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
            if not para:
                result.append("")
                continue
            start = 0
            para_len = len(para)
            while start < para_len:
                best_end = start
                last_space_end = -1
                overflowed = False
                for end in range(start + 1, para_len + 1):
                    candidate = para[start:end]
                    if self._text_width(theme, candidate) <= max_width:
                        best_end = end
                        if candidate.endswith(" "):
                            last_space_end = end
                        continue
                    overflowed = True
                    break
                if best_end == start:
                    best_end = start + 1
                wrap_end = last_space_end if overflowed and last_space_end > start else best_end
                result.append(para[start:wrap_end])
                start = wrap_end
        return result

    def _fire_change(self) -> None:
        self._line_cache_key = None
        self.invalidate()
        if self._on_change is not None:
            self._on_change(self._value)

    def _reset_blink(self) -> None:
        self._reset_text_edit_blink()
