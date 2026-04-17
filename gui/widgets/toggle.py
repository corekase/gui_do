from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.constants import ButtonStyle, InteractiveState
from ..utility.interactive import BaseInteractive

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Toggle(BaseInteractive):
    """Two-state button that flips pushed state on left click."""

    @property
    def pushed(self) -> bool:
        """Return pushed state."""
        return self._pushed

    @pushed.setter
    def pushed(self, value: bool) -> None:
        """Set pushed state."""
        self._pushed = value

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> None:
        """Create a toggle with separate bitmaps for raised and pushed states."""
        super().__init__(gui, id, rect)
        self._pushed: bool = pushed
        if raised_text is None:
            raised_text = pressed_text
        (_, _, self.armed), rect1 = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, pressed_text, rect)
        (self.idle, self.hover, _), rect2 = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, raised_text, rect)
        if rect1.width > rect2.width:
            self.hit_rect = rect1
        else:
            self.hit_rect = rect2

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Update hover state and flip pushed on left button down."""
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        if not super().handle_event(event, window):
            return False
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
                self.pushed = not self.pushed
                return True
        return False

    def draw(self) -> None:
        if self.pushed:
            self.surface.blit(self.armed, self.draw_rect)
        else:
            super().draw()
