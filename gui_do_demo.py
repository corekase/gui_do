import pygame
from pygame import Rect
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature
from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from demo_features.main_demo_feature import MainDemoFeature
from demo_features.controls_demo_feature import ControlsShowcaseFeature
from demo_features.systems_demo_feature import SystemsDemoFeature

from gui_do import (
    GuiApplication,
    create_display,
    PanelControl,
    TaskPanelControl,
    ActionRegistry,
    FontRoleRegistry,
    SceneTransitionManager,
    SceneTransitionStyle,
    CommandPaletteManager,
    setup_standard_font_roles,
    register_standard_actions,
    set_window_visible_state,
    toggle_window_visibility,
)


class GuiDoDemo:
        # Add font roles for all controls (full coverage)
        # ---
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    TASK_PANEL_CONTROL_FONT_ROLE = "screen.main.task_panel.control"
    SCREEN_TITLE_FONT_ROLE = "screen.main.title"

    def __init__(self) -> None:
        """Initialize pygame, app services, scene state, and demo UI."""
        self.screen = create_display((1920, 1080))
        pygame.display.set_caption("gui_do demo")

        self.screen_rect = self.screen.get_rect()
        # Create the font role registry ONCE and register all roles BEFORE creating the app
        self.font_roles = FontRoleRegistry()
        fonts = {
            "default": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 14},  # Fallback for undefined roles
            "window": "demo_features/data/fonts/Gimbot.ttf",  # All window titles
        }
        setup_standard_font_roles(
            self.font_roles,
            fonts,
            {
                "title": {"size": 14, "font": "window"},
            },
        )
        # Pass the font role registry to the application so it is used globally
        self.app = GuiApplication(self.screen, font_roles=self.font_roles)
        self.app.register_cursor("normal", "demo_features/data/cursors/cursor.png", (1, 1))
        self.app.register_cursor("hand", "demo_features/data/cursors/hand.png", (12, 12))
        self.app.set_cursor("normal")
        self.app.configure_telemetry(
            enabled=False,
            live_analysis_enabled=True,
            file_logging_enabled=False,
        )


        self.app.layout.set_anchor_bounds(self.screen_rect)
        self.app.create_scene("main", pretty_name="Desktop Demo")
        self.app.create_scene("control_showcase", pretty_name="Control Showcase")
        self.scene_transitions = SceneTransitionManager(self.app, default_style=SceneTransitionStyle.FADE, default_duration=0.5)
        self.scene_transitions.set_style("control_showcase", SceneTransitionStyle.SLIDE_LEFT, duration=0.5)
        self.scene_transitions.set_style("main", SceneTransitionStyle.SLIDE_RIGHT, duration=0.5)
        self._task_panels_by_scene: dict[str, TaskPanelControl] = {}
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False, scene_name="main")
        self.app.set_window_tiling_enabled(True, relayout=False, scene_name="main")
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False, scene_name="control_showcase")
        self.app.set_window_tiling_enabled(True, relayout=False, scene_name="control_showcase")
        self.app.switch_scene("main")

        # Feature registry keeps concerns isolated behind a small lifecycle contract.
        # A single backdrop instance with scene_name=None runs in all scenes so
        # shape positions and velocities are shared and continuous across scene switches.
        self._shapes_feature = BouncingShapesBackdropFeature(
            circle_count=12,
            square_count=12,
            octagon_count=12,
            star_count=12,
        )
        self._main_feature = MainDemoFeature()
        self._life_feature = LifeSimulationFeature()
        self._controls_feature = ControlsShowcaseFeature()
        self._mandel_feature = MandelbrotRenderFeature()
        self._systems_feature = SystemsDemoFeature()
        for feature in [
            self._main_feature,
            self._shapes_feature,
            self._life_feature,
            self._controls_feature,
            self._mandel_feature,
            self._systems_feature,
        ]:
            self.app.register_feature(feature, host=self)

        self._build_control_showcase_scene()

        # ActionRegistry must be created before build_features so MainDemoFeature
        # can access it during its build hook.
        self.action_registry = ActionRegistry()

        # Create a global palette manager accessible from all scenes
        self._palette_manager = CommandPaletteManager(self.app.overlay, self.app)
        self._palette_manager.enable_builtin_scene_and_window_entries(
            self.app,
            on_scene_selected=self.scene_transitions.go,
        )

        self._register_app_actions()

        self.app.build_features(self)
        self.life_window = self._life_feature.window
        self.mandel_window = self._mandel_feature.window
        self.systems_window = self._systems_feature.window
        self.life_window.visible = False
        self.mandel_window.visible = False
        self.systems_window.visible = False
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="main")
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="control_showcase")
        register_standard_actions(
            self.app.actions,
            app=self.app,
            scene_transitions=self.scene_transitions,
            palette_manager=self._palette_manager,
            window_toggles={
                "win_life": (lambda: self.life_window, "set_life_window_visible"),
                "win_mandel": (lambda: self.mandel_window, "set_mandel_window_visible"),
                "win_systems": (lambda: self.systems_window, "set_systems_window_visible"),
            },
        )
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="control_showcase")

        self.app.bind_features_runtime(self)
        self.app.prewarm_scene("control_showcase")

        base_controls = [
            self.exit_button,
            self.systems_toggle_window,
            self.showcase_button,
            self.life_toggle_window,
            self.mandel_toggle_window,
        ]
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)

        self.exit_button.set_accessibility(role="button", label="Exit")
        self.systems_toggle_window.set_accessibility(role="toggle", label="Show Systems window")
        self.showcase_button.set_accessibility(role="button", label="Showcase")
        self.life_toggle_window.set_accessibility(role="toggle", label="Show Life window")
        self.mandel_toggle_window.set_accessibility(role="toggle", label="Show Mandelbrot window")
        self.app.configure_features_accessibility(self, len(base_controls))
        self.app.switch_scene("main")

    def ensure_scene_task_panel(
        self,
        scene_name: str,
        *,
        control_id: str,
        height: int = 50,
        hidden_peek_pixels: int = 6,
        animation_step_px: int = 8,
        dock_bottom: bool = True,
        auto_hide: bool = True,
    ) -> TaskPanelControl:
        panel = self._task_panels_by_scene.get(scene_name)
        if panel is not None:
            return panel
        panel = self.app.add(
            TaskPanelControl(
                control_id,
                Rect(0, self.screen_rect.height - int(height), self.screen_rect.width, int(height)),
                auto_hide=auto_hide,
                hidden_peek_pixels=hidden_peek_pixels,
                animation_step_px=animation_step_px,
                dock_bottom=dock_bottom,
            ),
            scene_name=scene_name,
        )
        self._task_panels_by_scene[scene_name] = panel
        return panel

    def register_scene_task_panel(self, scene_name: str, panel: TaskPanelControl) -> None:
        self._task_panels_by_scene[scene_name] = panel

    def get_scene_task_panel(self, scene_name: str) -> TaskPanelControl | None:
        return self._task_panels_by_scene.get(scene_name)

    def _build_control_showcase_scene(self) -> None:
        """Build the control showcase scene and provide a way back to main."""
        self.control_showcase_root = self.app.add(
            PanelControl(
                "control_showcase_root",
                Rect(0, 0, self.screen_rect.width, self.screen_rect.height),
                draw_background=False,
            ),
            scene_name="control_showcase",
        )

    def run(self) -> int:
        """Run demo via app entrypoint boilerplate."""
        return self.app.run_entrypoint(target_fps=120)

    def _register_app_actions(self) -> None:
        """Declare all top-level demo actions on the shared ActionRegistry."""
        r = self.action_registry
        r.declare("exit",                "Exit",                          lambda _ctx, _ev: (setattr(self.app, "running", False) or True), category="File")
        r.declare(
            "nav_main",
            "Go to Main Scene",
            lambda _ctx, _ev: (self.scene_transitions.go("main") or True),
            category="Scenes",
        )
        r.declare(
            "nav_showcase",
            "Go to Controls Showcase",
            lambda _ctx, _ev: (self.scene_transitions.go("control_showcase") or True),
            category="Scenes",
        )
        r.declare("win_life",            "Show Life Window",              lambda _ctx, _ev: (self.set_life_window_visible(True) or True),  category="Windows")
        r.declare("win_mandel",          "Show Mandelbrot Window",        lambda _ctx, _ev: (self.set_mandel_window_visible(True) or True), category="Windows")
        r.declare("palette_open",        "Open Command Palette (F5)",     lambda _ctx, _ev: (self._palette_manager.show(self.app) or True))

    def go_to_control_showcase(self) -> None:
        self.scene_transitions.go("control_showcase")

    def go_to_main(self) -> None:
        self.scene_transitions.go("main")


    def set_life_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        set_window_visible_state(self.life_window, visible, from_toggle=from_toggle, tile_windows=getattr(self.app, 'tile_windows', None))

    def set_mandel_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        set_window_visible_state(self.mandel_window, visible, from_toggle=from_toggle, tile_windows=getattr(self.app, 'tile_windows', None))

    def set_systems_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        set_window_visible_state(self.systems_window, visible, from_toggle=from_toggle, tile_windows=getattr(self.app, 'tile_windows', None))

def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
