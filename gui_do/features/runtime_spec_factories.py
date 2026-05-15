from __future__ import annotations


def make_window_toggle_spec(
    *,
    window_spec_cls,
    key: str,
    feature_attribute_name: str,
    task_panel_slot_index: int | None = None,
    task_panel_label: str | None = None,
    task_panel_style: str = "round",
    action_label: str | None = None,
    action_name: str | None = None,
    task_panel_toggle_button_id: str | None = None,
    toggle_attribute_name: str | None = None,
    accessibility_label: str | None = None,
    window_effects: dict | None = None,
):
    """Build a WindowSpec-like object with conventional defaults for window toggles."""
    normalized_key = str(key)
    normalized_label = task_panel_label or normalized_key.replace("_", " ").title()
    return window_spec_cls(
        key=normalized_key,
        feature_attribute_name=str(feature_attribute_name),
        toggle_attribute_name=toggle_attribute_name or f"{normalized_key}_toggle_window",
        action_name=action_name or f"win_{normalized_key}",
        action_label=action_label or f"Show {normalized_label} Window",
        task_panel_toggle_button_id=task_panel_toggle_button_id or f"show_{normalized_key}",
        task_panel_label=normalized_label,
        task_panel_style=str(task_panel_style),
        task_panel_slot_index=(None if task_panel_slot_index is None else int(task_panel_slot_index)),
        accessibility_label=accessibility_label or f"Show {normalized_label} window",
        window_effects=window_effects or {},
    )


def make_scene_nav_action(*, action_spec_cls, action_id: str, label: str, target_scene: str, category: str = "Scenes"):
    """Build a scene-navigation ActionSpec-like object with consistent defaults."""
    return action_spec_cls(
        action_id=str(action_id),
        label=str(label),
        kind="scene_nav",
        target=str(target_scene),
        category=str(category),
    )


def make_exit_action(*, action_spec_cls, action_id: str = "exit", label: str = "Exit", category: str = "File"):
    """Build a standard exit ActionSpec-like object."""
    return action_spec_cls(
        action_id=str(action_id),
        label=str(label),
        kind="exit",
        target=None,
        category=str(category),
    )


def make_palette_open_action(
    *,
    action_spec_cls,
    action_id: str = "palette_open",
    label: str = "Open Command Palette",
    key: int | None = None,
):
    """Build a standard command-palette open ActionSpec-like object."""
    return action_spec_cls(
        action_id=str(action_id),
        label=str(label),
        kind="palette_open",
        target=None,
        category=None,
        key=key,
    )


def make_static_accessibility_spec(*, static_accessibility_spec_cls, control_attr: str, label: str, role: str = "button"):
    """Build a StaticAccessibilitySpec-like object with a button-role default."""
    return static_accessibility_spec_cls(
        control_attr=str(control_attr),
        role=str(role),
        label=str(label),
    )
