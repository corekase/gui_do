"""CommandPaletteManager — searchable command launcher using an overlay."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from .overlay_manager import OverlayHandle, OverlayManager
from ..controls.overlay_panel_control import OverlayPanelControl
from ..controls.list_view_control import ListItem, ListViewControl
from ..controls.text_input_control import TextInputControl

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication

_SEARCH_H = 32
_PAD = 6
_ROW_H = 28


@dataclass
class CommandEntry:
    """A single entry in the command palette registry.

    Attributes:
        entry_id:    Unique identifier used for deregistration.
        title:       Short display name shown in the palette list.
        description: Optional longer description shown as a sub-label.
        action:      Zero-argument callable invoked when the entry is selected.
        category:    Optional category prefix used in fuzzy filtering.
    """

    entry_id: str
    title: str
    action: Callable[[], None]
    description: str = ""
    category: str = ""


class CommandPaletteHandle:
    """Handle for an open command palette session.

    Returned by :meth:`CommandPaletteManager.show`.
    """

    def __init__(self, manager: "CommandPaletteManager") -> None:
        self._manager = manager

    def close(self) -> None:
        """Close the palette without executing a command."""
        self._manager.hide()

    @property
    def is_open(self) -> bool:
        return self._manager.is_open


class CommandPaletteManager:
    """Searchable command palette backed by :class:`OverlayManager`.

    Register named commands via :meth:`register`, then call :meth:`show` to
    display the palette.  The palette provides a text search box and a filtered
    list of matching commands.  Selecting a command invokes its
    :attr:`~CommandEntry.action` and closes the palette.

    Usage::

        palette = CommandPaletteManager(app.overlays)
        palette.register(CommandEntry(
            entry_id="new_file",
            title="New File",
            action=lambda: open_new_file(),
            category="File",
        ))
        # Open from a keyboard shortcut handler:
        handle = palette.show(app)
    """

    _OWNER_ID = "__command_palette__"

    def __init__(self, overlay_manager: OverlayManager) -> None:
        self._overlays = overlay_manager
        self._entries: Dict[str, CommandEntry] = {}
        self._handle: Optional[OverlayHandle] = None
        # Live references for event forwarding
        self._search_input: Optional[TextInputControl] = None
        self._list_view: Optional[ListViewControl] = None
        self._overlay_panel: Optional[OverlayPanelControl] = None

    # ------------------------------------------------------------------
    # Registry API
    # ------------------------------------------------------------------

    def register(self, entry: CommandEntry) -> None:
        """Register a command entry.  Replaces any existing entry with the same id."""
        self._entries[str(entry.entry_id)] = entry

    def unregister(self, entry_id: str) -> bool:
        """Remove a registered entry. Returns ``True`` if it existed."""
        return bool(self._entries.pop(str(entry_id), None))

    def entry_count(self) -> int:
        """Return the number of registered entries."""
        return len(self._entries)

    # ------------------------------------------------------------------
    # Palette lifecycle
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._overlays.has_overlay(self._OWNER_ID)

    def show(
        self,
        app: "GuiApplication",
        *,
        rect: Optional[Rect] = None,
    ) -> CommandPaletteHandle:
        """Open the command palette overlay and return a handle.

        If *rect* is not given, the palette is centered horizontally in the
        current window at the top third of the screen.
        """
        self.hide()

        if rect is None:
            screen = pygame.display.get_surface()
            sw = screen.get_width() if screen else 800
            sh = screen.get_height() if screen else 600
            pw = min(600, sw - 40)
            ph = _SEARCH_H + _PAD * 3 + _ROW_H * 8
            rect = Rect((sw - pw) // 2, sh // 6, pw, ph)

        panel = OverlayPanelControl(self._OWNER_ID + "_panel", rect)
        self._overlay_panel = panel

        # Search input
        search_rect = Rect(
            rect.x + _PAD, rect.y + _PAD, rect.width - _PAD * 2, _SEARCH_H
        )
        search = TextInputControl(
            self._OWNER_ID + "_search",
            search_rect,
            placeholder="Type to search commands…",
        )
        search.tab_index = 0

        # Results list
        list_rect = Rect(
            rect.x + _PAD,
            rect.y + _PAD + _SEARCH_H + _PAD,
            rect.width - _PAD * 2,
            rect.height - _SEARCH_H - _PAD * 3,
        )
        listview = ListViewControl(
            self._OWNER_ID + "_list",
            list_rect,
            items=self._build_items(list(self._entries.values())),
            row_height=_ROW_H,
        )

        self._search_input = search
        self._list_view = listview

        # Wire search → filter
        current_entries = list(self._entries.values())

        def _on_search_change(text: str) -> None:
            filtered = self._filter_entries(current_entries, text)
            if listview is not None:
                listview.set_items(self._build_items(filtered))

        search._on_change = _on_search_change

        # Wire list selection → action + close
        def _on_select(idx: int, item: ListItem) -> None:
            entry = item.data
            self.hide()
            if entry is not None and callable(entry.action):
                try:
                    entry.action()
                except Exception:
                    pass

        listview._on_select = _on_select

        panel.add(search)
        panel.add(listview)

        self._handle = self._overlays.show(
            self._OWNER_ID,
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            on_dismiss=self._on_dismissed,
        )
        return CommandPaletteHandle(self)

    def hide(self) -> None:
        """Close the palette if open."""
        self._overlays.hide(self._OWNER_ID)
        self._search_input = None
        self._list_view = None
        self._overlay_panel = None
        self._handle = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_dismissed(self) -> None:
        self._search_input = None
        self._list_view = None
        self._overlay_panel = None
        self._handle = None

    @staticmethod
    def _filter_entries(
        entries: List[CommandEntry], query: str
    ) -> List[CommandEntry]:
        if not query:
            return entries
        q = query.lower()
        return [
            e
            for e in entries
            if q in e.title.lower()
            or q in e.description.lower()
            or q in e.category.lower()
        ]

    @staticmethod
    def _build_items(entries: List[CommandEntry]) -> List[ListItem]:
        return [
            ListItem(
                label=f"{e.category}: {e.title}" if e.category else e.title,
                value=e.entry_id,
                data=e,
            )
            for e in entries
        ]
