import pygame
from pygame import Rect
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .scheduler import Timers, Scheduler
from .constants import GKind, GType, CType
from .bitmapfactory import BitmapFactory
from .widgets.registry import create_widget
class GuiError(Exception):
    pass

class GuiManager:
    def __init__(self, surface, fonts):
        self.bitmap_factory = BitmapFactory()
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        for name, filename, size in fonts:
            self.get_bitmapfactory().load_font(name, filename, size)
        # gridded layout variables and functions
        self.position_gridded = self.x_size_pixels_gridded = self.y_size_pixels_gridded = self.space_size_gridded = self.use_rect = None
        # screen surface
        self.surface = surface
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
        self.mouse_delta = None
        # current mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        # whether the mouse is in a locked area state
        self.mouse_locked = False
        # area rect to keep the mouse position within
        self.lock_area_rect = None
        # cursor image and hotspot
        self.cursor_image = None
        self.cursor_hotspot = None
        self.cursor_rect = None
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
        self.set_buffered(False)
        # scheduler
        self.scheduler = Scheduler(self)
        # gui timers
        self.timers = Timers()

    def create(self, widget_type, *args, **kwargs):
        return self.add(create_widget(widget_type, self, *args, **kwargs))

    def add(self, gui_object):
        if gui_object.ctype == CType.Window:
            # add this window to the gui
            self.windows.append(gui_object)
            # make this object the destination for gui add commands
            self.active_object = gui_object
        elif gui_object.ctype == CType.Widget:
            # callback
            if self.active_object != None:
                # store a reference to the window the widget is in
                gui_object.window = self.active_object
                # give the widget a reference to the window surface
                gui_object.surface = self.active_object.surface
                # append the widget to the window's list
                self.active_object.widgets.append(gui_object)
            else:
                # give the widget a reference to the screen surface
                gui_object.surface = self.surface
                # append the widget to the screen list
                self.widgets.append(gui_object)
        else:
            raise GuiError('gui_object must be a window or widget')
        return gui_object

    # setup variables for gridded
    def set_grid_properties(self, anchor, width, height, spacing, use_rect_flag=True):
        self.position_gridded = anchor
        self.x_size_pixels_gridded = width
        self.y_size_pixels_gridded = height
        self.space_size_gridded = spacing
        self.use_rect = use_rect_flag

    # returns Rect() from width, height, and spacing for x and y grid coordinates from the anchor
    def gridded(self, x, y):
        base_x, base_y = self.position_gridded
        # (size per unit) + (space per unit)
        x_pos = base_x + (x * self.x_size_pixels_gridded) + (x * self.space_size_gridded)
        y_pos = base_y + (y * self.y_size_pixels_gridded) + (y * self.space_size_gridded)
        if self.use_rect:
            return Rect(x_pos, y_pos, self.x_size_pixels_gridded, self.y_size_pixels_gridded)
        else:
            return (x_pos, y_pos)

    # convert the point from a main surface one to a window point
    def convert_to_window(self, point, window):
        # fall-through function, perform the conversion only if necessary
        if window != None:
            x, y = self.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        # conversion not necessary
        return self.lock_area(point)

    # convert the point from a window point to a main surface one
    def convert_to_screen(self, point, window):
        # fall-through function, perform the conversion only if necessary
        if window != None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        # conversion not necessary
        return self.lock_area(point)

    def set_pristine(self, image, obj=None):
        # set the backdrop bitmap for the main surface and copy it to the pristine bitmap
        if obj == None:
            obj = self
        if image != None:
            bitmap = pygame.image.load(self.bitmap_factory.file_resource('images', image))
            _, _, width, height = obj.surface.get_rect()
            scaled_bitmap = pygame.transform.smoothscale(bitmap, (width, height))
            obj.surface.blit(scaled_bitmap.convert(), (0, 0), scaled_bitmap.get_rect())
        else:
            raise GuiError('set_pristine requires an image')
        obj.pristine = self.copy_graphic_area(obj.surface, obj.surface.get_rect()).convert()

    # copy graphic helper
    def copy_graphic_area(self, surface, rect, flags = 0):
        bitmap = pygame.Surface((rect.width, rect.height), flags)
        bitmap.blit(surface, (0, 0), rect)
        return bitmap

    def restore_pristine(self, area=None, obj=None):
        # if obj is ommited then restore_pristine is from the screen pristine.
        # if obj is supplied the object must have a obj.surface and an obj.pristine
        # to use here
        # restores a graphic area from the screen's pristine bitmap to the
        # screen surface. if area is None then restore entire surface
        if obj == None:
            obj = self
        if area == None:
            area = obj.pristine.get_rect()
        x, y, _, _ = area
        obj.surface.blit(obj.pristine, (x, y), area)

    def set_cursor(self, hotspot, image):
        # set the cursor image and hotspot
        self.cursor_image = self.bitmap_factory.image_alpha('cursors', image)
        self.cursor_rect = self.cursor_image.get_rect()
        self.cursor_hotspot = hotspot

    def get_buffered(self):
        # return whether or not drawing is buffered
        return self.buffered

    def set_buffered(self, buffered):
        # if buffered is set to True then bitmaps under gui objects
        # will be saved and the undraw will undo them
        self.buffered = buffered

    def get_scheduler(self):
        return self.scheduler

    def get_bitmapfactory(self):
        return self.bitmap_factory

    def get_mouse_pos(self):
        # if a gui_do client needs the mouse position they use this method
        return self.lock_area(self.mouse_pos)

    def set_mouse_pos(self, pos, update_physical_coords=True):
        self.mouse_pos = self.lock_area(pos)
        if update_physical_coords:
            pygame.mouse.set_pos(self.mouse_pos)

    # if more items needed, item3=None and so on so they're always optional
    def event(self, event_type, item1=None, item2=None):
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
                # button group
                self.group = None
        # construct an event to be returned to the client
        gui_event = GuiEvent()
        # set the type of the event
        gui_event.type = event_type
        # parse additional information about the event
        if event_type == GKind.Pass or event_type == GKind.Quit:
            return gui_event
        elif event_type == GKind.Widget:
            gui_event.widget_id = item1
        elif event_type == GKind.Group:
            gui_event.group = item1
            gui_event.widget_id = item2
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
                self.dragging_window.set_pos((self.dragging_window.x, self.dragging_window.y))
                self.set_mouse_pos((self.dragging_window.x - self.mouse_delta[0], self.dragging_window.y - self.mouse_delta[1]))
                self.dragging_window = None
                self.mouse_delta = None
        elif (event.type == MOUSEMOTION) and self.dragging:
            x = self.dragging_window.x + event.rel[0]
            y = self.dragging_window.y + event.rel[1]
            self.set_mouse_pos((x - self.mouse_delta[0], y - self.mouse_delta[1]), False)
            self.dragging_window.set_pos((x, y))
        elif (event.type == MOUSEBUTTONDOWN) and (not self.dragging):
            if event.button == 1:
                # if there is an active window test for dragging
                if self.active_window != None:
                    # if within the title bar
                    if self.active_window.get_title_bar_rect().collidepoint(self.lock_area(event.pos)):
                        # if the lower widget
                        if self.active_window.get_widget_rect().collidepoint(self.lock_area(event.pos)):
                            self.lower_window(self.active_window)
                            self.active_window = self.windows[-1]
                            return self.event(GKind.Pass)
                        # begin dragging
                        self.dragging = True
                        self.dragging_window = self.active_window
                        self.mouse_delta = (self.dragging_window.x - self.mouse_pos[0],
                                            self.dragging_window.y - self.mouse_pos[1])
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
                                        if widget.GType == GType.ButtonGroup:
                                            return self.event(GKind.Group, widget.read_group(), widget.read_id())
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
                        if widget.GType == GType.ButtonGroup:
                            return self.event(GKind.Group, widget.read_group(), widget.read_id())
                        return self.event(GKind.Widget, widget.id)
                    if widget.hit_rect != None:
                        hit = widget.hit_rect.collidepoint(self.convert_to_window(self.get_mouse_pos(), None))
                    else:
                        hit = widget.draw_rect.collidepoint(self.convert_to_window(self.get_mouse_pos(), None))
                    if hit:
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
        else:
            if self.mouse_locked:
                pygame.mouse.set_pos(self.mouse_pos)
            # switch to absolute mouse mode
            self.locking_object = None
            self.mouse_locked = False
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
            return (x, y)
        else:
            return position

    def raise_window(self, window):
        # move the window to the last item in the list which has the highest priority
        self.windows.append(self.windows.pop(self.windows.index(window)))

    def lower_window(self, window):
        # move the window to the first item in the list which has the lowest priority
        self.windows.insert(0, self.windows.pop(self.windows.index(window)))

    # reading and setting last_widget and current_widget are used in the widget base class
    def read_last_widget(self):
        return self.last_widget

    def set_last_widget(self, widget):
        self.last_widget = widget

    def read_current_widget(self):
        return self.current_widget

    def set_current_widget(self, widget):
        self.current_widget = widget

    def hide_widgets(self, *widgets):
        for widget in widgets:
            widget.set_visible(False)

    def show_widgets(self, *widgets):
        for widget in widgets:
            widget.set_visible(True)

    def draw_gui(self):
        # draw all widgets to their surfaces
        if self.buffered:
            self.bitmaps.clear()
        for widget in self.widgets:
            if widget.get_visible():
                # save the bitmap area under the widgets if buffered
                if self.buffered:
                    self.bitmaps.insert(0, (self.copy_graphic_area(self.surface, widget.get_rect()), widget.get_rect()))
                # draw the widget
                widget.draw()
        for window in self.windows:
            if window.get_visible():
                # save the bitmap area under the window if buffered
                if self.buffered:
                    self.bitmaps.insert(0, (self.copy_graphic_area(self.surface, window.get_window_rect()), window.get_window_rect()))
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
            self.mouse_pos = self.lock_area(self.mouse_pos)
        # draw mouse cursor
        cursor_rect = Rect(self.mouse_pos[0] - self.cursor_hotspot[0], self.mouse_pos[1] - self.cursor_hotspot[1],
                           self.cursor_rect.width, self.cursor_rect.height)
        # save the bitmap area under the window if buffered
        if self.buffered:
            self.bitmaps.insert(0, (self.copy_graphic_area(self.surface, cursor_rect), cursor_rect))
        self.surface.blit(self.cursor_image, cursor_rect)

    def undraw_gui(self):
        # reverse the bitmaps that were under each gui object drawn, if buffered is false then
        # the client does not call this method at all
        for bitmap, rect in self.bitmaps:
            self.surface.blit(bitmap, rect)
        self.bitmaps.clear()
