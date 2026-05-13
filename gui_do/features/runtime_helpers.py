from __future__ import annotations

from typing import Sequence

from pygame import Rect

from ..text.localization import LocaleRegistry


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


def apply_accessibility_sequence_from_attrs(target, specs: Sequence[object], tab_index_start: int) -> int:
    """Apply sequential accessibility/tab-order metadata using target attribute names."""
    items = [
        (getattr(target, spec.control_attr, None), spec.role, spec.label)
        for spec in specs
    ]
    return apply_accessibility_sequence(items, tab_index_start)


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
    """Queue runtime scenes that opt in so prewarm work runs after entrypoint start."""
    for spec in runtime_scene_specs:
        if not spec.prewarm:
            continue
        queue_scene_prewarm = getattr(app, "queue_scene_prewarm", None)
        if callable(queue_scene_prewarm):
            queue_scene_prewarm(spec.scene_name)
            continue
        app.prewarm_scene(spec.scene_name)
