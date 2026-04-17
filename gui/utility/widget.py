from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from .constants import Event, GuiError

if TYPE_CHECKING:
    from .guimanager import GuiEvent
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

    @property
    def position(self) -> Tuple[int, int]:
        """Widget draw position as an (x, y) tuple."""
        return self.draw_rect.x, self.draw_rect.y

    @position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        """Move the widget without changing size."""
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'widget pos must be a tuple of (x, y), got: {pos}')
        old_x, old_y = self.draw_rect.x, self.draw_rect.y
        hit_offset_x: Optional[int] = None
        hit_offset_y: Optional[int] = None
        if self.hit_rect is not None:
            hit_offset_x = self.hit_rect.x - old_x
            hit_offset_y = self.hit_rect.y - old_y
        self.draw_rect.x, self.draw_rect.y = pos
        if self.hit_rect is not None and hit_offset_x is not None and hit_offset_y is not None:
            self.hit_rect.x = self.draw_rect.x + hit_offset_x
            self.hit_rect.y = self.draw_rect.y + hit_offset_y

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        self.gui: "GuiManager" = gui
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

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        """Handle an input event. Subclasses return True on activation."""
        return False

    def build_gui_event(self, window: Optional["Window"] = None) -> "GuiEvent":
        """Create the GUI event emitted when this widget activates."""
        return self.gui.event(Event.Widget, widget_id=self.id, window=window)

    def should_handle_outside_collision(self) -> bool:
        """Return True when this widget should still process events off-collision."""
        return False

    def draw(self) -> None:
        """Draw the widget. Subclasses should call this first when needed."""
        if self.auto_restore_pristine:
            self.gui.restore_pristine(self.draw_rect, self.window)
