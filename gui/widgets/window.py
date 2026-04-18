from __future__ import annotations

import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple
from ..utility.events import colours, GuiError, InteractiveState
from ..utility.lifecycle.lifecycle_callbacks import LifecycleCallbacks
from .frame import Frame

if TYPE_CHECKING:
    from ..utility.events import BaseEvent
    from ..utility.gui_manager import GuiManager
    from ..utility.widget import Widget

class Window:
    """Top-level container with title bar, child widgets, and lifecycle hooks."""

    @property
    def visible(self) -> bool:
        """Visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Visible."""
        if not isinstance(value, bool):
            raise GuiError('window visible must be a bool')
        self._visible = value

    @property
    def position(self) -> Tuple[int, int]:
        """Position."""
        return self.x, self.y

    @position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        """Position."""
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'window pos must be a tuple of (x, y), got: {pos}')
        self.x, self.y = pos

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
        """Create Window."""
        if not isinstance(title, str) or title == '':
            raise GuiError('window title must be a non-empty string')
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'window pos must be a tuple of (x, y), got: {pos}')
        if not isinstance(size, tuple) or len(size) != 2:
            raise GuiError(f'window size must be a tuple of (w, h), got: {size}')
        if size[0] <= 0 or size[1] <= 0:
            raise GuiError(f'window size must be positive, got: {size}')
        self.gui: "GuiManager" = gui
        self.x: int
        self.y: int
        self.x, self.y = pos
        self.width: int
        self.height: int
        self.width, self.height = size
        self.titlebar_size: int = self.gui.graphics_factory.get_titlebar_height()
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
        self.position = pos
        self.title_bar_inactive_bitmap: Surface
        self.title_bar_active_bitmap: Surface
        chrome = self.gui.graphics_factory.build_window_chrome_visuals(self.gui, title, self.width, self.titlebar_size)
        self.title_bar_inactive_bitmap = chrome.title_bar_inactive
        self.title_bar_active_bitmap = chrome.title_bar_active
        self.title_bar_rect: Rect = self.title_bar_active_bitmap.get_rect()
        self.window_widget_lower_bitmap: Surface = chrome.lower_widget
        self._visible: bool = True
        callbacks = LifecycleCallbacks.from_optionals(preamble, event_handler, postamble)
        self._preamble: Callable[[], None] = callbacks.preamble
        self._event_handler: Callable[["BaseEvent"], None] = callbacks.event_handler
        self._postamble: Callable[[], None] = callbacks.postamble

    def run_postamble(self) -> None:
        """Run postamble."""
        self._postamble()

    def run_preamble(self) -> None:
        """Run preamble."""
        self._preamble()

    def get_title_bar_rect(self) -> Rect:
        """Get title bar rect."""
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def get_widget_rect(self) -> Rect:
        """Get widget rect."""
        x, y, w, h = self.window_widget_lower_bitmap.get_rect()
        return Rect(self.get_window_rect().x + 2 + self.get_window_rect().width - self.titlebar_size, self.get_title_bar_rect().y + 1, w, h)
    def get_window_rect(self) -> Rect:
        """Return window bounds including title bar."""
        return Rect(self.x, self.y - self.titlebar_size - 1, self.width, self.height + self.titlebar_size - 1)

    def handle_event(self, event: "BaseEvent") -> None:
        """Handle event."""
        self._event_handler(event)

    def draw_title_bar_active(self) -> None:
        """Draw title bar active."""
        self.gui.surface.blit(self.title_bar_active_bitmap, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_lower_bitmap, self.get_widget_rect())

    def draw_title_bar_inactive(self) -> None:
        """Draw title bar inactive."""
        self.gui.surface.blit(self.title_bar_inactive_bitmap, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_lower_bitmap, self.get_widget_rect())

    def draw_window(self) -> None:
        """Draw window."""
        self.gui.restore_pristine(self.surface.get_rect(), self)

    def _window_save_pristine(self) -> None:
        """Window save pristine."""
        self.pristine = self.gui.copy_graphic_area(self.surface, self.surface.get_rect()).convert()
