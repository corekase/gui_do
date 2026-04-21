from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pygame import Rect, SRCALPHA
from pygame.draw import line, rect
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL
from pygame.surface import Surface

from ..utility.events import colours, GuiError, InteractiveState, Orientation
from ..utility.input.normalized_event import normalize_input_event
from ..utility.input.overlay_drag_guard import cancel_drag_for_overlay_contact
from ..utility.intermediates.axis_range import AxisRangeMixin
from ..utility.intermediates.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window


@dataclass(frozen=True)
class _SliderGeometry:
    track_rect: Rect
    graphic_rect: Rect
    draw_rect: Rect


class Slider(Widget, AxisRangeMixin):
    """Single-handle slider supporting float and integer logical ranges."""

    @property
    def value(self) -> float:
        """Current logical slider value."""
        return self._position

    @value.setter
    def value(self, position: float) -> None:
        """Set slider value with clamping and optional integer snapping."""
        self._position = self.clamp_axis_position(position, self._total_range, self._integer_type)

    def __init__(
        self,
        gui: "GuiManager",
        id: str,
        rect: Rect,
        horizontal: Orientation,
        total_range: int,
        position: float = 0.0,
        integer_type: bool = False,
        notch_interval_percent: float = 5.0,
        wheel_positive_to_max: bool = False,
        wheel_step: Optional[float] = None,
    ) -> None:
        """Create Slider."""
        super().__init__(gui, id, rect)
        self._set_orientation(horizontal)
        self._validate_constructor_args(total_range, integer_type, notch_interval_percent, wheel_positive_to_max, wheel_step)

        self._total_range: int = total_range
        self._integer_type: bool = integer_type
        self._notch_interval_percent: float = float(notch_interval_percent)
        self._wheel_positive_to_max: bool = wheel_positive_to_max
        self._wheel_step: Optional[float] = None if wheel_step is None else float(wheel_step)

        self.state: InteractiveState = InteractiveState.Idle
        self._wheel_active: bool = False
        self._dragging: bool = False
        self._drag_anchor_offset: int = 0

        self._handle_size: int = self._compute_handle_size(self.draw_rect)
        geometry = self._build_geometry(self.draw_rect)
        self._track_rect = geometry.track_rect
        self._graphic_rect = geometry.graphic_rect
        self.draw_rect = geometry.draw_rect

        self._track_bitmap = self._build_track_bitmap()
        self._disabled_track_bitmap = self.gui.graphics_factory.build_disabled_bitmap(self._track_bitmap)
        self._idle_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['medium'], colours['none'])
        self._hover_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['highlight'], colours['none'])
        self._armed_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['highlight'], colours['none'])
        self._disabled_handle = self.gui.graphics_factory.build_disabled_bitmap(self._idle_handle)

        self.value = position

    def _validate_constructor_args(
        self,
        total_range: int,
        integer_type: bool,
        notch_interval_percent: float,
        wheel_positive_to_max: bool,
        wheel_step: Optional[float],
    ) -> None:
        """Validate constructor arguments."""
        if not isinstance(total_range, int) or total_range <= 0:
            raise GuiError(f'total_range must be a positive int, got: {total_range}')
        if not isinstance(integer_type, bool):
            raise GuiError(f'integer_type must be a bool, got: {integer_type}')
        if not isinstance(notch_interval_percent, (int, float)):
            raise GuiError(f'notch_interval_percent must be a number, got: {notch_interval_percent}')
        if notch_interval_percent <= 0 or notch_interval_percent > 100:
            raise GuiError(f'notch_interval_percent must be in (0, 100], got: {notch_interval_percent}')
        if not isinstance(wheel_positive_to_max, bool):
            raise GuiError(f'wheel_positive_to_max must be a bool, got: {wheel_positive_to_max}')
        if wheel_step is None:
            return
        if not isinstance(wheel_step, (int, float)):
            raise GuiError(f'wheel_step must be None or a number, got: {wheel_step}')
        if float(wheel_step) <= 0.0:
            raise GuiError(f'wheel_step must be > 0 when provided, got: {wheel_step}')

    def _compute_handle_size(self, layout_rect: Rect) -> int:
        """Compute a visually stable handle size from the layout rect."""
        base_handle_size = max(6, min(layout_rect.width, layout_rect.height) - 4)
        reduced_handle_size = max(6, int(round(base_handle_size * 0.8)))
        if reduced_handle_size % 2 != 0:
            reduced_handle_size -= 1
            if reduced_handle_size < 6:
                reduced_handle_size = 6
        return reduced_handle_size

    def _build_geometry(self, layout_rect: Rect) -> _SliderGeometry:
        """Build track, travel, and final draw geometry."""
        track_thickness = max(2, min(6, min(layout_rect.width, layout_rect.height) // 3))
        if self._horizontal == Orientation.Horizontal:
            track_w = max(1, layout_rect.width)
            track_y = layout_rect.y + self.gui.graphics_factory.centre(layout_rect.height, track_thickness)
            track_rect = Rect(layout_rect.x, track_y, track_w, track_thickness)
            travel = max(1, layout_rect.width - self._handle_size)
            handle_y = int(round(track_rect.centery - (self._handle_size / 2.0)))
            graphic_rect = Rect(layout_rect.x, handle_y, travel, self._handle_size)
            min_handle = Rect(graphic_rect.x, graphic_rect.y, self._handle_size, self._handle_size)
            max_handle = Rect(graphic_rect.x + graphic_rect.width, graphic_rect.y, self._handle_size, self._handle_size)
        else:
            track_h = max(1, layout_rect.height)
            track_x = layout_rect.x + self.gui.graphics_factory.centre(layout_rect.width, track_thickness)
            track_rect = Rect(track_x, layout_rect.y, track_thickness, track_h)
            travel = max(1, layout_rect.height - self._handle_size)
            handle_x = int(round(track_rect.centerx - (self._handle_size / 2.0)))
            graphic_rect = Rect(handle_x, layout_rect.y, self._handle_size, travel)
            min_handle = Rect(graphic_rect.x, graphic_rect.y, self._handle_size, self._handle_size)
            max_handle = Rect(graphic_rect.x, graphic_rect.y + graphic_rect.height, self._handle_size, self._handle_size)
        draw_rect = track_rect.union(min_handle).union(max_handle)
        return _SliderGeometry(track_rect=track_rect, graphic_rect=graphic_rect, draw_rect=draw_rect)

    def _on_disabled_changed(self, disabled: bool) -> None:
        """Synchronize interaction state with disabled transitions."""
        if disabled:
            self._reset_drag()
            self._wheel_active = False
            self.state = InteractiveState.Disabled
        else:
            self._wheel_active = False
            self.state = InteractiveState.Idle

    def _build_track_bitmap(self) -> Surface:
        """Render a transparent track with notch marks."""
        bitmap = Surface((self.draw_rect.width, self.draw_rect.height), SRCALPHA)
        local_track = self._track_rect.move(-self.draw_rect.x, -self.draw_rect.y)

        half_handle = self._handle_size // 2
        if self._horizontal == Orientation.Horizontal:
            axis_start = local_track.left + half_handle
            axis_end = local_track.right - half_handle
            trimmed = Rect(axis_start, local_track.top, max(1, axis_end - axis_start), local_track.height)
        else:
            axis_start = local_track.top + half_handle
            axis_end = local_track.bottom - half_handle
            trimmed = Rect(local_track.left, axis_start, local_track.width, max(1, axis_end - axis_start))

        rect(bitmap, colours['dark'] + (255,), trimmed, 0)

        for notch in self._notch_points():
            if self._horizontal == Orientation.Horizontal:
                center = self._notch_pixel(notch, trimmed.left, max(0, trimmed.width - 1))
                y1 = trimmed.top - 2
                y2 = (trimmed.bottom - 1) + 2
                line(bitmap, colours['full'] + (200,), (center, y1), (center, y2), 1)
            else:
                center = self._notch_pixel(notch, trimmed.top, max(0, trimmed.height - 1))
                x1 = trimmed.left - 2
                x2 = (trimmed.right - 1) + 2
                line(bitmap, colours['full'] + (200,), (x1, center), (x2, center), 1)
        return bitmap

    def _notch_pixel(self, value: float, start: int, span: int) -> int:
        """Map logical notch to a local axis pixel."""
        if self._total_range <= 0 or span <= 0:
            return start
        ratio = float(value) / float(self._total_range)
        return int(round(start + (ratio * span)))

    def _notch_points(self) -> list[float]:
        """Return logical notch positions across the slider range."""
        if self._integer_type:
            return [float(i) for i in range(0, self._total_range + 1)]

        interval_units = (self._total_range * self._notch_interval_percent) / 100.0
        if interval_units <= 0.0:
            interval_units = 1.0

        points: list[float] = []
        current = 0.0
        maximum = float(self._total_range)
        while current <= maximum:
            points.append(current)
            current += interval_units
        if not points or points[-1] != maximum:
            points.append(maximum)
        return points

    def _handle_area(self) -> Rect:
        """Return current handle rect in widget coordinates."""
        axis_pixel = self.total_to_pixel(self._position, self._total_range)
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x + axis_pixel, self._graphic_rect.y, self._handle_size, self._handle_size)
        return Rect(self._graphic_rect.x, self._graphic_rect.y + axis_pixel, self._handle_size, self._handle_size)

    def _wheel_hit_area(self) -> Rect:
        """Return wheel interaction corridor covering full handle travel."""
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x, self._graphic_rect.y, self._graphic_rect.width + self._handle_size, self._handle_size)
        return Rect(self._graphic_rect.x, self._graphic_rect.y, self._handle_size, self._graphic_rect.height + self._handle_size)

    def _resolve_wheel_step(self) -> float:
        """Resolve wheel step size in logical units."""
        if self._wheel_step is not None:
            return self._wheel_step
        default_step = float(self._total_range) * 0.1
        if self._integer_type:
            return float(round(default_step))
        return default_step

    def leave(self) -> None:
        """Reset non-drag hover state when pointer leaves the widget."""
        if self._dragging:
            return
        self._wheel_active = False
        if self.disabled:
            self.state = InteractiveState.Disabled
        else:
            self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle wheel/drag interactions for logical value updates."""
        if self.disabled:
            return False
        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP, MOUSEWHEEL):
            return False

        normalized = normalize_input_event(event)

        if event.type == MOUSEWHEEL:
            mouse_point = self.gui._convert_to_window(self.gui._get_mouse_pos(), window)
            if self._dragging or not self._wheel_hit_area().collidepoint(mouse_point):
                return False
            wheel_delta = normalized.wheel_delta
            if wheel_delta == 0:
                return False
            direction = 1 if wheel_delta > 0 else -1
            if not self._wheel_positive_to_max:
                direction *= -1
            self.value = self.value + (direction * abs(wheel_delta) * self._resolve_wheel_step())
            self._wheel_active = True
            self.state = InteractiveState.Armed
            return True

        if event.type in (MOUSEMOTION, MOUSEBUTTONUP):
            if cancel_drag_for_overlay_contact(
                self.gui,
                self._dragging,
                window,
                self._reset_drag,
                lambda: setattr(self, 'state', InteractiveState.Idle),
            ):
                return True

        mouse_point = self.gui._convert_to_window(self.gui._get_mouse_pos(), window)

        if event.type == MOUSEBUTTONDOWN:
            if not normalized.is_left_down:
                return False
            handle_rect = self._handle_area()
            if not handle_rect.collidepoint(mouse_point):
                return False

            if self._horizontal == Orientation.Horizontal:
                self._drag_anchor_offset = mouse_point[0] - handle_rect.x
                lock_x = self._graphic_rect.x + self._drag_anchor_offset
                lock_y = mouse_point[1]
                lock_w = self._graphic_rect.width + 1
                lock_h = 1
            else:
                self._drag_anchor_offset = mouse_point[1] - handle_rect.y
                lock_x = mouse_point[0]
                lock_y = self._graphic_rect.y + self._drag_anchor_offset
                lock_w = 1
                lock_h = self._graphic_rect.height + 1

            lock_screen_x, lock_screen_y = self.gui._convert_to_screen((lock_x, lock_y), window)
            self.gui.set_lock_area(self, Rect(lock_screen_x, lock_screen_y, lock_w, lock_h))
            self._dragging = True
            self.state = InteractiveState.Armed
            return True

        if event.type == MOUSEMOTION:
            if not self._dragging:
                if self._wheel_active and not self._wheel_hit_area().collidepoint(mouse_point):
                    self._wheel_active = False
                if self._wheel_active:
                    self.state = InteractiveState.Armed
                elif self._handle_area().collidepoint(mouse_point):
                    self.state = InteractiveState.Hover
                else:
                    self.state = InteractiveState.Idle
                return False

            drag_pos = normalized.pos if isinstance(normalized.pos, tuple) and len(normalized.pos) == 2 else self.gui._get_mouse_pos()
            drag_point = self.gui._convert_to_window(drag_pos, window)
            if self._horizontal == Orientation.Horizontal:
                axis_pixel = drag_point[0] - self._graphic_rect.x - self._drag_anchor_offset
            else:
                axis_pixel = drag_point[1] - self._graphic_rect.y - self._drag_anchor_offset
            self.value = self.pixel_to_total(axis_pixel, self._total_range)
            self.state = InteractiveState.Armed
            return True

        if not normalized.is_left_up or not self._dragging:
            return False
        self._reset_drag()

        if self._wheel_active and self._wheel_hit_area().collidepoint(mouse_point):
            self.state = InteractiveState.Armed
        elif self._handle_area().collidepoint(mouse_point):
            self.state = InteractiveState.Hover
        else:
            self.state = InteractiveState.Idle
        return True

    def _reset_drag(self) -> None:
        """Release lock and clear drag state."""
        self.gui.set_lock_area(None)
        self._dragging = False
        self._drag_anchor_offset = 0

    def draw(self) -> None:
        """Draw the slider track and handle."""
        super().draw()
        if self.disabled:
            self.surface.blit(self._disabled_track_bitmap, (self.draw_rect.x, self.draw_rect.y))
            handle = self._disabled_handle
        else:
            self.surface.blit(self._track_bitmap, (self.draw_rect.x, self.draw_rect.y))
            if self.state == InteractiveState.Armed:
                handle = self._armed_handle
            elif self.state == InteractiveState.Hover:
                handle = self._hover_handle
            else:
                handle = self._idle_handle

        handle_rect = self._handle_area()
        self.surface.blit(handle, (handle_rect.x, handle_rect.y))
