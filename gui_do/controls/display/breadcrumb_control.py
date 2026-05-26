"""BreadcrumbControl — clickable path navigation trail."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size.
_FONT_SCALE: float = 1.0           # breadcrumb label text size ratio
_PAD_X_RATIO: float = 0.375       # horizontal padding before first item


@dataclass
class BreadcrumbItem:
    """A single segment in a :class:`BreadcrumbControl`."""
    label: str
    value: object = None
    on_click: Optional[Callable[["BreadcrumbItem"], None]] = None


class BreadcrumbControl(UiNode):
    """Horizontal breadcrumb path control.

    Each segment is a clickable label separated by ``>`` arrows.
    The last item is rendered without a click affordance (current location).

    Usage::

        crumb = BreadcrumbControl(
            "breadcrumb", Rect(0, 0, 400, 24),
            items=[
                BreadcrumbItem("Home", on_click=go_home),
                BreadcrumbItem("Projects", on_click=go_projects),
                BreadcrumbItem("gui_do"),   # current — not clickable
            ],
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: Optional[List[BreadcrumbItem]] = None,
        font_role: str = "body",
        on_navigate: Optional[Callable[[BreadcrumbItem, int], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._items: List[BreadcrumbItem] = list(items or [])
        self._font_role = font_role
        self._on_navigate = on_navigate
        self._hit_rects: List[Optional[Rect]] = []
        self._hovered_index: int = -1
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def items(self) -> List[BreadcrumbItem]:
        return self._items

    def set_items(self, items: List[BreadcrumbItem]) -> None:
        self._items = list(items)
        self._hit_rects = []
        self._hovered_index = -1
        self.invalidate()

    def push(self, item: BreadcrumbItem) -> None:
        self._items.append(item)
        self._hit_rects = []
        self.invalidate()

    def pop(self) -> Optional[BreadcrumbItem]:
        if not self._items:
            return None
        item = self._items.pop()
        self._hit_rects = []
        self._hovered_index = -1
        self.invalidate()
        return item

    def navigate_to(self, index: int) -> None:
        """Trim path to ``index`` (inclusive) and fire navigate callback."""
        if 0 <= index < len(self._items):
            item = self._items[index]
            self._items = self._items[: index + 1]
            self._hit_rects = []
            self._hovered_index = -1
            self.invalidate()
            if item.on_click:
                item.on_click(item)
            if self._on_navigate:
                self._on_navigate(item, index)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled and len(self._items) > 1

    def accepts_mouse_focus(self) -> bool:
        return False

    def reconcile_hover(self, wants_hover: bool) -> None:
        if not wants_hover and self._hovered_index != -1:
            self._hovered_index = -1
            self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._hovered_index = -1
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._hovered_index = -1
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._hovered_index = -1
            return False

        pos = event.pos
        if pos is None:
            return False

        if event.is_mouse_motion():
            prev = self._hovered_index
            self._hovered_index = self._index_at(pos)
            if prev != self._hovered_index:
                self.invalidate()
            return False

        if event.is_mouse_down(1):
            idx = self._index_at(pos)
            if idx >= 0:
                self.navigate_to(idx)
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        pad_x = max(3, fonts.scaled_size(_PAD_X_RATIO))

        self._hit_rects = []
        x = r.left + pad_x
        last_idx = len(self._items) - 1

        for idx, item in enumerate(self._items):
            is_last = idx == last_idx
            is_hovered = idx == self._hovered_index and not is_last

            if not self.enabled:
                color = theme.dark
            elif is_last:
                color = theme.medium
            elif is_hovered:
                color = theme.highlight
            else:
                color = theme.text

            label_surf = theme.render_text(
                item.label, role=self._font_role,
                size=font_size, color=color,
            )
            lw, lh = label_surf.get_size()

            item_rect = Rect(x, r.top, lw, r.height)
            self._hit_rects.append(None if is_last else Rect(item_rect))

            ty = r.top + (r.height - lh) // 2
            surface.blit(label_surf, (x, ty))
            x += lw

            if not is_last:
                sep_color = theme.dark if not self.enabled else theme.medium
                sep_surf = theme.render_text(
                    " › ", role=self._font_role,
                    size=font_size, color=sep_color,
                )
                surface.blit(sep_surf, (x, ty))
                x += sep_surf.get_width()

        # Focus ring
        if self._focused:
            pygame.draw.rect(surface, theme.highlight, r, 2)

    def _index_at(self, pos: tuple) -> int:
        if not self.rect.collidepoint(pos):
            return -1
        last_idx = len(self._items) - 1
        for idx, hit in enumerate(self._hit_rects):
            if hit is not None and hit.collidepoint(pos) and idx != last_idx:
                return idx
        return -1
