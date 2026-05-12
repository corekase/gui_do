"""ChipInputControl — multi-value tag input with add/remove chip affordances."""
from __future__ import annotations

from typing import Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size.
_FONT_SCALE: float = 1.0            # chip label size ratio
_CHIP_PAD_X_RATIO: float = 0.375   # horizontal padding inside each chip
_CHIP_PAD_Y_RATIO: float = 0.1875  # vertical padding inside each chip (tight)
_CHIP_GAP: int = 4                   # gap between chips (px, not scaled)
_CHIP_CLOSE_RATIO: float = 0.875    # close-button width ratio (relative to font size)
_CHIP_CORNER: int = 4               # border-radius for chip rect (px, not scaled)
_INPUT_MIN_W_RATIO: float = 3.75   # minimum input field width ratio
_INPUT_FONT_SCALE: float = _FONT_SCALE  # keep typed text size aligned with chip labels


class ChipInputControl(UiNode):
    """Multi-value tag/chip input control.

    Each entered value is rendered as a removable "chip".  Typing in the
    embedded text field and pressing Enter (or a configurable separator key)
    adds a new chip.  Clicking the × on a chip removes it.

    Usage::

        chips = ChipInputControl(
            "tags", Rect(0, 0, 300, 36),
            values=["python", "pygame"],
            placeholder="Add tag…",
            on_change=lambda vals: print(vals),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        values: Optional[List[str]] = None,
        placeholder: str = "Add…",
        max_values: int = 20,
        separator_keys: Optional[List[int]] = None,
        on_change: Optional[Callable[[List[str]], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._values: List[str] = list(values or [])
        self._placeholder = placeholder
        self._max_values = max(1, int(max_values))
        self._separator_keys = separator_keys or [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_COMMA]
        self._on_change = on_change
        self._font_role = font_role
        self._edit_text: str = ""
        # Route Enter keys through handle_event instead of generic focus
        # activation so both main Enter and keypad Enter commit chips.
        self.key_activatable = False
        self._cursor_visible = True
        self._cursor_timer = 0.0
        # Track per-chip close-button rects (rebuilt on draw)
        self._chip_close_rects: List[Optional[Rect]] = []
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def values(self) -> List[str]:
        return list(self._values)

    def set_values(self, values: List[str]) -> None:
        self._values = list(values)
        self._chip_close_rects = []
        self.invalidate()

    def add_value(self, value: str) -> bool:
        """Add a value if not a duplicate and within max_values.  Returns True if added."""
        stripped = value.strip()
        if not stripped or stripped in self._values or len(self._values) >= self._max_values:
            return False
        self._values.append(stripped)
        self._chip_close_rects = []
        if self._on_change:
            self._on_change(list(self._values))
        self.invalidate()
        return True

    def remove_value(self, value: str) -> bool:
        if value in self._values:
            self._values.remove(value)
            self._chip_close_rects = []
            if self._on_change:
                self._on_change(list(self._values))
            self.invalidate()
            return True
        return False

    def clear(self) -> None:
        self._values.clear()
        self._edit_text = ""
        self._chip_close_rects = []
        if self._on_change:
            self._on_change([])
        self.invalidate()

    @property
    def edit_text(self) -> str:
        return self._edit_text

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def on_focus_changed(self, is_focused: bool) -> None:
        """Enable text input when focused, disable when unfocused."""
        if is_focused:
            try:
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(self.rect)
            except Exception:
                pass
        else:
            try:
                pygame.key.stop_text_input()
            except Exception:
                pass

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        super()._on_visibility_changed(old_visible, new_visible)

    def update(self, dt_seconds: float) -> None:
        if not self._focused:
            return
        self._cursor_timer += dt_seconds
        if self._cursor_timer >= 0.5:
            self._cursor_timer -= 0.5
            self._cursor_visible = not self._cursor_visible
            self.invalidate()

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            return False

        pos = event.pos

        # Click on chip close button
        if event.is_mouse_down(1) and pos is not None:
            for idx, close_rect in enumerate(self._chip_close_rects):
                if close_rect and close_rect.collidepoint(pos):
                    self._values.pop(idx)
                    self._chip_close_rects = []
                    if self._on_change:
                        self._on_change(list(self._values))
                    self.invalidate()
                    return True
            if self.rect.collidepoint(pos):
                return True  # claim focus

        # Keyboard input
        if event.kind == EventType.KEY_DOWN and self._focused:
            key = event.key
            if key in self._separator_keys:
                if self._edit_text.strip():
                    self.add_value(self._edit_text)
                    self._edit_text = ""
                    self.invalidate()
                return True
            # Consume space on key-down so it does not propagate to global or
            # scene-level key handlers; actual character insertion occurs via
            # the corresponding TEXT_INPUT event.
            if key == pygame.K_SPACE:
                return True
            if key == pygame.K_BACKSPACE:
                if self._edit_text:
                    self._edit_text = self._edit_text[:-1]
                elif self._values:
                    self._values.pop()
                    self._chip_close_rects = []
                    if self._on_change:
                        self._on_change(list(self._values))
                self.invalidate()
                return True

        if event.kind == EventType.TEXT_INPUT and self._focused:
            char = event.text or ""
            if not char:
                return False
            is_comma_separator = (char == "," and pygame.K_COMMA in self._separator_keys)
            is_enter_separator = (
                char in ("\r", "\n")
                and (
                    pygame.K_RETURN in self._separator_keys
                    or pygame.K_KP_ENTER in self._separator_keys
                )
            )
            if is_comma_separator or is_enter_separator:
                if self._edit_text.strip():
                    self.add_value(self._edit_text)
                    self._edit_text = ""
                    self.invalidate()
                return True
            self._edit_text += char
            self.invalidate()
            return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        chip_font_size = fonts.scaled_size(_FONT_SCALE)
        input_font_size = fonts.scaled_size(_INPUT_FONT_SCALE)
        pad_x = max(3, fonts.scaled_size(_CHIP_PAD_X_RATIO))
        pad_y = max(2, fonts.scaled_size(_CHIP_PAD_Y_RATIO))
        close_w = max(10, fonts.scaled_size(_CHIP_CLOSE_RATIO))
        min_input_w = max(40, fonts.scaled_size(_INPUT_MIN_W_RATIO))

        # Background
        if not self.enabled:
            bg = theme.dark
        elif self._focused:
            bg = theme.light
        else:
            bg = theme.medium
        pygame.draw.rect(surface, bg, r)
        border_color = theme.highlight if self._focused else theme.dark
        pygame.draw.rect(surface, border_color, r, 1)

        self._chip_close_rects = []
        x = r.left + 4
        chip_h = self._chip_h(fonts)
        y = r.top + (r.height - chip_h) // 2

        text_color = theme.dark if not self.enabled else theme.text

        for val in self._values:
            chip_surf = theme.render_text(val, role=self._font_role, shadow=False, size=chip_font_size, color=theme.background)
            cw = chip_surf.get_width() + pad_x * 2 + close_w
            ch = chip_h
            chip_rect = Rect(x, y, cw, ch)

            chip_bg = theme.dark if not self.enabled else theme.highlight
            pygame.draw.rect(surface, chip_bg, chip_rect, border_radius=_CHIP_CORNER)
            pygame.draw.rect(surface, theme.dark, chip_rect, 1, border_radius=_CHIP_CORNER)
            text_cy = chip_rect.top + (chip_rect.height - chip_surf.get_height()) // 2
            surface.blit(chip_surf, (chip_rect.left + pad_x, text_cy))

            # Close button (only when enabled)
            close_rect = Rect(chip_rect.right - close_w, chip_rect.top, close_w, chip_rect.height)
            self._chip_close_rects.append(Rect(close_rect) if self.enabled else None)
            if self.enabled:
                cx_mid = close_rect.left + close_rect.width // 2
                cy_mid = close_rect.top + close_rect.height // 2
                d = max(3, close_w // 4)
                pygame.draw.line(surface, theme.background, (cx_mid - d, cy_mid - d), (cx_mid + d, cy_mid + d), 2)
                pygame.draw.line(surface, theme.background, (cx_mid + d, cy_mid - d), (cx_mid - d, cy_mid + d), 2)

            x += cw + _CHIP_GAP

        # Input field area
        if self._edit_text:
            input_surf = theme.render_text(self._edit_text, role=self._font_role, shadow=False, size=input_font_size, color=text_color)
            input_y = r.top + (r.height - input_surf.get_height()) // 2
            surface.blit(input_surf, (x, input_y))
            cursor_x = x + input_surf.get_width()
        else:
            if not self._focused:
                ph_color = theme.dark
                ph_surf = theme.render_text(self._placeholder, role=self._font_role, shadow=False, size=input_font_size, color=ph_color)
                ph_y = r.top + (r.height - ph_surf.get_height()) // 2
                surface.blit(ph_surf, (x, ph_y))
            cursor_x = x

        if self._focused and self._cursor_visible and self.enabled:
            cursor_top = max(r.top + 2, r.top + (r.height - input_font_size) // 2)
            cursor_bottom = min(r.bottom - 3, cursor_top + input_font_size)
            pygame.draw.line(surface, text_color, (cursor_x, cursor_top), (cursor_x, cursor_bottom), 1)

    def _chip_h(self, fonts) -> int:
        """Compute chip height from font metrics."""
        font_size = fonts.scaled_size(_FONT_SCALE)
        pad_y = max(2, fonts.scaled_size(_CHIP_PAD_Y_RATIO))
        return font_size + pad_y * 2
