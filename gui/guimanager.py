import pygame
from pygame import Rect
from typing import Optional, List, Tuple, Any, Callable, Iterable
from .scheduler import Timers, Scheduler
from .utility.values.constants import EventKind, ContainerKind
from .bitmapfactory import BitmapFactory
from .utility.registry import create_widget
from .utility.event_dispatcher import EventDispatcher
from .utility.layout_manager import LayoutManager
from .utility.renderer import Renderer

class GuiError(Exception):
    pass

class GuiManager:
    def __init__(self, surface: Any, fonts: List[Tuple[str, str, int]], bitmap_factory: Optional[BitmapFactory] = None) -> None:
        self._bitmap_factory: BitmapFactory = bitmap_factory or BitmapFactory()
        self.event_dispatcher: EventDispatcher = EventDispatcher(self)
        self.layout_manager: LayoutManager = LayoutManager()
        self.renderer: Renderer = Renderer(self)
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        for name, filename, size in fonts:
            self._bitmap_factory.load_font(name, filename, size)
        # gridded layout variables and functions
        self.position_gridded: Optional[Any] = None
        self.x_size_pixels_gridded: Optional[Any] = None
        self.y_size_pixels_gridded: Optional[Any] = None
        self.space_size_gridded: Optional[Any] = None
        self.use_rect: Optional[bool] = None
        # screen surface
        self.surface: Any = surface
        # list of widgets attached to the screen
        self.widgets: List[Any] = []
        # list of bitmaps overwritten by gui objects
        self.bitmaps: List[Tuple[Any, Rect]] = []
        # active object for add()
        self.active_object: Optional[Any] = None
        # list of windows
        self.windows: List[Any] = []
        # dragging window
        self.dragging: bool = False
        self.dragging_window: Optional[Any] = None
        self.mouse_delta: Optional[Tuple[int, int]] = None
        # current mouse position
        self.mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        # whether the mouse is in a locked area state
        self.mouse_locked: bool = False
        # area rect to keep the mouse position within
        self.lock_area_rect: Optional[Rect] = None
        # cursor image and hotspot
        self.cursor_image: Optional[Any] = None
        self.cursor_hotspot: Optional[Tuple[int, int]] = None
        self.cursor_rect: Optional[Rect] = None
        # which window is active
        self.active_window: Optional[Any] = None
        # current widget
        self._current_widget: Optional[Any] = None
        # the pristine state of the screen bitmap
        self.pristine: Optional[Any] = None
        # locking object
        self.locking_object: Optional[Any] = None
        # whether or not drawing is buffered
        self._buffered: bool = False
        self._scheduler: Scheduler = Scheduler(self)
        self.timers: Timers = Timers()

    def create(self, widget_type: str, *args: Any, **kwargs: Any) -> Any:
        return self.add(create_widget(widget_type, self, *args, **kwargs))

    def add(self, gui_object: Any) -> Any:
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

    def set_grid_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        self.layout_manager.set_properties(anchor, width, height, spacing, use_rect)

    def gridded(self, x: int, y: int) -> Any:
        return self.layout_manager.get_cell(x, y)

    # convert the point from a main surface one to a window point
    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        # fall-through function, perform the conversion only if necessary
        if window is not None:
            x, y = self.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        # conversion not necessary
        return self.lock_area(point)

    # convert the point from a window point to a main surface one
    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        # fall-through function, perform the conversion only if necessary
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        # conversion not necessary
        return self.lock_area(point)

    def set_pristine(self, image: str, obj: Optional[Any] = None) -> None:
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
    def copy_graphic_area(self, surface: Any, rect: Rect, flags: int = 0) -> Any:
        bitmap = pygame.Surface((rect.width, rect.height), flags)
        bitmap.blit(surface, (0, 0), rect)
        return bitmap

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional[Any] = None) -> None:
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

    def set_cursor(self, hotspot: Tuple[int, int], image: str) -> None:
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

    def get_mouse_pos(self) -> Tuple[int, int]:
        # if a gui_do client needs the mouse position they use this method
        return self.lock_area(self.mouse_pos)

    def set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        self.mouse_pos = self.lock_area(pos)
        if update_physical_coords:
            pygame.mouse.set_pos(self.mouse_pos)

    def event(self, event_type: Any, **kwargs: Any) -> "GuiManager.GuiEvent":
        class GuiEvent:
            def __init__(self, event_type: Any, **kwargs: Any) -> None:
                self.type: Any = event_type
                self.key: Optional[Any] = kwargs.get('key')
                self.pos: Optional[Tuple[int, int]] = kwargs.get('pos')
                self.rel: Optional[Tuple[int, int]] = kwargs.get('rel')
                self.button: Optional[int] = kwargs.get('button')
                self.widget_id: Optional[Any] = kwargs.get('widget_id')
                self.group: Optional[str] = kwargs.get('group')
        if event_type in (EventKind.MouseButtonUp, EventKind.MouseButtonDown, EventKind.MouseMotion):
            kwargs.setdefault('pos', self.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self) -> Iterable["GuiManager.GuiEvent"]:
        # process event queue
        for raw_event in pygame.event.get():
            # process event
            event = self.handle_event(raw_event)
            if event.type == EventKind.Pass:
                # no operation
                continue
            # yield current event
            yield event

    def handle_event(self, event: Any) -> "GuiManager.GuiEvent":
        return self.event_dispatcher.handle(event)

    def handle_widget(self, widget: Any, event: Any, window: Optional[Any] = None) -> bool:
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

    def update_focus(self, new_hover: Optional[Any]) -> None:
        # Delegate to the property setter
        self.current_widget = new_hover

    def set_lock_area(self, locking_object: Optional[Any], area: Optional[Rect] = None) -> None:
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

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
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

    def raise_window(self, window: Any) -> None:
        # move the window to the last item in the list which has the highest priority
        self.windows.remove(window)
        self.windows.append(window)

    def lower_window(self, window: Any) -> None:
        # move the window to the first item in the list which has the lowest priority
        self.windows.remove(window)
        self.windows.insert(0, window)

    def hide_widgets(self, *widgets: Any) -> None:
        for widget in widgets:
            widget.visible = False

    def show_widgets(self, *widgets: Any) -> None:
        for widget in widgets:
            widget.visible = True

    def draw_gui(self) -> None:
        self.renderer.draw()

    def undraw_gui(self) -> None:
        self.renderer.undraw()
