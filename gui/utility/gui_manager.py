from __future__ import annotations

import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
import logging
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, TypeVar, Union, cast, TYPE_CHECKING
from .scheduler import Timers, Scheduler
from .events import GuiError, ArrowPosition, BaseEvent, ButtonStyle, Event, Orientation
from .graphics.widget_graphics_factory import WidgetGraphicsFactory
from .buttongroup_mediator import ButtonGroupMediator
from .dispatch_bridge_coordinator import DispatchBridgeCoordinator
from .event_delivery import EventDeliveryCoordinator
from .event_dispatcher import EventDispatcher
from .focus_state import FocusStateController
from .focus_state_model import FocusState
from .drag_state_model import DragState
from .graphics_coordinator import GraphicsCoordinator
from .input_emitter import InputEventEmitter
from .input_event_coordinator import InputEventCoordinator
from .input_providers import InputProviders
from .input.drag_state_controller import DragStateController
from .input.lock_state_controller import LockStateController
from .layout_coordinator import LayoutCoordinator
from .layout_manager import LayoutManager
from .lifecycle import LifecycleCoordinator, ScreenLifecycle
from .lock_flow_coordinator import LockFlowCoordinator
from .lock_state_model import LockState
from .object_registry import GuiObjectRegistry
from .pointer_coordinator import PointerCoordinator
from .render_coordinator import RenderCoordinator
from .renderer import Renderer
from .task_panel_config_coordinator import TaskPanelConfigCoordinator
from .ui_factory import GuiUiFactory
from .widget_state_coordinator import WidgetStateCoordinator
from .workspace_coordinator import WorkspaceCoordinator
from .workspace_state import WorkspaceState
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

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .gui_event import GuiEvent
    from .task_panel import _ManagedTaskPanel

TGuiObject = TypeVar("TGuiObject", Window, Widget)

