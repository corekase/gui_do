from __future__ import annotations

import pygame
from collections import deque
import logging
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Dict, Optional, Tuple, TYPE_CHECKING, Union
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.events import GuiError, InteractiveState, CanvasEvent
from ..utility.widget import Widget
from .frame import Frame
from .events.canvas_event_packet import CanvasEventPacket

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window

_logger = logging.getLogger(__name__)

class Canvas(Widget):
    """Off-screen drawing surface that queues canvas-local input events."""

    _DEFAULT_MAX_QUEUED_EVENTS = 128
    _OVERFLOW_MODES = ('drop_oldest', 'reject_new')

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> None:
        """Create Canvas."""
        if on_activate is not None and not callable(on_activate):
            raise GuiError('on_activate must be callable when provided')
        super().__init__(gui, id, rect)
        self.canvas: Surface = pygame.surface.Surface((rect.width, rect.height)).convert()
        if backdrop is None:
            frame = Frame(gui, 'canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = InteractiveState.Idle
            frame.surface = self.canvas
            frame.draw()
            self.pristine = self.gui.copy_graphic_area(self.canvas, self.canvas.get_rect()).convert()
        else:
            self.gui.set_pristine(backdrop, self)
        self.on_activate = on_activate
        self.auto_restore_pristine: bool = automatic_pristine
        self._events: deque[CanvasEventPacket] = deque()
        self._configure_max_queued_events()
        self.dropped_events: int = 0
        self.last_overflow: bool = False
        self.on_overflow: Optional[Callable[[int, int], None]] = None
        self._overflow_callback_strict: bool = False
        self._overflow_mode: str = 'drop_oldest'
        self.coalesce_motion_events: bool = True
        self.queued_event: bool = False
        self.CEvent: Optional["CanvasEventPacket"] = None

    def get_canvas_surface(self) -> Surface:
        """Get canvas surface."""
        return self.canvas

    def leave(self) -> None:
        """Canvas has no leave-state transition; keep hook explicit for Widget contract."""
        return

    def get_event_queue_limit(self) -> int:
        """Get event queue limit."""
        maxlen = self._events.maxlen
        return 0 if maxlen is None else maxlen

    def get_event_queue_stats(self) -> Dict[str, Union[int, bool, str]]:
        """Get event queue stats."""
        return {
            'queued': len(self._events),
            'limit': self.get_event_queue_limit(),
            'dropped_events': self.dropped_events,
            'last_overflow': self.last_overflow,
            'coalesce_motion_events': self.coalesce_motion_events,
            'overflow_mode': self._overflow_mode,
        }

    def reset_event_queue_stats(self, clear_queue: bool = False) -> None:
        """Reset event queue stats."""
        if not isinstance(clear_queue, bool):
            raise GuiError(f'clear_queue must be a bool, got: {type(clear_queue).__name__}')
        self.dropped_events = 0
        self.last_overflow = False
        if clear_queue:
            self._events.clear()
            self.queued_event = False
            self.CEvent = None

    def read_event(self) -> Optional[CanvasEventPacket]:
        """Pop the next queued canvas event, or None when empty."""
        if not self._events:
            self.queued_event = False
            self.CEvent = None
            return None
        event = self._events.popleft()
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None
        return event

    def set_event_queue_limit(self, max_events: int) -> None:
        """Set event queue limit."""
        self._configure_max_queued_events(max_events)
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None

    def _configure_max_queued_events(self, max_events: Optional[int] = None) -> None:
        """Configure max queued events."""
        if max_events is None:
            max_events = self._DEFAULT_MAX_QUEUED_EVENTS
        if not isinstance(max_events, int):
            raise GuiError(f'max_events must be an int, got: {type(max_events).__name__}')
        if max_events <= 0:
            raise GuiError(f'max_events must be > 0, got: {max_events}')
        if self._events.maxlen == max_events:
            return
        self._events = deque(self._events, maxlen=max_events)

    def set_motion_coalescing(self, enabled: bool) -> None:
        """Set motion coalescing."""
        if not isinstance(enabled, bool):
            raise GuiError(f'motion coalescing flag must be bool, got: {type(enabled).__name__}')
        self.coalesce_motion_events = enabled

    def set_overflow_handler(self, callback: Optional[Callable[[int, int], None]], *, strict: bool = False) -> None:
        """Set overflow handler."""
        if callback is not None and not callable(callback):
            raise GuiError('overflow callback must be callable when provided')
        if not isinstance(strict, bool):
            raise GuiError(f'overflow callback strict flag must be bool, got: {type(strict).__name__}')
        self.on_overflow = callback
        self._overflow_callback_strict = strict

    def set_overflow_mode(self, mode: str) -> None:
        """Set overflow mode."""
        if not isinstance(mode, str) or mode not in self._OVERFLOW_MODES:
            raise GuiError(f'overflow mode must be one of {self._OVERFLOW_MODES}, got: {mode!r}')
        self._overflow_mode = mode

    def get_overflow_mode(self) -> str:
        """Get overflow mode."""
        return self._overflow_mode

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Queue supported events while focused and signal activation on enqueue."""
        if self.disabled:
            return False
        if event.type not in (MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        locked_owner = (self.gui.locking_object is self) and self.gui.mouse_locked
        if self.get_collide(window) or locked_owner:
            canvas_x, canvas_y = self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)
            packet = CanvasEventPacket()
            packet.pos = (canvas_x - self.draw_rect.x, canvas_y - self.draw_rect.y)
            if event.type == MOUSEWHEEL:
                packet.type = CanvasEvent.MouseWheel
                packet.y = getattr(event, 'y', None)
            elif event.type == MOUSEMOTION:
                packet.type = CanvasEvent.MouseMotion
                packet.rel = getattr(event, 'rel', None)
            elif event.type == MOUSEBUTTONDOWN:
                packet.type = CanvasEvent.MouseButtonDown
                packet.button = getattr(event, 'button', None)
            elif event.type == MOUSEBUTTONUP:
                packet.type = CanvasEvent.MouseButtonUp
                packet.button = getattr(event, 'button', None)
            # Coalescing keeps motion floods from starving click/wheel processing.
            if (
                self.coalesce_motion_events
                and packet.type == CanvasEvent.MouseMotion
                and len(self._events) > 0
                and self._events[-1].type == CanvasEvent.MouseMotion
            ):
                self._events[-1] = packet
                self.queued_event = True
                self.CEvent = self._events[0]
                return True
            was_full = len(self._events) == self._events.maxlen
            self.last_overflow = was_full
            if was_full:
                self.dropped_events += 1
                self._notify_overflow()
                if getattr(self, '_overflow_mode', 'drop_oldest') == 'reject_new':
                    return True
            self._events.append(packet)
            self.queued_event = True
            self.CEvent = self._events[0]
            return True
        else:
            return False

    def _notify_overflow(self) -> None:
        """Notify overflow."""
        if self.on_overflow is None:
            return
        try:
            self.on_overflow(1, self.dropped_events)
        except Exception as exc:
            if getattr(self, '_overflow_callback_strict', False):
                raise GuiError('canvas overflow callback failed in strict mode') from exc
            _logger.warning('Canvas overflow callback failed: %s: %s', type(exc).__name__, exc)

    def draw(self) -> None:
        """Blit canvas contents into the owning GUI surface."""
        self.surface.blit(self.canvas, self.draw_rect)
        if self.disabled:
            self._blit_disabled_overlay()
        if self.auto_restore_pristine:
            self.restore_pristine()

    def focused(self) -> bool:
        """Return True when mouse is inside this canvas."""
        if self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)):
            return True
        else:
            return False

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        """Restore a region from the canvas pristine snapshot."""
        if self.pristine is None:
            raise GuiError('canvas pristine image is not initialized')
        if area is None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, (area.x, area.y), area)
