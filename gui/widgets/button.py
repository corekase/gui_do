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
    """Clickable widget with hover/armed visuals and optional repeat callback."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None, skip_factory: bool = False) -> None:
        """Create a button and its state bitmaps."""
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Button
        self.timer_id: Optional[str] = None
        if not skip_factory:
            (self.idle, self.hover, self.armed), self.hit_rect = \
                self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        self.on_activate = on_activate

    def leave(self) -> None:
        self._clear_timer()
        super().leave()
        self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Advance button state and return True when activation should be emitted."""
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        if not super().handle_event(event, window):
            self._clear_timer()
            return False
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
                    self._clear_timer()
                    self.state = InteractiveState.Hover
                    if self.on_activate is not None:
                        return False
                    return True
        return False

    def _clear_timer(self) -> None:
        if self.timer_id is None:
            return
        try:
            self.gui.timers.remove_timer(self.timer_id)
        except Exception:
            pass
        finally:
            self.timer_id = None

    def _invoke_on_activate(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def __del__(self) -> None:
        self._clear_timer()
