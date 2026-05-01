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
    ButtonControl,
    LocaleRegistry,
    MenuEntry,
    SceneMenuStripControl,
    ToggleControl,
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


def collect_window_toggle_controls(host, window_presentation):
    """Return sorted (binding, control) pairs for all available window toggles on host."""
    controls = []
    for binding in sorted_window_bindings(window_presentation.bindings()):
        toggle_attr = getattr(binding, "toggle_attr", None)
        if toggle_attr is None:
            continue
        control = getattr(host, str(toggle_attr), None)
        if control is not None:
            controls.append((binding, control))
    return controls


def apply_window_toggle_accessibility(host, window_presentation, *, role: str = "toggle") -> None:
    """Apply accessibility metadata for all window toggle controls declared by bindings."""
    for binding, control in collect_window_toggle_controls(host, window_presentation):
        control.set_accessibility(
            role=str(role),
            label=binding.accessibility_label or binding.action_label or binding.key,
        )


def add_window_toggle_task_panel_controls(host, task_panel, app_layout, window_presentation):
    """Create window toggle controls on the task panel from declarative bindings."""
    toggle_controls = []
    max_slot_index = 0
    for binding in sorted_window_bindings(window_presentation.bindings()):
        slot_index = 1 if binding.task_panel_slot_index is None else int(binding.task_panel_slot_index)
        max_slot_index = max(max_slot_index, slot_index)
        toggle = task_panel.add(
            ToggleControl(
                binding.task_panel_button_id or f"show_{binding.key}",
                app_layout.linear(slot_index),
                binding.task_panel_label or binding.key.title(),
                binding.task_panel_label or binding.key.title(),
                pushed=False,
                on_toggle=lambda pushed, _key=binding.key: window_presentation.set_visible(
                    _key,
                    bool(pushed),
                    from_toggle=True,
                ),
                style=binding.task_panel_style,
            )
        )
        if binding.toggle_attr:
            setattr(host, binding.toggle_attr, toggle)
        toggle_controls.append((binding, toggle))
    return toggle_controls, max_slot_index


def register_window_toggle_tooltips(tooltip_manager, toggle_controls) -> None:
    """Register standardized window toggle tooltip labels."""
    for binding, toggle in toggle_controls:
        label = binding.task_panel_label or binding.action_label or binding.key.title()
        tooltip_manager.register(toggle, f"Toggle the {label} window")


def initialize_locale_registry(tables, *, initial_locale: str) -> LocaleRegistry:
    """Create a LocaleRegistry, register all tables, and select the initial locale."""
    locale_registry = LocaleRegistry()
    for table in tables:
        locale_registry.register(table)
    locale_registry.set_locale(str(initial_locale))
    return locale_registry


def bind_input_map_actions(input_map, bindings, *, mod: int = 0) -> None:
    """Bind multiple (key, action) pairs on an InputMap using a shared modifier."""
    for key, action in bindings:
        input_map.bind(str(action), key=key, mod=int(mod))


def register_descriptors(registry, owner_class, descriptors) -> None:
    """Register a sequence of property descriptors for a given owner class."""
    for descriptor in descriptors:
        registry.register(owner_class, descriptor)


def resolve_canvas_local_point(packet, canvas_rect: Rect):
    """Resolve packet coordinates to canvas-local space, if available."""
    local_pos = getattr(packet, "local_pos", None)
    if local_pos is not None:
        return (float(local_pos[0]), float(local_pos[1]))
    pos = getattr(packet, "pos", None)
    if pos is None:
        return None
    return (float(pos[0] - canvas_rect.left), float(pos[1] - canvas_rect.top))


def apply_runtime_scene_pristine_assets(app, runtime_scene_specs) -> None:
    """Apply configured pristine assets to runtime scenes from declarative specs."""
    for spec in runtime_scene_specs:
        if not spec.pristine_asset:
            continue
        app.set_pristine(spec.pristine_asset, scene_name=spec.scene_name)


def bind_runtime_scene_exit_keys(actions, runtime_scene_specs, *, key, action_name: str = "exit") -> None:
    """Bind a shared exit action key for all runtime scenes that opt in."""
    for spec in runtime_scene_specs:
        if not spec.bind_escape_to_exit:
            continue
        actions.bind_key(key, str(action_name), scene=spec.scene_name)


def prewarm_runtime_scenes(app, runtime_scene_specs) -> None:
    """Prewarm runtime scenes that opt in via declarative scene specs."""
    for spec in runtime_scene_specs:
        if not spec.prewarm:
            continue
        app.prewarm_scene(spec.scene_name)


def add_task_panel_button(task_panel, app_layout, *, control_id: str, slot_index: int, label: str, on_click, style: str = "angle"):
    """Create and add a standard task-panel button positioned by linear slot index."""
    return task_panel.add(
        ButtonControl(
            str(control_id),
            app_layout.linear(int(slot_index)),
            str(label),
            on_click,
            style=str(style),
        )
    )


def register_tooltip_specs(tooltip_manager, specs) -> None:
    """Register a sequence of tooltip specs as (control, message) pairs."""
    for control, message in specs:
        tooltip_manager.register(control, str(message))


def instantiate_features_from_specs(host, feature_specs) -> None:
    """Instantiate feature objects from specs and attach them to host attributes."""
    for spec in feature_specs:
        setattr(host, spec.attr_name, spec.factory())


def register_features_from_specs(app, host, feature_specs) -> None:
    """Register instantiated host feature attributes to the application."""
    for spec in feature_specs:
        feature = getattr(host, spec.attr_name)
        app.register_feature(feature, host=host)


def register_window_presentation_specs(window_presentation, window_specs) -> None:
    """Register feature-window presentation bindings from declarative window specs."""
    for spec in window_specs:
        window_presentation.register_feature_window(
            spec.key,
            feature_attr=spec.feature_attr,
            toggle_attr=spec.toggle_attr,
            action_name=spec.action_name,
            action_label=spec.action_label,
            task_panel_button_id=spec.task_panel_button_id,
            task_panel_label=spec.task_panel_label,
            task_panel_style=spec.task_panel_style,
            task_panel_slot_index=spec.task_panel_slot_index,
            tab_before_showcase=spec.tab_before_showcase,
            accessibility_label=spec.accessibility_label,
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
