"""ToolbarControl — horizontal strip of labeled tool buttons with separators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size (typically 16 px).
# All geometry is derived from these at draw/event time so the control
# scales correctly with any custom font configuration.
_FONT_SCALE: float = 1.0          # label text size ratio
_PAD_X_RATIO: float = 0.5         # horizontal padding inside each button
_PAD_Y_RATIO: float = 0.375       # vertical padding inside each button
_SEP_MARGIN_RATIO: float = 0.25   # space on each side of a separator line
_BTN_GAP: int = 2                  # fixed gap between buttons (px, not scaled)


@dataclass
class ToolbarItem:
    """A single button entry in a ToolbarControl.

    Set ``separator=True`` for a visual divider; all other fields are ignored.
    """
    label: str = ""
    action_id: str = ""
    on_click: Optional[Callable[[], None]] = None
    tooltip: str = ""
    separator: bool = False
    enabled: bool = True


class ToolbarControl(UiNode):
    """Horizontal toolbar strip with labeled tool buttons and separators.

    Unlike :class:`MenuBarControl`, a toolbar presents direct-action buttons
    rather than pull-down menus.  Items can be enabled or disabled at runtime
    via :meth:`set_item_enabled`.

    Usage::

        bar = ToolbarControl(
            "toolbar", Rect(0, 0, 800, 32),
            items=[
                ToolbarItem("New", on_click=new_file),
                ToolbarItem("Open", on_click=open_file),
                ToolbarItem(separator=True),
                ToolbarItem("Run", on_click=run_action),
            ],
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: Optional[List[ToolbarItem]] = None,
        font_role: str = "body",
        background: bool = True,
    ) -> None:
        super().__init__(control_id, rect)
        self._items: List[ToolbarItem] = list(items or [])
        self._font_role = font_role
        self._background = background
        # Per-item hit rects (populated on draw or layout; separators have empty rects).
        self._hit_rects: List[Optional[Rect]] = []
        self._hovered_index: int = -1
        self._pressed_index: int = -1
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def items(self) -> List[ToolbarItem]:
        return self._items

    def set_items(self, items: List[ToolbarItem]) -> None:
        """Replace the toolbar item list and invalidate."""
        self._items = list(items)
        self._hit_rects = []
        self._hovered_index = -1
        self._pressed_index = -1
        self.invalidate()

    def set_item_enabled(self, action_id: str, enabled: bool) -> bool:
        """Enable or disable a button by ``action_id``.  Returns True if found."""
        for item in self._items:
            if item.action_id == action_id:
                item.enabled = bool(enabled)
                self.invalidate()
                return True
        return False

    def append_item(self, item: ToolbarItem) -> None:
        self._items.append(item)
        self._hit_rects = []
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled and any(not i.separator for i in self._items)

    def accepts_mouse_focus(self) -> bool:
        return False

    def reconcile_hover(self, wants_hover: bool) -> None:
        if not wants_hover and self._hovered_index != -1:
            self._hovered_index = -1
            self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._hovered_index = -1
        self._pressed_index = -1
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._hovered_index = -1
        self._pressed_index = -1
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._hovered_index = -1
            self._pressed_index = -1
            return False

        pos = event.pos
        if pos is None:
            return False

        if event.is_mouse_motion():
            prev = self._hovered_index
            self._hovered_index = self._index_at(pos)
            if prev != self._hovered_index:
                self.invalidate()
            return self._hovered_index >= 0

        if event.is_mouse_down(1):
            idx = self._index_at(pos)
            if idx >= 0:
                self._pressed_index = idx
                self.invalidate()
                return True
            return False

        if event.is_mouse_up(1):
            prev_pressed = self._pressed_index
            self._pressed_index = -1
            if prev_pressed >= 0:
                self.invalidate()
                idx = self._index_at(pos)
                if idx == prev_pressed:
                    item = self._items[prev_pressed]
                    if item.enabled and item.on_click is not None:
                        item.on_click()
                return True
            return False

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        pad_x = max(4, fonts.scaled_size(_PAD_X_RATIO))
        sep_margin = max(2, fonts.scaled_size(_SEP_MARGIN_RATIO))

        if self._background:
            bg = theme.medium if self.enabled else theme.dark
            pygame.draw.rect(surface, bg, r)
        # Bottom border
        pygame.draw.line(surface, theme.dark, (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1))

        self._hit_rects = []
        x = r.left + 4

        for idx, item in enumerate(self._items):
            if item.separator:
                sep_x = x + sep_margin
                line_color = theme.dark if self.enabled else theme.medium
                pygame.draw.line(surface, line_color, (sep_x, r.top + 3), (sep_x, r.bottom - 4))
                self._hit_rects.append(None)
                x = sep_x + sep_margin + 1
                continue

            item_enabled = self.enabled and item.enabled
            is_hovered = idx == self._hovered_index and item_enabled
            is_pressed = idx == self._pressed_index and item_enabled

            label_surf = theme.render_text(
                item.label, role=self._font_role, shadow=False, size=font_size
            )
            label_w, label_h = label_surf.get_size()
            btn_w = label_w + pad_x * 2
            btn_rect = Rect(x, r.top, btn_w, r.height)
            self._hit_rects.append(Rect(btn_rect))

            if is_pressed:
                pygame.draw.rect(surface, theme.dark, btn_rect)
            elif is_hovered:
                pygame.draw.rect(surface, theme.light, btn_rect)

            if not item_enabled:
                text_color = theme.dark
            elif is_pressed:
                text_color = theme.background
            else:
                text_color = theme.text

            label_surf = theme.render_text(
                item.label, role=self._font_role, shadow=False,
                size=font_size, color=text_color,
            )
            text_y = r.top + (r.height - label_surf.get_height()) // 2
            surface.blit(label_surf, (x + pad_x, text_y))
            x += btn_w + _BTN_GAP

        # Focus ring around the entire bar when keyboard-focused
        if self._focused:
            pygame.draw.rect(surface, theme.highlight, r, 2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _index_at(self, pos: tuple) -> int:
        if not self.rect.collidepoint(pos):
            return -1
        for idx, hit in enumerate(self._hit_rects):
            if hit is not None and hit.collidepoint(pos):
                item = self._items[idx]
                if not item.separator:
                    return idx
        return -1
