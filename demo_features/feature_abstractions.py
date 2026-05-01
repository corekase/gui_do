"""Shared abstractions for demo feature presentation wiring."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from typing import Iterable, Sequence
from pygame import Rect

from gui_do import (
    MenuEntry,
    SceneMenuStripControl,
    WindowControl,
    create_anchored_feature_window,
    resolve_scene_selection_callback,
)


def build_tools_menu_entries(host, *, exclude_labels: Iterable[str] = ()) -> list[MenuEntry]:
    """Build the optional Tools menu entry from the host action registry."""
    action_registry = getattr(host, "action_registry", None)
    if action_registry is None:
        return []
    excluded = {str(label) for label in exclude_labels}
    tools_items = [
        item
        for item in action_registry.context_menu_items(category="Tools")
        if item.label not in excluded
    ]
    if not tools_items:
        return []
    return [MenuEntry("Tools", tools_items)]


def add_standard_scene_menu_strip(
    container,
    host,
    *,
    control_id: str,
    rect,
    scene_name: str,
    scenes_shown: bool = True,
    windows_shown: bool = True,
    tools_exclude_labels: Sequence[str] = (),
    on_window_toggled=None,
):
    """Attach a standardized SceneMenuStripControl with optional Tools menu entries."""
    return container.add(
        SceneMenuStripControl(
            str(control_id),
            rect,
            host.app,
            scene_name=str(scene_name),
            scenes_shown=bool(scenes_shown),
            windows_shown=bool(windows_shown),
            extra_entries_provider=lambda: build_tools_menu_entries(
                host,
                exclude_labels=tools_exclude_labels,
            ),
            on_scene_selected=resolve_scene_selection_callback(host),
            on_window_toggled=on_window_toggled,
        )
    )


def apply_accessibility_sequence(items, tab_index_start: int) -> int:
    """Apply sequential tab order and accessibility metadata to controls."""
    next_index = int(tab_index_start)
    for control, role, label in items:
        if control is None:
            continue
        control.set_tab_index(next_index)
        control.set_accessibility(role=str(role), label=str(label))
        next_index += 1
    return next_index


def register_companion_logic_features(feature_manager, host, providers) -> None:
    """Register companion logic features for a routed/direct feature."""
    for provider in providers:
        feature_manager.register(provider, host)


def ensure_scene_scheduler(feature, host, *, scene_name: str = "main", attr_name: str = "scheduler"):
    """Return and cache a scene scheduler on the feature instance."""
    scheduler = getattr(feature, attr_name, None)
    if scheduler is None:
        scheduler = host.app.get_scene_scheduler(str(scene_name))
        setattr(feature, attr_name, scheduler)
    return scheduler


def sorted_window_bindings(bindings):
    """Return feature-window bindings sorted by declarative slot and key."""
    return tuple(
        sorted(
            tuple(bindings),
            key=lambda b: (
                10_000 if getattr(b, "task_panel_slot_index", None) is None else int(b.task_panel_slot_index),
                str(getattr(b, "key", "")),
            ),
        )
    )


def register_window_tab_builders(tab_manager, feature, host, rect, tab_specs) -> None:
    """Register tab content builders from declarative (tab_key, builder_attr) specs."""
    for tab_key, builder_attr in tab_specs:
        builder = getattr(feature, str(builder_attr), None)
        if not callable(builder):
            raise AttributeError(f"Missing tab builder '{builder_attr}' for tab '{tab_key}'")
        tab_manager.register(str(tab_key), builder(host, Rect(rect)))


def create_presented_anchored_window(
    host,
    *,
    control_id: str,
    title: str,
    size: tuple[int, int],
    anchor: str,
    margin: tuple[int, int],
    presenter,
    window_control_cls=WindowControl,
    use_frame_backdrop: bool = True,
):
    """Create an anchored window and attach a presenter in one call."""
    window = create_anchored_feature_window(
        host,
        window_control_cls=window_control_cls,
        control_id=control_id,
        title=title,
        size=size,
        anchor=anchor,
        margin=margin,
        use_frame_backdrop=bool(use_frame_backdrop),
    )
    window.set_presenter(presenter)
    return window
