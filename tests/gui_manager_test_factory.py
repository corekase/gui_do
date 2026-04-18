from types import SimpleNamespace
from typing import Any, Literal, Optional

from pygame import Rect

from gui.utility.dispatch_bridge_coordinator import DispatchBridgeCoordinator
from gui.utility.event_delivery import EventDeliveryCoordinator
from gui.utility.focus_state import FocusStateController
from gui.utility.graphics_coordinator import GraphicsCoordinator
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_event_coordinator import InputEventCoordinator
from gui.utility.input_state import DragStateController, LockStateController
from gui.utility.guimanager import GuiManager
from gui.utility.layout_coordinator import LayoutCoordinator
from gui.utility.lifecycle import LifecycleCoordinator
from gui.utility.lock_flow_coordinator import LockFlowCoordinator
from gui.utility.object_registry import GuiObjectRegistry
from gui.utility.pointer_coordinator import PointerCoordinator
from gui.utility.render_coordinator import RenderCoordinator
from gui.utility.task_panel_config_coordinator import TaskPanelConfigCoordinator
from gui.utility.ui_factory import GuiUiFactory
from gui.utility.widget_state_coordinator import WidgetStateCoordinator
from gui.utility.workspace_coordinator import WorkspaceCoordinator
from gui.utility.widget import Widget

StubPreset = Literal["base", "routing", "locking", "state_manager"]


def _default_surface() -> Any:
    return SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))


def _apply_preset(gui: GuiManager, preset: StubPreset) -> None:
    if preset == "base":
        return

    if preset == "routing":
        gui._screen_events = []
        gui._screen_event_handler = lambda event: gui._screen_events.append(event)
        gui.lock_area = lambda point: point
        return

    if preset == "locking":
        gui.locking_object = Widget.__new__(Widget)
        gui._is_registered_object = lambda _obj: True
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
    gui._task_panel_capture = False
    gui._active_object = None
    gui._task_owner_by_id = {}

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
    gui._current_widget = None
    gui.pristine = None
    gui.locking_object = None

    gui._screen_preamble = None
    gui._screen_event_handler = lambda _event: None
    gui._screen_postamble = None

    gui._event_getter = lambda: []
    gui._mouse_get_pos = lambda: (0, 0)
    gui._mouse_set_pos = lambda _pos: None

    gui.input_emitter = InputEventEmitter(gui)
    gui.drag_state = DragStateController(gui)
    gui.focus_state = FocusStateController(gui)
    gui.lock_state = LockStateController(gui)

    gui.object_registry = GuiObjectRegistry(gui)
    gui.dispatch_bridge = DispatchBridgeCoordinator(gui)
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
