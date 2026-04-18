import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
import logging
from typing import Callable, Dict, Hashable, Iterable, List, Optional, Protocol, Tuple, TypeVar, Union, cast
from .scheduler import Timers, Scheduler
from .constants import GuiError, ArrowPosition, BaseEvent, ButtonStyle, Event, Orientation
from .bitmapfactory import BitmapFactory
from .buttongroup_mediator import ButtonGroupMediator
from .event_dispatcher import EventDispatcher
from .layout_manager import LayoutManager
from .resource_error import DataResourceErrorHandler
from .renderer import Renderer
from .widget import Widget
from ..widgets.window import Window as gWindow
from ..widgets.button import Button as gButton
from ..widgets.label import Label as gLabel
from ..widgets.canvas import Canvas as gCanvas
from ..widgets.image import Image as gImage
from ..widgets.scrollbar import Scrollbar as gScrollbar
from ..widgets.toggle import Toggle as gToggle
from ..widgets.arrowbox import ArrowBox as gArrowBox
from ..widgets.buttongroup import ButtonGroup as gButtonGroup
from ..widgets.frame import Frame as gFrame
from ..widgets.panel import Panel as gPanel

_logger = logging.getLogger(__name__)

def _noop() -> None:
    pass

def _noop_event(_: BaseEvent) -> None:
    pass

class _PristineContainer(Protocol):
    surface: Surface
    pristine: Optional[Surface]

TGuiObject = TypeVar("TGuiObject", gWindow, Widget)

class GuiEvent(BaseEvent):
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        super().__init__(event_type)
        # Normalize optional payloads defensively so malformed external event data
        # cannot corrupt GUI event routing.
        self.key: Optional[int] = self._as_optional_int(kwargs.get('key'))
        self.pos: Optional[Tuple[int, int]] = self._as_optional_int_pair(kwargs.get('pos'))
        self.rel: Optional[Tuple[int, int]] = self._as_optional_int_pair(kwargs.get('rel'))
        self.button: Optional[int] = self._as_optional_int(kwargs.get('button'))
        self.widget_id: Optional[str] = kwargs.get('widget_id') if isinstance(kwargs.get('widget_id'), str) else None
        self.group: Optional[str] = kwargs.get('group') if isinstance(kwargs.get('group'), str) else None
        self.window: Optional[gWindow] = kwargs.get('window') if isinstance(kwargs.get('window'), gWindow) else None

    @staticmethod
    def _as_optional_int(value: object) -> Optional[int]:
        if type(value) is int:
            return value
        return None

    @staticmethod
    def _as_optional_int_pair(value: object) -> Optional[Tuple[int, int]]:
        if not isinstance(value, tuple) or len(value) != 2:
            return None
        if type(value[0]) is not int or type(value[1]) is not int:
            return None
        return (value[0], value[1])

