from __future__ import annotations

from typing import Mapping

from pygame import Rect

from ..controls.input.window_toggle_button_control import WindowToggleButtonControl


def sorted_window_bindings(bindings):
    """Return feature-window bindings ordered by explicit slot then declaration order."""
    ordered = list(tuple(bindings))
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
    attr_owner=None,
    flow_start_slot: int = 0,
    flow_slot_assignments: Mapping[str, int] | None = None,
    panel_rect_overrides: Mapping[str, Rect | tuple[int, int, int, int]] | None = None,
):
    """Create window toggle controls on the task panel from declarative bindings."""
    target = host if attr_owner is None else attr_owner
    toggle_controls = []
    slot_map = {} if flow_slot_assignments is None else {str(k): int(v) for k, v in flow_slot_assignments.items()}
    rect_map = {
        str(k): v
        for k, v in ({} if panel_rect_overrides is None else panel_rect_overrides).items()
    }
    next_auto_slot = int(flow_start_slot)
    used_slots: set[int] = set(slot_map.values())
    next_tab_index = int(flow_start_slot)

    def _resolve_panel_rect(raw_rect) -> Rect:
        if isinstance(raw_rect, Rect):
            rel_rect = Rect(raw_rect)
        else:
            rel_rect = Rect(
                int(raw_rect[0]),
                int(raw_rect[1]),
                int(raw_rect[2]),
                int(raw_rect[3]),
            )
        return Rect(
            int(task_panel.rect.left) + int(rel_rect.left),
            int(task_panel.rect.top) + int(rel_rect.top),
            int(rel_rect.width),
            int(rel_rect.height),
        )

    for binding in sorted_window_bindings(window_presentation.bindings()):
        key = str(binding.key)
        assigned_slot = slot_map.get(key)
        if assigned_slot is None and getattr(binding, "task_panel_slot_index", None) is not None:
            assigned_slot = int(binding.task_panel_slot_index)

        if key in rect_map:
            control_rect = _resolve_panel_rect(rect_map[key])
        else:
            slot_index = assigned_slot
            if slot_index is None:
                while next_auto_slot in used_slots:
                    next_auto_slot += 1
                slot_index = int(next_auto_slot)
                next_auto_slot += 1
            used_slots.add(int(slot_index))
            next_auto_slot = max(next_auto_slot, int(slot_index) + 1)
            control_rect = app_layout.slot_rect(int(slot_index))

        tab_index = int(assigned_slot) if assigned_slot is not None else int(next_tab_index)
        next_tab_index = max(next_tab_index + 1, tab_index + 1)

        def _toggle_visibility(pushed, _key=binding.key):
            window_presentation.set_visible(
                _key,
                bool(pushed),
                from_toggle=True,
            )

        # Mark this callback so the button can avoid duplicate set_visible
        # when it already routed through app.window_presentation directly.
        setattr(_toggle_visibility, "_window_presentation_visibility_handler", True)

        toggle = task_panel.add(
            WindowToggleButtonControl(
                binding.task_panel_toggle_button_id or f"show_{binding.key}",
                control_rect,
                binding.key,  # window_id
                binding.task_panel_label or binding.key.title(),
                binding.task_panel_label or binding.key.title(),
                pushed=False,
                on_toggle=_toggle_visibility,
                on_show=(
                    lambda _key=binding.key: window_presentation.show(_key)
                ),
                style=binding.task_panel_style,
            )
        )
        toggle.set_tab_index(int(tab_index))
        panel_rect = Rect(
            int(toggle.rect.left) - int(task_panel.rect.left),
            int(toggle.rect.top) - int(task_panel.rect.top),
            int(toggle.rect.width),
            int(toggle.rect.height),
        )
        setattr(toggle, "task_panel_window_key", key)
        setattr(toggle, "task_panel_panel_rect", panel_rect)
        if binding.toggle_attribute_name:
            setattr(target, binding.toggle_attribute_name, toggle)
        toggle_controls.append((binding, toggle))
    return toggle_controls


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
    flow_slot_assignments: Mapping[str, int] | None = None,
    panel_rect_overrides: Mapping[str, Rect | tuple[int, int, int, int]] | None = None,
) -> list:
    """Create window toggle controls from a declarative TaskPanelWindowToggleGroupSpec."""
    toggle_controls = add_window_toggle_task_panel_controls(
        host,
        task_panel,
        app_layout,
        window_presentation,
        attr_owner=attr_owner,
        flow_start_slot=int(spec.flow_start_slot),
        flow_slot_assignments=(
            flow_slot_assignments
            if flow_slot_assignments is not None
            else spec.flow_slot_assignments
        ),
        panel_rect_overrides=(
            panel_rect_overrides
            if panel_rect_overrides is not None
            else spec.panel_rect_overrides
        ),
    )
    return toggle_controls
