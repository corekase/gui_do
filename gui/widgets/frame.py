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
        super().__init__(gui, id, rect)
        self._idle: Surface
        self._hover: Surface
        self._armed: Surface
        visuals = self.gui.graphics_factory.build_frame_visuals(rect)
        self._idle = visuals.idle
        self._hover = visuals.hover
        self._armed = visuals.armed
        self.state: InteractiveState = InteractiveState.Idle

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        return False

    def leave(self) -> None:
        """Frame is non-interactive and keeps no focus state."""
        return

    def draw(self) -> None:
        super().draw()
        if self.state == InteractiveState.Idle:
            self.surface.blit(self._idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Hover:
            self.surface.blit(self._hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Armed:
            self.surface.blit(self._armed, (self.draw_rect.x, self.draw_rect.y))
