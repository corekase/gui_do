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
    ActionSpec,
    CursorSpec,
    FeatureSpec,
    HostApplicationConfig,
    RuntimeSceneSpec,
    SceneRootSpec,
    SceneSetupSpec,
    SceneTransitionStyle,
    StaticAccessibilitySpec,
    TelemetryConfig,
    WindowSpec,
)


SCENE_SPECS = (
    SceneSetupSpec(
        name="main",
        pretty_name="Desktop Demo",
        transition_style=SceneTransitionStyle.SLIDE_RIGHT,
        transition_duration=0.5,
        make_initial=True,
    ),
    SceneSetupSpec(
        name="control_showcase",
        pretty_name="Control Showcase",
        transition_style=SceneTransitionStyle.SLIDE_LEFT,
        transition_duration=0.5,
    ),
)

FEATURE_SPECS = (
    FeatureSpec(
        attr_name="_shapes_feature",
        factory=lambda: BouncingShapesBackdropFeature(
            circle_count=12,
            square_count=12,
            octagon_count=12,
            star_count=12,
        ),
    ),
    FeatureSpec(attr_name="_main_feature", factory=MainDemoFeature),
    FeatureSpec(attr_name="_life_feature", factory=LifeSimulationFeature),
    FeatureSpec(attr_name="_controls_feature", factory=ControlsShowcaseFeature),
    FeatureSpec(attr_name="_mandel_feature", factory=MandelbrotRenderFeature),
    FeatureSpec(attr_name="_systems_feature", factory=SystemsDemoFeature),
)

WINDOW_SPECS = (
    WindowSpec(
        key="systems",
        feature_attr="_systems_feature",
        toggle_attr="systems_toggle_window",
        action_name="win_systems",
        action_label="Show Systems Window",
        task_panel_button_id="show_systems",
        task_panel_label="System",
        task_panel_style="angle",
        task_panel_slot_index=1,
        tab_before_showcase=True,
        accessibility_label="Show Systems window",
    ),
    WindowSpec(
        key="life",
        feature_attr="_life_feature",
        toggle_attr="life_toggle_window",
        action_name="win_life",
        action_label="Show Life Window",
        task_panel_button_id="show_life",
        task_panel_label="Life",
        task_panel_style="round",
        task_panel_slot_index=3,
        tab_before_showcase=False,
        accessibility_label="Show Life window",
    ),
    WindowSpec(
        key="mandel",
        feature_attr="_mandel_feature",
        toggle_attr="mandel_toggle_window",
        action_name="win_mandel",
        action_label="Show Mandelbrot Window",
        task_panel_button_id="show_mandel",
        task_panel_label="Mandelbrot",
        task_panel_style="round",
        task_panel_slot_index=4,
        tab_before_showcase=False,
        accessibility_label="Show Mandelbrot window",
    ),
)

RUNTIME_SCENE_SPECS = (
    RuntimeSceneSpec(
        scene_name="main",
        pristine_asset="demo_features/data/images/backdrop.jpg",
        bind_escape_to_exit=True,
        prewarm=False,
    ),
    RuntimeSceneSpec(
        scene_name="control_showcase",
        pristine_asset="demo_features/data/images/backdrop.jpg",
        bind_escape_to_exit=True,
        prewarm=True,
    ),
)

ACTION_SPECS = (
    ActionSpec(
        action_id="exit",
        label="Exit",
        kind="exit",
        category="File",
    ),
    ActionSpec(
        action_id="nav_main",
        label="Go to Main Scene",
        kind="scene_nav",
        target="main",
        category="Scenes",
    ),
    ActionSpec(
        action_id="nav_showcase",
        label="Go to Controls Showcase",
        kind="scene_nav",
        target="control_showcase",
        category="Scenes",
    ),
    ActionSpec(
        action_id="palette_open",
        label="Open Command Palette (F5)",
        kind="palette_open",
        category=None,
    ),
)

STATIC_ACCESSIBILITY_SPECS = (
    StaticAccessibilitySpec(
        control_attr="exit_button",
        role="button",
        label="Exit",
    ),
    StaticAccessibilitySpec(
        control_attr="showcase_button",
        role="button",
        label="Showcase",
    ),
)

DEMO_BOOTSTRAP_CONFIG = HostApplicationConfig(
    display_size=(1920, 1080),
    window_title="gui_do demo",
    fonts={
        "default": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 14},
        "window": "demo_features/data/fonts/Gimbot.ttf",
    },
    font_role_specs=(
        {"title": {"size": 14, "font": "window"}},
    ),
    cursors=(
        CursorSpec("normal", "demo_features/data/cursors/cursor.png", (1, 1)),
        CursorSpec("hand", "demo_features/data/cursors/hand.png", (12, 12)),
    ),
    scene_specs=SCENE_SPECS,
    feature_specs=FEATURE_SPECS,
    window_specs=WINDOW_SPECS,
    runtime_scene_specs=RUNTIME_SCENE_SPECS,
    action_specs=ACTION_SPECS,
    static_accessibility_specs=STATIC_ACCESSIBILITY_SPECS,
    initial_scene_name="main",
    scene_roots=(
        SceneRootSpec("control_showcase", "control_showcase_root", draw_background=False),
    ),
    telemetry=TelemetryConfig(enabled=False, live_analysis_enabled=True, file_logging_enabled=False),
    target_fps=120,
)
