from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.event import Event as PygameEvent

if TYPE_CHECKING:
    from ..gui_utils.gui_event import GuiEvent
    from ..gui_manager import GuiManager


class DispatchBridgeCoordinator:
    """Owns GUI raw-event to GuiEvent dispatch bridging."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create DispatchBridgeCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def handle_event(self, event: PygameEvent) -> "GuiEvent":
        """Handle event."""
        return self.gui.event_dispatcher.handle(event)
