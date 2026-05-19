"""CommandPaletteManager — list-based command launcher using an overlay."""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Callable, Optional, Sequence, TYPE_CHECKING

import pygame
from pygame import Rect

from .overlay_manager import OverlayHandle, OverlayManager
from ..events.gui_event import EventType
from ..controls.composite.overlay_panel_control import OverlayPanelControl
from ..controls.data.list_view_control import ListItem, ListViewControl
from ..graphics.built_in_definitions import BUILT_IN_COLOURS

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication

_PAD = 6
_ROW_H = 28
_MAX_VISIBLE_ROWS = 10


def _resolved_none_color(theme) -> tuple[int, int, int] | tuple[int, int, int, int]:
    def _valid_color(value) -> bool:
        if not isinstance(value, (tuple, list)):
            return False
        if len(value) not in (3, 4):
            return False
        return all(isinstance(component, int) and 0 <= component <= 255 for component in value)

    none_color = getattr(theme, "none", None)
    if _valid_color(none_color):
        return tuple(none_color)
    shadow_color = getattr(theme, "shadow", None)
    if _valid_color(shadow_color):
        return tuple(shadow_color)
    return (0, 0, 0)


def _resolved_highlight_color(theme) -> tuple[int, int, int] | tuple[int, int, int, int]:
    highlight_color = getattr(theme, "highlight", None)
    if isinstance(highlight_color, (tuple, list)) and len(highlight_color) in (3, 4):
        if all(isinstance(component, int) and 0 <= component <= 255 for component in highlight_color):
            return tuple(highlight_color)
    return tuple(BUILT_IN_COLOURS["highlight"])


class _CommandPalettePanel(OverlayPanelControl):
    """Overlay panel that manages wheel-scroll and keyboard navigation within palette semantics."""

    def __init__(self, control_id: str, rect: Rect, *, listview: ListViewControl) -> None:
        super().__init__(control_id, rect)
        self._listview = listview

    _POINTER_EVENT_KINDS = frozenset((
        EventType.MOUSE_WHEEL,
        EventType.MOUSE_BUTTON_DOWN,
        EventType.MOUSE_BUTTON_UP,
        EventType.MOUSE_MOTION,
    ))

    def handle_event(self, event, app, theme=None) -> bool:
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

        result = super().handle_event(event, app)

        # Consume all remaining pointer events over the palette panel so they
        # never reach controls rendered beneath the overlay.
        if not result and event.kind in self._POINTER_EVENT_KINDS:
            pointer = (
                event.pos
                if isinstance(event.pos, tuple) and len(event.pos) == 2
                else getattr(app, "logical_pointer_pos", None)
            )
            if isinstance(pointer, tuple) and len(pointer) == 2 and self.rect.collidepoint(pointer):
                return True

        return result

    def draw_screen_phase(self, surface: "pygame.Surface", theme, app=None) -> None:
        pygame.draw.rect(surface, theme.medium, self.rect)
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
        border_color = _resolved_none_color(theme)
        pygame.draw.rect(surface, border_color, self.rect, width=1)


