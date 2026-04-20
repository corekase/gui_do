from __future__ import annotations

from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.input.normalized_event import normalize_input_event
from ..utility.events import ButtonStyle, InteractiveState
from ..utility.intermediates.interactive import BaseInteractive
from ..utility.intermediates.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
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
        visuals = self.gui.graphics_factory.build_toggle_visuals(style, pressed_text, raised_text, rect)
        self.idle = visuals.idle
        self.hover = visuals.hover
        self.armed = visuals.armed
        self.disabled_graphic = visuals.disabled
        self.hit_rect = visuals.hit_rect

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Update hover state and flip pushed on left button down."""
        if self.disabled:
            return False
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        normalized = normalize_input_event(event)
        if not super().handle_event(event, window):
            return False
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN and normalized.is_left_down:
                self.pushed = not self.pushed
                return True
        return False

    def draw(self) -> None:
        """Draw."""
        if self.disabled:
            if self.disabled_graphic is not None:
                Widget.draw(self)
                self.surface.blit(self.disabled_graphic, self.draw_rect)
            else:
                super().draw()
            return
        if self.pushed:
            Widget.draw(self)
            self.surface.blit(self.armed, self.draw_rect)
        else:
            super().draw()
