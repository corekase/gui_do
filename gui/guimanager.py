from .utility import copy_graphic, load_font, set_font
from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from pygame import Rect

class GuiManager:
    def __init__(self, surface):
        # surface to draw the widget to
        self.surface = surface
        # load fonts for utility functions
        load_font('label', 'Ubuntu-Medium.ttf', 10)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 12)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('bigger', 'Ubuntu-Medium.ttf', 18)
        load_font('biggest', 'Ubuntu-Medium.ttf', 36)
        # set default font
        set_font('normal')
        # widgets to be managed: key:value -> group_name:list_of_widgets
        self.widgets = []
        # which key group to use
        self.group = None
        # list of bitmaps overwritten by gui objects
        self.bitmaps = []
        # active window
        self.window = None
        # list of windows to process
        self.windows = []
        # dragging window
        self.dragging = None
        self.dragging_window = None
        self.saved_graphic = None
        # set the default group to the screen
        self.set_group()

    def set_group(self, window=None):
        # set which key group is active
        self.window = window

    def save_graphic(self, window):
        rec = Rect(window.x, window.y - 20, window.width, window.height + 20)
        self.saved_graphic = (copy_graphic(self.surface, rec), rec)

    def restore_graphic(self):
        self.surface.blit(self.saved_graphic[0], self.saved_graphic[1])

    def handle_event(self, event):
        # handle window dragging
        if event.type == MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            self.restore_graphic()
        elif event.type == MOUSEMOTION and self.dragging:
            xdif, ydif = event.rel
            self.restore_graphic()
            self.dragging_window.set_pos((self.dragging_window.x + xdif, self.dragging_window.y + ydif))
            self.save_graphic(self.dragging_window)
        elif event.type == MOUSEBUTTONDOWN and not self.dragging:
            for window in self.windows:
                if window.title_bar_rect.collidepoint(event.pos):
                    if event.button == 1:
                        self.dragging = True
                        self.dragging_window = window
                        self.save_graphic(window)
        # if a widget signals that it had an action return the widget id
        for window in self.windows:
            for widget in window.widgets:
                # test widget activation
                if widget.handle_event(event, window):
                    # widget activated, return its id
                    return widget.id
        for widget in self.widgets:
            # test widget activation
            if widget.handle_event(event, None):
                # widget activated, return its id
                return widget.id
        # no widget activated to this event
        return None

    def draw_gui(self):
        # -> To-do: gui handles the cursor, and because of that knows which window it is over for events
        #           gui draws and undraws cursor, and tracks its location internally
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        for widget in self.widgets:
            # tuple of the bitmap and its rect, after loop ends in reverse order
            self.bitmaps.insert(0, (copy_graphic(self.surface, widget.rect), widget.rect))
            # draw the widget
            widget.draw()
        for window in self.windows:
            window_rect = Rect(window.x, window.y - 20, window.width, window.height + 20)
            self.bitmaps.insert(0, (copy_graphic(self.surface, window_rect), window_rect))
            window.draw_title_bar()
            for widget in window.widgets:
                # draw the widget
                widget.draw()
            self.surface.blit(window.surface, (window.x, window.y))

    def undraw_gui(self):
        # reverse the bitmaps that were under each gui object drawn
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)

    def add_window(self, window):
        self.windows.append(window)

    def get_window(self, name):
        pass

    def add_widget(self, widget):
        if self.window != None:
            widget.surface = self.window.surface
            # append the widget to the context
            self.window.widgets.append(widget)
        else:
            # add a widget to the manager
            widget.surface = self.surface
            # append the widget to the group
            self.widgets.append(widget)
