"""Window presenter for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import PanelControl, TabControl, TabItem
from gui_do.controls.chrome.window_presenter import WindowPresenter
from .systems_specs import (
    SYSTEMS_PRESENTER_HORIZONTAL_PADDING,
    SYSTEMS_PRESENTER_TAB_GAP,
    SYSTEMS_PRESENTER_TAB_HEIGHT,
    SYSTEMS_TAB_DEFINITIONS,
    SYSTEMS_TAB_KEYS,
)

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


class _SystemsPresenter(WindowPresenter):
    def __init__(self, feature: SystemsFeature, host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        feature = self.feature
        content_rect = self.window.content_rect()
        tab_height = SYSTEMS_PRESENTER_TAB_HEIGHT
        tab_gap = SYSTEMS_PRESENTER_TAB_GAP
        tabs = TabControl(
            "systems_tabs",
            Rect(content_rect.left, content_rect.top, content_rect.width, tab_height),
            items=[TabItem(key, label) for key, label in SYSTEMS_TAB_DEFINITIONS],
            selected_key=feature.active_tab_key,
            on_change=feature.set_active_tab,
            horizontal_padding=SYSTEMS_PRESENTER_HORIZONTAL_PADDING,
        )
        tabs.set_accessibility(role="tablist", label="Systems demo categories")
        self.add_control(tabs)
        feature.systems_tabs = tabs

        panel_rect = Rect(
            content_rect.left,
            content_rect.top + tab_height + tab_gap,
            content_rect.width,
            max(1, content_rect.height - tab_height - tab_gap),
        )
        panel_builders = [
            feature.build_data_panel,
            feature.build_validation_panel,
            feature.build_history_panel,
            feature.build_theme_panel,
            feature.build_state_panel,
            feature.build_infrastructure_panel,
            feature.build_scheduling_panel,
            feature.build_motion_panel,
            feature.build_persistence_panel,
            feature.build_graphics_panel,
            feature.build_text_panel,
        ]
        panel_keys = list(SYSTEMS_TAB_KEYS)
        panels: list[PanelControl] = [builder(panel_rect) for builder in panel_builders]
        for panel in panels:
            self.add_control(panel)

        feature._tab_panels = dict(zip(panel_keys, panels))
        feature.window = self.window
        feature.demo = self.host
        feature.set_active_tab(feature.active_tab_key)
        self.window.visible = False


__all__ = [
    "_SystemsPresenter",
]
