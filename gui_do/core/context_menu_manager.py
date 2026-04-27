"""ContextMenuManager — overlay-based contextual menus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..controls.overlay_panel_control import OverlayPanelControl
from ..core.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_ITEM_HEIGHT = 28
_SEPARATOR_HEIGHT = 9
_MENU_PADDING = 4
_MIN_MENU_WIDTH = 140
_TEXT_INDENT = 12


@dataclass
class ContextMenuItem:
    """A single entry in a context menu."""

    label: str
    action: Optional[Callable[[], None]] = None
    enabled: bool = True
    separator: bool = False  # When True, renders as a horizontal divider
    icon: Optional[str] = None  # Reserved for future icon support


@dataclass
class ContextMenuHandle:
    """Handle to a currently open context menu."""

    menu_id: str
    _manager: "ContextMenuManager"

    def dismiss(self) -> None:
        self._manager.dismiss(self.menu_id)

    @property
    def is_open(self) -> bool:
        return self._manager.has_menu(self.menu_id)


def _menu_height(items: List[ContextMenuItem]) -> int:
    h = _MENU_PADDING * 2
    for item in items:
        h += _SEPARATOR_HEIGHT if item.separator else _ITEM_HEIGHT
    return h


def _menu_width(items: List[ContextMenuItem]) -> int:
    try:
        font = pygame.font.SysFont(None, 18)
        widths = [font.size(item.label)[0] + _TEXT_INDENT * 2 + 16 for item in items if not item.separator]
        if widths:
            return max(_MIN_MENU_WIDTH, max(widths))
    except Exception:
        pass
    return _MIN_MENU_WIDTH


class _ContextMenuPanel(OverlayPanelControl):
    """Internal overlay panel that renders and handles one context menu."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: List[ContextMenuItem],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(control_id, rect, draw_background=False)
        self._items: List[ContextMenuItem] = list(items)
        self._on_close: Callable[[], None] = on_close
        self._hovered_index: int = -1
        self._keyboard_index: int = -1

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _item_rects(self) -> List[Rect]:
        """Return a Rect for each item row (including separators)."""
        rects: List[Rect] = []
        y = self.rect.y + _MENU_PADDING
        for item in self._items:
            h = _SEPARATOR_HEIGHT if item.separator else _ITEM_HEIGHT
            rects.append(Rect(self.rect.x, y, self.rect.width, h))
            y += h
        return rects

    def _selectable_indices(self) -> List[int]:
        return [i for i, item in enumerate(self._items) if not item.separator and item.enabled]

    def _activate_item(self, index: int) -> None:
        if 0 <= index < len(self._items):
            item = self._items[index]
            if not item.separator and item.enabled and item.action is not None:
                try:
                    self._on_close()
                    item.action()
                except Exception:
                    pass
                return
        self._on_close()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        rects = self._item_rects()

        if event.kind == EventType.MOUSE_MOTION:
            pos = event.pos
            self._hovered_index = -1
            for i, r in enumerate(rects):
                if r.collidepoint(pos) and not self._items[i].separator:
                    self._hovered_index = i
                    self._keyboard_index = i
                    break
            self.invalidate()
            return self.rect.collidepoint(pos)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            for i, r in enumerate(rects):
                if r.collidepoint(pos) and not self._items[i].separator:
                    if self._items[i].enabled:
                        self._activate_item(i)
                    return True
            return False

        if event.kind == EventType.KEY_DOWN:
            key = event.key
            selectable = self._selectable_indices()
            if not selectable:
                return False
            if key == pygame.K_DOWN:
                cur = self._keyboard_index
                nxt = [i for i in selectable if i > cur]
                self._keyboard_index = nxt[0] if nxt else selectable[0]
                self._hovered_index = self._keyboard_index
                self.invalidate()
                return True
            if key == pygame.K_UP:
                cur = self._keyboard_index
                prev = [i for i in selectable if i < cur]
                self._keyboard_index = prev[-1] if prev else selectable[-1]
                self._hovered_index = self._keyboard_index
                self.invalidate()
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if 0 <= self._keyboard_index < len(self._items):
                    self._activate_item(self._keyboard_index)
                return True
            return False

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        def _color(name: str, fallback: Tuple) -> Tuple:
            val = getattr(theme, name, fallback)
            if hasattr(val, "value"):
                val = val.value
            return val

        bg = _color("panel", (45, 45, 55))
        text_col = _color("text", (220, 220, 220))
        disabled_col = tuple(max(0, min(255, c // 2)) for c in text_col)
        hover_col = _color("highlight", (0, 100, 200))
        border_col = _color("border", (80, 80, 90))
        sep_col = border_col

        font = pygame.font.SysFont(None, 18)

        # Shadow
        shadow_rect = Rect(self.rect.x + 3, self.rect.y + 3, self.rect.width, self.rect.height)
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Background + border
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        rects = self._item_rects()
        for i, (item, r) in enumerate(zip(self._items, rects)):
            if item.separator:
                sep_y = r.y + r.height // 2
                pygame.draw.line(surface, sep_col, (r.x + 8, sep_y), (r.right - 8, sep_y))
                continue
            if i == self._hovered_index:
                pygame.draw.rect(surface, hover_col, r)
            col = text_col if item.enabled else disabled_col
            ts = font.render(item.label, True, col)
            surface.blit(ts, (r.x + _TEXT_INDENT, r.y + (r.height - ts.get_height()) // 2))


class ContextMenuManager:
    """Builds and displays context menus via the :class:`OverlayManager`.

    Typical usage::

        cm = ContextMenuManager(app)
        handle = cm.show(
            (mouse_x, mouse_y),
            [
                ContextMenuItem("Cut",  action=on_cut),
                ContextMenuItem("Copy", action=on_copy),
                ContextMenuItem(separator=True, label=""),
                ContextMenuItem("Paste", action=on_paste),
            ],
        )
    """

    def __init__(self, app: "GuiApplication") -> None:
        self._app = app
        self._next_id: int = 1
        self._open_ids: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(
        self,
        pos: Tuple[int, int],
        items: List[ContextMenuItem],
        *,
        on_dismiss: Optional[Callable[[], None]] = None,
    ) -> ContextMenuHandle:
        """Display a context menu rooted at *pos*.

        The menu is automatically dismissed when the user clicks outside it
        or presses Escape.  Returns a :class:`ContextMenuHandle` that can be
        used to programmatically close the menu.
        """
        menu_id = f"__ctxmenu__{self._next_id}__"
        self._next_id += 1

        def _close() -> None:
            self._dismiss_id(menu_id)

        # Compute size
        try:
            screen = self._app.surface.get_rect()
        except Exception:
            screen = Rect(0, 0, 1920, 1080)

        w = _menu_width(items)
        h = _menu_height(items)

        # Clamp to screen
        x = min(pos[0], screen.right - w - 4)
        y = min(pos[1], screen.bottom - h - 4)
        x = max(screen.left, x)
        y = max(screen.top, y)

        panel = _ContextMenuPanel(menu_id, Rect(x, y, w, h), items, _close)

        def _on_dismiss_outer() -> None:
            if menu_id in self._open_ids:
                self._open_ids.remove(menu_id)
            if on_dismiss is not None:
                try:
                    on_dismiss()
                except Exception:
                    pass

        self._open_ids.append(menu_id)
        self._app.overlay.show(
            menu_id,
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            on_dismiss=_on_dismiss_outer,
        )
        return ContextMenuHandle(menu_id, self)

    def dismiss(self, menu_id: str) -> bool:
        """Dismiss a specific context menu by id."""
        if menu_id in self._open_ids:
            return self._app.overlay.hide(menu_id)
        return False

    def dismiss_all(self) -> int:
        """Dismiss all open context menus."""
        ids = list(self._open_ids)
        count = 0
        for mid in ids:
            if self._app.overlay.hide(mid):
                count += 1
        return count

    def has_menu(self, menu_id: str) -> bool:
        return menu_id in self._open_ids

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _dismiss_id(self, menu_id: str) -> bool:
        if menu_id in self._open_ids:
            self._open_ids.remove(menu_id)
        return self._app.overlay.hide(menu_id)
