"""TabControl — tabbed container with a tab bar and swappable content panel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

_TAB_H = 32       # height of the tab bar strip
_TAB_PAD_H = 12   # horizontal padding per tab label
_TAB_PAD_V = 4    # vertical padding per tab label


@dataclass
class TabItem:
    """Descriptor for a single tab within a :class:`TabControl`.

    ``key``   — unique identifier for this tab (used with :meth:`TabControl.select`).
    ``label`` — display text shown in the tab strip.
    ``content`` — optional :class:`UiNode` to display in the content area when active.
    ``enabled`` — when ``False`` the tab strip button is greyed out and not clickable.
    """

    key: str
    label: str
    content: Optional[UiNode] = None
    enabled: bool = True


class TabControl(UiNode):
    """Tabbed container control.

    Renders a horizontal strip of tab buttons at the top and a content panel
    below.  Selecting a tab fires ``on_change(key)`` and swaps the visible
    content node.

    Usage::

        panel_a = PanelControl("panel_a", Rect(0, 0, 400, 300))
        panel_b = PanelControl("panel_b", Rect(0, 0, 400, 300))
        tabs = TabControl(
            "tabs", Rect(10, 10, 400, 340),
            items=[
                TabItem("a", "Alpha", panel_a),
                TabItem("b", "Beta",  panel_b),
            ],
            on_change=lambda key: print("selected", key),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: Optional[List[TabItem]] = None,
        selected_key: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
        font_size: int = 16,
    ) -> None:
        super().__init__(control_id, rect)
        self._items: List[TabItem] = list(items or [])
        self._on_change = on_change
        self._font_role = str(font_role)
        self._font_size = max(6, int(font_size))
        self.tab_index = 0  # the whole control is keyboard-navigable

        # Determine initial selection
        self._selected_key: Optional[str] = None
        if self._items:
            self._selected_key = self._items[0].key
        if selected_key is not None:
            for item in self._items:
                if item.key == selected_key:
                    self._selected_key = selected_key
                    break

        # Track tab button rects for hit testing
        self._tab_rects: List[Rect] = []

        # Mount tracking
        self._app: "Optional[GuiApplication]" = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def selected_key(self) -> Optional[str]:
        """The key of the currently selected tab, or *None* if empty."""
        return self._selected_key

    def select(self, key: str) -> bool:
        """Programmatically select a tab by key.

        Returns ``True`` if the key was found and the selection changed.
        """
        for item in self._items:
            if item.key == key and item.enabled:
                if self._selected_key != key:
                    self._selected_key = key
                    self.invalidate()
                    if self._on_change is not None:
                        self._on_change(key)
                return True
        return False

    def add_item(self, item: TabItem) -> None:
        """Append a :class:`TabItem` at the end of the tab strip."""
        self._items.append(item)
        if self._selected_key is None and item.enabled:
            self._selected_key = item.key
        self.invalidate()

    def remove_item(self, key: str) -> bool:
        """Remove the tab with the given key.  Returns ``True`` if found."""
        for i, item in enumerate(self._items):
            if item.key == key:
                self._items.pop(i)
                if self._selected_key == key:
                    # Advance to next enabled tab
                    self._selected_key = None
                    for candidate in self._items:
                        if candidate.enabled:
                            self._selected_key = candidate.key
                            break
                    if self._on_change is not None and self._selected_key is not None:
                        self._on_change(self._selected_key)
                self.invalidate()
                return True
        return False

    def items(self) -> List[TabItem]:
        """Return a copy of the tab item list."""
        return list(self._items)

    def accepts_focus(self) -> bool:
        return self.tab_index >= 0

    def accepts_mouse_focus(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self, parent: "Optional[UiNode]") -> None:  # type: ignore[override]
        super().on_mount(parent)

    def on_unmount(self, parent: "Optional[UiNode]") -> None:  # type: ignore[override]
        super().on_unmount(parent)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _content_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top + _TAB_H, self.rect.width, self.rect.height - _TAB_H)

    def _build_tab_rects(self, theme: "ColorTheme") -> List[Rect]:
        rects: List[Rect] = []
        x = self.rect.left
        y = self.rect.top
        for item in self._items:
            try:
                w, _ = theme.fonts.resolve(self._font_role, self._font_size).text_size(item.label)
            except Exception:
                w = len(item.label) * (self._font_size // 2)
            tab_w = w + _TAB_PAD_H * 2
            rects.append(Rect(x, y, tab_w, _TAB_H))
            x += tab_w
        return rects

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            tab_strip_rect = Rect(self.rect.left, self.rect.top, self.rect.width, _TAB_H)
            if tab_strip_rect.collidepoint(pos):
                for i, tab_rect in enumerate(self._tab_rects):
                    if tab_rect.collidepoint(pos) and i < len(self._items):
                        item = self._items[i]
                        if item.enabled and self._selected_key != item.key:
                            self._selected_key = item.key
                            self.invalidate()
                            if self._on_change is not None:
                                self._on_change(item.key)
                        return True
                return True  # consumed even if no tab hit (inside bar area)

        # Keyboard navigation within focused control
        if event.kind == EventType.KEY_DOWN and self._focused:
            key = event.key
            if key in (pygame.K_LEFT, pygame.K_RIGHT):
                enabled_keys = [it.key for it in self._items if it.enabled]
                if not enabled_keys:
                    return True
                try:
                    idx = enabled_keys.index(self._selected_key or "")
                except ValueError:
                    idx = 0
                if key == pygame.K_LEFT:
                    idx = max(0, idx - 1)
                else:
                    idx = min(len(enabled_keys) - 1, idx + 1)
                new_key = enabled_keys[idx]
                if new_key != self._selected_key:
                    self._selected_key = new_key
                    self.invalidate()
                    if self._on_change is not None:
                        self._on_change(new_key)
                return True

        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        r = self.rect
        tab_rects = self._build_tab_rects(theme)
        self._tab_rects = tab_rects  # cache for hit testing

        # Draw tab strip background
        strip_rect = Rect(r.left, r.top, r.width, _TAB_H)
        bg_color = theme.dark
        pygame.draw.rect(surface, bg_color, strip_rect)

        # Draw tab buttons
        for i, item in enumerate(self._items):
            tab_rect = tab_rects[i] if i < len(tab_rects) else None
            if tab_rect is None:
                continue
            is_selected = item.key == self._selected_key
            is_enabled = item.enabled
            if is_selected:
                tab_bg = theme.background
                pygame.draw.rect(surface, tab_bg, tab_rect)
            tab_color = theme.text if is_enabled else theme.medium
            label_surf = theme.render_text(
                item.label, role=self._font_role, size=self._font_size, color=tab_color
            )
            lw, lh = label_surf.get_size()
            lx = tab_rect.left + (tab_rect.width - lw) // 2
            ly = tab_rect.top + (tab_rect.height - lh) // 2
            surface.blit(label_surf, (lx, ly))
            # Bottom border
            if is_selected:
                pygame.draw.line(surface, theme.background, (tab_rect.left, tab_rect.bottom - 1), (tab_rect.right - 1, tab_rect.bottom - 1), 2)
            else:
                pygame.draw.line(surface, theme.medium, (tab_rect.left, tab_rect.bottom - 1), (tab_rect.right - 1, tab_rect.bottom - 1), 1)

        # Draw content area
        content_rect = self._content_rect()
        pygame.draw.rect(surface, theme.background, content_rect)

        # Draw active content node
        selected_content: Optional[UiNode] = None
        for item in self._items:
            if item.key == self._selected_key and item.content is not None:
                selected_content = item.content
                break
        if selected_content is not None and selected_content.visible:
            # Position content node within content area
            selected_content.rect.topleft = (content_rect.left, content_rect.top)
            selected_content.draw(surface, theme)

        # Outer border
        pygame.draw.rect(surface, theme.medium, r, 1)

    def update(self, dt_seconds: float) -> None:
        """Forward updates to the active content node."""
        for item in self._items:
            if item.key == self._selected_key and item.content is not None:
                item.content.update(dt_seconds)
