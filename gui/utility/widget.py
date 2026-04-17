from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from .constants import WidgetKind, GuiError

if TYPE_CHECKING:
    from .guimanager import GuiManager
    from ..widgets.window import Window

class Widget:
    """Base widget contract used by all concrete widgets."""

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise GuiError('widget visible must be a bool')
        self._visible = value

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        self.gui: "GuiManager" = gui
        self.WidgetKind: Optional[WidgetKind] = None
        self.surface: Optional[Surface] = None
        self.window: Optional["Window"] = None
        self.id: str = id
        self.draw_rect: Rect = Rect(rect)
        self.hit_rect: Optional[Rect] = None
        self.pristine: Optional[Surface] = None
        self._visible: bool = True
        self.on_activate: Optional[Callable[[], None]] = None
        self.auto_restore_pristine: bool = False

    def leave(self) -> None:
        """Hook called when focus leaves this widget."""
        pass
    def get_collide(self, window: Optional["Window"] = None) -> bool:
        """Return True when the current mouse position is inside this widget."""
        if self.hit_rect is None:
            return self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))
        return self.hit_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))

    def set_pos(self, pos: Tuple[int, int]) -> None:
        """Move the widget without changing size."""
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'widget pos must be a tuple of (x, y), got: {pos}')
        self.draw_rect.x, self.draw_rect.y = pos

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        """Handle an input event. Subclasses return True on activation."""
        return False

    def draw(self) -> None:
        """Draw the widget. Subclasses should call this first when needed."""
        if self.auto_restore_pristine:
            self.gui.restore_pristine(self.draw_rect, self.window)
