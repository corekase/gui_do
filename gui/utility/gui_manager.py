from __future__ import annotations

import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
import logging
from typing import Any, Callable, Dict, Hashable, Iterable, List, Literal, Optional, Sequence, Tuple, TypeVar, Union, cast, TYPE_CHECKING
from .scheduler import Timers, Scheduler
from .events import GuiError, ArrowPosition, BaseEvent, ButtonStyle, Event, Orientation
from .graphics.widget_graphics_factory import WidgetGraphicsFactory
from .intermediates.buttongroup_mediator import ButtonGroupMediator
from .coordinators.event_delivery import EventDeliveryCoordinator
from .event_dispatcher import EventDispatcher
from .focus_state import FocusStateController
from .gui_utils.focus_state_model import FocusState
from .gui_utils.drag_state_model import DragState
from .coordinators.graphics_coordinator import GraphicsCoordinator
from .input.input_emitter import InputEventEmitter
from .coordinators.input_event_coordinator import InputEventCoordinator
from .gui_utils.input_providers import InputProviders
from .input.drag_state_controller import DragStateController
from .input.lock_state_controller import LockStateController
from .coordinators.layout_coordinator import LayoutCoordinator
from .layout_manager import LayoutManager
from .lifecycle import LifecycleCoordinator, ScreenLifecycle
from .coordinators.lock_flow_coordinator import LockFlowCoordinator
from .gui_utils.lock_state_model import LockState
from .object_registry import GuiObjectRegistry
from .coordinators.pointer_coordinator import PointerCoordinator
from .coordinators.window_tiling_coordinator import WindowTilingCoordinator
from .renderer import Renderer
from .ui_factory import GuiUiFactory
from .coordinators.widget_state_coordinator import WidgetStateCoordinator
from .coordinators.workspace_coordinator import WorkspaceCoordinator
from .gui_utils.workspace_state import WorkspaceState
from .gui_utils.task_panel_settings import TaskPanelSettings
from .gui_utils.mouse_input_state import MouseInputState
from .intermediates.widget import Widget
from ..widgets.window import Window
from ..widgets.button import Button
from ..widgets.label import Label
from ..widgets.canvas import Canvas
from ..widgets.image import Image
from ..widgets.slider import Slider
from ..widgets.scrollbar import Scrollbar
from ..widgets.toggle import Toggle
from ..widgets.arrowbox import ArrowBox
from ..widgets.buttongroup import ButtonGroup
from ..widgets.frame import Frame

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .gui_utils.gui_event import GuiEvent
    from .gui_utils.task_panel import _ManagedTaskPanel

TGuiObject = TypeVar("TGuiObject", Window, Widget)
ScrollbarStyle = Literal['skip', 'split', 'near', 'far']

