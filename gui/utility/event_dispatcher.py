from pygame.event import Event as PygameEvent
from typing import TYPE_CHECKING
from .input_router import InputRouter

if TYPE_CHECKING:
    from .guimanager import GuiEvent, GuiManager

class EventDispatcher:
    """Thin facade that delegates input routing to InputRouter."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager
        self.router: InputRouter = InputRouter(gui_manager)

    def handle(self, event: PygameEvent) -> "GuiEvent":
        return self.router.handle(event)

    def _handle_base_mouse_events(self, event: PygameEvent) -> "GuiEvent":
        return self.router._handle_base_mouse_events(event)

    def _handle_locked_object(self, event: PygameEvent) -> "GuiEvent":
        return self.router._handle_locked_object(event)

    def _handle_mouse_motion(self, event: PygameEvent) -> None:
        self.router._handle_mouse_motion(event)

    def _handle_system_event(self, event: PygameEvent) -> "GuiEvent":
        return self.router._handle_system_event(event)

    def _handle_window_dragging(self, event: PygameEvent) -> "GuiEvent":
        return self.router._handle_window_dragging(event)

    def _process_screen_widgets(self, event: PygameEvent) -> "GuiEvent":
        return self.router._process_screen_widgets(event)

    def _process_window_widgets(self, event: PygameEvent) -> "GuiEvent":
        return self.router._process_window_widgets(event)

    def _process_task_panel_widgets(self, event: PygameEvent):
        return self.router._process_task_panel_widgets(event)

    def _check_window_drag_start(self, event: PygameEvent) -> None:
        self.router._check_window_drag_start(event)

    def _is_registered_widget(self, widget) -> bool:
        return self.router._is_registered_widget(widget)

    def _reset_window_drag_state(self) -> None:
        self.router._reset_window_drag_state()

    def _update_active_window(self) -> None:
        self.router._update_active_window()
