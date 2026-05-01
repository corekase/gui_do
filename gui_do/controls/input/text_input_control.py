"""Single-line text input control with cursor, selection, masking, and IME support."""
from __future__ import annotations

from typing import Callable, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base.abstract_text_input_control import AbstractTextInputControl
from ...overlays.clipboard import ClipboardManager

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

_H_PADDING = 4


class TextInputControl(AbstractTextInputControl):
    def _build_display_raw_mapping(self):
        """
        Build mappings between display string indices and raw value indices.
        Returns (display_to_raw, raw_to_display):
        - display_to_raw[i]: raw index for display index i (None if literal)
        - raw_to_display[j]: display index for raw index j
        """
        display = self._get_display_value()
        raw = self._value
        # If no formatter, 1:1 mapping
        if not self._display_value_provider or display == raw:
            display_to_raw = [i for i in range(len(display) + 1)]
            raw_to_display = [i for i in range(len(raw) + 1)]
            return display_to_raw, raw_to_display

        # For formatters, try to align digits/characters
        display_to_raw = [None] * (len(display) + 1)
        raw_to_display = [None] * (len(raw) + 1)
        di = 0
        ri = 0
        while di < len(display) and ri < len(raw):
            if display[di] == raw[ri]:
                display_to_raw[di] = ri
                raw_to_display[ri] = di
                di += 1
                ri += 1
            elif display[di] in raw:
                # Try to sync up by advancing raw
                ri += 1
            else:
                # Literal in display
                display_to_raw[di] = None
                di += 1
        # Fill trailing indices
        for i in range(di, len(display) + 1):
            display_to_raw[i] = len(raw)
        for j in range(ri, len(raw) + 1):
            raw_to_display[j] = len(display)
        # Fill None with nearest valid
        last = 0
        for i, v in enumerate(display_to_raw):
            if v is not None:
                last = v
            else:
                display_to_raw[i] = last
        last = 0
        for i, v in enumerate(raw_to_display):
            if v is not None:
                last = v
            else:
                raw_to_display[i] = last
        return display_to_raw, raw_to_display

    """Single-line editable text field with cursor, selection, masking, and clipboard."""

    def __init__(self, control_id: str, rect: Rect, value: str = "", placeholder: str = "", max_length: Optional[int] = None, masked: bool = False, on_change: Optional[Callable[[str], None]] = None, on_submit: Optional[Callable[[str], None]] = None, input_filter: Optional[Callable[[str], str]] = None, font_role: str = "body", display_value_provider: Optional[Callable[[], str]] = None) -> None:
        super().__init__(control_id, rect)
        self._value = str(value)
        self._placeholder = str(placeholder)
        self._max_length = max_length
        self._masked = bool(masked)
        self._on_change = on_change
        self._on_submit = on_submit
        self._input_filter = input_filter
        self._font_role = font_role
        self.tab_index = 0
        self._display_value_provider = display_value_provider
        self._cursor_pos = len(self._value)
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_offset_px = 0
    _FONT_SCALE: float = 1.25   # 20/16 — slightly larger for text input legibility

    def get_char_index_at_pixel(self, x: int, y: Optional[int] = None, theme=None) -> int:
        """Map pixel x to logical (raw) caret index using formatter-aware mapping."""
        font = self._get_font(theme)
        display = self._get_display_value()
        x_local = x - self.rect.left - _H_PADDING + self._scroll_offset_px
        if x_local <= 0 or not display:
            return 0
        lo = 0
        hi = len(display)
        def measure(n):
            px, _ = font.text_size(display[:n]) if hasattr(font, "text_size") else font.size(display[:n])
            return px
        while lo < hi:
            mid = (lo + hi) // 2
            if measure(mid) < x_local:
                lo = mid + 1
            else:
                hi = mid
        disp_idx = lo
        # Snap to closest display index
        if disp_idx > 0 and disp_idx < len(display):
            left_w = measure(disp_idx - 1)
            right_w = measure(disp_idx)
            if abs(x_local - left_w) <= abs(x_local - right_w):
                disp_idx -= 1
        # Map display index to nearest editable raw index
        display_to_raw, _ = self._build_display_raw_mapping()
        # Find nearest editable position (not None)
        search_range = list(range(disp_idx, -1, -1)) + list(range(disp_idx + 1, len(display) + 1))
        for idx in search_range:
            raw_idx = display_to_raw[idx]
            if raw_idx is not None:
                return raw_idx
        return 0

    def get_pixel_for_char_index(self, index: int, theme=None) -> Tuple[int, int]:
        font = self._get_font(theme)
        display = self._get_display_value()
        _, raw_to_display = self._build_display_raw_mapping()
        disp_idx = raw_to_display[index] if index < len(raw_to_display) else len(display)
        px, _ = font.text_size(display[:disp_idx]) if hasattr(font, "text_size") else font.size(display[:disp_idx])
        return (self.rect.left + _H_PADDING - self._scroll_offset_px + px, self.rect.top)

    def _get_font(self, theme) -> Optional["pygame.font.Font"]:
        from ...theme.color_theme import get_global_font_manager
        font_manager = get_global_font_manager()
        if font_manager is not None:
            return font_manager.font_instance(getattr(self, "_font_role", "controls.control"), size=font_manager.scaled_size(self._FONT_SCALE))
        # Fallback: use theme if provided
        if theme is not None and hasattr(theme, "fonts") and theme.fonts is not None:
            return theme.fonts.font_instance(getattr(self, "_font_role", "controls.control"), size=theme.fonts.scaled_size(self._FONT_SCALE))
        return None

    def _get_display_value(self) -> str:
        if self._display_value_provider is not None:
            return self._display_value_provider()
        if self._masked:
            return "*" * len(self._value)
        return self._value

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
        self._scroll_offset_px = 0
        self.invalidate()

    def set_value_with_cursor(self, value: str, cursor_pos: int) -> None:
        """Set value programmatically while preserving an explicit cursor index."""
        self._value = str(value)
        if self._max_length is not None:
            self._value = self._value[: self._max_length]
        self._cursor_pos = max(0, min(int(cursor_pos), len(self._value)))
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_to_cursor()
        self.invalidate()

    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    @property
    def selection_range(self) -> Tuple[int, int]:
        """Return (start, end) of selection. start == end means no selection."""
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

    def clear_selection(self) -> None:
        self._sel_anchor = None
        self._sel_active = None
        self.invalidate()

    def accepts_focus(self) -> bool:
        return self.tab_index >= 0

    def accepts_mouse_focus(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Focus hooks
    # ------------------------------------------------------------------

    def on_focus_changed(self, is_focused: bool) -> None:
        self._on_text_edit_focus_changed(is_focused, invalidate=False)

    # ------------------------------------------------------------------
    # Update (blink timer)
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        self._update_text_edit_blink(dt_seconds)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            return False

        # TEXT_INPUT: IME-safe character insertion
        if event.kind == EventType.TEXT_INPUT:
            if not self._focused:
                return False
            text = event.text or ""
            if text:
                self._insert_text(text, theme=theme)
                if self._on_change is not None:
                    self._on_change(self._value)
                self._reset_blink()
            return True

        # TEXT_EDITING: IME composition preview — ignore for now (do not consume)
        if event.kind == EventType.TEXT_EDITING:
            return self._focused

        # KEY_DOWN
        if event.kind == EventType.KEY_DOWN:
            if not self._focused:
                return False
            key = event.key
            mod = event.mod
            ctrl = bool(mod & pygame.KMOD_CTRL)
            shift = bool(mod & pygame.KMOD_SHIFT)
            return self._handle_key(key, ctrl, shift, app, theme=theme)

        # Mouse events
        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return False
            # Reset scroll offset so mapping is always relative to visible text
            self._scroll_offset_px = 0
            idx = self.get_char_index_at_pixel(event.pos[0], None, theme)
            self._cursor_pos = idx
            self._sel_anchor = idx
            self._sel_active = idx
            self._drag_selecting = True
            self._reset_blink()
            self._scroll_to_cursor(theme=theme)
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_MOTION and self._drag_selecting:
            idx = self.get_char_index_at_pixel(event.pos[0], None, theme)
            self._sel_active = idx
            self._cursor_pos = idx
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            if self._drag_selecting:
                self._drag_selecting = False
                # If anchor == active, clear selection (pure cursor placement)
                if self._sel_anchor == self._sel_active:
                    self._sel_anchor = None
                    self._sel_active = None
                self.invalidate()
                return True

        return False

    def _handle_key(self, key: int, ctrl: bool, shift: bool, app: "GuiApplication", theme=None) -> bool:
        if ctrl:
            if key == pygame.K_a:
                self.select_all()
                return True
            if key == pygame.K_c:
                sel = self.selection_range
                if sel[0] != sel[1]:
                    selected_text = self._get_display_value()[sel[0]:sel[1]]
                    ClipboardManager.copy(selected_text if not self._masked else "")
                return True
            if key == pygame.K_x:
                sel = self.selection_range
                if sel[0] != sel[1]:
                    if not self._masked:
                        ClipboardManager.copy(self._value[sel[0]:sel[1]])
                    self._delete_selection(theme=theme)
                    if self._on_change is not None:
                        self._on_change(self._value)
                return True
            if key == pygame.K_v:
                text = ClipboardManager.paste()
                if text:
                    self._insert_text(text, theme=theme)
                    if self._on_change is not None:
                        self._on_change(self._value)
                return True

        if key == pygame.K_BACKSPACE:
            sel = self.selection_range
            if sel[0] != sel[1]:
                self._delete_selection(theme=theme)
            elif self._cursor_pos > 0:
                self._value = self._value[:self._cursor_pos - 1] + self._value[self._cursor_pos:]
                self._cursor_pos -= 1
                self._sel_anchor = None
                self._sel_active = None
                self._scroll_to_cursor(theme=theme)
            if self._on_change is not None:
                self._on_change(self._value)
            self.invalidate()
            return True

        if key == pygame.K_DELETE:
            sel = self.selection_range
            if sel[0] != sel[1]:
                self._delete_selection(theme=theme)
            elif self._cursor_pos < len(self._value):
                self._value = self._value[:self._cursor_pos] + self._value[self._cursor_pos + 1:]
                self._scroll_to_cursor(theme=theme)
            if self._on_change is not None:
                self._on_change(self._value)
            self.invalidate()
            return True

        if key == pygame.K_LEFT:
            new_pos = max(0, self._cursor_pos - 1)
            if shift:
                if self._sel_anchor is None:
                    self._sel_anchor = self._cursor_pos
                self._sel_active = new_pos
            else:
                self._sel_anchor = None
                self._sel_active = None
            self._cursor_pos = new_pos
            self._scroll_to_cursor(theme=theme)
            self.invalidate()
            return True

        if key == pygame.K_RIGHT:
            new_pos = min(len(self._value), self._cursor_pos + 1)
            if shift:
                if self._sel_anchor is None:
                    self._sel_anchor = self._cursor_pos
                self._sel_active = new_pos
            else:
                self._sel_anchor = None
                self._sel_active = None
            self._cursor_pos = new_pos
            self._scroll_to_cursor(theme=theme)
            self.invalidate()
            return True

        if key == pygame.K_HOME:
            new_pos = 0
            if shift:
                if self._sel_anchor is None:
                    self._sel_anchor = self._cursor_pos
                self._sel_active = new_pos
            else:
                self._sel_anchor = None
                self._sel_active = None
            self._cursor_pos = new_pos
            self._scroll_to_cursor(theme=theme)
            self.invalidate()
            return True

        if key == pygame.K_END:
            new_pos = len(self._value)
            if shift:
                if self._sel_anchor is None:
                    self._sel_anchor = self._cursor_pos
                self._sel_active = new_pos
            else:
                self._sel_anchor = None
                self._sel_active = None
            self._cursor_pos = new_pos
            self._scroll_to_cursor(theme=theme)
            self.invalidate()
            return True

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self._on_submit is not None:
                self._on_submit(self._value)
            return True

        if key == pygame.K_ESCAPE:
            try:
                app.focus.clear_focus()
            except Exception:
                pass
            return True

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_display_value(self) -> str:
        if self._display_value_provider is not None:
            return self._display_value_provider()
        if self._masked:
            return "*" * len(self._value)
        return self._value

    def _insert_text(self, text: str, theme=None) -> None:
        if self._input_filter is not None:
            text = self._input_filter(str(text))
            if not text:
                return
        sel = self.selection_range
        if sel[0] != sel[1]:
            self._delete_selection(theme=theme)
        available = len(text)
        if self._max_length is not None:
            available = max(0, self._max_length - len(self._value))
        text = text[:available]
        self._value = self._value[:self._cursor_pos] + text + self._value[self._cursor_pos:]
        self._cursor_pos += len(text)
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_to_cursor(theme=theme)
        self.invalidate()

    def _delete_selection(self, theme=None) -> None:
        sel = self.selection_range
        if sel[0] == sel[1]:
            return
        self._value = self._value[:sel[0]] + self._value[sel[1]:]
        self._cursor_pos = sel[0]
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_to_cursor(theme=theme)

    def _scroll_to_cursor(self, theme=None) -> None:
        """Adjust scroll so cursor is visible."""
        font = self._get_font(theme)
        if font is None:
            return
        display = self._get_display_value()
        cursor_px, _ = font.text_size(display[:self._cursor_pos]) if hasattr(font, "text_size") else font.size(display[:self._cursor_pos])
        visible_width = self.rect.width - 2 * _H_PADDING
        if cursor_px < self._scroll_offset_px:
            self._scroll_offset_px = cursor_px
        elif cursor_px > self._scroll_offset_px + visible_width:
            self._scroll_offset_px = cursor_px - visible_width + 4
        self._scroll_offset_px = max(0, self._scroll_offset_px)


    def _get_font(self, theme) -> Optional["pygame.font.Font"]:
        from ...theme.color_theme import get_global_font_manager
        font_manager = get_global_font_manager()
        if font_manager is not None:
            return font_manager.font_instance(getattr(self, "_font_role", "controls.control"), size=font_manager.scaled_size(self._FONT_SCALE))
        if theme is not None and hasattr(theme, "fonts") and theme.fonts is not None:
            return theme.fonts.font_instance(getattr(self, "_font_role", "controls.control"), size=theme.fonts.scaled_size(self._FONT_SCALE))
        return None

    def _get_display_value(self) -> str:
        if self._display_value_provider is not None:
            return self._display_value_provider()
        if self._masked:
            return "*" * len(self._value)
        return self._value

    def _reset_blink(self) -> None:
        self._reset_text_edit_blink()

    # ------------------------------------------------------------------
    # Value-state serialization
    # ------------------------------------------------------------------

    def capture_state(self) -> dict:  # type: ignore[override]
        """Return current text value and cursor position."""
        return {"value": str(self._value), "cursor_pos": int(self._cursor_pos)}

    def restore_state(self, state: dict) -> None:  # type: ignore[override]
        """Restore text value and cursor position."""
        if "value" in state:
            self.set_value_with_cursor(
                str(state["value"]),
                int(state.get("cursor_pos", len(str(state["value"])))),
            )

    # ------------------------------------------------------------------
    # Intrinsic sizing
    # ------------------------------------------------------------------

    def preferred_size(self, available_width: int = -1, available_height: int = -1) -> "tuple[int, int]":  # type: ignore[override]
        """Return the natural height of a single text-input row.

        The control is not height-constrained by content so the preferred
        height is the current ``rect`` height.  Width is unconstrained
        (fill available) by default.
        """
        w = available_width if available_width > 0 else self.rect.width
        return (w, self.rect.height)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self._visible:
            return
        # Background
        bg_color = theme.background
        border_color = theme.text if self._focused else theme.medium
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)

        # Clip to inner rect
        clip_rect = Rect(
            self.rect.x + _H_PADDING,
            self.rect.y,
            max(1, self.rect.width - 2 * _H_PADDING),
            self.rect.height,
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect.clip(old_clip) if old_clip else clip_rect)

        font = self._get_font(theme)
        display = self._get_display_value()

        if font is not None:
            font_h = font.line_height if hasattr(font, "line_height") else font.get_height()
            text_y = self.rect.y + (self.rect.height - font_h) // 2

            # Selection highlight
            sel = self.selection_range
            if sel[0] != sel[1] and font is not None:
                sel_x_start, _ = font.text_size(display[:sel[0]]) if hasattr(font, "text_size") else font.size(display[:sel[0]])
                sel_x_end, _ = font.text_size(display[:sel[1]]) if hasattr(font, "text_size") else font.size(display[:sel[1]])
                sel_rect = Rect(
                    self.rect.x + _H_PADDING + sel_x_start - self._scroll_offset_px,
                    text_y,
                    sel_x_end - sel_x_start,
                    font_h,
                )
                sel_color = getattr(theme, "highlight", (100, 150, 240))
                pygame.draw.rect(surface, sel_color, sel_rect)

            # Text or placeholder
            if display:
                text_surf = font._font.render(display, True, theme.text) if hasattr(font, "_font") else font.render(display, True, theme.text)
                surface.blit(text_surf, (self.rect.x + _H_PADDING - self._scroll_offset_px, text_y))
            elif self._placeholder and not self._focused:
                ph_color = getattr(theme, "medium", (150, 150, 150))
                ph_surf = font._font.render(self._placeholder, True, ph_color) if hasattr(font, "_font") else font.render(self._placeholder, True, ph_color)
                surface.blit(ph_surf, (self.rect.x + _H_PADDING, text_y))

            # Cursor
            if self._focused and self._cursor_visible:
                cursor_x_px, _ = font.text_size(display[:self._cursor_pos]) if hasattr(font, "text_size") else font.size(display[:self._cursor_pos])
                cx = self.rect.x + _H_PADDING + cursor_x_px - self._scroll_offset_px
                pygame.draw.line(
                    surface,
                    theme.text,
                    (cx, text_y),
                    (cx, text_y + font_h - 1),
                    1,
                )

        surface.set_clip(old_clip)
