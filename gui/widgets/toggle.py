from typing import Any, Optional
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.constants import WidgetKind, InteractiveState
from ..utility.interactive import BaseInteractive

class Toggle(BaseInteractive):
    """A toggle button widget with two states (pushed/raised).

    Toggles between two visual states each time it's clicked. Can have different
    text for each state.

    Attributes:
        pushed: Whether the toggle is currently in the pressed state.
    """
    def __init__(self, gui: Any, id: Any, rect: Any, style: Any, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> None:
        """Initialize a toggle widget.

        Args:
            gui: Reference to GuiManager.
            id: Unique identifier for this toggle.
            rect: Rect defining toggle position and size.
            style: ButtonStyle enum value for visual style.
            pushed: Initial state (True = pressed, False = raised).
            pressed_text: Text to display when toggle is pressed.
            raised_text: Text to display when toggle is raised. Defaults to pressed_text.
        """
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Toggle
        self.pushed: bool = pushed
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

    def handle_event(self, event: Any, window: Any) -> bool:
        """Handle toggle events.

        Args:
            event: The pygame event to handle.
            window: The parent window, if any.

        Returns:
            True if toggle state changed, False otherwise.
        """
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        # Call base logic
        if not super().handle_event(event, window):
            return False
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.pushed = not self.pushed
                return True
        return False

    def draw(self) -> None:
        if self.pushed:
            self.surface.blit(self.armed, self.draw_rect)
        else:
            super().draw()

    def set(self, pushed: bool) -> None:
        """Set the toggle state programmatically.

        Args:
            pushed: True for pressed state, False for raised state.
        """
        self.pushed = pushed

    def read(self) -> bool:
        """Read the current toggle state.

        Returns:
            True if toggle is pressed, False if raised.
        """
        return self.pushed