class _CommandPaletteListView(ListViewControl):
    def __init__(self, control_id: str, rect: Rect, items=None, *, row_height: int = _ROW_H, selected_index: int = -1) -> None:
        super().__init__(control_id, rect, items=items, row_height=row_height, selected_index=selected_index)
        self._toggle_visual_cache: Dict[tuple, object] = {}
        self._scene_visual_cache: Dict[tuple, object] = {}
        self._draw_font = None

    def draw(self, surface: "pygame.Surface", theme) -> None:
        if not self.visible:
            return
        r = self.rect
        pygame.draw.rect(surface, theme.medium, r)

        vh = self._viewport_height()
        if self._parent_scroll_view() is not None and not self._show_scrollbar:
            first_row = 0
            last_row = len(self._items)
        else:
            first_row = self._scroll_offset // self._row_height
            last_row = min(len(self._items), first_row + vh // self._row_height + 2)

        content_w = r.width
        if self._scrollbar_rect() is not None:
            content_w = max(1, content_w - 12)
        content_rect = Rect(r.x, r.y, content_w, r.height)

        clip = surface.get_clip()
        surface.set_clip(content_rect.clip(clip) if clip else content_rect)
        selected_border_color = _resolved_highlight_color(theme)
        for i in range(first_row, last_row):
            if i >= len(self._items):
                break
            item = self._items[i]
            row_y = r.y + i * self._row_height - self._scroll_offset
            row_rect = Rect(content_rect.x, row_y, content_rect.width, self._row_height)
            entry = item.data
            is_selected = i in self._selected_set

            if is_selected:
                pygame.draw.rect(surface, theme.medium, row_rect)

            if isinstance(entry, CommandEntry) and entry.render_kind == "window_toggle":
                self._draw_window_toggle_row(surface, theme, row_rect, entry)
                if is_selected:
                    pygame.draw.rect(surface, selected_border_color, row_rect, width=1)
                continue

            if isinstance(entry, CommandEntry) and entry.render_kind == "command_toggle":
                self._draw_command_toggle_row(surface, theme, row_rect, entry)
                if is_selected:
                    pygame.draw.rect(surface, selected_border_color, row_rect, width=1)
                continue

            if isinstance(entry, CommandEntry) and entry.render_kind == "command_button":
                self._draw_command_button_row(surface, theme, row_rect, entry)
                if is_selected:
                    pygame.draw.rect(surface, selected_border_color, row_rect, width=1)
                continue

            self._draw_standard_row(surface, theme, row_rect, item, selected=is_selected)
            if is_selected:
                pygame.draw.rect(surface, selected_border_color, row_rect, width=1)

        surface.set_clip(clip)

        sb_rect = self._scrollbar_rect()
        handle_rect = self._scrollbar_handle_rect()
        if sb_rect is not None and handle_rect is not None:
            pygame.draw.rect(surface, theme.medium, sb_rect)
            pygame.draw.rect(surface, theme.medium, handle_rect, border_radius=2)

    def _draw_standard_row(self, surface: "pygame.Surface", theme, row_rect: Rect, item: ListItem, *, selected: bool = False) -> None:
        entry = item.data
        if isinstance(entry, CommandEntry) and entry.category == "Scenes":
            factory = theme.graphics_factory
            font_revision = factory.font_revision()
            scene_rect = Rect(row_rect.x + 2, row_rect.y + 2, max(1, row_rect.width - 4), max(1, row_rect.height - 4))
            scene_text = str(entry.title)
            visual_key = (scene_text, scene_rect.width, scene_rect.height, font_revision)
            visuals = self._scene_visual_cache.get(visual_key)
            if visuals is None:
                visuals = factory.build_interactive_visuals("round", scene_text, scene_rect, font_role="body")
                self._scene_visual_cache[visual_key] = visuals
            selected_surface = factory.resolve_visual_state(
                visuals,
                visible=True,
                enabled=bool(item.enabled),
                armed=False,
                hovered=False,
            )
            surface.blit(selected_surface, scene_rect)
            return

        if self._draw_font is None:
            if not hasattr(theme, "fonts"):
                raise RuntimeError("CommandPaletteManager requires theme with centralized font roles.")
            self._draw_font = theme.fonts.font_instance("command_palette.text", size=18)
        font = self._draw_font
        text_color = theme.text
        if not item.enabled:
            text_color = (text_color[0] >> 1, text_color[1] >> 1, text_color[2] >> 1)
        text_surf = font.render(item.label, True, text_color)
        surface.blit(text_surf, (row_rect.x + 4, row_rect.y + (self._row_height - text_surf.get_height()) // 2))

    def _draw_window_toggle_row(self, surface: "pygame.Surface", theme, row_rect: Rect, entry: "CommandEntry") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        button_rect = Rect(row_rect.x + 2, row_rect.y + 2, max(1, row_rect.width - 4), max(1, row_rect.height - 4))
        visual_key = (entry.title, button_rect.width, button_rect.height, font_revision)
        visuals = self._toggle_visual_cache.get(visual_key)
        if visuals is None:
            visuals = factory.build_interactive_visuals("box", entry.title, button_rect, font_role="body")
            self._toggle_visual_cache[visual_key] = visuals
        selected = factory.resolve_visual_state(
            visuals,
            visible=True,
            enabled=True,
            armed=bool(entry.window_visible),
            hovered=False,
        )
        surface.blit(selected, button_rect)

    def _draw_command_toggle_row(self, surface: "pygame.Surface", theme, row_rect: Rect, entry: "CommandEntry") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        button_rect = Rect(row_rect.x + 2, row_rect.y + 2, max(1, row_rect.width - 4), max(1, row_rect.height - 4))
        visual_key = (entry.title, button_rect.width, button_rect.height, font_revision, "command_toggle")
        visuals = self._toggle_visual_cache.get(visual_key)
        if visuals is None:
            visuals = factory.build_interactive_visuals("box", entry.title, button_rect, font_role="body")
            self._toggle_visual_cache[visual_key] = visuals
        selected = factory.resolve_visual_state(
            visuals,
            visible=True,
            enabled=True,
            armed=bool(entry.toggle_state),
            hovered=False,
        )
        surface.blit(selected, button_rect)

    def _draw_command_button_row(self, surface: "pygame.Surface", theme, row_rect: Rect, entry: "CommandEntry") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        button_rect = Rect(row_rect.x + 2, row_rect.y + 2, max(1, row_rect.width - 4), max(1, row_rect.height - 4))
        visual_key = (entry.title, button_rect.width, button_rect.height, font_revision, "command_button")
        visuals = self._toggle_visual_cache.get(visual_key)
        if visuals is None:
            visuals = factory.build_interactive_visuals("box", entry.title, button_rect, font_role="body")
            self._toggle_visual_cache[visual_key] = visuals
        selected = factory.resolve_visual_state(
            visuals,
            visible=True,
            enabled=True,
            armed=False,
            hovered=False,
        )
        surface.blit(selected, button_rect)


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
    scene_name: str = ""
    render_kind: str = ""
    window_visible: bool = False
    toggle_state: bool = False
    refresh_after_action: Optional[Callable[["CommandEntry"], None]] = None


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
    _BUILTIN_TOGGLE_ACTION_ID = "command_palette_toggle_builtin"

    def __init__(self, overlay_manager: OverlayManager, app: "Optional[GuiApplication]" = None, *, action_registry=None) -> None:
        self._overlays = overlay_manager
        self._app = app
        self._entries: Dict[str, CommandEntry] = {}
        self._entry_snapshot: List[CommandEntry] = []
        self._entry_items: List[ListItem] = []
        self._entry_index_by_id: Dict[str, int] = {}
        self._entries_dirty: bool = True
        self._handle: Optional[OverlayHandle] = None
        self._open_listview: Optional[_CommandPaletteListView] = None
        self._open_rect: Optional[Rect] = None
        self._previous_focus = None
        self._action_registry = action_registry
        self._before_show_callback: Optional[Callable[[], None]] = None
        self._selection_provider: Optional[Callable[[], Optional[str]]] = None
        self._entry_selected_callback: Optional[Callable[[CommandEntry], None]] = None
        self._selected_entry_id_by_scene: Dict[str, str] = {}
        self._window_presentation = None
        self._include_scene_entries: bool = True
        self._include_window_entries: bool = True
        self._group_order: tuple[str, ...] = ("scenes", "windows", "custom")
        self._custom_entries_provider: Optional[Callable[..., Sequence[CommandEntry]]] = None
        self._suppressed_window_select_entry_id: Optional[str] = None
        self._suppressed_command_toggle_select_entry_id: Optional[str] = None
        self._suppressed_command_button_select_entry_id: Optional[str] = None

    def _invalidate_entry_projection(self) -> None:
        self._entries_dirty = True
        self._entry_snapshot = []
        self._entry_items = []
        self._entry_index_by_id = {}

    def _project_entries(self) -> tuple[List[CommandEntry], List[ListItem], Dict[str, int]]:
        if self._entries_dirty:
            app = self._app
            entries = [entry for entry in self._entries.values() if self._entry_is_visible_for_scene(entry, app)]
            self._entry_snapshot = entries
            self._entry_items = self._build_items(entries)
            self._entry_index_by_id = {
                str(entry.entry_id): index
                for index, entry in enumerate(entries)
            }
            self._entries_dirty = False
        return self._entry_snapshot, self._entry_items, self._entry_index_by_id

    # ------------------------------------------------------------------
    # Registry API
    # ------------------------------------------------------------------

    def register(self, entry: CommandEntry) -> None:
        """Register a command entry.  Replaces any existing entry with the same id."""
        self._entries[str(entry.entry_id)] = entry
        self._invalidate_entry_projection()

    def clear(self) -> None:
        """Remove all registered entries."""
        self._entries.clear()
        self._invalidate_entry_projection()

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
        removed = bool(self._entries.pop(str(entry_id), None))
        if removed:
            self._invalidate_entry_projection()
        return removed

    def entry_count(self) -> int:
        """Return the number of registered entries."""
        return len(self._entries)

    def entries(self) -> List[CommandEntry]:
        """Return a snapshot list of entries visible in the active scene."""
        app = self._app
        return [entry for entry in self._entries.values() if self._entry_is_visible_for_scene(entry, app)]

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
        window_presentation=None,
    ) -> None:
        """Populate built-in scene/window entries and remember selection per scene.

        This opt-in helper rebuilds palette entries immediately before open using:
        - scene entries for all non-active, non-``default`` scenes
        - window entries for the active scene using window titles

        Selection is remembered per active scene and restored on reopen.

        When *window_presentation* (a ``FeatureWindowPresentationModel``) is
        provided, window toggle actions route through it so that task panel
        toggle buttons and tile_windows stay in sync with the palette.
        """
        self.configure_builtin_entry_groups(
            app,
            on_scene_selected=on_scene_selected,
            window_presentation=window_presentation,
            include_scene_entries=True,
            include_window_entries=True,
            group_order=("scenes", "windows", "custom"),
            custom_entries_provider=None,
        )

    def configure_builtin_entry_groups(
        self,
        app: "GuiApplication",
        *,
        on_scene_selected: Optional[Callable[[str], None]] = None,
        window_presentation=None,
        include_scene_entries: bool = True,
        include_window_entries: bool = True,
        group_order: Sequence[str] = ("scenes", "windows", "custom"),
        custom_entries_provider: Optional[Callable[..., Sequence[CommandEntry]]] = None,
    ) -> None:
        """Configure built-in palette groups and their placement order.

        ``group_order`` may include any of ``"scenes"``, ``"windows"``, and
        ``"custom"`` in any order, allowing built-in groups to appear before,
        after, or between custom entries.

        ``custom_entries_provider`` is a user-defined callable returning a
        sequence of :class:`CommandEntry` objects. It may accept zero arguments
        or a single ``app`` argument.
        """
        self._app = app
        self._window_presentation = window_presentation
        self._include_scene_entries = bool(include_scene_entries)
        self._include_window_entries = bool(include_window_entries)
        self._group_order = self._normalize_group_order(group_order)
        self._custom_entries_provider = custom_entries_provider

        def _before_show() -> None:
            self._register_configured_builtin_entries(app, on_scene_selected=on_scene_selected)

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

        If the palette is already open, repeated calls are ignored and the
        existing open session remains visible. If *rect* is not given, the
        palette is centered horizontally in the current window at the top third
        of the screen.
        """
        # Always sync to the current scene's overlay manager so scene switches
        # don't leave the palette on a stale overlay.
        self._app = app
        self._overlays = app.overlay

        # Idempotent open: ignore repeated activation while already visible.
        if self.is_open:
            return CommandPaletteHandle(self)

        if callable(self._before_show_callback):
            self._before_show_callback()

        current_entries, current_items, entry_index_by_id = self._project_entries()
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
        self._open_rect = Rect(rect)

        # Results list
        list_rect = Rect(
            rect.x + _PAD,
            rect.y + _PAD,
            rect.width - _PAD * 2,
            rect.height - _PAD * 2,
        )
        selected_index = self._selected_index_for_entry_id(current_entries, selected_entry_id, entry_index_by_id)
        listview = _CommandPaletteListView(
            self._OWNER_ID + "_list",
            list_rect,
            items=list(current_items),
            row_height=_ROW_H,
            selected_index=selected_index,
        )
        self._open_listview = listview
        if 0 <= selected_index < listview.item_count():
            listview.scroll_to_item(selected_index)

        # Wire list selection → action + close
        def _on_select(idx: int, item: ListItem) -> None:
            entry = item.data
            if (
                isinstance(entry, CommandEntry)
                and entry.render_kind == "window_toggle"
                and str(entry.entry_id) == str(self._suppressed_window_select_entry_id or "")
            ):
                self._suppressed_window_select_entry_id = None
                return
            if (
                isinstance(entry, CommandEntry)
                and entry.render_kind == "command_toggle"
                and str(entry.entry_id) == str(self._suppressed_command_toggle_select_entry_id or "")
            ):
                self._suppressed_command_toggle_select_entry_id = None
                return
            if (
                isinstance(entry, CommandEntry)
                and entry.render_kind == "command_button"
                and str(entry.entry_id) == str(self._suppressed_command_button_select_entry_id or "")
            ):
                self._suppressed_command_button_select_entry_id = None
                return
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
            if isinstance(entry, CommandEntry) and entry.render_kind == "window_toggle":
                entry.window_visible = not entry.window_visible

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
            dismiss_on_focus_lost=True,
            focus_owner_id=listview.control_id,
            on_dismiss=self._on_dismissed,
        )
        focus = getattr(app, "focus", None)
        if focus is not None and hasattr(focus, "set_focus"):
            self._previous_focus = getattr(focus, "focused_node", None)
            focus.set_focus(listview)
        return CommandPaletteHandle(self)

    def hide(self) -> None:
        """Close the palette if open."""
        self._overlays.hide(self._OWNER_ID)
        self._handle = None
        self._open_listview = None
        self._open_rect = None
        self._suppressed_window_select_entry_id = None
        self._suppressed_command_toggle_select_entry_id = None
        self._suppressed_command_button_select_entry_id = None

    def try_activate_action_at(self, pos: tuple) -> bool:
        """Activate a stay-open palette action under *pos* without closing the palette."""
        if not self.is_open or self._open_listview is None:
            return False
        listview = self._open_listview
        if not listview.rect.collidepoint(pos):
            return False
        rel_y = pos[1] - listview.rect.y
        idx = listview._row_at_y(rel_y)
        if idx < 0 or idx >= len(listview._items):
            return False
        item = listview._items[idx]
        entry = item.data
        if not isinstance(entry, CommandEntry):
            return False
        if entry.render_kind == "window_toggle":
            handled = self._activate_window_toggle_at(idx, entry)
        elif entry.render_kind == "command_toggle":
            handled = self._activate_command_toggle_at(idx, entry)
        elif entry.render_kind == "command_button":
            handled = self._activate_command_button_at(idx, entry)
        else:
            handled = False
        if handled:
            listview.selected_index = idx
            listview.scroll_to_item(idx)
        return handled

    def _activate_window_toggle_at(self, idx: int, entry: CommandEntry) -> bool:
        reopen_rect = Rect(self._open_rect) if self._open_rect is not None else None
        reopen_app = self._app
        if callable(self._entry_selected_callback):
            try:
                self._entry_selected_callback(entry)
            except Exception:
                pass
        if callable(entry.action):
            try:
                entry.action()
            except Exception:
                pass
        entry.window_visible = not entry.window_visible
        self._suppressed_window_select_entry_id = str(entry.entry_id)

        if not self.is_open and reopen_app is not None:
            self.show(reopen_app, rect=reopen_rect, selected_entry_id=str(entry.entry_id))

        return True

    def _activate_command_toggle_at(self, idx: int, entry: CommandEntry) -> bool:
        _ = idx
        reopen_rect = Rect(self._open_rect) if self._open_rect is not None else None
        reopen_app = self._app
        if callable(self._entry_selected_callback):
            try:
                self._entry_selected_callback(entry)
            except Exception:
                pass
        if callable(entry.action):
            try:
                entry.action()
            except Exception:
                pass
        if callable(entry.refresh_after_action):
            try:
                entry.refresh_after_action(entry)
            except Exception:
                pass
        else:
            entry.toggle_state = not entry.toggle_state
        self._suppressed_command_toggle_select_entry_id = str(entry.entry_id)

        if not self.is_open and reopen_app is not None:
            self.show(reopen_app, rect=reopen_rect, selected_entry_id=str(entry.entry_id))

        return True

    def _activate_command_button_at(self, idx: int, entry: CommandEntry) -> bool:
        _ = idx
        reopen_rect = Rect(self._open_rect) if self._open_rect is not None else None
        reopen_app = self._app
        if callable(self._entry_selected_callback):
            try:
                self._entry_selected_callback(entry)
            except Exception:
                pass
        if callable(entry.action):
            try:
                entry.action()
            except Exception:
                pass
        self._suppressed_command_button_select_entry_id = str(entry.entry_id)

        if not self.is_open and reopen_app is not None:
            self.show(reopen_app, rect=reopen_rect, selected_entry_id=str(entry.entry_id))

        return True

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

    def _on_dismissed(self) -> None:
        previous_focus = self._previous_focus
        app = self._app
        focus = getattr(app, "focus", None) if app is not None else None
        current_focus = getattr(focus, "focused_node", None) if focus is not None else None
        if focus is not None and hasattr(focus, "set_focus"):
            if current_focus is self._open_listview:
                focus.set_focus(previous_focus)
        self._handle = None
        self._open_listview = None
        self._open_rect = None
        self._previous_focus = None
        self._suppressed_window_select_entry_id = None
        self._suppressed_command_toggle_select_entry_id = None
        self._suppressed_command_button_select_entry_id = None

    def _register_configured_builtin_entries(
        self,
        app: "GuiApplication",
        *,
        on_scene_selected: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.clear()

        grouped_entries: dict[str, list[CommandEntry]] = {
            "scenes": self._collect_builtin_scene_entries(app, on_scene_selected=on_scene_selected)
            if self._include_scene_entries
            else [],
            "windows": self._collect_builtin_window_entries(app)
            if self._include_window_entries
            else [],
            "custom": self._collect_custom_entries(app),
        }
        for group_name in self._group_order:
            for entry in grouped_entries.get(group_name, ()):
                self.register(entry)

    def _collect_builtin_scene_entries(
        self,
        app: "GuiApplication",
        *,
        on_scene_selected: Optional[Callable[[str], None]] = None,
    ) -> list[CommandEntry]:
        entries: list[CommandEntry] = []
        scene_pretty_name_fn = getattr(app, "scene_pretty_name", None)
        for scene_name in self._allowed_builtin_scene_names(app):
            pretty_name = str(scene_name)
            if callable(scene_pretty_name_fn):
                pretty_name = str(scene_pretty_name_fn(scene_name))
            entries.append(
                CommandEntry(
                    entry_id=f"scene:{scene_name}",
                    title=pretty_name,
                    action=lambda target=scene_name: self._select_builtin_scene(app, target, on_scene_selected),
                    category="Scenes",
                )
            )
        return entries

    def _collect_builtin_window_entries(self, app: "GuiApplication") -> list[CommandEntry]:
        entries: list[CommandEntry] = []
        scene_key = self._selection_scene_key(app)
        windows = self._ordered_builtin_windows(app)
        for window in windows:
            control_id = str(getattr(window, "control_id", ""))
            window_title = str(getattr(window, "title", "") or control_id or "Window")
            entries.append(
                CommandEntry(
                    entry_id=f"window:{scene_key}:{control_id}",
                    title=window_title,
                    action=lambda target=window: self._toggle_builtin_window(app, target),
                    category="Windows",
                    render_kind="window_toggle",
                    window_visible=bool(getattr(window, "visible", False)),
                )
            )
        return entries

    def _ordered_builtin_windows(self, app: "GuiApplication") -> list[object]:
        active_scene = self._selection_scene_key(app)
        active_scene_windows = self._active_scene_window_set(app)
        presentation = self._window_presentation
        if presentation is not None and hasattr(presentation, "bindings"):
            bindings = tuple(getattr(presentation, "bindings")() or ())
            sorted_bindings = sorted(
                bindings,
                key=lambda b: (
                    10_000 if getattr(b, "task_panel_slot_index", None) is None else int(getattr(b, "task_panel_slot_index")),
                    str(getattr(b, "key", "")),
                ),
            )
            ordered: list[object] = []
            for binding in sorted_bindings:
                # Skip windows opted out of management
                if not bool(getattr(binding, "window_management_opt_in", True)):
                    continue
                key = str(getattr(binding, "key", ""))
                window = None
                get_window = getattr(presentation, "get_window", None)
                if callable(get_window) and key:
                    window = get_window(key)
                if window is None:
                    continue
                if active_scene_windows is not None and window not in active_scene_windows:
                    continue
                window_scene = str(getattr(window, "scene_name", "") or "")
                if active_scene and window_scene and window_scene != active_scene:
                    continue
                ordered.append(window)
            if ordered:
                return ordered

        windows = []
        scene = getattr(app, "scene", None)
        walk_nodes = getattr(scene, "_walk_nodes", None)
        if callable(walk_nodes):
            for node in walk_nodes():
                is_window = getattr(node, "is_window", None)
                if callable(is_window) and is_window():
                    windows.append(node)
        windows.sort(key=self._window_sort_key)
        return windows

    @staticmethod
    def _active_scene_window_set(app: "GuiApplication") -> Optional[set[object]]:
        scene = getattr(app, "scene", None)
        walk_nodes = getattr(scene, "_walk_nodes", None)
        if not callable(walk_nodes):
            return None
        scene_windows: set[object] = set()
        for node in walk_nodes():
            is_window = getattr(node, "is_window", None)
            if callable(is_window) and is_window():
                scene_windows.add(node)
        return scene_windows

    def _collect_custom_entries(self, app: "GuiApplication") -> list[CommandEntry]:
        provider = self._custom_entries_provider
        if not callable(provider):
            return []
        entries = None
        try:
            entries = provider(app)
        except TypeError:
            entries = provider()
        except Exception:
            return []
        if entries is None:
            return []
        return [entry for entry in tuple(entries) if isinstance(entry, CommandEntry)]

    @staticmethod
    def _entry_is_visible_for_scene(entry: CommandEntry, app: "Optional[GuiApplication]") -> bool:
        entry_scene_name = str(getattr(entry, "scene_name", "") or "")
        if not entry_scene_name:
            return True
        if app is None:
            return False
        return entry_scene_name == str(getattr(app, "active_scene_name", "") or "")

    @staticmethod
    def _normalize_group_order(group_order: Sequence[str]) -> tuple[str, ...]:
        allowed = ("scenes", "windows", "custom")
        remaining = list(allowed)
        normalized: list[str] = []
        for item in tuple(group_order or ()):
            name = str(item).strip().casefold()
            if name in remaining:
                normalized.append(name)
                remaining.remove(name)
        normalized.extend(remaining)
        return tuple(normalized)

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
        # Route through the user's presentation model when one is connected so
        # that task panel toggle buttons and tile_windows stay in sync.
        if self._window_presentation is not None:
            if self._window_presentation.toggle_window(window):
                return
        next_visible = not bool(getattr(window, "visible", False))
        setter = self._resolve_builtin_visibility_setter(app, window)
        if setter is not None:
            setter(next_visible)
            return
        window.visible = next_visible
        tile_windows = getattr(app, "tile_windows", None)
        if callable(tile_windows):
            if next_visible:
                tile_windows(newly_visible=(window,), as_visibility_event=True)
            else:
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

    @staticmethod
    def _window_sort_key(window) -> tuple[str, str]:
        control_id = str(getattr(window, "control_id", "")).strip()
        title = str(getattr(window, "title", "")).strip()
        if control_id:
            return ("0", control_id.casefold())
        if title:
            return ("1", title.casefold())
        return ("2", str(id(window)))

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
    def _selected_index_for_entry_id(entries: List[CommandEntry], entry_id: Optional[str], entry_index_by_id: Optional[Dict[str, int]] = None) -> int:
        if not entry_id:
            return 0 if entries else -1
        if entry_index_by_id is not None:
            index = entry_index_by_id.get(str(entry_id))
            if index is not None:
                return index
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