class GuiManager:
    """Owns widgets/windows, input routing, and rendering for one GUI context."""

    @property
    def bitmap_factory(self):
        return self._bitmap_factory

    @property
    def buffered(self):
        return self._buffered

    @buffered.setter
    def buffered(self, value):
        if not isinstance(value, bool):
            raise GuiError('buffered must be a bool')
        self._buffered = value

    @property
    def current_widget(self):
        return self._resolve_current_widget()

    @current_widget.setter
    def current_widget(self, value):
        if value is not None:
            if not isinstance(value, Widget) or not self._is_registered_object(value):
                value = None
        current = self._resolve_current_widget()
        if current != value:
            if current is not None:
                current.leave()
            self._current_widget = value

    @property
    def scheduler(self):
        return self._scheduler

    # widgets
    def ArrowBox(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> gArrowBox:
        return self.add(gArrowBox(self, id, rect, direction, on_activate))

    def Button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> gButton:
        safe_text = '' if text is None else text
        return self.add(gButton(self, id, rect, style, safe_text, on_activate))

    def ButtonGroup(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> gButtonGroup:
        return self.add(gButtonGroup(self, group, id, rect, style, text))

    def Canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> gCanvas:
        return self.add(gCanvas(self, id, rect, backdrop, on_activate, automatic_pristine))

    def Frame(self, id: str, rect: Rect) -> gFrame:
        return self.add(gFrame(self, id, rect))

    def Image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> gImage:
        return self.add(gImage(self, id, rect, image, automatic_pristine, scale))

    def Label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> gLabel:
        if id is None:
            self._label_sequence += 1
            id = f'label_{self._label_sequence}'
        return self.add(gLabel(self, id, position, text, shadow))

    def Scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> gScrollbar:
        return self.add(gScrollbar(self, id, overall_rect, horizontal, style, params))

    def Toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> gToggle:
        return self.add(gToggle(self, id, rect, style, pushed, pressed_text, raised_text))

    def Window(
        self,
        title: str,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> gWindow:
        return self.add(gWindow(self, title, pos, size, backdrop, preamble, event_handler, postamble))

    def Panel(
        self,
        id: str,
        size: Tuple[int, int],
        x: int = 0,
        reveal_pixels: int = 4,
        auto_hide: bool = True,
        timer_interval: float = 16.0,
        movement_step: int = 4,
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> gPanel:
        return self.add(
            gPanel(
                self,
                id,
                size,
                x,
                reveal_pixels,
                auto_hide,
                timer_interval,
                movement_step,
                backdrop,
                preamble,
                event_handler,
                postamble,
            )
        )

    def __init__(self, surface: Surface, fonts: List[Tuple[str, str, int]], bitmap_factory: Optional[BitmapFactory] = None) -> None:
        """Create a GUI manager bound to a target surface and font registry."""
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
        pygame.mouse.set_visible(False)
        for name, filename, size in fonts:
            self._bitmap_factory.load_font(name, filename, size)
        self.surface: Surface = surface
        self.widgets: List[Widget] = []
        self._active_object: Optional[gWindow] = None
        self.windows: List[gWindow] = []
        self.dragging: bool = False
        self.dragging_window: Optional[gWindow] = None
        self.mouse_delta: Optional[Tuple[int, int]] = None
        self.mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        self.mouse_locked: bool = False
        self.mouse_point_locked: bool = False
        self.lock_area_rect: Optional[Rect] = None
        self.lock_point_pos: Optional[Tuple[int, int]] = None
        self.lock_point_recenter_pending: bool = False
        self.lock_point_tolerance_rect: Optional[Rect] = None
        self.cursor_image: Optional[Surface] = None
        self.cursor_hotspot: Optional[Tuple[int, int]] = None
        self.cursor_rect: Optional[Rect] = None
        self.active_window: Optional[gWindow] = None
        self._current_widget: Optional[Widget] = None
        self.pristine: Optional[Surface] = None
        self.locking_object: Optional[Widget] = None
        self._buffered: bool = False
        self._scheduler: Scheduler = Scheduler(self)
        self.timers: Timers = Timers()
        self.button_group_mediator: ButtonGroupMediator = ButtonGroupMediator(self._is_registered_button_group)
        self._label_sequence: int = 0
        self._screen_preamble: Callable[[], None] = _noop
        self._screen_event_handler: Callable[[BaseEvent], None] = _noop_event
        self._screen_postamble: Callable[[], None] = _noop
        self._task_owner_by_id: Dict[Hashable, gWindow] = {}
        self.point_lock_recenter_rect: Rect = self._build_centered_recenter_rect()
        self.point_lock_tolerance_size: Tuple[int, int] = (
            max(1, self.point_lock_recenter_rect.width),
            max(1, self.point_lock_recenter_rect.height),
        )

    def run_postamble(self) -> None:
        for window in self.windows:
            if window.visible:
                window.run_postamble()
        self._screen_postamble()

    def run_preamble(self) -> None:
        self._screen_preamble()
        for window in self.windows:
            if window.visible:
                window.run_preamble()

    def get_mouse_pos(self) -> Tuple[int, int]:
        return self.lock_area(self.mouse_pos)

    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget and attach container-specific state."""
        if gui_object is None:
            raise GuiError('gui_object cannot be None')
        if not isinstance(gui_object, (gWindow, Widget)):
            raise GuiError('gui_object must be a Window or Widget instance')
        if self._is_registered_object(gui_object):
            raise GuiError(f'gui_object is already registered: {self._describe_gui_object(gui_object)}')
        if isinstance(gui_object, gWindow):
            self.windows.append(gui_object)
            self._active_object = gui_object
        elif isinstance(gui_object, Widget):
            if not isinstance(gui_object.id, str) or gui_object.id == '':
                raise GuiError('widget id must be a non-empty string')
            conflict = self._find_widget_id_conflict(gui_object.id, gui_object)
            if conflict is not None:
                raise GuiError(
                    f'duplicate widget id: {gui_object.id}; '
                    f'incoming={self._describe_gui_object(gui_object)} '
                    f'on {self._describe_incoming_widget_container()}; '
                    f'conflict={self._describe_gui_object(conflict)} '
                    f'on {self._describe_widget_container(conflict)}'
                )
            active_window = self._resolve_active_object()
            if active_window is not None:
                gui_object.window = active_window
                gui_object.surface = active_window.surface
                active_window.widgets.append(gui_object)
            else:
                gui_object.window = None
                gui_object.surface = self.surface
                self.widgets.append(gui_object)
            # Roll back partial registration when post-add hooks fail.
            post_add = getattr(gui_object, '_on_added_to_gui', None)
            if callable(post_add):
                try:
                    post_add()
                except Exception:
                    if active_window is not None:
                        if gui_object in active_window.widgets:
                            active_window.widgets.remove(gui_object)
                    else:
                        if gui_object in self.widgets:
                            self.widgets.remove(gui_object)
                    gui_object.window = None
                    gui_object.surface = None
                    raise
        return gui_object

    def clear_button_groups(self) -> None:
        self.button_group_mediator.clear()

    def clear_task_owners_for_window(self, window: gWindow) -> None:
        if window not in self.windows:
            return
        stale_ids = [task_id for task_id, owner in self._task_owner_by_id.items() if owner is window]
        for task_id in stale_ids:
            del self._task_owner_by_id[task_id]

    def hide_widgets(self, *widgets: Widget) -> None:
        for widget in widgets:
            if not isinstance(widget, Widget):
                raise GuiError(f'hide_widgets expected Widget, got: {type(widget).__name__}')
            widget.visible = False

    def lower_window(self, window: gWindow) -> None:
        self._resolve_active_object()
        if window not in self.windows:
            if self._active_object is window:
                self._active_object = None
            return
        self.windows.remove(window)
        self.windows.insert(0, window)

    def raise_window(self, window: gWindow) -> None:
        self._resolve_active_object()
        if window not in self.windows:
            if self._active_object is window:
                self._active_object = None
            return
        self.windows.remove(window)
        self.windows.append(window)

    def set_cursor(self, name: str) -> None:
        """Set custom cursor from a named cursor loaded via BitmapFactory.load_cursor."""
        if not isinstance(name, str) or name == '':
            raise GuiError('cursor name must be a non-empty string')
        hotspot_position = self.lock_point_pos if (self.mouse_point_locked and self.lock_point_pos is not None) else self.mouse_pos
        if self.cursor_rect is not None and self.cursor_hotspot is not None:
            hotspot_position = (
                self.cursor_rect.x + self.cursor_hotspot[0],
                self.cursor_rect.y + self.cursor_hotspot[1],
            )
        self.cursor_image, self.cursor_hotspot = self.bitmap_factory.get_cursor(name)
        self.cursor_rect = self.cursor_image.get_rect()
        self.cursor_rect.topleft = (
            hotspot_position[0] - self.cursor_hotspot[0],
            hotspot_position[1] - self.cursor_hotspot[1],
        )

    def set_grid_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        """Configure grid cell sizing used by gridded."""
        if width <= 0:
            raise GuiError(f'grid width must be positive, got: {width}')
        if height <= 0:
            raise GuiError(f'grid height must be positive, got: {height}')
        if spacing < 0:
            raise GuiError(f'grid spacing cannot be negative, got: {spacing}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise GuiError(f'anchor must be a tuple of (x, y), got: {anchor}')
        self.layout_manager.set_properties(anchor, width, height, spacing, use_rect)

    def set_lock_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        """Clamp mouse motion to area until released."""
        if area is not None:
            if not isinstance(area, Rect):
                raise GuiError('lock area must be a Rect')
            if locking_object is None:
                raise GuiError('locking_object is required when setting a lock area')
            if not isinstance(locking_object, Widget):
                raise GuiError('locking_object must be a widget')
            if not self._is_registered_object(locking_object):
                raise GuiError('locking_object must be a registered widget')
            if area.width <= 0 or area.height <= 0:
                raise GuiError('lock area dimensions must be positive')
            self.locking_object = locking_object
            self.mouse_locked = True
            self.mouse_point_locked = False
            self.lock_point_pos = None
            self.lock_point_recenter_pending = False
            self.lock_point_tolerance_rect = None
        else:
            if self.mouse_locked:
                if self.mouse_point_locked and self.lock_point_pos is not None:
                    self._set_physical_mouse_pos(self.lock_point_pos)
                    self.mouse_pos = self.lock_point_pos
                else:
                    self._set_physical_mouse_pos(self.mouse_pos)
            self.locking_object = None
            self.mouse_locked = False
            self.mouse_point_locked = False
            self.lock_point_pos = None
            self.lock_point_recenter_pending = False
            self.lock_point_tolerance_rect = None
        self.lock_area_rect = area

    def set_lock_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        """Lock mouse-relative input and recenter hardware pointer when it leaves a broad center area."""
        if locking_object is None:
            self.set_lock_area(None)
            return
        if not isinstance(locking_object, Widget):
            raise GuiError('locking_object must be a widget')
        if not self._is_registered_object(locking_object):
            raise GuiError('locking_object must be a registered widget')
        if point is None:
            point = pygame.mouse.get_pos()
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = True
        self.lock_area_rect = None
        self.lock_point_pos = point
        self.lock_point_tolerance_rect = None
        self.lock_point_recenter_pending = False

    def set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'pos must be a tuple of (x, y), got: {pos}')
        self.mouse_pos = self.lock_area(pos)
        if update_physical_coords:
            self._set_physical_mouse_pos(self.mouse_pos)

    def set_pristine(self, image: str, obj: Optional[_PristineContainer] = None) -> None:
        """Load a backdrop image, scale it to target surface, and cache pristine copy."""
        if obj is None:
            obj = self
        if obj.surface is None:
            raise GuiError('set_pristine target surface is not initialized')
        if image is not None:
            if not isinstance(image, str) or image == '':
                raise GuiError(f'set_pristine image must be a non-empty string, got: {image!r}')
            image_path = self.bitmap_factory.file_resource('images', image)
            try:
                bitmap = pygame.image.load(image_path)
            except GuiError:
                raise
            except Exception as exc:
                DataResourceErrorHandler.raise_load_error('failed to load pristine image', image_path, exc)
            _, _, width, height = obj.surface.get_rect()
            scaled_bitmap = pygame.transform.smoothscale(bitmap, (width, height))
            obj.surface.blit(scaled_bitmap.convert(), (0, 0), scaled_bitmap.get_rect())
        else:
            raise GuiError('set_pristine requires an image')
        obj.pristine = self.copy_graphic_area(obj.surface, obj.surface.get_rect()).convert()

    def set_screen_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        if preamble is not None and not callable(preamble):
            raise GuiError('screen preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('screen event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('screen postamble must be callable or None')
        self._screen_preamble = preamble if preamble is not None else _noop
        self._screen_event_handler = event_handler if event_handler is not None else _noop_event
        self._screen_postamble = postamble if postamble is not None else _noop

    def set_task_owner(self, task_id: Hashable, window: Optional[gWindow]) -> None:
        try:
            hash(task_id)
        except TypeError as exc:
            raise GuiError(f'task id must be hashable: {task_id!r}') from exc
        if window is None:
            self._task_owner_by_id.pop(task_id, None)
            return
        if window not in self.windows:
            raise GuiError('task owner window must be registered')
        self._task_owner_by_id[task_id] = window

    def set_task_owners(self, window: Optional[gWindow], *task_ids: Hashable) -> None:
        for task_id in task_ids:
            self.set_task_owner(task_id, window)

    def show_widgets(self, *widgets: Widget) -> None:
        for widget in widgets:
            if not isinstance(widget, Widget):
                raise GuiError(f'show_widgets expected Widget, got: {type(widget).__name__}')
            widget.visible = True

    def dispatch_event(self, event: BaseEvent) -> None:
        task_owner = self._resolve_task_event_owner(event)
        if task_owner is not None:
            task_owner.handle_event(event)
            return
        event_window = getattr(event, 'window', None)
        if not isinstance(event_window, gWindow):
            event_window = None
        if event_window is not None and event_window in self.windows and event_window.visible:
            event_window.handle_event(event)
            return
        self._screen_event_handler(event)

    def event(self, event_type: Event, **kwargs: object) -> GuiEvent:
        if event_type in (Event.MouseButtonUp, Event.MouseButtonDown, Event.MouseMotion):
            kwargs.setdefault('pos', self.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self) -> Iterable[GuiEvent]:
        for raw_event in pygame.event.get():
            event = self.handle_event(raw_event)
            if event.type == Event.Pass:
                continue
            yield event

    def handle_event(self, event: PygameEvent) -> GuiEvent:
        return self.event_dispatcher.handle(event)

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional[gWindow] = None) -> bool:
        """Run widget handler and execute activation callbacks when present."""
        if widget.handle_event(event, window):
            if widget.on_activate is not None:
                if not callable(widget.on_activate):
                    raise GuiError(f'widget callback is not callable for id: {widget.id}')
                widget.on_activate()
                return False
            else:
                return True
        return False

    def draw_gui(self) -> None:
        self.renderer.draw()

    def undraw_gui(self) -> None:
        self.renderer.undraw()

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[gWindow]) -> Tuple[int, int]:
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        if window is not None and window not in self.windows:
            window = None
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        return self.lock_area(point)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[gWindow]) -> Tuple[int, int]:
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        if window is not None and window not in self.windows:
            window = None
        if window is not None:
            x, y = self.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        return self.lock_area(point)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        return self.layout_manager.get_cell(x, y)

    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        """Return a surface copy of rect from surface."""
        bitmap = pygame.Surface((rect.width, rect.height), flags)
        bitmap.blit(surface, (0, 0), rect)
        return bitmap

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Recenters pointer only when it exits the configured broad center region."""
        if self.lock_point_pos is None:
            self.lock_point_recenter_pending = False
            return
        if not isinstance(hardware_position, tuple) or len(hardware_position) != 2:
            raise GuiError(f'hardware_position must be a tuple of (x, y), got: {hardware_position}')
        in_recenter_rect = self.point_lock_recenter_rect.collidepoint(hardware_position)
        if self.lock_point_recenter_pending:
            if in_recenter_rect:
                self.lock_point_recenter_pending = False
            return
        if not in_recenter_rect:
            self._set_physical_mouse_pos(self.point_lock_recenter_rect.center)
            self.lock_point_recenter_pending = True

    def _set_physical_mouse_pos(self, pos: Tuple[int, int]) -> None:
        try:
            pygame.mouse.set_pos(pos)
        except Exception as exc:
            _logger.debug('pygame.mouse.set_pos failed: %s: %s', type(exc).__name__, exc)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        if not isinstance(position, tuple) or len(position) != 2:
            raise GuiError(f'position must be a tuple of (x, y), got: {position}')
        self._resolve_locking_state()
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

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional[_PristineContainer] = None) -> None:
        """Restore a region from a previously cached pristine bitmap."""
        if obj is None:
            obj = self
        if obj.pristine is None:
            raise GuiError('restore_pristine called before pristine was initialized')
        if area is None:
            area = obj.pristine.get_rect()
        x, y, _, _ = area
        obj.surface.blit(obj.pristine, (x, y), area)

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        self.current_widget = new_hover

    def _resolve_task_event_owner(self, event: BaseEvent) -> Optional[gWindow]:
        if getattr(event, 'type', None) != Event.Task:
            return None
        task_id = cast(Optional[Hashable], getattr(event, 'id', None))
        if task_id is None:
            return None
        try:
            hash(task_id)
        except TypeError:
            return None
        owner = self._task_owner_by_id.get(task_id)
        if owner is None:
            return None
        if owner not in self.windows or not owner.visible:
            return None
        return owner

    def _build_centered_recenter_rect(self, coverage: float = 0.8) -> Rect:
        if coverage <= 0.0 or coverage > 1.0:
            raise GuiError(f'coverage must be in the range (0, 1], got: {coverage}')
        surface_rect = self.surface.get_rect()
        width = max(1, int(surface_rect.width * coverage))
        height = max(1, int(surface_rect.height * coverage))
        centered = Rect(0, 0, width, height)
        centered.center = surface_rect.center
        return centered

    def _describe_gui_object(self, gui_object: TGuiObject) -> str:
        if isinstance(gui_object, Widget):
            return f'{type(gui_object).__name__} id={getattr(gui_object, "id", "<missing>")}'
        if isinstance(gui_object, gWindow):
            return (
                f'{type(gui_object).__name__} '
                f'pos=({gui_object.x},{gui_object.y}) size=({gui_object.width},{gui_object.height})'
            )
        return type(gui_object).__name__

    def _describe_incoming_widget_container(self) -> str:
        window = self._resolve_active_object()
        if window is None:
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def _describe_widget_container(self, widget: Widget) -> str:
        window = getattr(widget, 'window', None)
        if window is None or not isinstance(window, gWindow):
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def _find_widget_id_conflict(self, widget_id: str, candidate: Widget) -> Optional[Widget]:
        for widget in self.widgets:
            if widget is not candidate and widget.id == widget_id:
                return widget
        for window in self.windows:
            for widget in window.widgets:
                if widget is not candidate and widget.id == widget_id:
                    return widget
        return None

    def _is_registered_button_group(self, button: gButtonGroup) -> bool:
        # Construction registers group membership before final GUI attachment.
        if button.surface is None:
            return True
        if button in self.widgets:
            return True
        for window in self.windows:
            if button in window.widgets:
                return True
        return False

    def _is_registered_object(self, gui_object: TGuiObject) -> bool:
        if isinstance(gui_object, gWindow):
            return gui_object in self.windows
        if isinstance(gui_object, Widget):
            if gui_object in self.widgets:
                return True
            for window in self.windows:
                if gui_object in window.widgets:
                    return True
        return False

    def _resolve_active_object(self) -> Optional[gWindow]:
        if self._active_object is None:
            return None
        if self._active_object not in self.windows:
            self._active_object = None
            return None
        return self._active_object

    def _resolve_current_widget(self) -> Optional[Widget]:
        if self._current_widget is None:
            return None
        if not self._is_registered_object(self._current_widget):
            self._current_widget = None
            return None
        return self._current_widget

    def _resolve_locking_state(self) -> Optional[Widget]:
        if self.locking_object is None:
            if self.mouse_locked or self.lock_area_rect is not None or self.lock_point_pos is not None:
                self.mouse_locked = False
                self.mouse_point_locked = False
                self.lock_area_rect = None
                self.lock_point_pos = None
                self.lock_point_recenter_pending = False
                self.lock_point_tolerance_rect = None
            return None
        if not isinstance(self.locking_object, Widget):
            self.locking_object = None
            self.mouse_locked = False
            self.mouse_point_locked = False
            self.lock_area_rect = None
            self.lock_point_pos = None
            self.lock_point_recenter_pending = False
            self.lock_point_tolerance_rect = None
            return None
        if not self._is_registered_object(self.locking_object):
            self.locking_object = None
            self.mouse_locked = False
            self.mouse_point_locked = False
            self.lock_area_rect = None
            self.lock_point_pos = None
            self.lock_point_recenter_pending = False
            self.lock_point_tolerance_rect = None
            return None
        if self.lock_area_rect is None and self.lock_point_pos is None:
            self.locking_object = None
            self.mouse_locked = False
            self.mouse_point_locked = False
            self.lock_point_recenter_pending = False
            self.lock_point_tolerance_rect = None
            return None
        return self.locking_object
