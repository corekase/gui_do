"""CommandPaletteManager — searchable command launcher using an overlay."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from .overlay_manager import OverlayHandle, OverlayManager
from ..events.gui_event import EventType
from ..controls.composite.overlay_panel_control import OverlayPanelControl
from ..controls.data.list_view_control import ListItem, ListViewControl
from ..controls.input.text_input_control import TextInputControl

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication

_SEARCH_H = 32
_PAD = 6
_ROW_H = 28


class _CommandPalettePanel(OverlayPanelControl):
    """Overlay panel that manages wheel-scroll and keyboard navigation within palette semantics."""

    def __init__(self, control_id: str, rect: Rect, *, listview: ListViewControl) -> None:
        super().__init__(control_id, rect)
        self._listview = listview

    def handle_event(self, event, app) -> bool:
        # Wheel: move selected item first; scroll_to_item() in _move_selection_by_wheel
        # ensures the new selection scrolls into view automatically.
        if event.kind == EventType.MOUSE_WHEEL:
            pointer = (
                event.pos
                if isinstance(event.pos, tuple) and len(event.pos) == 2
                else app.logical_pointer_pos
            )
            if isinstance(pointer, tuple) and len(pointer) == 2 and self.rect.collidepoint(pointer):
                delta = getattr(event, "wheel_delta", 0)
                if int(delta) == 0:
                    delta = getattr(event, "wheel_y", 0) or getattr(event, "y", 0)
                CommandPaletteManager._move_selection_by_wheel(self._listview, int(delta))
                return True

        # Keyboard navigation: intercept before children so the search TextInput
        # does not consume arrow/confirm keys.
        if event.kind == EventType.KEY_DOWN:
            key = getattr(event, "key", 0)
            # Standard accessibility navigation (ARIA listbox pattern).
            if key == pygame.K_UP:
                CommandPaletteManager._move_selection_by_wheel(self._listview, 1)
                return True
            if key == pygame.K_DOWN:
                CommandPaletteManager._move_selection_by_wheel(self._listview, -1)
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                idx = self._listview.selected_index
                if 0 <= idx < self._listview.item_count():
                    # Calling select() fires the registered _on_select callback,
                    # which executes the command and closes the palette.
                    self._listview.select(idx, scroll_to=False)
                return True

        return super().handle_event(event, app)


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

    def __init__(self, overlay_manager: OverlayManager, app: "Optional[GuiApplication]" = None, *, action_registry=None) -> None:
        self._overlays = overlay_manager
        self._entries: Dict[str, CommandEntry] = {}
        self._handle: Optional[OverlayHandle] = None
        self._background_trigger_dispose: Optional[Callable[[], bool]] = None
        self._action_registry = action_registry
        if app is not None:
            self._register_background_trigger(app)

    # ------------------------------------------------------------------
    # Registry API
    # ------------------------------------------------------------------

    def register(self, entry: CommandEntry) -> None:
        """Register a command entry.  Replaces any existing entry with the same id."""
        self._entries[str(entry.entry_id)] = entry

    def register_action_registry(
        self,
        action_registry,
        *,
        context=None,
        category: str | None = None,
        clear_existing: bool = False,
    ) -> None:
        """Register entries projected from an ActionRegistry."""
        if clear_existing:
            self._entries.clear()
        for entry in action_registry.command_entries(context=context):
            if category is not None and str(entry.category) != str(category):
                continue
            self.register(entry)

    def unregister(self, entry_id: str) -> bool:
        """Remove a registered entry. Returns ``True`` if it existed."""
        return bool(self._entries.pop(str(entry_id), None))

    def entry_count(self) -> int:
        """Return the number of registered entries."""
        return len(self._entries)

    def entries(self) -> List[CommandEntry]:
        """Return a snapshot list of currently registered entries."""
        return list(self._entries.values())

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
    ) -> "CommandPaletteHandle":
        """Open the command palette overlay and return a handle.

        If the palette is already open, calling this method closes it and
        returns the handle (toggle behaviour).  If *rect* is not given, the
        palette is centered horizontally in the current window at the top third
        of the screen.
        """
        # Always sync to the current scene's overlay manager so scene switches
        # don't leave the palette on a stale overlay.
        self._overlays = app.overlay

        # Toggle: close if already visible (uses freshly synced overlay).
        if self.is_open:
            self.hide()
            return CommandPaletteHandle(self)

        # Auto-register the background right-click trigger the first time show
        # is called with an app, if it was not already set up at construction.
        if self._background_trigger_dispose is None:
            self._register_background_trigger(app)

        # Refresh entries from a bound ActionRegistry so both the F5 path and
        # the background right-click path always display the current command set.
        if self._action_registry is not None:
            self.register_action_registry(self._action_registry)

        if rect is None:
            screen = pygame.display.get_surface()
            sw = screen.get_width() if screen else 800
            sh = screen.get_height() if screen else 600
            pw = min(600, sw - 40)
            ph = _SEARCH_H + _PAD * 3 + _ROW_H * 8
            rect = Rect((sw - pw) // 2, sh // 6, pw, ph)

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

        panel = _CommandPalettePanel(
            self._OWNER_ID + "_panel",
            rect,
            listview=listview,
        )

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
        self._handle = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_background_trigger(self, app: "GuiApplication") -> None:
        """Register a fallthrough handler that opens the palette on background right-click.

        Empty space means: not over an overlay, not over a window, and not over
        a focusable control hit target.  Uses :meth:`~GuiApplication.chain_screen_fallthrough`
        so the handler only fires when the full event pipeline found nothing else
        to consume the click.
        """
        stored_app = app

        def _on_background_right_click(event) -> bool:
            if getattr(event, "kind", None) != EventType.MOUSE_BUTTON_DOWN:
                return False
            if int(getattr(event, "button", 0) or 0) != 3:
                return False
            pos = getattr(event, "pos", None)
            if not (isinstance(pos, tuple) and len(pos) == 2):
                return False
            if stored_app.overlay.point_in_any_overlay(pos):
                return False
            window_hit, focus_target = stored_app.scene.pointer_context_at(pos)
            if window_hit or focus_target is not None:
                return False
            self._overlays = stored_app.overlay
            self.show(stored_app)
            return True

        self._background_trigger_dispose = app.chain_screen_fallthrough(
            event_handler=_on_background_right_click,
        )

    def _on_dismissed(self) -> None:
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

    @staticmethod
    def _move_selection_by_wheel(listview: ListViewControl, delta: int) -> None:
        """Step selection via wheel and clamp to list bounds."""
        if int(delta) == 0:
            return
        count = listview.item_count()
        if count <= 0:
            return
        current = listview.selected_index
        if current < 0:
            current = 0
        target = max(0, min(count - 1, current - int(delta)))
        listview.selected_index = target
        listview.scroll_to_item(target)
