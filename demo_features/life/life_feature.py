"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from typing import Any, Set, Tuple

from pygame import Rect
from gui_do import FeatureMessage, RoutedFeature, WindowControl
from gui_do.features.data_driven_runtime import (
    bind_routed_feature_lifecycle,
    create_feature_presented_window,
    register_routed_feature_companions,
)
from .life_runtime_helpers import (
    life_reset as life_reset_helper,
    normalize_life_cells_payload as normalize_life_cells_payload_helper,
    on_life_zoom_slider_changed as on_life_zoom_slider_changed_helper,
    send_life_logic_command as send_life_logic_command_helper,
    sync_life_zoom_from_slider as sync_life_zoom_from_slider_helper,
    update_life as update_life_helper,
    update_life_frame_core as update_life_frame_core_helper,
    zoom_life_view_about as zoom_life_view_about_helper,
)
from .life_specs import (
    LIFE_EVENT_STATE,
    LIFE_KEY_CELLS,
    LIFE_KEY_COMMAND,
    LIFE_KEY_TOPIC,
    LIFE_LOGIC_TOPIC,
    _LIFE_WINDOW_SPEC,
    _LIFE_LIFECYCLE_SPEC,
)


class LifeFeature(RoutedFeature):
    """Build and run the Conway's Game of Life feature window and interactions."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    LOGIC_ALIAS = "life"

    def __init__(self) -> None:
        super().__init__("life_simulation", scene_name="main")
        self.life_cells: Set[Tuple[int, int]] = set()
        self.life_origin = [0.0, 0.0]
        self.life_cell_size = 12
        self.life_dragging = False
        self.life_zoom_slider_last_value = 5
        self.scheduler = None
        self._runtime_spec = None
        self.demo = None  # Will be set during build_window
        self.window = None
        self.menu_bar = None
        self.canvas = None
        self.reset_button = None
        self.toggle = None
        self.zoom_slider = None

    def on_register(self, host) -> None:
        """Auto-register the companion logic feature when this feature is registered."""
        register_routed_feature_companions(self, host, _LIFE_LIFECYCLE_SPEC)

    def build(self, host) -> None:
        """Build the Life feature UI using the new presenter/controller pattern."""
        from .life_presenter import LifePresenter

        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=LifePresenter,
            spec=_LIFE_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        """Bind scheduler/runtime services required after scene construction."""
        self.scheduler = bind_routed_feature_lifecycle(self, host, _LIFE_LIFECYCLE_SPEC)
        self._send_life_logic_command("snapshot")

    def message_handlers(self):
        """Route lifecycle feature messages by canonical topic."""
        return {
            LIFE_LOGIC_TOPIC: self._handle_life_logic_message,
        }

    def _handle_life_logic_message(self, _host, message: FeatureMessage) -> None:
        if message.event != LIFE_EVENT_STATE:
            return
        cells = message.get(LIFE_KEY_CELLS)
        normalized = self._normalize_life_cells_payload(cells)
        if normalized is not None:
            self.life_cells = normalized

    def _normalize_life_cells_payload(self, cells: Any) -> Set[Tuple[int, int]] | None:
        return normalize_life_cells_payload_helper(self, cells)

    def _send_life_logic_command(self, command: str, **extra: Any) -> bool:
        return send_life_logic_command_helper(self, command, **extra)

    def life_reset(self) -> None:
        """Reset simulation state, viewport origin, zoom level, and run toggle."""
        life_reset_helper(self)

    def zoom_life_view_about(self, anchor_local: Tuple[float, float], new_size: int) -> None:
        """Zoom around a local canvas anchor while preserving the anchored world point."""
        zoom_life_view_about_helper(self, anchor_local, new_size)

    def on_life_zoom_slider_changed(self, value: float, _reason) -> None:
        """Slider callback that converts float slider values into integer zoom steps."""
        on_life_zoom_slider_changed_helper(self, value, _reason)

    def sync_life_zoom_from_slider(self, slider_value: int) -> None:
        """Apply slider-driven zoom changes using the canvas center as anchor."""
        sync_life_zoom_from_slider_helper(self, slider_value)

    def update_life(self) -> None:
        """Process queued canvas input, step simulation, then redraw visible cells."""
        update_life_helper(self)

    def _update_life_frame_core(self, demo, canvas, toggle) -> None:
        """Shared life frame update used by both feature and presenter update paths."""
        update_life_frame_core_helper(self, demo, canvas, toggle)
