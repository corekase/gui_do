"""MenuBarControl — horizontal application menu bar with flyout sub-menus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base.ui_node import UiNode
from ...overlays.context_menu_manager import ContextMenuItem
from ...overlays.menu_overlay_panel_base import _MenuOverlayPanelBase

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_ENTRY_PADDING_X = 12


@dataclass
class MenuEntry:
    """One top-level menu in the menu bar (e.g., File, Edit, View)."""

    label: str
    items: List[ContextMenuItem] = field(default_factory=list)
    enabled: bool = True
    flyout_min_width: Optional[int] = None


class _FlyoutPanel(_MenuOverlayPanelBase):
    """Internal overlay panel rendering one flyout sub-menu."""

    _ITEM_H = 26
    _SEP_H = 8
    _PAD = 4
    _TEXT_PAD = 12
    _MIN_W = 140
    _FONT_SIZE = 17  # legacy concrete size; no theme at construction time

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
            font_size=self._FONT_SIZE,
        )

    @classmethod
    def measure(
        cls,
        items: List[ContextMenuItem],
        *,
        min_width: Optional[int] = None,
    ) -> Tuple[int, int]:
        resolved_min_width = cls._MIN_W if min_width is None else max(cls._MIN_W, int(min_width))
        return _MenuOverlayPanelBase.measure(
            items,
            item_height=cls._ITEM_H,
            separator_height=cls._SEP_H,
            padding=cls._PAD,
            text_padding=cls._TEXT_PAD,
            min_width=resolved_min_width,
            font_size=cls._FONT_SIZE,
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
        self._open_flyout_rect: Optional[Rect] = None
        self._last_app: Optional["GuiApplication"] = None
        self.tab_index = 0
        self._draw_font_role: str = "menu_bar.entry"
        self._entry_rects_cache_key: Optional[tuple] = None
        self._entry_rects_cache: List[Rect] = []

    _FONT_SCALE: float = 1.0625   # 17/16 — slightly larger than body for menu legibility

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def set_entries(self, entries: List[MenuEntry]) -> None:
        """Replace all top-level menu entries."""
        self._entries = list(entries)
        self._open_index = -1
        self._hovered_index = -1
        self._entry_rects_cache_key = None
        self._entry_rects_cache = []
        self.invalidate()

    def accepts_focus(self) -> bool:
        return True

    def on_focus_changed(self, is_focused: bool) -> None:
        if is_focused:
            return
        if self._open_index < 0:
            return
        if self._last_app is None:
            return
        self._dismiss_flyout(self._last_app)

    @property
    def entries(self) -> List[MenuEntry]:
        return list(self._entries)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _entry_rects(self, theme) -> List[Rect]:
        if theme is None or not hasattr(theme, "fonts") or theme.fonts is None:
            raise RuntimeError("MenuBarControl requires a non-None theme with a valid 'fonts' attribute. Ensure theme is passed everywhere this control is used.")
        scaled_size = theme.fonts.scaled_size(self._FONT_SCALE)
        labels = tuple(entry.label for entry in self._entries)
        font_revision = getattr(theme.fonts, "revision", 0)
        cache_key = (
            self.rect.x,
            self.rect.y,
            self.rect.height,
            labels,
            font_revision,
            scaled_size,
        )
        if self._entry_rects_cache_key == cache_key:
            return self._entry_rects_cache

        rects: List[Rect] = []
        x = self.rect.x
        y = self.rect.y
        h = self.rect.height
        font = theme.fonts.font_instance(self._draw_font_role, size=scaled_size)
        for entry in self._entries:
            if font:
                if hasattr(font, "text_size"):
                    tw = font.text_size(entry.label)[0]
                else:
                    tw = font.size(entry.label)[0]
            else:
                tw = len(entry.label) * 8
            w = tw + _ENTRY_PADDING_X * 2
            rects.append(Rect(x, y, w, h))
            x += w
        self._entry_rects_cache_key = cache_key
        self._entry_rects_cache = rects
        return rects

    def _hover_index_from_pointer(self, pointer_pos, er: List[Rect]) -> int:
        if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return -1
        for i, r in enumerate(er):
            if r.collidepoint(pointer_pos):
                return i
        return -1

    def _sync_open_menu_with_highlight(self, app: "GuiApplication", er: List[Rect]) -> None:
        if self._open_index < 0 or self._hovered_index < 0:
            return
        if self._hovered_index == self._open_index:
            return
        if self._hovered_index >= len(self._entries):
            return
        if not self._entries[self._hovered_index].enabled:
            return
        self._dismiss_flyout(app)
        self._open_flyout(self._hovered_index, app, er)

    def _navigable_entry_indices(self) -> List[int]:
        return [
            i
            for i, entry in enumerate(self._entries)
            if entry.enabled and bool(entry.items)
        ]

    @staticmethod
    def _cycle_entry_index(indices: List[int], current: int, step: int) -> int:
        if not indices:
            return -1
        if current not in indices:
            return indices[0]
        current_pos = indices.index(current)
        return indices[(current_pos + step) % len(indices)]

    def _open_for_keyboard(self, app: "GuiApplication", er: List[Rect], *, index: int | None = None) -> bool:
        indices = self._navigable_entry_indices()
        if not indices:
            return False
        target = indices[0] if index is None else int(index)
        if target not in indices:
            target = indices[0]
        self._dismiss_flyout(app)
        self._open_flyout(target, app, er)
        self._hovered_index = target
        self.invalidate()
        return True

    def _cycle_top_level_menu(self, app: "GuiApplication", er: List[Rect], *, step: int) -> bool:
        indices = self._navigable_entry_indices()
        if not indices:
            return False
        current = self._open_index if self._open_index >= 0 else self._hovered_index
        target = self._cycle_entry_index(indices, current, step)
        if target < 0:
            return False
        return self._open_for_keyboard(app, er, index=target)

    def _pointer_in_open_menu_elements(self, pointer_pos) -> bool:
        if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return False
        if self.rect.collidepoint(pointer_pos):
            return True
        if self._open_flyout_rect is not None and self._open_flyout_rect.collidepoint(pointer_pos):
            return True
        return False

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            return False
        if theme is None or not hasattr(theme, "fonts") or theme.fonts is None:
            raise RuntimeError("MenuBarControl.handle_event requires a non-None theme with a valid 'fonts' attribute. Ensure theme is passed everywhere this control is used.")
        self._last_app = app
        er = self._entry_rects(theme)

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered_index = -1
            for i, r in enumerate(er):
                if r.collidepoint(event.pos):
                    self._hovered_index = i
                    break
            # Entering/hovering strip should open the submenu under pointer.
            if self._hovered_index >= 0 and self._open_index < 0:
                if self._entries[self._hovered_index].enabled and self._entries[self._hovered_index].items:
                    self._open_flyout(self._hovered_index, app, er)
            # If a menu is already open and highlight moved to a new entry,
            # keep the flyout in sync with the highlighted top-level item.
            self._sync_open_menu_with_highlight(app, er)
            # Leaving both strip and flyout closes any open menu and clears highlight.
            if self._hovered_index < 0 and not self._pointer_in_open_menu_elements(event.pos):
                if self._open_index >= 0:
                    self._dismiss_flyout(app)
                self._hovered_index = -1
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

        if event.kind == EventType.KEY_DOWN:
            if event.key == pygame.K_LEFT:
                return self._cycle_top_level_menu(app, er, step=-1)
            if event.key == pygame.K_RIGHT:
                return self._cycle_top_level_menu(app, er, step=1)
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                if self._open_index >= 0:
                    # Keep up/down ownership with the active flyout panel.
                    return False
                return self._open_for_keyboard(app, er)

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self._open_index >= 0:
                    self._dismiss_flyout(app)
                    return True
                return self._open_for_keyboard(app, er)

            if event.key == pygame.K_ESCAPE and self._open_index >= 0:
                self._dismiss_flyout(app)
                return True

        return False

    def _dismiss_flyout(self, app: "GuiApplication") -> None:
        if self._open_index >= 0:
            owner = f"_menubar_{self.control_id}_{self._open_index}"
            app.overlay.hide(owner)
            self._open_index = -1
            self._open_flyout_rect = None
            self.invalidate()

    def _open_flyout(self, index: int, app: "GuiApplication", er: List[Rect]) -> None:
        if index < 0 or index >= len(self._entries):
            return
        entry = self._entries[index]
        if not entry.items:
            return
        owner = f"_menubar_{self.control_id}_{index}"
        er_rect = er[index]
        w, h = _FlyoutPanel.measure(entry.items, min_width=entry.flyout_min_width)
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
        self._open_flyout_rect = Rect(fx, fy, w, h)
        self.invalidate()

    def _on_flyout_dismissed(self, index: int) -> None:
        if self._open_index == index:
            self._open_index = -1
            self._open_flyout_rect = None
            self.invalidate()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bar_bg = getattr(theme, "panel", (40, 40, 50))
        text_col = theme.text
        disabled_col = (text_col[0] >> 1, text_col[1] >> 1, text_col[2] >> 1)
        hover_col = theme.highlight
        border_col = getattr(theme, "border", (60, 60, 70))

        font = theme.fonts.font_instance(self._draw_font_role, size=theme.fonts.scaled_size(self._FONT_SCALE))

        pygame.draw.rect(surface, bar_bg, self.rect)
        # Bottom border line
        pygame.draw.line(
            surface, border_col,
            (self.rect.left, self.rect.bottom - 1),
            (self.rect.right, self.rect.bottom - 1),
        )

        er = self._entry_rects(theme)
        pointer_pos = None
        app = self._last_app
        if app is not None and hasattr(app, "logical_pointer_pos"):
            pointer_pos = app.logical_pointer_pos
        else:
            pointer_pos = (0, 0)
        pointer_hovered = self._hover_index_from_pointer(pointer_pos, er)
        if pointer_hovered != self._hovered_index:
            self._hovered_index = pointer_hovered
            if self._last_app is not None:
                self._sync_open_menu_with_highlight(self._last_app, er)
        draw_hovered_index = pointer_hovered if pointer_hovered >= 0 else self._hovered_index
        for i, (entry, r) in enumerate(zip(self._entries, er)):
            if (i == self._open_index or i == draw_hovered_index) and entry.enabled:
                pygame.draw.rect(surface, hover_col, r)
            col = disabled_col if not entry.enabled else text_col
            if font:
                txt = font._font.render(entry.label, True, col) if hasattr(font, "_font") else font.render(entry.label, True, col)
                surface.blit(txt, (r.x + _ENTRY_PADDING_X, r.y + (r.height - txt.get_height()) // 2))
