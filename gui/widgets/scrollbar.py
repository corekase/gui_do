from pygame.event import Event as PygameEvent
from typing import List, Optional, Tuple, TYPE_CHECKING
from pygame import Rect
from pygame.draw import rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP
from .arrowbox import ArrowBox
from .frame import Frame
from ..utility.constants import colours, WidgetKind, Orientation, ArrowPosition, InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Scrollbar(Frame):
    def __init__(self, gui: "GuiManager", id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> None:
        # list of registered sub-widgets
        self._registered: List[ArrowBox] = []
        # parse the style
        if style == ArrowPosition.Skip:
            # pass through with no arrowboxes
            scroll_area_rect = overall_rect
        else:
            # define rects for scrollbar and arrowboxes
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
                from ..utility.guimanager import GuiError
                raise GuiError('style not implemented')
        # add arrowboxes
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
            inc_arrow = gui.arrowbox(f'{id}.increment', inc_rect, inc_degree, self.increment)
            dec_arrow = gui.arrowbox(f'{id}.decrement', dec_rect, dec_degree, self.decrement)
            # Store arrows for later - window context will be set after super().__init__()
            self._registered.append(inc_arrow)
            self._registered.append(dec_arrow)
        else:
            scroll_area_rect = overall_rect
        # Scrollbar range parameters
        self._total_range: int = 0
        self._start_pos: int = 0
        self._bar_size: int = 0
        self._inc_size: int = 0
        # initialize common widget values
        super().__init__(gui, id, scroll_area_rect)
        self.WidgetKind = WidgetKind.Scrollbar
        # Ensure arrows inherit window context from scrollbar when in a window
        if self.window is not None:
            for arrow in self._registered:
                arrow.window = self.window
        # maximum area that can be filled
        self._graphic_rect: Rect = Rect(self.draw_rect.left + 4, self.draw_rect.top + 4, self.draw_rect.width - 8, self.draw_rect.height - 8)
        # setup the parameters of the scrollbar
        total, start, size, inc = params
        self.set(total, start, size, inc)
        # whether the scrollbar is horizontal or vertical
        self._horizontal: Orientation = horizontal
        # state to track if the scrollbar is currently dragging
        self._dragging: bool = False
        # previous mouse position the last time the event was handled
        self._last_mouse_pos: Optional[int] = None
        # whether or not the arrowboxes modified the start_pos
        self._hit: bool = False

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        if self._hit:
            # if the scrollbar state was modified by a callback then signal a change
            self._hit = False
            return True
        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
            # no matching events for scrollbar logic
            return False
        # do last object logic
        # manage the state of the scrollbar
        point = self.gui.convert_to_window(self.gui.get_mouse_pos(), window)
        if (event.type == MOUSEBUTTONDOWN) and self._handle_area().collidepoint(point):
            if event.button == 1:
                # lock mouse movement to scrollbar area
                x, y = self.gui.convert_to_screen((self._graphic_rect[0], self._graphic_rect[1]), window)
                lock_rect = Rect(x, y, self._graphic_rect.width, self._graphic_rect.height)
                self.gui.set_lock_area(self, lock_rect)
                # begin dragging the scrollbar
                self.state = InteractiveState.Hover
                self._dragging = True
                # signal no change
                return False
        if (event.type == MOUSEMOTION) and self._dragging:
            x, y = self.gui.convert_to_window(self.gui.get_mouse_pos(), window)
            # normalize x and y to graphic drawing area
            x, y = (x - self._graphic_rect.x, y - self._graphic_rect.y)
            # test bounds for dragging
            if self._horizontal == Orientation.Horizontal:
                point = self._graphical_to_total(x)
            else:
                point = self._graphical_to_total(y)
            if point < 0:
                point = 0
                self._last_mouse_pos = 0
                return True
            elif point > self._total_range:
                self._start_pos = self._total_range - self._bar_size
                self._last_mouse_pos = self._total_range - self._bar_size
                return True
            if self._last_mouse_pos is not None:
                # convert mouse position to total range units
                mouse_pos = point
                # find the difference in mouse movement between handle calls
                mouse_delta = mouse_pos - self._last_mouse_pos
                # calculate new position
                new_start_pos = self._start_pos + mouse_delta
                # limit position
                if new_start_pos < 0:
                    new_start_pos = 0
                if new_start_pos > self._total_range - self._bar_size:
                    new_start_pos = self._total_range - self._bar_size
                # store new positions
                self._start_pos = new_start_pos
                self._last_mouse_pos = mouse_pos
                # signal that there was a change
                return True
            else:
                # if there is no last mouse position make it this one
                self._last_mouse_pos = point
                # signal no change
                return False
        if (event.type == MOUSEBUTTONUP) and self._dragging:
            if event.button == 1:
                self._reset()
                # signal there was a change
                return True
        # signal no changes
        return False

    def leave(self) -> None:
        self._reset()

    def _reset(self) -> None:
        # unlock mouse movement
        self.gui.set_lock_area(None)
        # reset state to default values
        self.state = InteractiveState.Idle
        self._hit = False
        self._dragging = False
        self._last_mouse_pos = None

    def read(self) -> int:
        # return scrollbar start position
        return self._start_pos

    def set(self, total_range: int, start_pos: int, bar_size: int, inc_size: int) -> None:
        # set scrollbar data, all variables are in total units
        from ..utility.guimanager import GuiError
        if total_range <= 0:
            raise GuiError(f'total_range must be > 0, got {total_range}')
        if bar_size <= 0 or bar_size > total_range:
            raise GuiError(f'bar_size must be in 1..{total_range}, got {bar_size}')
        if start_pos < 0 or start_pos > (total_range - bar_size):
            raise GuiError(f'start_pos must be in 0..{total_range - bar_size}, got {start_pos}')
        if inc_size <= 0:
            raise GuiError(f'inc_size must be > 0, got {inc_size}')
        self._total_range, self._start_pos, self._bar_size, self._inc_size = total_range, start_pos, bar_size, inc_size

    def _handle_area(self) -> Rect:
        # calculate where the start point is and what the size is in graphical units
        start_point = self._total_to_graphical(self._start_pos)
        graphical_size = self._total_to_graphical(self._bar_size)
        # define a rectangle for the filled area
        if self._horizontal == Orientation.Horizontal:
            return Rect(self._graphic_rect.x + start_point, self._graphic_rect.y, graphical_size, self._graphic_rect.height)
        else:
            return Rect(self._graphic_rect.x, self._graphic_rect.y + start_point, self._graphic_rect.width, graphical_size)

    def _graphical_to_total(self, point: int) -> int:
        graphical = self._graphical_range()
        if graphical <= 0:
            return 0
        return int((point * self._total_range) / graphical)

    def _total_to_graphical(self, point: int) -> int:
        if self._total_range <= 0:
            return 0
        return int((point * self._graphical_range()) / self._total_range)

    def _graphical_range(self) -> int:
        # return the appropriate range depending on whether the scrollbar is horizontal or vertical
        if self._horizontal == Orientation.Horizontal:
            return self._graphic_rect.width
        else:
            return self._graphic_rect.height

    def draw(self) -> None:
        # draw the frame
        super().draw()
        # fill graphical area to represent the start position and size
        rect(self.surface, colours['full'], self._handle_area(), 0)

    def set_visible(self, visible: bool) -> None:
        # Scrollbar and its arrow widgets share visibility state.
        self.visible = visible
        # for each attached arrowbox also do their setting
        for widget in self._registered:
            widget.visible = visible

    # callbacks
    def increment(self) -> None:
        self._hit = True
        self._start_pos += self._inc_size
        if self._start_pos + self._bar_size > self._total_range:
            self._start_pos = self._total_range - self._bar_size

    def decrement(self) -> None:
        self._hit = True
        self._start_pos -= self._inc_size
        if self._start_pos < 0:
            self._start_pos = 0
