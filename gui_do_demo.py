import pygame
from pygame import Rect
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature
from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from demo_features.main_demo_feature import MainDemoFeature
from demo_features.controls_demo_feature import ControlsShowcaseFeature
from demo_features.system_window_demo_feature import SystemWindowDemoFeature
from demo_features.new_systems_demo_feature import NewSystemsDemoFeature

from gui_do import (
    GuiApplication,
    create_display,
    PanelControl,
    FontRoleRegistry,
    SceneTransitionManager,
    SceneTransitionStyle,
)


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    TASK_PANEL_CONTROL_FONT_ROLE = "screen.main.task_panel.control"
    SCREEN_TITLE_FONT_ROLE = "screen.main.title"

    def __init__(self) -> None:
        """Initialize pygame, app services, scene state, and demo UI."""
        pygame.init()
        self.screen = create_display((1920, 1080))
        pygame.display.set_caption("gui_do demo")

        self.screen_rect = self.screen.get_rect()
        self.app = GuiApplication(self.screen)
        self.app.register_cursor("normal", "demo_features/data/cursors/cursor.png", (1, 1))
        self.app.register_cursor("hand", "demo_features/data/cursors/hand.png", (12, 12))
        self.app.set_cursor("normal")
        self.app.configure_telemetry(
            enabled=False,
            live_analysis_enabled=True,
            file_logging_enabled=False,
        )

        # Font roles are defined here during demo startup, independent of any
        # scene.  Features bind local role names to these pre-defined global
        # roles (via Feature.use_font_roles) instead of redefining sizes/files.
        self.font_roles = FontRoleRegistry()
        self.font_roles.define("body",    size=16, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("title",   size=14, file_path="demo_features/data/fonts/Ubuntu-B.ttf", bold=True)
        self.font_roles.define("display", size=72, file_path="demo_features/data/fonts/Gimbot.ttf")
        self.font_roles.define("controls.label", size=14, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("controls.control", size=15, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("life.window_title", size=14, file_path="demo_features/data/fonts/Gimbot.ttf", bold=True)
        self.font_roles.define("life.control", size=16, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("mandelbrot.window_title", size=14, file_path="demo_features/data/fonts/Gimbot.ttf", bold=True)
        self.font_roles.define("mandelbrot.control", size=16, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("mandelbrot.caption", size=14, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("mandelbrot.status", size=16, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("system.window_title", size=14, file_path="demo_features/data/fonts/Gimbot.ttf", bold=True)
        self.font_roles.define("system.control", size=15, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("system.label", size=13, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define("system.status", size=13, file_path="demo_features/data/fonts/Ubuntu-B.ttf")
        self.font_roles.define(
            self.TASK_PANEL_CONTROL_FONT_ROLE,
            size=16,
            file_path="demo_features/data/fonts/Ubuntu-B.ttf",
        )
        self.font_roles.define(
            self.SCREEN_TITLE_FONT_ROLE,
            size=72,
            file_path="demo_features/data/fonts/Gimbot.ttf",
        )

        self.app.layout.set_anchor_bounds(self.screen_rect)
        self.app.create_scene("main")
        self.app.create_scene("control_showcase")
        self.scene_transitions = SceneTransitionManager(self.app, default_style=SceneTransitionStyle.FADE, default_duration=0.22)
        self.scene_transitions.set_style("control_showcase", SceneTransitionStyle.SLIDE_LEFT, duration=0.22)
        self.scene_transitions.set_style("main", SceneTransitionStyle.SLIDE_RIGHT, duration=0.22)
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
        self._system_feature = SystemWindowDemoFeature()
        self._new_systems_feature = NewSystemsDemoFeature()
        for feature in [
            self._main_feature,
            self._shapes_feature,
            self._life_feature,
            self._controls_feature,
            self._mandel_feature,
            self._system_feature,
            self._new_systems_feature,
        ]:
            self.app.register_feature(feature, host=self)

        self._build_control_showcase_scene()
        self.app.build_features(self)
        self.life_window = self._life_feature.window
        self.mandel_window = self._mandel_feature.window
        self.system_window = self._system_feature.window
        self.new_systems_window = self._new_systems_feature.window
        self.life_window.visible = False
        self.mandel_window.visible = False
        self.system_window.visible = False
        self.new_systems_window.visible = False
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="main")
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="control_showcase")
        self.app.actions.register_action("exit", lambda _event: (setattr(self.app, "running", False) or True))
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="control_showcase")
        self.app.bind_features_runtime(self)
        self.app.prewarm_scene("control_showcase")

        base_controls = [
            self.exit_button,
            self.showcase_button,
            self.life_toggle_window,
            self.mandel_toggle_window,
            self.system_toggle_window,
            self.new_systems_toggle_window,
            self.inbox_button,
        ]
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)

        self.exit_button.set_accessibility(role="button", label="Exit")
        self.showcase_button.set_accessibility(role="button", label="Showcase")
        self.life_toggle_window.set_accessibility(role="toggle", label="Show Life window")
        self.mandel_toggle_window.set_accessibility(role="toggle", label="Show Mandelbrot window")
        self.system_toggle_window.set_accessibility(role="toggle", label="Show System window")
        self.new_systems_toggle_window.set_accessibility(role="toggle", label="Show New Systems window")
        self.inbox_button.set_accessibility(role="button", label="Open notification panel")
        self.app.configure_features_accessibility(self, len(base_controls))
        self.app.switch_scene("main")

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
        """Run demo with final-layer app error handling and return OS exit code."""
        return self.app.run_entrypoint(target_fps=120)

    def go_to_control_showcase(self) -> None:
        self.scene_transitions.go("control_showcase")

    def go_to_main(self) -> None:
        self.scene_transitions.go("main")

    def set_life_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.life_window.visible = show
        if not from_toggle and self.life_toggle_window is not None:
            self.life_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.life_window] if show else None)

    def set_mandel_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.mandel_window.visible = show
        if not from_toggle and self.mandel_toggle_window is not None:
            self.mandel_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.mandel_window] if show else None)

    def set_system_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.system_window.visible = show
        if not from_toggle and self.system_toggle_window is not None:
            self.system_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.system_window] if show else None)

    def set_new_systems_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.new_systems_window.visible = show
        if not from_toggle and self.new_systems_toggle_window is not None:
            self.new_systems_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.new_systems_window] if show else None)

    def _open_file_dialog_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.open_file_dialog()

    def _save_file_dialog_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.save_file_dialog()

    def _open_notifications_panel_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.show_notifications_panel()

    def _publish_system_test_event_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.publish_test_notification()


def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    raise SystemExit(GuiDoDemo().run())


if __name__ == "__main__":
    main()
