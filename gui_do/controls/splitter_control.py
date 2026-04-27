"""SplitterControl — resizable two-pane divider control."""
from __future__ import annotations

from typing import Callable, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_DIVIDER_THICKNESS = 6
_MIN_PANE_DEFAULT = 48
_CURSOR_HORIZONTAL = pygame.SYSTEM_CURSOR_SIZEWE
_CURSOR_VERTICAL = pygame.SYSTEM_CURSOR_SIZENS


RatioChangedCallback = Optional[Callable[[float], None]]


class SplitterControl(UiNode):
    """Two-pane layout with a draggable divider.

    Parameters
    ----------
    control_id:
        Unique node identifier.
    rect:
        Total bounding rectangle for both panes and the divider.
    axis:
        ``LayoutAxis.HORIZONTAL`` — left/right panes (divider is vertical).
        ``LayoutAxis.VERTICAL``   — top/bottom panes (divider is horizontal).
    ratio:
        Initial split position expressed as a fraction (0.0–1.0) of the
        primary dimension (width for horizontal, height for vertical).
    min_pane_size:
        Minimum pixel size of each pane along the primary axis.
    on_ratio_changed:
        Called with the new ratio whenever the user drags the divider.

    Properties
    ----------
    pane_a_rect : Rect
        Rectangle of the first pane (left/top).
    pane_b_rect : Rect
        Rectangle of the second pane (right/bottom).
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        axis: LayoutAxis = LayoutAxis.HORIZONTAL,
        ratio: float = 0.5,
        min_pane_size: int = _MIN_PANE_DEFAULT,
        on_ratio_changed: RatioChangedCallback = None,
        divider_thickness: int = _DIVIDER_THICKNESS,
    ) -> None:
        super().__init__(control_id, rect)
        self._axis = axis
        self._ratio: float = max(0.0, min(1.0, float(ratio)))
        self._min_pane_size: int = max(4, int(min_pane_size))
        self._on_ratio_changed: RatioChangedCallback = on_ratio_changed
        self._divider_thickness: int = max(2, int(divider_thickness))
        self._dragging: bool = False
        self._drag_start_pos: Tuple[int, int] = (0, 0)
        self._drag_start_ratio: float = self._ratio
        self._hovered: bool = False
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def ratio(self) -> float:
        return self._ratio

    @ratio.setter
    def ratio(self, value: float) -> None:
        self._ratio = self._clamp_ratio(float(value))
        self.invalidate()

    @property
    def axis(self) -> LayoutAxis:
        return self._axis

    @property
    def is_horizontal(self) -> bool:
        """True when panes are side-by-side (divider is a vertical bar)."""
        return self._axis == LayoutAxis.HORIZONTAL

    @property
    def pane_a_rect(self) -> Rect:
        """Rectangle of the first pane (left for horizontal, top for vertical)."""
        d = self._divider_offset()
        if self.is_horizontal:
            return Rect(self.rect.x, self.rect.y, d, self.rect.height)
        return Rect(self.rect.x, self.rect.y, self.rect.width, d)

    @property
    def pane_b_rect(self) -> Rect:
        """Rectangle of the second pane (right for horizontal, bottom for vertical)."""
        d = self._divider_offset()
        t = self._divider_thickness
        if self.is_horizontal:
            x = self.rect.x + d + t
            return Rect(x, self.rect.y, max(0, self.rect.width - d - t), self.rect.height)
        y = self.rect.y + d + t
        return Rect(self.rect.x, y, self.rect.width, max(0, self.rect.height - d - t))

    @property
    def divider_rect(self) -> Rect:
        """Rectangle of the draggable divider bar."""
        d = self._divider_offset()
        t = self._divider_thickness
        if self.is_horizontal:
            return Rect(self.rect.x + d, self.rect.y, t, self.rect.height)
        return Rect(self.rect.x, self.rect.y + d, self.rect.width, t)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _primary_size(self) -> int:
        return self.rect.width if self.is_horizontal else self.rect.height

    def _available_size(self) -> int:
        return max(0, self._primary_size() - self._divider_thickness)

    def _divider_offset(self) -> int:
        """Pixel offset of the divider's leading edge from the control's origin."""
        avail = self._available_size()
        raw = int(self._ratio * avail)
        return max(self._min_pane_size, min(raw, avail - self._min_pane_size))

    def _clamp_ratio(self, ratio: float) -> float:
        avail = max(1, self._available_size())
        lo = self._min_pane_size / avail
        hi = (avail - self._min_pane_size) / avail
        return max(lo, min(ratio, hi))

    def _ratio_from_pos(self, pos: Tuple[int, int]) -> float:
        avail = max(1, self._available_size())
        if self.is_horizontal:
            pixel = pos[0] - self.rect.x
        else:
            pixel = pos[1] - self.rect.y
        return max(0.0, min(1.0, pixel / avail))

    def _in_divider(self, pos: Tuple[int, int]) -> bool:
        hit = Rect(self.divider_rect)
        # Expand hit zone by 2px on each side for easier grab
        if self.is_horizontal:
            hit.x -= 2
            hit.width += 4
        else:
            hit.y -= 2
            hit.height += 4
        return hit.collidepoint(pos)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled and self.tab_index >= 0

    def update(self, dt_seconds: float) -> None:
        pass

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if self._in_divider(event.pos):
                self._dragging = True
                self._drag_start_pos = event.pos
                self._drag_start_ratio = self._ratio
                # Request pointer capture so we get motion events outside the rect
                try:
                    app.capture_pointer(self.control_id)
                except Exception:
                    pass
                return True

        if event.kind == EventType.MOUSE_MOTION:
            if self._dragging:
                new_ratio = self._clamp_ratio(self._ratio_from_pos(event.pos))
                if new_ratio != self._ratio:
                    self._ratio = new_ratio
                    if self._on_ratio_changed is not None:
                        try:
                            self._on_ratio_changed(self._ratio)
                        except Exception:
                            pass
                    self.invalidate()
                return True
            hovered = self._in_divider(event.pos)
            if hovered != self._hovered:
                self._hovered = hovered
                self.invalidate()
            return False

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            if self._dragging:
                self._dragging = False
                try:
                    app.release_pointer(self.control_id)
                except Exception:
                    pass
                return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key, event.mod)

        return False

    def _handle_key(self, key: int, mod: int) -> bool:
        step = 0.01
        if mod & pygame.KMOD_SHIFT:
            step = 0.05
        if self.is_horizontal:
            if key == pygame.K_LEFT:
                self._apply_ratio_delta(-step)
                return True
            if key == pygame.K_RIGHT:
                self._apply_ratio_delta(step)
                return True
        else:
            if key == pygame.K_UP:
                self._apply_ratio_delta(-step)
                return True
            if key == pygame.K_DOWN:
                self._apply_ratio_delta(step)
                return True
        return False

    def _apply_ratio_delta(self, delta: float) -> None:
        new_ratio = self._clamp_ratio(self._ratio + delta)
        if new_ratio != self._ratio:
            self._ratio = new_ratio
            if self._on_ratio_changed is not None:
                try:
                    self._on_ratio_changed(self._ratio)
                except Exception:
                    pass
            self.invalidate()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        def _color(name: str, fallback: tuple) -> tuple:
            val = getattr(theme, name, fallback)
            if hasattr(val, "value"):
                val = val.value
            return val

        divider_col = _color("border", (80, 80, 90))
        hover_col = _color("highlight", (0, 100, 200))
        focus_col = _color("focus", (100, 160, 255))

        dr = self.divider_rect

        # Divider bar
        color = hover_col if (self._hovered or self._dragging) else divider_col
        pygame.draw.rect(surface, color, dr)

        # Subtle center grip line
        if self.is_horizontal:
            cx = dr.centerx
            grip_y1 = dr.centery - 12
            grip_y2 = dr.centery + 12
            grip_col = tuple(min(255, c + 40) for c in divider_col)
            pygame.draw.line(surface, grip_col, (cx, grip_y1), (cx, grip_y2), 1)
        else:
            cy = dr.centery
            grip_x1 = dr.centerx - 12
            grip_x2 = dr.centerx + 12
            grip_col = tuple(min(255, c + 40) for c in divider_col)
            pygame.draw.line(surface, grip_col, (grip_x1, cy), (grip_x2, cy), 1)

        # Focus ring
        if self._focused:
            pygame.draw.rect(surface, focus_col, dr, 2)
