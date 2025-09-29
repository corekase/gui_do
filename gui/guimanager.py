import pygame
from enum import Enum
from pygame import Rect
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .command import copy_graphic_area, convert_to_window
from .timers import Timers

GKind = Enum('GKind', ['Pass', 'Quit', 'KeyDown', 'KeyUp', 'MouseButtonDown',
                       'MouseButtonUp', 'MouseMotion', 'Widget'])

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
        # whether the mouse is in a locked area state
        self.mouse_locked = False
        # where the mouse pointer is when an area is locked
        self.locked_pos = None
        # area rect to keep the mouse position within
        self.lock_area_rect = None
        # cursor image and hotspot
        self.cursor_image = None
        self.cursor_hotspot = None
        self.cursor_rect = None
        # object_bank[name][bank][screen|windows]=lists
        self.object_bank = {}
        # which window is active
        self.active_window = None
        # current and last widgets
        self.current_widget = None
        self.last_widget = None
        # the pristine state of the screen bitmap
        self.pristine = None
        # locking object
        self.locking_object = None
        # whether or not drawing is buffered
        self.buffered = False
        # gui timers
        self.timers = Timers()

    def get_mouse_pos(self):
        # if a gui_do client needs the mouse position they use this method
        return self.lock_area(self.mouse_pos)

    # if more items needed, item2=None and so on so they're always optional
    def event(self, event_type, item1=None):
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
                self.widget_id = None
        # construct an event to be returned to the client
        gui_event = GuiEvent()
        # set the type of the event
        gui_event.type = event_type
        # parse additional information about the event
        if event_type == GKind.Pass or event_type == GKind.Quit:
            return gui_event
        elif event_type == GKind.Widget:
            gui_event.widget_id = item1
        elif event_type == GKind.KeyUp:
            gui_event.key = item1
        elif event_type == GKind.KeyDown:
            gui_event.key = item1
        elif event_type == GKind.MouseButtonUp:
            gui_event.pos = self.get_mouse_pos()
            gui_event.button = item1
        elif event_type == GKind.MouseButtonDown:
            gui_event.pos = self.get_mouse_pos()
            gui_event.button = item1
        elif event_type == GKind.MouseMotion:
            gui_event.pos = self.get_mouse_pos()
            gui_event.rel = item1
        # elif more types
        return gui_event

    def events(self):
        # update internal gui timers
        self.timers.update()
        # process event queue
        for raw_event in pygame.event.get():
            # process event
            event = self.handle_event(raw_event)
            if event.type == GKind.Pass:
                # no operation
                continue
            # yield current event
            yield event

    def handle_event(self, event):
        # update internal mouse position
        if event.type == MOUSEMOTION:
            if self.mouse_locked:
                # switching to relative mode is because the mouse set_pos() function is very
                # expensive on Linux and tanks the framerate if called too much. Windows is
                # unaffected by that, it's a Linux platform-specific bug and by being relative
                # for the lock area set_pos is only called once, when the lock area is released
                x, y = self.mouse_pos
                dx, dy = event.rel
                x += dx
                y += dy
                self.mouse_pos = (x, y)
                self.locked_pos = (x, y)
            else:
                self.mouse_pos = self.lock_area(event.pos)
        # check for alt-f4 or window quit button
        if event.type == QUIT:
            return self.event(GKind.Quit)
        # check for a keys
        if event.type == KEYUP:
            return self.event(GKind.KeyUp, event.key)
        elif event.type == KEYDOWN:
            return self.event(GKind.KeyDown, event.key)
        # find highest window
        top_window = None
        for window in self.windows[::-1]:
            if window.get_visible():
                if window.get_window_rect().collidepoint(self.get_mouse_pos()):
                    top_window = window
                    break
        # if top_window is None then the mouse isn't over any window
        if top_window != None:
            # clicking on the window the mouse is over raises it
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.raise_window(top_window)
            # if the highest window isn't active make it so
            if self.active_window != top_window:
                self.active_window = top_window
        else:
            # no window is active, the mouse isn't over one
            self.active_window = None
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
                # if there is an active window test for dragging
                if self.active_window != None:
                    # if within the title bar
                    if self.active_window.get_title_bar_rect().collidepoint(self.lock_area(event.pos)):
                        # if the lower widget
                        if self.active_window.get_widget_rect().collidepoint(self.lock_area(event.pos)):
                            self.lower_window(window)
                            self.active_window = self.windows[-1]
                            return self.event(GKind.Pass)
                        # begin dragging
                        self.dragging = True
                        self.dragging_window = self.active_window
        if self.active_window != None:
            # for each window handle their widgets
            window_consumed = False
            widget_consumed = False
            widget_hit = None
            working_windows = self.windows.copy()[::-1]
            for window in working_windows:
                if window.get_visible():
                    if window.get_window_rect().collidepoint(self.get_mouse_pos()):
                        window_consumed = True
                        for widget in window.widgets:
                                if widget.get_visible():
                                    collision = widget.get_collide(window)
                                    if self.handle_widget(widget, event, window):
                                        return self.event(GKind.Widget, widget.id)
                                    if collision:
                                        widget_consumed = True
                                        widget_hit = widget
                    title_hit = self.active_window.get_title_bar_rect().collidepoint(self.get_mouse_pos())
                    if title_hit or (widget_hit != self.last_widget):
                        if self.last_widget != None:
                            self.last_widget.leave()
                            self.last_widget = None
                    if title_hit or (widget_hit != self.locking_object):
                        if self.locking_object != None:
                            self.locking_object.leave()
                            self.set_lock_area(None)
                    if window_consumed or widget_consumed:
                        return self.event(GKind.Pass)
        else:
            # handle screen widgets
            consumed = False
            widget_hit = None
            for widget in self.widgets:
                if widget.get_visible():
                    if self.handle_widget(widget, event):
                        return self.event(GKind.Widget, widget.id)
                    if widget.rect.collidepoint(convert_to_window(self.get_mouse_pos(), None)):
                        consumed = True
                        widget_hit = widget
            if self.locking_object != None:
                if widget_hit != self.locking_object:
                    self.locking_object.leave()
                    self.set_lock_area(None)
            if consumed:
                return self.event(GKind.Pass)
        #
        if self.last_widget != None:
            self.last_widget.leave()
        # no widget or window consumed the event now do pygame base events
        if event.type == MOUSEBUTTONUP:
            return self.event(GKind.MouseButtonUp, event.button)
        elif event.type == MOUSEBUTTONDOWN:
            return self.event(GKind.MouseButtonDown, event.button)
        if event.type == MOUSEMOTION:
            return self.event(GKind.MouseMotion, event.rel)
        # event did not match anything
        return self.event(GKind.Pass)

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

    def set_lock_area(self, locking_object, area=None):
        # lock area rect is in screen coordinates
        if area != None:
            # switch to relative mouse mode
            self.locking_object = locking_object
            self.mouse_locked = True
            self.locked_pos = self.mouse_pos
        else:
            if self.mouse_locked:
                pygame.mouse.set_pos(self.mouse_pos)
            # switch to absolute mouse mode
            self.locking_object = None
            self.mouse_locked = False
            self.locked_pos = None
        self.lock_area_rect = area

    def lock_area(self, position):
        # keep the position within the lock area rect
        if self.lock_area_rect != None:
            x, y = self.mouse_pos
            if x < self.lock_area_rect.left:
                x = self.lock_area_rect.left
            elif x > self.lock_area_rect.right:
                x = self.lock_area_rect.right
            if y < self.lock_area_rect.top:
                y = self.lock_area_rect.top
            elif y > self.lock_area_rect.bottom:
                y = self.lock_area_rect.bottom
            self.locked_pos = (x, y)
            return (x, y)
        else:
            return position

    def add_window(self, window):
        # add the window object to the list of windows
        self.windows.append(window)

    def raise_window(self, window):
        # move the window to the last item in the list which has the highest priority
        self.windows.append(self.windows.pop(self.windows.index(window)))

    def lower_window(self, window):
        # move the window to the first item in the list which has the lowest priority
        self.windows.insert(0, self.windows.pop(self.windows.index(window)))

    def draw_gui(self):
        # draw all widgets to their surfaces
        if self.buffered:
            self.bitmaps.clear()
        for widget in self.widgets:
            if widget.get_visible():
                # save the bitmap area under the window if buffered
                if self.buffered:
                    self.bitmaps.insert(0, (copy_graphic_area(self.surface, widget.get_rect()), widget.get_rect()))
                # draw the widget
                widget.draw()
        for window in self.windows:
            if window.get_visible():
                # save the bitmap area under the window if buffered
                if self.buffered:
                    self.bitmaps.insert(0, (copy_graphic_area(self.surface, window.get_window_rect()), window.get_window_rect()))
                if window is self.windows[-1]:
                    window.draw_title_bar_active()
                else:
                    window.draw_title_bar_inactive()
                window.draw_window()
                for widget in window.widgets:
                    # draw the widget
                    if widget.get_visible():
                        widget.draw()
                self.surface.blit(window.surface, (window.x, window.y))
        # if locked mode is active always use the locked mode mouse position
        if self.mouse_locked:
            self.mouse_pos = self.locked_pos
        # draw mouse cursor
        cursor_rect = Rect(self.mouse_pos[0] - self.cursor_hotspot[0], self.mouse_pos[1] - self.cursor_hotspot[1],
                           self.cursor_rect.width, self.cursor_rect.height)
        # save the bitmap area under the window if buffered
        if self.buffered:
            self.bitmaps.insert(0, (copy_graphic_area(self.surface, cursor_rect), cursor_rect))
        self.surface.blit(self.cursor_image, cursor_rect)

    def undraw_gui(self):
        # reverse the bitmaps that were under each gui object drawn, if buffered is false then
        # the client does not call this method at all
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)

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

    def load_bank(self):
        # loads a bank entry into the root datastructure. entries are instantiated in the bank and by
        # reference they are moved to the root and from the root. the root is a "working-memory" of
        # whatever happens to be loaded into it
        pass

    def unload_bank(self):
        # removes a bank from the root
        pass
