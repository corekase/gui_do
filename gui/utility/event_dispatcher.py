from pygame.event import Event as PygameEvent
from typing import TYPE_CHECKING
from .input_emitter import InputEventEmitter
from .input_router import InputRouter

if TYPE_CHECKING:
    from .gui_event import GuiEvent
    from .gui_manager import GuiManager

class EventDispatcher:
    """Consumes routed input actions and emits GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager
        self.router: InputRouter = InputRouter(gui_manager)
        self.emitter: InputEventEmitter = gui_manager.input_emitter

    def handle(self, event: PygameEvent) -> "GuiEvent":
        return self.emitter.emit_action(self.router.handle(event))
