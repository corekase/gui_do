from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.event import Event as PygameEvent

if TYPE_CHECKING:
    from .gui_event import GuiEvent
    from .gui_manager import GuiManager


class DispatchBridgeCoordinator:
    """Owns GUI raw-event to GuiEvent dispatch bridging."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Initialize the DispatchBridgeCoordinator instance."""
        self.gui: "GuiManager" = gui_manager

    def handle_event(self, event: PygameEvent) -> "GuiEvent":
        """Run handle event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.gui.event_dispatcher.handle(event)
