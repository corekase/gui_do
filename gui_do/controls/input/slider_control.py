import pygame
from typing import Optional, TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import GuiEvent
from ...events.value_change_callback import ValueChangeCallback
from ...events.value_change_callback import dispatch_value_change
from ...events.value_change_callback import validate_value_change_callback
from ...events.value_change_reason import ValueChangeReason
from ..base._axis_drag_control_base import _AxisDragControlBase
from ...layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


class SliderControl(_AxisDragControlBase):
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
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.value = float(value)
        self.on_change = on_change
        validate_value_change_callback(self.on_change)
        self._init_axis_drag_state()
        self.handle_size = 16
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_value()

    def set_on_change_callback(self, callback: Optional[ValueChangeCallback[float]]) -> Optional[ValueChangeCallback[float]]:
        """Update callback at runtime."""
        validate_value_change_callback(callback)
        self.on_change = callback
        return self.on_change

    def _normalize_range(self) -> None:
        if self.maximum < self.minimum:
            self.minimum, self.maximum = self.maximum, self.minimum

    def _clamp_value(self) -> None:
        self._normalize_range()
        self.value = min(max(self.value, self.minimum), self.maximum)

    def _travel_rect(self) -> Rect:
        return Rect(self.rect)

    def _handle_length(self) -> int:
        return max(1, int(self.handle_size))

    def _travel_span(self) -> int:
        handle_len = self._handle_length()
        if self.axis == LayoutAxis.HORIZONTAL:
            return max(0, self.rect.width - handle_len)
        return max(0, self.rect.height - handle_len)

    def _to_pixel(self, value: float) -> int:
        self._normalize_range()
        span = self.maximum - self.minimum
        ratio = 0.0 if span <= 0 else (value - self.minimum) / span
        travel = self._travel_rect()
        handle_len = self._handle_length()
        origin = travel.left if self.axis == LayoutAxis.HORIZONTAL else travel.top
        return int(round(origin + (handle_len / 2.0) + (ratio * self._travel_span())))

    def _to_value(self, pixel: int) -> float:
        self._normalize_range()
        travel = self._travel_rect()
        handle_len = self._handle_length()
        span_pixels = self._travel_span()
        origin = travel.left if self.axis == LayoutAxis.HORIZONTAL else travel.top
        ratio = 0.0 if span_pixels <= 0 else (pixel - (origin + (handle_len / 2.0))) / float(span_pixels)
        ratio = min(max(ratio, 0.0), 1.0)
        return self.minimum + ((self.maximum - self.minimum) * ratio)

    def _keyboard_step(self) -> float:
        span = self.maximum - self.minimum
        return max(1.0, abs(span) * 0.05)

    def should_arm_focus_activation_for_event(self, event: GuiEvent) -> bool:
        """Return True when this key event should arm the handle visual.

        Supports accessibility-style less/more and home/end keyboard adjustments.
        """
        if event.is_key_down(pygame.K_HOME) or event.is_key_down(pygame.K_END):
            return True
        if self.axis == LayoutAxis.HORIZONTAL:
            return bool(event.is_key_down(pygame.K_LEFT) or event.is_key_down(pygame.K_RIGHT))
        return bool(event.is_key_down(pygame.K_DOWN) or event.is_key_down(pygame.K_UP))

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point used by the focus manager's armed-visual path."""
        # Sliders activate visually on focus key activation; value changes remain
        # driven by directional/home/end keys and pointer interaction.
        return

    def set_value(self, value: float) -> bool:
        """Set value programmatically with clamp and on_change callback semantics."""
        return self._set_value(value, reason=ValueChangeReason.PROGRAMMATIC)

    def adjust_value(self, delta: float) -> bool:
        """Adjust value programmatically by a delta with clamp and callbacks."""
        return self._set_value(self.value + float(delta), reason=ValueChangeReason.PROGRAMMATIC)

    @property
    def normalized(self) -> float:
        """Return the current value as a normalized 0.0–1.0 ratio within the slider range.

        Returns 0.0 when minimum equals maximum.
        """
        span = self.maximum - self.minimum
        if span <= 0:
            return 0.0
        return min(max((self.value - self.minimum) / span, 0.0), 1.0)

    def set_normalized(self, ratio: float) -> bool:
        """Set value from a normalized 0.0–1.0 ratio. Clamped to the valid range."""
        clamped = min(max(float(ratio), 0.0), 1.0)
        return self.set_value(self.minimum + clamped * (self.maximum - self.minimum))

    def _set_value(self, new_value: float, reason: ValueChangeReason = ValueChangeReason.PROGRAMMATIC) -> bool:
        old_value = self.value
        self.value = float(new_value)
        self._clamp_value()
        changed = self.value != old_value
        if changed and reason == ValueChangeReason.PROGRAMMATIC:
            self._programmatic_change_epoch += 1
        if changed:
            dispatch_value_change(self.on_change, self.value, reason)
        return changed

    def handle_rect(self) -> Rect:
        self._normalize_range()
        pixel = self._drag_handle_axis_pixel if self.dragging else self._to_pixel(self.value)
        handle_len = self._handle_length()
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(int(round(pixel - (handle_len / 2.0))), self.rect.y, handle_len, self.rect.height)
        return Rect(self.rect.x, int(round(pixel - (handle_len / 2.0))), self.rect.width, handle_len)

    def _build_lock_rect(self, pointer_pos) -> Rect:
        travel = self._travel_rect()
        travel_span = self._travel_span()
        if self.axis == LayoutAxis.HORIZONTAL:
            min_pointer = travel.left + self._drag_anchor_offset
            max_pointer = travel.left + travel_span + self._drag_anchor_offset
            return Rect(min_pointer, pointer_pos[1], max(1, (max_pointer - min_pointer) + 1), 1)
        min_pointer = travel.top + self._drag_anchor_offset
        max_pointer = travel.top + travel_span + self._drag_anchor_offset
        return Rect(pointer_pos[0], min_pointer, 1, max(1, (max_pointer - min_pointer) + 1))

    def _lock_area_axis_rect(self, app: "GuiApplication", pointer_pos) -> Optional[Rect]:
        if app.lock_area is None:
            return None
        lock = Rect(app.lock_area)
        handle_len = self._handle_length()
        if self.axis == LayoutAxis.HORIZONTAL:
            # Keep pointer/anchor relationship stable while enforcing lock-area limits
            # for the full handle footprint.
            min_pointer = int(lock.left + self._drag_anchor_offset)
            max_pointer = int((lock.right - handle_len) + self._drag_anchor_offset)
            if max_pointer < min_pointer:
                max_pointer = min_pointer
            return Rect(min_pointer, int(pointer_pos[1]), max(1, (max_pointer - min_pointer) + 1), 1)
        min_pointer = int(lock.top + self._drag_anchor_offset)
        max_pointer = int((lock.bottom - handle_len) + self._drag_anchor_offset)
        if max_pointer < min_pointer:
            max_pointer = min_pointer
        return Rect(int(pointer_pos[0]), min_pointer, 1, max(1, (max_pointer - min_pointer) + 1))

    def _refresh_drag_lock_rect(self, app: "GuiApplication", pointer_pos) -> None:
        lock_rect = self._build_lock_rect(pointer_pos)
        axis_lock = self._lock_area_axis_rect(app, pointer_pos)
        if axis_lock is not None:
            clipped = lock_rect.clip(axis_lock)
            if clipped.width > 0 and clipped.height > 0:
                lock_rect = clipped
            else:
                lock_rect = axis_lock
        app.pointer_capture.lock_rect = Rect(lock_rect)

    def _constrained_drag_pointer(self, app: "GuiApplication", pointer_pos):
        self._refresh_drag_lock_rect(app, pointer_pos)
        lock = app.pointer_capture.lock_rect
        if lock is None:
            pointer_axis = int(pointer_pos[0]) if self.axis == LayoutAxis.HORIZONTAL else int(pointer_pos[1])
            return pointer_pos, pointer_axis
        if self.axis == LayoutAxis.HORIZONTAL:
            pointer_axis = min(max(int(pointer_pos[0]), lock.left), lock.right - 1)
            pointer_pos = (int(pointer_axis), int(lock.top))
        else:
            pointer_axis = min(max(int(pointer_pos[1]), lock.top), lock.bottom - 1)
            pointer_pos = (int(lock.left), int(pointer_axis))
        # Keep rendered cursor anchored without warping hardware every motion event.
        app.set_logical_pointer_position(pointer_pos, apply_constraints=False)
        return pointer_pos, pointer_axis

    def _update_drag_handle_pixel(self, pointer_axis: int) -> int:
        """Clamp *pointer_axis* to travel bounds, update ``_drag_handle_axis_pixel``, and return the raw axis pixel."""
        handle_len = max(1, int(self.handle_size))
        is_h = self.axis == LayoutAxis.HORIZONTAL
        origin = self.rect.left if is_h else self.rect.top
        span = max(0, (self.rect.width if is_h else self.rect.height) - handle_len)
        half = handle_len / 2.0
        axis_pixel = pointer_axis - self._drag_anchor_offset + (handle_len // 2)
        self._drag_handle_axis_pixel = min(max(axis_pixel, int(round(origin + half))), int(round(origin + half + span)))
        return axis_pixel

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            if self.dragging:
                self._end_drag(app)
            return False

        if self.dragging and self._drag_start_programmatic_epoch != self._programmatic_change_epoch:
            self._end_drag(app)
            return False

        if not self.focused and (
            event.is_key_down(pygame.K_HOME)
            or event.is_key_down(pygame.K_END)
            or event.is_key_down(pygame.K_LEFT)
            or event.is_key_down(pygame.K_RIGHT)
            or event.is_key_down(pygame.K_DOWN)
            or event.is_key_down(pygame.K_UP)
        ):
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
                return self._set_value(self.value + step, reason=ValueChangeReason.KEYBOARD)
            if event.is_key_down(pygame.K_UP):
                return self._set_value(self.value - step, reason=ValueChangeReason.KEYBOARD)

        event_pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else None
        pointer = app.logical_pointer_pos
        if event.is_mouse_down(1) and isinstance(pointer, tuple) and len(pointer) == 2:
            handle = self.handle_rect()
            if handle.collidepoint(pointer):
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = pointer[0] - handle.x
                else:
                    self._drag_anchor_offset = pointer[1] - handle.y
                self._refresh_drag_lock_rect(app, pointer)
                app.pointer_capture.begin(self.control_id, app.pointer_capture.lock_rect, use_relative_motion=True)
                pointer_pos = app.logical_pointer_pos
                pointer_axis = int(pointer_pos[0]) if self.axis == LayoutAxis.HORIZONTAL else int(pointer_pos[1])
                self._update_drag_handle_pixel(pointer_axis)
                self._drag_start_programmatic_epoch = self._programmatic_change_epoch
                self.dragging = True
                return True

        if event.is_mouse_motion() and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pointer_pos = app.logical_pointer_pos
            if self._ancestor_window() is None and isinstance(pointer_pos, tuple) and len(pointer_pos) == 2 and app.scene._point_in_window(pointer_pos):
                self._end_drag(app, sync_pointer=True, release_pos=pointer_pos)
                return False
            pointer_pos, pointer_axis = self._constrained_drag_pointer(app, pointer_pos)
            axis_pixel = self._update_drag_handle_pixel(pointer_axis)
            return self._set_value(self._to_value(axis_pixel), reason=ValueChangeReason.MOUSE_DRAG)

        if event.is_mouse_up(1) and self.dragging:
            pointer_pos = app.logical_pointer_pos
            pointer_pos, pointer_axis = self._constrained_drag_pointer(app, pointer_pos)
            axis_pixel = self._update_drag_handle_pixel(pointer_axis)
            self._set_value(self._to_value(axis_pixel), reason=ValueChangeReason.MOUSE_DRAG)
            self._end_drag(app, sync_pointer=True)
            return True

        logical_pointer = app.logical_pointer_pos if isinstance(app.logical_pointer_pos, tuple) and len(app.logical_pointer_pos) == 2 else None
        wheel_hit = (
            isinstance(event_pointer, tuple)
            and self.rect.collidepoint(event_pointer)
        ) or (
            isinstance(logical_pointer, tuple)
            and self.rect.collidepoint(logical_pointer)
        )
        if event.is_mouse_wheel() and wheel_hit:
            return self._set_value(
                self.value - (float(event.wheel_delta) * ((self.maximum - self.minimum) * 0.05)),
                reason=ValueChangeReason.WHEEL,
            )
        return False

    def capture_state(self) -> dict:  # type: ignore[override]
        """Return current slider value and bounds as a serializable dict."""
        return {"value": float(self.value), "minimum": float(self.minimum), "maximum": float(self.maximum)}

    def restore_state(self, state: dict) -> None:  # type: ignore[override]
        """Restore slider value from a previously captured state dict."""
        if "value" in state:
            self._set_value(float(state["value"]))

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
            armed=self.dragging or self._focus_activation_armed,
            hovered=not self.dragging,
        )
        surface.blit(track_selected, travel)
        surface.blit(handle_selected, handle)
