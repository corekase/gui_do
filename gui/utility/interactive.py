"""
Base class for interactive widgets.

Provides state management (Idle, Hover, Armed) and common event handling
for widgets that respond to mouse input.
"""

from .widget import Widget
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from typing import Optional, Any, TYPE_CHECKING
from .constants import InteractiveState

if TYPE_CHECKING:
    from ..guimanager import GuiManager

class BaseInteractive(Widget):
    """
    Base class for interactive widgets.

    Manages three-state interaction: Idle → Hover → Armed.
    Subclasses override handle_event and draw to customize behavior.
    """

    def __init__(self, gui: "GuiManager", id: Any, rect) -> None:
        super().__init__(gui, id, rect)
        self.state: InteractiveState = InteractiveState.Idle
        self.idle: Optional[Any] = None      # Surface for idle state
        self.hover: Optional[Any] = None     # Surface for hover state
        self.armed: Optional[Any] = None     # Surface for armed state

    def handle_event(self, event: Any, window: Any) -> bool:
        """
        Handle mouse events and manage state transitions.

        Returns:
            bool: True if event was handled by widget, False otherwise
        """
        collision = self.get_collide(window)
        if not collision:
            if self.state != InteractiveState.Armed:
                self.state = InteractiveState.Idle
            return False

        if self.state == InteractiveState.Idle:
            self.state = InteractiveState.Hover
        return True

    def leave(self) -> None:
        """Called when widget loses focus. Reset state if not armed."""
        if self.state != InteractiveState.Armed:
            self.state = InteractiveState.Idle

    def draw(self) -> None:
        """Draw widget state appropriate surface."""
        super().draw()
        if self.state == InteractiveState.Idle and self.idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Hover and self.hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Armed and self.armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
