import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
import logging
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Protocol, Tuple, TypeVar, Union, cast
from .scheduler import Timers, Scheduler
from .constants import GuiError, ArrowPosition, BaseEvent, ButtonStyle, Event, Orientation, InteractiveState
from .bitmapfactory import BitmapFactory
from .buttongroup_mediator import ButtonGroupMediator
from .event_delivery import EventDeliveryCoordinator
from .event_dispatcher import EventDispatcher
from .focus_state import FocusStateController
from .input_emitter import InputEventEmitter
from .input_state import DragStateController, LockStateController
from .layout_manager import LayoutManager
from .object_registry import GuiObjectRegistry
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

_logger = logging.getLogger(__name__)

def _noop() -> None:
    pass

def _noop_event(_: BaseEvent) -> None:
    pass

class _PristineContainer(Protocol):
    surface: Surface
    pristine: Optional[Surface]

class _ManagedTaskPanel:
    """GuiManager-owned bottom task panel container."""

    def __init__(
        self,
        gui: "GuiManager",
        height: int,
        x: int,
        reveal_pixels: int,
        auto_hide: bool,
        timer_interval: float,
        movement_step: int,
        backdrop: Optional[str],
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        if not isinstance(height, int) or height <= 0:
            raise GuiError(f'task_panel_height must be a positive int, got: {height}')
        if not isinstance(x, int):
            raise GuiError(f'task_panel_x must be an int, got: {x}')
        if not isinstance(reveal_pixels, int) or reveal_pixels < 1:
            raise GuiError(f'task_panel_reveal_pixels must be >= 1, got: {reveal_pixels}')
        if not isinstance(auto_hide, bool):
            raise GuiError('task_panel_auto_hide must be a bool')
        if not isinstance(movement_step, int) or movement_step <= 0:
            raise GuiError(f'task_panel_movement_step must be > 0, got: {movement_step}')
        if timer_interval <= 0:
            raise GuiError(f'task_panel_timer_interval must be > 0, got: {timer_interval}')
        screen_rect = gui.surface.get_rect()
        if x < 0 or x >= screen_rect.width:
            raise GuiError(f'task_panel_x must be in range [0, {screen_rect.width - 1}], got: {x}')
        width = screen_rect.width - x
        if reveal_pixels >= height:
            raise GuiError(f'task_panel_reveal_pixels must be < panel height ({height}), got: {reveal_pixels}')
        self.gui: "GuiManager" = gui
        self.x: int = x
        self.width: int = width
        self.height: int = height
        self.visible: bool = True
        self.widgets: List[Widget] = []
        self.surface: Surface = pygame.surface.Surface((self.width, self.height)).convert()
        self.pristine: Optional[Surface] = None
        self.reveal_pixels: int = reveal_pixels
        self.auto_hide: bool = auto_hide
        self.timer_interval: float = timer_interval
        self.movement_step: int = movement_step
        self._shown_y: int = screen_rect.height - self.height
        self._hidden_y: int = screen_rect.height - self.reveal_pixels
        self.y: int = self._hidden_y if self.auto_hide else self._shown_y
        self._hovered: bool = False
        self._timer_id: Tuple[str, int] = ('task-panel-motion', id(self))
        self._preamble: Callable[[], None] = preamble if callable(preamble) else _noop
        self._event_handler: Callable[[BaseEvent], None] = event_handler if callable(event_handler) else _noop_event
        self._postamble: Callable[[], None] = postamble if callable(postamble) else _noop
        self.backdrop: Optional[str] = backdrop
        if backdrop is None:
            frame = gFrame(gui, 'task_panel_frame', Rect(0, 0, self.width, self.height))
            frame.state = InteractiveState.Idle
            frame.surface = self.surface
            frame.draw()
            self.pristine = gui.copy_graphic_area(self.surface, self.surface.get_rect()).convert()
        else:
            gui.set_pristine(backdrop, self)
        gui.timers.add_timer(self._timer_id, self.timer_interval, self.animate)

    def dispose(self) -> None:
        self.gui.timers.remove_timer(self._timer_id)

    def run_preamble(self) -> None:
        self._preamble()

    def run_postamble(self) -> None:
        self._postamble()

    def handle_event(self, event: BaseEvent) -> None:
        self._event_handler(event)

    def get_rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)

    def refresh_targets(self) -> None:
        screen_rect = self.gui.surface.get_rect()
        self._shown_y = screen_rect.height - self.height
        self._hidden_y = screen_rect.height - self.reveal_pixels
        self._hovered = self.get_rect().collidepoint(self.gui.get_mouse_pos())

    def draw_background(self) -> None:
        if self.pristine is None:
            raise GuiError('task panel pristine is not initialized')
        self.gui.restore_pristine(self.surface.get_rect(), self)

    def animate(self) -> None:
        if not self.visible:
            return
        self.refresh_targets()
        target_y = self._hidden_y
        if not self.auto_hide or self._hovered:
            target_y = self._shown_y
        if self.y < target_y:
            self.y = min(target_y, self.y + self.movement_step)
        elif self.y > target_y:
            self.y = max(target_y, self.y - self.movement_step)

    def set_visible(self, visible: bool) -> None:
        if not isinstance(visible, bool):
            raise GuiError('task panel visibility must be a bool')
        self.visible = visible
        if visible:
            self.refresh_targets()

    def set_auto_hide(self, auto_hide: bool) -> None:
        if not isinstance(auto_hide, bool):
            raise GuiError('task panel auto_hide must be a bool')
        self.auto_hide = auto_hide
        if not auto_hide:
            self.refresh_targets()
            self.y = self._shown_y

    def set_reveal_pixels(self, reveal_pixels: int) -> None:
        if not isinstance(reveal_pixels, int):
            raise GuiError(f'task panel reveal_pixels must be an int, got: {reveal_pixels}')
        if reveal_pixels < 1:
            raise GuiError(f'task panel reveal_pixels must be >= 1, got: {reveal_pixels}')
        if reveal_pixels >= self.height:
            raise GuiError(f'task panel reveal_pixels must be < panel height ({self.height}), got: {reveal_pixels}')
        self.reveal_pixels = reveal_pixels
        self.refresh_targets()

    def set_movement_step(self, movement_step: int) -> None:
        if not isinstance(movement_step, int):
            raise GuiError(f'task panel movement_step must be an int, got: {movement_step}')
        if movement_step <= 0:
            raise GuiError(f'task panel movement_step must be > 0, got: {movement_step}')
        self.movement_step = movement_step

    def set_timer_interval(self, timer_interval: float) -> None:
        if timer_interval <= 0:
            raise GuiError(f'task panel timer_interval must be > 0, got: {timer_interval}')
        self.timer_interval = timer_interval
        self.gui.timers.remove_timer(self._timer_id)
        self.gui.timers.add_timer(self._timer_id, self.timer_interval, self.animate)

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
        self.task_panel: bool = kwargs.get('task_panel') is True

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
        return self.focus_state.resolve_current_widget()

    @current_widget.setter
    def current_widget(self, value):
        self.focus_state.set_current_widget(value)

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

    def __init__(
        self,
        surface: Surface,
        fonts: List[Tuple[str, str, int]],
        bitmap_factory: Optional[BitmapFactory] = None,
        task_panel_enabled: bool = True,
        event_getter: Optional[Callable[[], Iterable[PygameEvent]]] = None,
        mouse_get_pos: Optional[Callable[[], Tuple[int, int]]] = None,
        mouse_set_pos: Optional[Callable[[Tuple[int, int]], None]] = None,
        mouse_set_visible: Optional[Callable[[bool], None]] = None,
    ) -> None:
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
        self._event_getter: Callable[[], Iterable[PygameEvent]] = event_getter or pygame.event.get
        self._mouse_get_pos: Callable[[], Tuple[int, int]] = mouse_get_pos or pygame.mouse.get_pos
        self._mouse_set_pos: Callable[[Tuple[int, int]], None] = mouse_set_pos or pygame.mouse.set_pos
        self._mouse_set_visible: Callable[[bool], None] = mouse_set_visible or pygame.mouse.set_visible
        if not callable(self._event_getter):
            raise GuiError('event_getter must be callable')
        if not callable(self._mouse_get_pos):
            raise GuiError('mouse_get_pos must be callable')
        if not callable(self._mouse_set_pos):
            raise GuiError('mouse_set_pos must be callable')
        if not callable(self._mouse_set_visible):
            raise GuiError('mouse_set_visible must be callable')
        self.input_emitter: InputEventEmitter = InputEventEmitter(self)
        self.drag_state: DragStateController = DragStateController(self)
        self.focus_state: FocusStateController = FocusStateController(self)
        self.lock_state: LockStateController = LockStateController(self)
        self.event_dispatcher: EventDispatcher = EventDispatcher(self)
        self.layout_manager: LayoutManager = LayoutManager()
        self.renderer: Renderer = Renderer(self)
        self._mouse_set_visible(False)
        for name, filename, size in fonts:
            self._bitmap_factory.load_font(name, filename, size)
        self.surface: Surface = surface
        self.widgets: List[Widget] = []
        self._active_object: Optional[gWindow] = None
        self.windows: List[gWindow] = []
        self.dragging: bool = False
        self.dragging_window: Optional[gWindow] = None
        self.mouse_delta: Optional[Tuple[int, int]] = None
        self.mouse_pos: Tuple[int, int] = self._mouse_get_pos()
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
        self.object_registry: GuiObjectRegistry = GuiObjectRegistry(self)
        self.event_delivery: EventDeliveryCoordinator = EventDeliveryCoordinator(self)
        self.button_group_mediator: ButtonGroupMediator = ButtonGroupMediator(self.object_registry.is_registered_button_group)
        self._label_sequence: int = 0
        self._screen_preamble: Callable[[], None] = _noop
        self._screen_event_handler: Callable[[BaseEvent], None] = _noop_event
        self._screen_postamble: Callable[[], None] = _noop
        self._task_owner_by_id: Dict[Hashable, gWindow] = {}
        self._task_panel_capture: bool = False
        self.task_panel: Optional[_ManagedTaskPanel] = None
        self.point_lock_recenter_rect: Rect = self._build_centered_recenter_rect()
        self.point_lock_tolerance_size: Tuple[int, int] = (
            max(1, self.point_lock_recenter_rect.width),
            max(1, self.point_lock_recenter_rect.height),
        )
        if not isinstance(task_panel_enabled, bool):
            raise GuiError('task_panel_enabled must be a bool')
        if task_panel_enabled:
            self.configure_task_panel()

    def configure_task_panel(
        self,
        *,
        height: int = 38,
        x: int = 0,
        reveal_pixels: int = 4,
        auto_hide: bool = True,
        timer_interval: float = 16.0,
        movement_step: int = 4,
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        if type(height) is not int or height <= 0:
            raise GuiError(f'task_panel_height must be a positive int, got: {height}')
        if type(x) is not int:
            raise GuiError(f'task_panel_x must be an int, got: {x}')
        if type(reveal_pixels) is not int or reveal_pixels < 1:
            raise GuiError(f'task_panel_reveal_pixels must be >= 1, got: {reveal_pixels}')
        if type(auto_hide) is not bool:
            raise GuiError('task_panel_auto_hide must be a bool')
        if type(movement_step) is not int or movement_step <= 0:
            raise GuiError(f'task_panel_movement_step must be > 0, got: {movement_step}')
        if isinstance(timer_interval, bool) or not isinstance(timer_interval, (int, float)) or timer_interval <= 0:
            raise GuiError(f'task_panel_timer_interval must be > 0, got: {timer_interval}')
        if backdrop is not None and (not isinstance(backdrop, str) or backdrop == ''):
            raise GuiError(f'task_panel_backdrop must be a non-empty string or None, got: {backdrop!r}')
        if preamble is not None and not callable(preamble):
            raise GuiError('task panel preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('task panel event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('task panel postamble must be callable or None')
        old_panel = self.task_panel
        existing_widgets: List[Widget] = []
        existing_visible = True
        if old_panel is not None:
            existing_widgets = list(old_panel.widgets)
            existing_visible = old_panel.visible
        panel = _ManagedTaskPanel(
            self,
            height,
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
        if old_panel is not None:
            old_panel.dispose()
        if existing_widgets:
            panel.widgets = existing_widgets
            for widget in panel.widgets:
                widget.window = cast(Any, panel)
                widget.surface = panel.surface
        if old_panel is not None:
            panel.set_visible(existing_visible)
            if not existing_visible:
                self._task_panel_capture = False
        self.task_panel = panel

    def run_postamble(self) -> None:
        for window in self.windows:
            if window.visible:
                window.run_postamble()
        if self.task_panel is not None and self.task_panel.visible:
            self.task_panel.run_postamble()
        self._screen_postamble()

    def run_preamble(self) -> None:
        self._screen_preamble()
        for window in self.windows:
            if window.visible:
                window.run_preamble()
        if self.task_panel is not None and self.task_panel.visible:
            self.task_panel.run_preamble()

    def begin_task_panel(self) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self._task_panel_capture = True
        self._active_object = None

    def end_task_panel(self) -> None:
        self._task_panel_capture = False

    def set_task_panel_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        if preamble is not None and not callable(preamble):
            raise GuiError('task panel preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('task panel event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('task panel postamble must be callable or None')
        self.task_panel._preamble = preamble if preamble is not None else _noop
        self.task_panel._event_handler = event_handler if event_handler is not None else _noop_event
        self.task_panel._postamble = postamble if postamble is not None else _noop

    def set_task_panel_enabled(self, enabled: bool) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.task_panel.set_visible(enabled)
        if not enabled:
            self._task_panel_capture = False

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.task_panel.set_auto_hide(auto_hide)

    def set_task_panel_reveal_pixels(self, reveal_pixels: int) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.task_panel.set_reveal_pixels(reveal_pixels)

    def set_task_panel_movement_step(self, movement_step: int) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.task_panel.set_movement_step(movement_step)

    def set_task_panel_timer_interval(self, timer_interval: float) -> None:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.task_panel.set_timer_interval(timer_interval)

    def read_task_panel_settings(self) -> Dict[str, object]:
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        panel = self.task_panel
        return {
            'enabled': panel.visible,
            'auto_hide': panel.auto_hide,
            'reveal_pixels': panel.reveal_pixels,
            'movement_step': panel.movement_step,
            'timer_interval': panel.timer_interval,
            'rect': panel.get_rect(),
        }

    def get_mouse_pos(self) -> Tuple[int, int]:
        return self.lock_area(self.mouse_pos)

    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget and attach container-specific state."""
        return self.object_registry.register(gui_object)

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
        self.lock_state.set_area(locking_object, area)

    def set_lock_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        """Lock mouse-relative input and recenter hardware pointer when it leaves a broad center area."""
        if locking_object is None:
            self.set_lock_area(None)
            return
        self.lock_state.set_point(locking_object, point)

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
        self.event_delivery.dispatch_event(event)

    def event(self, event_type: Event, **kwargs: object) -> GuiEvent:
        if event_type in (Event.MouseButtonUp, Event.MouseButtonDown, Event.MouseMotion):
            kwargs.setdefault('pos', self.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self) -> Iterable[GuiEvent]:
        for raw_event in self._event_getter():
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

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        if window is not None and window not in self.windows and window is not self.task_panel:
            window = None
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.lock_area((x + wx, y + wy))
        return self.lock_area(point)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        if window is not None and window not in self.windows and window is not self.task_panel:
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
        self.lock_state.enforce_point_lock(hardware_position)

    def _set_physical_mouse_pos(self, pos: Tuple[int, int]) -> None:
        try:
            self._mouse_set_pos(pos)
        except Exception as exc:
            _logger.debug('mouse_set_pos failed: %s: %s', type(exc).__name__, exc)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        return self.lock_state.clamp_position(position)

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
        self.focus_state.update_focus(new_hover)

    def update_active_window(self) -> None:
        self.focus_state.update_active_window()

    def _resolve_task_event_owner(self, event: BaseEvent) -> Optional[gWindow]:
        return self.event_delivery.resolve_task_event_owner(event)

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
        return self.object_registry.describe_incoming_widget_container()

    def _describe_widget_container(self, widget: Widget) -> str:
        return self.object_registry.describe_widget_container(widget)

    def _find_widget_id_conflict(self, widget_id: str, candidate: Widget) -> Optional[Widget]:
        return self.object_registry.find_widget_id_conflict(widget_id, candidate)

    def _is_registered_button_group(self, button: gButtonGroup) -> bool:
        return self.object_registry.is_registered_button_group(button)

    def _is_registered_object(self, gui_object: TGuiObject) -> bool:
        return self.object_registry.is_registered_object(gui_object)

    def _resolve_active_object(self) -> Optional[gWindow]:
        return self.object_registry.resolve_active_object()

    def _resolve_current_widget(self) -> Optional[Widget]:
        return self.focus_state.resolve_current_widget()

    def _resolve_locking_state(self) -> Optional[Widget]:
        return self.lock_state.resolve()
