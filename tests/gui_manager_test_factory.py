from types import SimpleNamespace
from typing import Any, Callable, Literal, Optional

from pygame import Rect

from gui.utility.coordinators.event_delivery import EventDeliveryCoordinator
from gui.utility.focus_state import FocusStateController
from gui.utility.gui_utils.focus_state_model import FocusState
from gui.utility.coordinators.graphics_coordinator import GraphicsCoordinator
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.coordinators.input_event_coordinator import InputEventCoordinator
from gui.utility.gui_utils.input_providers import InputProviders
from gui.utility.gui_utils.drag_state_model import DragState
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from gui.utility.gui_manager import GuiManager
from gui.utility.coordinators.layout_coordinator import LayoutCoordinator
from gui.utility.lifecycle import LifecycleCoordinator, ScreenLifecycle
from gui.utility.coordinators.lock_flow_coordinator import LockFlowCoordinator
from gui.utility.gui_utils.lock_state_model import LockState
from gui.utility.object_registry import GuiObjectRegistry
from gui.utility.coordinators.pointer_coordinator import PointerCoordinator
from gui.utility.coordinators.render_coordinator import RenderCoordinator
from gui.utility.coordinators.task_panel_config_coordinator import TaskPanelConfigCoordinator
from gui.utility.ui_factory import GuiUiFactory
from gui.utility.coordinators.widget_state_coordinator import WidgetStateCoordinator
from gui.utility.coordinators.workspace_coordinator import WorkspaceCoordinator
from gui.utility.gui_utils.workspace_state import WorkspaceState
from gui.utility.intermediates.widget import Widget

StubPreset = Literal["base", "routing", "locking", "state_manager"]


def _default_surface() -> Any:
    return SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))


def _apply_preset(gui: GuiManager, preset: StubPreset) -> None:
    if preset == "base":
        return

    if preset == "routing":
        gui._screen_events = []
        gui.screen_lifecycle.set_lifecycle(None, lambda event: gui._screen_events.append(event), None)
        gui.lock_area = lambda point: point
        return

    if preset == "locking":
        gui.locking_object = Widget.__new__(Widget)
        gui.object_registry.is_registered_object = lambda _obj: True
        gui.mouse_locked = True
        gui.mouse_point_locked = False
        gui.lock_area_rect = Rect(10, 20, 5, 6)
        gui.lock_point_pos = None
        gui.lock_point_recenter_pending = False
        gui.lock_point_tolerance_rect = None
        return

    if preset == "state_manager":
        gui._mouse_pos = (0, 0)

        def get_mouse_pos() -> Any:
            return gui._mouse_pos

        def set_mouse_pos(pos: Any, update_physical_coords: bool = True) -> None:
            _ = update_physical_coords
            gui._mouse_pos = pos

        gui.get_mouse_pos = get_mouse_pos
        gui.set_mouse_pos = set_mouse_pos
        return

    raise ValueError(f"unknown stub preset: {preset}")


def build_gui_manager_stub(
    *,
    surface: Optional[Any] = None,
    include_ui_factory: bool = False,
    preset: StubPreset = "base",
) -> GuiManager:
    gui = GuiManager.__new__(GuiManager)

    gui.surface = _default_surface() if surface is None else surface
    gui.widgets = []
    gui.windows = []
    gui.task_panel = None
    gui.workspace_state = WorkspaceState()

    gui._drag_state = DragState()
    gui._lock_state = LockState()

    gui.dragging = False
    gui.dragging_window = None
    gui.mouse_delta = None
    gui.mouse_pos = (0, 0)
    gui.mouse_locked = False
    gui.mouse_point_locked = False
    gui.lock_area_rect = None
    gui.lock_point_pos = None
    gui.lock_point_recenter_pending = False
    gui.lock_point_tolerance_rect = None

    gui.cursor_image = None
    gui.cursor_hotspot = None
    gui.cursor_rect = None
    gui.active_window = None
    gui.focus_state_data = FocusState()
    gui.pristine = None
    gui.locking_object = None

    gui.screen_lifecycle = ScreenLifecycle()

    gui.input_providers = InputProviders(
        lambda: [],
        lambda: (0, 0),
        lambda _pos: None,
        lambda _visible: None,
    )

    gui.input_emitter = InputEventEmitter(gui)
    gui.drag_state = DragStateController(gui)
    gui.focus_state = FocusStateController(gui)
    gui.lock_state = LockStateController(gui)

    gui.object_registry = GuiObjectRegistry(gui)
    gui.event_delivery = EventDeliveryCoordinator(gui)
    gui.event_input = InputEventCoordinator(gui)
    gui.graphics = GraphicsCoordinator(gui)
    gui.layout = LayoutCoordinator(gui)
    gui.lifecycle = LifecycleCoordinator(gui)
    gui.lock_flow = LockFlowCoordinator(gui)
    gui.pointer = PointerCoordinator(gui)
    gui.render_flow = RenderCoordinator(gui)
    gui.task_panel_config = TaskPanelConfigCoordinator(gui)
    gui.widget_state = WidgetStateCoordinator(gui)
    gui.workspace = WorkspaceCoordinator(gui)

    if include_ui_factory:
        gui.ui_factory = GuiUiFactory(gui)

    _apply_preset(gui, preset)

    return gui


def build_routing_stub(*, surface: Optional[Any] = None, include_ui_factory: bool = False) -> GuiManager:
    return build_gui_manager_stub(surface=surface, include_ui_factory=include_ui_factory, preset="routing")


def build_locking_stub(*, surface: Optional[Any] = None, include_ui_factory: bool = False) -> GuiManager:
    return build_gui_manager_stub(surface=surface, include_ui_factory=include_ui_factory, preset="locking")


def build_state_manager_stub(
    *,
    surface: Optional[Any] = None,
    include_ui_factory: bool = False,
    mouse_pos: Any = (0, 0),
    scheduler: Optional[Any] = None,
    scheduler_factory: Optional[Callable[[GuiManager], Any]] = None,
    track_set_calls: bool = False,
) -> GuiManager:
    if scheduler is not None and scheduler_factory is not None:
        raise ValueError("scheduler and scheduler_factory are mutually exclusive")

    gui = build_gui_manager_stub(surface=surface, include_ui_factory=include_ui_factory, preset="state_manager")
    gui._mouse_pos = mouse_pos

    if track_set_calls:
        gui.set_calls = []

        def set_mouse_pos(pos: Any, update_physical_coords: bool = True) -> None:
            gui._mouse_pos = pos
            gui.set_calls.append((pos, update_physical_coords))

        gui.set_mouse_pos = set_mouse_pos

    if scheduler is not None:
        gui._scheduler = scheduler
    elif scheduler_factory is not None:
        gui._scheduler = scheduler_factory(gui)

    return gui
