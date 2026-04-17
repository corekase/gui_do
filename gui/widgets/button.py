from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Callable, Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import ButtonStyle
from ..utility.interactive import BaseInteractive, InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Button(BaseInteractive):
    """Clickable widget with hover/armed visuals."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> None:
        """Create a button and its state bitmaps."""
        super().__init__(gui, id, rect)
        (self.idle, self.hover, self.armed), self.hit_rect = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        self.on_activate = on_activate

    def leave(self) -> None:
        super().leave()
        self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Advance button state and return True when activation should be emitted."""
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        if not super().handle_event(event, window):
            return False
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN:
                if getattr(event, 'button', None) == 1:
                    self.state = InteractiveState.Armed
                    return True
        if self.state == InteractiveState.Armed:
            if event.type == MOUSEBUTTONUP:
                if getattr(event, 'button', None) == 1:
                    self.state = InteractiveState.Hover
                    if self.on_activate is not None:
                        return False
                    return True
        return False
