import pygame
from typing import Optional, TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ...events.value_change import ValueChangeCallback
from ...events.value_change import ValueChangeReason
from ...events.value_change import dispatch_value_change
from ...events.value_change import validate_value_change_callback
from ..base._axis_drag_control_base import _AxisDragControlBase
from ...layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_SCROLLBAR_FOCUS_KEYS: frozenset[int] = frozenset((
    pygame.K_HOME,
    pygame.K_END,
    pygame.K_PAGEUP,
    pygame.K_PAGEDOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_UP,
    pygame.K_DOWN,
))


class ScrollbarControl(_AxisDragControlBase):
    """Viewport scrollbar with captured handle drag and wheel stepping."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        axis: LayoutAxis,
        content_size: int,
        viewport_size: int,
        offset: int = 0,
        step: int = 16,
        on_change: Optional[ValueChangeCallback[int]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.content_size = max(1, int(content_size))
        self.viewport_size = max(1, int(viewport_size))
        self.offset = max(0, int(offset))
        self.step = max(1, int(step))
        self.on_change = on_change
        validate_value_change_callback(self.on_change)
        self._init_axis_drag_state()
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_offset()

    def set_on_change_callback(self, callback: Optional[ValueChangeCallback[int]]) -> Optional[ValueChangeCallback[int]]:
        """Update callback at runtime."""
        validate_value_change_callback(callback)
        self.on_change = callback
        return self.on_change

    def _normalize_geometry(self) -> None:
        self.content_size = max(1, int(self.content_size))
        self.viewport_size = max(1, int(self.viewport_size))
        self.step = max(1, int(self.step))

    def _max_offset(self) -> int:
        self._normalize_geometry()
        return max(0, self.content_size - self.viewport_size)

    def _clamp_offset(self) -> None:
        self.offset = min(max(0, self.offset), self._max_offset())

    def _page_step(self) -> int:
        return max(self.step, int(round(self.viewport_size * 0.9)))

    def set_offset(self, offset: int) -> bool:
        """Set offset programmatically with clamp and on_change callback semantics."""
        return self._set_offset(offset, reason=ValueChangeReason.PROGRAMMATIC)

    def adjust_offset(self, delta: int) -> bool:
        """Adjust offset programmatically by a delta with clamp and callbacks."""
        return self._set_offset(self.offset + int(delta), reason=ValueChangeReason.PROGRAMMATIC)

    @property
    def scroll_fraction(self) -> float:
        """Return the current scroll position as a normalized 0.0–1.0 fraction.

        0.0 means scrolled to the beginning, 1.0 means scrolled to the end.
        Returns 0.0 when content fits entirely within the viewport.
        """
        max_off = self._max_offset()
        if max_off <= 0:
            return 0.0
        return min(max(self.offset / max_off, 0.0), 1.0)

    def _set_offset(self, new_offset: int, reason: ValueChangeReason = ValueChangeReason.PROGRAMMATIC) -> bool:
        old_offset = self.offset
        self.offset = int(new_offset)
        self._clamp_offset()
        changed = self.offset != old_offset
        if changed and reason == ValueChangeReason.PROGRAMMATIC:
            self._programmatic_change_epoch += 1
        if changed:
            dispatch_value_change(self.on_change, self.offset, reason)
        return changed

    def should_arm_focus_activation_for_event(self, event: GuiEvent) -> bool:
        """Return True when this key event should arm the handle visual.

        Supports accessibility-style less/more and home/end keyboard adjustments.
        """
        if event.is_key_down(pygame.K_HOME) or event.is_key_down(pygame.K_END):
            return True
        if event.is_key_down(pygame.K_PAGEUP) or event.is_key_down(pygame.K_PAGEDOWN):
            return True
        if self.axis == LayoutAxis.HORIZONTAL:
            return bool(event.is_key_down(pygame.K_LEFT) or event.is_key_down(pygame.K_RIGHT))
        return bool(event.is_key_down(pygame.K_UP) or event.is_key_down(pygame.K_DOWN))

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point used by the focus manager's armed-visual path."""
        # Scrollbars activate visually on focus key activation; offset changes remain
        # driven by directional/page/home/end keys and pointer interaction.
        return

    def _handle_length(self) -> int:
        if self.content_size <= 0:
            return 12
        ratio = min(1.0, self.viewport_size / float(self.content_size))
        if self.axis == LayoutAxis.HORIZONTAL:
            track_span = max(1, self.rect.width)
        else:
            track_span = max(1, self.rect.height)
        base = int(round(track_span * ratio))
        return max(1, min(track_span, max(12, base)))

    def _offset_to_pixel_with_len(self, handle_len: int) -> int:
        max_offset = self._max_offset()
        travel_span = max(1, (self.rect.width - handle_len) if self.axis == LayoutAxis.HORIZONTAL else (self.rect.height - handle_len))
        ratio = 0.0 if max_offset <= 0 else self.offset / float(max_offset)
        return int(round(ratio * travel_span))

    def _pixel_to_offset(self, pixel: int, handle_len: int) -> int:
        travel_span = max(1, (self.rect.width - handle_len) if self.axis == LayoutAxis.HORIZONTAL else (self.rect.height - handle_len))
        max_offset = self._max_offset()
        ratio = min(max(pixel / float(travel_span), 0.0), 1.0)
        return int(round(ratio * max_offset))

    def handle_rect(self) -> Rect:
        self._clamp_offset()
        handle_len = self._handle_length()
        pixel = self._drag_handle_axis_pixel if self.dragging else self._offset_to_pixel_with_len(handle_len)
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(self.rect.left + pixel, self.rect.top, handle_len, self.rect.height)
        return Rect(self.rect.left, self.rect.top + pixel, self.rect.width, handle_len)

    def _lock_rect(self, pointer_pos, handle_len: int) -> Rect:
        travel_span = max(1, (self.rect.width - handle_len) if self.axis == LayoutAxis.HORIZONTAL else (self.rect.height - handle_len))
        if self.axis == LayoutAxis.HORIZONTAL:
            min_pointer = self.rect.left + self._drag_anchor_offset
            max_pointer = self.rect.left + travel_span + self._drag_anchor_offset
            return Rect(min_pointer, pointer_pos[1], max(1, (max_pointer - min_pointer) + 1), 1)
        min_pointer = self.rect.top + self._drag_anchor_offset
        max_pointer = self.rect.top + travel_span + self._drag_anchor_offset
        return Rect(pointer_pos[0], min_pointer, 1, max(1, (max_pointer - min_pointer) + 1))

    def _lock_area_axis_rect(self, app: "GuiApplication", pointer_pos, handle_len: int) -> Optional[Rect]:
        if app.lock_area is None:
            return None
        lock = Rect(app.lock_area)
        if self.axis == LayoutAxis.HORIZONTAL:
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

    def _refresh_drag_lock_rect(self, app: "GuiApplication", pointer_pos, handle_len: int) -> None:
        lock_rect = self._lock_rect(pointer_pos, handle_len)
        axis_lock = self._lock_area_axis_rect(app, pointer_pos, handle_len)
        if axis_lock is not None:
            clipped = lock_rect.clip(axis_lock)
            if clipped.width > 0 and clipped.height > 0:
                lock_rect = clipped
            else:
                lock_rect = axis_lock
        app.pointer_capture.lock_rect = Rect(lock_rect)

    def _constrained_drag_pointer(self, app: "GuiApplication", pointer_pos, handle_len: int):
        self._refresh_drag_lock_rect(app, pointer_pos, handle_len)
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
        app.set_logical_pointer_position(pointer_pos, apply_constraints=False)
        return pointer_pos, pointer_axis

    def _update_drag_handle_pixel(self, pointer_axis: int, handle_len: int) -> int:
        """Compute axis pixel from *pointer_axis*, clamp and store in ``_drag_handle_axis_pixel``, return the raw axis pixel."""
        is_h = self.axis == LayoutAxis.HORIZONTAL
        track_origin = self.rect.left if is_h else self.rect.top
        axis_pixel = pointer_axis - track_origin - self._drag_anchor_offset
        travel_span = max(1, (self.rect.width if is_h else self.rect.height) - handle_len)
        self._drag_handle_axis_pixel = min(max(axis_pixel, 0), travel_span)
        return axis_pixel

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            if self.dragging:
                self._end_drag(app)
            return False

        if self.dragging and self._drag_start_programmatic_epoch != self._programmatic_change_epoch:
            self._end_drag(app)
            return False

        if not self.focused and event.kind is EventType.KEY_DOWN and event.key in _SCROLLBAR_FOCUS_KEYS:
            return False

        if event.is_key_down(pygame.K_HOME):
            return self._set_offset(0, reason=ValueChangeReason.KEYBOARD)
        if event.is_key_down(pygame.K_END):
            return self._set_offset(self._max_offset(), reason=ValueChangeReason.KEYBOARD)
        if event.is_key_down(pygame.K_PAGEUP):
            return self._set_offset(self.offset - self._page_step(), reason=ValueChangeReason.KEYBOARD)
        if event.is_key_down(pygame.K_PAGEDOWN):
            return self._set_offset(self.offset + self._page_step(), reason=ValueChangeReason.KEYBOARD)
        if self.axis == LayoutAxis.HORIZONTAL:
            if event.is_key_down(pygame.K_LEFT):
                return self._set_offset(self.offset - self.step, reason=ValueChangeReason.KEYBOARD)
            if event.is_key_down(pygame.K_RIGHT):
                return self._set_offset(self.offset + self.step, reason=ValueChangeReason.KEYBOARD)
        else:
            if event.is_key_down(pygame.K_UP):
                return self._set_offset(self.offset - self.step, reason=ValueChangeReason.KEYBOARD)
            if event.is_key_down(pygame.K_DOWN):
                return self._set_offset(self.offset + self.step, reason=ValueChangeReason.KEYBOARD)

        event_pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else None
        pointer = app.logical_pointer_pos
        if event.is_mouse_down(1) and isinstance(pointer, tuple) and len(pointer) == 2:
            handle = self.handle_rect()
            if handle.collidepoint(pointer):
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = pointer[0] - handle.x
                else:
                    self._drag_anchor_offset = pointer[1] - handle.y
                handle_len = handle.width if self.axis == LayoutAxis.HORIZONTAL else handle.height
                self._refresh_drag_lock_rect(app, pointer, handle_len)
                app.pointer_capture.begin(self.control_id, app.pointer_capture.lock_rect, use_relative_motion=True)
                pointer_pos = pointer
                self._drag_handle_axis_pixel = (
                    int(pointer_pos[0]) - self.rect.left - self._drag_anchor_offset
                    if self.axis == LayoutAxis.HORIZONTAL
                    else int(pointer_pos[1]) - self.rect.top - self._drag_anchor_offset
                )
                self._drag_start_programmatic_epoch = self._programmatic_change_epoch
                self.dragging = True
                return True

        if event.is_mouse_motion() and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pointer_pos = app.logical_pointer_pos
            if self._ancestor_window() is None and isinstance(pointer_pos, tuple) and len(pointer_pos) == 2 and app.scene._point_in_window(pointer_pos):
                self._end_drag(app, sync_pointer=True, release_pos=pointer_pos)
                return False
            handle_len = self._handle_length()
            pointer_pos, pointer_axis = self._constrained_drag_pointer(app, pointer_pos, handle_len)
            axis_pixel = self._update_drag_handle_pixel(pointer_axis, handle_len)
            return self._set_offset(self._pixel_to_offset(axis_pixel, handle_len), reason=ValueChangeReason.MOUSE_DRAG)

        if event.is_mouse_up(1) and self.dragging:
            pointer_pos = app.logical_pointer_pos
            handle_len = self._handle_length()
            pointer_pos, pointer_axis = self._constrained_drag_pointer(app, pointer_pos, handle_len)
            axis_pixel = self._update_drag_handle_pixel(pointer_axis, handle_len)
            self._set_offset(self._pixel_to_offset(axis_pixel, handle_len), reason=ValueChangeReason.MOUSE_DRAG)
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
            return self._set_offset(self.offset - (int(event.wheel_delta) * self.step), reason=ValueChangeReason.WHEEL)
        return False

    def capture_state(self) -> dict:  # type: ignore[override]
        """Return current scrollbar offset as a serializable dict."""
        return {"offset": int(self.offset)}

    def restore_state(self, state: dict) -> None:  # type: ignore[override]
        """Restore scrollbar offset from a previously captured state dict."""
        if "offset" in state:
            self._set_offset(int(state["offset"]))

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        handle = self.handle_rect()
        factory = theme.graphics_factory
        track_size = (self.rect.width, self.rect.height)
        handle_size = (handle.width, handle.height)
        if self._track_visuals is None or self._track_visuals_size != track_size:
            self._track_visuals = factory.build_frame_visuals(self.rect)
            self._track_visuals_size = track_size
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
        surface.blit(track_selected, self.rect)
        surface.blit(handle_selected, handle)
