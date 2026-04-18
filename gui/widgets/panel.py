import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import TYPE_CHECKING, Callable, Optional, Tuple
from ..utility.constants import GuiError, InteractiveState
from .frame import Frame
from .window import Window

if TYPE_CHECKING:
    from ..utility.constants import BaseEvent
    from ..utility.guimanager import GuiManager

def _noop() -> None:
    pass

def _noop_event(_: "BaseEvent") -> None:
    pass

class Panel(Window):
    """Bottom-docked container that can auto-hide and reveal on hover."""

    @property
    def position(self) -> Tuple[int, int]:
        return self.x, self.y

    @position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'panel pos must be a tuple of (x, y), got: {pos}')
        self.x, self.y = pos

    def __init__(
        self,
        gui: "GuiManager",
        panel_id: str,
        size: Tuple[int, int],
        x: int = 0,
        reveal_pixels: int = 4,
        auto_hide: bool = True,
        timer_interval: float = 16.0,
        movement_step: int = 4,
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[["BaseEvent"], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        if not isinstance(panel_id, str) or panel_id == '':
            raise GuiError('panel id must be a non-empty string')
        if not isinstance(size, tuple) or len(size) != 2:
            raise GuiError(f'panel size must be a tuple of (w, h), got: {size}')
        if not isinstance(x, int):
            raise GuiError(f'panel x must be an int, got: {x}')
        if size[0] <= 0 or size[1] <= 0:
            raise GuiError(f'panel size must be positive, got: {size}')
        if not isinstance(reveal_pixels, int):
            raise GuiError(f'panel reveal_pixels must be an int, got: {reveal_pixels}')
        if reveal_pixels < 1:
            raise GuiError(f'panel reveal_pixels must be >= 1, got: {reveal_pixels}')
        if reveal_pixels >= size[1]:
            raise GuiError(f'panel reveal_pixels must be < panel height ({size[1]}), got: {reveal_pixels}')
        if not isinstance(auto_hide, bool):
            raise GuiError('panel auto_hide must be a bool')
        if not isinstance(movement_step, int):
            raise GuiError(f'panel movement_step must be an int, got: {movement_step}')
        if movement_step <= 0:
            raise GuiError(f'panel movement_step must be > 0, got: {movement_step}')
        if timer_interval <= 0:
            raise GuiError(f'panel timer_interval must be > 0, got: {timer_interval}')

        self.id: str = panel_id
        self.gui: "GuiManager" = gui
        self.width, self.height = size
        self._validate_bounds(x)
        self._shown_y: int = self.gui.surface.get_rect().height - self.height
        self._hidden_y: int = self.gui.surface.get_rect().height - reveal_pixels
        self._hovered: bool = False
        self._auto_hide: bool = auto_hide
        self.reveal_pixels: int = reveal_pixels
        self.timer_interval: float = timer_interval
        self.movement_step: int = movement_step
        self._timer_id = ('panel-motion', self)

        self.x = x
        self.y = self._shown_y
        self.position = (self.x, self.y)
        self.surface: Surface = pygame.surface.Surface(size).convert()
        self.pristine: Optional[Surface] = None
        if backdrop is None:
            frame = Frame(gui, f'{panel_id}_frame', Rect(0, 0, size[0], size[1]))
            frame.state = InteractiveState.Idle
            frame.surface = self.surface
            frame.draw()
        else:
            self.gui.set_pristine(backdrop, self)
        self._window_save_pristine()
        self.widgets = []
        self._visible = True
        self._preamble: Callable[[], None] = preamble if callable(preamble) else _noop
        self._event_handler: Callable[["BaseEvent"], None] = event_handler if callable(event_handler) else _noop_event
        self._postamble: Callable[[], None] = postamble if callable(postamble) else _noop

        self.gui.timers.add_timer(self._timer_id, self.timer_interval, self._animate)

    @property
    def auto_hide(self) -> bool:
        return self._auto_hide

    @auto_hide.setter
    def auto_hide(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise GuiError('panel auto_hide must be a bool')
        self._auto_hide = value
        if not value:
            self.y = self._shown_y

    def draw_title_bar_active(self) -> None:
        # Panels intentionally do not render a title bar.
        pass

    def draw_title_bar_inactive(self) -> None:
        # Panels intentionally do not render a title bar.
        pass

    def get_title_bar_rect(self) -> Rect:
        return Rect(0, 0, 0, 0)

    def get_widget_rect(self) -> Rect:
        return Rect(0, 0, 0, 0)

    def get_window_rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)

    def _animate(self) -> None:
        if not self.visible:
            return
        self._refresh_targets()
        target_y = self._hidden_y
        if not self._auto_hide or self._hovered:
            target_y = self._shown_y
        if self.y < target_y:
            self.y = min(target_y, self.y + self.movement_step)
        elif self.y > target_y:
            self.y = max(target_y, self.y - self.movement_step)

    def _refresh_targets(self) -> None:
        self._validate_bounds(self.x)
        self._shown_y = self.gui.surface.get_rect().height - self.height
        self._hidden_y = self.gui.surface.get_rect().height - self.reveal_pixels
        self._hovered = self.get_window_rect().collidepoint(self.gui.get_mouse_pos())

    def _validate_bounds(self, x: int) -> None:
        screen_rect = self.gui.surface.get_rect()
        if x < 0:
            raise GuiError(f'panel x must be >= 0, got: {x}')
        if x + self.width > screen_rect.width:
            raise GuiError(
                f'panel must fit within screen width ({screen_rect.width}), '
                f'got x={x}, width={self.width}'
            )
