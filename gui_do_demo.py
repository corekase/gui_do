from typing import Optional, Set, Tuple

import pygame
from pygame import Rect
from demo_parts.mandel_events import (
    MANDEL_STATUS_SCOPE,
    MANDEL_STATUS_TOPIC,
)
from demo_parts.life_simulation_feature import LifeSimulationFeature
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature

from gui import (
    GuiApplication,
    UiEngine,
    PanelControl,
    LabelControl,
    ButtonControl,
    CanvasControl,
    SliderControl,
    TaskPanelControl,
    ToggleControl,
    WindowControl,
    LayoutAxis,
    ObservableValue,
    PresentationModel,
)

class _MandelPresentationModel(PresentationModel):
    """Presentation state for Mandelbrot controls and status text."""

    def __init__(self) -> None:
        super().__init__()
        self.status_text = ObservableValue("Mandelbrot: idle")

    def set_status(self, text: str) -> None:
        self.status_text.value = str(text)


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    # Simulation/model constants.
    neighbours = (
        (-1, -1), (-1,  0), (-1,  1),
        ( 0, -1),           ( 0,  1),
        ( 1, -1), ( 1,  0), ( 1,  1),
    )

    mandel_cols = (
        (66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
        (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
        (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
        (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
    )
    _MANDEL_FAILURE_PREVIEW_MIN = 1
    _MANDEL_FAILURE_PREVIEW_MAX = 20

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
        self.scene_scheduler = self.app.get_scene_scheduler("main")
        self.life_scheduler = self.scene_scheduler
        self.mandel_scheduler = self.scene_scheduler

        self.life_cells: Set[Tuple[int, int]] = set()
        self.life_origin = [0, 0]
        self.life_cell_size = 12
        self.life_dragging = False
        self._life_zoom_slider_last_value = 5
        self.mandel_task_ids: Set[str] = set()
        self.mandel_task_id_pool = ("iter", "recu", "1", "2", "3", "4", "can1", "can2", "can3", "can4")
        self.max_iter = 96
        self.mandel_model = _MandelPresentationModel()
        self._mandel_status_topic = MANDEL_STATUS_TOPIC
        self._mandel_status_scope = MANDEL_STATUS_SCOPE
        self._mandel_status_subscription = None
        self._mandel_status_bus_ready = False
        self._mandel_running_mode: Optional[str] = None
        self._mandel_failure_preview_limit = 3

        # Keep gui constructors on the demo so demo_parts modules can remain gui-independent.
        self._window_control_cls = WindowControl
        self._label_control_cls = LabelControl
        self._button_control_cls = ButtonControl
        self._canvas_control_cls = CanvasControl
        self._slider_control_cls = SliderControl
        self._toggle_control_cls = ToggleControl
        self._layout_axis_cls = LayoutAxis

        # Feature registry keeps concerns isolated behind a small lifecycle contract.
        self._demo_features = [
            LifeSimulationFeature(),
            MandelbrotRenderFeature(),
        ]
        # Backward-compatible alias used by existing tests.
        self._feature_parts = self._demo_features

        self._build_main_scene()
        self.app.set_pristine("backdrop.jpg", scene_name="main")
        self._bind_runtime()
        self.app.set_screen_lifecycle(
            preamble=self._screen_preamble,
            event_handler=self._screen_event_handler,
            postamble=self._screen_postamble,
        )

        self.app.update = self._update

    # ---------------------------------------------------------------------
    # Scene construction and widget composition.
    # ---------------------------------------------------------------------
    def _build_main_scene(self) -> None:
        """Build root scene container, windows, and bottom task panel controls."""
        self.root = self.app.add(
            PanelControl("main_root", Rect(0, 0, self.screen_rect.width, self.screen_rect.height), draw_background=False),
            scene_name="main",
        )
        for feature in self._demo_features:
            feature.build(self)
        self.life_window.visible = True
        self.mandel_window.visible = True
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
        self.quit_button = self.task_panel.add(
            ButtonControl(
                "quit",
                self.app.layout.linear(0),
                "Quit",
                self._exit_app,
                style="angle",
            )
        )
        self.life_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_life",
                self.app.layout.linear(1),
                "Life",
                "Life",
                pushed=True,
                on_toggle=self._toggle_life_window,
                style="round",
            )
        )
        self.mandel_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_mandel",
                self.app.layout.linear(2),
                "Mandelbrot",
                "Mandelbrot",
                pushed=True,
                on_toggle=self._toggle_mandel_window,
                style="round",
            )
        )
        self._tile_visible_windows()

    def _set_text(self, label: LabelControl, size: int = 16) -> LabelControl:
        """Apply consistent demo text styling to a label and return it."""
        label.title = False
        label.text_size = size
        return label

    def _format_mandel_help_text(self) -> str:
        """Return the dynamic help string shown above the Mandelbrot canvas."""
        return MandelbrotRenderFeature.format_help_text(self)

    def _set_mandel_help_label(self) -> None:
        """Refresh Mandel help label text when runtime options change."""
        MandelbrotRenderFeature.set_help_label(self)

    def set_mandel_failure_preview_limit(self, limit: int) -> int:
        """Set Mandel failure preview limit and return the clamped effective value."""
        return MandelbrotRenderFeature.set_failure_preview_limit(self, limit)

    def _adjust_mandel_failure_preview_limit(self, delta: int) -> bool:
        """Adjust failure preview limit and publish user-facing status feedback."""
        return MandelbrotRenderFeature.adjust_failure_preview_limit(self, delta)

    def _set_life_zoom_label(self) -> None:
        """Render the current life-cell zoom level into the zoom label."""
        LifeSimulationFeature.set_life_zoom_label(self)

    def _build_life_window(self) -> None:
        """Create the Game of Life window, canvas, and bottom control strip."""
        LifeSimulationFeature.build_window(
            self,
            window_control_cls=self._window_control_cls,
            canvas_control_cls=self._canvas_control_cls,
            button_control_cls=self._button_control_cls,
            toggle_control_cls=self._toggle_control_cls,
            slider_control_cls=self._slider_control_cls,
            label_control_cls=self._label_control_cls,
            layout_axis_cls=self._layout_axis_cls,
        )

    def _build_mandelbrot_window(self) -> None:
        """Create the Mandelbrot window, canvases, controls, and status labels."""
        MandelbrotRenderFeature.build_window(
            self,
            window_control_cls=self._window_control_cls,
            label_control_cls=self._label_control_cls,
            canvas_control_cls=self._canvas_control_cls,
            button_control_cls=self._button_control_cls,
        )

    def _bind_runtime(self) -> None:
        """Register keyboard actions, event bus bindings, and accessibility metadata."""
        self.app.actions.register_action("exit", lambda _event: (self._exit_app() or True))
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")
        for feature in self._demo_features:
            feature.bind_runtime(self)
        self._configure_focus_and_accessibility()

    # ---------------------------------------------------------------------
    # Status presentation and event-bus synchronization.
    # ---------------------------------------------------------------------
    def _on_mandel_status_changed(self, text: str) -> None:
        """Apply presentation-model status updates to the visible label."""
        MandelbrotRenderFeature.on_status_changed(self, text)

    def _on_mandel_status_event(self, payload) -> None:
        """Handle event-bus Mandel status payload and update presentation model."""
        MandelbrotRenderFeature.on_status_event(self, payload)

    def _format_mandel_status(self, payload) -> str:
        """Normalize Mandel status payloads into a user-facing status line."""
        return MandelbrotRenderFeature.format_status(self, payload)

    def _publish_mandel_event(self, kind: str, detail: Optional[str] = None) -> None:
        """Publish Mandel status event or fall back to direct model update."""
        MandelbrotRenderFeature.publish_event(self, kind, detail)

    def _publish_mandel_running_status(self) -> None:
        """Emit running status text with current in-flight task count."""
        MandelbrotRenderFeature.publish_running_status(self)

    def _format_mandel_failure_summary(self, failed_details) -> str:
        """Build a deterministic, capped summary string for Mandel task failures."""
        return MandelbrotRenderFeature.format_failure_summary(self, failed_details)

    # ---------------------------------------------------------------------
    # Accessibility, visibility toggles, and window tiling.
    # ---------------------------------------------------------------------
    def _configure_focus_and_accessibility(self) -> None:
        """Configure tab order and accessibility labels for interactive controls."""
        base_controls = [
            self.quit_button,
            self.life_toggle_window,
            self.mandel_toggle_window,
        ]
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)

        self.quit_button.set_accessibility(role="button", label="Quit")
        self.life_toggle_window.set_accessibility(role="toggle", label="Show Life window")
        self.mandel_toggle_window.set_accessibility(role="toggle", label="Show Mandelbrot window")
        next_index = len(base_controls)
        for feature in self._demo_features:
            next_index = feature.configure_accessibility(self, next_index)

    def _toggle_life_window(self, pushed: bool) -> None:
        """Show or hide Life window and retile visible windows."""
        self.life_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.life_window])
        else:
            self._tile_visible_windows()

    def _toggle_mandel_window(self, pushed: bool) -> None:
        """Show or hide Mandel window and retile visible windows."""
        self.mandel_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.mandel_window])
        else:
            self._tile_visible_windows()

    def _visible_windows_for_tiling(self):
        """Return currently visible demo windows eligible for tiling."""
        windows = [self.life_window, self.mandel_window]
        return [window for window in windows if window.visible]

    def _tile_visible_windows(self, newly_visible=None) -> None:
        """Apply configured tiling strategy to visible demo windows."""
        if not self.app.read_window_tiling_settings().get("enabled", False):
            return
        if newly_visible is None:
            newly_visible = self._visible_windows_for_tiling()
        self.app.tile_windows(newly_visible=newly_visible)

    def _exit_app(self) -> None:
        """Signal the application loop to stop on the next update."""
        self.app.running = False

    # ---------------------------------------------------------------------
    # Life simulation state and interaction logic.
    # ---------------------------------------------------------------------
    def _life_reset(self) -> None:
        """Reset Life board, zoom, and playback toggle to demo defaults."""
        LifeSimulationFeature.life_reset(self)

    def _life_population(self, cell: Tuple[int, int]) -> int:
        """Count live neighbors for a given Life cell."""
        return LifeSimulationFeature.life_population(self, cell)

    def _life_step(self) -> None:
        """Advance Conway's Game of Life simulation by one generation."""
        LifeSimulationFeature.life_step(self)

    def _zoom_life_view_about(self, anchor_local: Tuple[float, float], new_size: int) -> None:
        """Zoom Life canvas around a local anchor while preserving that anchor point."""
        LifeSimulationFeature.zoom_life_view_about(self, anchor_local, new_size)

    def _life_window_preamble(self) -> None:
        """Sync zoom state from slider before per-frame Life updates."""
        LifeSimulationFeature.life_window_preamble(self)

    def _on_life_zoom_slider_changed(self, value: float) -> None:
        """Handle slider callback and map it to discrete Life zoom steps."""
        LifeSimulationFeature.on_life_zoom_slider_changed(self, value)

    def _sync_life_zoom_from_slider(self, slider_value: int) -> None:
        """Apply discrete slider zoom updates around the canvas center."""
        LifeSimulationFeature.sync_life_zoom_from_slider(self, slider_value)

    def _life_window_event_handler(self, event) -> bool:
        """Process Life canvas drag, wheel zoom, and lock-point interactions."""
        return LifeSimulationFeature.life_window_event_handler(self, event)

    # ---------------------------------------------------------------------
    # Mandelbrot render pipeline and task orchestration.
    # ---------------------------------------------------------------------
    def _mandel_window_event_handler(self, event) -> bool:
        """Handle Mandel window-level events (unused in this demo)."""
        return MandelbrotRenderFeature.window_event_handler(self, event)

    def _life_window_postamble(self) -> None:
        """Flush queued Life input and redraw board each frame."""
        LifeSimulationFeature.life_window_postamble(self)

    def _mandel_col(self, k: int) -> Tuple[int, int, int]:
        """Map iteration count to palette color for Mandelbrot rendering."""
        return MandelbrotRenderFeature.mandel_col(self, k)

    def _mandel_viewport(self, width: int, height: int) -> Tuple[complex, float]:
        """Return default Mandel viewport center and pixel scale for a canvas size."""
        return MandelbrotRenderFeature.mandel_viewport(self, width, height)

    def _mandel_pixel(self, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        """Evaluate Mandelbrot iteration count for one pixel coordinate."""
        return MandelbrotRenderFeature.mandel_pixel(self, px, py, width, height, center, scale)

    def _clear_mandel_surfaces(self) -> None:
        """Clear all Mandel canvases to the current theme medium color."""
        MandelbrotRenderFeature.clear_surfaces(self)

    def _set_mandel_task_buttons_disabled(self, disabled: bool) -> None:
        """Toggle Mandel run controls and keep focus on an enabled control."""
        MandelbrotRenderFeature.set_task_buttons_disabled(self, disabled)

    def _show_single_mandel_canvas(self) -> None:
        """Switch UI to single-canvas Mandel presentation mode."""
        MandelbrotRenderFeature.show_single_canvas(self)

    def _prepare_mandel_single_canvas_run(self) -> None:
        """Prepare controls/canvases for a single-canvas Mandel task launch."""
        MandelbrotRenderFeature.prepare_single_canvas_run(self)

    def _prepare_mandel_split_canvas_run(self) -> None:
        """Prepare controls/canvases for a four-canvas Mandel task launch."""
        MandelbrotRenderFeature.prepare_split_canvas_run(self)

    def _mandel_canvas_for_task(self, task_id: str):
        """Resolve task id to its destination pygame canvas surface."""
        return MandelbrotRenderFeature.canvas_for_task(self, task_id)

    def _make_mandel_progress_handler(self, task_id: str):
        """Build scheduler message handler that routes payloads by task id."""
        return MandelbrotRenderFeature.make_progress_handler(self, task_id)

    def _apply_mandel_result(self, task_id: str, payload) -> None:
        """Apply Mandel worker payload into the target canvas, with clipping."""
        MandelbrotRenderFeature.apply_result(self, task_id, payload)

    def _clear_mandel(self) -> None:
        """Stop Mandel tasks and reset UI/state to cleared mode."""
        MandelbrotRenderFeature.clear(self)

    def _mandel_iterative_task(self, task_id, params):
        """Compute Mandel rows iteratively and stream row payload updates."""
        return MandelbrotRenderFeature.iterative_task(self, task_id, params)

    def _recursive_fill(self, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
        """Recursive Mandel region evaluation using corner coherence fill optimization."""
        MandelbrotRenderFeature.recursive_fill(self, task_id, x, y, w, h, width, height, center, scale)

    def _mandel_recursive_task(self, task_id, params):
        """Run recursive Mandel fill task for full or partial region."""
        return MandelbrotRenderFeature.recursive_task(self, task_id, params)

    def _queue_mandel_recursive_task(self, task_id: str, rect: Rect, size: Tuple[int, int], center: complex, scale: float) -> None:
        """Enqueue one recursive Mandel task and track it as in-flight."""
        MandelbrotRenderFeature.queue_recursive_task(self, task_id, rect, size, center, scale)

    def _launch_mandel_iterative(self) -> None:
        """Launch iterative full-canvas Mandel rendering task."""
        MandelbrotRenderFeature.launch_iterative(self)

    def _launch_mandel_recursive(self) -> None:
        """Launch recursive full-canvas Mandel rendering task."""
        MandelbrotRenderFeature.launch_recursive(self)

    def _launch_mandel_one_split(self) -> None:
        """Launch one-canvas, four-task recursive Mandel rendering split."""
        MandelbrotRenderFeature.launch_one_split(self)

    def _launch_mandel_four_split(self) -> None:
        """Launch four-canvas, four-task recursive Mandel rendering split."""
        MandelbrotRenderFeature.launch_four_split(self)

    # ---------------------------------------------------------------------
    # Frame updates and engine lifecycle hooks.
    # ---------------------------------------------------------------------
    def _update_life(self) -> None:
        """Consume Life canvas events, mutate board, and redraw the Life surface."""
        LifeSimulationFeature.update_life(self)

    def _update_mandel_events(self) -> None:
        """Drain Mandel scheduler events and maintain UI/status/task state."""
        MandelbrotRenderFeature.update_events(self)

    def _update(self, dt_seconds: float) -> None:
        """Delegate frame update into GuiApplication core update pipeline."""
        GuiApplication.update(self.app, dt_seconds)

    def _screen_preamble(self) -> None:
        """Scene-level preamble hook (kept for parity with lifecycle API)."""
        return None

    def _screen_event_handler(self, event) -> bool:
        """Scene-level event hook (unused; allows app default dispatching)."""
        return False

    def _screen_postamble(self) -> None:
        """Scene-level postamble hook used to reconcile Mandel task events."""
        for feature in self._demo_features:
            feature.on_post_frame(self)

    def run(self) -> None:
        """Run demo engine and perform shutdown cleanup on exit."""
        UiEngine(self.app, target_fps=120).run()
        if self._mandel_status_subscription is not None:
            self.app.events.unsubscribe(self._mandel_status_subscription)
            self._mandel_status_subscription = None
        self._mandel_status_bus_ready = False
        self.mandel_model.dispose()
        pygame.quit()


def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