class GuiManager:
    """Owns widgets/windows, input routing, and rendering for one GUI context."""

    _SCROLLBAR_STYLE_MAP = {
        'skip': ArrowPosition.Skip,
        'split': ArrowPosition.Split,
        'near': ArrowPosition.Near,
        'far': ArrowPosition.Far,
    }

    @staticmethod
    def _validate_font_entry(name: str, filename: str, size: int) -> None:
        """Validate one normalized ``(name, filename, size)`` font entry."""
        if not isinstance(name, str) or not name:
            raise GuiError(f'font name must be a non-empty string, got: {name}')
        if not isinstance(filename, str) or not filename:
            raise GuiError(f'font filename must be a non-empty string, got: {filename}')
        if not isinstance(size, int) or size <= 0:
            raise GuiError(f'font size must be a positive integer, got: {size}')

    @staticmethod
    def _normalize_font_registry(fonts: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
        """Normalize font registry."""
        registry = list(fonts)
        if not registry:
            raise GuiError('fonts registry cannot be empty')
        for font_entry in registry:
            if not isinstance(font_entry, tuple) or len(font_entry) != 3:
                raise GuiError('each font entry must be a tuple of (name, filename, size)')
            name, filename, size = font_entry
            GuiManager._validate_font_entry(name, filename, size)
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
            if not isinstance(font_def, tuple) or len(font_def) != 2:
                raise GuiError(f'font entry for {name} must be a tuple of (filename, size)')
            filename, size = font_def
            self._validate_font_entry(name, filename, size)
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
        """Graphics factory."""
        return self._graphics_factory

    @property
    def buffered(self):
        """Buffered."""
        return self._buffered

    @buffered.setter
    def buffered(self, value):
        """Buffered."""
        if not isinstance(value, bool):
            raise GuiError('buffered must be a bool')
        self._buffered = value

    @property
    def current_widget(self):
        """Current widget."""
        return self.focus_state.current_widget

    @current_widget.setter
    def current_widget(self, value):
        """Current widget."""
        self.focus_state.current_widget = value

    @property
    def scheduler(self):
        """Scheduler."""
        return self._scheduler

    @property
    def dragging(self) -> bool:
        """Dragging."""
        return self._drag_state.dragging

    @dragging.setter
    def dragging(self, value: bool) -> None:
        """Dragging."""
        self._drag_state.dragging = value

    @property
    def dragging_window(self) -> Optional[Window]:
        """Dragging window."""
        return self._drag_state.dragging_window

    @dragging_window.setter
    def dragging_window(self, value: Optional[Window]) -> None:
        """Dragging window."""
        self._drag_state.dragging_window = value

    @property
    def mouse_delta(self) -> Optional[Tuple[int, int]]:
        """Mouse delta."""
        return self._drag_state.mouse_delta

    @mouse_delta.setter
    def mouse_delta(self, value: Optional[Tuple[int, int]]) -> None:
        """Mouse delta."""
        self._drag_state.mouse_delta = value

    @property
    def locking_object(self) -> Optional[Widget]:
        """Locking object."""
        return self._lock_state.locking_object

    @locking_object.setter
    def locking_object(self, value: Optional[Widget]) -> None:
        """Locking object."""
        self._lock_state.locking_object = value

    @property
    def mouse_locked(self) -> bool:
        """Mouse locked."""
        return self._lock_state.mouse_locked

    @mouse_locked.setter
    def mouse_locked(self, value: bool) -> None:
        """Mouse locked."""
        self._lock_state.mouse_locked = value

    @property
    def mouse_point_locked(self) -> bool:
        """Mouse point locked."""
        return self._lock_state.mouse_point_locked

    @mouse_point_locked.setter
    def mouse_point_locked(self, value: bool) -> None:
        """Mouse point locked."""
        self._lock_state.mouse_point_locked = value

    @property
    def lock_area_rect(self) -> Optional[Rect]:
        """Lock area rect."""
        return self._lock_state.lock_area_rect

    @lock_area_rect.setter
    def lock_area_rect(self, value: Optional[Rect]) -> None:
        """Lock area rect."""
        self._lock_state.lock_area_rect = value

    @property
    def lock_point_pos(self) -> Optional[Tuple[int, int]]:
        """Lock point pos."""
        return self._lock_state.lock_point_pos

    @lock_point_pos.setter
    def lock_point_pos(self, value: Optional[Tuple[int, int]]) -> None:
        """Lock point pos."""
        self._lock_state.lock_point_pos = value

    @property
    def lock_point_recenter_pending(self) -> bool:
        """Lock point recenter pending."""
        return self._lock_state.lock_point_recenter_pending

    @lock_point_recenter_pending.setter
    def lock_point_recenter_pending(self, value: bool) -> None:
        """Lock point recenter pending."""
        self._lock_state.lock_point_recenter_pending = value

    @property
    def lock_point_tolerance_rect(self) -> Optional[Rect]:
        """Lock point tolerance rect."""
        return self._lock_state.lock_point_tolerance_rect

    @lock_point_tolerance_rect.setter
    def lock_point_tolerance_rect(self, value: Optional[Rect]) -> None:
        """Lock point tolerance rect."""
        self._lock_state.lock_point_tolerance_rect = value

    # widgets
    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox:
        """Arrow box."""
        return self.ui_factory.arrow_box(id, rect, direction, on_activate)

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button:
        """Button."""
        return self.ui_factory.button(id, rect, style, text, on_activate)

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        """Button group."""
        return self.ui_factory.button_group(group, id, rect, style, text)

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        """Canvas."""
        return self.ui_factory.canvas(id, rect, backdrop, on_activate, automatic_pristine)

    def frame(self, id: str, rect: Rect) -> Frame:
        """Frame."""
        return self.ui_factory.frame(id, rect)

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        """Image."""
        return self.ui_factory.image(id, rect, image, automatic_pristine, scale)

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label:
        """Label."""
        return self.ui_factory.label(position, text, shadow, id)

    def scrollbar(
        self,
        id: str,
        overall_rect: Rect,
        horizontal: bool,
        style: ScrollbarStyle,
        total_range: int,
        start_pos: int,
        bar_size: int,
        inc_size: int,
        wheel_positive_to_max: bool = False,
    ) -> Scrollbar:
        """Scrollbar."""
        orientation = self._resolve_orientation(horizontal)
        arrow_style = self._resolve_scrollbar_style(style)
        return self.ui_factory.scrollbar(
            id,
            overall_rect,
            orientation,
            arrow_style,
            total_range,
            start_pos,
            bar_size,
            inc_size,
            wheel_positive_to_max,
        )

    def slider(
        self,
        id: str,
        rect: Rect,
        horizontal: bool,
        total_range: int,
        position: float = 0.0,
        integer_type: bool = False,
        notch_interval_percent: float = 5.0,
        wheel_positive_to_max: bool = False,
        wheel_step: Optional[float] = None,
    ) -> Slider:
        """Slider."""
        orientation = self._resolve_orientation(horizontal)
        return self.ui_factory.slider(
            id,
            rect,
            orientation,
            total_range,
            position,
            integer_type,
            notch_interval_percent,
            wheel_positive_to_max,
            wheel_step,
        )

    @staticmethod
    def _resolve_orientation(horizontal: bool) -> Orientation:
        """Resolve public boolean horizontal flag to internal orientation enum."""
        if not isinstance(horizontal, bool):
            raise GuiError(f'horizontal must be a bool, got: {horizontal}')
        if horizontal:
            return Orientation.Horizontal
        return Orientation.Vertical

    @staticmethod
    def _resolve_scrollbar_style(style: ScrollbarStyle) -> ArrowPosition:
        """Resolve public scrollbar style string flag to internal enum."""
        if not isinstance(style, str):
            raise GuiError(f'style must be a str, got: {style}')
        normalized = style.strip().lower()
        resolved = GuiManager._SCROLLBAR_STYLE_MAP.get(normalized)
        if resolved is None:
            raise GuiError(f'style must be one of skip/split/near/far, got: {style}')
        return resolved

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        """Toggle."""
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
        """Window."""
        return self.ui_factory.window(title, pos, size, backdrop, preamble, event_handler, postamble)

    def _task_panel_add_created_widget(self, create_widget: Callable[[], Widget]) -> Widget:
        """Create/register one widget in the task panel capture context."""
        if self.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        previous_capture = self.workspace_state.task_panel_capture
        previous_active_object = self.workspace_state.active_object
        self.workspace_state.task_panel_capture = True
        self.workspace_state.active_object = None
        try:
            widget = create_widget()
            if isinstance(widget, Window):
                raise GuiError('task panel only supports widgets; windows are not supported')
            if not isinstance(widget, Widget):
                raise GuiError('task panel constructor must return a Widget instance')
            return widget
        finally:
            self.workspace_state.task_panel_capture = previous_capture
            self.workspace_state.active_object = previous_active_object

    def _task_panel_widget(self, widget_type: str, *args: Any, **kwargs: Any) -> Widget:
        """Create one task-panel widget through the UI factory with shared argument shaping."""
        factory_method = getattr(self.ui_factory, widget_type, None)
        if not callable(factory_method):
            raise GuiError(f'unknown task panel widget type: {widget_type}')

        call_args = list(args)
        if widget_type == 'slider':
            call_args[2] = self._resolve_orientation(call_args[2])
        elif widget_type == 'scrollbar':
            call_args[2] = self._resolve_orientation(call_args[2])
            call_args[3] = self._resolve_scrollbar_style(call_args[3])

        return self._task_panel_add_created_widget(lambda: factory_method(*call_args, **kwargs))

    def __init__(
        self,
        surface: Surface,
        fonts: Optional[Iterable[Tuple[str, str, int]]] = None,
        graphics_factory: Optional[WidgetGraphicsFactory] = None,
        task_panel_enabled: bool = True,
        event_getter: Optional[Callable[[], Iterable[PygameEvent]]] = None,
        mouse_get_pos: Optional[Callable[[], Tuple[int, int]]] = None,
        mouse_get_pressed: Optional[Callable[[], Sequence[bool]]] = None,
        mouse_set_pos: Optional[Callable[[Tuple[int, int]], None]] = None,
        mouse_set_visible: Optional[Callable[[bool], None]] = None,
        window_tiling_enabled: bool = False,
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
        resolved_mouse_get_pressed = mouse_get_pressed or pygame.mouse.get_pressed
        resolved_mouse_set_pos = mouse_set_pos or pygame.mouse.set_pos
        resolved_mouse_set_visible = mouse_set_visible or pygame.mouse.set_visible
        if not callable(resolved_event_getter):
            raise GuiError('event_getter must be callable')
        if not callable(resolved_mouse_get_pos):
            raise GuiError('mouse_get_pos must be callable')
        if not callable(resolved_mouse_get_pressed):
            raise GuiError('mouse_get_pressed must be callable')
        if not callable(resolved_mouse_set_pos):
            raise GuiError('mouse_set_pos must be callable')
        if not callable(resolved_mouse_set_visible):
            raise GuiError('mouse_set_visible must be callable')
        self.input_providers: InputProviders = InputProviders(
            resolved_event_getter,
            resolved_mouse_get_pos,
            resolved_mouse_get_pressed,
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
        self.event_delivery: EventDeliveryCoordinator = EventDeliveryCoordinator(self)
        self.event_input: InputEventCoordinator = InputEventCoordinator(self)
        self.graphics: GraphicsCoordinator = GraphicsCoordinator(self)
        self.layout: LayoutCoordinator = LayoutCoordinator(self)
        self.lifecycle: LifecycleCoordinator = LifecycleCoordinator(self)
        self.lock_flow: LockFlowCoordinator = LockFlowCoordinator(self)
        self.pointer: PointerCoordinator = PointerCoordinator(self)
        self.window_tiling: WindowTilingCoordinator = WindowTilingCoordinator(self)
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
            self.set_task_panel_settings(TaskPanelSettings())
        self.set_window_tiling_enabled(window_tiling_enabled, relayout=False)

    def set_task_panel_settings(self, settings: TaskPanelSettings) -> None:
        """Configure task panel using an immutable settings object."""
        from .gui_utils.task_panel import _ManagedTaskPanel

        if not isinstance(settings, TaskPanelSettings):
            raise GuiError('task panel settings must be a TaskPanelSettings instance')

        panel_height = settings.panel_height
        left = settings.left
        width = settings.width
        hidden_peek_pixels = settings.hidden_peek_pixels
        auto_hide = settings.auto_hide
        animation_interval_ms = settings.animation_interval_ms
        animation_step_px = settings.animation_step_px
        backdrop_image = settings.backdrop_image
        preamble = settings.preamble
        event_handler = settings.event_handler
        postamble = settings.postamble

        if type(panel_height) is not int or panel_height <= 0:
            raise GuiError(f'task_panel_panel_height must be a positive int, got: {panel_height}')
        if type(left) is not int:
            raise GuiError(f'task_panel_left must be an int, got: {left}')
        if width is not None and type(width) is not int:
            raise GuiError(f'task_panel_width must be an int or None, got: {width}')
        if type(hidden_peek_pixels) is not int or hidden_peek_pixels < 1:
            raise GuiError(f'task_panel_hidden_peek_pixels must be >= 1, got: {hidden_peek_pixels}')
        if type(auto_hide) is not bool:
            raise GuiError('task_panel_auto_hide must be a bool')
        if type(animation_step_px) is not int or animation_step_px <= 0:
            raise GuiError(f'task_panel_animation_step_px must be > 0, got: {animation_step_px}')
        if isinstance(animation_interval_ms, bool) or not isinstance(animation_interval_ms, (int, float)) or animation_interval_ms <= 0:
            raise GuiError(f'task_panel_animation_interval_ms must be > 0, got: {animation_interval_ms}')
        if backdrop_image is not None and (not isinstance(backdrop_image, str) or backdrop_image == ''):
            raise GuiError(f'task_panel_backdrop_image must be a non-empty string or None, got: {backdrop_image!r}')
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
            panel_height,
            left,
            width,
            hidden_peek_pixels,
            auto_hide,
            animation_interval_ms,
            animation_step_px,
            backdrop_image,
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
                self.workspace_state.task_panel_capture = False

        self.task_panel = panel

    def run_postamble(self) -> None:
        """Run postamble."""
        self.lifecycle.run_postamble()

    def run_preamble(self) -> None:
        """Run preamble."""
        self.lifecycle.run_preamble()

    def set_task_panel_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set task panel lifecycle."""
        self.lifecycle.set_task_panel_lifecycle(preamble, event_handler, postamble)

    def set_task_panel_enabled(self, enabled: bool) -> None:
        """Set task panel enabled."""
        panel = self._require_task_panel()
        panel.set_visible(enabled)
        if not enabled:
            self.workspace_state.task_panel_capture = False

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        """Set task panel auto hide."""
        self._require_task_panel().set_auto_hide(auto_hide)

    def set_task_panel_hidden_peek_pixels(self, hidden_peek_pixels: int) -> None:
        """Set task panel hidden peek pixels."""
        self._require_task_panel().set_hidden_peek_pixels(hidden_peek_pixels)

    def set_task_panel_animation_step_px(self, animation_step_px: int) -> None:
        """Set task panel animation step in pixels."""
        self._require_task_panel().set_animation_step_px(animation_step_px)

    def set_task_panel_animation_interval_ms(self, animation_interval_ms: float) -> None:
        """Set task panel animation interval in milliseconds."""
        self._require_task_panel().set_animation_interval_ms(animation_interval_ms)

    def read_task_panel_settings(self) -> Dict[str, object]:
        """Read task panel settings."""
        panel = self._require_task_panel()
        return {
            'enabled': panel.visible,
            'auto_hide': panel.auto_hide,
            'panel_height': panel.panel_height,
            'left': panel.left,
            'width': panel.width,
            'hidden_peek_pixels': panel.hidden_peek_pixels,
            'animation_step_px': panel.animation_step_px,
            'animation_interval_ms': panel.animation_interval_ms,
            'backdrop_image': panel.backdrop_image,
            'rect': panel.get_rect(),
        }

    def _require_task_panel(self) -> "_ManagedTaskPanel":
        """Return task panel or raise when task-panel support is disabled."""
        panel = self.task_panel
        if panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        return panel

    def _get_mouse_pos(self) -> Tuple[int, int]:
        """Get logical mouse position for internal routing paths."""
        return self.pointer.get_mouse_pos()

    @staticmethod
    def _normalize_mouse_buttons(buttons: Sequence[bool]) -> Tuple[bool, bool, bool]:
        """Normalize backend button tuples to left/middle/right booleans."""
        if isinstance(buttons, tuple):
            raw = buttons
        else:
            raw = tuple(buttons)
        if len(raw) < 3:
            raise GuiError('mouse_get_pressed must return at least three button states')
        return (bool(raw[0]), bool(raw[1]), bool(raw[2]))

    def get_mouse_input_state(self) -> MouseInputState:
        """Return a snapshot of logical pointer position and primary button states."""
        position = self._get_mouse_pos()
        buttons = self._normalize_mouse_buttons(self.input_providers.mouse_get_pressed())
        return MouseInputState(position=position, buttons=buttons)

    def add(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget and attach container-specific state."""
        return self.object_registry.register(gui_object)

    def clear_button_groups(self) -> None:
        """Clear button groups."""
        self.button_group_mediator.clear()

    def clear_task_owners_for_window(self, window: Window) -> None:
        """Clear task owners for window."""
        self.event_delivery.clear_task_owners_for_window(window)

    def hide_widgets(self, *widgets: Widget) -> None:
        """Hide widgets."""
        self.widget_state.hide_widgets(*widgets)

    def lower_window(self, window: Window) -> None:
        """Lower window."""
        self.workspace.lower_window(window)

    def raise_window(self, window: Window) -> None:
        """Raise window."""
        self.workspace.raise_window(window)

    def set_window_tiling_enabled(self, enabled: bool, relayout: bool = True) -> None:
        """Enable or disable automatic non-overlapping window tiling."""
        self.window_tiling.set_enabled(enabled, relayout)

    def configure_window_tiling(
        self,
        *,
        gap: Optional[int] = None,
        padding: Optional[int] = None,
        avoid_task_panel: Optional[bool] = None,
        center_on_failure: Optional[bool] = None,
        relayout: bool = True,
    ) -> None:
        """Configure runtime window-tiling behavior and optionally apply immediately."""
        self.window_tiling.configure(
            gap=gap,
            padding=padding,
            avoid_task_panel=avoid_task_panel,
            center_on_failure=center_on_failure,
            relayout=relayout,
        )

    def tile_windows(self) -> None:
        """Run one tiling pass for currently visible windows using current settings."""
        self.window_tiling.arrange_windows()

    def read_window_tiling_settings(self) -> Dict[str, object]:
        """Read current runtime window-tiling settings."""
        return self.window_tiling.read_settings()

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

    def _set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        """Set logical pointer position for internal flows."""
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
        """Set screen lifecycle."""
        self.lifecycle.set_screen_lifecycle(preamble, event_handler, postamble)

    def set_task_owner(self, task_id: Hashable, window: Optional[Window]) -> None:
        """Set task owner."""
        self.event_delivery.set_task_owner(task_id, window)

    def set_task_owners(self, window: Optional[Window], *task_ids: Hashable) -> None:
        """Set task owners."""
        self.event_delivery.set_task_owners(window, *task_ids)

    def show_widgets(self, *widgets: Widget) -> None:
        """Show widgets."""
        self.widget_state.show_widgets(*widgets)

    def dispatch_event(self, event: BaseEvent) -> None:
        """Dispatch event."""
        self.event_delivery.dispatch_event(event)

    def event(self, event_type: Event, **kwargs: object) -> "GuiEvent":
        """Event."""
        return self.event_input.event(event_type, **kwargs)

    def events(self) -> Iterable["GuiEvent"]:
        """Events."""
        yield from self.event_input.events()

    def handle_event(self, event: PygameEvent) -> "GuiEvent":
        """Handle event."""
        return self.event_dispatcher.handle(event)

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional[Window] = None) -> bool:
        """Run widget handler and execute activation callbacks when present."""
        return self.widget_state.handle_widget(widget, event, window)

    def _draw_gui(self) -> None:
        """Render one GUI frame."""
        self.renderer.draw()

    def _undraw_gui(self) -> None:
        """Restore buffered GUI regions after a frame flip."""
        self.renderer.undraw()

    def _convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Convert container coordinates to screen coordinates for internal flows."""
        return self.pointer.convert_to_screen(point, window)

    def _convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Convert screen coordinates to container-local coordinates for internal flows."""
        return self.pointer.convert_to_window(point, window)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        """Gridded."""
        return self.layout_manager.get_cell(x, y)

    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        """Return a surface copy of rect from surface."""
        return self.graphics.copy_graphic_area(surface, rect, flags)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Recenters pointer only when it exits the configured broad center region."""
        self.lock_flow.enforce_point_lock(hardware_position)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Lock area."""
        return self.lock_flow.lock_area(position)

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional["_PristineContainer"] = None) -> None:
        """Restore a region from a previously cached pristine bitmap."""
        self.graphics.restore_pristine(area, obj)

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        """Update focus."""
        self.focus_state.update_focus(new_hover)

    def update_active_window(self) -> None:
        """Update active window."""
        self.focus_state.update_active_window()

    def _build_centered_recenter_rect(self, coverage: float = 0.8) -> Rect:
        """Build centered recenter rect."""
        if coverage <= 0.0 or coverage > 1.0:
            raise GuiError(f'coverage must be in the range (0, 1], got: {coverage}')
        surface_rect = self.surface.get_rect()
        width = max(1, int(surface_rect.width * coverage))
        height = max(1, int(surface_rect.height * coverage))
        centered = Rect(0, 0, width, height)
        centered.center = surface_rect.center
        return centered
