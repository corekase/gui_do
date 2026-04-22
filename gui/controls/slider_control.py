import pygame
from typing import Optional, TYPE_CHECKING

from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.value_change_callback import ValueChangeCallback
from ..core.value_change_callback import ValueChangeCallbackMode
from ..core.value_change_callback import dispatch_value_change
from ..core.value_change_callback import normalize_value_change_callback_mode
from ..core.value_change_callback import validate_value_change_callback
from ..core.value_change_reason import ValueChangeReason
from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class SliderControl(UiNode):
    """Single-value slider with capture-locked drag behavior."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        axis: LayoutAxis,
        minimum: float,
        maximum: float,
        value: float,
        on_change: Optional[ValueChangeCallback[float]] = None,
        on_change_mode: ValueChangeCallbackMode = "compat",
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.value = float(value)
        self.on_change = on_change
        self.on_change_mode = normalize_value_change_callback_mode(on_change_mode)
        validate_value_change_callback(self.on_change, self.on_change_mode)
        self.dragging = False
        self.handle_size = 16
        self._drag_anchor_offset = 0
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_value()

    def set_on_change_mode(self, mode: str) -> ValueChangeCallbackMode:
        """Update callback dispatch mode at runtime with validation."""
        normalized = normalize_value_change_callback_mode(mode)
        validate_value_change_callback(self.on_change, normalized)
        self.on_change_mode = normalized
        return self.on_change_mode

    def set_on_change_callback(self, callback: Optional[ValueChangeCallback[float]]) -> Optional[ValueChangeCallback[float]]:
        """Update callback at runtime and validate compatibility with current mode."""
        validate_value_change_callback(callback, self.on_change_mode)
        self.on_change = callback
        return self.on_change

    def _normalize_range(self) -> None:
        if self.maximum < self.minimum:
            self.minimum, self.maximum = self.maximum, self.minimum

    def _clamp_value(self) -> None:
        self._normalize_range()
        self.value = min(max(self.value, self.minimum), self.maximum)

    def _travel_rect(self) -> Rect:
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(self.rect.x + 8, self.rect.centery - 4, max(1, self.rect.width - 16), 8)
        return Rect(self.rect.centerx - 4, self.rect.y + 8, 8, max(1, self.rect.height - 16))

    def _to_pixel(self, value: float) -> int:
        self._normalize_range()
        travel = self._travel_rect()
        span = self.maximum - self.minimum
        ratio = 0.0 if span <= 0 else (value - self.minimum) / span
        if self.axis == LayoutAxis.HORIZONTAL:
            return int(round(travel.left + (ratio * travel.width)))
        return int(round(travel.top + (ratio * travel.height)))

    def _to_value(self, pixel: int) -> float:
        self._normalize_range()
        travel = self._travel_rect()
        if self.axis == LayoutAxis.HORIZONTAL:
            ratio = 0.0 if travel.width <= 0 else (pixel - travel.left) / float(travel.width)
        else:
            ratio = 0.0 if travel.height <= 0 else (pixel - travel.top) / float(travel.height)
        ratio = min(max(ratio, 0.0), 1.0)
        return self.minimum + ((self.maximum - self.minimum) * ratio)

    def _keyboard_step(self) -> float:
        span = self.maximum - self.minimum
        return max(1.0, abs(span) * 0.05)

    def _nudge(self, delta: float) -> None:
        self._set_value(self.value + float(delta))

    def set_value(self, value: float) -> bool:
        """Set value programmatically with clamp and on_change callback semantics."""
        return self._set_value(value, reason=ValueChangeReason.PROGRAMMATIC)

    def adjust_value(self, delta: float) -> bool:
        """Adjust value programmatically by a delta with clamp and callbacks."""
        return self._set_value(self.value + float(delta), reason=ValueChangeReason.PROGRAMMATIC)

    def _set_value(self, new_value: float, reason: ValueChangeReason = ValueChangeReason.PROGRAMMATIC) -> bool:
        old_value = self.value
        self.value = float(new_value)
        self._clamp_value()
        changed = self.value != old_value
        if changed:
            dispatch_value_change(self.on_change, self.value, reason, mode=self.on_change_mode)
        return changed

    def handle_rect(self) -> Rect:
        self._normalize_range()
        pixel = self._to_pixel(self.value)
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(pixel - (self.handle_size // 2), self.rect.centery - (self.handle_size // 2), self.handle_size, self.handle_size)
        return Rect(self.rect.centerx - (self.handle_size // 2), pixel - (self.handle_size // 2), self.handle_size, self.handle_size)

    def _build_lock_rect(self, pointer_pos) -> Rect:
        travel = self._travel_rect()
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(travel.left, pointer_pos[1], travel.width + 1, 1)
        return Rect(pointer_pos[0], travel.top, 1, travel.height + 1)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            if self.dragging and app.pointer_capture.is_owned_by(self.control_id):
                app.pointer_capture.end(self.control_id)
            self.dragging = False
            return False

        step = self._keyboard_step()
        if event.is_key_down(pygame.K_HOME):
            return self._set_value(self.minimum, reason=ValueChangeReason.KEYBOARD)
        if event.is_key_down(pygame.K_END):
            return self._set_value(self.maximum, reason=ValueChangeReason.KEYBOARD)
        if self.axis == LayoutAxis.HORIZONTAL:
            if event.is_key_down(pygame.K_LEFT):
                return self._set_value(self.value - step, reason=ValueChangeReason.KEYBOARD)
            if event.is_key_down(pygame.K_RIGHT):
                return self._set_value(self.value + step, reason=ValueChangeReason.KEYBOARD)
        else:
            if event.is_key_down(pygame.K_DOWN):
                return self._set_value(self.value - step, reason=ValueChangeReason.KEYBOARD)
            if event.is_key_down(pygame.K_UP):
                return self._set_value(self.value + step, reason=ValueChangeReason.KEYBOARD)

        raw = event.pos
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.handle_rect().collidepoint(raw):
                handle = self.handle_rect()
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = raw[0] - handle.x
                else:
                    self._drag_anchor_offset = raw[1] - handle.y
                app.pointer_capture.begin(self.control_id, self._build_lock_rect(raw))
                self.dragging = True
                return True

        if event.is_mouse_motion() and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pos = app.pointer_capture.clamp(app.input_state.pointer_pos)
            if self.axis == LayoutAxis.HORIZONTAL:
                axis_pixel = pos[0] - self._drag_anchor_offset + (self.handle_size // 2)
            else:
                axis_pixel = pos[1] - self._drag_anchor_offset + (self.handle_size // 2)
            return self._set_value(self._to_value(axis_pixel), reason=ValueChangeReason.MOUSE_DRAG)

        if event.is_mouse_up(1) and self.dragging:
            self.dragging = False
            app.pointer_capture.end(self.control_id)
            return True

        if event.is_mouse_wheel() and self.rect.collidepoint(app.input_state.pointer_pos):
            return self._set_value(
                self.value + (float(event.wheel_delta) * ((self.maximum - self.minimum) * 0.05)),
                reason=ValueChangeReason.WHEEL,
            )
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        travel = self._travel_rect()
        handle = self.handle_rect()
        factory = theme.graphics_factory
        travel_size = (travel.width, travel.height)
        handle_size = (handle.width, handle.height)
        if self._track_visuals is None or self._track_visuals_size != travel_size:
            self._track_visuals = factory.build_frame_visuals(travel)
            self._track_visuals_size = travel_size
        if self._handle_visuals is None or self._handle_visuals_size != handle_size:
            self._handle_visuals = factory.build_frame_visuals(handle)
            self._handle_visuals_size = handle_size
        track_selected = factory.resolve_visual_state(
            self._track_visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=False,
            hovered=False,
        )
        handle_selected = factory.resolve_visual_state(
            self._handle_visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.dragging,
            hovered=not self.dragging,
        )
        surface.blit(track_selected, travel)
        surface.blit(handle_selected, handle)
