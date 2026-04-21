from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING

from pygame import Rect
from pygame.draw import rect
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL

from .arrowbox import ArrowBox
from .frame import Frame
from ..utility.events import ArrowPosition, GuiError, InteractiveState, Orientation, colours
from ..utility.input.normalized_event import normalize_input_event
from ..utility.input.overlay_drag_guard import cancel_drag_for_overlay_contact
from ..utility.intermediates.axis_range import AxisRangeMixin
from ..utility.intermediates.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window


@dataclass(frozen=True)
class _ScrollbarStyleLayout:
    scroll_area_rect: Rect
    increment_rect: Optional[Rect]
    decrement_rect: Optional[Rect]
    increment_degree: Optional[float]
    decrement_degree: Optional[float]


class Scrollbar(Frame, AxisRangeMixin):
    """Draggable scrollbar with optional arrow controls and wheel support."""

    @property
    def start_pos(self) -> int:
        """Current logical start position."""
        return self._start_pos

    @property
    def visible(self) -> bool:
        """Visible state for the bar and its optional arrow controls."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Toggle visibility for this bar and bound arrow controls."""
        if not isinstance(value, bool):
            raise GuiError('widget visible must be a bool')
        self._visible = value
        for widget in self._registered:
            widget.visible = value

    @Widget.position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        """Move bar and any bound arrow controls while preserving geometry."""
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
        """Toggle disabled state and mirror to bound arrows."""
        Widget.disabled.fset(self, value)
        for widget in self._registered:
            widget.disabled = value
        if value:
            self._reset()

    def __init__(
        self,
        gui: "GuiManager",
        id: str,
        overall_rect: Rect,
        horizontal: Orientation,
        style: ArrowPosition,
        total_range: int,
        start_pos: int,
        bar_size: int,
        inc_size: int,
        wheel_positive_to_max: bool = False,
    ) -> None:
        """Create Scrollbar."""
        if not isinstance(wheel_positive_to_max, bool):
            raise GuiError(f'wheel_positive_to_max must be a bool, got: {wheel_positive_to_max}')

        self._set_orientation(horizontal)
        if not isinstance(style, ArrowPosition):
            raise GuiError('style not implemented')

        self._registered: List[ArrowBox] = []
        self._subwidgets_bound: bool = False
        self._wheel_positive_to_max: bool = wheel_positive_to_max
        self._style: ArrowPosition = style
        self._overall_rect: Rect = Rect(overall_rect)

        style_layout = self._build_style_layout(self._overall_rect, self._horizontal, style)
        self._increment_rect = style_layout.increment_rect
        self._decrement_rect = style_layout.decrement_rect
        self._inc_degree = style_layout.increment_degree
        self._dec_degree = style_layout.decrement_degree

        self._total_range: int = 0
        self._start_pos: int = 0
        self._bar_size: int = 0
        self._inc_size: int = 0

        super().__init__(gui, id, style_layout.scroll_area_rect)
        self._graphic_rect = Rect(self.draw_rect.left + 4, self.draw_rect.top + 4, self.draw_rect.width - 8, self.draw_rect.height - 8)

        self._dragging: bool = False
        self._hit: bool = False
        self._drag_anchor_offset: int = 0

        self.set(total_range, start_pos, bar_size, inc_size)

    def _build_style_layout(self, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition) -> _ScrollbarStyleLayout:
        """Compute the bar area and optional arrow geometry for the selected style."""
        x, y, width, height = overall_rect
        if style == ArrowPosition.Skip:
            return _ScrollbarStyleLayout(overall_rect, None, None, None, None)

        if style == ArrowPosition.Split:
            if horizontal == Orientation.Horizontal:
                inc = Rect(width - height, 0, height, height)
                bar = Rect(height, 0, width - (height * 2), height)
                dec = Rect(0, 0, height, height)
            else:
                inc = Rect(0, height - width, width, width)
                bar = Rect(0, width, width, height - (width * 2))
                dec = Rect(0, 0, width, width)
        elif style == ArrowPosition.Near:
            if horizontal == Orientation.Horizontal:
                dec = Rect(0, 0, height, height)
                inc = Rect(height, 0, height, height)
                bar = Rect(height * 2, 0, width - (height * 2), height)
            else:
                dec = Rect(0, 0, width, width)
                inc = Rect(0, width, width, width)
                bar = Rect(0, width * 2, width, height - (width * 2))
        elif style == ArrowPosition.Far:
            if horizontal == Orientation.Horizontal:
                bar = Rect(0, 0, width - (height * 2), height)
                dec = Rect(width - (height * 2), 0, height, height)
                inc = Rect(width - height, 0, height, height)
            else:
                bar = Rect(0, 0, width, height - (width * 2))
                dec = Rect(0, height - (width * 2), width, width)
                inc = Rect(0, height - width, width, width)
        else:
            raise GuiError('style not implemented')

        scroll_area = Rect(x + bar.x, y + bar.y, bar.width, bar.height)
        increment_rect = Rect(x + inc.x, y + inc.y, inc.width, inc.height)
        decrement_rect = Rect(x + dec.x, y + dec.y, dec.width, dec.height)

        if horizontal == Orientation.Horizontal:
            inc_degree = 0
            dec_degree = 180
        else:
            inc_degree = 270
            dec_degree = 90

        return _ScrollbarStyleLayout(scroll_area, increment_rect, decrement_rect, inc_degree, dec_degree)

    def leave(self) -> None:
        """Reset transient drag state when focus leaves this control."""
        self._reset()

    def set(self, total_range: int, start_pos: int, bar_size: int, inc_size: int) -> None:
        """Set logical total range, start offset, visible window size, and step size."""
        if total_range <= 0:
            raise GuiError(f'total_range must be > 0, got {total_range}')
        if bar_size <= 0 or bar_size > total_range:
            raise GuiError(f'bar_size must be in 1..{total_range}, got {bar_size}')
        if start_pos < 0 or start_pos > (total_range - bar_size):
            raise GuiError(f'start_pos must be in 0..{total_range - bar_size}, got {start_pos}')
        if inc_size <= 0:
            raise GuiError(f'inc_size must be > 0, got {inc_size}')
        self._total_range = total_range
        self._start_pos = start_pos
        self._bar_size = bar_size
        self._inc_size = inc_size

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle drag and wheel interactions for the logical start position."""
        if self.disabled:
            return False

        normalized = normalize_input_event(event)

        if event.type in (MOUSEMOTION, MOUSEBUTTONUP):
            if cancel_drag_for_overlay_contact(self.gui, self._dragging, window, self._reset):
                return True

        if self._hit:
            self._hit = False
            return True

        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP, MOUSEWHEEL):
            return False

        if event.type == MOUSEWHEEL:
            if self._dragging or not self.get_collide(window):
                return False
            wheel_delta = normalized.wheel_delta
            if wheel_delta == 0:
                return False
            direction = 1 if wheel_delta > 0 else -1
            if not self._wheel_positive_to_max:
                direction *= -1
            self._start_pos += direction * abs(wheel_delta) * self._inc_size
            self._start_pos = self._clamp_start(self._start_pos)
            self.state = InteractiveState.Hover
            return True

        point = self.gui._convert_to_window(self.gui._get_mouse_pos(), window)

        if event.type == MOUSEBUTTONDOWN and self._handle_area().collidepoint(point):
            if normalized.is_left_down:
                handle_rect = self._handle_area()
                if self._horizontal == Orientation.Horizontal:
                    self._drag_anchor_offset = point[0] - handle_rect.x
                    lock_x = self._graphic_rect.x + self._drag_anchor_offset
                    lock_y = point[1]
                    lock_w = self._graphic_rect.width + 1
                    lock_h = 1
                else:
                    self._drag_anchor_offset = point[1] - handle_rect.y
                    lock_x = point[0]
                    lock_y = self._graphic_rect.y + self._drag_anchor_offset
                    lock_w = 1
                    lock_h = self._graphic_rect.height + 1
                lock_x, lock_y = self.gui._convert_to_screen((lock_x, lock_y), window)
                self.gui.set_lock_area(self, Rect(lock_x, lock_y, lock_w, lock_h))
                self.state = InteractiveState.Hover
                self._dragging = True
                return False

        if event.type == MOUSEMOTION and self._dragging:
            local_x, local_y = self.gui._convert_to_window(self.gui._get_mouse_pos(), window)
            local_x -= self._graphic_rect.x
            local_y -= self._graphic_rect.y
            anchor_offset = getattr(self, '_drag_anchor_offset', 0)
            if self._horizontal == Orientation.Horizontal:
                axis_pixel = local_x - anchor_offset
            else:
                axis_pixel = local_y - anchor_offset
            self._start_pos = self._clamp_start(self._graphical_to_total(axis_pixel))
            return True

        if event.type == MOUSEBUTTONUP and self._dragging:
            if not normalized.is_left_up:
                return False
            self._reset()
            return True

        return False

    def draw(self) -> None:
        """Draw the frame and moving bar handle."""
        super().draw()
        handle_colour = colours['full']
        if self.disabled:
            handle_colour = tuple(max(0, int(channel * 0.75)) for channel in colours['full'])
        rect(self.surface, handle_colour, self._handle_area(), 0)

    def decrement(self) -> None:
        """Move the logical start position backward by one increment."""
        self._hit = True
        self._start_pos = self._clamp_start(self._start_pos - self._inc_size)

    def increment(self) -> None:
        """Move the logical start position forward by one increment."""
        self._hit = True
        self._start_pos = self._clamp_start(self._start_pos + self._inc_size)

    def _clamp_start(self, value: int) -> int:
        """Clamp start position into valid scrollbar bounds."""
        maximum = self._total_range - self._bar_size
        if value < 0:
            return 0
        if value > maximum:
            return maximum
        return value

    def _handle_area(self) -> Rect:
        """Return current draggable bar handle area."""
        start_point = self._total_to_graphical(self._start_pos)
        graphical_size = self._total_to_graphical(self._bar_size)
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x + start_point, self._graphic_rect.y, graphical_size, self._graphic_rect.height)
        return Rect(self._graphic_rect.x, self._graphic_rect.y + start_point, self._graphic_rect.width, graphical_size)

    def _graphical_range(self) -> int:
        """Return axis-aligned graphic travel range."""
        return AxisRangeMixin._graphical_range(self)

    def _graphical_to_total(self, point: int) -> int:
        """Convert graphic axis point to logical range units."""
        return int(self.pixel_to_total(point, self._total_range))

    def _total_to_graphical(self, point: int) -> int:
        """Convert logical range units to graphic axis point."""
        return self.total_to_pixel(point, self._total_range)

    def on_added_to_gui(self) -> None:
        """Create arrow controls after registration, with rollback on failure."""
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
                for win in self.gui.windows:
                    if arrow in win.widgets:
                        win.widgets.remove(arrow)
            raise

    def _reset(self) -> None:
        """Clear transient drag/lock state."""
        self.gui.set_lock_area(None)
        self.state = InteractiveState.Idle
        self._hit = False
        self._dragging = False
        self._drag_anchor_offset = 0
