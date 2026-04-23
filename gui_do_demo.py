import pygame
from pygame import Rect
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature
from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.bouncing_circles_demo_part import BouncingCirclesBackdropFeature

from gui import (
    GuiApplication,
    PanelControl,
    ButtonControl,
    TaskPanelControl,
    ToggleControl,
)


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    TASK_PANEL_CONTROL_FONT_ROLE = "screen.main.task_panel.control"

    def __init__(self) -> None:
        """Initialize pygame, app services, scene state, and demo UI."""
        pygame.init()
        flags = pygame.FULLSCREEN | pygame.SCALED
        try:
            self.screen = pygame.display.set_mode((1920, 1080), flags=flags, vsync=1)
        except TypeError:
            self.screen = pygame.display.set_mode((1920, 1080), flags=flags)
        pygame.display.set_caption("gui_do demo")

        self.screen_rect = self.screen.get_rect()
        self.app = GuiApplication(self.screen)
        self.app.layout.set_anchor_bounds(self.screen_rect)
        self.app.create_scene("main")
        self.app.switch_scene("main")
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False)
        self.app.set_window_tiling_enabled(True, relayout=False)

        # Feature registry keeps concerns isolated behind a small lifecycle contract.
        self._circles_feature = BouncingCirclesBackdropFeature(circle_count=30)
        self._life_feature = LifeSimulationFeature()
        self._mandel_feature = MandelbrotRenderFeature()
        self._demo_features = [self._circles_feature, self._life_feature, self._mandel_feature]
        for feature in self._demo_features:
            self.app.register_part(feature, host=self)

        self._build_main_scene()
        self.app.set_pristine("backdrop.jpg", scene_name="main")
        self.app.actions.register_action("exit", lambda _event: (setattr(self.app, "running", False) or True))
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")
        self.app.bind_parts_runtime(self)

        base_controls = [
            self.exit_button,
            self.life_toggle_window,
            self.mandel_toggle_window,
        ]
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)

        self.exit_button.set_accessibility(role="button", label="Exit")
        self.life_toggle_window.set_accessibility(role="toggle", label="Show Life window")
        self.mandel_toggle_window.set_accessibility(role="toggle", label="Show Mandelbrot window")
        self.app.configure_parts_accessibility(self, len(base_controls))

    def _life_part(self):
        """Return the Life feature instance, creating/wiring it on demand."""
        part = getattr(self, "_life_feature", None)
        if part is None:
            part = LifeSimulationFeature()
            self._life_feature = part
        if getattr(part, "demo", None) is None:
            part.demo = self  # Ensure part has access to demo for callbacks
        return part

    def _circles_part(self):
        """Return the circles backdrop feature, creating one when absent."""
        part = getattr(self, "_circles_feature", None)
        if part is None:
            part = BouncingCirclesBackdropFeature(circle_count=30)
            self._circles_feature = part
        return part

    def _mandel_part(self):
        """Return the Mandelbrot feature instance, creating/wiring it on demand."""
        part = getattr(self, "_mandel_feature", None)
        if part is None:
            part = MandelbrotRenderFeature()
            self._mandel_feature = part
        if getattr(part, "demo", None) is None:
            part.demo = self  # Ensure part has access to demo for callbacks
        return part

    def _register_screen_font_roles(self) -> None:
        """Register screen-owned font roles for non-part scene composition."""
        self.app.register_font_role(
            self.TASK_PANEL_CONTROL_FONT_ROLE,
            size=16,
            file_path="data/fonts/Ubuntu-B.ttf",
            system_name="arial",
            scene_name="main",
        )

    # ---------------------------------------------------------------------
    # Scene construction and widget composition.
    # ---------------------------------------------------------------------
    def _build_main_scene(self) -> None:
        """Build root scene container, windows, and bottom task panel controls."""
        self._register_screen_font_roles()
        self.root = self.app.add(
            PanelControl("main_root", Rect(0, 0, self.screen_rect.width, self.screen_rect.height), draw_background=False),
            scene_name="main",
        )
        self.app.build_parts(self)
        self.life_window = self._life_part().window
        self.mandel_window = self._mandel_part().window
        self.life_window.visible = False
        self.mandel_window.visible = False
        self.task_panel = self.app.add(
            TaskPanelControl(
                "task_panel",
                Rect(0, self.screen_rect.height - 50, self.screen_rect.width, 50),
                auto_hide=True,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
            ),
            scene_name="main",
        )
        self.app.layout.set_linear_properties(
            anchor=(16, self.screen_rect.height - 40),
            item_width=110,
            item_height=30,
            spacing=10,
            horizontal=True,
        )

        def _tile_visible_windows(newly_visible=None) -> None:
            if not self.app.read_window_tiling_settings().get("enabled", False):
                return
            if newly_visible is None:
                windows = [self.life_window, self.mandel_window]
                newly_visible = [window for window in windows if window.visible]
            self.app.tile_windows(newly_visible=newly_visible)

        def _on_life_toggle(pushed: bool) -> None:
            self.life_window.visible = bool(pushed)
            if pushed:
                _tile_visible_windows(newly_visible=[self.life_window])
            else:
                _tile_visible_windows()

        def _on_mandel_toggle(pushed: bool) -> None:
            self.mandel_window.visible = bool(pushed)
            if pushed:
                _tile_visible_windows(newly_visible=[self.mandel_window])
            else:
                _tile_visible_windows()

        self.exit_button = self.task_panel.add(
            ButtonControl(
                "exit",
                self.app.layout.linear(0),
                "Exit",
                lambda: setattr(self.app, "running", False),
                style="angle",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.life_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_life",
                self.app.layout.linear(1),
                "Life",
                "Life",
                pushed=False,
                on_toggle=_on_life_toggle,
                style="round",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.mandel_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_mandel",
                self.app.layout.linear(2),
                "Mandelbrot",
                "Mandelbrot",
                pushed=False,
                on_toggle=_on_mandel_toggle,
                style="round",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        _tile_visible_windows()

    def run(self) -> None:
        """Run demo engine and perform shutdown cleanup on exit."""
        self.app.run(target_fps=120)
        self._mandel_part().shutdown_runtime(self)
        pygame.quit()


def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
