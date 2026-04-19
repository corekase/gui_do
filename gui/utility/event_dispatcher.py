from __future__ import annotations

from pygame.event import Event as PygameEvent
from typing import TYPE_CHECKING
from .input.input_emitter import InputEventEmitter
from .input.input_router import InputRouter

if TYPE_CHECKING:
    from .gui_utils.gui_event import GuiEvent
    from .gui_manager import GuiManager

class EventDispatcher:
    """Consumes routed input actions and emits GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create EventDispatcher."""
        self.gui: "GuiManager" = gui_manager
        self.router: InputRouter = InputRouter(gui_manager)
        self.emitter: InputEventEmitter = gui_manager.input_emitter

    def handle(self, event: PygameEvent) -> "GuiEvent":
        """Handle."""
        action = self.router.route(event)
        return self.emitter.emit_action(action)
