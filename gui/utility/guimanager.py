import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Iterable, List, Optional, Protocol, Tuple, TypeVar, Union, cast
from .scheduler import Timers, Scheduler
from .constants import ArrowPosition, ButtonStyle, ContainerKind, Event, Orientation, InteractiveState
from .bitmapfactory import BitmapFactory
from .event_dispatcher import EventDispatcher
from .layout_manager import LayoutManager
from .renderer import Renderer
from .widget import Widget
from ..widgets.window import Window
from ..widgets.button import Button
from ..widgets.label import Label
from ..widgets.canvas import Canvas
from ..widgets.image import Image
from ..widgets.scrollbar import Scrollbar
from ..widgets.toggle import Toggle
from ..widgets.arrowbox import ArrowBox
from ..widgets.buttongroup import ButtonGroup
from ..widgets.frame import Frame

class GuiError(Exception):
    pass


class _PristineContainer(Protocol):
    surface: Surface
    pristine: Optional[Surface]


TGuiObject = TypeVar("TGuiObject", Window, Widget)

class GuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type: Event = event_type
        self.key: Optional[int] = cast(Optional[int], kwargs.get('key'))
        self.pos: Optional[Tuple[int, int]] = cast(Optional[Tuple[int, int]], kwargs.get('pos'))
        self.rel: Optional[Tuple[int, int]] = cast(Optional[Tuple[int, int]], kwargs.get('rel'))
        self.button: Optional[int] = cast(Optional[int], kwargs.get('button'))
        self.widget_id: Optional[str] = cast(Optional[str], kwargs.get('widget_id'))
        self.group: Optional[str] = cast(Optional[str], kwargs.get('group'))

