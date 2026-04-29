"""Display surface creation helpers."""
from __future__ import annotations

import warnings

import pygame


def create_display(
    size: tuple[int, int],
    *,
    fullscreen: bool = True,
    scaled: bool = True,
    vsync: bool = True,
) -> "pygame.Surface":
    """Create and return a pygame display surface.

    Requests vsync when *vsync* is ``True`` and silently degrades to no-vsync
    when the display driver cannot satisfy the request (the pygame-ce warning
    ``"no fast renderer available"`` is suppressed in that case).

    Parameters
    ----------
    size:
        Desired display resolution as an ``(width, height)`` tuple.
    fullscreen:
        Pass ``pygame.FULLSCREEN`` to ``set_mode`` when ``True``.
    scaled:
        Pass ``pygame.SCALED`` to ``set_mode`` when ``True`` (letterbox/scale
        to fit the physical display).
    vsync:
        Request vertical synchronization.  Silently falls back to no-vsync
        when the driver cannot provide it.
    """
    # Centralize pygame startup in display creation for top-level apps.
    pygame.init()

    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    if scaled:
        flags |= pygame.SCALED

    if not vsync:
        return pygame.display.set_mode(size, flags=flags, vsync=0)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="no fast renderer available")
        try:
            return pygame.display.set_mode(size, flags=flags, vsync=1)
        except Exception:
            return pygame.display.set_mode(size, flags=flags, vsync=0)
