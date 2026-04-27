"""SpinnerControl — numeric input with increment/decrement buttons."""
from __future__ import annotations

from typing import Callable, Optional, Union, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.value_change_reason import ValueChangeReason

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_BTN_W = 20
_H_PAD = 4


class SpinnerControl(UiNode):
    """Numeric spinner with up/down buttons, keyboard, and scroll-wheel input.

    Supports both integer and float values.  Set ``decimals=0`` (the default)
    for integer-mode: the value and step are treated as integers.  Set
    ``decimals`` to a positive number to allow floating-point values displayed
    to that many decimal places.

    Usage::

        sp = SpinnerControl(
            "qty", Rect(10, 10, 120, 28),
            value=5, min_value=0, max_value=100, step=1,
        )
        sp.on_change = lambda v, reason: print("value:", v)
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        value: Union[int, float] = 0,
        *,
        min_value: Union[int, float, None] = None,
        max_value: Union[int, float, None] = None,
        step: Union[int, float] = 1,
        decimals: int = 0,
        on_change: Optional[Callable[[Union[int, float], ValueChangeReason], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._min = min_value
        self._max = max_value
        self._step = step
        self._decimals = max(0, int(decimals))
        self.on_change = on_change
        self.tab_index = 0
        self._value = self._clamp(value)
        # Text editing state
        self._editing: bool = False
        self._edit_text: str = ""
        self._cursor_blink: float = 0.0
        self._cursor_visible: bool = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def value(self) -> Union[int, float]:
        return self._value

    @value.setter
    def value(self, v: Union[int, float]) -> None:
        self._set_value(v, ValueChangeReason.PROGRAMMATIC)

    def set_value(self, v: Union[int, float]) -> None:
        """Set value programmatically without firing on_change."""
        self._value = self._clamp(v)
        self._editing = False
        self.invalidate()

    def increment(self) -> None:
        self._set_value(self._value + self._step, ValueChangeReason.KEYBOARD)

    def decrement(self) -> None:
        self._set_value(self._value - self._step, ValueChangeReason.KEYBOARD)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def update(self, dt_seconds: float) -> None:
        if self._focused:
            self._cursor_blink += dt_seconds
            if self._cursor_blink >= 0.5:
                self._cursor_blink = 0.0
                self._cursor_visible = not self._cursor_visible
                self.invalidate()

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            if pos is None or not self.rect.collidepoint(pos):
                if self._editing:
                    self._commit_edit()
                return False
            up_rect, down_rect = self._button_rects()
            if up_rect.collidepoint(pos):
                self.increment()
                return True
            if down_rect.collidepoint(pos):
                self.decrement()
                return True
            # Click on text area — enter edit mode
            if not self._editing:
                self._editing = True
                self._edit_text = self._format_value(self._value)
                self.invalidate()
            return True

        if event.kind == EventType.MOUSE_WHEEL:
            pos = event.pos
            if pos is not None and self.rect.collidepoint(pos):
                wheel_y = getattr(event, "wheel_y", 0) or getattr(event, "y", 0)
                if wheel_y > 0:
                    self.increment()
                else:
                    self.decrement()
                return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key, event.mod)

        if event.kind == EventType.TEXT_INPUT and self._focused and self._editing:
            char = event.text or ""
            allowed = set("0123456789.-+")
            for ch in char:
                if ch in allowed:
                    self._edit_text += ch
            self.invalidate()
            return True

        return False

    def _handle_key(self, key: int, mod: int) -> bool:
        if key == pygame.K_UP:
            self._commit_edit()
            self.increment()
            return True
        if key == pygame.K_DOWN:
            self._commit_edit()
            self.decrement()
            return True
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self._editing:
                self._commit_edit()
            return True
        if key == pygame.K_ESCAPE:
            self._editing = False
            self.invalidate()
            return True
        if self._editing:
            if key == pygame.K_BACKSPACE:
                self._edit_text = self._edit_text[:-1]
                self.invalidate()
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return
        r = self.rect

        # Background
        if self._focused:
            bg = getattr(theme, "input_focused", getattr(theme, "input_bg", (45, 45, 60)))
        else:
            bg = getattr(theme, "input_bg", (40, 40, 40))
        if hasattr(bg, "value"):
            bg = bg.value
        pygame.draw.rect(surface, bg, r, border_radius=3)

        border_color = getattr(theme, "border", (80, 80, 80))
        if hasattr(border_color, "value"):
            border_color = border_color.value
        pygame.draw.rect(surface, border_color, r, width=1, border_radius=3)

        up_rect, down_rect = self._button_rects()

        # Button backgrounds
        btn_bg = getattr(theme, "button_bg", (60, 60, 70))
        if hasattr(btn_bg, "value"):
            btn_bg = btn_bg.value
        pygame.draw.rect(surface, btn_bg, up_rect, border_radius=2)
        pygame.draw.rect(surface, btn_bg, down_rect, border_radius=2)

        # Arrow symbols
        text_color = getattr(theme, "text", (220, 220, 220))
        if hasattr(text_color, "value"):
            text_color = text_color.value
        font = pygame.font.SysFont(None, 14)
        up_surf = font.render("▲", True, text_color)
        dn_surf = font.render("▼", True, text_color)
        surface.blit(
            up_surf,
            (
                up_rect.centerx - up_surf.get_width() // 2,
                up_rect.centery - up_surf.get_height() // 2,
            ),
        )
        surface.blit(
            dn_surf,
            (
                down_rect.centerx - dn_surf.get_width() // 2,
                down_rect.centery - dn_surf.get_height() // 2,
            ),
        )

        # Value text
        display = self._edit_text if self._editing else self._format_value(self._value)
        if self._editing and self._cursor_visible:
            display = display + "|"
        val_font = pygame.font.SysFont(None, 18)
        val_surf = val_font.render(display, True, text_color)
        text_x = r.x + _H_PAD
        text_y = r.centery - val_surf.get_height() // 2
        # Clip text area
        clip = surface.get_clip()
        text_rect = Rect(r.x, r.y, r.width - _BTN_W * 2 - 2, r.height)
        surface.set_clip(text_rect.clip(clip) if clip else text_rect)
        surface.blit(val_surf, (text_x, text_y))
        surface.set_clip(clip)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _button_rects(self) -> tuple[Rect, Rect]:
        r = self.rect
        up = Rect(r.right - _BTN_W * 2, r.y + 1, _BTN_W - 1, r.height // 2 - 1)
        dn = Rect(r.right - _BTN_W * 2, r.y + r.height // 2, _BTN_W - 1, r.height - r.height // 2 - 1)
        return up, dn

    def _clamp(self, v: Union[int, float]) -> Union[int, float]:
        result = float(v)
        if self._min is not None:
            result = max(float(self._min), result)
        if self._max is not None:
            result = min(float(self._max), result)
        if self._decimals == 0:
            return int(round(result))
        return round(result, self._decimals)

    def _format_value(self, v: Union[int, float]) -> str:
        if self._decimals == 0:
            return str(int(v))
        return f"{v:.{self._decimals}f}"

    def _set_value(self, v: Union[int, float], reason: ValueChangeReason) -> None:
        new_val = self._clamp(v)
        if new_val == self._value:
            return
        self._value = new_val
        self._editing = False
        self.invalidate()
        if self.on_change is not None:
            try:
                self.on_change(self._value, reason)
            except Exception:
                pass

    def _commit_edit(self) -> None:
        if not self._editing:
            return
        self._editing = False
        try:
            parsed: Union[int, float] = (
                int(self._edit_text) if self._decimals == 0 else float(self._edit_text)
            )
            self._set_value(parsed, ValueChangeReason.USER_INTERACTION)
        except (ValueError, OverflowError):
            pass
        self.invalidate()
