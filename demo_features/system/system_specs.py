"""Shared specs and top-level config for the systems demo feature."""

from __future__ import annotations

from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec,
    TabbedPresenterSpec,
    build_tab_builder_specs,
)

_TAB_H = 36

_SYSTEMS_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="systems_window",
    title="System",
    size=(820, 590),
    anchor="top_left",
    margin=(24, 92),
    use_frame_backdrop=True,
)

_SYSTEMS_TAB_ENTRIES = (
    ("filter", "Filter"),
    ("locale", "Locale"),
    ("input", "Input"),
    ("event", "Event"),
    ("inspect", "Inspect"),
    ("props", "Props"),
    ("dock", "Dock"),
    ("particle", "Particle"),
    ("sprite", "Sprite"),
    ("sched", "Sched"),
    ("tilemap", "TileMap"),
    ("progress", "Progress"),
    ("flow", "Flow"),
    ("search", "Search"),
    ("listdiff", "ListDiff"),
    ("cache", "Cache"),
    ("shortcuts", "Shortcuts"),
    ("arch2", "New Arch"),
    ("arch3", "New Sys"),
)
_SYSTEMS_TAB_SPECS = build_tab_builder_specs(_SYSTEMS_TAB_ENTRIES)

_SYSTEMS_TABBED_PRESENTER_SPEC = TabbedPresenterSpec(
    control_id="nsdf_tab",
    selected_key="filter",
    tab_height=_TAB_H,
    tab_rows=2,
    padding=0,
    min_content_height=60,
)

_SYSTEMS_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_shortcut_overlay",
            action_registry_attr="action_registry",
            width=560,
            height=400,
        ),
    ),
)

_SYSTEMS_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec=_SYSTEMS_RUNTIME_SPEC,
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)
