from demo_features.life.life_feature import LifeFeature
from demo_features.main.main_feature import MainFeature
from demo_features.mandelbrot.mandelbrot_feature import MandelbrotFeature
from demo_features.moving_shapes.moving_shapes_backdrop_feature import MovingShapesBackdropFeature
from demo_features.showcase.showcase_feature import ShowcaseFeature
from demo_features.systems.systems_feature import SystemsFeature

from gui_do import (
    ActionBindingSpec,
    CommandEntry,
    CursorBindingSpec,
    FeatureWindowBundleBindingSpec,
    FontRoleBindingSpec,
    HostApplicationBindingSpec,
    PaletteBindingSpec,
    SceneBundleBindingSpec,
    SceneTransitionStyle,
    TelemetryConfig,
    build_host_application_config,
)


def _build_demo_palette_entries(app):
    feature_manager = getattr(app, "features", None)
    get_feature = getattr(feature_manager, "get", None)
    if not callable(get_feature):
        return ()
    main_feature = get_feature("main_demo")
    if main_feature is None:
        return ()

    tiling_enabled = False
    is_window_tiling_enabled = getattr(app, "is_window_tiling_enabled", None)
    if callable(is_window_tiling_enabled):
        tiling_enabled = bool(is_window_tiling_enabled(scene_name="main"))

    def _refresh_automatic_layout_entry(entry: CommandEntry) -> None:
        enabled = False
        if callable(is_window_tiling_enabled):
            enabled = bool(is_window_tiling_enabled(scene_name="main"))
        entry.toggle_state = enabled
        entry.title = "Automatic Layout On" if enabled else "Automatic Layout Off"

    return (
        CommandEntry(
            entry_id="command:main:toggle_automatic_layout",
            title="Automatic Layout On" if tiling_enabled else "Automatic Layout Off",
            action=main_feature.toggle_automatic_layout,
            description="Toggle automatic window layout for the main scene.",
            category="Commands",
            scene_name="main",
            render_kind="command_toggle",
            toggle_state=tiling_enabled,
            refresh_after_action=_refresh_automatic_layout_entry,
        ),
        CommandEntry(
            entry_id="command:main:layout_now",
            title="Layout Windows Now",
            action=main_feature.layout_windows_now,
            description="Tile all visible windows in the main scene immediately.",
            category="Commands",
            scene_name="main",
            render_kind="command_button",
        ),
    )


DEMO_BOOTSTRAP_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1920, 1080),
        window_title="gui_do demo",
        fonts={
            "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14},
            "window": "demo_features/data/fonts/Ubuntu-B.ttf",
        },
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Desktop Demo",
                transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                transition_duration=0.5,
                tiling_enabled=True,
                pristine_asset="demo_features/data/images/backdrop.jpg",
                prewarm=True,
                emit_nav_action_spec=True,
                nav_action_id="nav_main",
                nav_label="Go to Main Scene",
            ),
            SceneBundleBindingSpec(
                scene_name="control_showcase",
                pretty_name="Control Showcase",
                transition_style=SceneTransitionStyle.SLIDE_LEFT,
                transition_duration=0.5,
                pristine_asset="demo_features/data/images/backdrop.jpg",
                prewarm=True,
                emit_scene_root_spec=True,
                scene_root_id="control_showcase_root",
                scene_root_draw_background=False,
                emit_nav_action_spec=True,
                nav_action_id="nav_showcase",
                nav_label="Go to Controls Showcase",
            ),
        ),
        feature_entries=(
            (
                "_shapes_feature",
                lambda: MovingShapesBackdropFeature(total_shapes=49),
            ),
            ("_main_feature", MainFeature),
            ("_controls_feature", ShowcaseFeature),
        ),
        feature_window_bundle_entries=(
            FeatureWindowBundleBindingSpec(
                "_systems_feature",
                SystemsFeature,
                "systems",
                task_panel_label="Systems",
                task_panel_style="round",
                task_panel_slot_index=1,
                window_effects={"grow_shrink_enabled": True},
            ),
            FeatureWindowBundleBindingSpec(
                "_life_feature",
                LifeFeature,
                "life",
                task_panel_label="Life",
                task_panel_style="round",
                task_panel_slot_index=2,
                window_effects={"hide_show_enabled": True},
            ),
            FeatureWindowBundleBindingSpec(
                "_mandel_feature",
                MandelbrotFeature,
                "mandel",
                task_panel_label="Mandelbrot",
                task_panel_style="round",
                task_panel_slot_index=3,
                window_effects={"hide_show_enabled": True},
            ),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
            ActionBindingSpec(
                kind="palette_toggle",
                action_id="palette_toggle",
                label="Toggle Command Palette",
            ),
        ),
        static_accessibility_entries=(
            ("exit_button", "Exit"),
        ),
        font_role_entries=(
            FontRoleBindingSpec("title", 14, "window"),
        ),
        cursor_entries=(
            CursorBindingSpec("normal", "demo_features/data/cursors/cursor.png", (1, 1)),
            CursorBindingSpec("hand", "demo_features/data/cursors/hand.png", (12, 12)),
        ),
        telemetry=TelemetryConfig(enabled=False),
        target_fps=60,
        palette_spec=PaletteBindingSpec(
            enable_builtin_entries=True,
            include_scene_entries=True,
            include_window_entries=True,
            group_order=("windows", "scenes", "custom"),
            custom_entries_provider=_build_demo_palette_entries,
            connect_window_presentation=True,
        ),
    )
)

RUNTIME_SCENE_SPECS = DEMO_BOOTSTRAP_CONFIG.runtime_scene_specs
ACTION_SPECS = DEMO_BOOTSTRAP_CONFIG.action_specs
STATIC_ACCESSIBILITY_SPECS = DEMO_BOOTSTRAP_CONFIG.static_accessibility_specs
