"""DebugOverlay — live visual diagnostic layer for development.

When enabled the :class:`DebugOverlay` renders on top of all scene content
as a ``DrawPhase.DEBUG`` pass.  It has zero production cost: the overlay
skips all rendering unless :attr:`enabled` is ``True``.

Visualizations
--------------
- **Widget rects** — color-coded outlines by control type (e.g. green for
  buttons, blue for containers, yellow for text, etc.)
- **Focus chain** — magenta border around the currently focused node
- **Dirty region flashes** — translucent red flash on dirty rects for one
  frame (requires a :class:`~gui_do.DirtyRegionTracker`)
- **Hover highlight** — cyan outline on the topmost hovered node
- **Accessibility badges** — small ``accessibility_role`` labels
- **FPS counter** — frame rate overlay in the corner
- **Event log** — tail of the last N event kinds received

Usage::

    from gui_do import DebugOverlay

    debug = DebugOverlay()
    debug.enabled = True   # toggle at runtime (e.g. F12 key binding)

    # In the render loop, after the scene draw:
    debug.draw(screen_surface, scene, theme,
               focused_id=focus_manager.focused_node_id,
               hovered_id=input_snapshot.topmost_hovered_id,
               fps=clock.get_fps())

    # Log an event kind for the event-log tail:
    debug.log_event(event.kind.name)

    # Clear the event log:
    debug.clear_event_log()
"""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect, Surface

if TYPE_CHECKING:
    from ..app.scene import Scene
    from ..theme.color_theme import ColorTheme
    from .dirty_region import DirtyRegionTracker


# Role → outline color
_ROLE_COLORS: dict = {
    "button": (80, 220, 80),
    "toggle": (80, 220, 80),
    "slider": (80, 220, 160),
    "scrollbar": (80, 220, 160),
    "text": (220, 220, 80),
    "label": (220, 220, 80),
    "input": (220, 160, 80),
    "container": (80, 120, 220),
    "panel": (80, 120, 220),
    "window": (160, 80, 220),
    "canvas": (80, 200, 200),
    "list": (200, 200, 80),
    "grid": (200, 200, 80),
    "image": (200, 120, 200),
}
_DEFAULT_ROLE_COLOR = (160, 160, 160)
_FOCUS_COLOR = (255, 60, 255)
_HOVER_COLOR = (60, 240, 240)
_DIRTY_COLOR = (255, 40, 40, 60)
_FPS_COLOR = (255, 255, 255)
_LOG_COLOR = (200, 255, 200)
_LOG_BG = (0, 0, 0, 160)


