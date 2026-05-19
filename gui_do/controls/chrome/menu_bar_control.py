"""Menu strip control with static and dynamic scene/window menu sections."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Sequence, Tuple

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ...overlays.context_menu_manager import ContextMenuItem
from ...overlays.menu_overlay_panel_base import _MenuOverlayPanelBase
from ..base.ui_node import UiNode

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_ENTRY_PADDING_X = 12


@dataclass
class MenuEntry:
    """One top-level menu in the menu strip (for example File/Edit/View)."""

    label: str
    items: List[ContextMenuItem] = field(default_factory=list)
    enabled: bool = True
    flyout_min_width: Optional[int] = None


@dataclass(frozen=True)
class SceneMenuOptions:
    """Configuration for automatic Scene menu population."""

    label: str = "Scene"
    insert_index: int = 0
    mode: str = "add_all"  # add_all | opt_in
    opt_in_scene_names: Sequence[str] = field(default_factory=tuple)
    include_current_scene: bool = False
    shown: bool = True


@dataclass(frozen=True)
class WindowMenuOptions:
    """Configuration for automatic Window menu population."""

    label: str = "Window"
    insert_index: int = 1
    shown: bool = True


class _FlyoutPanel(_MenuOverlayPanelBase):
    """Internal overlay panel rendering one flyout sub-menu."""

    _ITEM_H = 26
    _SEP_H = 8
    _PAD = 4
    _TEXT_PAD = 12
    _MIN_W = 140
    _FONT_SIZE = 17

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
        theme=None,
        min_width: Optional[int] = None,
    ) -> Tuple[int, int]:
        resolved_min_width = cls._MIN_W if min_width is None else max(1, int(min_width))
        return _MenuOverlayPanelBase.measure(
            items,
            item_height=cls._ITEM_H,
            separator_height=cls._SEP_H,
            padding=cls._PAD,
            text_padding=cls._TEXT_PAD,
            min_width=resolved_min_width,
            font_size=cls._FONT_SIZE,
            theme=theme,
        )


class MenuStripControl(UiNode):
    """Unified menu strip for static entries and dynamic Scene/Window menus."""

    _FONT_SCALE: float = 1.0625

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        entries: Optional[List[MenuEntry]] = None,
        *,
        app: Optional["GuiApplication"] = None,
        scene_name: Optional[str] = None,
        scene_menu: Optional[SceneMenuOptions] = None,
        window_menu: Optional[WindowMenuOptions] = None,
        scene_items_provider: Optional[Callable[[], List[ContextMenuItem]]] = None,
        window_items_provider: Optional[Callable[[], List[ContextMenuItem]]] = None,
        on_scene_selected: Optional[Callable[[str], None]] = None,
        on_window_toggled: Optional[Callable[[UiNode, bool], None]] = None,
        window_presentation: Optional[object] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._app = app
        self._scene_name = scene_name
        self._scene_menu = scene_menu if scene_menu is not None else SceneMenuOptions(shown=False)
        self._window_menu = window_menu if window_menu is not None else WindowMenuOptions(shown=False)
        self._scene_items_provider = scene_items_provider
        self._window_items_provider = window_items_provider
        self._on_scene_selected = on_scene_selected
        self._on_window_toggled = on_window_toggled
        self._window_presentation = window_presentation

        self._base_entries: List[MenuEntry] = list(entries) if entries else []
        self._entries: List[MenuEntry] = []
        self._open_index: int = -1
        self._hovered_index: int = -1
        self._open_flyout_rect: Optional[Rect] = None
        self._last_app: Optional["GuiApplication"] = None
        self.tab_index = 0
        self._draw_font_role: str = "menu_bar.entry"
        self._entry_rects_cache_key: Optional[tuple] = None
        self._entry_rects_cache: List[Rect] = []
        self._dynamic_flyout_min_width_by_label: Dict[str, int] = {}
        self._window_order_rank_by_scene: Dict[str, Dict[str, int]] = {}
        self._window_order_next_by_scene: Dict[str, int] = {}
        self.refresh_entries()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_entries(self, entries: List[MenuEntry]) -> None:
        self._base_entries = list(entries)
        self.refresh_entries()

    def append_entry(self, entry: MenuEntry) -> None:
        self._base_entries.append(entry)
        self.refresh_entries()

    def insert_entry(self, index: int, entry: MenuEntry) -> None:
        target = max(0, min(int(index), len(self._base_entries)))
        self._base_entries.insert(target, entry)
        self.refresh_entries()

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

    def refresh_entries(self) -> None:
        merged_entries: List[MenuEntry] = list(self._base_entries)
        dynamic_insertions: List[Tuple[int, MenuEntry]] = []

        if self._scene_menu.shown:
            scene_items = self._build_scene_items()
            dynamic_insertions.append(
                (
                    int(self._scene_menu.insert_index),
                    MenuEntry(
                        str(self._scene_menu.label),
                        scene_items,
                        enabled=True,
                        flyout_min_width=self._dynamic_flyout_min_width_by_label.get(str(self._scene_menu.label)),
                    ),
                )
            )

        if self._window_menu.shown:
            window_items = self._build_window_items()
            dynamic_insertions.append(
                (
                    int(self._window_menu.insert_index),
                    MenuEntry(
                        str(self._window_menu.label),
                        window_items,
                        enabled=True,
                        flyout_min_width=self._dynamic_flyout_min_width_by_label.get(str(self._window_menu.label)),
                    ),
                )
            )

        for offset, (insert_index, entry) in enumerate(sorted(dynamic_insertions, key=lambda item: item[0])):
            target = max(0, min(int(insert_index) + offset, len(merged_entries)))
            merged_entries.insert(target, entry)

        self._set_entries_preserving_state(merged_entries)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _entry_rects(self, theme) -> List[Rect]:
        if theme is None or not hasattr(theme, "fonts") or theme.fonts is None:
            raise RuntimeError("MenuStripControl requires a non-None theme with a valid 'fonts' attribute.")
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
            raise RuntimeError("MenuStripControl.handle_event requires a non-None theme with a valid 'fonts' attribute.")

        self._last_app = app
        if getattr(event, "kind", None) in (EventType.MOUSE_MOTION, EventType.MOUSE_BUTTON_DOWN, EventType.KEY_DOWN):
            self.refresh_entries()
        er = self._entry_rects(theme)

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered_index = -1
            for i, r in enumerate(er):
                if r.collidepoint(event.pos):
                    self._hovered_index = i
                    break
            if self._hovered_index >= 0 and self._open_index < 0:
                if self._entries[self._hovered_index].enabled and self._entries[self._hovered_index].items:
                    self._open_flyout(self._hovered_index, app, er)
            self._sync_open_menu_with_highlight(app, er)
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

    def update(self, dt_seconds: float) -> None:
        super().update(dt_seconds)
        self._refresh_open_flyout_if_needed()

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
        pygame.draw.line(surface, border_col, (self.rect.left, self.rect.bottom - 1), (self.rect.right, self.rect.bottom - 1))

        er = self._entry_rects(theme)
        if self._last_app is not None and hasattr(self._last_app, "logical_pointer_pos"):
            pointer_pos = self._last_app.logical_pointer_pos
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
                txt = font.render(entry.label, True, col)
                surface.blit(txt, (r.x + _ENTRY_PADDING_X, r.y + (r.height - txt.get_height()) // 2))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _set_entries_preserving_state(self, entries: List[MenuEntry]) -> None:
        old_open_label = None
        old_hover_label = None
        if 0 <= self._open_index < len(self._entries):
            old_open_label = self._entries[self._open_index].label
        if 0 <= self._hovered_index < len(self._entries):
            old_hover_label = self._entries[self._hovered_index].label

        self._entries = list(entries)
        self._entry_rects_cache_key = None
        self._entry_rects_cache = []

        def _index_for_label(label: Optional[str]) -> int:
            if label is None:
                return -1
            for i, entry in enumerate(self._entries):
                if entry.label == label:
                    return i
            return -1

        self._open_index = _index_for_label(old_open_label)
        self._hovered_index = _index_for_label(old_hover_label)
        self.invalidate()

    @staticmethod
    def _entry_state_signature(entry: MenuEntry) -> tuple:
        items = []
        for item in entry.items:
            items.append(
                (
                    str(getattr(item, "label", "")),
                    bool(getattr(item, "enabled", True)),
                    bool(getattr(item, "separator", False)),
                    bool(getattr(item, "_menu_window_checkbox", False)),
                    bool(getattr(item, "_menu_window_visible", False)),
                )
            )
        return (str(entry.label), bool(entry.enabled), tuple(items), entry.flyout_min_width)

    def _refresh_open_flyout_if_needed(self) -> None:
        app = self._last_app if self._last_app is not None else self._app
        if app is None or self._open_index < 0:
            return

        old_index = int(self._open_index)
        old_label = None
        old_signature = None
        if 0 <= old_index < len(self._entries):
            old_entry = self._entries[old_index]
            old_label = str(old_entry.label)
            old_signature = self._entry_state_signature(old_entry)

        self.refresh_entries()

        if self._open_index < 0:
            if old_label is not None:
                app.overlay.hide(f"_menubar_{self.control_id}_{old_index}")
            return

        if not (0 <= self._open_index < len(self._entries)):
            return

        refreshed_entry = self._entries[self._open_index]
        refreshed_signature = self._entry_state_signature(refreshed_entry)
        if refreshed_signature == old_signature:
            return

        theme = getattr(app, "theme", None)
        if theme is None or getattr(theme, "fonts", None) is None:
            return
        target_index = int(self._open_index)
        er = self._entry_rects(theme)
        self._dismiss_flyout(app)
        self._open_flyout(target_index, app, er)

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
        w, h = _FlyoutPanel.measure(entry.items, theme=getattr(app, "theme", None), min_width=entry.flyout_min_width)
        # Ensure each dropdown is never narrower than its top-level menu entry.
        if w < er_rect.width:
            w = int(er_rect.width)
        screen = app.surface.get_rect()
        fx = er_rect.x
        fy = er_rect.bottom
        if fx + w > screen.right:
            fx = screen.right - w
        if fy + h > screen.bottom:
            fy = er_rect.y - h

        panel = _FlyoutPanel(owner, Rect(fx, fy, w, h), entry.items, on_close=lambda: self._dismiss_flyout(app))
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

    def _build_scene_items(self) -> List[ContextMenuItem]:
        if self._scene_items_provider is not None:
            try:
                provider_items = self._scene_items_provider() or []
            except Exception:
                provider_items = []
            for item in provider_items:
                setattr(item, "_menu_scene_compact", True)
            self._set_auto_scene_menu_flyout_min_width(self._scene_menu.label, provider_items, theme=getattr(self._app, "theme", None))
            return provider_items

        if self._app is None:
            self._set_auto_scene_menu_flyout_min_width(self._scene_menu.label, [])
            return []

        active = str(getattr(self._app, "active_scene_name", ""))
        scene_pretty_name_fn = getattr(self._app, "scene_pretty_name", None)
        items: List[ContextMenuItem] = []
        for scene in self._allowed_scene_names():
            if scene == active and not bool(self._scene_menu.include_current_scene):
                continue
            pretty = str(scene)
            if callable(scene_pretty_name_fn):
                pretty = str(scene_pretty_name_fn(scene))
            item = ContextMenuItem(pretty, action=lambda selected=scene: self._select_scene(selected))
            setattr(item, "_menu_scene_compact", True)
            items.append(item)
        self._set_auto_scene_menu_flyout_min_width(self._scene_menu.label, items, theme=getattr(self._app, "theme", None))
        return items

    def _set_auto_scene_menu_flyout_min_width(self, menu_label: str, items: List[ContextMenuItem], theme=None) -> None:
        longest = 0
        font = None
        if theme is not None and getattr(theme, "fonts", None) is not None:
            try:
                font = theme.fonts.font_instance("title", size=_FlyoutPanel._FONT_SIZE)
            except Exception:
                font = None
        for item in items:
            if bool(getattr(item, "separator", False)):
                continue
            text = str(getattr(item, "label", ""))
            try:
                if font is None:
                    font = pygame.font.SysFont(None, int(_FlyoutPanel._FONT_SIZE))
                text_w = font.text_size(text)[0] if hasattr(font, "text_size") else font.size(text)[0]
            except Exception:
                text_w = len(text) * 8
            # 5px inset + longest entry text width + 5px end gutter.
            entry_width = 5 + int(text_w) + 5
            longest = max(longest, entry_width)
        if longest > 0:
            self._dynamic_flyout_min_width_by_label[str(menu_label)] = int(longest)
            return
        self._dynamic_flyout_min_width_by_label.pop(str(menu_label), None)

    def _allowed_scene_names(self) -> List[str]:
        if self._app is None:
            return []
        scene_names_fn = getattr(self._app, "scene_names", None)
        if not callable(scene_names_fn):
            return []
        names = [str(name) for name in scene_names_fn()]

        mode = str(self._scene_menu.mode).strip().lower()
        if mode == "opt_in":
            allowed_opt_in = {str(name) for name in self._scene_menu.opt_in_scene_names}
            return [name for name in names if name in allowed_opt_in]

        features = getattr(self._app, "features", None)
        feature_map = getattr(features, "_features", None)
        active = str(getattr(self._app, "active_scene_name", ""))
        if not hasattr(feature_map, "values"):
            return [name for name in names if name != "default"]

        scene_counts: Counter[str] = Counter()
        for feature in feature_map.values():
            scene_name = getattr(feature, "scene_name", None)
            if isinstance(scene_name, str) and scene_name:
                scene_counts[scene_name] += 1

        allowed: List[str] = []
        for name in names:
            if name == "default" and scene_counts.get("default", 0) <= 0:
                continue
            if scene_counts and scene_counts.get(name, 0) <= 0 and name != active:
                continue
            allowed.append(name)
        return allowed

    def _build_window_items(self) -> List[ContextMenuItem]:
        if self._window_items_provider is not None:
            try:
                provider_items = self._window_items_provider() or []
            except Exception:
                provider_items = []
            self._set_dynamic_flyout_min_width(self._window_menu.label, provider_items, theme=getattr(self._app, "theme", None))
            return provider_items

        scene = self._resolve_scene()
        if scene is None:
            self._set_dynamic_flyout_min_width(self._window_menu.label, [])
            return []

        # Get all windows from the scene
        windows: List[UiNode] = [node for node in scene._walk_nodes() if node.is_window()]  # noqa: SLF001

        # Filter by opt-in flag if presentation model is available; otherwise include all
        if self._window_presentation is not None and hasattr(self._window_presentation, "bindings"):
            bindings = getattr(self._window_presentation, "bindings")() or ()
            opted_in_bindings = {
                str(getattr(b, "key", "")): b
                for b in bindings
                if bool(getattr(b, "window_management_opt_in", True))
            }
            # Map windows to their binding keys via the presentation model
            windows_by_key = {}
            for binding_key, binding in opted_in_bindings.items():
                get_window = getattr(self._window_presentation, "get_window", None)
                if callable(get_window):
                    window = get_window(binding_key)
                    if window is not None:
                        windows_by_key[id(window)] = window
            # Only include windows that are in the opted-in set
            windows = [w for w in windows if id(w) in windows_by_key]

        scene_order_key = self._window_scene_order_key(scene)
        windows.sort(key=lambda window: self._window_order_rank(scene_order_key, window))
        items: List[ContextMenuItem] = []
        for window in windows:
            window_name = str(getattr(window, "title", "") or window.control_id)
            item = ContextMenuItem(window_name, action=lambda target=window: self._toggle_window(target))
            # Tag auto-generated window items so flyout drawing can render checkbox glyphs.
            setattr(item, "_menu_window_checkbox", True)
            setattr(item, "_menu_window_visible", bool(window.visible))
            items.append(item)
        self._set_auto_window_menu_flyout_min_width(self._window_menu.label, items, theme=getattr(self._app, "theme", None))
        return items

    def _set_auto_window_menu_flyout_min_width(self, menu_label: str, items: List[ContextMenuItem], theme=None) -> None:
        longest = 0
        line_height = int(_FlyoutPanel._ITEM_H)
        checkbox_size = max(1, line_height - 4)
        font = None
        if theme is not None and getattr(theme, "fonts", None) is not None:
            try:
                font = theme.fonts.font_instance("title", size=_FlyoutPanel._FONT_SIZE)
            except Exception:
                font = None
        for item in items:
            if bool(getattr(item, "separator", False)):
                continue
            text = str(getattr(item, "label", ""))
            try:
                if font is None:
                    font = pygame.font.SysFont(None, int(_FlyoutPanel._FONT_SIZE))
                text_w = font.text_size(text)[0] if hasattr(font, "text_size") else font.size(text)[0]
            except Exception:
                text_w = len(text) * 8
            entry_width = 3 + checkbox_size + 3 + int(text_w) + 3 + 5
            longest = max(longest, entry_width)
        if longest > 0:
            self._dynamic_flyout_min_width_by_label[str(menu_label)] = int(longest)
            return
        self._dynamic_flyout_min_width_by_label.pop(str(menu_label), None)

    def _measure_item_label_width(self, label: str, theme=None) -> int:
        text = str(label)
        try:
            font = None
            if theme is not None and getattr(theme, "fonts", None) is not None:
                font = theme.fonts.font_instance("title", size=17)
            if font is None:
                font = pygame.font.SysFont(None, 17)
            text_w = font.text_size(text)[0] if hasattr(font, "text_size") else font.size(text)[0]
        except Exception:
            text_w = len(text) * 8
        return int(text_w) + 40

    def _set_dynamic_flyout_min_width(self, menu_label: str, items: List[ContextMenuItem], theme=None) -> None:
        longest = 0
        for item in items:
            if bool(getattr(item, "separator", False)):
                continue
            longest = max(longest, self._measure_item_label_width(getattr(item, "label", ""), theme=theme))
        if longest > 0:
            self._dynamic_flyout_min_width_by_label[str(menu_label)] = longest
            return
        self._dynamic_flyout_min_width_by_label.pop(str(menu_label), None)

    def _window_scene_order_key(self, scene) -> str:
        if self._scene_name:
            return str(self._scene_name)
        if self._app is not None:
            active_scene_name = str(getattr(self._app, "active_scene_name", "")).strip()
            if active_scene_name:
                return active_scene_name
        scene_name = str(getattr(scene, "name", "")).strip()
        if scene_name:
            return scene_name
        return f"scene:{id(scene)}"

    @staticmethod
    def _window_order_key(window: UiNode) -> str:
        control_id = str(getattr(window, "control_id", "")).strip()
        if control_id:
            return control_id
        title = str(getattr(window, "title", "")).strip()
        if title:
            return f"title:{title}"
        return f"window:{id(window)}"

    def _window_order_rank(self, scene_order_key: str, window: UiNode) -> int:
        ranks = self._window_order_rank_by_scene.setdefault(scene_order_key, {})
        key = self._window_order_key(window)
        existing = ranks.get(key)
        if existing is not None:
            return existing
        next_rank = self._window_order_next_by_scene.get(scene_order_key, 0)
        ranks[key] = next_rank
        self._window_order_next_by_scene[scene_order_key] = next_rank + 1
        return next_rank

    def _select_scene(self, scene_name: str) -> None:
        if self._app is None:
            return
        active_scene = str(getattr(self._app, "active_scene_name", ""))
        if str(scene_name) == active_scene:
            return
        if self._on_scene_selected is not None:
            self._on_scene_selected(scene_name)
            return
        switch_scene = getattr(self._app, "switch_scene", None)
        if callable(switch_scene):
            switch_scene(scene_name)

    def _toggle_window(self, window: UiNode) -> None:
        next_visible = not bool(window.visible)
        window.visible = next_visible
        if self._on_window_toggled is not None:
            self._on_window_toggled(window, next_visible)
            return
        if self._app is not None:
            tile_windows = getattr(self._app, "tile_windows", None)
            if callable(tile_windows):
                if next_visible:
                    tile_windows(newly_visible=(window,), as_visibility_event=True)
                else:
                    tile_windows()

    def _resolve_scene(self):
        if self._app is None:
            return None
        current_scene = getattr(self._app, "scene", None)
        active_scene_name = getattr(self._app, "active_scene_name", None)
        if self._scene_name is None or active_scene_name == self._scene_name:
            return current_scene
        has_scene = getattr(self._app, "has_scene", None)
        create_scene = getattr(self._app, "create_scene", None)
        if callable(has_scene) and callable(create_scene) and has_scene(self._scene_name):
            return create_scene(self._scene_name)
        return None


__all__ = [
    "MenuEntry",
    "SceneMenuOptions",
    "WindowMenuOptions",
    "MenuStripControl",
    "_FlyoutPanel",
]
