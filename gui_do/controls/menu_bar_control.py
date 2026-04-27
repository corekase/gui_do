"""MenuBarControl — horizontal application menu bar with flyout sub-menus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..core.context_menu_manager import ContextMenuItem
from ..controls.overlay_panel_control import OverlayPanelControl

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_ENTRY_PADDING_X = 12
_ENTRY_PADDING_Y = 4
_BAR_HEIGHT = 28
_FONT_SIZE = 17


@dataclass
class MenuEntry:
    """One top-level menu in the menu bar (e.g., File, Edit, View)."""

    label: str
    items: List[ContextMenuItem] = field(default_factory=list)
    enabled: bool = True


class _FlyoutPanel(OverlayPanelControl):
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
        super().__init__(control_id, rect, draw_background=False)
        self._items = list(items)
        self._on_close = on_close
        self._hovered = -1
        self._keyboard_idx = -1

    @classmethod
    def measure(cls, items: List[ContextMenuItem]) -> Tuple[int, int]:
        h = cls._PAD * 2
        for it in items:
            h += cls._SEP_H if it.separator else cls._ITEM_H
        try:
            font = pygame.font.SysFont(None, _FONT_SIZE)
            ws = [font.size(it.label)[0] + cls._TEXT_PAD * 2 + 8 for it in items if not it.separator]
            w = max(cls._MIN_W, max(ws, default=cls._MIN_W))
        except Exception:
            w = cls._MIN_W
        return w, h

    def _item_rects(self) -> List[Rect]:
        rects: List[Rect] = []
        y = self.rect.y + self._PAD
        for it in self._items:
            h = self._SEP_H if it.separator else self._ITEM_H
            rects.append(Rect(self.rect.x, y, self.rect.width, h))
            y += h
        return rects

    def _selectable(self) -> List[int]:
        return [i for i, it in enumerate(self._items) if not it.separator and it.enabled]

    def _activate(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            it = self._items[idx]
            if not it.separator and it.enabled and it.action is not None:
                try:
                    self._on_close()
                    it.action()
                except Exception:
                    pass
                return
        self._on_close()

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        rects = self._item_rects()

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered = -1
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos) and not self._items[i].separator:
                    self._hovered = i
                    self._keyboard_idx = i
                    break
            self.invalidate()
            return self.rect.collidepoint(event.pos)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos) and not self._items[i].separator:
                    if self._items[i].enabled:
                        self._activate(i)
                    return True
            return False

        if event.kind == EventType.KEY_DOWN:
            sel = self._selectable()
            if not sel:
                return False
            if event.key == pygame.K_DOWN:
                nxt = [i for i in sel if i > self._keyboard_idx]
                self._keyboard_idx = nxt[0] if nxt else sel[0]
                self._hovered = self._keyboard_idx
                self.invalidate()
                return True
            if event.key == pygame.K_UP:
                prev = [i for i in sel if i < self._keyboard_idx]
                self._keyboard_idx = prev[-1] if prev else sel[-1]
                self._hovered = self._keyboard_idx
                self.invalidate()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._activate(self._keyboard_idx)
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        def _c(name: str, fallback: Tuple) -> Tuple:
            v = getattr(theme, name, fallback)
            return v.value if hasattr(v, "value") else v

        bg = _c("panel", (45, 45, 55))
        text_col = _c("text", (220, 220, 220))
        disabled_col = tuple(max(0, min(255, c // 2)) for c in text_col)
        hover_col = _c("highlight", (0, 100, 200))
        border_col = _c("border", (80, 80, 90))

        font = pygame.font.SysFont(None, _FONT_SIZE)

        # Shadow
        sh = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 70))
        surface.blit(sh, (self.rect.x + 3, self.rect.y + 3))

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        rects = self._item_rects()
        for i, (it, r) in enumerate(zip(self._items, rects)):
            if it.separator:
                sy = r.y + r.height // 2
                pygame.draw.line(surface, border_col, (r.x + 4, sy), (r.x + r.width - 4, sy))
                continue
            if i == self._hovered:
                pygame.draw.rect(surface, hover_col, r)
            col = disabled_col if not it.enabled else text_col
            txt = font.render(it.label, True, col)
            surface.blit(txt, (r.x + self._TEXT_PAD, r.y + (r.height - txt.get_height()) // 2))


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
            font = pygame.font.SysFont(None, _FONT_SIZE)
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

        def _c(name: str, fallback: tuple) -> tuple:
            v = getattr(theme, name, fallback)
            return v.value if hasattr(v, "value") else v

        bar_bg = _c("panel", (40, 40, 50))
        text_col = _c("text", (220, 220, 220))
        disabled_col = tuple(max(0, min(255, c // 2)) for c in text_col)
        hover_col = _c("highlight", (0, 100, 200))
        open_col = _c("accent", (0, 80, 160))
        border_col = _c("border", (60, 60, 70))

        try:
            font = pygame.font.SysFont(None, _FONT_SIZE)
        except Exception:
            font = None

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
