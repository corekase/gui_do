"""Window presenter for the systems demo feature."""

from __future__ import annotations

from gui_do.controls.chrome.window_presenter import WindowPresenter

from .system_feature import (
    _SYSTEMS_TAB_SPECS,
    _SYSTEMS_TABBED_PRESENTER_SPEC,
    setup_feature_presenter_tabs_from_window_content,
)


class SystemPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.tab = None

    def on_create(self):
        self.feature.window = self.window
        self.feature.demo = self.host
        self.tab = setup_feature_presenter_tabs_from_window_content(
            self,
            window=self.window,
            spec=_SYSTEMS_TABBED_PRESENTER_SPEC,
            tab_specs=_SYSTEMS_TAB_SPECS,
            on_change=self.feature._on_tab_change,
            tab_manager=self.feature._tabs,
            feature=self.feature,
            host=self.host,
            on_activate_callbacks=(
                ("locale", lambda: setattr(self.feature, "_text_flow_dirty", True)),
            ),
        )
        self.feature.tab = self.tab
        self.window.visible = False


__all__ = ["SystemPresenter"]
