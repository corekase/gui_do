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
        self.context = None
        # lock to this context
        self.locked_context = None
        # list of bitmaps overwritten by gui objects
        self.bitmaps = []
        # active window
        self.window = None
        # list of windows to process
        self.windows = []

    def switch_context(self, context):
        # if locked_context isn't None then ignore the switch_context call
        if self.locked_context == None:
            # set which key group is active
            self.context = context

    def lock_context(self, lock_context):
        # call with a context to lock to or None to clear
        self.locked_context = lock_context
        self.context = lock_context

    def handle_event(self, event):
        # if a widget signals that it had an action return the widget id
        if self.window != None:
            widgets = self.window.widgets.get(self.context, [])
        else:
            widgets = self.widgets['global'] + self.widgets.get(self.context, [])
        for widget in widgets:
            # test widget activation
            if widget.handle_event(event):
                # widget activated, return its id
                return widget.id
        # no widget activated to this event
        return None

    def draw_widgets(self):
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        if len(self.windows) > 0:
            for window in self.windows:
                widgets = window.widgets.get(self.context, [])
                for widget in widgets:
                    # tuple of the bitmap and its rect, after loop ends in reverse order
                    self.bitmaps.insert(0, (cut(self.surface, widget.rect), widget.rect))
                    # draw the widget
                    widget.draw()
        else:
            widgets = self.widgets['global']
            #widgets = self.widgets['global'] + self.widgets.get(self.context, [])
            for widget in widgets:
                # tuple of the bitmap and its rect, after loop ends in reverse order
                self.bitmaps.insert(0, (cut(self.surface, widget.rect), widget.rect))
                # draw the widget
                widget.draw()
        #if self.window != None:
        self.surface.blit(self.window.surface, (self.window.x, self.window.y))

    def undraw_widgets(self):
        # reverse the bitmaps that were under each gui object drawn
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)

    def add_window(self, window):
        self.windows.append(window)

    def set_window(self, window):
        # which window add_widget adds to
        self.window = window

    def add_widget(self, context, widget):
        if self.window != None:
            widget.surface = self.window.surface
            if context not in self.window.widgets.keys():
                self.window.widgets[context] = []
            # append the widget to the context
            self.window.widgets[context].append(widget)
        else:
            # add a widget to the manager
            if context not in self.widgets.keys():
                self.widgets[context] = []
            # append the widget to the context
            self.widgets[context].append(widget)
