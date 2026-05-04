"""SceneGraph2D — parent-child 2D transform tree for canvas-based content.

Provides a lightweight scene graph with translation and scale transform
inheritance so child nodes draw in their parent's local coordinate space.
Rotation is intentionally omitted for the UI-centric baseline (add-on if
needed later).

Integrates with :class:`~gui_do.CanvasControl` and the existing graphics
primitives (:class:`~gui_do.ParticleSystem`, :class:`~gui_do.TileMap`,
:class:`~gui_do.SpriteSheet`) via the :class:`Node2D` draw hook.

Usage::

    from gui_do import SceneGraph2D, Node2D, Camera2D
    import pygame

    graph = SceneGraph2D()
    camera = Camera2D(viewport_rect=pygame.Rect(0, 0, 800, 600), zoom=1.0)

    # Build a hierarchy:
    player = Node2D("player", pos=(200.0, 200.0), scale=(1.0, 1.0))
    body   = Node2D("body",   pos=(0.0, 0.0))
    shadow = Node2D("shadow", pos=(5.0, 10.0))

    player.add_child(body)
    player.add_child(shadow)
    graph.add(player)

    # Custom draw hook per node:
    def draw_player(surface, world_x, world_y, scale_x, scale_y):
        pygame.draw.circle(surface, (0, 200, 80),
                           (int(world_x), int(world_y)), int(12 * scale_x))

    body.on_draw = draw_player

    # Per-frame in your CanvasControl event / post-frame handler:
    def on_canvas_draw(surface):
        graph.draw(surface, camera)

    # Move player:
    player.x += 5.0

    # Remove from graph:
    graph.remove(player)
"""
from __future__ import annotations

from typing import Callable, Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

# DrawHook: called with (surface, world_x, world_y, scale_x, scale_y)
DrawHook = Callable[["pygame.Surface", float, float, float, float], None]


# ---------------------------------------------------------------------------
# Camera2D
# ---------------------------------------------------------------------------


class Camera2D:
    """2D viewport with position offset and zoom.

    Parameters
    ----------
    viewport_rect:
        The screen-space rect the camera renders into (e.g. ``CanvasControl.draw_rect``).
    zoom:
        Initial zoom factor.  ``1.0`` = 1:1, ``2.0`` = 2x magnification.
    x, y:
        Initial camera world-space position (top-left of visible area).
    """

    def __init__(
        self,
        viewport_rect: "pygame.Rect",
        *,
        zoom: float = 1.0,
        x: float = 0.0,
        y: float = 0.0,
    ) -> None:
        self.viewport_rect = viewport_rect
        self.zoom = float(max(0.001, zoom))
        self.x = float(x)
        self.y = float(y)

    def world_to_screen(self, wx: float, wy: float) -> Tuple[float, float]:
        """Convert world-space coordinates to screen-space pixels."""
        sx = (wx - self.x) * self.zoom + self.viewport_rect.x
        sy = (wy - self.y) * self.zoom + self.viewport_rect.y
        return sx, sy

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Convert screen-space pixels to world-space coordinates."""
        wx = (sx - self.viewport_rect.x) / self.zoom + self.x
        wy = (sy - self.viewport_rect.y) / self.zoom + self.y
        return wx, wy

    def pan(self, dx: float, dy: float) -> None:
        """Move the camera by *(dx, dy)* in world units."""
        self.x += float(dx)
        self.y += float(dy)

    def pan_screen(self, dx: float, dy: float) -> None:
        """Move the camera by *(dx, dy)* screen pixels, accounting for zoom."""
        self.x += float(dx) / self.zoom
        self.y += float(dy) / self.zoom

    def set_zoom(self, zoom: float, *, anchor_screen: Optional[Tuple[float, float]] = None) -> None:
        """Set zoom level, optionally anchored to a screen-space point.

        When *anchor_screen* is provided the world point under that screen
        coordinate remains stationary after the zoom change (useful for
        scroll-wheel zoom centred on the cursor).
        """
        zoom = max(0.001, float(zoom))
        if anchor_screen is not None:
            # Compute world point before zoom
            wx, wy = self.screen_to_world(*anchor_screen)
            self.zoom = zoom
            # Adjust camera position so the same world point is under anchor
            ax, ay = anchor_screen
            self.x = wx - (ax - self.viewport_rect.x) / self.zoom
            self.y = wy - (ay - self.viewport_rect.y) / self.zoom
        else:
            self.zoom = zoom


# ---------------------------------------------------------------------------
# Node2D
# ---------------------------------------------------------------------------


class Node2D:
    """A node in the 2D scene graph with local position and scale.

    Parameters
    ----------
    name:
        Unique name within its parent (used for debugging and ``find``).
    pos:
        Local position ``(x, y)`` relative to the parent node.
    scale:
        Local scale ``(sx, sy)`` relative to the parent node.
    visible:
        When ``False`` this node and all its children are skipped during draw.
    on_draw:
        Optional draw hook: ``(surface, world_x, world_y, scale_x, scale_y) -> None``.
    """

    def __init__(
        self,
        name: str,
        *,
        pos: Tuple[float, float] = (0.0, 0.0),
        scale: Tuple[float, float] = (1.0, 1.0),
        visible: bool = True,
        on_draw: Optional[DrawHook] = None,
    ) -> None:
        self.name = str(name)
        self.x: float = float(pos[0])
        self.y: float = float(pos[1])
        self.scale_x: float = float(scale[0])
        self.scale_y: float = float(scale[1])
        self.visible: bool = bool(visible)
        self.on_draw: Optional[DrawHook] = on_draw

        self._children: List["Node2D"] = []
        self._parent: Optional["Node2D"] = None

        # Cached world transform: (world_x, world_y, world_sx, world_sy)
        self._world_transform: Optional[Tuple[float, float, float, float]] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @pos.setter
    def pos(self, value: Tuple[float, float]) -> None:
        self.x, self.y = float(value[0]), float(value[1])
        self._invalidate_transform()

    @property
    def scale(self) -> Tuple[float, float]:
        return (self.scale_x, self.scale_y)

    @scale.setter
    def scale(self, value: Tuple[float, float]) -> None:
        self.scale_x, self.scale_y = float(value[0]), float(value[1])
        self._invalidate_transform()

    # ------------------------------------------------------------------
    # Children
    # ------------------------------------------------------------------

    def add_child(self, child: "Node2D") -> None:
        """Append *child* as a child of this node."""
        if child._parent is not None:
            child._parent.remove_child(child)
        self._children.append(child)
        child._parent = self
        child._invalidate_transform()

    def remove_child(self, child: "Node2D") -> bool:
        """Remove *child* from this node's children.  Returns ``True`` if found."""
        try:
            self._children.remove(child)
            child._parent = None
            child._invalidate_transform()
            return True
        except ValueError:
            return False

    def children(self) -> List["Node2D"]:
        return list(self._children)

    def find(self, name: str) -> Optional["Node2D"]:
        """DFS search for a descendant node with the given *name*."""
        for child in self._children:
            if child.name == name:
                return child
            result = child.find(name)
            if result is not None:
                return result
        return None

    @property
    def parent(self) -> Optional["Node2D"]:
        return self._parent

    # ------------------------------------------------------------------
    # World transform
    # ------------------------------------------------------------------

    def _invalidate_transform(self) -> None:
        """Mark this node and all descendants as needing transform recomputation."""
        self._world_transform = None
        for child in self._children:
            child._invalidate_transform()

    def world_transform(self) -> Tuple[float, float, float, float]:
        """Return ``(world_x, world_y, world_scale_x, world_scale_y)``."""
        if self._world_transform is not None:
            return self._world_transform
        if self._parent is None:
            t = (self.x, self.y, self.scale_x, self.scale_y)
        else:
            px, py, psx, psy = self._parent.world_transform()
            wx = px + self.x * psx
            wy = py + self.y * psy
            wsx = psx * self.scale_x
            wsy = psy * self.scale_y
            t = (wx, wy, wsx, wsy)
        self._world_transform = t
        return t

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: "pygame.Surface",
        camera: Camera2D,
    ) -> None:
        """Draw this node and its visible children using *camera*."""
        if not self.visible:
            return
        wx, wy, wsx, wsy = self.world_transform()
        sx, sy = camera.world_to_screen(wx, wy)
        screen_sx = wsx * camera.zoom
        screen_sy = wsy * camera.zoom
        if self.on_draw is not None:
            try:
                self.on_draw(surface, sx, sy, screen_sx, screen_sy)
            except Exception:
                pass
        for child in self._children:
            child.draw(surface, camera)


