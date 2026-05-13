"""State/runtime helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, DropdownControl, DropdownOption, LabelControl, PanelControl, StateTransaction

from .systems_commands import _SetIndexCommand

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_state_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_state_panel", Rect(rect), draw_background=False)
    context_title = LabelControl(
        "systems_state_context_title",
        Rect(0, 0, 120, 28),
        "Undo Context",
        align="left",
    )
    feature.state_context_dropdown = DropdownControl(
        "systems_state_context",
        Rect(0, 0, 180, 32),
        options=[
            DropdownOption("Release", "release"),
            DropdownOption("Build", "build"),
        ],
        selected_index=0,
        on_change=lambda value, _index: feature._on_state_context_changed(value),
    )
    feature._place_compact_labeled_row(
        panel,
        left=feature.LABEL_INSET_X,
        top=0,
        label=context_title,
        field=feature.state_context_dropdown,
        label_width=120,
        gap=10,
    )

    cycle_route_button = ButtonControl(
        "systems_state_route_cycle",
        Rect(0, 0, 170, 32),
        "Cycle Route Stack",
        feature._cycle_release_router,
        style="round",
    )
    state_label_top = feature._add_button_rows(
        panel,
        rect,
        44,
        [
            ButtonControl(
                "systems_state_approve",
                Rect(0, 0, 140, 32),
                "Approve Item",
                feature._approve_release_item,
                style="round",
            ),
            ButtonControl(
                "systems_state_blocker",
                Rect(0, 0, 140, 32),
                "Add Blocker",
                feature._add_release_blocker,
                style="round",
            ),
            ButtonControl(
                "systems_state_advance_context",
                Rect(0, 0, 190, 32),
                "Advance Active Context",
                feature._advance_active_context,
                style="round",
            ),
            ButtonControl(
                "systems_state_undo_context",
                Rect(0, 0, 96, 32),
                "Undo",
                feature._undo_active_context,
                style="round",
            ),
            ButtonControl(
                "systems_state_redo_context",
                Rect(0, 0, 96, 32),
                "Redo",
                feature._redo_active_context,
                style="round",
            ),
            ButtonControl(
                "systems_state_advance_fsm",
                Rect(0, 0, 156, 32),
                "Advance FSM",
                feature._advance_release_state_machine,
                style="round",
            ),
        ],
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )
    state_label_top = feature._add_single_column_button_row(
        panel,
        rect,
        state_label_top,
        cycle_route_button,
        column_index=0,
        span_both_columns=True,
        span_from_window_left=False,
        left=feature.PANEL_PADDING_X,
        width=max(1, rect.width - (feature.PANEL_PADDING_X * 2) - feature.LEFT_SIDE_INSET_X),
    )

    feature.state_store_label = LabelControl("systems_state_store", Rect(0, 0, rect.width, 28), "", align="left")
    feature.state_readiness_label = LabelControl(
        "systems_state_readiness", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.state_context_label = LabelControl(
        "systems_state_context_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.state_machine_label = LabelControl(
        "systems_state_machine_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.state_router_label = LabelControl(
        "systems_state_router_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            state_label_top + 8,
            max(1, rect.width - feature.LABEL_INSET_X),
            172,
        ),
        [
            feature.state_store_label,
            feature.state_readiness_label,
            feature.state_context_label,
            feature.state_machine_label,
            feature.state_router_label,
        ],
        gap=8,
    )
    feature._refresh_state_labels()
    return panel


def on_state_context_changed(feature: SystemsFeature, value: str) -> None:
    key = str(value)
    if key not in {"release", "build"}:
        return
    feature._undo_context.set_active(key)
    feature._undo_context_key = key
    feature._refresh_state_labels()


def approve_release_item(feature: SystemsFeature) -> None:
    pending = int(feature._release_store.get("pending", 0))
    approved = int(feature._release_store.get("approved", 0))
    blocked = int(feature._release_store.get("blocked", 0))
    if pending <= 0:
        return
    with StateTransaction(feature._release_store):
        next_pending = max(0, pending - 1)
        feature._release_store.dispatch(
            {
                "pending": next_pending,
                "approved": approved + 1,
                "status": "Ready" if next_pending == 0 and blocked == 0 else "Review",
            }
        )
    feature._refresh_state_labels()


def add_release_blocker(feature: SystemsFeature) -> None:
    blocked = int(feature._release_store.get("blocked", 0))
    feature._release_store.dispatch({"blocked": blocked + 1, "status": "Blocked"})
    feature._refresh_state_labels()


def advance_active_context(feature: SystemsFeature) -> None:
    if feature._undo_context_key == "release":
        current = feature._state_stage_index
        if current >= len(feature._state_stages) - 1:
            return
        next_index = current + 1
        feature._state_history.push(
            _SetIndexCommand(
                feature,
                "_state_stage_index",
                next_index,
                f"Set release milestone to {feature._state_stages[next_index]}",
            )
        )
    else:
        current = feature._state_build_stage_index
        if current >= len(feature._state_build_stages) - 1:
            return
        next_index = current + 1
        feature._state_build_history.push(
            _SetIndexCommand(
                feature,
                "_state_build_stage_index",
                next_index,
                f"Set build lane to {feature._state_build_stages[next_index]}",
            )
        )
    feature._refresh_state_labels()


def undo_active_context(feature: SystemsFeature) -> None:
    feature._undo_context.undo()
    feature._refresh_state_labels()


def redo_active_context(feature: SystemsFeature) -> None:
    feature._undo_context.redo()
    feature._refresh_state_labels()


def advance_release_state_machine(feature: SystemsFeature) -> None:
    feature._release_state_machine.trigger("advance")
    if feature._release_hierarchical_state_machine.current.value == "planning":
        feature._release_hierarchical_state_machine.trigger("start")
    else:
        promoted = feature._release_hierarchical_state_machine.sub_trigger("execution", "promote")
        if not promoted:
            feature._release_hierarchical_state_machine.trigger("pause")
    feature._refresh_state_labels()


def cycle_release_router(feature: SystemsFeature) -> None:
    phase = feature._router_cycle_index % 3
    next_route = feature._router_cycle_paths[feature._router_cycle_index % len(feature._router_cycle_paths)]
    if phase == 0:
        feature._release_router.push(next_route, {"source": "systems_demo"})
    elif phase == 1:
        feature._release_router.replace(next_route, {"mode": "replace"})
    else:
        if not feature._release_router.pop():
            feature._release_router.push(next_route, {"source": "systems_demo"})
    feature._router_cycle_index += 1
    feature._refresh_state_labels()


def refresh_state_labels(feature: SystemsFeature) -> None:
    pending = int(feature._release_store.get("pending", 0))
    approved = int(feature._release_store.get("approved", 0))
    blocked = int(feature._release_store.get("blocked", 0))
    status = str(feature._release_store.get("status", "Review"))
    readiness = int(feature._release_readiness.value)
    active_key = feature._undo_context.active_key or "none"
    if feature.state_store_label is not None:
        feature.state_store_label.text = (
            f"AppStateStore release queue -> pending {pending} | approved {approved} | blocked {blocked} | status {status}"
        )
    if feature.state_readiness_label is not None:
        feature.state_readiness_label.text = (
            f"StateSelector readiness score: {readiness} (approved contributes +25, blockers contribute -10 each)"
        )
    if feature.state_context_label is not None:
        release_stage = feature._state_stages[feature._state_stage_index]
        build_stage = feature._state_build_stages[feature._state_build_stage_index]
        feature.state_context_label.text = (
            f"UndoContextManager active={active_key} | release={release_stage} | build={build_stage} "
            f"| can_undo={feature._undo_context.can_undo} | can_redo={feature._undo_context.can_redo}"
        )
    if feature.state_machine_label is not None:
        hierarchy_state = feature._release_hierarchical_state_machine.current.value
        hierarchy_ring = feature._release_hierarchical_state_machine.sub_current("execution")
        feature.state_machine_label.text = (
            f"StateMachine stage={feature._release_state_machine.current.value} | "
            f"HierarchicalStateMachine outer={hierarchy_state} ring={hierarchy_ring}"
        )
    if feature.state_router_label is not None:
        current_route = feature._release_router.current_route or "none"
        feature.state_router_label.text = (
            f"Router route={current_route} history={len(feature._release_router.history)} "
            f"can_pop={feature._release_router.can_pop()}"
        )


__all__ = [
    "build_state_panel",
    "add_release_blocker",
    "advance_active_context",
    "advance_release_state_machine",
    "approve_release_item",
    "cycle_release_router",
    "on_state_context_changed",
    "redo_active_context",
    "refresh_state_labels",
    "undo_active_context",
]
