import pygame
from pygame import Rect
from .scheduler import Timers, Scheduler
from .values.constants import EventKind, ContainerKind
from .bitmapfactory import BitmapFactory
from .widgets.utility.registry import create_widget
from .widgets.utility.event_dispatcher import EventDispatcher
from .widgets.utility.layout_manager import LayoutManager
from .widgets.utility.renderer import Renderer

class GuiError(Exception):
    pass

class GuiManager:
    def __init__(self, surface, fonts, bitmap_factory=None):
        self._bitmap_factory = bitmap_factory or BitmapFactory()
        self.event_dispatcher = EventDispatcher(self)
        self.layout_manager = LayoutManager()
        self.renderer = Renderer(self)
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        for name, filename, size in fonts:
            self._bitmap_factory.load_font(name, filename, size)
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
        # current widget
        self._current_widget = None
        # the pristine state of the screen bitmap
        self.pristine = None
        # locking object
        self.locking_object = None
        # whether or not drawing is buffered
        self._buffered = False
        self._scheduler = Scheduler(self)
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

    def set_grid_properties(self, anchor, width, height, spacing, use_rect=True):
        self.layout_manager.set_properties(anchor, width, height, spacing, use_rect)

    def gridded(self, x, y):
        return self.layout_manager.get_cell(x, y)

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

    @property
    def buffered(self):
        return self._buffered

    @buffered.setter
    def buffered(self, value):
        self._buffered = value

    @property
    def bitmap_factory(self):
        return self._bitmap_factory

    @property
    def scheduler(self):
        return self._scheduler

    def set_buffered(self, buffered):
        self.buffered = buffered

    def get_buffered(self):
        return self.buffered

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
        self.renderer.draw()

    def undraw_gui(self):
        self.renderer.undraw()
