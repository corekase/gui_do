from .utility import cut, load_font, set_font
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
        self.widgets = {}
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
        self.old_graphic = None
        # set the default group to the screen
        self.set_group('screen')

    def set_group(self, group, window=None):
        # set which key group is active
        self.group = group
        self.window = window

    def cut_old(self, window):
        rec = Rect(window.x, window.y - 20, window.width, window.height + 20)
        self.old_graphic = (cut(self.surface, rec), rec)

    def handle_event(self, event):
        # handle window dragging
        if event.type == MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            self.surface.blit(self.old_graphic[0], self.old_graphic[1])
        elif event.type == MOUSEMOTION and self.dragging:
            xdif, ydif = event.rel
            self.surface.blit(self.old_graphic[0], self.old_graphic[1])
            self.dragging_window.set_pos((self.dragging_window.x + xdif, self.dragging_window.y + ydif))
            self.cut_old(self.dragging_window)
        elif event.type == MOUSEBUTTONDOWN and not self.dragging:
            for window in self.windows:
                if window.title_bar_rect.collidepoint(event.pos):
                    if event.button == 1:
                        self.dragging = True
                        self.dragging_window = window
                        self.cut_old(window)
        # if a widget signals that it had an action return the widget id
        if len(self.windows) > 0:
            for window in self.windows:
                widgets = window.widgets.get('window', [])
                for widget in widgets:
                    # test widget activation
                    if widget.handle_event(event, window):
                        # widget activated, return its id
                        return widget.id
        widgets = self.widgets['screen']
        for widget in widgets:
            # test widget activation
            if widget.handle_event(event, None):
                # widget activated, return its id
                return widget.id
        # no widget activated to this event
        return None

    def draw_gui(self):
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        widgets = self.widgets['screen']
        if len(widgets) > 0:
            for widget in widgets:
                # tuple of the bitmap and its rect, after loop ends in reverse order
                self.bitmaps.insert(0, (cut(self.surface, widget.rect), widget.rect))
                # draw the widget
                widget.draw()
        if len(self.windows) > 0:
            for window in self.windows:
                rec = Rect(window.x, window.y - 20, window.width, window.height + 20)
                self.bitmaps.insert(0, (cut(self.surface, rec), rec))
                window.draw_title_bar()
                widgets = window.widgets.get('window', [])
                for widget in widgets:
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
            if 'window' not in self.window.widgets.keys():
                self.window.widgets['window'] = []
            # append the widget to the context
            self.window.widgets['window'].append(widget)
        else:
            # add a widget to the manager
            widget.surface = self.surface
            if 'screen' not in self.widgets.keys():
                self.widgets['screen'] = []
            # append the widget to the group
            self.widgets['screen'].append(widget)
