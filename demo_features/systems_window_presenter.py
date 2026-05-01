from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.controls.chrome.window_control import WindowControl
from gui_do import (
    TabControl, TabItem, CanvasControl, LabelControl, inset_rect
)
from pygame import Rect

class SystemsWindowPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.tab = None


    def on_create(self):
        content = self.window.content_rect()
        pad = 10
        body_top = content.top + pad
        body_bottom = content.bottom - pad
        body_h = body_bottom - body_top
        body_content_top = body_top + 36 * 2  # _TAB_H * 2
        body_content_h = max(60, body_bottom - body_content_top)
        body_rect = Rect(content.left + pad, body_top, content.width - pad * 2, body_h)
        body_content_rect = Rect(
            content.left + pad, body_content_top, content.width - pad * 2, body_content_h
        )
        self.tab = TabControl(
            "nsdf_tab",
            body_rect,
            items=[
                TabItem("filter", "Filter"),
                TabItem("locale", "Locale"),
                TabItem("input", "Input"),
                TabItem("event", "Event"),
                TabItem("inspect", "Inspect"),
                TabItem("props", "Props"),
                TabItem("dock", "Dock"),
                TabItem("particle", "Particle"),
                TabItem("sprite", "Sprite"),
                TabItem("sched", "Sched"),
                TabItem("tilemap", "TileMap"),
                TabItem("progress", "Progress"),
                TabItem("flow", "Flow"),
                TabItem("search", "Search"),
                TabItem("listdiff", "ListDiff"),
                TabItem("cache", "Cache"),
                TabItem("shortcuts", "Shortcuts"),
            ],
            selected_key="filter",
            on_change=self.feature._on_tab_change,
            font_role=self.feature.font_role("control"),
        )
        self.window.add(self.tab)
        self.feature.tab = self.tab
        # Register tab content using previous logic
        self.feature._tabs.register("filter", self.feature._build_filter_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("locale", self.feature._build_locale_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("input", self.feature._build_input_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("event", self.feature._build_event_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("inspect", self.feature._build_inspect_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("props", self.feature._build_props_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("dock", self.feature._build_dock_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("particle", self.feature._build_particle_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("sprite", self.feature._build_sprite_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("sched", self.feature._build_sched_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("tilemap", self.feature._build_tilemap_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("progress", self.feature._build_progress_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("flow", self.feature._build_flow_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("search", self.feature._build_search_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("listdiff", self.feature._build_listdiff_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("cache", self.feature._build_cache_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("shortcuts", self.feature._build_shortcuts_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.on_activate("locale", lambda: setattr(self.feature, "_text_flow_dirty", True))

        # Restore feature state for correct initialization
        self.feature.window = self.window
        self.feature.demo = self.host
        self.window.visible = False

    def handle_event(self, event):
        # Optionally handle window-level events
        return False

    def update(self, dt_seconds: float):
        # Optionally update window state
        pass
