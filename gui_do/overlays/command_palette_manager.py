"""CommandPaletteManager — list-based command launcher using an overlay."""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from .overlay_manager import OverlayHandle, OverlayManager
from ..events.gui_event import EventType
from ..controls.composite.overlay_panel_control import OverlayPanelControl
from ..controls.data.list_view_control import ListItem, ListViewControl

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication

_PAD = 6
_ROW_H = 28
_MAX_VISIBLE_ROWS = 10


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
                CommandPaletteManager._move_selection_by_wheel(self._listview, event.wheel_y)
                return True

        # Keyboard navigation: intercept before children so the search TextInput
        # does not consume arrow/confirm keys.
        if event.kind == EventType.KEY_DOWN:
            key = event.key or 0
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
    """List-based command palette backed by :class:`OverlayManager`.

    Register named commands via :meth:`register`, then call :meth:`show` to
    display the palette. Selecting a command invokes its
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
        self._before_show_callback: Optional[Callable[[], None]] = None
        self._selection_provider: Optional[Callable[[], Optional[str]]] = None
        self._entry_selected_callback: Optional[Callable[[CommandEntry], None]] = None
        self._selected_entry_id_by_scene: Dict[str, str] = {}
        self._window_order_rank_by_scene: Dict[str, Dict[str, int]] = {}
        self._window_order_next_by_scene: Dict[str, int] = {}
        if app is not None:
            self._register_background_trigger(app)

    # ------------------------------------------------------------------
    # Registry API
    # ------------------------------------------------------------------

    def register(self, entry: CommandEntry) -> None:
        """Register a command entry.  Replaces any existing entry with the same id."""
        self._entries[str(entry.entry_id)] = entry

    def clear(self) -> None:
        """Remove all registered entries."""
        self._entries.clear()

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

    def set_before_show(self, callback: Optional[Callable[[], None]]) -> None:
        """Set a callback invoked immediately before the palette opens."""
        self._before_show_callback = callback

    def set_selection_provider(self, provider: Optional[Callable[[], Optional[str]]]) -> None:
        """Set a provider returning the entry id to preselect when the palette opens."""
        self._selection_provider = provider

    def set_on_entry_selected(self, callback: Optional[Callable[[CommandEntry], None]]) -> None:
        """Set a callback invoked when a palette entry is selected."""
        self._entry_selected_callback = callback

    def enable_builtin_scene_and_window_entries(
        self,
        app: "GuiApplication",
        *,
        on_scene_selected: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Populate built-in scene/window entries and remember selection per scene.

        This opt-in helper rebuilds palette entries immediately before open using:
        - scene entries for all non-active, non-``default`` scenes
        - window entries for the active scene using window titles

        Selection is remembered per active scene and restored on reopen.
        """

        def _before_show() -> None:
            self._register_builtin_scene_and_window_entries(app, on_scene_selected=on_scene_selected)

        def _selected_entry_id() -> Optional[str]:
            return self._selected_entry_id_for_scene(app)

        def _remember_selection(entry: CommandEntry) -> None:
            self._remember_selection_for_scene(app, entry)

        self.set_before_show(_before_show)
        self.set_selection_provider(_selected_entry_id)
        self.set_on_entry_selected(_remember_selection)

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
        selected_entry_id: Optional[str] = None,
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

        if callable(self._before_show_callback):
            self._before_show_callback()

        current_entries = list(self._entries.values())
        if not current_entries:
            return CommandPaletteHandle(self)
        if selected_entry_id is None and callable(self._selection_provider):
            selected_entry_id = self._selection_provider()

        if rect is None:
            screen = pygame.display.get_surface()
            sw = screen.get_width() if screen else 800
            sh = screen.get_height() if screen else 600
            pw = min(600, sw - 40)
            visible_rows = max(1, min(len(current_entries), _MAX_VISIBLE_ROWS))
            ph = _PAD * 2 + _ROW_H * visible_rows
            rect = Rect((sw - pw) // 2, (sh - ph) // 2, pw, ph)

        # Results list
        list_rect = Rect(
            rect.x + _PAD,
            rect.y + _PAD,
            rect.width - _PAD * 2,
            rect.height - _PAD * 2,
        )
        selected_index = self._selected_index_for_entry_id(current_entries, selected_entry_id)
        listview = ListViewControl(
            self._OWNER_ID + "_list",
            list_rect,
            items=self._build_items(current_entries),
            row_height=_ROW_H,
            selected_index=selected_index,
        )
        if 0 <= selected_index < listview.item_count():
            listview.scroll_to_item(selected_index)

        # Wire list selection → action + close
        def _on_select(idx: int, item: ListItem) -> None:
            del idx
            entry = item.data
            if entry is not None and callable(self._entry_selected_callback):
                try:
                    self._entry_selected_callback(entry)
                except Exception:
                    pass
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

    def bind_toggle_key(
        self,
        app: "GuiApplication",
        key: int,
        *,
        scene: "Optional[str]" = None,
        action_id: str = "command_palette_toggle",
        on_before_show: Optional[Callable[[], None]] = None,
    ) -> None:
        """Bind *key* so it toggles this palette in the given scene(s).

        *scene* may be a single scene name, a list of scene names, or ``None``
        to bind globally (all scenes).  *action_id* is the internal action name
        registered with :attr:`~GuiApplication.actions`; override it only when
        multiple palettes share the same application.

        Example::

            palette.bind_toggle_key(app, pygame.K_F5, scene=["main", "editor"])
        """
        def _toggle(_event):
            if callable(on_before_show):
                on_before_show()
            self.show(app)
            return True

        app.actions.register_action(action_id, _toggle)

        scenes = [scene] if isinstance(scene, str) else (scene or [None])
        for s in scenes:
            if s is None:
                app.actions.bind_key(key, action_id)
            else:
                app.actions.bind_key(key, action_id, scene=s)

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
            if event.kind != EventType.MOUSE_BUTTON_DOWN:
                return False
            if (event.button or 0) != 3:
                return False
            pos = event.pos
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

    def _register_builtin_scene_and_window_entries(
        self,
        app: "GuiApplication",
        *,
        on_scene_selected: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.clear()

        scene_pretty_name_fn = getattr(app, "scene_pretty_name", None)
        for scene_name in self._allowed_builtin_scene_names(app):
            pretty_name = str(scene_name)
            if callable(scene_pretty_name_fn):
                pretty_name = str(scene_pretty_name_fn(scene_name))
            self.register(
                CommandEntry(
                    entry_id=f"scene:{scene_name}",
                    title=pretty_name,
                    action=lambda target=scene_name: self._select_builtin_scene(app, target, on_scene_selected),
                    category="Scenes",
                )
            )

        windows = []
        scene = getattr(app, "scene", None)
        walk_nodes = getattr(scene, "_walk_nodes", None)
        if callable(walk_nodes):
            for node in walk_nodes():
                is_window = getattr(node, "is_window", None)
                if callable(is_window) and is_window():
                    windows.append(node)

        scene_order_key = self._window_scene_order_key(app)
        windows.sort(key=lambda window: self._window_order_rank(scene_order_key, window))
        for window in windows:
            control_id = str(getattr(window, "control_id", ""))
            window_title = str(getattr(window, "title", "") or control_id or "Window")
            self.register(
                CommandEntry(
                    entry_id=f"window:{self._selection_scene_key(app)}:{control_id}",
                    title=window_title,
                    action=lambda target=window: self._toggle_builtin_window(app, target),
                    category="Windows",
                )
            )

    @staticmethod
    def _allowed_builtin_scene_names(app: "GuiApplication") -> List[str]:
        scene_names_fn = getattr(app, "scene_names", None)
        if not callable(scene_names_fn):
            return []
        active = str(getattr(app, "active_scene_name", ""))
        names = [str(name) for name in scene_names_fn()]
        features = getattr(app, "features", None)
        feature_map = getattr(features, "_features", None)
        if not hasattr(feature_map, "values"):
            return [name for name in names if name != active]

        scene_counts: Counter[str] = Counter()
        for feature in feature_map.values():
            scene_name = getattr(feature, "scene_name", None)
            if isinstance(scene_name, str) and scene_name:
                scene_counts[scene_name] += 1

        allowed: List[str] = []
        for name in names:
            if name == active:
                continue
            if scene_counts and scene_counts.get(name, 0) <= 0:
                continue
            allowed.append(name)
        return allowed

    @staticmethod
    def _select_builtin_scene(
        app: "GuiApplication",
        scene_name: str,
        on_scene_selected: Optional[Callable[[str], None]],
    ) -> None:
        if on_scene_selected is not None:
            on_scene_selected(scene_name)
            return
        switch_scene = getattr(app, "switch_scene", None)
        if callable(switch_scene):
            switch_scene(scene_name)

    def _toggle_builtin_window(self, app: "GuiApplication", window) -> None:
        next_visible = not bool(getattr(window, "visible", False))
        setter = self._resolve_builtin_visibility_setter(app, window)
        if setter is not None:
            setter(next_visible)
            return
        window.visible = next_visible
        tile_windows = getattr(app, "tile_windows", None)
        if callable(tile_windows):
            tile_windows()

    @staticmethod
    def _resolve_builtin_visibility_setter(app: "GuiApplication", window):
        control_id = str(getattr(window, "control_id", "")).strip()
        if not control_id.endswith("_window"):
            return None
        window_key = control_id[: -len("_window")]
        if not window_key:
            return None
        method_name = f"set_{window_key}_window_visible"

        app_method = getattr(app, method_name, None)
        if callable(app_method):
            return app_method

        features = getattr(app, "features", None)
        feature_hosts = getattr(features, "_feature_hosts", None)
        if isinstance(feature_hosts, dict):
            for host in feature_hosts.values():
                host_method = getattr(host, method_name, None)
                if callable(host_method):
                    return host_method
        return None

    @staticmethod
    def _selection_scene_key(app: "GuiApplication") -> str:
        return str(getattr(app, "active_scene_name", "")).strip()

    def _selected_entry_id_for_scene(self, app: "GuiApplication") -> Optional[str]:
        scene_key = self._selection_scene_key(app)
        if not scene_key:
            return None
        return self._selected_entry_id_by_scene.get(scene_key)

    def _remember_selection_for_scene(self, app: "GuiApplication", entry: CommandEntry) -> None:
        scene_key = self._selection_scene_key(app)
        if not scene_key:
            return
        self._selected_entry_id_by_scene[scene_key] = str(entry.entry_id)

    def _window_scene_order_key(self, app: "GuiApplication") -> str:
        scene_key = self._selection_scene_key(app)
        if scene_key:
            return scene_key
        return f"scene:{id(getattr(app, 'scene', None))}"

    @staticmethod
    def _window_order_key(window) -> str:
        control_id = str(getattr(window, "control_id", "")).strip()
        if control_id:
            return control_id
        title = str(getattr(window, "title", "")).strip()
        if title:
            return f"title:{title}"
        return f"window:{id(window)}"

    def _window_order_rank(self, scene_order_key: str, window) -> int:
        ranks = self._window_order_rank_by_scene.setdefault(scene_order_key, {})
        key = self._window_order_key(window)
        existing = ranks.get(key)
        if existing is not None:
            return existing
        next_rank = self._window_order_next_by_scene.get(scene_order_key, 0)
        ranks[key] = next_rank
        self._window_order_next_by_scene[scene_order_key] = next_rank + 1
        return next_rank

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
    def _selected_index_for_entry_id(entries: List[CommandEntry], entry_id: Optional[str]) -> int:
        if not entry_id:
            return 0 if entries else -1
        for index, entry in enumerate(entries):
            if str(entry.entry_id) == str(entry_id):
                return index
        return 0 if entries else -1

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
