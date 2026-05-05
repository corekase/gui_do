"""SurfaceEffects — portable pixel-level surface post-processing.

All functions return a **new** :class:`pygame.Surface` and leave the
original unmodified.  All processing uses :mod:`pygame.surfarray` plus
standard-library math — no external image libraries, no OS-specific APIs.

Usage::

    from gui_do import SurfaceEffects

    blurred    = SurfaceEffects.blur(scene_surface, radius=8)
    greyed     = SurfaceEffects.greyscale(control_surface)
    tinted     = SurfaceEffects.tint(icon_surface, (255, 100, 0), alpha=120)
    brightened = SurfaceEffects.brightness(panel_surface, factor=1.4)
    pixelated  = SurfaceEffects.pixelate(sprite_surface, block_size=4)
    vignetted  = SurfaceEffects.vignette(scene_surface, strength=0.6)

numpy dependency
----------------
:mod:`pygame.surfarray` operations on 3-D pixel arrays require numpy.  If
numpy is not available the functions fall back to a slower pure-Python path
(significant for large surfaces).  The public API is identical regardless.
"""
from __future__ import annotations

import math
from typing import Tuple

import pygame
from pygame import Surface

try:
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def _fallback_pixels3d(surface: Surface) -> list:
    """Pure-Python pixel accessor when numpy is unavailable."""
    w, h = surface.get_size()
    return [
        [[surface.get_at((x, y))[c] for c in range(3)] for y in range(h)]
        for x in range(w)
    ]


class SurfaceEffects:
    """Static surface post-processing helpers.  All methods are ``@staticmethod``."""

    # ------------------------------------------------------------------
    # Blur
    # ------------------------------------------------------------------

    @staticmethod
    def blur(surface: Surface, radius: int) -> Surface:
        """Return a box-filtered blurred copy of *surface*.

        Uses repeated :func:`pygame.transform.smoothscale` downscale/upscale
        as a portable approximation of a Gaussian blur.  Output surface has
        the same size and mode as *surface*.

        Parameters
        ----------
        radius:
            Blur strength in pixels.  ``0`` returns an unchanged copy.
        """
        radius = max(0, int(radius))
        if radius == 0:
            return surface.copy()
        w, h = surface.get_size()
        if w <= 0 or h <= 0:
            return surface.copy()
        # Scale down then up — cheap blur approximation
        factor = max(1, radius // 2 + 1)
        small_w = max(1, w // factor)
        small_h = max(1, h // factor)
        small = pygame.transform.smoothscale(surface, (small_w, small_h))
        return pygame.transform.smoothscale(small, (w, h))

    # ------------------------------------------------------------------
    # Greyscale
    # ------------------------------------------------------------------

    @staticmethod
    def greyscale(surface: Surface) -> Surface:
        """Return a greyscale copy of *surface* using BT.601 luma coefficients."""
        result = surface.copy()
        if _HAS_NUMPY:
            import numpy as np
            arr = pygame.surfarray.pixels3d(result)
            # BT.601: 0.299 R + 0.587 G + 0.114 B
            luma = (arr[:, :, 0] * 0.299 +
                    arr[:, :, 1] * 0.587 +
                    arr[:, :, 2] * 0.114).astype(np.uint8)
            arr[:, :, 0] = luma
            arr[:, :, 1] = luma
            arr[:, :, 2] = luma
            del arr  # release pixel lock
        else:
            # Pure-Python fallback (slow but correct)
            w, h = result.get_size()
            for x in range(w):
                for y in range(h):
                    r, g, b, a = result.get_at((x, y))
                    luma = int(r * 0.299 + g * 0.587 + b * 0.114)
                    result.set_at((x, y), (luma, luma, luma, a))
        return result

    # ------------------------------------------------------------------
    # Tint
    # ------------------------------------------------------------------

    @staticmethod
    def tint(
        surface: Surface,
        color: Tuple[int, int, int],
        alpha: int = 128,
    ) -> Surface:
        """Blend a solid color over *surface* at the given *alpha* (0–255).

        Returns a new surface with the same size and SRCALPHA mode.
        """
        result = surface.copy()
        if not (result.get_flags() & pygame.SRCALPHA):
            alpha_result = Surface(result.get_size(), pygame.SRCALPHA)
            alpha_result.blit(result, (0, 0))
            result = alpha_result
        overlay = Surface(result.get_size(), pygame.SRCALPHA)
        overlay.fill((color[0], color[1], color[2], int(max(0, min(255, alpha)))))
        result.blit(overlay, (0, 0))
        return result

    # ------------------------------------------------------------------
    # Brightness
    # ------------------------------------------------------------------

    @staticmethod
    def brightness(surface: Surface, factor: float) -> Surface:
        """Scale RGB channels by *factor* (e.g. 1.5 = 50% brighter, 0.5 = darker).

        Alpha channel is preserved unchanged.
        """
        result = surface.copy()
        if _HAS_NUMPY:
            import numpy as np
            arr = pygame.surfarray.pixels3d(result)
            scaled = (arr.astype(np.float32) * factor).clip(0, 255).astype(np.uint8)
            arr[:] = scaled
            del arr
        else:
            w, h = result.get_size()
            for x in range(w):
                for y in range(h):
                    r, g, b, a = result.get_at((x, y))
                    result.set_at((x, y), (
                        min(255, int(r * factor)),
                        min(255, int(g * factor)),
                        min(255, int(b * factor)),
                        a,
                    ))
        return result

    # ------------------------------------------------------------------
    # Vignette
    # ------------------------------------------------------------------

    @staticmethod
    def vignette(surface: Surface, strength: float = 0.5) -> Surface:
        """Darken the edges of *surface* toward the center.

        Parameters
        ----------
        strength:
            0.0 = no effect, 1.0 = black edges.
        """
        strength = max(0.0, min(1.0, float(strength)))
        w, h = surface.get_size()
        result = surface.copy()
        # Create a radial mask
        mask = Surface((w, h), pygame.SRCALPHA)
        cx, cy = w / 2.0, h / 2.0
        max_dist = math.sqrt(cx * cx + cy * cy)
        if max_dist == 0:
            return result
        if _HAS_NUMPY:
            import numpy as np
            xs = np.arange(w, dtype=np.float32) - cx
            ys = np.arange(h, dtype=np.float32) - cy
            xx, yy = np.meshgrid(xs, ys, indexing="ij")
            dist = np.sqrt(xx * xx + yy * yy) / max_dist
            alpha = (dist * strength * 255).clip(0, 255).astype(np.uint8)
            arr = pygame.surfarray.pixels_alpha(mask)
            arr[:] = alpha
            del arr
        else:
            for x in range(w):
                for y in range(h):
                    dx, dy = x - cx, y - cy
                    dist = math.sqrt(dx * dx + dy * dy) / max_dist
                    a = int(min(255, dist * strength * 255))
                    mask.set_at((x, y), (0, 0, 0, a))
        result.blit(mask, (0, 0))
        return result

    # ------------------------------------------------------------------
    # Pixelate
    # ------------------------------------------------------------------

    @staticmethod
    def pixelate(surface: Surface, block_size: int) -> Surface:
        """Return a pixelated (mosaic) copy of *surface*.

        Parameters
        ----------
        block_size:
            Pixel block size in screen pixels.  Values < 2 return a copy.
        """
        block_size = max(1, int(block_size))
        if block_size < 2:
            return surface.copy()
        w, h = surface.get_size()
        small_w = max(1, w // block_size)
        small_h = max(1, h // block_size)
        small = pygame.transform.scale(surface, (small_w, small_h))
        return pygame.transform.scale(small, (w, h))