class DebugOverlay:
    """Developer diagnostic overlay drawn as a DrawPhase.DEBUG pass.

    Parameters
    ----------
    max_event_log:
        Maximum number of event-kind strings kept in the rolling log.
    show_rects:
        Draw color-coded control outlines.
    show_roles:
        Draw accessibility-role badges next to each control.
    show_dirty:
        Flash dirty rects for one frame (requires ``dirty_tracker``).
    show_fps:
        Render an FPS counter in the top-left corner.
    show_event_log:
        Render the rolling event log tail.
    show_focus:
        Highlight the focused node.
    show_hover:
        Highlight the topmost hovered node.
    """

    def __init__(
        self,
        *,
        max_event_log: int = 12,
        show_rects: bool = True,
        show_roles: bool = False,
        show_dirty: bool = True,
        show_fps: bool = True,
        show_event_log: bool = True,
        show_focus: bool = True,
        show_hover: bool = True,
    ) -> None:
        self.enabled: bool = False
        self.show_rects = show_rects
        self.show_roles = show_roles
        self.show_dirty = show_dirty
        self.show_fps = show_fps
        self.show_event_log = show_event_log
        self.show_focus = show_focus
        self.show_hover = show_hover
        self._event_log: Deque[str] = deque(maxlen=int(max_event_log))
        self._dirty_flash: List[Rect] = []
        self._font: Optional[pygame.font.Font] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_event(self, event_kind: str) -> None:
        """Append *event_kind* to the rolling event log."""
        self._event_log.append(str(event_kind))

    def clear_event_log(self) -> None:
        """Clear the event log."""
        self._event_log.clear()

    def feed_dirty_rects(self, rects: List[Rect]) -> None:
        """Supply dirty rects to flash for the next draw call."""
        self._dirty_flash = [Rect(r) for r in rects]

    def toggle(self) -> bool:
        """Toggle enabled state. Returns the new state."""
        self.enabled = not self.enabled
        return self.enabled

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: Surface,
        scene: "Optional[Scene]",
        *,
        focused_id: Optional[str] = None,
        hovered_id: Optional[str] = None,
        fps: float = 0.0,
        dirty_tracker: "Optional[DirtyRegionTracker]" = None,
    ) -> None:
        """Draw the debug overlay onto *surface*.

        Parameters
        ----------
        surface:
            Render target (typically the screen surface).
        scene:
            Active scene whose node tree is visualized.  Pass ``None`` to
            skip node-tree visualization.
        focused_id:
            The ``control_id`` of the currently focused node (or ``None``).
        hovered_id:
            The ``control_id`` of the topmost hovered node (or ``None``).
        fps:
            Current frame rate for the FPS counter.
        dirty_tracker:
            Optional tracker whose pending dirty rects are flashed.
        """
        if not self.enabled:
            return

        font = self._get_font()

        # --- Dirty flash ---
        if self.show_dirty:
            dirty_rects = list(self._dirty_flash)
            if dirty_tracker is not None:
                dirty_rects.extend(dirty_tracker.dirty_union() and [dirty_tracker.dirty_union()] or [])
            self._dirty_flash = []
            flash_surf = Surface((1, 1), pygame.SRCALPHA)
            for dr in dirty_rects:
                if dr and dr.width > 0 and dr.height > 0:
                    fs = Surface((dr.width, dr.height), pygame.SRCALPHA)
                    fs.fill(_DIRTY_COLOR)
                    surface.blit(fs, (dr.x, dr.y))

        # --- Node tree visualization ---
        if scene is not None:
            try:
                nodes = list(scene._walk_nodes())
            except Exception:
                nodes = []

            for node in nodes:
                rect = getattr(node, "rect", None)
                if rect is None:
                    continue
                role = getattr(node, "accessibility_role", "control")
                node_id = getattr(node, "control_id", "")

                if self.show_rects:
                    color = _ROLE_COLORS.get(role.lower(), _DEFAULT_ROLE_COLOR)
                    pygame.draw.rect(surface, color, rect, 1)

                if self.show_focus and node_id == focused_id:
                    pygame.draw.rect(surface, _FOCUS_COLOR, rect.inflate(4, 4), 2)

                if self.show_hover and node_id == hovered_id:
                    pygame.draw.rect(surface, _HOVER_COLOR, rect.inflate(2, 2), 2)

                if self.show_roles and font is not None and role:
                    label_surf = font.render(role[:12], True, _DEFAULT_ROLE_COLOR)
                    surface.blit(label_surf, (rect.x + 2, rect.y + 2))

        # --- FPS counter ---
        if self.show_fps and font is not None:
            fps_text = f"FPS: {fps:.1f}"
            fps_surf = font.render(fps_text, True, _FPS_COLOR)
            # Dark background
            bg = Surface((fps_surf.get_width() + 4, fps_surf.get_height() + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            surface.blit(bg, (2, 2))
            surface.blit(fps_surf, (4, 3))

        # --- Event log tail ---
        if self.show_event_log and font is not None and self._event_log:
            log_lines = list(self._event_log)
            line_h = font.get_linesize()
            log_y = surface.get_height() - len(log_lines) * line_h - 4
            for line in log_lines:
                text_surf = font.render(line, True, _LOG_COLOR)
                bg = Surface((text_surf.get_width() + 4, line_h), pygame.SRCALPHA)
                bg.fill(_LOG_BG)
                surface.blit(bg, (2, log_y))
                surface.blit(text_surf, (4, log_y + 1))
                log_y += line_h

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_font(self) -> Optional[pygame.font.Font]:
        if self._font is None:
            try:
                self._font = pygame.font.SysFont("monospace", 11)
            except Exception:
                pass
        return self._font
