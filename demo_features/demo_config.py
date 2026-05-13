from demo_features.moving_shapes import MovingShapesBackdropFeature
from demo_features.showcase import ShowcaseFeature
from demo_features.life import LifeFeature
from demo_features.main import MainFeature
from demo_features.mandelbrot import MandelbrotFeature

from gui_do import (
    ActionBindingSpec,
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
                "_life_feature",
                LifeFeature,
                "life",
                task_panel_label="Life",
                task_panel_style="round",
            ),
            FeatureWindowBundleBindingSpec(
                "_mandel_feature",
                MandelbrotFeature,
                "mandel",
                task_panel_label="Mandelbrot",
                task_panel_style="round",
            ),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
            ActionBindingSpec(
                kind="palette_open",
                action_id="palette_open",
                label="Open Command Palette",
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
        target_fps=120,
        palette_spec=PaletteBindingSpec(
            enable_builtin_entries=True,
            include_scene_entries=True,
            include_window_entries=True,
            group_order=("windows", "scenes"),
            connect_window_presentation=True,
        ),
    )
)

RUNTIME_SCENE_SPECS = DEMO_BOOTSTRAP_CONFIG.runtime_scene_specs
ACTION_SPECS = DEMO_BOOTSTRAP_CONFIG.action_specs
STATIC_ACCESSIBILITY_SPECS = DEMO_BOOTSTRAP_CONFIG.static_accessibility_specs
