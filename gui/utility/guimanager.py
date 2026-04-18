import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
import logging
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Protocol, Tuple, TypeVar, Union, cast, TYPE_CHECKING
from .scheduler import Timers, Scheduler
from .constants import GuiError, ArrowPosition, BaseEvent, ButtonStyle, Event, Orientation
from .bitmapfactory import BitmapFactory
from .buttongroup_mediator import ButtonGroupMediator
from .dispatch_bridge_coordinator import DispatchBridgeCoordinator
from .event_delivery import EventDeliveryCoordinator
from .event_dispatcher import EventDispatcher
from .focus_state import FocusStateController
from .graphics_coordinator import GraphicsCoordinator
from .input_emitter import InputEventEmitter
from .input_event_coordinator import InputEventCoordinator
from .input_state import DragStateController, LockStateController
from .layout_coordinator import LayoutCoordinator
from .layout_manager import LayoutManager
from .lifecycle import LifecycleCoordinator, ScreenLifecycle
from .lock_flow_coordinator import LockFlowCoordinator
from .object_registry import GuiObjectRegistry
from .pointer_coordinator import PointerCoordinator
from .render_coordinator import RenderCoordinator
from .renderer import Renderer
from .task_panel_config_coordinator import TaskPanelConfigCoordinator
from .ui_factory import GuiUiFactory
from .widget_state_coordinator import WidgetStateCoordinator
from .workspace_coordinator import WorkspaceCoordinator
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

if TYPE_CHECKING:
    from .gui_event import GuiEvent
    from .task_panel import _ManagedTaskPanel

def _noop() -> None:
    pass

def _noop_event(_: BaseEvent) -> None:
    pass

class _PristineContainer(Protocol):
    surface: Surface
    pristine: Optional[Surface]

