"""RangeSliderControl — two-handle slider for selecting a min/max range."""
from __future__ import annotations

from typing import Callable, Optional, Tuple, Union, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.value_change_reason import ValueChangeReason

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_HANDLE_R = 8   # handle radius in pixels
_TRACK_H = 4    # track bar height in pixels


class RangeSliderControl(UiNode):
    """Horizontal two-handle range slider.

    Provides a ``low_value`` and a ``high_value`` handle that can be dragged
    independently.  The invariant ``low_value <= high_value`` is always
    maintained; dragging one handle past the other snaps both together.

    Usage::

        rs = RangeSliderControl(
            "price_range",
            Rect(20, 20, 300, 28),
            min_value=0,
            max_value=1000,
            low_value=100,
            high_value=800,
            step=10,
            on_change=lambda lo, hi, reason: print(lo, hi),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        min_value: Union[int, float] = 0,
        max_value: Union[int, float] = 100,
        low_value: Optional[Union[int, float]] = None,
        high_value: Optional[Union[int, float]] = None,
        step: Union[int, float] = 1,
        on_change: Optional[
            Callable[
                [Union[int, float], Union[int, float], ValueChangeReason], None
            ]
        ] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._min = float(min_value)
        self._max = float(max_value)
        if self._max <= self._min:
            self._max = self._min + 1.0
        self._step = float(step) if step else 1.0
        self._low = float(low_value if low_value is not None else self._min)
        self._high = float(high_value if high_value is not None else self._max)
        self.on_change = on_change
        self.tab_index = 0
        self._clamp_values()
        # Drag state: 0=none, 1=low handle, 2=high handle
        self._dragging: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def low_value(self) -> Union[int, float]:
        return self._low

    @property
    def high_value(self) -> Union[int, float]:
        return self._high

    def set_values(self, low: Union[int, float], high: Union[int, float]) -> None:
        """Set both handles programmatically."""
        self._low = float(low)
        self._high = float(high)
        self._clamp_values()
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def update(self, dt_seconds: float) -> None:
        pass

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            if pos is None or not self.rect.collidepoint(pos):
                return False
            lx = self._value_to_x(self._low)
            hx = self._value_to_x(self._high)
            px = pos[0]
            dist_low = abs(px - lx)
            dist_high = abs(px - hx)
            if dist_low <= dist_high:
                self._dragging = 1
            else:
                self._dragging = 2
            self._drag_to(px)
            app.pointer_capture.begin(self.control_id, owner=self)
            return True

        if event.kind == EventType.MOUSE_MOTION and self._dragging:
            pos = event.pos
            if pos is not None:
                self._drag_to(pos[0])
            return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1 and self._dragging:
            pos = event.pos
            if pos is not None:
                self._drag_to(pos[0])
            self._dragging = 0
            if app.pointer_capture.is_owned_by(self.control_id):
                app.pointer_capture.end(self.control_id)
            return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key)

        return False

    def _handle_key(self, key: int) -> bool:
        if key == pygame.K_LEFT:
            new_low = self._snap(self._low - self._step)
            self._set_low(new_low, ValueChangeReason.USER_INTERACTION)
            return True
        if key == pygame.K_RIGHT:
            new_low = self._snap(self._low + self._step)
            self._set_low(new_low, ValueChangeReason.USER_INTERACTION)
            return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        # Track
        track_color = getattr(theme, "scrollbar_track", getattr(theme, "panel", (60, 60, 60)))
        if hasattr(track_color, "value"):
            track_color = track_color.value
        fill_color = getattr(theme, "highlight", (0, 120, 215))
        if hasattr(fill_color, "value"):
            fill_color = fill_color.value
        handle_color = getattr(theme, "button_bg", (200, 200, 200))
        if hasattr(handle_color, "value"):
            handle_color = handle_color.value

        cy = self.rect.centery
        track_rect = Rect(
            self.rect.x + _HANDLE_R,
            cy - _TRACK_H // 2,
            self.rect.width - _HANDLE_R * 2,
            _TRACK_H,
        )
        pygame.draw.rect(surface, track_color, track_rect, border_radius=2)

        # Filled range between handles
        lx = self._value_to_x(self._low)
        hx = self._value_to_x(self._high)
        if hx > lx:
            fill_rect = Rect(lx, cy - _TRACK_H // 2, hx - lx, _TRACK_H)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=2)

        # Handles
        pygame.draw.circle(surface, handle_color, (lx, cy), _HANDLE_R)
        pygame.draw.circle(surface, handle_color, (hx, cy), _HANDLE_R)
        border = getattr(theme, "border", (120, 120, 120))
        if hasattr(border, "value"):
            border = border.value
        pygame.draw.circle(surface, border, (lx, cy), _HANDLE_R, width=1)
        pygame.draw.circle(surface, border, (hx, cy), _HANDLE_R, width=1)

        # Focus ring
        if self._focused:
            focus_color = getattr(theme, "focus_ring", (0, 150, 255))
            if hasattr(focus_color, "value"):
                focus_color = focus_color.value
            pygame.draw.rect(surface, focus_color, self.rect, width=1, border_radius=3)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clamp_values(self) -> None:
        self._low = max(self._min, min(self._low, self._max))
        self._high = max(self._min, min(self._high, self._max))
        if self._low > self._high:
            self._low, self._high = self._high, self._low

    def _snap(self, v: float) -> float:
        if self._step > 0:
            snapped = round(v / self._step) * self._step
        else:
            snapped = v
        return max(self._min, min(snapped, self._max))

    def _value_to_x(self, v: float) -> int:
        track_w = max(1, self.rect.width - _HANDLE_R * 2)
        frac = (v - self._min) / max(1e-9, self._max - self._min)
        return self.rect.x + _HANDLE_R + int(frac * track_w)

    def _x_to_value(self, x: int) -> float:
        track_w = max(1, self.rect.width - _HANDLE_R * 2)
        frac = (x - self.rect.x - _HANDLE_R) / track_w
        return self._snap(self._min + frac * (self._max - self._min))

    def _drag_to(self, px: int) -> None:
        v = self._x_to_value(px)
        if self._dragging == 1:
            self._set_low(min(v, self._high), ValueChangeReason.USER_INTERACTION)
        elif self._dragging == 2:
            self._set_high(max(v, self._low), ValueChangeReason.USER_INTERACTION)

    def _set_low(self, v: float, reason: ValueChangeReason) -> None:
        new_low = max(self._min, min(float(v), self._high))
        if new_low == self._low:
            return
        self._low = new_low
        self.invalidate()
        self._fire_change(reason)

    def _set_high(self, v: float, reason: ValueChangeReason) -> None:
        new_high = min(self._max, max(float(v), self._low))
        if new_high == self._high:
            return
        self._high = new_high
        self.invalidate()
        self._fire_change(reason)

    def _fire_change(self, reason: ValueChangeReason) -> None:
        if self.on_change is not None:
            try:
                self.on_change(self._low, self._high, reason)
            except Exception:
                pass
