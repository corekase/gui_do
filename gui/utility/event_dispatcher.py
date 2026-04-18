from __future__ import annotations

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
        """Initialize the EventDispatcher instance."""
        self.gui: "GuiManager" = gui_manager
        self.router: InputRouter = InputRouter(gui_manager)
        self.emitter: InputEventEmitter = gui_manager.input_emitter

    def handle(self, event: PygameEvent) -> "GuiEvent":
        """Run handle and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self._emit_action(self._route_action(event))

    def _route_action(self, event: PygameEvent):
        """Internal helper for route action."""
        return self.router.route(event)

    def _emit_action(self, action):
        """Internal helper for emit action."""
        return self.emitter.emit_action(action)
