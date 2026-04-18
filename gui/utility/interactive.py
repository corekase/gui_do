from __future__ import annotations

from .widget import Widget
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Optional, TYPE_CHECKING
from .events import InteractiveState

if TYPE_CHECKING:
    from .gui_manager import GuiManager
    from ..widgets.window import Window

class BaseInteractive(Widget):
    """Shared hover/armed state machine for interactive widgets."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        """Create BaseInteractive."""
        super().__init__(gui, id, rect)
        self.state: InteractiveState = InteractiveState.Idle
        self.idle: Optional[Surface] = None
        self.hover: Optional[Surface] = None
        self.armed: Optional[Surface] = None
        self.disabled_graphic: Optional[Surface] = None

    def _on_disabled_changed(self, disabled: bool) -> None:
        """Keep visual state in sync with disabled mode."""
        if disabled:
            self.state = InteractiveState.Disabled
        else:
            self.state = InteractiveState.Idle

    def leave(self) -> None:
        """Reset to idle unless this widget intentionally stays armed."""
        if self.disabled:
            self.state = InteractiveState.Disabled
            return
        if self.state != InteractiveState.Armed:
            self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Update interaction state and return True while hovered."""
        if self.disabled:
            self.state = InteractiveState.Disabled
            return False
        collision = self.get_collide(window)
        if not collision:
            if self.state != InteractiveState.Armed:
                self.state = InteractiveState.Idle
            return False

        if self.state == InteractiveState.Idle:
            self.state = InteractiveState.Hover
        return True

    def draw(self) -> None:
        """Blit the bitmap matching the current interaction state."""
        super().draw()
        if self.disabled:
            if self.disabled_graphic is not None:
                self.surface.blit(self.disabled_graphic, (self.draw_rect.x, self.draw_rect.y))
            elif self.idle is not None:
                self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
                self._blit_disabled_overlay()
            return
        if self.state == InteractiveState.Idle and self.idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Hover and self.hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Armed and self.armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
