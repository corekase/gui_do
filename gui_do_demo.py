import pygame
from demo_features.feature_abstractions import (
    apply_window_toggle_accessibility,
    collect_window_toggle_controls,
)

from demo_features.demo_config import (
    ACTION_SPECS,
    FEATURE_SPECS,
    RUNTIME_SCENE_SPECS,
    SCENE_SPECS,
    STATIC_ACCESSIBILITY_SPECS,
    WINDOW_SPECS,
)

from gui_do import (
    GuiApplication,
    create_display,
    ActionRegistry,
    FontRoleRegistry,
    SceneTransitionManager,
    SceneTransitionStyle,
    apply_scene_setup_specs,
    CommandPaletteManager,
    setup_standard_font_roles,
    register_standard_actions,
)
from gui_do.features.feature_lifecycle import FeatureWindowPresentationModel, ScenePresentationModel


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
        self.scene_transitions = SceneTransitionManager(self.app, default_style=SceneTransitionStyle.FADE, default_duration=0.5)
        apply_scene_setup_specs(
            self.app,
            SCENE_SPECS,
            scene_transitions=self.scene_transitions,
        )
        self.scene_presentation = ScenePresentationModel(self)

        self.control_showcase_root = self.scene_presentation.ensure_scene_root(
            "control_showcase",
            control_id="control_showcase_root",
            draw_background=False,
        )

        self._instantiate_features()
        self.window_presentation = FeatureWindowPresentationModel(
            self,
            tile_windows=self.app.tile_windows,
        )
        self._configure_window_presentation()
        self._register_features()

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
        self.window_presentation.sync_initial_visibility(visible=False)
        self._apply_runtime_scene_pristine_assets()
        register_standard_actions(
            self.app.actions,
            app=self.app,
            scene_transitions=self.scene_transitions,
            palette_manager=self._palette_manager,
            window_toggles=self.window_presentation.action_callbacks(),
        )
        self._bind_runtime_scene_exit_keys()

        self.app.bind_features_runtime(self)
        self._prewarm_runtime_scenes()

        window_toggle_controls = self._collect_window_toggle_controls()
        base_controls = self._build_main_tab_order_controls(window_toggle_controls)
        self._apply_main_accessibility(base_controls)
        self.app.configure_features_accessibility(self, len(base_controls))
        self.app.switch_scene("main")

    def _instantiate_features(self) -> None:
        # Declarative feature specs keep host bootstrap compact and stable.
        for spec in FEATURE_SPECS:
            setattr(self, spec.attr_name, spec.factory())

    def _register_features(self) -> None:
        for spec in FEATURE_SPECS:
            feature = getattr(self, spec.attr_name)
            self.app.register_feature(feature, host=self)

    def _configure_window_presentation(self) -> None:
        for spec in WINDOW_SPECS:
            self.window_presentation.register_feature_window(
                spec.key,
                feature_attr=spec.feature_attr,
                toggle_attr=spec.toggle_attr,
                action_name=spec.action_name,
                action_label=spec.action_label,
                task_panel_button_id=spec.task_panel_button_id,
                task_panel_label=spec.task_panel_label,
                task_panel_style=spec.task_panel_style,
                task_panel_slot_index=spec.task_panel_slot_index,
                tab_before_showcase=spec.tab_before_showcase,
                accessibility_label=spec.accessibility_label,
            )

    def _apply_runtime_scene_pristine_assets(self) -> None:
        for spec in RUNTIME_SCENE_SPECS:
            if not spec.pristine_asset:
                continue
            self.app.set_pristine(spec.pristine_asset, scene_name=spec.scene_name)

    def _bind_runtime_scene_exit_keys(self) -> None:
        for spec in RUNTIME_SCENE_SPECS:
            if not spec.bind_escape_to_exit:
                continue
            self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene=spec.scene_name)

    def _prewarm_runtime_scenes(self) -> None:
        for spec in RUNTIME_SCENE_SPECS:
            if not spec.prewarm:
                continue
            self.app.prewarm_scene(spec.scene_name)

    def run(self) -> int:
        """Run demo via app entrypoint boilerplate."""
        return self.app.run_entrypoint(target_fps=120)

    def _register_app_actions(self) -> None:
        """Declare all top-level demo actions on the shared ActionRegistry."""
        r = self.action_registry
        for spec in ACTION_SPECS:
            handler = self._build_action_handler(spec)
            if spec.category is None:
                r.declare(spec.action_id, spec.label, handler)
            else:
                r.declare(spec.action_id, spec.label, handler, category=spec.category)
        self.window_presentation.declare_actions(r, category="Windows")

    def _build_action_handler(self, spec):
        builders = {
            "exit": self._build_exit_action_handler,
            "scene_nav": self._build_scene_nav_action_handler,
            "palette_open": self._build_palette_open_action_handler,
        }
        builder = builders.get(str(spec.kind))
        if builder is None:
            raise ValueError(f"Unsupported action kind: {spec.kind}")
        return builder(spec)

    def _build_exit_action_handler(self, _spec):
        return lambda _ctx, _ev: (setattr(self.app, "running", False) or True)

    def _build_scene_nav_action_handler(self, spec):
        scene_name = str(spec.target)
        return lambda _ctx, _ev: (self.scene_transitions.go(scene_name) or True)

    def _build_palette_open_action_handler(self, _spec):
        return lambda _ctx, _ev: (self._palette_manager.show(self.app) or True)

    def _collect_window_toggle_controls(self) -> list[tuple[object, object]]:
        return collect_window_toggle_controls(self, self.window_presentation)

    def _build_main_tab_order_controls(self, window_toggle_controls: list[tuple[object, object]]) -> list[object]:
        before_showcase = [control for binding, control in window_toggle_controls if binding.tab_before_showcase]
        after_showcase = [control for binding, control in window_toggle_controls if not binding.tab_before_showcase]
        base_controls = [self.exit_button]
        base_controls.extend(before_showcase)
        base_controls.append(self.showcase_button)
        base_controls.extend(after_showcase)
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)
        return base_controls

    def _apply_main_accessibility(self, base_controls: list[object]) -> None:
        _ = base_controls
        for spec in STATIC_ACCESSIBILITY_SPECS:
            control = getattr(self, spec.control_attr, None)
            if control is None:
                continue
            control.set_accessibility(role=spec.role, label=spec.label)
        apply_window_toggle_accessibility(self, self.window_presentation, role="toggle")

    def go_to_control_showcase(self) -> None:
        self.scene_transitions.go("control_showcase")

    def go_to_main(self) -> None:
        self.scene_transitions.go("main")

def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
