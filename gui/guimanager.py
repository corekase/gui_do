import pygame
from enum import Enum
from pygame import Rect
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .utility import copy_graphic_area, convert_to_window

GKind = Enum('GKind', ['Pass', 'Quit', 'KeyDown', 'KeyUp', 'MouseButtonDown', 'MouseButtonUp', 'MouseMotion',
                       'Widget', 'Window'])

class GuiEvent:
    # an event object to be returned which includes pygame event information and gui_do information
    def __init__(self):
        self.type: GKind = None
        # keyboard
        self.key = None
        # mouse
        self.pos = None
        self.rel = None
        self.button = None
        # gui
        self.window_id = None
        self.widget_id = None

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
        self.dragging = False
        self.dragging_window = None
        # current mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        # cursor image and hotspot
        self.cursor_image = None
        self.cursor_hotspot = None
        self.cursor_rect = None
        # area rect to keep the mouse position within
        self.lock_area_rect = None
        # object_bank[name][bank][screen|windows]=lists
        self.object_bank = {}
        # which window is active
        self.active_window = None
        # whether to save graphic area under screen widgets, controlled by set_save manipulator in utility
        self.save = True
        # last objects
        self.last_window_object = None
        self.last_screen_object = None

    def set_surface(self, surface):
        # set gui screen surface
        self.surface = surface

    def add_window(self, name, window):
        # store the window object by name
        self.names[name] = window
        # add the window object to the list of windows
        self.windows.append(window)

    def get_window(self, name):
        # returns a window object for the given name
        return self.names[name]

    def get_mouse_pos(self):
        # if a gui_do client needs the mouse position they use this method
        return self.lock_area(self.mouse_pos)

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
        # check for alt-f4 or window quit button
        if event.type == QUIT:
            return self.event({'quit': None})
        # check for a keys
        if event.type == KEYUP:
            return self.event({'keyup': event.key})
        elif event.type == KEYDOWN:
            return self.event({'keydown': event.key})
        # handle window dragging and lower widget
        if (event.type == MOUSEBUTTONUP) and self.dragging:
            if event.button == 1:
                self.dragging = False
                self.dragging_window = None
        elif (event.type == MOUSEMOTION) and self.dragging:
            xdif, ydif = event.rel
            self.dragging_window.set_pos((self.dragging_window.x + xdif, self.dragging_window.y + ydif))
        elif (event.type == MOUSEBUTTONDOWN) and (not self.dragging):
            if event.button == 1:
                for window in self.windows:
                    if window.title_bar_rect.collidepoint(self.lock_area(event.pos)):
                        if window.get_widget_rect().collidepoint(self.get_mouse_pos()):
                            self.lower_window(window)
                            return self.event(None)
                        self.raise_window(window)
                        self.dragging = True
                        self.dragging_window = window
                        return self.event(None)
        # for each window handle their widgets
        window_consumed = False
        widget_consumed = False
        raise_flag = False
        widget_hit = None
        # work on a reversed copy of the window list. the copy is in case the list is modified by raising
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
                            return self.event({'widget_id': widget.id})
                        collision = widget.get_rect().collidepoint(convert_to_window(self.get_mouse_pos(), window))
                        if collision:
                            widget_consumed = True
                            widget_hit = widget
            if self.last_window_object != widget_hit:
                if self.last_window_object != None:
                    self.last_window_object.leave()
                if self.last_screen_object != None:
                    self.last_screen_object.leave()
                    self.last_screen_object = None
                self.last_window_object = widget_hit
            if window_consumed or widget_consumed or raise_flag:
                return self.event(None)
        # handle screen widgets
        consumed = False
        widget_hit = None
        for widget in self.widgets:
            if self.handle_widget(widget, event):
                self.last_screen_object = widget
                return self.event({'widget_id': widget.id})
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
            return self.event(None)
        # no widget or window consumed the event now do pygame base events
        if event.type == MOUSEBUTTONUP:
            return self.event({'mousebuttonup': event.button})
        elif event.type == MOUSEBUTTONDOWN:
            return self.event({'mousebuttondown': event.button})
        if event.type == MOUSEMOTION:
            return self.event({'mousemotion': event.rel})
        # no event matched anything
        return self.event(None)

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

    def event(self, event_dict):
        # construct an event to be returned to the client which includes both gui_do information and pygame
        # event information
        gui_event = GuiEvent()
        if event_dict == None:
            gui_event.type = GKind.Pass
            return gui_event
        keys = event_dict.keys()
        if 'widget_id' in keys:
            gui_event.type = GKind.Widget
            gui_event.widget_id = event_dict['widget_id']
        elif 'quit' in keys:
            gui_event.type = GKind.Quit
        elif 'keyup' in keys:
            gui_event.type = GKind.KeyUp
            gui_event.key = event_dict['keyup']
        elif 'keydown' in keys:
            gui_event.type = GKind.KeyDown
            gui_event.key = event_dict['keydown']
        elif 'mousebuttonup' in keys:
            gui_event.type = GKind.MouseButtonUp
            gui_event.pos = self.get_mouse_pos()
            gui_event.button = event_dict['mousebuttonup']
        elif 'mousebuttondown' in keys:
            gui_event.type = GKind.MouseButtonDown
            gui_event.pos = self.get_mouse_pos()
            gui_event.button = event_dict['mousebuttondown']
        elif 'mousemotion' in keys:
            gui_event.type = GKind.MouseMotion
            gui_event.pos = self.get_mouse_pos()
            gui_event.rel = event_dict['mousemotion']
        # elif more key types
        return gui_event

    def raise_window(self, window):
        # move the window to the last item in the list which has the highest priority
        self.windows.append(self.windows.pop(self.windows.index(window)))
        self.active_window = window

    def lower_window(self, window):
        # move the window to the first item in the list which has the lowest priority
        self.windows.insert(0, self.windows.pop(self.windows.index(window)))
        self.active_window = self.windows[-1]

    def draw_gui(self):
        # draw all widgets to their surfaces
        self.bitmaps.clear()
        for widget in self.widgets:
            # if screen widgets never move then the contents under them don't need to be saved
            if widget.save:
                # tuple of the bitmap and its rect, after loop ends in reverse order
                self.bitmaps.insert(0, (copy_graphic_area(self.surface, widget.rect), widget.rect))
            # draw the widget
            widget.draw()
        for window in self.windows:
            # windows always save contents for the window rect only and not for contained widgets
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
