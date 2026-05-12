"""CursorManager — priority-stack cursor management for pygame applications.

Controls push cursor requests with a priority level.  Each frame the manager
resolves the highest-priority active request and calls
``pygame.mouse.set_cursor()`` only when the resolved shape changes — avoiding
redundant system calls.

Uses portable system cursors from ``pygame``; no image files are required.

Usage::

    from gui_do import CursorManager, CursorShape

    cursor_mgr = CursorManager()

    # Push a resize cursor while the user drags a splitter:
    handle = cursor_mgr.push(CursorShape.RESIZE_H, priority=10)

    # Per frame — resolves and applies the winning cursor:
    cursor_mgr.update()

    # Release when the drag ends; the previous cursor is restored automatically:
    handle.release()

    # Reset to the default shape (e.g. on scene change):
    cursor_mgr.reset()
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# CursorShape
# ---------------------------------------------------------------------------


class CursorShape(Enum):
    """Portable system cursor shapes backed by ``pygame.SYSTEM_CURSOR_*``."""

    ARROW = "arrow"
    TEXT = "text"
    WAIT = "wait"
    CROSSHAIR = "crosshair"
    RESIZE_NW_SE = "resize_nw_se"
    RESIZE_NE_SW = "resize_ne_sw"
    RESIZE_H = "resize_h"
    RESIZE_V = "resize_v"
    RESIZE_ALL = "resize_all"
    FORBIDDEN = "forbidden"
    HAND = "hand"


_PYGAME_CURSOR_MAP: dict = {}   # populated lazily to avoid import at module load


def _pygame_cursor(shape: CursorShape):
    """Return the pygame system cursor constant for *shape*."""
    global _PYGAME_CURSOR_MAP
    if not _PYGAME_CURSOR_MAP:
        try:
            import pygame
            _PYGAME_CURSOR_MAP = {
                CursorShape.ARROW:       pygame.SYSTEM_CURSOR_ARROW,
                CursorShape.TEXT:        pygame.SYSTEM_CURSOR_IBEAM,
                CursorShape.WAIT:        pygame.SYSTEM_CURSOR_WAIT,
                CursorShape.CROSSHAIR:   pygame.SYSTEM_CURSOR_CROSSHAIR,
                CursorShape.RESIZE_NW_SE: pygame.SYSTEM_CURSOR_SIZENWSE,
                CursorShape.RESIZE_NE_SW: pygame.SYSTEM_CURSOR_SIZENESW,
                CursorShape.RESIZE_H:    pygame.SYSTEM_CURSOR_SIZEWE,
                CursorShape.RESIZE_V:    pygame.SYSTEM_CURSOR_SIZENS,
                CursorShape.RESIZE_ALL:  pygame.SYSTEM_CURSOR_SIZEALL,
                CursorShape.FORBIDDEN:   pygame.SYSTEM_CURSOR_NO,
                CursorShape.HAND:        pygame.SYSTEM_CURSOR_HAND,
            }
        except Exception:
            _PYGAME_CURSOR_MAP = {s: None for s in CursorShape}
    return _PYGAME_CURSOR_MAP.get(shape)


# ---------------------------------------------------------------------------
# CursorHandle
# ---------------------------------------------------------------------------


class CursorHandle:
    """Returned by :meth:`CursorManager.push`.  Call :meth:`release` when done."""

    def __init__(self, shape: CursorShape, priority: int, manager: "CursorManager") -> None:
        self._shape = shape
        self._priority = priority
        self._manager = manager
        self._released = False

    @property
    def shape(self) -> CursorShape:
        return self._shape

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def released(self) -> bool:
        return self._released

    def release(self) -> None:
        """Remove this cursor request so a lower-priority request takes effect."""
        if not self._released:
            self._released = True
            self._manager._remove(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"CursorHandle(shape={self._shape.value!r}, priority={self._priority})"


# ---------------------------------------------------------------------------
# CursorManager
# ---------------------------------------------------------------------------


class CursorManager:
    """Priority-stack cursor resolver.

    Any number of cursor requests may be active simultaneously; the one with
    the highest *priority* wins.  Ties are broken by insertion order (later
    push wins).  When all requests are released the manager reverts to
    :attr:`default_shape`.

    Parameters
    ----------
    default_shape:
        Cursor shown when no request is active (default: ``ARROW``).
    """

    def __init__(self, default_shape: CursorShape = CursorShape.ARROW) -> None:
        self._default = default_shape
        self._stack: List[CursorHandle] = []
        self._current: Optional[CursorShape] = None

    @property
    def default_shape(self) -> CursorShape:
        return self._default

    @default_shape.setter
    def default_shape(self, shape: CursorShape) -> None:
        if not isinstance(shape, CursorShape):
            raise TypeError("default_shape must be a CursorShape")
        self._default = shape

    def push(self, shape: CursorShape, priority: int = 0) -> CursorHandle:
        """Register a cursor request and return a handle.

        Parameters
        ----------
        shape:
            The desired cursor shape.
        priority:
            Higher values beat lower values.  Use consistent priority bands
            (e.g. drag operations at 100, hover at 10) to avoid conflicts.
        """
        if not isinstance(shape, CursorShape):
            raise TypeError("shape must be a CursorShape")
        handle = CursorHandle(shape, int(priority), self)
        self._stack.append(handle)
        return handle

    def _remove(self, handle: CursorHandle) -> None:
        try:
            self._stack.remove(handle)
        except ValueError:
            pass

    def update(self) -> None:
        """Resolve the winning cursor and apply it if changed.  Call once per frame."""
        resolved = self._resolve()
        if resolved == self._current:
            return
        self._current = resolved
        pygame_cursor = _pygame_cursor(resolved)
        if pygame_cursor is not None:
            try:
                import pygame
                pygame.mouse.set_cursor(pygame_cursor)
            except Exception:
                pass

    def _resolve(self) -> CursorShape:
        if not self._stack:
            return self._default
        # Highest priority wins; ties resolved by last insertion
        best = max(self._stack, key=lambda h: h.priority)
        return best.shape

    def reset(self) -> None:
        """Release all pending requests and revert to the default shape."""
        self._stack.clear()
        self._current = None
        self.update()

    @property
    def active_shape(self) -> CursorShape:
        """Return the currently resolved cursor shape."""
        return self._resolve()

    @property
    def request_count(self) -> int:
        """Return the number of active (unreleased) cursor requests."""
        return len(self._stack)
