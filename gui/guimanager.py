from .utility import copy_graphic_area, load_font, set_font, image_alpha, screen_coord_to_window_coord
from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from pygame import Rect
from pygame.mouse import set_pos

class GuiManager:
    # the following code makes the GuiManager a singleton. there is one screen so there is one gui manager
    # No matter how many times it is instantiated the result is the one object and its state
    _instance_ = None
    def __new__(cls):
        if GuiManager._instance_ is None:
            GuiManager._instance_ = object.__new__(cls)
            GuiManager._instance_._populate_()
        return GuiManager._instance_

    # instead of an __init__ we have _populate_ and it is executed exactly once
    def _populate_(self):
        # gui drawing surface
        self.surface = None
        # load fonts for utility functions
        load_font('label', 'Ubuntu-Medium.ttf', 10)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 12)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('bigger', 'Ubuntu-Medium.ttf', 18)
        load_font('biggest', 'Ubuntu-Medium.ttf', 36)
        # set default font
        set_font('normal')
        # dictionary of window names to their objects: key:value -> name, object
        self.names = {}
        # list of widgets attached to the screen
        self.widgets = []
        # which key group to use
        self.group = None
        # list of bitmaps overwritten by gui objects
        self.bitmaps = []
        # active object
        self.active_object = None
        # set the default object to the screen
        self.set_active_object()
        # list of windows to process
        self.windows = []
        # dragging window
        self.dragging = None
        self.dragging_window = None
        self.saved_graphic = None
        # current mouse position
        self.mouse_pos = None
        # cursor image and hotspot
        self.cursor_image = None
        self.cursor_hotspot = None
        self.cursor_rect = None
        # area rect to lock the mouse position within, lock area is in screen coordinates not window
        self.lock_area_rect = None

    def set_surface(self, surface):
        # gui screen surface
        self.surface = surface

    def set_active_object(self, object=None):
        # set which object is active
        self.active_object = object

    def set_cursor_image(self, *image):
        self.cursor_image = image_alpha(*image)
        self.cursor_rect = self.cursor_image.get_rect()

    def set_cursor_hotspot(self, position):
        self.cursor_hotspot = position

    def get_mouse_pos(self):
        # return the mouse position
        return self.mouse_pos

    def add(self, widget):
        if self.active_object != None:
            widget.surface = self.active_object.surface
            # append the widget to the object
            self.active_object.widgets.append(widget)
        else:
            # add a widget to the screen
            widget.surface = self.surface
            # append the widget to the group
            self.widgets.append(widget)

    def add_window(self, name, window):
        self.names[name] = window
        self.windows.append(window)

    def get_window(self, name):
        return self.names[name]

    def set_lock_area(self, area=None):
        self.lock_area_rect = area

    def lock_area(self, position):
        if self.lock_area_rect != None:
            x, y = position
            adjusted = False
            if x < self.lock_area_rect.x:
                x = self.lock_area_rect.x
                adjusted = True
            elif x > self.lock_area_rect.right:
                x = self.lock_area_rect.right
                adjusted = True
            if y < self.lock_area_rect.top:
                y = self.lock_area_rect.top
                adjusted = True
            elif y > self.lock_area_rect.bottom:
                y = self.lock_area_rect.bottom
                adjusted = True
            if adjusted:
                set_pos(x, y)
            return (x, y)
        else:
            return position

    def handle_event(self, event):
        # update internal mouse position
        if event.type == MOUSEMOTION:
            self.mouse_pos = self.lock_area(event.pos)
        # handle window dragging
        if event.type == MOUSEBUTTONUP and self.dragging:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            xdif, ydif = event.rel
            self.dragging_window.set_pos((self.dragging_window.x + xdif, self.dragging_window.y + ydif))
        elif event.type == MOUSEBUTTONDOWN and not self.dragging:
            if event.button == 1:
                for window in self.windows:
                    if window.title_bar_rect.collidepoint(event.pos):
                        self.dragging = True
                        self.dragging_window = window
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
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        for widget in self.widgets:
            # tuple of the bitmap and its rect, after loop ends in reverse order
            self.bitmaps.insert(0, (copy_graphic_area(self.surface, widget.rect), widget.rect))
            # draw the widget
            widget.draw()
        for window in self.windows:
            self.bitmaps.insert(0, (copy_graphic_area(self.surface, window.get_rect()), window.get_rect()))
            window.draw_title_bar()
            for widget in window.widgets:
                # draw the widget
                widget.draw()
            self.surface.blit(window.surface, (window.x, window.y))
        # draw mouse cursor
        cursor_rect = Rect(self.mouse_pos[0] - self.cursor_hotspot[0], self.mouse_pos[1] - self.cursor_hotspot[1],
                           self.cursor_rect.width, self.cursor_rect.height)
        self.bitmaps.insert(0, (copy_graphic_area(self.surface, cursor_rect), cursor_rect))
        self.surface.blit(self.cursor_image, cursor_rect)

    def undraw_gui(self):
        # reverse the bitmaps that were under each gui object drawn
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)
