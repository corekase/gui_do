"""SceneMenuStripControl — reusable top menu strip with dynamic scene/window entries."""
from __future__ import annotations

from collections import Counter
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from .menu_bar_control import MenuBarControl as _BaseMenuBarControl, MenuEntry
from ...events.gui_event import EventType
from ...overlays.context_menu_manager import ContextMenuItem

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ..base.ui_node import UiNode


class SceneMenuStripControl(_BaseMenuBarControl):
    """Dynamic menu strip with optional Scenes/Windows sections.

    The control rebuilds its entries before pointer interactions so scene lists
    and window visibility toggles always reflect current runtime state.

    Optional built-in sections:
    - Scenes: all registered scene names
    - Windows: visibility toggles for window controls in the target scene

    Additional sections can be injected through ``extra_entries_provider``.
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        app: "GuiApplication",
        *,
        scene_name: Optional[str] = None,
        scenes_shown: bool = False,
        windows_shown: bool = False,
        file_items_provider: Optional[Callable[[], List[ContextMenuItem]]] = None,
        scene_items_provider: Optional[Callable[[], List[ContextMenuItem]]] = None,
        window_items_provider: Optional[Callable[[], List[ContextMenuItem]]] = None,
        extra_entries_provider: Optional[Callable[[], List[MenuEntry]]] = None,
        on_exit: Optional[Callable[[], None]] = None,
        on_scene_selected: Optional[Callable[[str], None]] = None,
        on_window_toggled: Optional[Callable[["UiNode", bool], None]] = None,
    ) -> None:
        super().__init__(control_id, rect, entries=[])
        self._app = app
        self._scene_name = scene_name
        self._scenes_shown = bool(scenes_shown)
        self._windows_shown = bool(windows_shown)
        self._file_items_provider = file_items_provider
        self._scene_items_provider = scene_items_provider
        self._window_items_provider = window_items_provider
        self._extra_entries_provider = extra_entries_provider
        self._on_exit = on_exit
        self._on_scene_selected = on_scene_selected
        self._on_window_toggled = on_window_toggled
        self._dynamic_flyout_min_width_by_label: Dict[str, int] = {}
        # Preserve a stable menu order for windows even if scene walk order changes.
        self._window_order_rank_by_scene: Dict[str, Dict[str, int]] = {}
        self._window_order_next_by_scene: Dict[str, int] = {}
        self.refresh_entries()

    def refresh_entries(self) -> None:
        entries: List[MenuEntry] = []
        if self._scenes_shown:
            scene_items = self._build_scene_items()
            if scene_items:
                entries.append(
                    MenuEntry(
                        "Scenes",
                        scene_items,
                        flyout_min_width=self._dynamic_flyout_min_width_by_label.get("Scenes"),
                    )
                )
        if self._windows_shown:
            window_items = self._build_window_items()
            if window_items:
                entries.append(
                    MenuEntry(
                        "Windows",
                        window_items,
                        flyout_min_width=self._dynamic_flyout_min_width_by_label.get("Windows"),
                    )
                )
        file_items = self._build_file_items()
        if file_items:
            entries.append(MenuEntry("File", file_items))
        if self._extra_entries_provider is not None:
            try:
                extras = self._extra_entries_provider() or []
            except Exception:
                extras = []
            entries.extend(extras)
        self._set_entries_preserving_state(entries)

    def _set_entries_preserving_state(self, entries: List[MenuEntry]) -> None:
        """Update menu entries without clearing open/highlight selection state."""
        old_open_label = None
        old_hover_label = None
        if 0 <= self._open_index < len(self._entries):
            old_open_label = self._entries[self._open_index].label
        if 0 <= self._hovered_index < len(self._entries):
            old_hover_label = self._entries[self._hovered_index].label

        self._entries = list(entries)

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

    def handle_event(self, event, app: "GuiApplication", theme=None) -> bool:
        # Keep dynamic menu content current before pointer-driven interactions.
        if getattr(event, "kind", None) in (EventType.MOUSE_MOTION, EventType.MOUSE_BUTTON_DOWN):
            self.refresh_entries()
        # Always propagate theme to parent
        return super().handle_event(event, app, theme=theme)

    # ------------------------------------------------------------------
    # Default section builders
    # ------------------------------------------------------------------

    def _build_file_items(self) -> List[ContextMenuItem]:
        if self._file_items_provider is None:
            return []
        try:
            return self._file_items_provider() or []
        except Exception:
            return []

    def _build_scene_items(self) -> List[ContextMenuItem]:
        if self._scene_items_provider is not None:
            try:
                provider_items = self._scene_items_provider() or []
            except Exception:
                provider_items = []
            self._set_dynamic_flyout_min_width("Scenes", provider_items)
            return provider_items

        active = str(getattr(self._app, "active_scene_name", ""))
        scene_pretty_name_fn = getattr(self._app, "scene_pretty_name", None)
        items: List[ContextMenuItem] = []
        for scene in self._allowed_scene_names():
            pretty = str(scene)
            if callable(scene_pretty_name_fn):
                pretty = str(scene_pretty_name_fn(scene))
            label = f"* {pretty}" if scene == active else pretty
            items.append(
                ContextMenuItem(label, action=lambda selected=scene: self._select_scene(selected))
            )
        self._set_dynamic_flyout_min_width("Scenes", items)
        return items

    def _allowed_scene_names(self) -> List[str]:
        scene_names_fn = getattr(self._app, "scene_names", None)
        if not callable(scene_names_fn):
            return []
        names = [str(name) for name in scene_names_fn()]
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
            self._set_dynamic_flyout_min_width("Windows", provider_items)
            return provider_items

        scene = self._resolve_scene()
        if scene is None:
            self._set_dynamic_flyout_min_width("Windows", [])
            return []
        windows: List[UiNode] = [node for node in scene._walk_nodes() if node.is_window()]  # noqa: SLF001
        scene_order_key = self._window_scene_order_key(scene)
        windows.sort(key=lambda window: self._window_order_rank(scene_order_key, window))
        items: List[ContextMenuItem] = []
        for window in windows:
            if not self._is_window_allowed_for_dynamic_menu(window):
                continue
            window_name = str(getattr(window, "title", "") or window.control_id)
            prefix = "[x]" if bool(window.visible) else "[ ]"
            items.append(
                ContextMenuItem(
                    f"{prefix} {window_name}",
                    action=lambda target=window: self._toggle_window(target),
                )
            )
        self._set_dynamic_flyout_min_width("Windows", items)
        return items

    def _is_window_allowed_for_dynamic_menu(self, window: "UiNode") -> bool:
        return window is not None

    def _measure_item_label_width(self, label: str) -> int:
        text = str(label)
        try:
            font = pygame.font.SysFont(None, 17)
            text_w = font.size(text)[0]
        except Exception:
            text_w = len(text) * 8
        # Keep sizing aligned with menu overlay internals: text padding + icon/check space.
        return int(text_w) + 40

    def _set_dynamic_flyout_min_width(self, menu_label: str, items: List[ContextMenuItem]) -> None:
        longest = 0
        for item in items:
            if bool(getattr(item, "separator", False)):
                continue
            longest = max(longest, self._measure_item_label_width(getattr(item, "label", "")))
        if longest > 0:
            self._dynamic_flyout_min_width_by_label[str(menu_label)] = longest
            return
        self._dynamic_flyout_min_width_by_label.pop(str(menu_label), None)

    def _window_scene_order_key(self, scene) -> str:
        if self._scene_name:
            return str(self._scene_name)
        active_scene_name = str(getattr(self._app, "active_scene_name", "")).strip()
        if active_scene_name:
            return active_scene_name
        scene_name = str(getattr(scene, "name", "")).strip()
        if scene_name:
            return scene_name
        return f"scene:{id(scene)}"

    @staticmethod
    def _window_order_key(window: "UiNode") -> str:
        control_id = str(getattr(window, "control_id", "")).strip()
        if control_id:
            return control_id
        title = str(getattr(window, "title", "")).strip()
        if title:
            return f"title:{title}"
        return f"window:{id(window)}"

    def _window_order_rank(self, scene_order_key: str, window: "UiNode") -> int:
        ranks = self._window_order_rank_by_scene.setdefault(scene_order_key, {})
        key = self._window_order_key(window)
        existing = ranks.get(key)
        if existing is not None:
            return existing
        next_rank = self._window_order_next_by_scene.get(scene_order_key, 0)
        ranks[key] = next_rank
        self._window_order_next_by_scene[scene_order_key] = next_rank + 1
        return next_rank

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _exit(self) -> None:
        if self._on_exit is not None:
            self._on_exit()
            return
        self._app.running = False

    def _select_scene(self, scene_name: str) -> None:
        if self._on_scene_selected is not None:
            self._on_scene_selected(scene_name)
            return
        switch_scene = getattr(self._app, "switch_scene", None)
        if callable(switch_scene):
            switch_scene(scene_name)

    def _toggle_window(self, window: "UiNode") -> None:
        next_visible = not bool(window.visible)
        window.visible = next_visible
        if self._on_window_toggled is not None:
            self._on_window_toggled(window, next_visible)
            return
        setter = self._resolve_builtin_visibility_setter(window)
        if setter is not None:
            setter(bool(next_visible))
            return
        tile_windows = getattr(self._app, "tile_windows", None)
        if callable(tile_windows):
            tile_windows()

    def _resolve_builtin_visibility_setter(self, window: "UiNode"):
        """Resolve a built-in visibility setter for a dynamic window entry."""
        control_id = str(getattr(window, "control_id", "")).strip()
        if not control_id.endswith("_window"):
            return None
        window_key = control_id[: -len("_window")]
        if not window_key:
            return None
        method_name = f"set_{window_key}_window_visible"

        app_method = getattr(self._app, method_name, None)
        if callable(app_method):
            return app_method

        features = getattr(self._app, "features", None)
        feature_hosts = getattr(features, "_feature_hosts", None)
        if isinstance(feature_hosts, dict):
            for host in feature_hosts.values():
                host_method = getattr(host, method_name, None)
                if callable(host_method):
                    return host_method
        return None

    def _resolve_scene(self):
        current_scene = getattr(self._app, "scene", None)
        active_scene_name = getattr(self._app, "active_scene_name", None)
        if self._scene_name is None or active_scene_name == self._scene_name:
            return current_scene
        has_scene = getattr(self._app, "has_scene", None)
        create_scene = getattr(self._app, "create_scene", None)
        if callable(has_scene) and callable(create_scene) and has_scene(self._scene_name):
            return create_scene(self._scene_name)
        return None
