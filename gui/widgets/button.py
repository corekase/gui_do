from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Callable, Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import ButtonStyle, WidgetKind
from ..utility.interactive import BaseInteractive, InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Button(BaseInteractive):
    """An interactive button widget with state feedback.

    Buttons transition through three states (Idle → Hover → Armed) and can execute
    callbacks when activated. Includes automatic repeat functionality when held down.

    Attributes:
        on_activate: Optional callback invoked when button is activated.
        timer_id: ID of the repeat timer, if any.
    """
    def __init__(self, gui: "GuiManager", id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None, skip_factory: bool = False) -> None:
        """Initialize a button widget.

        Args:
            gui: Reference to GuiManager.
            id: Unique identifier for this button.
            rect: Rect defining button position and size.
            style: ButtonStyle enum value for visual style.
            text: Optional text to display on button.
            on_activate: Optional callback when button is activated.
            skip_factory: If True, skip bitmap factory initialization (for subclasses).
        """
        # initialize common widget values
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Button
        # this object's timer
        self.timer_id: Optional[str] = None
        if not skip_factory:
            (self.idle, self.hover, self.armed), self.hit_rect = \
                self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        self.on_activate = on_activate

    def _invoke_on_activate(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle button events and manage state transitions.

        Updates button state based on mouse position and input. Manages the Armed state
        and invokes callbacks as appropriate.

        Args:
            event: The pygame event to handle.
            window: The parent window, if any.

        Returns:
            True if the event resulted in button activation, False otherwise.
        """
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False

        # Call base interactive logic first
        if not super().handle_event(event, window):
            if self.timer_id is not None:
                self.gui.timers.remove_timer(self.timer_id)
                self.timer_id = None
            return False

        # manage the state of the button
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN:
                if getattr(event, 'button', None) == 1:
                    self.state = InteractiveState.Armed
                    if self.on_activate is not None and self.timer_id is None:
                        self.gui.timers.add_timer(f'{self.id}.timer', 150, self._invoke_on_activate)
                        self.timer_id = f'{self.id}.timer'
                    return True
        if self.state == InteractiveState.Armed:
            if event.type == MOUSEBUTTONUP:
                if getattr(event, 'button', None) == 1:
                    if self.timer_id is not None:
                        self.gui.timers.remove_timer(f'{self.id}.timer')
                        self.timer_id = None
                    self.state = InteractiveState.Hover
                    if self.on_activate is not None:
                        return False
                    return True
        return False

    def leave(self) -> None:
        if self.timer_id is not None:
            self.gui.timers.remove_timer(f'{self.id}.timer')
            self.timer_id = None
        super().leave()
        self.state = InteractiveState.Idle
