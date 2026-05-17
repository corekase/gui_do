"""Build/helpers for the main demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import PanelControl, TooltipManager
from gui_do.features.data_driven_runtime import (
    RightAnchoredTaskPanelButtonSpec,
    add_right_anchored_task_panel_button,
    add_scene_menu_strip_from_spec,
    create_auto_sized_styled_label,
    register_tooltip_attr_specs,
    register_window_toggle_tooltips,
)
from gui_do.features.scene_task_panel_builder import SceneTaskPanelBuilder

from .main_specs import (
    MAIN_TASK_PANEL_LAYOUT_SPEC,
    MAIN_TASK_PANEL_SCENE_NAV_SPECS,
    MAIN_TASK_PANEL_SPEC,
    MAIN_TASK_PANEL_WINDOW_TOGGLE_GROUP_SPEC,
    MAIN_TITLE_SPEC,
    MAIN_TOOLTIP_BINDINGS,
    build_main_menu_strip_spec,
    build_main_task_panel_button_specs,
)

if TYPE_CHECKING:
    from .main_feature import MainFeature


def build_main_scene(feature: MainFeature, host) -> None:
    host.root = host.app.add(
        PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height), draw_background=False),
        scene_name="main",
    )

    host.desktop_menu_bar = add_scene_menu_strip_from_spec(
        host.root,
        host,
        build_main_menu_strip_spec(host.screen_rect.width, host.window_presentation.handle_window_toggle),
    )
    host.screen_title = host.root.add(
        create_auto_sized_styled_label(
            host,
            MAIN_TITLE_SPEC,
            scene_name="main",
        )
    )

    builder = (
        SceneTaskPanelBuilder(host)
        .panel_runtime(MAIN_TASK_PANEL_SPEC)
        .slots_runtime(MAIN_TASK_PANEL_LAYOUT_SPEC)
        .add_buttons(build_main_task_panel_button_specs(host))
        .with_window_toggles(
            group_spec=MAIN_TASK_PANEL_WINDOW_TOGGLE_GROUP_SPEC,
            window_presentation=host.window_presentation,
            attr_owner=host,
            tab_sequence_start=0,
        )
    )
    for nav_spec in MAIN_TASK_PANEL_SCENE_NAV_SPECS:
        builder.add_scene_nav_runtime(nav_spec)

    host.task_panel, task_panel_layout, task_panel_items = builder.build()
    toggle_controls = task_panel_items.window_toggle_controls

    slot0_rect = task_panel_layout.slot_rect(0)
    host.help_button = add_right_anchored_task_panel_button(
        host,
        host.task_panel,
        RightAnchoredTaskPanelButtonSpec(
            attr_name="help_button",
            control_id="show_help",
            label="Help (F9)",
            on_click=feature._toggle_help_overlay,
            width=int(slot0_rect.width),
            height=int(slot0_rect.height),
            top_offset=int(slot0_rect.top - host.task_panel.rect.top),
            right_padding=16,
            style="angle",
        ),
    )

    host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
    register_tooltip_attr_specs(
        host,
        host._main_tooltip_manager,
        MAIN_TOOLTIP_BINDINGS,
    )
    register_window_toggle_tooltips(host._main_tooltip_manager, toggle_controls)

    host.app.tile_windows()


def toggle_help_overlay(feature: MainFeature) -> None:
    overlay = feature._help_overlay
    if overlay is None:
        return
    overlay.toggle()


__all__ = [
    "build_main_scene",
    "toggle_help_overlay",
]
