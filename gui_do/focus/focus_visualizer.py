"""Focus visualization with dashed rectangles and smooth fade-out."""
from __future__ import annotations

import pygame


class FocusVisualizer:
    """Manages visual focus indicators (dashed rectangles).

    Draws a dashed rectangle around the currently focused node on every render
    pass.  The focused node is read directly from ``app.focus`` at draw time so
    the hint is always in sync with actual focus state — no separate tracking
    or timeout is needed.  Painter's draw order (screen roots before windows)
    handles natural occlusion automatically.
    """

    # Dashed rectangle rendering
    DASH_WIDTH = 2  # Width of dashes in pixels
    GAP_WIDTH = 2  # Width of gaps in pixels
    LINE_WIDTH = 1  # Thickness of rectangle outline
    PADDING = 2  # Padding between control rect and focus rectangle

    def __init__(self, app) -> None:
        self.app = app

    def _focused_node(self):
        """Return the currently focused UI node when hint drawing is enabled."""
        if not self.app.focus.should_draw_focus_hint():
            return None
        node = self.app.focus.focused_node
        if self._should_suppress_node_hint(node):
            return None
        return node

    def _should_suppress_node_hint(self, node) -> bool:
        if node is None:
            return False
        overlay = getattr(self.app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        if not callable(has_overlay) or not has_overlay("__command_palette__"):
            return False
        module_name = str(getattr(node.__class__, "__module__", ""))
        # While command palette is open, only draw focus hints for palette-owned controls.
        return module_name != "gui_do.overlays.command_palette_manager"

    def draw_hints(self, surface: "pygame.Surface", theme) -> None:
        """Draw focus hint for the currently focused node."""
        node = self._focused_node()
        if node is None:
            return
        self._draw_dashed_rect(surface, node, theme=theme)

    def draw_hint_for_scene_root(self, surface: "pygame.Surface", theme, root_node) -> None:
        """Draw the current hint only when it belongs to the given scene root subtree.

        This allows hints to be rendered inline with scene root draw order so any later
        top-layer roots (for example active windows) naturally occlude the hint.
        """
        node = self._focused_node()
        if node is None:
            return
        if node.root() is not root_node:
            return
        if self._find_ancestor_window(node) is not None:
            return
        self._draw_dashed_rect(surface, node, theme=theme)

    def draw_hint_for_window(self, surface: "pygame.Surface", theme, window_node) -> None:
        """Draw hint when focused node belongs to the given window subtree."""
        node = self._focused_node()
        if node is None:
            return
        if self._find_ancestor_window(node) is not window_node:
            return
        self._draw_dashed_rect(surface, node, theme=theme)

    def draw_window_focus_hint(self, surface: "pygame.Surface", theme) -> None:
        """Draw the window-focus hint (Ctrl+Tab cycling) around the focused window.

        Suppressed while the command palette overlay is open.
        """
        window_focus = getattr(self.app, "window_focus", None)
        if window_focus is None or not window_focus.should_draw_window_focus_hint():
            return
        window = window_focus.focused_window
        if window is None or not window.visible:
            return
        # Suppress while command palette is open.
        overlay = getattr(self.app, "overlay", None)
        if callable(getattr(overlay, "has_overlay", None)) and overlay.has_overlay("__command_palette__"):
            return
        self._draw_dashed_rect(surface, window, theme=theme)

    @staticmethod
    def _find_ancestor_window(node):
        current = node.parent
        while current is not None:
            if current.is_window():
                return current
            current = current.parent
        return None

    @staticmethod
    def _find_ancestor_scroll_view(node):
        current = node.parent
        while current is not None:
            if all(hasattr(current, name) for name in ("scroll_y", "set_scroll", "_viewport_w", "_viewport_h")):
                return current
            current = current.parent
        return None

    def _draw_dashed_rect(
        self,
        surface: "pygame.Surface",
        node,
        theme,
    ) -> None:
        """Draw a dashed rectangle around a node's rect.

        No explicit occlusion handling is performed here.  Hints are drawn
        during the scene's per-root draw pass, so any windows rendered
        afterward will naturally overdraw them via normal painter's-order.
        """
        if not node.visible:
            return

        rect = node.rect
        if rect.width < 2 or rect.height < 2:
            return

        scroll_view = self._find_ancestor_scroll_view(node)
        if scroll_view is not None and not scroll_view.rect.contains(rect):
            # When focus is on an oversized descendant inside a scroll view,
            # show the hint on the visible scroll view control bounds.
            rect = scroll_view.rect

        focus_rect = rect.inflate(2 * self.PADDING, 2 * self.PADDING)
        self._draw_dashed_rectangle(surface, focus_rect, theme.highlight)

    def _draw_dashed_rectangle(
        self,
        surface: "pygame.Surface",
        rect: "pygame.Rect",
        color,
    ) -> None:
        """Draw a dashed rectangle outline."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        if w <= 0 or h <= 0:
            return
        right = x + w - 1
        bottom = y + h - 1

        def draw_dashes(x1, y1, x2, y2):
            if x1 == x2:  # Vertical line
                start, end = min(y1, y2), max(y1, y2)
                pos = start
                while pos < end:
                    next_pos = min(pos + self.DASH_WIDTH, end)
                    pygame.draw.line(surface, color[:3], (x1, pos), (x1, next_pos), self.LINE_WIDTH)
                    pos = next_pos + self.GAP_WIDTH
            else:  # Horizontal line
                start, end = min(x1, x2), max(x1, x2)
                pos = start
                while pos < end:
                    next_pos = min(pos + self.DASH_WIDTH, end)
                    pygame.draw.line(surface, color[:3], (pos, y1), (next_pos, y1), self.LINE_WIDTH)
                    pos = next_pos + self.GAP_WIDTH

        # Draw four dashed lines (top, right, bottom, left)
        draw_dashes(x, y, right, y)  # Top
        draw_dashes(right, y, right, bottom)  # Right
        draw_dashes(right, bottom, x, bottom)  # Bottom
        draw_dashes(x, bottom, x, y)  # Left
