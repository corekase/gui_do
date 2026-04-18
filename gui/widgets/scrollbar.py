from __future__ import annotations

from pygame.event import Event as PygameEvent
from typing import List, Optional, Tuple, TYPE_CHECKING
from pygame import Rect
from pygame.draw import rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP
from .arrowbox import ArrowBox
from .frame import Frame
from ..utility.intermediates.axis_range import AxisRangeMixin
from ..utility.intermediates.widget import Widget
from ..utility.events import colours, GuiError, Orientation, ArrowPosition, InteractiveState

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window

class Scrollbar(Frame, AxisRangeMixin):
    """Draggable range selector with optional increment/decrement arrow boxes."""

    @property
    def start_pos(self) -> int:
        """Return current start position in total-range units."""
        return self._start_pos

    @property
    def visible(self) -> bool:
        """Visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Visible."""
        if not isinstance(value, bool):
            raise GuiError('widget visible must be a bool')
        self._visible = value
        for widget in self._registered:
            widget.visible = value

    @Widget.position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        """Position."""
        old_x, old_y = self.draw_rect.x, self.draw_rect.y
        Widget.position.fset(self, pos)
        delta_x = self.draw_rect.x - old_x
        delta_y = self.draw_rect.y - old_y
        if delta_x == 0 and delta_y == 0:
            return
        self._overall_rect.move_ip(delta_x, delta_y)
        self._graphic_rect.move_ip(delta_x, delta_y)
        if self._increment_rect is not None:
            self._increment_rect.move_ip(delta_x, delta_y)
        if self._decrement_rect is not None:
            self._decrement_rect.move_ip(delta_x, delta_y)
        for arrow in self._registered:
            arrow.position = (arrow.draw_rect.x + delta_x, arrow.draw_rect.y + delta_y)

    @Widget.disabled.setter
    def disabled(self, value: bool) -> None:
        """Disabled."""
        Widget.disabled.fset(self, value)
        for widget in self._registered:
            widget.disabled = value
        if value:
            self._reset()

    def __init__(self, gui: "GuiManager", id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> None:
        """Create Scrollbar."""
        self._registered: List[ArrowBox] = []
        self._subwidgets_bound: bool = False
        self._style: ArrowPosition = style
        self._set_orientation(horizontal)
        self._overall_rect: Rect = Rect(overall_rect)
        self._increment_rect: Optional[Rect] = None
        self._decrement_rect: Optional[Rect] = None
        self._inc_degree: Optional[float] = None
        self._dec_degree: Optional[float] = None
        if style == ArrowPosition.Skip:
            scroll_area_rect = overall_rect
        else:
            x, y, width, height = overall_rect
            if style == ArrowPosition.Split:
                if horizontal == Orientation.Horizontal:
                    increment_rect = Rect(width - height, 0, height, height)
                    scrollbar_rect = Rect(height, 0, (width - height * 2), height)
                    decrement_rect = Rect(0, 0, height, height)
                else:
                    increment_rect = Rect(0, height - width, width, width)
                    scrollbar_rect = Rect(0, width, width, height - width * 2)
                    decrement_rect = Rect(0, 0, width, width)
            elif style == ArrowPosition.Near:
                if horizontal == Orientation.Horizontal:
                    decrement_rect = Rect(0, 0, height, height)
                    increment_rect = Rect(height, 0, height, height)
                    scrollbar_rect = Rect(height * 2, 0, width - (height * 2), height)
                else:
                    decrement_rect = Rect(0, 0, width, width)
                    increment_rect = Rect(0, width, width, width)
                    scrollbar_rect = Rect(0, width * 2, width, height - (width * 2))
            elif style == ArrowPosition.Far:
                if horizontal == Orientation.Horizontal:
                    scrollbar_rect = Rect(0, 0, (width - height * 2), height)
                    decrement_rect = Rect(width - (height * 2), 0, height, height)
                    increment_rect = Rect(width - height, 0, height, height)
                else:
                    scrollbar_rect = Rect(0, 0, width, height - (width * 2))
                    decrement_rect = Rect(0, height - (width * 2), width, width)
                    increment_rect = Rect(0, height - width, width, width)
            else:
                raise GuiError('style not implemented')
        # Arrow widgets are created after this scrollbar is added to its container.
        if style != ArrowPosition.Skip:
            x, y, width, height = overall_rect
            scroll_area_rect = Rect(x + scrollbar_rect.x, y + scrollbar_rect.y, scrollbar_rect.width, scrollbar_rect.height)
            inc_rect = Rect(x + increment_rect.x, y + increment_rect.y, increment_rect.width, increment_rect.height)
            dec_rect = Rect(x + decrement_rect.x, y + decrement_rect.y, decrement_rect.width, decrement_rect.height)
            if horizontal == Orientation.Horizontal:
                inc_degree = 0
                dec_degree = 180
            else:
                inc_degree = 270
                dec_degree = 90
            self._increment_rect = inc_rect
            self._decrement_rect = dec_rect
            self._inc_degree = inc_degree
            self._dec_degree = dec_degree
        else:
            scroll_area_rect = overall_rect
        self._total_range: int = 0
        self._start_pos: int = 0
        self._bar_size: int = 0
        self._inc_size: int = 0
        super().__init__(gui, id, scroll_area_rect)
        self._graphic_rect: Rect = Rect(self.draw_rect.left + 4, self.draw_rect.top + 4, self.draw_rect.width - 8, self.draw_rect.height - 8)
        total, start, size, inc = params
        self.set(total, start, size, inc)
        self._set_orientation(horizontal)
        self._dragging: bool = False
        self._last_mouse_pos: Optional[int] = None
        self._hit: bool = False

    def leave(self) -> None:
        """Leave."""
        self._reset()

    def set(self, total_range: int, start_pos: int, bar_size: int, inc_size: int) -> None:
        """Set total range, start, visible size, and increment in logical units."""
        if total_range <= 0:
            raise GuiError(f'total_range must be > 0, got {total_range}')
        if bar_size <= 0 or bar_size > total_range:
            raise GuiError(f'bar_size must be in 1..{total_range}, got {bar_size}')
        if start_pos < 0 or start_pos > (total_range - bar_size):
            raise GuiError(f'start_pos must be in 0..{total_range - bar_size}, got {start_pos}')
        if inc_size <= 0:
            raise GuiError(f'inc_size must be > 0, got {inc_size}')
        self._total_range, self._start_pos, self._bar_size, self._inc_size = total_range, start_pos, bar_size, inc_size

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle event."""
        if self.disabled:
            return False
        if event.type in (MOUSEMOTION, MOUSEBUTTONUP):
            if self._cancel_drag_for_overlay_contact(window):
                return True
        if self._hit:
            self._hit = False
            return True
        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
            return False
        point = self.gui.convert_to_window(self.gui.get_mouse_pos(), window)
        if (event.type == MOUSEBUTTONDOWN) and self._handle_area().collidepoint(point):
            if getattr(event, 'button', None) == 1:
                x, y = self.gui.convert_to_screen((self._graphic_rect[0], self._graphic_rect[1]), window)
                lock_rect = Rect(x, y, self._graphic_rect.width, self._graphic_rect.height)
                self.gui.set_lock_area(self, lock_rect)
                self.state = InteractiveState.Hover
                self._dragging = True
                return False
        if (event.type == MOUSEMOTION) and self._dragging:
            x, y = self.gui.convert_to_window(self.gui.get_mouse_pos(), window)
            x, y = (x - self._graphic_rect.x, y - self._graphic_rect.y)
            if self._horizontal == Orientation.Horizontal:
                point = self._graphical_to_total(x)
            else:
                point = self._graphical_to_total(y)
            if point < 0:
                point = 0
                self._start_pos = 0
                self._last_mouse_pos = 0
                return True
            elif point > self._total_range:
                self._start_pos = self._total_range - self._bar_size
                self._last_mouse_pos = self._total_range - self._bar_size
                return True
            if self._last_mouse_pos is not None:
                mouse_pos = point
                mouse_delta = mouse_pos - self._last_mouse_pos
                new_start_pos = self._start_pos + mouse_delta
                if new_start_pos < 0:
                    new_start_pos = 0
                if new_start_pos > self._total_range - self._bar_size:
                    new_start_pos = self._total_range - self._bar_size
                self._start_pos = new_start_pos
                self._last_mouse_pos = mouse_pos
                return True
            else:
                self._last_mouse_pos = point
                return False
        if (event.type == MOUSEBUTTONUP) and self._dragging:
            if getattr(event, 'button', None) == 1:
                self._reset()
                return True
        return False

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
        self._reset()
        return True

    def draw(self) -> None:
        """Draw."""
        super().draw()
        handle_colour = colours['full']
        if self.disabled:
            handle_colour = tuple(max(0, int(channel * 0.75)) for channel in colours['full'])
        rect(self.surface, handle_colour, self._handle_area(), 0)

    def decrement(self) -> None:
        """Decrement."""
        self._hit = True
        self._start_pos -= self._inc_size
        if self._start_pos < 0:
            self._start_pos = 0
    def increment(self) -> None:
        """Increment."""
        self._hit = True
        self._start_pos += self._inc_size
        if self._start_pos + self._bar_size > self._total_range:
            self._start_pos = self._total_range - self._bar_size

    def _handle_area(self) -> Rect:
        """Handle area."""
        start_point = self._total_to_graphical(self._start_pos)
        graphical_size = self._total_to_graphical(self._bar_size)
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x + start_point, self._graphic_rect.y, graphical_size, self._graphic_rect.height)
        else:
            return Rect(self._graphic_rect.x, self._graphic_rect.y + start_point, self._graphic_rect.width, graphical_size)

    def _graphical_range(self) -> int:
        """Graphical range."""
        return AxisRangeMixin._graphical_range(self)

    def _graphical_to_total(self, point: int) -> int:
        """Graphical to total."""
        return int(self.pixel_to_total(point, self._total_range))

    def _on_added_to_gui(self) -> None:
        """On added to gui."""
        if self._subwidgets_bound or self._style == ArrowPosition.Skip:
            return
        if self._increment_rect is None or self._decrement_rect is None:
            raise GuiError('scrollbar arrow geometry is not initialized')
        if self._inc_degree is None or self._dec_degree is None:
            raise GuiError('scrollbar arrow direction is not initialized')
        created: List[ArrowBox] = []
        try:
            inc_arrow = self.gui.arrow_box(f'{self.id}.increment', self._increment_rect, self._inc_degree, self.increment)
            created.append(inc_arrow)
            dec_arrow = self.gui.arrow_box(f'{self.id}.decrement', self._decrement_rect, self._dec_degree, self.decrement)
            created.append(dec_arrow)
            self._registered.extend(created)
            self._subwidgets_bound = True
        except Exception:
            for arrow in created:
                if arrow in self.gui.widgets:
                    self.gui.widgets.remove(arrow)
                for window in self.gui.windows:
                    if arrow in window.widgets:
                        window.widgets.remove(arrow)
            raise

    def _reset(self) -> None:
        """Reset."""
        self.gui.set_lock_area(None)
        self.state = InteractiveState.Idle
        self._hit = False
        self._dragging = False
        self._last_mouse_pos = None

    def _total_to_graphical(self, point: int) -> int:
        """Total to graphical."""
        return self.total_to_pixel(point, self._total_range)
