import pygame
from pygame import Rect
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .scheduler import Timers, Scheduler
from .values.constants import EventKind, WidgetKind, ContainerKind
from .widgets.utility.interactive import State
from .bitmapfactory import BitmapFactory
from .widgets.utility.registry import create_widget
from .widgets.utility.event_dispatcher import EventDispatcher

class GuiError(Exception):
    pass

class GuiManager:
    def __init__(self, surface, fonts, bitmap_factory=None):
        self.bitmap_factory = bitmap_factory or BitmapFactory()
        self.event_dispatcher = EventDispatcher(self)
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
        # current widgets
        self._current_widget = None
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
        if gui_object.ContainerKind == ContainerKind.Window:
            # add this window to the gui
            self.windows.append(gui_object)
            # make this object the destination for gui add commands
            self.active_object = gui_object
        elif gui_object.ContainerKind == ContainerKind.Widget:
            # callback
            if self.active_object is not None:
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
        if window is not None:
            x, y = self.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        # conversion not necessary
        return self.lock_area(point)

    # convert the point from a window point to a main surface one
    def convert_to_screen(self, point, window):
        # fall-through function, perform the conversion only if necessary
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        # conversion not necessary
        return self.lock_area(point)

    def set_pristine(self, image, obj=None):
        # set the backdrop bitmap for the main surface and copy it to the pristine bitmap
        if obj is None:
            obj = self
        if image is not None:
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
        if obj is None:
            obj = self
        if area is None:
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

    def event(self, event_type, **kwargs):
        class GuiEvent:
            def __init__(self, event_type, **kwargs):
                self.type = event_type
                self.key = kwargs.get('key')
                self.pos = kwargs.get('pos')
                self.rel = kwargs.get('rel')
                self.button = kwargs.get('button')
                self.widget_id = kwargs.get('widget_id')
                self.group = kwargs.get('group')
        if event_type in (EventKind.MouseButtonUp, EventKind.MouseButtonDown, EventKind.MouseMotion):
            kwargs.setdefault('pos', self.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self):
        # process event queue
        for raw_event in pygame.event.get():
            # process event
            event = self.handle_event(raw_event)
            if event.type == EventKind.Pass:
                # no operation
                continue
            # yield current event
            yield event

    def handle_event(self, event):
        return self.event_dispatcher.handle(event)

    def _update_active_window(self):
        top_window = None
        for window in self.windows[::-1]:
            if window.get_visible() and window.get_window_rect().collidepoint(self.get_mouse_pos()):
                top_window = window
                break
        if top_window:
            self.active_window = top_window
        else:
            self.active_window = None

    def _handle_window_dragging(self, event):
        if event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.dragging_window.set_pos((self.dragging_window.x, self.dragging_window.y))
            self.set_mouse_pos((self.dragging_window.x - self.mouse_delta[0], self.dragging_window.y - self.mouse_delta[1]))
            self.dragging_window = None
            self.mouse_delta = None
        elif event.type == MOUSEMOTION and self.dragging:
            x = self.dragging_window.x + event.rel[0]
            y = self.dragging_window.y + event.rel[1]
            self.set_mouse_pos((x - self.mouse_delta[0], y - self.mouse_delta[1]), False)
            self.dragging_window.set_pos((x, y))
        return self.event(EventKind.Pass)

    def _check_window_drag_start(self, event):
        if self.active_window and self.active_window.get_title_bar_rect().collidepoint(self.lock_area(event.pos)):
            if self.active_window.get_widget_rect().collidepoint(self.lock_area(event.pos)):
                self.lower_window(self.active_window)
                self.active_window = self.windows[-1]
            else:
                self.dragging = True
                self.dragging_window = self.active_window
                self.mouse_delta = (self.dragging_window.x - self.mouse_pos[0],
                                    self.dragging_window.y - self.mouse_pos[1])

    def _handle_locked_object(self, event):
        if self.locking_object.WidgetKind == WidgetKind.Scrollbar:
            window = self.locking_object.window if hasattr(self.locking_object, 'window') else None
            if self.handle_widget(self.locking_object, event, window):
                # Ensure widget_id is provided even if locking_object.id is None
                widget_id = getattr(self.locking_object, 'id', None)
                return self.event(EventKind.Widget, widget_id=widget_id)
            return self.event(EventKind.Pass)
        return self.event(EventKind.Pass)

    def _process_window_widgets(self, event):
        # clicking on the window the mouse is over raises it
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.raise_window(self.active_window)
        hit_any = False
        for window in self.windows.copy()[::-1]:
            if window.get_visible() and window.get_window_rect().collidepoint(self.get_mouse_pos()):
                for widget in window.widgets.copy()[::-1]:
                    if widget.get_visible():
                        if widget.get_collide(window):
                            hit_any = True
                            self.update_focus(widget)
                            if self.handle_widget(widget, event, window):
                                if widget.WidgetKind == WidgetKind.ButtonGroup:
                                    return self.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                                return self.event(EventKind.Widget, widget_id=widget.id)
                        elif widget.WidgetKind == WidgetKind.ButtonGroup and widget.state == State.Armed:
                            if self.handle_widget(widget, event, window):
                                return self.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                # If window is visible but mouse not in window rect (or no widget hit), clear focus
                if not hit_any:
                    self.update_focus(None)
                return self.event(EventKind.Pass)
        self.update_focus(None)
        return self._handle_base_mouse_events(event)

    def _process_screen_widgets(self, event):
        hit_any = False
        for widget in self.widgets.copy()[::-1]:
            if widget.get_visible():
                hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
                if hit_rect.collidepoint(self.convert_to_window(self.get_mouse_pos(), None)):
                    hit_any = True
                    self.update_focus(widget)
                    if self.handle_widget(widget, event):
                        if widget.WidgetKind == WidgetKind.ButtonGroup:
                            return self.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                        return self.event(EventKind.Widget, widget_id=widget.id)
        if not hit_any:
            self.update_focus(None)
            return self._handle_base_mouse_events(event)
        return self.event(EventKind.Pass)

    def _handle_base_mouse_events(self, event):
        if event.type == MOUSEBUTTONUP:
            return self.event(EventKind.MouseButtonUp, button=event.button)
        elif event.type == MOUSEBUTTONDOWN:
            return self.event(EventKind.MouseButtonDown, button=event.button)
        if event.type == MOUSEMOTION:
            return self.event(EventKind.MouseMotion, rel=event.rel)
        return self.event(EventKind.Pass)

    def handle_widget(self, widget, event, window=None):
        # if a widget has an activation use the callback or signal that its id be returned from handle_event()
        if widget.handle_event(event, window):
            # widget activated
            if widget.callback is not None:
                widget.callback()
                return False
            else:
                return True
        return False

    @property
    def current_widget(self):
        return self._current_widget

    @current_widget.setter
    def current_widget(self, value):
        if self._current_widget != value:
            if self._current_widget is not None:
                self._current_widget.leave()
            self._current_widget = value

    def update_focus(self, new_hover):
        # Delegate to the property setter
        self.current_widget = new_hover

    def set_lock_area(self, locking_object, area=None):
        # lock area rect is in screen coordinates
        if area is not None:
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
        if self.lock_area_rect is not None:
            x, y = position
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
        self.windows.remove(window)
        self.windows.append(window)

    def lower_window(self, window):
        # move the window to the first item in the list which has the lowest priority
        self.windows.remove(window)
        self.windows.insert(0, window)

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
