"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import math
from typing import Any, Dict, Set, Tuple

from pygame import Rect
from gui_do import FeatureMessage, LayoutAxis, RoutedFeature, WindowControl
from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    bind_routed_feature_lifecycle,
    LogicBindingSpec,
    create_feature_presented_window,
    register_routed_feature_companions,
    resolve_canvas_local_point,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
)
from .life_simulation_logic_feature import LifeSimulationLogicFeature


# ---------------------------------------------------------------------------
# Life window layout constants — single source of truth for sizing and layout
# ---------------------------------------------------------------------------
_LIFE_PAD = 10           # Uniform padding inside the window body on all four sides
_LIFE_CTRL_GAP = 8       # Gap between the canvas bottom edge and the control strip
_LIFE_CTRL_H = 28        # Control strip height
_LIFE_CTRL_SPACING = 12  # Horizontal spacing between items in the control strip
_LIFE_CANVAS_SIZE = 600  # Square canvas dimension
_LIFE_TITLEBAR_H = 24    # Estimated titlebar height (matches size-14 title font)

_LIFE_BODY_W = _LIFE_PAD + _LIFE_CANVAS_SIZE + _LIFE_PAD
_LIFE_BODY_H = (
    _LIFE_PAD + _LIFE_CANVAS_SIZE + _LIFE_CTRL_GAP + _LIFE_CTRL_H + _LIFE_PAD
)
_LIFE_WINDOW_SIZE = (_LIFE_BODY_W, _LIFE_TITLEBAR_H + _LIFE_BODY_H)

_LIFE_CANVAS_CONTROL_SPEC = {
    "control_id": "life_canvas",
    "max_events": 256,
}

_LIFE_STRIP_CONTROL_SPECS = (
    {
        "kind": "button",
        "slot_index": 0,
        "presenter_attr": "reset_button",
        "feature_attr": "reset_button",
        "control_id": "life_reset",
        "label": "Reset",
        "style": "angle",
        "handler_attr": "life_reset",
        "accessibility_role": "button",
        "accessibility_label": "Reset life board",
    },
    {
        "kind": "toggle",
        "slot_index": 1,
        "presenter_attr": "toggle",
        "feature_attr": "toggle",
        "control_id": "life_toggle",
        "off_text": "Stop",
        "on_text": "Start",
        "pushed": False,
        "style": "round",
        "accessibility_role": "toggle",
        "accessibility_label": "Run life simulation",
    },
)

_LIFE_ZOOM_SLIDER_SPEC = {
    "control_id": "life_zoom",
    "axis": LayoutAxis.HORIZONTAL,
    "min": 0.0,
    "max": 11.0,
    "value": 5.0,
    "height": 20,
    "min_width": 80,
    "presenter_attr": "zoom_slider",
    "feature_attr": "zoom_slider",
    "on_change_attr": "on_life_zoom_slider_changed",
    "accessibility_role": "slider",
    "accessibility_label": "Life zoom",
}
# ---------------------------------------------------------------------------

_LIFE_LOGIC_TOPIC = "life_logic"

_LIFE_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="life_window",
    title="Conway's Game of Life",
    size=_LIFE_WINDOW_SIZE,
    anchor="top_right",
    margin=(28, 92),
    use_frame_backdrop=True,
)

_LIFE_LOGIC_BINDINGS = (
    LogicBindingSpec(alias="life", provider_name="life_simulation_logic"),
)

_LIFE_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    scheduler_attr_name="scheduler",
    scheduler_dispatch_limit=512,
    logic_bindings=_LIFE_LOGIC_BINDINGS,
)

_LIFE_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    companion_providers=(lambda: LifeSimulationLogicFeature(),),
    runtime_spec=_LIFE_RUNTIME_SPEC,
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)

_KEY_TOPIC = "topic"
_KEY_EVENT = "event"
_KEY_COMMAND = "command"
_KEY_LIFE_CELLS = "life_cells"

_LIFE_EVENT_STATE = "state"