# ---------------------------------------------------------------------------
# SceneGraph2D
# ---------------------------------------------------------------------------


class SceneGraph2D:
    """Manager for a collection of root-level :class:`Node2D` objects.

    All nodes added via :meth:`add` are drawn in insertion order.

    Usage::

        graph = SceneGraph2D()
        camera = Camera2D(viewport_rect=canvas.draw_rect)

        player = Node2D("player", pos=(100, 100))
        graph.add(player)

        # Per-frame:
        graph.draw(surface, camera)
    """

    def __init__(self) -> None:
        self._roots: List[Node2D] = []

    # ------------------------------------------------------------------
    # Root management
    # ------------------------------------------------------------------

    def add(self, node: Node2D) -> None:
        """Add *node* as a root node (drawn in insertion order)."""
        if node not in self._roots:
            self._roots.append(node)

    def remove(self, node: Node2D) -> bool:
        """Remove *node* from root nodes.  Returns ``True`` if found."""
        try:
            self._roots.remove(node)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all root nodes."""
        self._roots.clear()

    def find(self, name: str) -> Optional[Node2D]:
        """Search all root nodes and their descendants for *name*."""
        for root in self._roots:
            if root.name == name:
                return root
            result = root.find(name)
            if result is not None:
                return result
        return None

    @property
    def root_count(self) -> int:
        return len(self._roots)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", camera: Camera2D) -> None:
        """Draw all root nodes (and their subtrees) using *camera*."""
        for root in self._roots:
            root.draw(surface, camera)

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def _all_nodes(self) -> Iterator[Node2D]:
        """DFS iteration over all nodes in the graph."""
        stack = list(self._roots)
        while stack:
            node = stack.pop(0)
            yield node
            stack = list(node._children) + stack

    def find_all(self, *, visible_only: bool = False) -> List[Node2D]:
        """Return all nodes in the graph.

        Parameters
        ----------
        visible_only:
            When ``True``, exclude nodes whose :attr:`~Node2D.visible` is
            ``False``.
        """
        return [
            n for n in self._all_nodes()
            if not visible_only or n.visible
        ]
