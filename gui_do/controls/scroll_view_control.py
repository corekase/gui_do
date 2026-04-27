"""ScrollViewControl — clipped viewport with scrollable child content."""
from __future__ import annotations

import dataclasses
from typing import List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ScrollViewControl(UiNode):
    """Clipped scrollable container for child controls.

    Children are positioned in **content-local coordinates** where ``(0, 0)`` is
    the top-left of the scrollable content area.  The visible window (viewport)
    is defined by the control's :attr:`rect`.

    Horizontal and/or vertical scrolling are each enabled independently.
    Thin scrollbar tracks are drawn inside the viewport whenever the content
    overflows in the corresponding axis.

    Usage::

        scroll = ScrollViewControl("sv", Rect(10, 10, 400, 300), scroll_y=True)
        scroll.add(LabelControl("lbl", Rect(0, 0, 380, 24), "Hello"))
        scroll.add(LabelControl("lbl2", Rect(0, 30, 380, 24), "World"))
        panel.add(scroll)
    """

    _SCROLLBAR_W: int = 12

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        content_width: int = 0,
        content_height: int = 0,
        scroll_x: bool = False,
        scroll_y: bool = True,
    ) -> None:
        super().__init__(control_id, rect)
        self._content_width = max(0, int(content_width))
        self._content_height = max(0, int(content_height))
        self._scroll_x_pos: int = 0
        self._scroll_y_pos: int = 0
        self._scroll_x_enabled: bool = bool(scroll_x)
        self._scroll_y_enabled: bool = bool(scroll_y)
        # Parallel lists: children (also in self.children) + their content-space rects
        self._child_content_rects: List[Rect] = []

    # ------------------------------------------------------------------
    # Child management
    # ------------------------------------------------------------------

    def add(self, child: UiNode, content_x: int = 0, content_y: int = 0) -> UiNode:
        """Add *child* at content-local position ``(content_x, content_y)``.

        The child's rect dimensions are preserved; only its position within the
        content area is set by ``content_x``/``content_y``.
        """
        content_rect = Rect(
            int(content_x),
            int(content_y),
            child.rect.width,
            child.rect.height,
        )
        child.parent = self
        self.children.append(child)
        self._child_content_rects.append(content_rect)
        # Expand content bounds to accommodate the child
        self._content_width = max(
            self._content_width, int(content_x) + child.rect.width
        )
        self._content_height = max(
            self._content_height, int(content_y) + child.rect.height
        )
        self._sync_child_screen_rects()
        return child

    def remove(self, child: UiNode) -> bool:
        """Remove *child* from the scroll view. Returns ``True`` if found."""
        for i, c in enumerate(self.children):
            if c is child:
                self.children.pop(i)
                self._child_content_rects.pop(i)
                child.parent = None
                self.invalidate()
                return True
        return False

    # ------------------------------------------------------------------
    # Scroll API
    # ------------------------------------------------------------------

    @property
    def scroll_x(self) -> int:
        """Current horizontal scroll offset in pixels."""
        return self._scroll_x_pos

    @property
    def scroll_y(self) -> int:
        """Current vertical scroll offset in pixels."""
        return self._scroll_y_pos

    def set_scroll(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Set the scroll position, clamping to valid bounds."""
        if x is not None:
            max_x = max(0, self._content_width - self._viewport_w())
            self._scroll_x_pos = max(0, min(int(x), max_x))
        if y is not None:
            max_y = max(0, self._content_height - self._viewport_h())
            self._scroll_y_pos = max(0, min(int(y), max_y))
        self._sync_child_screen_rects()
        self.invalidate()

    def scroll_by(self, dx: int = 0, dy: int = 0) -> None:
        """Scroll relative to the current position."""
        self.set_scroll(
            x=self._scroll_x_pos + int(dx) if dx else None,
            y=self._scroll_y_pos + int(dy) if dy else None,
        )

    def set_content_size(self, width: int, height: int) -> None:
        """Explicitly set the scrollable content area dimensions in pixels."""
        self._content_width = max(0, int(width))
        self._content_height = max(0, int(height))
        self._clamp_scroll()
        self._sync_child_screen_rects()
        self.invalidate()

    # ------------------------------------------------------------------
    # Geometry overrides — keep children in sync when this node moves
    # ------------------------------------------------------------------

    def set_pos(self, x: int, y: int) -> None:
        self.rect.x = int(x)
        self.rect.y = int(y)
        self._sync_child_screen_rects()
        self.invalidate()

    def resize(self, width: int, height: int) -> None:
        self.rect.width = int(width)
        self.rect.height = int(height)
        self._clamp_scroll()
        self._sync_child_screen_rects()
        self.invalidate()

    def set_rect(self, rect: Rect) -> None:
        self.rect = Rect(rect)
        self._clamp_scroll()
        self._sync_child_screen_rects()
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            child.update(dt_seconds)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_WHEEL:
            pos = event.pos
            if pos is not None and self.rect.collidepoint(pos):
                wheel_y = getattr(event, "wheel_y", 0) or getattr(event, "y", 0)
                self.scroll_by(dy=int(-wheel_y) * 24)
                return True

        # Forward to children — their rects are already in screen-space
        for child in reversed(self.children):
            if not child.visible:
                continue
            if child.handle_event(event, app):
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        vw = self._viewport_w()
        vh = self._viewport_h()
        viewport_rect = Rect(self.rect.x, self.rect.y, vw, vh)

        old_clip = surface.get_clip()
        new_clip = viewport_rect.clip(old_clip) if old_clip else viewport_rect
        surface.set_clip(new_clip)

        bg = getattr(theme, "background", (30, 30, 30))
        if hasattr(bg, "value"):
            bg = bg.value
        pygame.draw.rect(surface, bg, viewport_rect)

        for child in self.children:
            if not child.visible:
                continue
            if viewport_rect.colliderect(child.rect):
                child.draw(surface, theme)

        surface.set_clip(old_clip)

        # Scrollbar tracks are drawn outside the clipped area so they appear
        # on top of the viewport edge rather than being clipped themselves.
        self._draw_scrollbar_y(surface, theme)
        self._draw_scrollbar_x(surface, theme)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _viewport_w(self) -> int:
        w = self.rect.width
        if self._scroll_y_enabled and self._content_height > self.rect.height:
            w -= self._SCROLLBAR_W
        return max(1, w)

    def _viewport_h(self) -> int:
        h = self.rect.height
        if self._scroll_x_enabled and self._content_width > self.rect.width:
            h -= self._SCROLLBAR_W
        return max(1, h)

    def _clamp_scroll(self) -> None:
        max_x = max(0, self._content_width - self._viewport_w())
        max_y = max(0, self._content_height - self._viewport_h())
        self._scroll_x_pos = max(0, min(self._scroll_x_pos, max_x))
        self._scroll_y_pos = max(0, min(self._scroll_y_pos, max_y))

    def _sync_child_screen_rects(self) -> None:
        """Update all children's screen rects from content-space rects and scroll."""
        ox = self.rect.x - self._scroll_x_pos
        oy = self.rect.y - self._scroll_y_pos
        for child, content_rect in zip(self.children, self._child_content_rects):
            child.rect = Rect(
                ox + content_rect.x,
                oy + content_rect.y,
                content_rect.width,
                content_rect.height,
            )

    def _draw_scrollbar_y(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self._scroll_y_enabled:
            return
        content_h = self._content_height
        vh = self._viewport_h()
        if content_h <= vh:
            return
        w = self._SCROLLBAR_W
        track_rect = Rect(self.rect.right - w, self.rect.y, w, vh)
        track_color = getattr(theme, "panel", (40, 40, 40))
        if hasattr(track_color, "value"):
            track_color = track_color.value
        pygame.draw.rect(surface, track_color, track_rect)

        handle_h = max(16, int(vh * vh / max(1, content_h)))
        max_scroll = max(1, content_h - vh)
        handle_y = track_rect.y + int((vh - handle_h) * self._scroll_y_pos / max_scroll)
        handle_rect = Rect(track_rect.x + 2, handle_y, w - 4, handle_h)
        handle_color = getattr(theme, "scrollbar_handle", (100, 100, 100))
        if hasattr(handle_color, "value"):
            handle_color = handle_color.value
        pygame.draw.rect(surface, handle_color, handle_rect, border_radius=2)

    def _draw_scrollbar_x(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self._scroll_x_enabled:
            return
        content_w = self._content_width
        vw = self._viewport_w()
        if content_w <= vw:
            return
        h = self._SCROLLBAR_W
        track_rect = Rect(self.rect.x, self.rect.bottom - h, vw, h)
        track_color = getattr(theme, "panel", (40, 40, 40))
        if hasattr(track_color, "value"):
            track_color = track_color.value
        pygame.draw.rect(surface, track_color, track_rect)

        handle_w = max(16, int(vw * vw / max(1, content_w)))
        max_scroll = max(1, content_w - vw)
        handle_x = track_rect.x + int((vw - handle_w) * self._scroll_x_pos / max_scroll)
        handle_rect = Rect(handle_x, track_rect.y + 2, handle_w, h - 4)
        handle_color = getattr(theme, "scrollbar_handle", (100, 100, 100))
        if hasattr(handle_color, "value"):
            handle_color = handle_color.value
        pygame.draw.rect(surface, handle_color, handle_rect, border_radius=2)
