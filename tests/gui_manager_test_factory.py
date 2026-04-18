from types import SimpleNamespace
from typing import Any, Optional

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


def _default_surface() -> Any:
    return SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))


def build_gui_manager_stub(*, surface: Optional[Any] = None, include_ui_factory: bool = False) -> GuiManager:
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

    return gui
