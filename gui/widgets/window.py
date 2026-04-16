import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple
from ..utility.constants import colours, GuiError, ContainerKind, InteractiveState
from .frame import Frame

if TYPE_CHECKING:
    from ..utility.constants import BaseEvent
    from ..utility.guimanager import GuiManager
    from ..utility.widget import Widget

def _noop() -> None:
    pass

def _noop_event(_: "BaseEvent") -> None:
    pass

class Window:
    """Top-level container with title bar, child widgets, and lifecycle hooks."""

    def __init__(
        self,
        gui: "GuiManager",
        title: str,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[["BaseEvent"], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        if not isinstance(title, str) or title == '':
            raise GuiError('window title must be a non-empty string')
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'window pos must be a tuple of (x, y), got: {pos}')
        if not isinstance(size, tuple) or len(size) != 2:
            raise GuiError(f'window size must be a tuple of (w, h), got: {size}')
        if size[0] <= 0 or size[1] <= 0:
            raise GuiError(f'window size must be positive, got: {size}')
        self.gui: "GuiManager" = gui
        self.ContainerKind = ContainerKind.Window
        self.x: int
        self.y: int
        self.x, self.y = pos
        self.width: int
        self.height: int
        self.width, self.height = size
        self.titlebar_size: int = 24
        self.surface: pygame.Surface = pygame.surface.Surface(size).convert()
        self.pristine: Optional[Surface] = None
        if backdrop is None:
            frame = Frame(gui, 'window_frame', Rect(0, 0, size[0], size[1]))
            frame.state = InteractiveState.Idle
            frame.surface = self.surface
            frame.draw()
        else:
            self.gui.set_pristine(backdrop, self)
        self._window_save_pristine()
        self.widgets: List["Widget"] = []
        self.set_pos(pos)
        self.title_bar_inactive_bitmap: Surface
        self.title_bar_active_bitmap: Surface
        self.title_bar_inactive_bitmap, self.title_bar_active_bitmap = self.gui.bitmap_factory.draw_window_title_bar_bitmaps(self.gui, title, self.width, self.titlebar_size)
        self.title_bar_rect: Rect = self.title_bar_active_bitmap.get_rect()
        self.window_widget_lower_bitmap: Surface = self.gui.bitmap_factory.draw_window_lower_widget_bitmap(self.titlebar_size - 2, colours['full'], colours['medium'])
        self._visible: bool = True
        self._preamble: Callable[[], None] = preamble if callable(preamble) else _noop
        self._event_handler: Callable[["BaseEvent"], None] = event_handler if callable(event_handler) else _noop_event
        self._postamble: Callable[[], None] = postamble if callable(postamble) else _noop

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise GuiError('window visible must be a bool')
        self._visible = value

    def set_pos(self, pos: Tuple[int, int]) -> None:
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'window pos must be a tuple of (x, y), got: {pos}')
        self.x, self.y = pos

    def _window_save_pristine(self) -> None:
        self.pristine = self.gui.copy_graphic_area(self.surface, self.surface.get_rect()).convert()

    def draw_title_bar_inactive(self) -> None:
        self.gui.surface.blit(self.title_bar_inactive_bitmap, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_lower_bitmap, self.get_widget_rect())

    def draw_title_bar_active(self) -> None:
        self.gui.surface.blit(self.title_bar_active_bitmap, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_lower_bitmap, self.get_widget_rect())

    def draw_window(self) -> None:
        self.gui.restore_pristine(self.surface.get_rect(), self)

    def run_preamble(self) -> None:
        self._preamble()

    def handle_event(self, event: "BaseEvent") -> None:
        self._event_handler(event)

    def run_postamble(self) -> None:
        self._postamble()

    def get_title_bar_rect(self) -> Rect:
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def get_window_rect(self) -> Rect:
        """Return window bounds including title bar."""
        return Rect(self.x, self.y - self.titlebar_size - 1, self.width, self.height + self.titlebar_size - 1)

    def get_widget_rect(self) -> Rect:
        x, y, w, h = self.window_widget_lower_bitmap.get_rect()
        return Rect(self.get_window_rect().x + 2 + self.get_window_rect().width - self.titlebar_size, self.get_title_bar_rect().y + 1, w, h)
