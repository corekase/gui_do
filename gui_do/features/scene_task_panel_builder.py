"""Generalized scene task panel composition helpers.

This module provides a compact API for feature code: callers provide small
specs and the builder handles panel creation, slot layout wiring, and item
insertion through the canonical runtime helpers.
"""

from __future__ import annotations

from dataclasses import dataclass

from gui_do.features.data_driven_runtime import (
    TaskPanelButtonSpec,
    SceneTaskPanelSpec,
    TaskPanelSceneNavButtonSpec,
    TaskPanelSlotLayoutSpec,
    add_scene_task_panel_items,
    create_task_panel_slot_layout,
    ensure_scene_task_panel,
)


@dataclass(frozen=True)
class SceneTaskPanelBuildSpec:
    scene_name: str
    control_id: str
    height: int
    hidden_peek_pixels: int
    animation_step_px: int
    dock_bottom: bool = True
    auto_hide: bool = True


@dataclass(frozen=True)
class TaskPanelSlotBuildSpec:
    left: int
    top_offset: int
    item_width: int
    item_height: int
    spacing: int
    horizontal: bool = True


@dataclass(frozen=True)
class SceneNavTaskButtonSpec:
    control_id: str
    slot_index: int | None
    label: str
    target_scene: str
    go_to_attr: str | None
    style: str = "angle"
    accessibility_role: str = "button"
    accessibility_label: str = ""
    tab_index: int | None = -1


class SceneTaskPanelBuilder:
    def __init__(self, host):
        self._host = host
        self._panel_spec: SceneTaskPanelBuildSpec | None = None
        self._slot_spec: TaskPanelSlotBuildSpec | None = None
        self._nav_specs: list[SceneNavTaskButtonSpec] = []
        self._button_specs: list[TaskPanelButtonSpec] = []
        self._window_toggle_group_spec = None
        self._window_presentation = None
        self._window_toggle_attr_owner = None
        self._tab_sequence_start = None

    def panel(self, spec: SceneTaskPanelBuildSpec) -> "SceneTaskPanelBuilder":
        self._panel_spec = spec
        return self

    def slots(self, spec: TaskPanelSlotBuildSpec) -> "SceneTaskPanelBuilder":
        self._slot_spec = spec
        return self

    def panel_runtime(self, spec: SceneTaskPanelSpec) -> "SceneTaskPanelBuilder":
        self._panel_spec = SceneTaskPanelBuildSpec(
            scene_name=str(spec.scene_name),
            control_id=str(spec.control_id),
            height=int(spec.height),
            hidden_peek_pixels=int(spec.hidden_peek_pixels),
            animation_step_px=int(spec.animation_step_px),
            dock_bottom=bool(spec.dock_bottom),
            auto_hide=bool(spec.auto_hide),
        )
        return self

    def slots_runtime(self, spec: TaskPanelSlotLayoutSpec) -> "SceneTaskPanelBuilder":
        self._slot_spec = TaskPanelSlotBuildSpec(
            left=int(spec.left),
            top_offset=int(spec.top_offset),
            item_width=int(spec.item_width),
            item_height=int(spec.item_height),
            spacing=int(spec.spacing),
            horizontal=bool(spec.horizontal),
        )
        return self

    def add_scene_nav(self, spec: SceneNavTaskButtonSpec) -> "SceneTaskPanelBuilder":
        self._nav_specs.append(spec)
        return self

    def add_scene_nav_runtime(self, spec: TaskPanelSceneNavButtonSpec) -> "SceneTaskPanelBuilder":
        slot_index = None if spec.slot_index is None else int(spec.slot_index)
        tab_index = None if spec.tab_index is None else int(spec.tab_index)
        go_to_attr = None if spec.go_to_attr is None else str(spec.go_to_attr)
        self._nav_specs.append(
            SceneNavTaskButtonSpec(
                control_id=str(spec.control_id),
                slot_index=slot_index,
                label=str(spec.label),
                target_scene=str(spec.target_scene),
                go_to_attr=go_to_attr,
                style=str(spec.style),
                accessibility_role=str(spec.accessibility_role),
                accessibility_label=str(spec.accessibility_label),
                tab_index=tab_index,
            )
        )
        return self

    def add_buttons(self, specs) -> "SceneTaskPanelBuilder":
        self._button_specs.extend(tuple(specs))
        return self

    def with_window_toggles(
        self,
        *,
        group_spec,
        window_presentation,
        attr_owner,
        tab_sequence_start=None,
    ) -> "SceneTaskPanelBuilder":
        self._window_toggle_group_spec = group_spec
        self._window_presentation = window_presentation
        self._window_toggle_attr_owner = attr_owner
        self._tab_sequence_start = tab_sequence_start
        return self

    def build(self):
        if self._panel_spec is None:
            raise ValueError("SceneTaskPanelBuilder requires panel() before build().")
        if self._slot_spec is None:
            raise ValueError("SceneTaskPanelBuilder requires slots() before build().")

        panel = ensure_scene_task_panel(
            self._host,
            SceneTaskPanelSpec(
                scene_name=self._panel_spec.scene_name,
                control_id=self._panel_spec.control_id,
                height=self._panel_spec.height,
                hidden_peek_pixels=self._panel_spec.hidden_peek_pixels,
                animation_step_px=self._panel_spec.animation_step_px,
                dock_bottom=self._panel_spec.dock_bottom,
                auto_hide=self._panel_spec.auto_hide,
            ),
        )

        layout = create_task_panel_slot_layout(
            panel,
            TaskPanelSlotLayoutSpec(
                left=self._slot_spec.left,
                top_offset=self._slot_spec.top_offset,
                item_width=self._slot_spec.item_width,
                item_height=self._slot_spec.item_height,
                spacing=self._slot_spec.spacing,
                horizontal=self._slot_spec.horizontal,
            ),
        )

        nav_specs = tuple(
            TaskPanelSceneNavButtonSpec(
                control_id=spec.control_id,
                slot_index=spec.slot_index,
                label=spec.label,
                target_scene=spec.target_scene,
                go_to_attr=spec.go_to_attr,
                style=spec.style,
                accessibility_role=spec.accessibility_role,
                accessibility_label=spec.accessibility_label,
                tab_index=spec.tab_index,
            )
            for spec in self._nav_specs
        )

        items = add_scene_task_panel_items(
            self._host,
            panel,
            layout,
            button_specs=tuple(self._button_specs),
            scene_nav_button_specs=nav_specs,
            window_toggle_group_spec=self._window_toggle_group_spec,
            window_presentation=self._window_presentation,
            window_toggle_attr_owner=self._window_toggle_attr_owner,
            tab_sequence_start=self._tab_sequence_start,
        )
        return panel, layout, items


__all__ = [
    "SceneTaskPanelBuildSpec",
    "TaskPanelSlotBuildSpec",
    "SceneNavTaskButtonSpec",
    "SceneTaskPanelBuilder",
]