class GuiManager:
    def __init__(self, surface: Surface, fonts: List[Tuple[str, str, int]], bitmap_factory: Optional[BitmapFactory] = None,
                 strict_widget_ids: bool = True) -> None:
        """Initialize the GUI manager.

        Args:
            surface: Pygame Surface to render GUI onto.
            fonts: List of (name, filename, size) tuples to load.
            bitmap_factory: Optional BitmapFactory instance. Creates new one if not provided.
            strict_widget_ids: If True, reject duplicate widget IDs across this GuiManager.

        Raises:
            GuiError: If surface is invalid or fonts list is empty.
        """
        if surface is None:
            raise GuiError('surface cannot be None')
        if not fonts or len(fonts) == 0:
            raise GuiError('fonts list cannot be empty')
        for font_entry in fonts:
            if not isinstance(font_entry, tuple) or len(font_entry) != 3:
                raise GuiError('each font entry must be a tuple of (name, filename, size)')
            name, filename, size = font_entry
            if not isinstance(name, str) or not name:
                raise GuiError(f'font name must be a non-empty string, got: {name}')
            if not isinstance(filename, str) or not filename:
                raise GuiError(f'font filename must be a non-empty string, got: {filename}')
            if not isinstance(size, int) or size <= 0:
                raise GuiError(f'font size must be a positive integer, got: {size}')

        self._bitmap_factory: BitmapFactory = bitmap_factory or BitmapFactory()
        self.event_dispatcher: EventDispatcher = EventDispatcher(self)
        self.layout_manager: LayoutManager = LayoutManager()
        self.renderer: Renderer = Renderer(self)
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        for name, filename, size in fonts:
            self._bitmap_factory.load_font(name, filename, size)
        # screen surface
        self.surface: Surface = surface
        # list of widgets attached to the screen
        self.widgets: List[Widget] = []
        # active object for add()
        self._active_object: Optional[Window] = None
        # list of windows
        self.windows: List[Window] = []
        # dragging window
        self.dragging: bool = False
        self.dragging_window: Optional[Window] = None
        self.mouse_delta: Optional[Tuple[int, int]] = None
        # current mouse position
        self.mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        # whether the mouse is in a locked area state
        self.mouse_locked: bool = False
        # area rect to keep the mouse position within
        self.lock_area_rect: Optional[Rect] = None
        # cursor image and hotspot
        self.cursor_image: Optional[Surface] = None
        self.cursor_hotspot: Optional[Tuple[int, int]] = None
        self.cursor_rect: Optional[Rect] = None
        # which window is active
        self.active_window: Optional[Window] = None
        # current widget
        self._current_widget: Optional[Widget] = None
        # the pristine state of the screen bitmap
        self.pristine: Optional[Surface] = None
        # locking object
        self.locking_object: Optional[Widget] = None
        # whether or not drawing is buffered
        self._buffered: bool = False
        self._scheduler: Scheduler = Scheduler(self)
        self.timers: Timers = Timers()
        self.strict_widget_ids: bool = strict_widget_ids
        # per-GuiManager state for ButtonGroup selections
        self._button_groups: dict[str, list[ButtonGroup]] = {}
        self._button_selections: dict[str, ButtonGroup] = {}

    def _widget_id_exists(self, widget_id: str, candidate: Widget) -> bool:
        for widget in self.widgets:
            if widget is not candidate and widget.id == widget_id:
                return True
        for window in self.windows:
            for widget in window.widgets:
                if widget is not candidate and widget.id == widget_id:
                    return True
        return False


    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Add a GUI object (widget or window) to the manager.

        Args:
            gui_object: Widget or Window to add.

        Returns:
            The gui_object that was added.

        Raises:
            GuiError: If gui_object is not a valid Widget or Window.
        """
        if gui_object is None:
            raise GuiError('gui_object cannot be None')
        if not hasattr(gui_object, 'ContainerKind'):
            raise GuiError('gui_object must have a ContainerKind attribute')
        if gui_object.ContainerKind == ContainerKind.Window:
            # add this window to the gui
            self.windows.append(gui_object)
            # make this object the destination for gui add commands
            self._active_object = gui_object
        elif gui_object.ContainerKind == ContainerKind.Widget:
            if self.strict_widget_ids and self._widget_id_exists(gui_object.id, gui_object):
                raise GuiError(f'duplicate widget id: {gui_object.id}')
            # callback
            if self._active_object is not None:
                # store a reference to the window the widget is in
                gui_object.window = self._active_object
                # give the widget a reference to the window surface
                gui_object.surface = self._active_object.surface
                # append the widget to the window's list
                self._active_object.widgets.append(gui_object)
            else:
                # give the widget a reference to the screen surface
                gui_object.surface = self.surface
                # append the widget to the screen list
                self.widgets.append(gui_object)
        else:
            raise GuiError('gui_object must be a window or widget')
        return gui_object

    def set_grid_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        """Configure grid layout properties.

        Args:
            anchor: (x, y) position of grid origin.
            width: Width of each grid cell in pixels.
            height: Height of each grid cell in pixels.
            spacing: Space between grid cells in pixels.
            use_rect: If True, cells are Rect objects; if False, tuples.

        Raises:
            GuiError: If dimensions are invalid.
        """
        if width <= 0:
            raise GuiError(f'grid width must be positive, got: {width}')
        if height <= 0:
            raise GuiError(f'grid height must be positive, got: {height}')
        if spacing < 0:
            raise GuiError(f'grid spacing cannot be negative, got: {spacing}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise GuiError(f'anchor must be a tuple of (x, y), got: {anchor}')
        self.layout_manager.set_properties(anchor, width, height, spacing, use_rect)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        return self.layout_manager.get_cell(x, y)

    # convert the point from a main surface one to a window point
    def convert_to_window(self, point: Tuple[int, int], window: Optional[Window]) -> Tuple[int, int]:
        # fall-through function, perform the conversion only if necessary
        if window is not None:
            x, y = self.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        # conversion not necessary
        return self.lock_area(point)

    # convert the point from a window point to a main surface one
    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Window]) -> Tuple[int, int]:
        # fall-through function, perform the conversion only if necessary
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        # conversion not necessary
        return self.lock_area(point)

    def set_pristine(self, image: str, obj: Optional[_PristineContainer] = None) -> None:
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
    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        bitmap = pygame.Surface((rect.width, rect.height), flags)
        bitmap.blit(surface, (0, 0), rect)
        return bitmap

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional[_PristineContainer] = None) -> None:
        # if obj is ommited then restore_pristine is from the screen pristine.
        # if obj is supplied the object must have a obj.surface and an obj.pristine
        # to use here
        # restores a graphic area from the screen's pristine bitmap to the
        # screen surface. if area is None then restore entire surface
        if obj is None:
            obj = self
        if obj.pristine is None:
            raise GuiError('restore_pristine called before pristine was initialized')
        if area is None:
            area = obj.pristine.get_rect()
        x, y, _, _ = area
        obj.surface.blit(obj.pristine, (x, y), area)

    def set_cursor(self, hotspot: Tuple[int, int], image: str) -> None:
        # set the cursor image and hotspot
        self.cursor_image = self.bitmap_factory.image_alpha('cursors', image)
        self.cursor_rect = self.cursor_image.get_rect()
        self.cursor_hotspot = hotspot

    def window(self, title: str, pos: Tuple[int, int], size: Tuple[int, int], backdrop: Optional[str] = None) -> Window:
        return self.add(Window(self, title, pos, size, backdrop))

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], button_callback: Optional[Callable[[], None]] = None, skip_factory: bool = False) -> Button:
        safe_text = '' if text is None else text
        return self.add(Button(self, id, rect, style, safe_text, button_callback, skip_factory))

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False) -> Label:
        return self.add(Label(self, position, text, shadow))

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, canvas_callback: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        return self.add(Canvas(self, id, rect, backdrop, canvas_callback, automatic_pristine))

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        return self.add(Image(self, id, rect, image, automatic_pristine, scale))

    def scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> Scrollbar:
        return self.add(Scrollbar(self, id, overall_rect, horizontal, style, params))

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        return self.add(Toggle(self, id, rect, style, pushed, pressed_text, raised_text))

    def arrowbox(self, id: str, rect: Rect, direction: float, callback: Optional[Callable[[], None]] = None) -> ArrowBox:
        return self.add(ArrowBox(self, id, rect, direction, callback))

    def buttongroup(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        return self.add(ButtonGroup(self, group, id, rect, style, text))

    def _is_registered_button_group(self, button: ButtonGroup) -> bool:
        # During construction, ButtonGroup widgets are registered in group state
        # before GuiManager.add() assigns their surface/window references.
        if button.surface is None:
            return True
        if button in self.widgets:
            return True
        for window in self.windows:
            if button in window.widgets:
                return True
        return False

    def _prune_button_group(self, group: str) -> None:
        buttons = self._button_groups.get(group)
        if buttons is None:
            return
        self._button_groups[group] = [button for button in buttons if self._is_registered_button_group(button)]
        buttons = self._button_groups.get(group)
        if buttons is None or len(buttons) == 0:
            self._button_groups.pop(group, None)
            self._button_selections.pop(group, None)
            return
        selected = self._button_selections.get(group)
        if selected not in buttons:
            self._button_selections[group] = buttons[0]

    def register_button_group(self, group: str, button: ButtonGroup) -> None:
        self._prune_button_group(group)
        if group not in self._button_groups:
            self._button_groups[group] = []
            self._button_selections[group] = button
        if button in self._button_groups[group]:
            return
        self._button_groups[group].append(button)

    def select_button_group(self, group: str, button: ButtonGroup) -> None:
        self._prune_button_group(group)
        if not self._is_registered_button_group(button):
            return
        previous = self._button_selections.get(group)
        if previous is not None and previous is not button:
            previous.state = InteractiveState.Idle
        self._button_selections[group] = button

    def get_button_group_selection(self, group: str) -> Optional[ButtonGroup]:
        self._prune_button_group(group)
        return self._button_selections.get(group)

    def clear_button_groups(self) -> None:
        self._button_groups.clear()
        self._button_selections.clear()

    def frame(self, id: str, rect: Rect) -> Frame:
        return self.add(Frame(self, id, rect))

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

    def event(self, event_type: Event, **kwargs: object) -> GuiEvent:
        if event_type in (Event.MouseButtonUp, Event.MouseButtonDown, Event.MouseMotion):
            kwargs.setdefault('pos', self.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self) -> Iterable[GuiEvent]:
        # process event queue
        for raw_event in pygame.event.get():
            # process event
            event = self.handle_event(raw_event)
            if event.type == Event.Pass:
                # no operation
                continue
            # yield current event
            yield event

    def handle_event(self, event: PygameEvent) -> GuiEvent:
        return self.event_dispatcher.handle(event)

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional[Window] = None) -> bool:
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

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        # Delegate to the property setter
        self.current_widget = new_hover

    def set_lock_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        # lock area rect is in screen coordinates
        if area is not None:
            if area.width <= 0 or area.height <= 0:
                raise GuiError('lock area dimensions must be positive')
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
            max_x = self.lock_area_rect.right - 1
            max_y = self.lock_area_rect.bottom - 1
            if x < self.lock_area_rect.left:
                x = self.lock_area_rect.left
            elif x > max_x:
                x = max_x
            if y < self.lock_area_rect.top:
                y = self.lock_area_rect.top
            elif y > max_y:
                y = max_y
            return (x, y)
        else:
            return position

    def raise_window(self, window: Window) -> None:
        # move the window to the last item in the list which has the highest priority
        if window not in self.windows:
            return
        self.windows.remove(window)
        self.windows.append(window)

    def lower_window(self, window: Window) -> None:
        # move the window to the first item in the list which has the lowest priority
        if window not in self.windows:
            return
        self.windows.remove(window)
        self.windows.insert(0, window)

    def hide_widgets(self, *widgets: Widget) -> None:
        for widget in widgets:
            widget.visible = False

    def show_widgets(self, *widgets: Widget) -> None:
        for widget in widgets:
            widget.visible = True

    def draw_gui(self) -> None:
        self.renderer.draw()

    def undraw_gui(self) -> None:
        self.renderer.undraw()
