from __future__ import annotations


def build_feature_specs(entries, *, feature_spec_cls):
    """Build FeatureSpec-like values from shorthand tuples or instances."""
    specs = []
    for entry in entries:
        if isinstance(entry, feature_spec_cls):
            specs.append(entry)
            continue
        attr_name, factory = entry
        specs.append(feature_spec_cls(attr_name=str(attr_name), factory=factory))
    return tuple(specs)


def build_feature_window_bundle_specs(
    entries,
    *,
    feature_spec_cls,
    window_spec_cls,
    make_window_toggle_spec_fn,
):
    """Build parallel (FeatureSpec-like, WindowSpec-like) tuples from bundle entries."""
    feature_specs = []
    window_specs = []
    for entry in entries:
        if isinstance(entry, feature_spec_cls):
            feature_specs.append(entry)
            continue
        if isinstance(entry, window_spec_cls):
            window_specs.append(entry)
            continue
        feature_specs.append(feature_spec_cls(attr_name=str(entry.feature_attribute_name), factory=entry.factory))
        window_specs.append(
            make_window_toggle_spec_fn(
                entry.window_key,
                entry.feature_attribute_name,
                task_panel_slot_index=entry.task_panel_slot_index,
                task_panel_label=entry.task_panel_label,
                task_panel_style=entry.task_panel_style,
                action_label=entry.action_label,
                action_name=entry.action_name,
                task_panel_toggle_button_id=entry.task_panel_toggle_button_id,
                toggle_attribute_name=entry.toggle_attribute_name,
                accessibility_label=entry.accessibility_label,
                wobbly_windows=(
                    entry.wobble_params.get("wobbly_windows", True)
                    if getattr(entry, "wobble_params", None)
                    else True
                ),
                wobble_params=getattr(entry, "wobble_params", {}) or {},
            )
        )
    return tuple(feature_specs), tuple(window_specs)


def build_window_toggle_specs(bindings, *, window_spec_cls, make_window_toggle_spec_fn):
    """Build WindowSpec-like values from binding entries."""
    specs = []
    for binding in bindings:
        if isinstance(binding, window_spec_cls):
            specs.append(binding)
            continue
        specs.append(
            make_window_toggle_spec_fn(
                binding.key,
                binding.feature_attribute_name,
                task_panel_slot_index=binding.task_panel_slot_index,
                task_panel_label=binding.task_panel_label,
                task_panel_style=binding.task_panel_style,
                action_label=binding.action_label,
                action_name=binding.action_name,
                task_panel_toggle_button_id=binding.task_panel_toggle_button_id,
                toggle_attribute_name=binding.toggle_attribute_name,
                accessibility_label=binding.accessibility_label,
            )
        )
    return tuple(specs)


def build_scene_nav_actions(nav_entries, *, action_spec_cls, make_scene_nav_action_fn, category: str = "Scenes"):
    """Build scene-navigation ActionSpec-like values from shorthand tuples."""
    specs = []
    for entry in nav_entries:
        if isinstance(entry, action_spec_cls):
            specs.append(entry)
            continue
        action_id, label, target_scene = entry
        specs.append(
            make_scene_nav_action_fn(
                str(action_id),
                label=str(label),
                target_scene=str(target_scene),
                category=str(category),
            )
        )
    return tuple(specs)


def build_action_specs(
    entries,
    *,
    action_spec_cls,
    make_exit_action_fn,
    make_scene_nav_action_fn,
    make_palette_open_action_fn,
):
    """Build ActionSpec-like values from action-binding entries."""
    specs = []
    for entry in entries:
        if isinstance(entry, action_spec_cls):
            specs.append(entry)
            continue
        kind = str(entry.kind)
        if kind == "exit":
            specs.append(
                make_exit_action_fn(
                    action_id=str(entry.action_id),
                    label=str(entry.label),
                    category="File" if entry.category is None else str(entry.category),
                )
            )
            continue
        if kind == "scene_nav":
            if entry.target is None:
                raise ValueError("scene_nav action bindings require target")
            specs.append(
                make_scene_nav_action_fn(
                    str(entry.action_id),
                    label=str(entry.label),
                    target_scene=str(entry.target),
                    category="Scenes" if entry.category is None else str(entry.category),
                )
            )
            continue
        if kind == "palette_open":
            specs.append(
                make_palette_open_action_fn(
                    action_id=str(entry.action_id),
                    label=str(entry.label),
                    key=entry.key,
                )
            )
            continue
        raise ValueError(f"Unsupported action binding kind: {kind!r}")
    return tuple(specs)


def build_static_accessibility_specs(
    entries,
    *,
    static_accessibility_spec_cls,
    make_static_accessibility_spec_fn,
    role: str = "button",
):
    """Build StaticAccessibilitySpec-like values from shorthand tuples."""
    specs = []
    for entry in entries:
        if isinstance(entry, static_accessibility_spec_cls):
            specs.append(entry)
            continue
        control_attr, label = entry
        specs.append(
            make_static_accessibility_spec_fn(
                str(control_attr),
                label=str(label),
                role=str(role),
            )
        )
    return tuple(specs)
