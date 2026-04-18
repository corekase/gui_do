from __future__ import annotations

from pygame import Rect, SRCALPHA
from pygame.draw import line, rect
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pygame.surface import Surface
from typing import Optional, TYPE_CHECKING

from ..utility.axis_range import AxisRangeMixin
from ..utility.events import colours, GuiError, InteractiveState, Orientation
from ..utility.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window


class Slider(Widget, AxisRangeMixin):
    """Single-handle slider supporting optional integer snapping."""

    @property
    def value(self) -> float:
        """Current logical slider value."""
        return self._position

    @value.setter
    def value(self, position: float) -> None:
        """Set slider value with clamping and optional snapping."""
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
    ) -> None:
        """Create Slider."""
        super().__init__(gui, id, rect)
        self._set_orientation(horizontal)
        if not isinstance(total_range, int) or total_range <= 0:
            raise GuiError(f'total_range must be a positive int, got: {total_range}')
        if not isinstance(integer_type, bool):
            raise GuiError(f'integer_type must be a bool, got: {integer_type}')
        if not isinstance(notch_interval_percent, (int, float)):
            raise GuiError(f'notch_interval_percent must be a number, got: {notch_interval_percent}')
        if notch_interval_percent <= 0 or notch_interval_percent > 100:
            raise GuiError(f'notch_interval_percent must be in (0, 100], got: {notch_interval_percent}')

        self._total_range: int = total_range
        self._integer_type: bool = integer_type
        self._notch_interval_percent: float = float(notch_interval_percent)
        self.state: InteractiveState = InteractiveState.Idle
        self._dragging: bool = False
        self._drag_anchor_offset: int = 0

        base_handle_size = max(6, min(self.draw_rect.width, self.draw_rect.height) - 4)
        reduced_handle_size = max(6, int(round(base_handle_size * 0.8)))
        # Keep handle dimensions even to avoid half-pixel visual drift after scaling.
        if reduced_handle_size % 2 != 0:
            reduced_handle_size -= 1
            if reduced_handle_size < 6:
                reduced_handle_size = 6
        self._handle_size = reduced_handle_size
        track_thickness = max(2, min(6, min(self.draw_rect.width, self.draw_rect.height) // 3))

        if self._horizontal == Orientation.Horizontal:
            track_w = max(1, self.draw_rect.width)
            track_y = self.draw_rect.y + self.gui.graphics_factory.centre(self.draw_rect.height, track_thickness)
            self._track_rect = Rect(self.draw_rect.x, track_y, track_w, track_thickness)
            travel = max(1, self.draw_rect.width - self._handle_size)
            handle_y = int(round(self._track_rect.centery - (self._handle_size / 2.0)))
            self._graphic_rect = Rect(self.draw_rect.x, handle_y, travel, self._handle_size)
        else:
            track_h = max(1, self.draw_rect.height)
            track_x = self.draw_rect.x + self.gui.graphics_factory.centre(self.draw_rect.width, track_thickness)
            self._track_rect = Rect(track_x, self.draw_rect.y, track_thickness, track_h)
            travel = max(1, self.draw_rect.height - self._handle_size)
            handle_x = int(round(self._track_rect.centerx - (self._handle_size / 2.0)))
            self._graphic_rect = Rect(handle_x, self.draw_rect.y, self._handle_size, travel)

        self._track_bitmap = self._build_track_bitmap()
        self._disabled_track_bitmap = self.gui.graphics_factory.build_disabled_bitmap(self._track_bitmap)
        self._idle_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['medium'], colours['none'])
        self._hover_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['highlight'], colours['none'])
        self._armed_handle = self.gui.graphics_factory.draw_radio_bitmap(self._handle_size, colours['highlight'], colours['none'])
        self._disabled_handle = self.gui.graphics_factory.build_disabled_bitmap(self._idle_handle)
        self.value = position

    def _on_disabled_changed(self, disabled: bool) -> None:
        """Keep interaction state and lock semantics in sync with disabled state."""
        if disabled:
            self._reset_drag()
            self.state = InteractiveState.Disabled
        else:
            self.state = InteractiveState.Idle

    def _build_track_bitmap(self) -> Surface:
        """Render transparent range bar with regularly spaced integer ticks."""
        bitmap = Surface((self.draw_rect.width, self.draw_rect.height), SRCALPHA)
        local_track = self._track_rect.move(-self.draw_rect.x, -self.draw_rect.y)
        half_handle = self._handle_size // 2
        if self._horizontal == Orientation.Horizontal:
            axis_start = local_track.left + half_handle
            axis_end = local_track.right - half_handle
            trimmed_width = max(1, axis_end - axis_start)
            trimmed_track = Rect(axis_start, local_track.top, trimmed_width, local_track.height)
        else:
            axis_start = local_track.top + half_handle
            axis_end = local_track.bottom - half_handle
            trimmed_height = max(1, axis_end - axis_start)
            trimmed_track = Rect(local_track.left, axis_start, local_track.width, trimmed_height)
        rect(bitmap, colours['medium'] + (255,), trimmed_track, 0)

        for point in self._notch_points():
            pixel_offset = self.total_to_pixel(point, self._total_range)
            if self._horizontal == Orientation.Horizontal:
                centre_x = (self._graphic_rect.x - self.draw_rect.x) + pixel_offset + (self._handle_size // 2)
                y1 = local_track.top - 2
                y2 = local_track.bottom + 2
                line(bitmap, colours['full'] + (200,), (centre_x, y1), (centre_x, y2), 1)
            else:
                centre_y = (self._graphic_rect.y - self.draw_rect.y) + pixel_offset + (self._handle_size // 2)
                x1 = local_track.left - 2
                x2 = local_track.right + 2
                line(bitmap, colours['full'] + (200,), (x1, centre_y), (x2, centre_y), 1)
        return bitmap

    def _notch_points(self) -> list[float]:
        """Return logical notch positions along the slider range."""
        if self._integer_type:
            return [float(index) for index in range(0, self._total_range + 1)]
        interval_units = (self._total_range * self._notch_interval_percent) / 100.0
        if interval_units <= 0.0:
            interval_units = 1.0
        tick_positions: list[float] = []
        tick = 0.0
        max_tick = float(self._total_range)
        while tick <= max_tick:
            tick_positions.append(tick)
            tick += interval_units
        if not tick_positions or tick_positions[-1] != max_tick:
            tick_positions.append(max_tick)
        return tick_positions

    def _handle_area(self) -> Rect:
        """Return current slider handle rect in window/screen coordinates."""
        pixel_point = self.total_to_pixel(self._position, self._total_range)
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x + pixel_point, self._graphic_rect.y, self._handle_size, self._handle_size)
        return Rect(self._graphic_rect.x, self._graphic_rect.y + pixel_point, self._handle_size, self._handle_size)

    def _topmost_window_at_mouse(self) -> Optional["Window"]:
        """Return the topmost visible window currently under the mouse position."""
        mouse_pos = self.gui.get_mouse_pos()
        for candidate in tuple(self.gui.windows)[::-1]:
            if not candidate.visible:
                continue
            if candidate.get_window_rect().collidepoint(mouse_pos):
                return candidate
        return None

    def _drag_blocked_by_overlay(self, owner_window: Optional["Window"]) -> bool:
        """Return True when drag enters a region occluded by another window."""
        topmost_window = self._topmost_window_at_mouse()
        if owner_window is None:
            return topmost_window is not None
        return topmost_window is not None and topmost_window is not owner_window

    def _cancel_drag_for_overlay_contact(self, owner_window: Optional["Window"]) -> bool:
        """Cancel drag when pointer enters an overlaid window region.

        Returning True allows the coordinator to emit a widget event or invoke
        on_activate callback, matching existing activation semantics.
        """
        if not self._dragging:
            return False
        if not self._drag_blocked_by_overlay(owner_window):
            return False
        self._reset_drag()
        self.state = InteractiveState.Idle
        return True

    def leave(self) -> None:
        """Reset hover state when focus leaves this widget."""
        if self._dragging:
            return
        if self.disabled:
            self.state = InteractiveState.Disabled
        else:
            self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle dragging interactions for slider handle movement."""
        if self.disabled:
            return False
        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
            return False
        if event.type in (MOUSEMOTION, MOUSEBUTTONUP):
            if self._cancel_drag_for_overlay_contact(window):
                return True

        mouse_point = self.gui.convert_to_window(self.gui.get_mouse_pos(), window)
        if event.type == MOUSEBUTTONDOWN:
            if getattr(event, 'button', None) != 1:
                return False
            handle_area = self._handle_area()
            if not handle_area.collidepoint(mouse_point):
                return False
            if self._horizontal == Orientation.Horizontal:
                self._drag_anchor_offset = mouse_point[0] - handle_area.x
                lock_x = self._graphic_rect.x + self._drag_anchor_offset
                lock_y = mouse_point[1]
                lock_w = self._graphic_rect.width + 1
                lock_h = 1
            else:
                self._drag_anchor_offset = mouse_point[1] - handle_area.y
                lock_x = mouse_point[0]
                lock_y = self._graphic_rect.y + self._drag_anchor_offset
                lock_w = 1
                lock_h = self._graphic_rect.height + 1
            screen_x, screen_y = self.gui.convert_to_screen((lock_x, lock_y), window)
            lock_rect = Rect(screen_x, screen_y, lock_w, lock_h)
            self.gui.set_lock_area(self, lock_rect)
            self._dragging = True
            self.state = InteractiveState.Armed
            return True

        if event.type == MOUSEMOTION:
            if not self._dragging:
                if self._handle_area().collidepoint(mouse_point):
                    self.state = InteractiveState.Hover
                else:
                    self.state = InteractiveState.Idle
                return False
            if self._horizontal == Orientation.Horizontal:
                axis_pixel = mouse_point[0] - self._graphic_rect.x - self._drag_anchor_offset
            else:
                axis_pixel = mouse_point[1] - self._graphic_rect.y - self._drag_anchor_offset
            self.value = self.pixel_to_total(axis_pixel, self._total_range)
            self.state = InteractiveState.Armed
            return True

        if getattr(event, 'button', None) != 1 or not self._dragging:
            return False
        self._reset_drag()
        if self._handle_area().collidepoint(mouse_point):
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
        """Draw slider track and handle in the current interaction state."""
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
