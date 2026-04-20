from __future__ import annotations

import logging
from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Callable, Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.input.normalized_event import normalize_input_event
from ..utility.intermediates.interactive import BaseInteractive, InteractiveState
from ..utility.events import GuiError

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window

_logger = logging.getLogger(__name__)

class ArrowBox(BaseInteractive):
    """Arrow button with press-and-hold repeat activation."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None, repeat_activation_ms: int = 150) -> None:
        """Create ArrowBox."""
        super().__init__(gui, id, rect)
        if not isinstance(repeat_activation_ms, int):
            raise GuiError(f'repeat_activation_ms must be an int, got: {type(repeat_activation_ms).__name__}')
        if repeat_activation_ms <= 0:
            raise GuiError(f'repeat_activation_ms must be > 0, got: {repeat_activation_ms}')
        visuals = self.gui.graphics_factory.build_arrow_visuals(rect, direction)
        self.idle = visuals.idle
        self.hover = visuals.hover
        self.armed = visuals.armed
        self.disabled_graphic = visuals.disabled
        self.hit_rect = visuals.hit_rect
        self.on_activate = on_activate
        self.repeat_activation_ms: int = repeat_activation_ms
        self._timer_id: Optional[str] = None

    def _on_disabled_changed(self, disabled: bool) -> None:
        """Stop repeat activation immediately when disabled."""
        super()._on_disabled_changed(disabled)
        if disabled:
            self._clear_timer()

    def leave(self) -> None:
        """Leave."""
        self._clear_timer()
        super().leave()
        self.state = InteractiveState.Idle

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Emit once on press and continue firing while held via timer."""
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        normalized = normalize_input_event(event)
        if not super().handle_event(event, window):
            self._clear_timer()
            return False
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN and normalized.is_left_down:
                self.state = InteractiveState.Armed
                if self.on_activate is not None and self._timer_id is None:
                    timer_id = f'{self.id}.timer'
                    self.gui.timers.add_timer(timer_id, self.repeat_activation_ms, self._invoke_on_activate)
                    self._timer_id = timer_id
                return True
        if self.state == InteractiveState.Armed:
            if event.type == MOUSEBUTTONUP and normalized.is_left_up:
                self._clear_timer()
                self.state = InteractiveState.Hover
                if self.on_activate is not None:
                    return False
                return True
        return False

    def should_handle_outside_collision(self) -> bool:
        """Keep receiving release events while armed so repeat can stop cleanly."""
        return self.state == InteractiveState.Armed

    def _clear_timer(self) -> None:
        """Clear timer."""
        timer_id = getattr(self, '_timer_id', None)
        if timer_id is None:
            return
        try:
            gui = getattr(self, 'gui', None)
            timers = getattr(gui, 'timers', None)
            if timers is not None:
                timers.remove_timer(timer_id)
        except Exception as exc:
            widget_id = getattr(self, 'id', '<unknown>')
            _logger.warning('ArrowBox timer cleanup failed for %s: %s: %s', widget_id, type(exc).__name__, exc)
        finally:
            self._timer_id = None

    def _invoke_on_activate(self) -> None:
        """Invoke on activate."""
        if self.on_activate is not None:
            self.on_activate()

    def __del__(self) -> None:
        try:
            self._clear_timer()
        except Exception as exc:
            _logger.debug('ArrowBox destructor cleanup failed: %s: %s', type(exc).__name__, exc)
