"""Single-line text input control with cursor, selection, masking, and IME support."""
from __future__ import annotations

from typing import Callable, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.clipboard import ClipboardManager

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_BLINK_INTERVAL = 0.5
_H_PADDING = 4


class TextInputControl(UiNode):
    """Single-line editable text field with cursor, selection, masking, and clipboard."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        value: str = "",
        placeholder: str = "",
        max_length: Optional[int] = None,
        masked: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._value = str(value)
        self._placeholder = str(placeholder)
        self._max_length = max_length
        self._masked = bool(masked)
        self._on_change = on_change
        self._on_submit = on_submit
        self._font_role = str(font_role)
        self.tab_index = 0  # focusable by default
        # Cursor / selection
        self._cursor_pos: int = len(self._value)
        self._sel_anchor: Optional[int] = None
        self._sel_active: Optional[int] = None
        self._scroll_offset_px: int = 0
        # Blink timer
        self._cursor_blink_elapsed: float = 0.0
        self._cursor_visible: bool = True
        # Mouse drag selection
        self._drag_selecting: bool = False
        # Visual cache
        self._bg_idle: Optional["pygame.Surface"] = None
        self._bg_focused: Optional["pygame.Surface"] = None
        self._bg_disabled: Optional["pygame.Surface"] = None
        self._visual_key: Optional[tuple] = None

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
        if is_focused:
            try:
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(self.rect)
            except Exception:
                pass
            self._cursor_visible = True
            self._cursor_blink_elapsed = 0.0
        else:
            try:
                pygame.key.stop_text_input()
            except Exception:
                pass
            self._drag_selecting = False

    # ------------------------------------------------------------------
    # Update (blink timer)
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        if not self._focused:
            return
        self._cursor_blink_elapsed += dt_seconds
        if self._cursor_blink_elapsed >= _BLINK_INTERVAL:
            self._cursor_blink_elapsed = 0.0
            self._cursor_visible = not self._cursor_visible
            self.invalidate()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        # TEXT_INPUT: IME-safe character insertion
        if event.kind == EventType.TEXT_INPUT:
            if not self._focused:
                return False
            text = event.text or ""
            if text:
                self._insert_text(text)
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
            return self._handle_key(key, ctrl, shift, app)

        # Mouse events
        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return False
            idx = self._pos_to_char_index(event.pos[0])
            self._cursor_pos = idx
            self._sel_anchor = idx
            self._sel_active = idx
            self._drag_selecting = True
            self._reset_blink()
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_MOTION and self._drag_selecting:
            idx = self._pos_to_char_index(event.pos[0])
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

    def _handle_key(self, key: int, ctrl: bool, shift: bool, app: "GuiApplication") -> bool:
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
                    self._delete_selection()
                    if self._on_change is not None:
                        self._on_change(self._value)
                return True
            if key == pygame.K_v:
                text = ClipboardManager.paste()
                if text:
                    self._insert_text(text)
                    if self._on_change is not None:
                        self._on_change(self._value)
                return True

        if key == pygame.K_BACKSPACE:
            sel = self.selection_range
            if sel[0] != sel[1]:
                self._delete_selection()
            elif self._cursor_pos > 0:
                self._value = self._value[:self._cursor_pos - 1] + self._value[self._cursor_pos:]
                self._cursor_pos -= 1
                self._sel_anchor = None
                self._sel_active = None
                self._scroll_to_cursor()
            if self._on_change is not None:
                self._on_change(self._value)
            self.invalidate()
            return True

        if key == pygame.K_DELETE:
            sel = self.selection_range
            if sel[0] != sel[1]:
                self._delete_selection()
            elif self._cursor_pos < len(self._value):
                self._value = self._value[:self._cursor_pos] + self._value[self._cursor_pos + 1:]
                self._scroll_to_cursor()
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
            self._scroll_to_cursor()
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
            self._scroll_to_cursor()
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
            self._scroll_to_cursor()
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
            self._scroll_to_cursor()
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
        if self._masked:
            return "*" * len(self._value)
        return self._value

    def _insert_text(self, text: str) -> None:
        sel = self.selection_range
        if sel[0] != sel[1]:
            self._delete_selection()
        available = len(text)
        if self._max_length is not None:
            available = max(0, self._max_length - len(self._value))
        text = text[:available]
        self._value = self._value[:self._cursor_pos] + text + self._value[self._cursor_pos:]
        self._cursor_pos += len(text)
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_to_cursor()
        self.invalidate()

    def _delete_selection(self) -> None:
        sel = self.selection_range
        if sel[0] == sel[1]:
            return
        self._value = self._value[:sel[0]] + self._value[sel[1]:]
        self._cursor_pos = sel[0]
        self._sel_anchor = None
        self._sel_active = None
        self._scroll_to_cursor()

    def _scroll_to_cursor(self) -> None:
        """Adjust scroll so cursor is visible."""
        font = self._get_font()
        if font is None:
            return
        display = self._get_display_value()
        cursor_px, _ = font.size(display[:self._cursor_pos])
        visible_width = self.rect.width - 2 * _H_PADDING
        if cursor_px < self._scroll_offset_px:
            self._scroll_offset_px = cursor_px
        elif cursor_px > self._scroll_offset_px + visible_width:
            self._scroll_offset_px = cursor_px - visible_width + 4
        self._scroll_offset_px = max(0, self._scroll_offset_px)

    def _pos_to_char_index(self, x_screen: int) -> int:
        """Convert screen x coordinate to character index."""
        font = self._get_font()
        if font is None:
            return 0
        display = self._get_display_value()
        x_local = x_screen - self.rect.left - _H_PADDING + self._scroll_offset_px
        best_idx = 0
        best_dist = abs(x_local)
        for i in range(1, len(display) + 1):
            px, _ = font.size(display[:i])
            dist = abs(x_local - px)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return max(0, min(best_idx, len(self._value)))

    def _get_font(self) -> Optional["pygame.font.Font"]:
        """Return pygame Font object or None if unavailable."""
        try:
            return pygame.font.SysFont(None, 20)
        except Exception:
            return None

    def _reset_blink(self) -> None:
        self._cursor_blink_elapsed = 0.0
        self._cursor_visible = True

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

        font = self._get_font()
        display = self._get_display_value()

        if font is not None:
            font_h = font.get_height()
            text_y = self.rect.y + (self.rect.height - font_h) // 2

            # Selection highlight
            sel = self.selection_range
            if sel[0] != sel[1] and font is not None:
                sel_x_start, _ = font.size(display[:sel[0]])
                sel_x_end, _ = font.size(display[:sel[1]])
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
                text_surf = font.render(display, True, theme.text)
                surface.blit(text_surf, (self.rect.x + _H_PADDING - self._scroll_offset_px, text_y))
            elif self._placeholder and not self._focused:
                ph_color = getattr(theme, "medium", (150, 150, 150))
                ph_surf = font.render(self._placeholder, True, ph_color)
                surface.blit(ph_surf, (self.rect.x + _H_PADDING, text_y))

            # Cursor
            if self._focused and self._cursor_visible:
                cursor_x_px, _ = font.size(display[:self._cursor_pos])
                cx = self.rect.x + _H_PADDING + cursor_x_px - self._scroll_offset_px
                pygame.draw.line(
                    surface,
                    theme.text,
                    (cx, text_y),
                    (cx, text_y + font_h - 1),
                    1,
                )

        surface.set_clip(old_clip)
