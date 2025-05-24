from .utility import cut, load_font, set_font

class GuiManager:
    def __init__(self, surface):
        # surface to draw the widget to
        self.surface = surface
        # load fonts for utility functions
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('bigger', 'Ubuntu-Medium.ttf', 18)
        load_font('biggest', 'Ubuntu-Medium.ttf', 36)
        # set default font
        set_font('normal')
        # widgets to be managed: key:value -> group_name:list_of_widgets
        self.widgets = {}
        # global widgets which are always shown and processed
        self.widgets['global'] = []
        # which key group to show
        self.group = None
        # list of bitmaps overwritten by gui objects
        self.bitmaps = []
        # active window
        self.window = None
        # list of windows to process
        self.windows = []

    def set_group(self, group, window=None):
        # set which key group is active
        self.group = group
        self.window = window

    def handle_event(self, event):
        # if a widget signals that it had an action return the widget id
        if len(self.windows) > 0:
            for window in self.windows:
                widgets = window.widgets.get(window.group, [])
                for widget in widgets:
                    # test widget activation
                    if widget.handle_event(event, window):
                        # widget activated, return its id
                        return widget.id
        widgets = self.widgets['global']
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
        widgets = self.widgets['global']
        if len(widgets) > 0:
            for widget in widgets:
                # tuple of the bitmap and its rect, after loop ends in reverse order
                self.bitmaps.insert(0, (cut(self.surface, widget.rect), widget.rect))
                # draw the widget
                widget.draw()
        if len(self.windows) > 0:
            for window in self.windows:
                widgets = window.widgets.get(window.group, [])
                for widget in widgets:
                    # tuple of the bitmap and its rect, after loop ends in reverse order
                    self.bitmaps.insert(0, (cut(self.surface, widget.rect), widget.rect))
                    # draw the widget
                    widget.draw()
                self.surface.blit(window.surface, (window.x, window.y))

    def undraw_gui(self):
        # reverse the bitmaps that were under each gui object drawn
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)

    def add_window(self, window):
        self.windows.append(window)

    def add_widget(self, widget):
        if self.window != None:
            widget.surface = self.window.surface
            if self.group not in self.window.widgets.keys():
                self.window.widgets[self.group] = []
            # append the widget to the context
            self.window.widgets[self.group].append(widget)
        else:
            # add a widget to the manager
            widget.surface = self.surface
            if self.group not in self.widgets.keys():
                self.widgets[self.group] = []
            # append the widget to the group
            self.widgets[self.group].append(widget)