TGuiObject = TypeVar("TGuiObject", gWindow, Widget)

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
        return self.ui_factory.ArrowBox(id, rect, direction, on_activate)

    def Button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> gButton:
        return self.ui_factory.Button(id, rect, style, text, on_activate)

    def ButtonGroup(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> gButtonGroup:
        return self.ui_factory.ButtonGroup(group, id, rect, style, text)

    def Canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> gCanvas:
        return self.ui_factory.Canvas(id, rect, backdrop, on_activate, automatic_pristine)

    def Frame(self, id: str, rect: Rect) -> gFrame:
        return self.ui_factory.Frame(id, rect)

    def Image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> gImage:
        return self.ui_factory.Image(id, rect, image, automatic_pristine, scale)

    def Label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> gLabel:
        return self.ui_factory.Label(position, text, shadow, id)

    def Scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> gScrollbar:
        return self.ui_factory.Scrollbar(id, overall_rect, horizontal, style, params)

    def Toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> gToggle:
        return self.ui_factory.Toggle(id, rect, style, pushed, pressed_text, raised_text)

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
        return self.ui_factory.Window(title, pos, size, backdrop, preamble, event_handler, postamble)

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
        self.ui_factory: GuiUiFactory = GuiUiFactory(self)
        self.object_registry: GuiObjectRegistry = GuiObjectRegistry(self)
        self.dispatch_bridge: DispatchBridgeCoordinator = DispatchBridgeCoordinator(self)
        self.event_delivery: EventDeliveryCoordinator = EventDeliveryCoordinator(self)
        self.event_input: InputEventCoordinator = InputEventCoordinator(self)
        self.graphics: GraphicsCoordinator = GraphicsCoordinator(self)
        self.layout: LayoutCoordinator = LayoutCoordinator(self)
        self.lifecycle: LifecycleCoordinator = LifecycleCoordinator(self)
        self.lock_flow: LockFlowCoordinator = LockFlowCoordinator(self)
        self.pointer: PointerCoordinator = PointerCoordinator(self)
        self.render_flow: RenderCoordinator = RenderCoordinator(self)
        self.task_panel_config: TaskPanelConfigCoordinator = TaskPanelConfigCoordinator(self)
        self.widget_state: WidgetStateCoordinator = WidgetStateCoordinator(self)
        self.workspace: WorkspaceCoordinator = WorkspaceCoordinator(self)
        self.button_group_mediator: ButtonGroupMediator = ButtonGroupMediator(self.object_registry.is_registered_button_group)
        self.screen_lifecycle: ScreenLifecycle = ScreenLifecycle()
        self._task_owner_by_id: Dict[Hashable, gWindow] = {}
        self._task_panel_capture: bool = False
        self.task_panel: Optional["_ManagedTaskPanel"] = None
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
        self.task_panel_config.configure_task_panel(
            height=height,
            x=x,
            reveal_pixels=reveal_pixels,
            auto_hide=auto_hide,
            timer_interval=timer_interval,
            movement_step=movement_step,
            backdrop=backdrop,
            preamble=preamble,
            event_handler=event_handler,
            postamble=postamble,
        )

    def run_postamble(self) -> None:
        self.lifecycle.run_postamble()

    def run_preamble(self) -> None:
        self.lifecycle.run_preamble()

    def begin_task_panel(self) -> None:
        self.workspace.begin_task_panel()

    def end_task_panel(self) -> None:
        self.workspace.end_task_panel()

    def set_task_panel_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        self.lifecycle.set_task_panel_lifecycle(preamble, event_handler, postamble)

    def set_task_panel_enabled(self, enabled: bool) -> None:
        self.workspace.set_task_panel_enabled(enabled)

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        self.workspace.set_task_panel_auto_hide(auto_hide)

    def set_task_panel_reveal_pixels(self, reveal_pixels: int) -> None:
        self.workspace.set_task_panel_reveal_pixels(reveal_pixels)

    def set_task_panel_movement_step(self, movement_step: int) -> None:
        self.workspace.set_task_panel_movement_step(movement_step)

    def set_task_panel_timer_interval(self, timer_interval: float) -> None:
        self.workspace.set_task_panel_timer_interval(timer_interval)

    def read_task_panel_settings(self) -> Dict[str, object]:
        return self.workspace.read_task_panel_settings()

    def get_mouse_pos(self) -> Tuple[int, int]:
        return self.pointer.get_mouse_pos()

    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget and attach container-specific state."""
        return self.object_registry.register(gui_object)

    def clear_button_groups(self) -> None:
        self.button_group_mediator.clear()

    def clear_task_owners_for_window(self, window: gWindow) -> None:
        self.event_delivery.clear_task_owners_for_window(window)

    def hide_widgets(self, *widgets: Widget) -> None:
        self.widget_state.hide_widgets(*widgets)

    def lower_window(self, window: gWindow) -> None:
        self.workspace.lower_window(window)

    def raise_window(self, window: gWindow) -> None:
        self.workspace.raise_window(window)

    def set_cursor(self, name: str) -> None:
        """Set custom cursor from a named cursor loaded via BitmapFactory.load_cursor."""
        self.pointer.set_cursor(name)

    def set_grid_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        """Configure grid cell sizing used by gridded."""
        self.layout.set_grid_properties(anchor, width, height, spacing, use_rect)

    def set_lock_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        """Clamp mouse motion to area until released."""
        self.lock_flow.set_lock_area(locking_object, area)

    def set_lock_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        """Lock mouse-relative input and recenter hardware pointer when it leaves a broad center area."""
        self.lock_flow.set_lock_point(locking_object, point)

    def set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        self.pointer.set_mouse_pos(pos, update_physical_coords)

    def set_pristine(self, image: str, obj: Optional[_PristineContainer] = None) -> None:
        """Load a backdrop image, scale it to target surface, and cache pristine copy."""
        self.graphics.set_pristine(image, obj)

    def set_screen_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        self.lifecycle.set_screen_lifecycle(preamble, event_handler, postamble)

    def set_task_owner(self, task_id: Hashable, window: Optional[gWindow]) -> None:
        self.event_delivery.set_task_owner(task_id, window)

    def set_task_owners(self, window: Optional[gWindow], *task_ids: Hashable) -> None:
        self.event_delivery.set_task_owners(window, *task_ids)

    def show_widgets(self, *widgets: Widget) -> None:
        self.widget_state.show_widgets(*widgets)

    def dispatch_event(self, event: BaseEvent) -> None:
        self.event_delivery.dispatch_event(event)

    def event(self, event_type: Event, **kwargs: object) -> "GuiEvent":
        return self.event_input.event(event_type, **kwargs)

    def events(self) -> Iterable["GuiEvent"]:
        yield from self.event_input.events()

    def handle_event(self, event: PygameEvent) -> "GuiEvent":
        return self.dispatch_bridge.handle_event(event)

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional[gWindow] = None) -> bool:
        """Run widget handler and execute activation callbacks when present."""
        return self.widget_state.handle_widget(widget, event, window)

    def draw_gui(self) -> None:
        self.render_flow.draw_gui()

    def undraw_gui(self) -> None:
        self.render_flow.undraw_gui()

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        return self.pointer.convert_to_screen(point, window)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        return self.pointer.convert_to_window(point, window)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        return self.layout.gridded(x, y)

    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        """Return a surface copy of rect from surface."""
        return self.graphics.copy_graphic_area(surface, rect, flags)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Recenters pointer only when it exits the configured broad center region."""
        self.lock_flow.enforce_point_lock(hardware_position)

    def _set_physical_mouse_pos(self, pos: Tuple[int, int]) -> None:
        try:
            self._mouse_set_pos(pos)
        except Exception as exc:
            _logger.debug('mouse_set_pos failed: %s: %s', type(exc).__name__, exc)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        return self.lock_flow.lock_area(position)

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional[_PristineContainer] = None) -> None:
        """Restore a region from a previously cached pristine bitmap."""
        self.graphics.restore_pristine(area, obj)

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
