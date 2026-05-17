"""Display surface creation helpers."""
from __future__ import annotations

import os
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
    force_windows_hardware_renderer = os.getenv("GUI_DO_WINDOWS_FORCE_HARDWARE_RENDERER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    allow_windows_vsync = os.getenv("GUI_DO_WINDOWS_ALLOW_VSYNC", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if os.name == "nt" and not force_windows_hardware_renderer:
        # Force SDL renderer to software to avoid GPU overlay/compositor paths
        # that can show monitor-only artifacts not present in captures.
        os.environ.setdefault("SDL_RENDER_DRIVER", "software")
        if not allow_windows_vsync:
            vsync = False

    # Centralize pygame startup in display creation for top-level apps.
    pygame.init()

    # Windows fullscreen presentation paths can exhibit monitor-only artifacts
    # (not visible in framebuffer captures) when desktop resolution already
    # matches the requested logical size. Use borderless fallback only in that
    # specific mode so high-resolution desktops can still use SCALED.
    force_windows_true_fullscreen = os.getenv("GUI_DO_WINDOWS_FORCE_TRUE_FULLSCREEN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    use_windows_borderless_fallback = False
    if os.name == "nt" and fullscreen and not force_windows_true_fullscreen:
        requested_size = (int(size[0]), int(size[1]))
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            desktop_size = (int(desktop_sizes[0][0]), int(desktop_sizes[0][1]))
            if desktop_size[0] > requested_size[0] or desktop_size[1] > requested_size[1]:
                scaled = True
            # Fallback is only for panel-desktop mode where no scaling is needed.
            if desktop_size == requested_size:
                size = desktop_size
                fullscreen = False
                scaled = False
                use_windows_borderless_fallback = True

    # Windows + FULLSCREEN + SCALED has shown compositor artifacts in runtime
    # despite clean framebuffer captures; default to the safer non-SCALED path.
    allow_windows_scaled_fullscreen = os.getenv("GUI_DO_WINDOWS_ALLOW_SCALED_FULLSCREEN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if (
        os.name == "nt"
        and fullscreen
        and scaled
        and force_windows_true_fullscreen
        and not allow_windows_scaled_fullscreen
    ):
        scaled = False

    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    elif os.name == "nt" and use_windows_borderless_fallback:
        flags |= pygame.NOFRAME
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
