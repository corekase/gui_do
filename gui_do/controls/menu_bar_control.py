"""MenuBarControl — horizontal application menu bar with flyout sub-menus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.context_menu_manager import ContextMenuItem
from ..core.menu_overlay_panel_base import _MenuOverlayPanelBase

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_ENTRY_PADDING_X = 12
_FONT_SIZE = 17


@dataclass
class MenuEntry:
    """One top-level menu in the menu bar (e.g., File, Edit, View)."""

    label: str
    items: List[ContextMenuItem] = field(default_factory=list)
    enabled: bool = True


class _FlyoutPanel(_MenuOverlayPanelBase):
    """Internal overlay panel rendering one flyout sub-menu."""

    _ITEM_H = 26
    _SEP_H = 8
    _PAD = 4
    _TEXT_PAD = 12
    _MIN_W = 140

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: List[ContextMenuItem],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            control_id,
            rect,
            items,
            on_close,
            item_height=self._ITEM_H,
            separator_height=self._SEP_H,
            padding=self._PAD,
            text_padding=self._TEXT_PAD,
            min_width=self._MIN_W,
            font_size=_FONT_SIZE,
        )

    @classmethod
    def measure(cls, items: List[ContextMenuItem]) -> Tuple[int, int]:
        return _MenuOverlayPanelBase.measure(
            items,
            item_height=cls._ITEM_H,
            separator_height=cls._SEP_H,
            padding=cls._PAD,
            text_padding=cls._TEXT_PAD,
            min_width=cls._MIN_W,
            font_size=_FONT_SIZE,
        )


class MenuBarControl(UiNode):
    """Horizontal application menu bar control.

    Add :class:`MenuEntry` items via :meth:`set_entries`.  When the user clicks
    a top-level entry a flyout sub-menu is shown via the application's
    :attr:`~gui_do.GuiApplication.overlay` manager.

    Usage::

        bar = MenuBarControl("menubar", Rect(0, 0, 800, 28))
        bar.set_entries([
            MenuEntry("File", [
                ContextMenuItem("New", action=on_new),
                ContextMenuItem("Open", action=on_open),
                ContextMenuItem("", separator=True),
                ContextMenuItem("Quit", action=on_quit),
            ]),
            MenuEntry("Edit", [
                ContextMenuItem("Undo", action=on_undo),
                ContextMenuItem("Redo", action=on_redo),
            ]),
        ])
        app.add(bar)
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        entries: Optional[List[MenuEntry]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._entries: List[MenuEntry] = list(entries) if entries else []
        self._open_index: int = -1  # index of currently open top-level entry
        self._hovered_index: int = -1
        self.tab_index = 0
        self._draw_font: object = None  # cached from pygame.font.SysFont(None, _FONT_SIZE)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def set_entries(self, entries: List[MenuEntry]) -> None:
        """Replace all top-level menu entries."""
        self._entries = list(entries)
        self._open_index = -1
        self._hovered_index = -1
        self.invalidate()

    @property
    def entries(self) -> List[MenuEntry]:
        return list(self._entries)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _entry_rects(self) -> List[Rect]:
        rects: List[Rect] = []
        x = self.rect.x
        y = self.rect.y
        h = self.rect.height
        try:
            if self._draw_font is None:
                self._draw_font = pygame.font.SysFont(None, _FONT_SIZE)
            font = self._draw_font
        except Exception:
            font = None
        for entry in self._entries:
            if font:
                tw = font.size(entry.label)[0]
            else:
                tw = len(entry.label) * 8
            w = tw + _ENTRY_PADDING_X * 2
            rects.append(Rect(x, y, w, h))
            x += w
        return rects

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        er = self._entry_rects()

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered_index = -1
            for i, r in enumerate(er):
                if r.collidepoint(event.pos):
                    self._hovered_index = i
                    break
            # If a menu is already open and mouse hovers a different entry, switch
            if self._open_index >= 0 and self._hovered_index >= 0 and self._hovered_index != self._open_index:
                self._dismiss_flyout(app)
                self._open_flyout(self._hovered_index, app, er)
            self.invalidate()
            return self.rect.collidepoint(event.pos)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            for i, r in enumerate(er):
                if r.collidepoint(pos) and self._entries[i].enabled:
                    if self._open_index == i:
                        self._dismiss_flyout(app)
                    else:
                        self._dismiss_flyout(app)
                        self._open_flyout(i, app, er)
                    return True
            # Click outside while open: dismiss
            if self._open_index >= 0:
                self._dismiss_flyout(app)
            return self.rect.collidepoint(pos)

        return False

    def _dismiss_flyout(self, app: "GuiApplication") -> None:
        if self._open_index >= 0:
            owner = f"_menubar_{self.control_id}_{self._open_index}"
            app.overlay.hide(owner)
            self._open_index = -1
            self.invalidate()

    def _open_flyout(self, index: int, app: "GuiApplication", er: List[Rect]) -> None:
        if index < 0 or index >= len(self._entries):
            return
        entry = self._entries[index]
        if not entry.items:
            return
        owner = f"_menubar_{self.control_id}_{index}"
        er_rect = er[index]
        w, h = _FlyoutPanel.measure(entry.items)
        screen = app.surface.get_rect()
        fx = er_rect.x
        fy = er_rect.bottom
        # Ensure flyout stays on screen horizontally
        if fx + w > screen.right:
            fx = screen.right - w
        # Ensure flyout stays on screen vertically
        if fy + h > screen.bottom:
            fy = er_rect.y - h

        panel = _FlyoutPanel(
            owner,
            Rect(fx, fy, w, h),
            entry.items,
            on_close=lambda: self._dismiss_flyout(app),
        )
        app.overlay.show(
            owner,
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            on_dismiss=lambda: self._on_flyout_dismissed(index),
        )
        self._open_index = index
        self.invalidate()

    def _on_flyout_dismissed(self, index: int) -> None:
        if self._open_index == index:
            self._open_index = -1
            self.invalidate()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bar_bg = getattr(theme, "panel", (40, 40, 50))
        text_col = theme.text
        disabled_col = (text_col[0] >> 1, text_col[1] >> 1, text_col[2] >> 1)
        hover_col = theme.highlight
        open_col = getattr(theme, "accent", (0, 80, 160))
        border_col = getattr(theme, "border", (60, 60, 70))

        if self._draw_font is None:
            try:
                self._draw_font = pygame.font.SysFont(None, _FONT_SIZE)
            except Exception:
                pass
        font = self._draw_font

        pygame.draw.rect(surface, bar_bg, self.rect)
        # Bottom border line
        pygame.draw.line(
            surface, border_col,
            (self.rect.left, self.rect.bottom - 1),
            (self.rect.right, self.rect.bottom - 1),
        )

        er = self._entry_rects()
        for i, (entry, r) in enumerate(zip(self._entries, er)):
            if i == self._open_index:
                pygame.draw.rect(surface, open_col, r)
            elif i == self._hovered_index and entry.enabled:
                pygame.draw.rect(surface, hover_col, r)
            col = disabled_col if not entry.enabled else text_col
            if font:
                txt = font.render(entry.label, True, col)
                surface.blit(txt, (r.x + _ENTRY_PADDING_X, r.y + (r.height - txt.get_height()) // 2))
