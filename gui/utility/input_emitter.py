from pygame.event import Event as PygameEvent
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from typing import Optional, TYPE_CHECKING
from .constants import Event
from .input_actions import InputAction

if TYPE_CHECKING:
    from .gui_event import GuiEvent
    from .guimanager import GuiManager


class InputEventEmitter:
    """Centralized translation from routed input outcomes to GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def emit_action(self, action: InputAction) -> "GuiEvent":
        if action.builder is not None:
            return action.builder()
        if action.event_type is None:
            return self.gui.event(Event.Pass)
        return self.gui.event(action.event_type, **action.kwargs)

    def base_mouse_event(self, event: PygameEvent) -> "GuiEvent":
        if event.type == MOUSEBUTTONUP:
            return self.gui.event(Event.MouseButtonUp, button=getattr(event, 'button', None))
        if event.type == MOUSEBUTTONDOWN:
            return self.gui.event(Event.MouseButtonDown, button=getattr(event, 'button', None))
        if event.type == MOUSEMOTION:
            return self.gui.event(Event.MouseMotion, rel=getattr(event, 'rel', (0, 0)))
        return self.pass_event()

    def system_event(self, event: PygameEvent) -> "GuiEvent":
        if event.type == QUIT:
            return self.gui.event(Event.Quit)
        if event.type == KEYUP:
            return self.gui.event(Event.KeyUp, key=getattr(event, 'key', None))
        if event.type == KEYDOWN:
            return self.gui.event(Event.KeyDown, key=getattr(event, 'key', None))
        return self.pass_event()

    def widget_event(self, widget_id: Optional[str] = None, *, window=None, task_panel: bool = False) -> "GuiEvent":
        kwargs = {}
        if widget_id is not None:
            kwargs['widget_id'] = widget_id
        if window is not None:
            kwargs['window'] = window
        if task_panel:
            kwargs['task_panel'] = True
        return self.gui.event(Event.Widget, **kwargs)

    def pass_event(self) -> "GuiEvent":
        return self.gui.event(Event.Pass)
