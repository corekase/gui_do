try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from demo_features.controls_demo_feature import ControlsShowcaseFeature
from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.main_demo_feature import MainDemoFeature
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature
from demo_features.systems_demo_feature import SystemsDemoFeature

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
import pygame


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
                bind_escape_to_exit=True,
                prewarm=True,
                include_nav_action=True,
                nav_action_id="nav_main",
                nav_label="Go to Main Scene",
            ),
            SceneBundleBindingSpec(
                scene_name="control_showcase",
                pretty_name="Control Showcase",
                transition_style=SceneTransitionStyle.SLIDE_LEFT,
                transition_duration=0.5,
                pristine_asset="demo_features/data/images/backdrop.jpg",
                bind_escape_to_exit=True,
                prewarm=True,
                include_scene_root=True,
                scene_root_id="control_showcase_root",
                scene_root_draw_background=False,
                include_nav_action=True,
                nav_action_id="nav_showcase",
                nav_label="Go to Controls Showcase",
            ),
        ),
        feature_entries=(
            (
                "_shapes_feature",
                lambda: BouncingShapesBackdropFeature(
                    circle_count=12,
                    square_count=12,
                    octagon_count=12,
                    star_count=12,
                ),
            ),
            ("_main_feature", MainDemoFeature),
            ("_controls_feature", ControlsShowcaseFeature),
        ),
        feature_window_bundle_entries=(
            FeatureWindowBundleBindingSpec(
                "_systems_feature",
                SystemsDemoFeature,
                "systems",
                slot_index=1,
                task_panel_label="System",
                task_panel_style="angle",
                tab_before_showcase=True,
            ),
            FeatureWindowBundleBindingSpec(
                "_life_feature",
                LifeSimulationFeature,
                "life",
                slot_index=3,
                task_panel_label="Life",
                task_panel_style="round",
            ),
            FeatureWindowBundleBindingSpec(
                "_mandel_feature",
                MandelbrotRenderFeature,
                "mandel",
                slot_index=4,
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
                key=pygame.K_F5,
            ),
        ),
        static_accessibility_entries=(
            ("exit_button", "Exit"),
            ("showcase_button", "Showcase"),
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
            connect_window_presentation=True,
        ),
    )
)

RUNTIME_SCENE_SPECS = DEMO_BOOTSTRAP_CONFIG.runtime_scene_specs
ACTION_SPECS = DEMO_BOOTSTRAP_CONFIG.action_specs
STATIC_ACCESSIBILITY_SPECS = DEMO_BOOTSTRAP_CONFIG.static_accessibility_specs
