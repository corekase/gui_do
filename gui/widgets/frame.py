from __future__ import annotations

from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Optional, TYPE_CHECKING
from ..utility.events import InteractiveState
from ..utility.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window

class Frame(Widget):
    """Static framed panel with idle/hover/armed variants."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        """Create Frame."""
        super().__init__(gui, id, rect)
        self._idle: Surface
        self._hover: Surface
        self._armed: Surface
        self._disabled_graphic: Optional[Surface]
        visuals = self.gui.graphics_factory.build_frame_visuals(rect)
        self._idle = visuals.idle
        self._hover = visuals.hover
        self._armed = visuals.armed
        self._disabled_graphic = visuals.disabled
        self.state: InteractiveState = InteractiveState.Idle

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        """Handle event."""
        if self.disabled:
            return False
        return False

    def leave(self) -> None:
        """Frame is non-interactive and keeps no focus state."""
        return

    def draw(self) -> None:
        """Draw."""
        super().draw()
        if self.disabled:
            if self._disabled_graphic is not None:
                self.surface.blit(self._disabled_graphic, (self.draw_rect.x, self.draw_rect.y))
            else:
                self.surface.blit(self._idle, (self.draw_rect.x, self.draw_rect.y))
                self._blit_disabled_overlay()
            return
        if self.state == InteractiveState.Idle:
            self.surface.blit(self._idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Hover:
            self.surface.blit(self._hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Armed:
            self.surface.blit(self._armed, (self.draw_rect.x, self.draw_rect.y))
