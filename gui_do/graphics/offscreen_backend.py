"""OffscreenBackend — headless render target protocol for CI and server-side use.

Decouples widget and graphics code from the live pygame display by providing a
:class:`RenderTarget` protocol and two concrete implementations:

- :class:`LiveRenderTarget` — wraps the real ``pygame.display`` surface.
- :class:`OffscreenRenderTarget` — wraps a plain ``pygame.Surface`` created
  with ``SRCALPHA``, usable without calling ``pygame.display.init()``.

This resolves the long-standing ``convert_alpha()`` failures in headless tests:
code that needs a compositing surface should call
:func:`create_surface` instead of ``Surface(...).convert_alpha()`` so the
headless path stays compatible.

Usage (application code)::

    from gui_do import RenderTarget, LiveRenderTarget, OffscreenRenderTarget

    # Production: wrap the display surface obtained from create_display()
    target = LiveRenderTarget(screen_surface)
    target.fill((0, 0, 0))
    target.blit(widget_surface, (10, 20))
    target.flip()

    # CI / headless: create without display
    target = OffscreenRenderTarget(width=800, height=600)
    target.fill((0, 0, 0))
    # ... draw into target.surface ...
    png_bytes = target.to_png_bytes()  # for screenshot regression tests

Factory helper::

    from gui_do import create_render_target

    # Returns LiveRenderTarget when display is initialised, OffscreenRenderTarget otherwise.
    target = create_render_target(800, 600)

Surface creation helper::

    from gui_do import create_surface

    # Always returns a surface usable for alpha blending without display.init().
    surface = create_surface(200, 100)
"""
from __future__ import annotations

import io
from typing import Optional, Protocol, Sequence, Tuple, runtime_checkable

import pygame
from pygame import Rect, Surface


# ---------------------------------------------------------------------------
# create_surface — portable alpha-capable surface creation
# ---------------------------------------------------------------------------


def create_surface(
    width: int,
    height: int,
    *,
    flags: int = pygame.SRCALPHA,
) -> Surface:
    """Return a new :class:`pygame.Surface` without requiring display init.

    Uses ``SRCALPHA`` by default so the result supports per-pixel alpha
    blending identically to ``Surface.convert_alpha()`` but without the
    display initialisation requirement.

    Parameters
    ----------
    width, height:
        Dimensions in pixels.
    flags:
        Optional pygame surface flags.  Defaults to ``SRCALPHA``.
    """
    return Surface((int(width), int(height)), flags)


# ---------------------------------------------------------------------------
# RenderTarget protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class RenderTarget(Protocol):
    """Protocol for render destinations.

    Both :class:`LiveRenderTarget` and :class:`OffscreenRenderTarget` satisfy
    this protocol.  Code that draws to a target should accept ``RenderTarget``
    rather than ``pygame.Surface`` directly so it can be tested headlessly.
    """

    @property
    def surface(self) -> Surface:
        """The underlying :class:`pygame.Surface`."""
        ...

    @property
    def size(self) -> Tuple[int, int]:
        """Width and height of the render target."""
        ...

    def fill(self, color: Tuple[int, int, int], rect: Optional[Rect] = None) -> None:
        """Fill *rect* (or the entire target) with *color*."""
        ...

    def blit(
        self,
        source: Surface,
        dest: Tuple[int, int],
        area: Optional[Rect] = None,
    ) -> Rect:
        """Blit *source* onto this target at *dest*."""
        ...

    def flip(self) -> None:
        """Present the current frame (no-op for offscreen targets)."""
        ...


# ---------------------------------------------------------------------------
# LiveRenderTarget
# ---------------------------------------------------------------------------


class LiveRenderTarget:
    """Wraps the live pygame display surface for production rendering.

    Parameters
    ----------
    surface:
        The surface returned by ``pygame.display.set_mode()``.
    """

    def __init__(self, surface: Surface) -> None:
        self._surface = surface

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def size(self) -> Tuple[int, int]:
        return self._surface.get_size()

    def fill(self, color: Tuple[int, int, int], rect: Optional[Rect] = None) -> None:
        if rect is not None:
            self._surface.fill(color, rect)
        else:
            self._surface.fill(color)

    def blit(
        self,
        source: Surface,
        dest: Tuple[int, int],
        area: Optional[Rect] = None,
    ) -> Rect:
        if area is not None:
            return self._surface.blit(source, dest, area)
        return self._surface.blit(source, dest)

    def flip(self) -> None:
        pygame.display.flip()


# ---------------------------------------------------------------------------
# OffscreenRenderTarget
# ---------------------------------------------------------------------------


class OffscreenRenderTarget:
    """A headless render target backed by a plain ``pygame.Surface``.

    No ``pygame.display`` initialisation is required.  Suitable for:
    - Headless CI test assertions
    - Screenshot regression tests via :meth:`to_png_bytes`
    - Server-side rendering

    Parameters
    ----------
    width, height:
        Dimensions in pixels.
    """

    def __init__(self, width: int, height: int) -> None:
        self._surface = create_surface(int(width), int(height))

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def size(self) -> Tuple[int, int]:
        return self._surface.get_size()

    def fill(self, color: Tuple[int, int, int], rect: Optional[Rect] = None) -> None:
        if rect is not None:
            self._surface.fill(color, rect)
        else:
            self._surface.fill(color)

    def blit(
        self,
        source: Surface,
        dest: Tuple[int, int],
        area: Optional[Rect] = None,
    ) -> Rect:
        if area is not None:
            return self._surface.blit(source, dest, area)
        return self._surface.blit(source, dest)

    def flip(self) -> None:
        """No-op for offscreen targets — there is no display to update."""

    def to_png_bytes(self) -> bytes:
        """Encode the current surface contents as a PNG and return raw bytes.

        Useful for screenshot regression tests::

            target.fill((255, 0, 0))
            png = target.to_png_bytes()
            assert len(png) > 0
        """
        buf = io.BytesIO()
        pygame.image.save(self._surface, buf, "png")
        return buf.getvalue()

    def get_at(self, pos: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Return the RGBA color of the pixel at *pos* (for test assertions)."""
        return self._surface.get_at(pos)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_render_target(width: int, height: int) -> "LiveRenderTarget | OffscreenRenderTarget":
    """Return a :class:`LiveRenderTarget` if the display is initialised, else :class:`OffscreenRenderTarget`.

    Parameters
    ----------
    width, height:
        Dimensions passed to :class:`OffscreenRenderTarget` when creating
        headlessly.  Ignored when wrapping the live display.
    """
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        return LiveRenderTarget(pygame.display.get_surface())
    return OffscreenRenderTarget(width, height)