class GuiManager:
    """Owns widgets/windows, input routing, and rendering for one GUI context."""

    @staticmethod
    def _normalize_font_registry(fonts: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
        """Internal helper for normalize font registry."""
        registry = list(fonts)
        if not registry:
            raise GuiError('fonts registry cannot be empty')
        for font_entry in registry:
            if not isinstance(font_entry, tuple) or len(font_entry) != 3:
                raise GuiError('each font entry must be a tuple of (name, filename, size)')
            name, filename, size = font_entry
            if not isinstance(name, str) or not name:
                raise GuiError(f'font name must be a non-empty string, got: {name}')
            if not isinstance(filename, str) or not filename:
                raise GuiError(f'font filename must be a non-empty string, got: {filename}')
            if not isinstance(size, int) or size <= 0:
                raise GuiError(f'font size must be a positive integer, got: {size}')
        return registry

    def build_font_registry(self, **fonts: Tuple[str, int]) -> List[Tuple[str, str, int]]:
        """Build a validated font registry from keyword entries.

        Example:
            gui.build_font_registry(
                titlebar=('Ubuntu-B.ttf', 14),
                normal=('Gimbot.ttf', 16),
            )
        """
        if not fonts:
            raise GuiError('fonts registry cannot be empty')
        registry: List[Tuple[str, str, int]] = []
        for name, font_def in fonts.items():
            if not isinstance(name, str) or not name:
                raise GuiError(f'font name must be a non-empty string, got: {name}')
            if not isinstance(font_def, tuple) or len(font_def) != 2:
                raise GuiError(f'font entry for {name} must be a tuple of (filename, size)')
            filename, size = font_def
            if not isinstance(filename, str) or not filename:
                raise GuiError(f'font filename must be a non-empty string, got: {filename}')
            if not isinstance(size, int) or size <= 0:
                raise GuiError(f'font size must be a positive integer, got: {size}')
            registry.append((name, filename, size))
        return registry

    def configure_fonts(self, **fonts: Tuple[str, int]) -> List[Tuple[str, str, int]]:
        """Build and load a font registry in one call.

        Returns the normalized registry as ``(name, filename, size)`` tuples.
        """
        registry = self.build_font_registry(**fonts)
        self.load_fonts(registry)
        return registry

    def load_fonts(self, fonts: Iterable[Tuple[str, str, int]]) -> None:
        """Load or reload fonts into this manager's graphics factory."""
        for name, filename, size in self._normalize_font_registry(fonts):
            self._graphics_factory.load_font(name, filename, size)

    @property
    def graphics_factory(self):
        """Run graphics factory and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._graphics_factory

    @property
    def buffered(self):
        """Run buffered and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._buffered

    @buffered.setter
    def buffered(self, value):
        """Run buffered and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        if not isinstance(value, bool):
            raise GuiError('buffered must be a bool')
        self._buffered = value

    @property
    def current_widget(self):
        """Run current widget and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.focus_state.current_widget

    @current_widget.setter
    def current_widget(self, value):
        """Run current widget and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.focus_state.current_widget = value

    @property
    def scheduler(self):
        """Run scheduler and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._scheduler

    @property
    def dragging(self) -> bool:
        """Run dragging and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._drag_state.dragging

    @dragging.setter
    def dragging(self, value: bool) -> None:
        """Run dragging and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._drag_state.dragging = value

    @property
    def dragging_window(self) -> Optional[Window]:
        """Run dragging window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._drag_state.dragging_window

    @dragging_window.setter
    def dragging_window(self, value: Optional[Window]) -> None:
        """Run dragging window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._drag_state.dragging_window = value

    @property
    def mouse_delta(self) -> Optional[Tuple[int, int]]:
        """Run mouse delta and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._drag_state.mouse_delta

    @mouse_delta.setter
    def mouse_delta(self, value: Optional[Tuple[int, int]]) -> None:
        """Run mouse delta and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._drag_state.mouse_delta = value

    @property
    def locking_object(self) -> Optional[Widget]:
        """Run locking object and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.locking_object

    @locking_object.setter
    def locking_object(self, value: Optional[Widget]) -> None:
        """Run locking object and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.locking_object = value

    @property
    def mouse_locked(self) -> bool:
        """Run mouse locked and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.mouse_locked

    @mouse_locked.setter
    def mouse_locked(self, value: bool) -> None:
        """Run mouse locked and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.mouse_locked = value

    @property
    def mouse_point_locked(self) -> bool:
        """Run mouse point locked and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.mouse_point_locked

    @mouse_point_locked.setter
    def mouse_point_locked(self, value: bool) -> None:
        """Run mouse point locked and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.mouse_point_locked = value

    @property
    def lock_area_rect(self) -> Optional[Rect]:
        """Run lock area rect and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.lock_area_rect

    @lock_area_rect.setter
    def lock_area_rect(self, value: Optional[Rect]) -> None:
        """Run lock area rect and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.lock_area_rect = value

    @property
    def lock_point_pos(self) -> Optional[Tuple[int, int]]:
        """Run lock point pos and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.lock_point_pos

    @lock_point_pos.setter
    def lock_point_pos(self, value: Optional[Tuple[int, int]]) -> None:
        """Run lock point pos and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.lock_point_pos = value

    @property
    def lock_point_recenter_pending(self) -> bool:
        """Run lock point recenter pending and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.lock_point_recenter_pending

    @lock_point_recenter_pending.setter
    def lock_point_recenter_pending(self, value: bool) -> None:
        """Run lock point recenter pending and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.lock_point_recenter_pending = value

    @property
    def lock_point_tolerance_rect(self) -> Optional[Rect]:
        """Run lock point tolerance rect and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._lock_state.lock_point_tolerance_rect

    @lock_point_tolerance_rect.setter
    def lock_point_tolerance_rect(self, value: Optional[Rect]) -> None:
        """Run lock point tolerance rect and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self._lock_state.lock_point_tolerance_rect = value

    # widgets
    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox:
        """Run arrow box and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.arrow_box(id, rect, direction, on_activate)

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button:
        """Run button and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.button(id, rect, style, text, on_activate)

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        """Run button group and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.button_group(group, id, rect, style, text)

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        """Run canvas and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.canvas(id, rect, backdrop, on_activate, automatic_pristine)

    def frame(self, id: str, rect: Rect) -> Frame:
        """Run frame and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.frame(id, rect)

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        """Run image and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.image(id, rect, image, automatic_pristine, scale)

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label:
        """Run label and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.label(position, text, shadow, id)

    def scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> Scrollbar:
        """Run scrollbar and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.scrollbar(id, overall_rect, horizontal, style, params)

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        """Run toggle and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.toggle(id, rect, style, pushed, pressed_text, raised_text)

    def window(
        self,
        title: str,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> Window:
        """Run window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.ui_factory.window(title, pos, size, backdrop, preamble, event_handler, postamble)

    def __init__(
        self,
        surface: Surface,
        fonts: Optional[Iterable[Tuple[str, str, int]]] = None,
        graphics_factory: Optional[WidgetGraphicsFactory] = None,
        task_panel_enabled: bool = True,
        event_getter: Optional[Callable[[], Iterable[PygameEvent]]] = None,
        mouse_get_pos: Optional[Callable[[], Tuple[int, int]]] = None,
        mouse_set_pos: Optional[Callable[[Tuple[int, int]], None]] = None,
        mouse_set_visible: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Create a GUI manager bound to a target surface and font registry."""
        if surface is None:
            raise GuiError('surface cannot be None')
        normalized_fonts: Optional[List[Tuple[str, str, int]]] = None
        if fonts is not None:
            normalized_fonts = self._normalize_font_registry(fonts)
        self._graphics_factory: WidgetGraphicsFactory = graphics_factory or WidgetGraphicsFactory()
        resolved_event_getter = event_getter or pygame.event.get
        resolved_mouse_get_pos = mouse_get_pos or pygame.mouse.get_pos
        resolved_mouse_set_pos = mouse_set_pos or pygame.mouse.set_pos
        resolved_mouse_set_visible = mouse_set_visible or pygame.mouse.set_visible
        if not callable(resolved_event_getter):
            raise GuiError('event_getter must be callable')
        if not callable(resolved_mouse_get_pos):
            raise GuiError('mouse_get_pos must be callable')
        if not callable(resolved_mouse_set_pos):
            raise GuiError('mouse_set_pos must be callable')
        if not callable(resolved_mouse_set_visible):
            raise GuiError('mouse_set_visible must be callable')
        self.input_providers: InputProviders = InputProviders(
            resolved_event_getter,
            resolved_mouse_get_pos,
            resolved_mouse_set_pos,
            resolved_mouse_set_visible,
        )
        self._drag_state: DragState = DragState()
        self._lock_state: LockState = LockState()
        self.input_emitter: InputEventEmitter = InputEventEmitter(self)
        self.drag_state: DragStateController = DragStateController(self)
        self.focus_state: FocusStateController = FocusStateController(self)
        self.lock_state: LockStateController = LockStateController(self)
        self.event_dispatcher: EventDispatcher = EventDispatcher(self)
        self.layout_manager: LayoutManager = LayoutManager()
        self.renderer: Renderer = Renderer(self)
        self.input_providers.mouse_set_visible(False)
        if normalized_fonts is not None:
            self.load_fonts(normalized_fonts)
        self.surface: Surface = surface
        self.widgets: List[Widget] = []
        self.workspace_state: WorkspaceState = WorkspaceState()
        self.windows: List[Window] = []
        self.mouse_pos: Tuple[int, int] = self.input_providers.mouse_get_pos()
        self.cursor_image: Optional[Surface] = None
        self.cursor_hotspot: Optional[Tuple[int, int]] = None
        self.cursor_rect: Optional[Rect] = None
        self.active_window: Optional[Window] = None
        self.focus_state_data: FocusState = FocusState()
        self.pristine: Optional[Surface] = None
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
        """Run configure task panel and return the resulting value.

        This method encapsulates the main behavior for this operation."""
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
        """Run run postamble and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.lifecycle.run_postamble()

    def run_preamble(self) -> None:
        """Run run preamble and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.lifecycle.run_preamble()

    def begin_task_panel(self) -> None:
        """Run begin task panel and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.begin_task_panel()

    def end_task_panel(self) -> None:
        """Run end task panel and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.end_task_panel()

    def set_task_panel_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Run set task panel lifecycle and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.lifecycle.set_task_panel_lifecycle(preamble, event_handler, postamble)

    def set_task_panel_enabled(self, enabled: bool) -> None:
        """Run set task panel enabled and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.set_task_panel_enabled(enabled)

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        """Run set task panel auto hide and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.set_task_panel_auto_hide(auto_hide)

    def set_task_panel_reveal_pixels(self, reveal_pixels: int) -> None:
        """Run set task panel reveal pixels and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.set_task_panel_reveal_pixels(reveal_pixels)

    def set_task_panel_movement_step(self, movement_step: int) -> None:
        """Run set task panel movement step and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.set_task_panel_movement_step(movement_step)

    def set_task_panel_timer_interval(self, timer_interval: float) -> None:
        """Run set task panel timer interval and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.set_task_panel_timer_interval(timer_interval)

    def read_task_panel_settings(self) -> Dict[str, object]:
        """Run read task panel settings and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.workspace.read_task_panel_settings()

    def get_mouse_pos(self) -> Tuple[int, int]:
        """Run get mouse pos and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.pointer.get_mouse_pos()

    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget and attach container-specific state."""
        return self.object_registry.register(gui_object)

    def clear_button_groups(self) -> None:
        """Run clear button groups and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.button_group_mediator.clear()

    def clear_task_owners_for_window(self, window: Window) -> None:
        """Run clear task owners for window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.event_delivery.clear_task_owners_for_window(window)

    def hide_widgets(self, *widgets: Widget) -> None:
        """Run hide widgets and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.widget_state.hide_widgets(*widgets)

    def lower_window(self, window: Window) -> None:
        """Run lower window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.lower_window(window)

    def raise_window(self, window: Window) -> None:
        """Run raise window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.workspace.raise_window(window)

    def set_cursor(self, name: str) -> None:
        """Set custom cursor from a named cursor loaded via WidgetGraphicsFactory.register_cursor."""
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
        """Run set mouse pos and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.pointer.set_mouse_pos(pos, update_physical_coords)

    def set_pristine(self, image: str, obj: Optional[Any] = None) -> None:
        """Load a backdrop image, scale it to target surface, and cache pristine copy."""
        self.graphics.set_pristine(image, obj)

    def set_screen_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Run set screen lifecycle and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.lifecycle.set_screen_lifecycle(preamble, event_handler, postamble)

    def set_task_owner(self, task_id: Hashable, window: Optional[Window]) -> None:
        """Run set task owner and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.event_delivery.set_task_owner(task_id, window)

    def set_task_owners(self, window: Optional[Window], *task_ids: Hashable) -> None:
        """Run set task owners and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.event_delivery.set_task_owners(window, *task_ids)

    def show_widgets(self, *widgets: Widget) -> None:
        """Run show widgets and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.widget_state.show_widgets(*widgets)

    def dispatch_event(self, event: BaseEvent) -> None:
        """Run dispatch event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.event_delivery.dispatch_event(event)

    def event(self, event_type: Event, **kwargs: object) -> "GuiEvent":
        """Run event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.event_input.event(event_type, **kwargs)

    def events(self) -> Iterable["GuiEvent"]:
        """Run events and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        yield from self.event_input.events()

    def handle_event(self, event: PygameEvent) -> "GuiEvent":
        """Run handle event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.dispatch_bridge.handle_event(event)

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional[Window] = None) -> bool:
        """Run widget handler and execute activation callbacks when present."""
        return self.widget_state.handle_widget(widget, event, window)

    def draw_gui(self) -> None:
        """Run draw gui and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.render_flow.draw_gui()

    def undraw_gui(self) -> None:
        """Run undraw gui and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.render_flow.undraw_gui()

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Run convert to screen and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.pointer.convert_to_screen(point, window)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Run convert to window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.pointer.convert_to_window(point, window)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        """Run gridded and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.layout.gridded(x, y)

    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        """Return a surface copy of rect from surface."""
        return self.graphics.copy_graphic_area(surface, rect, flags)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Recenters pointer only when it exits the configured broad center region."""
        self.lock_flow.enforce_point_lock(hardware_position)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Run lock area and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.lock_flow.lock_area(position)

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional["_PristineContainer"] = None) -> None:
        """Restore a region from a previously cached pristine bitmap."""
        self.graphics.restore_pristine(area, obj)

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        """Run update focus and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.focus_state.update_focus(new_hover)

    def update_active_window(self) -> None:
        """Run update active window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.focus_state.update_active_window()

    def _build_centered_recenter_rect(self, coverage: float = 0.8) -> Rect:
        """Internal helper for build centered recenter rect."""
        if coverage <= 0.0 or coverage > 1.0:
            raise GuiError(f'coverage must be in the range (0, 1], got: {coverage}')
        surface_rect = self.surface.get_rect()
        width = max(1, int(surface_rect.width * coverage))
        height = max(1, int(surface_rect.height * coverage))
        centered = Rect(0, 0, width, height)
        centered.center = surface_rect.center
        return centered
