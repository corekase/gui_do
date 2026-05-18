from __future__ import annotations

from typing import Mapping

from ..controls.input.toggle_control import ToggleControl


def sorted_window_bindings(bindings):
    """Return feature-window bindings ordered by explicit slot then declaration order, only including those with window_menu_opt_in=True (default). Setting window_menu_opt_in to False opts out."""
    ordered = list(tuple(bindings))
    # Only include bindings with window_menu_opt_in True (default)
    ordered = [b for b in ordered if getattr(b, "window_menu_opt_in", True)]
    with_slots = [b for b in ordered if getattr(b, "task_panel_slot_index", None) is not None]
    without_slots = [b for b in ordered if getattr(b, "task_panel_slot_index", None) is None]
    with_slots.sort(key=lambda b: (int(b.task_panel_slot_index), str(getattr(b, "key", ""))))
    return tuple([*with_slots, *without_slots])


def collect_window_toggle_controls(host, window_presentation):
    """Return sorted (binding, control) pairs for all available window toggles on host."""
    controls = []
    for binding in sorted_window_bindings(window_presentation.bindings()):
        toggle_attribute_name = getattr(binding, "toggle_attribute_name", None)
        if toggle_attribute_name is None:
            continue
        control = getattr(host, str(toggle_attribute_name), None)
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


def add_window_toggle_task_panel_controls(
    host,
    task_panel,
    app_layout,
    window_presentation,
    *,
    min_slot_index: int | None = None,
    max_slot_index: int | None = None,
    attr_owner=None,
    slot_overrides: Mapping[str, int] | None = None,
):
    """Create window toggle controls on the task panel from declarative bindings."""
    target = host if attr_owner is None else attr_owner
    toggle_controls = []
    max_seen_slot_index = 0
    slot_map = {} if slot_overrides is None else {str(k): int(v) for k, v in slot_overrides.items()}
    next_auto_slot = int(min_slot_index) if min_slot_index is not None else 0
    used_slots: set[int] = set(slot_map.values())
    for binding in sorted_window_bindings(window_presentation.bindings()):
        if str(binding.key) in slot_map:
            slot_index = int(slot_map[str(binding.key)])
        elif binding.task_panel_slot_index is not None:
            slot_index = int(binding.task_panel_slot_index)
        else:
            while next_auto_slot in used_slots:
                next_auto_slot += 1
            slot_index = int(next_auto_slot)
            used_slots.add(slot_index)
            next_auto_slot += 1
        if min_slot_index is not None and slot_index < int(min_slot_index):
            continue
        if max_slot_index is not None and slot_index > int(max_slot_index):
            continue
        used_slots.add(slot_index)
        next_auto_slot = max(next_auto_slot, slot_index + 1)
        max_seen_slot_index = max(max_seen_slot_index, slot_index)
        toggle = task_panel.add(
            ToggleControl(
                binding.task_panel_toggle_button_id or f"show_{binding.key}",
                app_layout.slot_rect(slot_index),
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
        toggle.set_tab_index(int(slot_index))
        if binding.toggle_attribute_name:
            setattr(target, binding.toggle_attribute_name, toggle)
        toggle_controls.append((binding, toggle))
    return toggle_controls, max_seen_slot_index


def register_window_toggle_tooltips(tooltip_manager, toggle_controls) -> None:
    """Register standardized window toggle tooltip labels."""
    for binding, toggle in toggle_controls:
        label = binding.task_panel_label or binding.action_label or binding.key.title()
        tooltip_manager.register(toggle, f"Toggle the {label} window")


def add_task_panel_window_toggle_group(
    host,
    task_panel,
    app_layout,
    window_presentation,
    spec,
    *,
    attr_owner=None,
    slot_overrides: Mapping[str, int] | None = None,
) -> list:
    """Create window toggle controls from a declarative TaskPanelWindowToggleGroupSpec."""
    toggle_controls, _ = add_window_toggle_task_panel_controls(
        host,
        task_panel,
        app_layout,
        window_presentation,
        min_slot_index=int(spec.start_index),
        attr_owner=attr_owner,
        slot_overrides=slot_overrides,
    )
    return toggle_controls
