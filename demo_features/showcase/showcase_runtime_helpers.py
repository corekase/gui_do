"""Runtime helpers for the controls showcase feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    TaskPanelSceneNavButtonSpec,
    add_scene_task_panel_items,
    apply_category_visibility,
    draw_controls_prewarm,
    ensure_scene_task_panel,
    SceneTaskPanelSpec,
)
from gui_do.features.data_driven_runtime import TaskPanelSlotLayoutSpec, create_task_panel_slot_layout
from gui_do.features.layout_geometry import split_columns

from .showcase_helpers import category_for_row

if TYPE_CHECKING:
    from .showcase_feature import ShowcaseFeature


def col_width(feature: ShowcaseFeature, bounds: Rect, num_cols: int) -> int:
    cols = split_columns(bounds, count=num_cols, gap=feature.ROW_GAP, min_width=100)
    return cols[0].width if cols else bounds.width


def default_rect(feature: ShowcaseFeature, host) -> Rect:
    screen_rect = getattr(host, "screen_rect", None)
    if screen_rect is None:
        screen = getattr(host, "screen", None)
        if screen is not None:
            screen_rect = screen.get_rect()
    if screen_rect is None:
        return Rect(0, 0, 1, 1)
    return Rect(
        int(feature.ROOT_MARGIN_X),
        int(feature.ROOT_MARGIN_TOP),
        max(1, int(screen_rect.width - feature.ROOT_MARGIN_X * 2)),
        max(1, int(screen_rect.height - feature.ROOT_MARGIN_TOP - feature.ROOT_MARGIN_BOTTOM)),
    )


def set_active_category(feature: ShowcaseFeature, host, key: str) -> None:
    valid_keys = {k for k, _ in feature.SHOWCASE_CATEGORY_TABS}
    if key not in valid_keys or key == feature._active_category_key:
        return
    feature._active_category_key = key
    feature._apply_category_visibility(host)


def apply_active_category_visibility(feature: ShowcaseFeature, host) -> None:
    reg = feature._registry
    apply_category_visibility(
        active_key=feature._active_category_key,
        placed_controls=reg.placed_controls if reg is not None else [],
        control_labels=reg.control_labels if reg is not None else [],
        category_fn=category_for_row,
    )
    focused = getattr(host.app.focus, "focused", None)
    if focused is not None and not getattr(focused, "visible", True):
        if feature._category_tabs is not None and feature._category_tabs.visible and feature._category_tabs.enabled:
            host.app.focus.set_focus(feature._category_tabs)


def build_scene_task_panel(feature: ShowcaseFeature, host) -> None:
    feature.task_panel = ensure_scene_task_panel(
        host,
        SceneTaskPanelSpec(
            scene_name=feature.scene_name,
            control_id="control_showcase_task_panel",
            height=feature.TASK_PANEL_HEIGHT,
            hidden_peek_pixels=feature.TASK_PANEL_HIDDEN_PEEK_PIXELS,
            animation_step_px=feature.TASK_PANEL_ANIMATION_STEP_PX,
            dock_bottom=True,
            auto_hide=True,
        ),
    )
    task_panel_layout = create_task_panel_slot_layout(
        feature.task_panel,
        TaskPanelSlotLayoutSpec(
            left=feature.TASK_PANEL_BUTTON_LEFT,
            top_offset=feature.TASK_PANEL_BUTTON_TOP_OFFSET,
            item_width=feature.TASK_PANEL_BUTTON_WIDTH,
            item_height=feature.TASK_PANEL_BUTTON_HEIGHT,
            spacing=feature.TASK_PANEL_SLOT_SPACING,
            horizontal=True,
        ),
    )
    task_panel_items = add_scene_task_panel_items(
        host,
        feature.task_panel,
        task_panel_layout,
        scene_nav_button_specs=(
            TaskPanelSceneNavButtonSpec(
                control_id="showcase_return",
                slot_index=0,
                label="Return",
                target_scene="main",
                go_to_attr="go_to_main",
                style="angle",
                accessibility_role="button",
                accessibility_label="Return to main",
                tab_index=-1,
            ),
        ),
        window_toggle_group_spec=None,
        window_presentation=getattr(host, "window_presentation", None),
        window_toggle_attr_owner=feature,
        tab_sequence_start=None,
    )
    feature.showcase_return_button = (
        task_panel_items.scene_nav_buttons[0] if task_panel_items.scene_nav_buttons else None
    )


def on_update(feature: ShowcaseFeature, host, dt: float) -> None:
    if feature._indeterminate_bar is not None and feature._indeterminate_bar.visible:
        feature._indeterminate_bar.tick(dt)
    if feature._showcase_anim_ctrl is not None and feature._showcase_anim_ctrl.visible:
        feature._showcase_anim_ctrl.animation.update(dt)
        feature._showcase_anim_ctrl.invalidate()

    if not feature._pending_initial_focus:
        return
    if host.app.active_scene_name != feature.scene_name:
        return
    target = feature._initial_focus_control
    if target is None:
        feature._pending_initial_focus = False
        return
    if not host.app.scene.contains(target) or not target.visible or not target.enabled:
        feature._pending_initial_focus = False
        return
    host.app.focus.set_focus(target)
    feature._pending_initial_focus = False


def prewarm(feature: ShowcaseFeature, host, surface, theme) -> None:
    menu_strip = getattr(host, "control_showcase_menu_bar", None)
    reg = feature._registry
    tracked = [*reg.control_labels, *reg.controls] if reg is not None else []
    draw_controls_prewarm(surface, theme, [menu_strip, *tracked, feature.task_panel, feature.showcase_return_button])


__all__ = [
    "apply_active_category_visibility",
    "build_scene_task_panel",
    "col_width",
    "default_rect",
    "on_update",
    "prewarm",
    "set_active_category",
]
