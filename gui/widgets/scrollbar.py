from pygame import Rect
from pygame.draw import rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..command import convert_to_window, convert_to_screen, add
from .frame import Frame, FrState
from .arrowbox import ArrowBox
from .widget import colours

class Scrollbar(Frame):
    def __init__(self, id, params, overall_rect, horizontal, style):
        # list of registered sub-widgets
        self.registered = []
        # parse the style
        if style == 0:
            # pass through with no arrowboxes
            scroll_area_rect = overall_rect
        else:
            # define rects for scrollbar and arrowboxes
            x, y, width, height = overall_rect
            if style == 1:
                if horizontal:
                    increment_rect = Rect(width - height, 0, height, height)
                    scrollbar_rect = Rect(height, 0, (width - height * 2), height)
                    decrement_rect = Rect(0, 0, height, height)
                else:
                    increment_rect = Rect(0, height - width, width, width)
                    scrollbar_rect = Rect(0, width, width, height - width * 2)
                    decrement_rect = Rect(0, 0, width, width)
            elif style == 2:
                if horizontal:
                    scrollbar_rect = Rect(0, 0, (width - height * 2), height)
                    decrement_rect = Rect(width - (height * 2), 0, height, height)
                    increment_rect = Rect(width - height, 0, height, height)
                else:
                    scrollbar_rect = Rect(0, 0, width, height - (width * 2))
                    decrement_rect = Rect(0, height - (width * 2), width, width)
                    increment_rect = Rect(0, height - width, width, width)
            elif style == 3:
                if horizontal:
                    decrement_rect = Rect(0, 0, height, height)
                    increment_rect = Rect(height, 0, height, height)
                    scrollbar_rect = Rect(height * 2, 0, width - (height * 2), height)
                else:
                    decrement_rect = Rect(0, 0, width, width)
                    increment_rect = Rect(0, width, width, width)
                    scrollbar_rect = Rect(0, width * 2, width, height - (width * 2))
            else:
                raise Exception(f'style {style} not implemented')
        # add arrowboxes
        if style != 0:
            x, y, width, height = overall_rect
            scroll_area_rect = Rect(x + scrollbar_rect.x, y + scrollbar_rect.y, scrollbar_rect.width, scrollbar_rect.height)
            inc_rect = Rect(x + increment_rect.x, y + increment_rect.y, increment_rect.width, increment_rect.height)
            dec_rect = Rect(x + decrement_rect.x, y + decrement_rect.y, decrement_rect.width, decrement_rect.height)
            if horizontal:
                inc_degree = 0
                dec_degree = 180
            else:
                inc_degree = 270
                dec_degree = 90
            self.registered.append(add(ArrowBox(f'{id}.increment', inc_rect, inc_degree, self.increment)))
            self.registered.append(add(ArrowBox(f'{id}.decrement', dec_rect, dec_degree, self.decrement)))
        # initialize common widget values
        super().__init__(id, scroll_area_rect)
        # get a reference to the gui
        self.gui = GuiManager()
        # maximum area that can be filled
        self.graphic_rect = Rect(self.rect.left + 4, self.rect.top + 4, self.rect.width - 8, self.rect.height - 8)
        # setup the parameters of the scrollbar
        total, start, size, inc = params
        self.set(total, start, size, inc)
        # whether the scrollbar is horizontal or vertical
        self.horizontal = horizontal
        # state to track if the scrollbar is currently dragging
        self.dragging = False
        # previous mouse position the last time the event was handled
        self.last_mouse_pos = None
        # whether or not the arrowboxes modified the start_pos
        self.hit = False

    def handle_event(self, event, window):
        if self.hit:
            # if the scrollbar state was modified by a callback then signal a change
            self.hit = False
            return True
        if event.type not in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
            # no matching events for scrollbar logic
            return False
        # do last object logic
        # manage the state of the scrollbar
        point = convert_to_window(self.gui.get_mouse_pos(), window)
        if (event.type == MOUSEBUTTONDOWN) and self.handle_area().collidepoint(point):
            if event.button == 1:
                # lock mouse movement to scrollbar area
                x, y = convert_to_screen((self.graphic_rect[0], self.graphic_rect[1]), window)
                lock_rect = Rect(x, y, self.graphic_rect.width, self.graphic_rect.height)
                self.gui.set_lock_area(self, lock_rect)
                # begin dragging the scrollbar
                self.state = FrState.Hover
                self.dragging = True
                # signal no change
                return False
        if (event.type == MOUSEMOTION) and self.dragging:
            x, y = convert_to_window(self.gui.get_mouse_pos(), window)
            # normalize x and y to graphic drawing area
            x, y = (x - self.graphic_rect.x, y - self.graphic_rect.y)
            # test bounds for dragging
            if self.horizontal:
                point = self.graphical_to_total(x)
            else:
                point = self.graphical_to_total(y)
            if point < 0:
                point = 0
                self.last_mouse_pos = 0
                return True
            elif point > self.total_range:
                self.start_pos = self.total_range - self.bar_size
                self.last_mouse_pos = self.total_range - self.bar_size
                return True
            if self.last_mouse_pos != None:
                # convert mouse position to total range units
                mouse_pos = point
                # find the difference in mouse movement between handle calls
                mouse_delta = mouse_pos - self.last_mouse_pos
                # calculate new position
                new_start_pos = self.start_pos + mouse_delta
                # limit position
                if new_start_pos < 0:
                    new_start_pos = 0
                if new_start_pos > self.total_range - self.bar_size:
                    new_start_pos = self.total_range - self.bar_size
                # store new positions
                self.start_pos = new_start_pos
                self.last_mouse_pos = mouse_pos
                # signal that there was a change
                return True
            else:
                # if there is no last mouse position make it this one
                self.last_mouse_pos = point
                # signal no change
                return False
        if (event.type == MOUSEBUTTONUP) and self.dragging:
            if event.button == 1:
                self.reset()
                # signal there was a change
                return True
        # signal no changes
        return False

    def leave(self):
        self.reset()

    def reset(self):
        # unlock mouse movement
        self.gui.set_lock_area(None)
        # reset state to default values
        self.state = FrState.Idle
        self.hit = False
        self.dragging = False
        self.last_mouse_pos = None

    def read(self):
        # return scrollbar start position
        return self.start_pos

    def set(self, total_range, start_pos, bar_size, inc_size):
        # set scrollbar data, all variables are in total units
        self.total_range, self.start_pos, self.bar_size, self.inc_size = total_range, start_pos, bar_size, inc_size

    def handle_area(self):
        # calculate where the start point is and what the size is in graphical units
        start_point = self.total_to_graphical(self.start_pos)
        graphical_size = self.total_to_graphical(self.bar_size)
        # define a rectangle for the filled area
        if self.horizontal:
            return Rect(self.graphic_rect.x + start_point, self.graphic_rect.y, graphical_size, self.graphic_rect.height)
        else:
            return Rect(self.graphic_rect.x, self.graphic_rect.y + start_point, self.graphic_rect.width, graphical_size)

    def graphical_to_total(self, point):
        return int((point * self.total_range) / self.graphical_range())

    def total_to_graphical(self, point):
        return int((point * self.graphical_range()) / self.total_range)

    def graphical_range(self):
        # return the appropriate range depending on whether the scrollbar is horizontal or vertical
        if self.horizontal:
            return self.graphic_rect.width
        else:
            return self.graphic_rect.height

    def draw(self):
        # draw the frame
        super().draw()
        # fill graphical area to represent the start position and size
        rect(self.surface, colours['full'], self.handle_area(), 0)

    def set_visible(self, visible):
        # call the parent set_visible, up to widget
        super().set_visible(visible)
        # for each attached arrowbox also do their setting
        for widget in self.registered:
            widget.set_visible(visible)

    # callbacks
    def increment(self):
        self.hit = True
        self.start_pos += self.inc_size
        if self.start_pos + self.bar_size > self.total_range:
            self.start_pos = self.total_range - self.bar_size

    def decrement(self):
        self.hit = True
        self.start_pos -= self.inc_size
        if self.start_pos < 0:
            self.start_pos = 0