class LifeSimulationFeature(RoutedFeature):
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
        from .life_window_presenter import LifeWindowPresenter

        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=LifeWindowPresenter,
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
            _LIFE_LOGIC_TOPIC: self._handle_life_logic_message,
        }

    def _handle_life_logic_message(self, _host, message: FeatureMessage) -> None:
        if message.event != _LIFE_EVENT_STATE:
            return
        cells = message.get(_KEY_LIFE_CELLS)
        normalized = self._normalize_life_cells_payload(cells)
        if normalized is not None:
            self.life_cells = normalized

    def _normalize_life_cells_payload(self, cells: Any) -> Set[Tuple[int, int]] | None:
        if isinstance(cells, set):
            return {(int(x), int(y)) for (x, y) in cells}
        if isinstance(cells, (tuple, list)):
            normalized: Set[Tuple[int, int]] = set()
            for candidate in cells:
                if isinstance(candidate, tuple) and len(candidate) == 2:
                    normalized.add((int(candidate[0]), int(candidate[1])))
            return normalized
        return None

    def _send_life_logic_command(self, command: str, **extra: Any) -> bool:
        if self._feature_manager is None:
            return False
        message: Dict[str, Any] = {
            _KEY_TOPIC: _LIFE_LOGIC_TOPIC,
            _KEY_COMMAND: str(command),
        }
        message.update(extra)
        return self.send_logic_message(message, alias=self.LOGIC_ALIAS)

    def life_reset(self) -> None:
        """Reset simulation state, viewport origin, zoom level, and run toggle."""
        self.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
        self.life_cell_size = 12
        self.zoom_slider.value = 5.0
        self.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.toggle.pushed = False
        # Apply local state immediately so the next frame cannot render stale cells
        # with the freshly reset viewport while the logic message is in transit.
        self.life_cells = set(LifeSimulationLogicFeature.DEFAULT_SEED)
        self._send_life_logic_command("reset")

    def zoom_life_view_about(self, anchor_local: Tuple[float, float], new_size: int) -> None:
        """Zoom around a local canvas anchor while preserving the anchored world point."""
        old_size = max(2, int(round(self.life_cell_size)))
        clamped_size = max(2, min(24, int(new_size)))
        if clamped_size == old_size:
            return
        anchor_x, anchor_y = anchor_local
        self.life_origin[0] = anchor_x - ((anchor_x - self.life_origin[0]) / old_size) * clamped_size
        self.life_origin[1] = anchor_y - ((anchor_y - self.life_origin[1]) / old_size) * clamped_size
        self.life_cell_size = clamped_size
        slider_value = max(0, min(11, (clamped_size // 2) - 1))
        self.zoom_slider.value = float(slider_value)
        self.life_zoom_slider_last_value = int(slider_value)

    def on_life_zoom_slider_changed(self, value: float, _reason) -> None:
        """Slider callback that converts float slider values into integer zoom steps."""
        self.sync_life_zoom_from_slider(int(round(value)))

    def sync_life_zoom_from_slider(self, slider_value: int) -> None:
        """Apply slider-driven zoom changes using the canvas center as anchor."""
        if slider_value == self.life_zoom_slider_last_value:
            return
        old_size = max(2, int(round(self.life_cell_size)))
        new_size = (slider_value + 1) * 2
        if new_size == old_size:
            self.life_zoom_slider_last_value = slider_value
            return
        self.life_zoom_slider_last_value = slider_value
        center_local = (self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0)
        self.zoom_life_view_about(center_local, new_size)

    def update_life(self) -> None:
        """Process queued canvas input, step simulation, then redraw visible cells."""
        self._update_life_frame_core(self.demo, self.canvas, self.toggle)

    def _update_life_frame_core(self, demo, canvas, toggle) -> None:
        """Shared life frame update used by both feature and presenter update paths."""
        while True:
            packet = canvas.read_event()
            if packet is None:
                break
            if not packet.is_mouse_down(1):
                continue
            local_point = resolve_canvas_local_point(packet, canvas.rect)
            if local_point is None:
                continue
            local_x, local_y = local_point
            cell_size = max(2, int(round(self.life_cell_size)))
            cell_x = math.floor((local_x - self.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - self.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            # Apply locally first so render state never lags behind input.
            if cell in self.life_cells:
                self.life_cells.remove(cell)
            else:
                self.life_cells.add(cell)
            self._send_life_logic_command("toggle_cell", cell=cell)

        if toggle.pushed:
            # Step locally first to keep animation deterministic even with message latency.
            self.life_cells = LifeSimulationLogicFeature.next_life_cycle(self.life_cells)
            self._send_life_logic_command("next")

        cell_size = max(2, int(round(self.life_cell_size)))
        canvas.canvas.fill(demo.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.life_cells:
            px = int(self.life_origin[0] + (cx * cell_size))
            py = int(self.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= canvas.rect.width and -cell_size <= py <= canvas.rect.height:
                canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))
