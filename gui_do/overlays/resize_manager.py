"""ResizeManager — listens for window resize events and reflows constrained layouts."""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

if TYPE_CHECKING:
    from ..layout.constraint_layout import ConstraintLayout
    from ..core.event_bus import EventBus

# Topic published to the EventBus when the window resizes.
WINDOW_RESIZED_TOPIC = "window_resized"


class ResizeManager:
    """Centralised handler for window resize events.

    When the pygame ``VIDEORESIZE`` event fires (or :meth:`notify_resize` is
    called directly), the manager:

    1. Records the new window size.
    2. Calls :meth:`ConstraintLayout.apply` on every registered layout using
       the full window rect as the parent rect.
    3. Publishes ``"window_resized"`` on the supplied :class:`EventBus` with
       a ``(width, height)`` payload.
    4. Calls any additional resize callbacks registered via
       :meth:`on_resize`.

    Usage::

        mgr = ResizeManager(initial_size=(800, 600), event_bus=app.events)
        mgr.register_layout(my_layout)
        mgr.on_resize(lambda w, h: camera.update_viewport(w, h))

        # In your event loop:
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                mgr.handle_pygame_event(event)
    """

    def __init__(
        self,
        initial_size: Tuple[int, int] = (800, 600),
        event_bus: "Optional[EventBus]" = None,
    ) -> None:
        w, h = int(initial_size[0]), int(initial_size[1])
        self._size: Tuple[int, int] = (max(1, w), max(1, h))
        self._event_bus: "Optional[EventBus]" = event_bus
        self._layouts: List["ConstraintLayout"] = []
        self._callbacks: List[Callable[[int, int], None]] = []
        self._resize_count: int = 0

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_layout(self, layout: "ConstraintLayout") -> None:
        """Register a :class:`ConstraintLayout` to be reflowed on resize.

        The layout is applied immediately with the current window size so
        that initial layout is correct before the first resize event.
        """
        if layout not in self._layouts:
            self._layouts.append(layout)
        parent_rect = self._window_rect()
        layout.apply(parent_rect)

    def unregister_layout(self, layout: "ConstraintLayout") -> bool:
        """Unregister a layout.  Returns True if it was registered."""
        try:
            self._layouts.remove(layout)
            return True
        except ValueError:
            return False

    def on_resize(self, callback: Callable[[int, int], None]) -> Callable[[], None]:
        """Subscribe to resize events.

        *callback* receives ``(width, height)`` of the new window size.
        Returns an *unsubscribe* callable.
        """
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._callbacks.append(callback)

        def _unsub() -> None:
            try:
                self._callbacks.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_pygame_event(self, event: pygame.event.Event) -> bool:
        """Process a raw pygame event.

        Returns ``True`` if it was a ``VIDEORESIZE`` event that was handled,
        ``False`` otherwise.
        """
        if event.type == pygame.VIDEORESIZE:
            w = max(1, int(getattr(event, "w", self._size[0])))
            h = max(1, int(getattr(event, "h", self._size[1])))
            self.notify_resize(w, h)
            return True
        return False

    def notify_resize(self, width: int, height: int) -> None:
        """Manually trigger a resize notification with the given dimensions.

        This is useful for testing or when resizing is detected via a
        mechanism other than the ``VIDEORESIZE`` pygame event.
        """
        w = max(1, int(width))
        h = max(1, int(height))
        self._size = (w, h)
        self._resize_count += 1
        parent_rect = self._window_rect()

        for layout in self._layouts:
            try:
                layout.apply(parent_rect)
            except Exception:
                pass

        if self._event_bus is not None:
            try:
                self._event_bus.publish(WINDOW_RESIZED_TOPIC, (w, h))
            except Exception:
                pass

        for cb in self._callbacks:
            try:
                cb(w, h)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> Tuple[int, int]:
        """Current window size as ``(width, height)``."""
        return self._size

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def resize_count(self) -> int:
        """Number of resize events processed since creation."""
        return self._resize_count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _window_rect(self) -> Rect:
        return Rect(0, 0, self._size[0], self._size[1])
