from __future__ import annotations

from collections.abc import Sequence

from pygame import Rect

from ..controls.input.button_control import ButtonControl


def add_task_panel_button(
    task_panel,
    app_layout,
    *,
    control_id: str,
    slot_index: int,
    label: str,
    on_click,
    style: str = "angle",
    assign_tab_index: bool = True,
):
    """Create and add a standard task-panel button positioned by linear slot index."""
    button = task_panel.add(
        ButtonControl(
            str(control_id),
            app_layout.linear(int(slot_index)),
            str(label),
            on_click,
            style=str(style),
        )
    )
    if bool(assign_tab_index):
        button.set_tab_index(int(slot_index))
    return button


def add_task_panel_buttons(host, task_panel, app_layout, specs: Sequence[object], *, add_task_panel_button_fn) -> None:
    """Create and assign host-owned task-panel buttons from declarative specs."""
    next_slot = 0
    used_slots: set[int] = set()
    for spec in specs:
        if spec.slot_index is None:
            while next_slot in used_slots:
                next_slot += 1
            slot_index = next_slot
            used_slots.add(slot_index)
            next_slot += 1
        else:
            slot_index = int(spec.slot_index)
            used_slots.add(slot_index)
            next_slot = max(next_slot, slot_index + 1)
        button = add_task_panel_button_fn(
            task_panel,
            app_layout,
            control_id=spec.control_id,
            slot_index=slot_index,
            label=spec.label,
            on_click=spec.on_click,
            style=spec.style,
        )
        setattr(host, spec.attr_name, button)


def add_right_anchored_task_panel_button(host, task_panel, spec) -> object:
    """Create one task-panel button anchored to the panel's right edge."""
    rect = Rect(
        int(task_panel.rect.right) - int(spec.right_padding) - int(spec.width),
        int(task_panel.rect.top) + int(spec.top_offset),
        int(spec.width),
        int(spec.height),
    )
    button = task_panel.add(
        ButtonControl(
            str(spec.control_id),
            rect,
            str(spec.label),
            spec.on_click,
            style=str(spec.style),
        )
    )
    if not bool(spec.include_in_task_panel_focus_cycle):
        button.set_tab_index(-1)
        setattr(button, "task_panel_focus_excluded", True)
    else:
        peers = getattr(task_panel, "children", None)
        if not isinstance(peers, list):
            peers = getattr(task_panel, "added_controls", [])
        prior_indices = [
            int(getattr(node, "tab_index", -1))
            for node in peers
            if node is not button and int(getattr(node, "tab_index", -1)) >= 0
        ]
        button.set_tab_index(0 if not prior_indices else (max(prior_indices) + 1))
    setattr(host, spec.attr_name, button)
    return button
