"""Build/helpers for the main demo feature."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from gui_do import LabelControl, PanelControl, TooltipManager, WindowControl
from gui_do.features.data_driven_runtime import (
    RightAnchoredTaskPanelButtonSpec,
    add_right_anchored_task_panel_button,
    add_menu_strip_from_spec,
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


def _add_opt_out_test_window(host) -> None:
    text = "This is an unmanaged window"
    text_w = 0
    text_h = 0
    theme = getattr(host.app, "theme", None)
    font_manager = getattr(theme, "fonts", None)
    if font_manager is not None and hasattr(font_manager, "font_instance"):
        try:
            size = int(font_manager.scaled_size(1.0))
            font = font_manager.font_instance("body", size=size)
            text_w, text_h = font.text_surface_size(text)
        except Exception:
            text_w = 0
            text_h = 0
    if text_w <= 0 or text_h <= 0:
        text_font = pygame.font.Font(None, 14)
        text_w, text_h = text_font.size(text)
    content_pad = 8
    titlebar_h = 24
    window_w = int(text_w + (content_pad * 2))
    window_h = int(titlebar_h + text_h + (content_pad * 2))

    screen_rect = Rect(host.screen_rect)
    window_rect = Rect(0, 0, window_w, window_h)
    window_rect.center = screen_rect.center

    host.opt_out_test_window = host.root.add(
        WindowControl(
            "opt_out_test_window",
            window_rect,
            "Opt-out test",
            use_frame_backdrop=True,
        )
    )
    host.opt_out_test_window.visible = True
    content_rect = host.opt_out_test_window.content_rect()
    host.opt_out_test_window.add(
        LabelControl(
            "opt_out_test_label",
            Rect(content_rect.left + content_pad, content_rect.top + content_pad, int(text_w), int(text_h)),
            text,
            align="left",
        )
    )

    # Register in presentation with explicit opt-out from window management surfaces.
    host._opt_out_test_window_feature = SimpleNamespace(window=host.opt_out_test_window)
    host.window_presentation.register_feature_window(
        "opt_out_test",
        feature_attribute_name="_opt_out_test_window_feature",
        window_management_opt_in=False,
    )


def build_main_scene(feature: MainFeature, host) -> None:
    host.root = host.app.add(
        PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height), draw_background=False),
        scene_name="main",
    )

    host.desktop_menu_bar = add_menu_strip_from_spec(
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
    _add_opt_out_test_window(host)


def toggle_help_overlay(feature: MainFeature) -> None:
    overlay = feature._help_overlay
    if overlay is None:
        return
    overlay.toggle()


__all__ = [
    "build_main_scene",
    "toggle_help_overlay",
]
