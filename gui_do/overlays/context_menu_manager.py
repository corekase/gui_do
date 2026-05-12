"""ContextMenuManager — overlay-based contextual menus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pygame import Rect

from .menu_overlay_panel_base import _MenuOverlayPanelBase

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication


_ITEM_HEIGHT = 28
_SEPARATOR_HEIGHT = 9
_MENU_PADDING = 4
_MIN_MENU_WIDTH = 140
_TEXT_INDENT = 12
_FONT_SIZE = 18


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


class _ContextMenuPanel(_MenuOverlayPanelBase):
    """Internal overlay panel that renders and handles one context menu."""

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
            item_height=_ITEM_HEIGHT,
            separator_height=_SEPARATOR_HEIGHT,
            padding=_MENU_PADDING,
            text_padding=_TEXT_INDENT,
            min_width=_MIN_MENU_WIDTH,
            font_size=_FONT_SIZE,
        )


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

        w, h = _ContextMenuPanel.measure(
            items,
            item_height=_ITEM_HEIGHT,
            separator_height=_SEPARATOR_HEIGHT,
            padding=_MENU_PADDING,
            text_padding=_TEXT_INDENT,
            min_width=_MIN_MENU_WIDTH,
            font_size=_FONT_SIZE,
        )

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

    def show_actions(
        self,
        pos: Tuple[int, int],
        action_registry,
        *,
        context=None,
        category: str | None = None,
        on_dismiss: Optional[Callable[[], None]] = None,
    ) -> ContextMenuHandle:
        """Display a context menu built from an ActionRegistry projection."""
        items = action_registry.context_menu_items(context=context, category=category)
        return self.show(pos, items, on_dismiss=on_dismiss)

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
