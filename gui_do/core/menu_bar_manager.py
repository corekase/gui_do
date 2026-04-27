"""MenuBarManager — feature-registration surface for application menu entries."""
from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

from ..core.context_menu_manager import ContextMenuItem
from ..controls.menu_bar_control import MenuBarControl, MenuEntry

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from pygame import Rect


class MenuBarManager:
    """Manages top-level menu entries contributed by features.

    Features call :meth:`register_menu` to declare their top-level menu and
    the items within it.  After all features have registered, call
    :meth:`build` to construct a :class:`MenuBarControl` with the merged
    entries in registration order, then add it to the scene.

    Usage::

        mgr = MenuBarManager()
        mgr.register_menu("File", [
            ContextMenuItem("New", action=on_new),
            ContextMenuItem("Open", action=on_open),
        ])
        mgr.register_menu("Edit", [
            ContextMenuItem("Undo", action=on_undo),
        ])

        bar = mgr.build("menubar", rect, app)
        app.add(bar)
    """

    def __init__(self) -> None:
        self._menus: Dict[str, List[ContextMenuItem]] = {}
        self._order: List[str] = []
        self._enabled: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_menu(
        self,
        label: str,
        items: List[ContextMenuItem],
        *,
        enabled: bool = True,
    ) -> None:
        """Declare or extend a top-level menu.

        Calling this multiple times with the same *label* appends items to the
        existing menu (useful for features adding to a shared menu like Edit).
        """
        label = str(label)
        if label not in self._menus:
            self._menus[label] = []
            self._order.append(label)
            self._enabled[label] = enabled
        self._menus[label].extend(items)

    def set_enabled(self, label: str, enabled: bool) -> None:
        """Enable or disable an entire top-level menu."""
        if label in self._enabled:
            self._enabled[label] = bool(enabled)

    def clear(self) -> None:
        """Remove all registered menus."""
        self._menus.clear()
        self._order.clear()
        self._enabled.clear()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(
        self,
        control_id: str,
        rect: "Rect",
        app: Optional["GuiApplication"] = None,
    ) -> "MenuBarControl":
        """Build and return a :class:`MenuBarControl` from registered menus."""
        entries = [
            MenuEntry(
                label=label,
                items=list(self._menus[label]),
                enabled=self._enabled.get(label, True),
            )
            for label in self._order
        ]
        bar = MenuBarControl(control_id, rect, entries)
        return bar

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def menu_labels(self) -> List[str]:
        """Return registered top-level menu labels in registration order."""
        return list(self._order)

    def items_for(self, label: str) -> List[ContextMenuItem]:
        """Return the registered items for a top-level menu, or empty list."""
        return list(self._menus.get(label, []))
