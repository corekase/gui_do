import pygame
from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from .utility import copy_graphic_area, load_font, image_alpha
from .utility import convert_to_window

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
        # screen surface
        self.surface = None
        # load fonts for utility functions
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        # dictionary of window names to their objects: key:value -> name, object
        self.names = {}
        # list of widgets attached to the screen
        self.widgets = []
        # list of bitmaps overwritten by gui objects
        self.bitmaps = []
        # active object for add()
        self.active_object = None
        # list of windows
        self.windows = []
        # dragging window
        self.dragging = None
        self.dragging_window = None
        # current mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        # cursor image and hotspot
        self.cursor_image = None
        self.cursor_hotspot = None
        self.cursor_rect = None
        # area rect to keep the mouse position within
        self.lock_area_rect = None
        # object bank dictionary
        # dictionary of key:value -> name
        #   dictionary of key:value -> bank
        #     dictionary of key:screen and key:windows
        #       -> for the lists
        # object_bank[name][bank][screen|windows]=lists
        self.object_bank = {}
        # which window is active
        self.active_window = None
        # whether to save graphic area under widgets
        self.save = True
        # last object
        self.last_window_object = None
        self.last_screen_object = None

    def set_save(self, flag):
        # whether to set the state of a widget to save the graphic under it
        self.save = flag

    def set_surface(self, surface):
        # set gui screen surface
        self.surface = surface

    def set_active_object(self, object=None):
        # set which object is active
        self.active_object = object

    def set_cursor(self, hotspot, *image):
        # set the cursor image and hotspot
        self.cursor_image = image_alpha(*image)
        self.cursor_rect = self.cursor_image.get_rect()
        self.cursor_hotspot = hotspot

    def get_mouse_pos(self):
        # if a gui_do client needs the mouse position they use this method
        return self.lock_area(self.mouse_pos)

    def add(self, widget, callback=None):
        if widget.id == '<CONSUMED>':
            raise Exception(f'<CONSUMED> is a reserved widget identifier')
        widget.callback = callback
        # set_save manipulator controls this setting
        widget.save = self.save
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
        # store the window object by name
        self.names[name] = window
        # add the window object to the list of windows
        self.windows.append(window)

    def get_window(self, name):
        # returns a window object for the given name
        return self.names[name]

    # -> To-do: implement show/hide for widgets and windows. widgets inside a window
    #           could be hidden, screen widgets could be hidden, and entire windows can be
    #           hidden
    #
    # -> To-do: object banks
    #    for the list of screen widgets and the list of windows and their
    #    lists of widgets: implement a "AMOS bank" system.  where you could define the gui
    #    elements, and switch between different sets of them depending on the state of
    #    your application
    #
    #    so, having one gui manager singleton might complicate a main-menu
    #    where you pass a screen and a new run() instantiates everything from there and releases
    #    the data when it returns. with a singleton gui that menu wouldn't work. but, switch out
    #    banks at the root of the data structures then multiple applications sharing a screen work
    #
    #    object banks could also be divided into specific windows or forms, and you could bank in and
    #    out different ones to a shared root data structure where they operate together.
    #    code definitions for gui layouts can be put into any source file in a function or method that
    #    has the gui manager singleton. as the code executes it creates all the data in the banks, and
    #    then in the application load and mix the bank data as needed
    #
    #    code executing into the object bank will use manipulators like how set_font() is used, to control
    #    which bank names and routes to the leaf lists are constructed

    def set_active_bank(self):
        # bank manipulator, sets destination bank for add widget and window commands.
        # as items are added, their surfaces are still the screen or a window while they are being
        # instantiated. then loading and unloading just determine which are active at any given time
        pass

    def load_bank(self):
        # loads a bank entry into the root datastructure. entries are instantiated in the bank and by
        # reference they are moved to the root and from the root. the root is a "working-memory" of
        # whatever happens to be loaded into it
        pass

    def unload_bank(self):
        # removes a bank from the root
        pass

    def set_lock_area(self, area=None):
        # lock area rect is in screen coordinates
        self.lock_area_rect = area

    def lock_area(self, position):
        # keep the position within the lock area rect
        if self.lock_area_rect != None:
            x, y = position
            adjusted = False
            if x < self.lock_area_rect.left:
                x = self.lock_area_rect.left
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
                pygame.mouse.set_pos(x, y)
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
                    if window.get_rect().collidepoint(self.get_mouse_pos()):
                        if window.title_bar_rect.collidepoint(self.lock_area(event.pos)):
                            if window.get_widget_rect().collidepoint(self.get_mouse_pos()):
                                self.lower_window(window)
                                return '<CONSUMED>'
                            self.dragging = True
                            self.dragging_window = window
        # for each window handle their widgets
        window_consumed = False
        widget_consumed = False
        raise_flag = False
        widget_hit = None
        # work on a copy of the window list in case the list is modified by raising
        working_windows = self.windows.copy()[::-1]
        for window in working_windows:
            if window.get_rect().collidepoint(self.get_mouse_pos()):
                window_consumed = True
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.active_window != window:
                            self.raise_window(window)
                            raise_flag = True
                for widget in window.widgets:
                        if self.handle_widget(widget, event, window):
                            self.last_window_object = widget
                            return widget.id
                        collision = widget.get_rect().collidepoint(convert_to_window(self.get_mouse_pos(), window))
                        if collision:
                            widget_hit = widget
                            widget_consumed = True
            if self.last_window_object != widget_hit:
                if self.last_window_object != None:
                    self.last_window_object.leave()
                if self.last_screen_object != None:
                    self.last_screen_object.leave()
                    self.last_screen_object = None
                self.last_window_object = widget_hit
            if window_consumed or widget_consumed or raise_flag:
                return '<CONSUMED>'
        # handle screen widgets
        consumed = False
        widget_hit = None
        for widget in self.widgets:
            if self.handle_widget(widget, event):
                self.last_screen_object = widget
                return widget.id
            collision = widget.get_rect().collidepoint(self.get_mouse_pos())
            if collision:
                consumed = True
                widget_hit = widget
        if self.last_screen_object != widget_hit:
            if self.last_screen_object != None:
                self.last_screen_object.leave()
        if self.last_window_object != None:
            self.last_window_object.leave()
            self.last_window_object = None
        self.last_screen_object = widget_hit
        if consumed:
            return '<CONSUMED>'
        # no widget or window activated to this event
        return None

    def handle_widget(self, widget, event, window=None):
        # if a widget has an activation use the callback or signal that its id be returned from handle_event()
        if widget.handle_event(event, window):
            # widget activated
            if widget.callback != None:
                widget.callback()
                return False
            else:
                return True
        return False

    def raise_window(self, window):
        # move window to the beginning of the window evaluation, which is done in reverse for the window list
        # so last item first
        self.windows.append(self.windows.pop(self.windows.index(window)))
        self.active_window = window

    def lower_window(self, window):
        self.windows.insert(0, self.windows.pop(self.windows.index(window)))
        self.active_window = self.windows[-1]

    def draw_gui(self):
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        for widget in self.widgets:
            # tuple of the bitmap and its rect, after loop ends in reverse order
            if widget.save:
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
