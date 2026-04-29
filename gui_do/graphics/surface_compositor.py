"""SurfaceCompositor — named-layer surface compositor with dirty-region compositing.

Maintains a Z-ordered stack of named :class:`Layer` objects, each backed by its
own :class:`pygame.Surface`.  Every frame call :meth:`compose` to blit all
visible layers onto a target surface, restricting blitting to the union of
supplied dirty rects for optimal throughput.

Works naturally with :class:`~gui_do.DirtyRegionTracker` and
:class:`~gui_do.DrawContext`.

Usage::

    from gui_do import SurfaceCompositor

    compositor = SurfaceCompositor((800, 600))

    # Add layers (lower z_index draws first):
    compositor.add_layer("scene",   z_index=0)
    compositor.add_layer("overlay", z_index=10, opacity=0.9)
    compositor.add_layer("debug",   z_index=100, visible=False)

    # In the draw loop — draw into each layer's surface:
    compositor.layer_surface("scene").fill((0, 0, 0))
    scene.draw(compositor.layer_surface("scene"))

    overlay.draw(compositor.layer_surface("overlay"))

    # Compose everything onto the screen:
    compositor.compose(screen)

    # Enable/disable a layer:
    compositor.set_layer_visible("debug", True)
    compositor.set_layer_opacity("overlay", 0.5)

    # Dirty-region optimisation:
    dirty_rects = tracker.consume_dirty_regions()
    compositor.compose(screen, dirty_rects=dirty_rects)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pygame
from pygame import Rect, Surface


class Layer:
    """A single named compositing layer.

    Attributes
    ----------
    name:
        Unique string identifier.
    z_index:
        Rendering order — lower values draw beneath higher values.
    opacity:
        Blending opacity in [0.0, 1.0].  ``1.0`` = fully opaque.
    visible:
        When ``False`` the layer is skipped during :meth:`SurfaceCompositor.compose`.
    blend_flags:
        Passed directly to :meth:`pygame.Surface.blit` as ``special_flags``.
    """

    def __init__(
        self,
        name: str,
        size: Tuple[int, int],
        z_index: int = 0,
        opacity: float = 1.0,
        visible: bool = True,
        blend_flags: int = 0,
    ) -> None:
        self.name: str = name
        self.z_index: int = int(z_index)
        self.visible: bool = bool(visible)
        self.blend_flags: int = int(blend_flags)
        self._opacity: float = max(0.0, min(1.0, float(opacity)))
        self._surface: Surface = Surface(size, pygame.SRCALPHA)

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        self._opacity = max(0.0, min(1.0, float(value)))
        # Push opacity into surface alpha channel for per-layer blend
        self._surface.set_alpha(int(self._opacity * 255))

    @property
    def surface(self) -> Surface:
        """The backing :class:`pygame.Surface` for this layer."""
        return self._surface

    def resize(self, new_size: Tuple[int, int]) -> None:
        """Replace the backing surface with a new one of *new_size*."""
        prev = self._surface
        self._surface = Surface(new_size, pygame.SRCALPHA)
        self._surface.set_alpha(int(self._opacity * 255))
        del prev


class SurfaceCompositor:
    """Ordered stack of named :class:`Layer` objects composited per-frame.

    Parameters
    ----------
    size:
        ``(width, height)`` of all layers and the composition target.
    """

    def __init__(self, size: Tuple[int, int]) -> None:
        self._size: Tuple[int, int] = (int(size[0]), int(size[1]))
        self._layers: Dict[str, Layer] = {}
        self._z_sorted: List[Layer] = []   # maintained in z_index order

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def add_layer(
        self,
        name: str,
        *,
        z_index: int = 0,
        opacity: float = 1.0,
        visible: bool = True,
        blend_flags: int = 0,
    ) -> Layer:
        """Add a new layer named *name*.

        Raises ``ValueError`` if *name* is already registered.
        """
        if name in self._layers:
            raise ValueError(f"SurfaceCompositor: layer {name!r} already exists")
        layer = Layer(
            name=name,
            size=self._size,
            z_index=z_index,
            opacity=opacity,
            visible=visible,
            blend_flags=blend_flags,
        )
        layer.opacity = opacity   # apply initial alpha
        self._layers[name] = layer
        self._resort()
        return layer

    def remove_layer(self, name: str) -> None:
        """Remove the layer named *name*.  No-op if not present."""
        self._layers.pop(name, None)
        self._resort()

    def has_layer(self, name: str) -> bool:
        return name in self._layers

    def layer(self, name: str) -> Layer:
        """Return the :class:`Layer` named *name*.  Raises ``KeyError`` if absent."""
        return self._layers[name]

    def layer_surface(self, name: str) -> Surface:
        """Return the backing :class:`pygame.Surface` for layer *name*."""
        return self._layers[name].surface

    def layer_names(self) -> List[str]:
        """Return layer names in z-order (lowest z first)."""
        return [layer.name for layer in self._z_sorted]

    # ------------------------------------------------------------------
    # Per-layer controls
    # ------------------------------------------------------------------

    def set_layer_visible(self, name: str, visible: bool) -> None:
        self._layers[name].visible = bool(visible)

    def set_layer_opacity(self, name: str, opacity: float) -> None:
        self._layers[name].opacity = opacity

    def set_layer_z(self, name: str, z_index: int) -> None:
        self._layers[name].z_index = int(z_index)
        self._resort()

    def clear_layer(self, name: str) -> None:
        """Fill layer *name*'s surface with fully-transparent black."""
        self._layers[name].surface.fill((0, 0, 0, 0))

    def clear_all(self) -> None:
        """Clear every layer's surface."""
        for layer in self._layers.values():
            layer.surface.fill((0, 0, 0, 0))

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resize(self, new_size: Tuple[int, int]) -> None:
        """Resize all layers to *new_size*.  Existing content is lost."""
        self._size = (int(new_size[0]), int(new_size[1]))
        for layer in self._layers.values():
            layer.resize(self._size)

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(
        self,
        target: Surface,
        *,
        dirty_rects: Optional[List[Rect]] = None,
    ) -> None:
        """Blit all visible layers onto *target* in z-order.

        Parameters
        ----------
        target:
            Destination surface (typically the screen).
        dirty_rects:
            If supplied, only the union of these rects is blitted per layer
            (clips each :meth:`pygame.Surface.blit` call to the dirty region).
            Pass ``None`` (default) to blit the full layer unconditionally.
        """
        if dirty_rects:
            union: Optional[Rect] = dirty_rects[0].copy()
            for r in dirty_rects[1:]:
                union = union.union(r)
        else:
            union = None

        for layer in self._z_sorted:
            if not layer.visible:
                continue
            if union is not None:
                # Blit only the dirty region
                target.blit(
                    layer.surface,
                    union.topleft,
                    area=union,
                    special_flags=layer.blend_flags,
                )
            else:
                target.blit(layer.surface, (0, 0), special_flags=layer.blend_flags)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resort(self) -> None:
        self._z_sorted = sorted(self._layers.values(), key=lambda l: l.z_index)
