import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

from .constants import BaseEvent, GuiError, InteractiveState
from .widget import Widget
from ..widgets.frame import Frame as gFrame

if TYPE_CHECKING:
    from .guimanager import GuiManager


def _noop() -> None:
    pass


def _noop_event(_: BaseEvent) -> None:
    pass


class _ManagedTaskPanel:
    """GuiManager-owned bottom task panel container."""

    def __init__(
        self,
        gui: "GuiManager",
        height: int,
        x: int,
        reveal_pixels: int,
        auto_hide: bool,
        timer_interval: float,
        movement_step: int,
        backdrop: Optional[str],
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        if not isinstance(height, int) or height <= 0:
            raise GuiError(f'task_panel_height must be a positive int, got: {height}')
        if not isinstance(x, int):
            raise GuiError(f'task_panel_x must be an int, got: {x}')
        if not isinstance(reveal_pixels, int) or reveal_pixels < 1:
            raise GuiError(f'task_panel_reveal_pixels must be >= 1, got: {reveal_pixels}')
        if not isinstance(auto_hide, bool):
            raise GuiError('task_panel_auto_hide must be a bool')
        if not isinstance(movement_step, int) or movement_step <= 0:
            raise GuiError(f'task_panel_movement_step must be > 0, got: {movement_step}')
        if timer_interval <= 0:
            raise GuiError(f'task_panel_timer_interval must be > 0, got: {timer_interval}')
        screen_rect = gui.surface.get_rect()
        if x < 0 or x >= screen_rect.width:
            raise GuiError(f'task_panel_x must be in range [0, {screen_rect.width - 1}], got: {x}')
        width = screen_rect.width - x
        if reveal_pixels >= height:
            raise GuiError(f'task_panel_reveal_pixels must be < panel height ({height}), got: {reveal_pixels}')
        self.gui: "GuiManager" = gui
        self.x: int = x
        self.width: int = width
        self.height: int = height
        self.visible: bool = True
        self.widgets: List[Widget] = []
        self.surface: Surface = pygame.surface.Surface((self.width, self.height)).convert()
        self.pristine: Optional[Surface] = None
        self.reveal_pixels: int = reveal_pixels
        self.auto_hide: bool = auto_hide
        self.timer_interval: float = timer_interval
        self.movement_step: int = movement_step
        self._shown_y: int = screen_rect.height - self.height
        self._hidden_y: int = screen_rect.height - self.reveal_pixels
        self.y: int = self._hidden_y if self.auto_hide else self._shown_y
        self._hovered: bool = False
        self._timer_id: Tuple[str, int] = ('task-panel-motion', id(self))
        self._preamble: Callable[[], None] = preamble if callable(preamble) else _noop
        self._event_handler: Callable[[BaseEvent], None] = event_handler if callable(event_handler) else _noop_event
        self._postamble: Callable[[], None] = postamble if callable(postamble) else _noop
        self.backdrop: Optional[str] = backdrop
        if backdrop is None:
            frame = gFrame(gui, 'task_panel_frame', Rect(0, 0, self.width, self.height))
            frame.state = InteractiveState.Idle
            frame.surface = self.surface
            frame.draw()
            self.pristine = gui.copy_graphic_area(self.surface, self.surface.get_rect()).convert()
        else:
            gui.set_pristine(backdrop, self)
        gui.timers.add_timer(self._timer_id, self.timer_interval, self.animate)

    def dispose(self) -> None:
        self.gui.timers.remove_timer(self._timer_id)

    def run_preamble(self) -> None:
        self._preamble()

    def run_postamble(self) -> None:
        self._postamble()

    def handle_event(self, event: BaseEvent) -> None:
        self._event_handler(event)

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        self._preamble = preamble if preamble is not None else _noop
        self._event_handler = event_handler if event_handler is not None else _noop_event
        self._postamble = postamble if postamble is not None else _noop

    def get_rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)

    def refresh_targets(self) -> None:
        screen_rect = self.gui.surface.get_rect()
        self._shown_y = screen_rect.height - self.height
        self._hidden_y = screen_rect.height - self.reveal_pixels
        self._hovered = self.get_rect().collidepoint(self.gui.get_mouse_pos())

    def draw_background(self) -> None:
        if self.pristine is None:
            raise GuiError('task panel pristine is not initialized')
        self.gui.restore_pristine(self.surface.get_rect(), self)

    def animate(self) -> None:
        if not self.visible:
            return
        self.refresh_targets()
        target_y = self._hidden_y
        if not self.auto_hide or self._hovered:
            target_y = self._shown_y
        if self.y < target_y:
            self.y = min(target_y, self.y + self.movement_step)
        elif self.y > target_y:
            self.y = max(target_y, self.y - self.movement_step)

    def set_visible(self, visible: bool) -> None:
        if not isinstance(visible, bool):
            raise GuiError('task panel visibility must be a bool')
        self.visible = visible
        if visible:
            self.refresh_targets()

    def set_auto_hide(self, auto_hide: bool) -> None:
        if not isinstance(auto_hide, bool):
            raise GuiError('task panel auto_hide must be a bool')
        self.auto_hide = auto_hide
        if not auto_hide:
            self.refresh_targets()
            self.y = self._shown_y

    def set_reveal_pixels(self, reveal_pixels: int) -> None:
        if not isinstance(reveal_pixels, int):
            raise GuiError(f'task panel reveal_pixels must be an int, got: {reveal_pixels}')
        if reveal_pixels < 1:
            raise GuiError(f'task panel reveal_pixels must be >= 1, got: {reveal_pixels}')
        if reveal_pixels >= self.height:
            raise GuiError(f'task panel reveal_pixels must be < panel height ({self.height}), got: {reveal_pixels}')
        self.reveal_pixels = reveal_pixels
        self.refresh_targets()

    def set_movement_step(self, movement_step: int) -> None:
        if not isinstance(movement_step, int):
            raise GuiError(f'task panel movement_step must be an int, got: {movement_step}')
        if movement_step <= 0:
            raise GuiError(f'task panel movement_step must be > 0, got: {movement_step}')
        self.movement_step = movement_step

    def set_timer_interval(self, timer_interval: float) -> None:
        if timer_interval <= 0:
            raise GuiError(f'task panel timer_interval must be > 0, got: {timer_interval}')
        self.timer_interval = timer_interval
        self.gui.timers.remove_timer(self._timer_id)
        self.gui.timers.add_timer(self._timer_id, self.timer_interval, self.animate)
