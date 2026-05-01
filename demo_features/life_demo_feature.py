"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

import math
from typing import Any, Dict, Set, Tuple

from pygame import Rect
from gui_do import (
    ButtonControl,
    CanvasControl,
    centered_horizontal_strip_layout,
    FeatureMessage,
    inset_rect,
    LayoutAxis,
    LogicFeature,
    RoutedFeature,
    SliderControl,
    split_slot_bounds,
    ToggleControl,
    WindowControl,
)
from gui_do.controls.chrome.window_presenter import WindowPresenter
from demo_features.feature_abstractions import (
    AccessibilitySequenceSpec,
    apply_accessibility_sequence_from_attrs,
    AnchoredWindowSpec,
    LogicBindingSpec,
    create_feature_presented_window,
    resolve_canvas_local_point,
    register_companion_logic_features,
    setup_routed_feature_runtime,
)


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

_LIFE_ACCESSIBILITY_SPECS = (
    AccessibilitySequenceSpec(control_attr="reset_button", role="button", label="Reset life board"),
    AccessibilitySequenceSpec(control_attr="toggle", role="toggle", label="Run life simulation"),
    AccessibilitySequenceSpec(control_attr="zoom_slider", role="slider", label="Life zoom"),
)

_KEY_TOPIC = "topic"
_KEY_EVENT = "event"
_KEY_COMMAND = "command"
_KEY_LIFE_CELLS = "life_cells"

_LIFE_EVENT_STATE = "state"


class LifeSimulationLogicFeature(LogicFeature):
    """Domain logic service for Conway life cycles."""

    DEFAULT_SEED: Set[Tuple[int, int]] = {
        (0, 0),
        (1, 0),
        (-1, 0),
        (0, -1),
        (1, -2),
    }
    NEIGHBOURS = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )

    def __init__(self) -> None:
        super().__init__("life_simulation_logic", scene_name="main")
        self.life_cells: Set[Tuple[int, int]] = set(self.DEFAULT_SEED)
        self._command_handlers = {
            "reset": self._handle_reset_command,
            "next": self._handle_next_command,
            "toggle_cell": self._handle_toggle_cell_command,
            "snapshot": self._handle_snapshot_command,
        }

    @classmethod
    def next_life_cycle(cls, cells: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        new_life: Set[Tuple[int, int]] = set()
        for cell in cells:
            pop = cls._life_population(cells, cell)
            if pop in (2, 3):
                new_life.add(cell)
            for dx, dy in cls.NEIGHBOURS:
                n_cell = (cell[0] + dx, cell[1] + dy)
                if cls._life_population(cells, n_cell) == 3:
                    new_life.add(n_cell)
        return new_life

    @classmethod
    def _life_population(cls, cells: Set[Tuple[int, int]], cell: Tuple[int, int]) -> int:
        count = 0
        for dx, dy in cls.NEIGHBOURS:
            if (cell[0] + dx, cell[1] + dy) in cells:
                count += 1
        return count

    def on_logic_command(self, _host, message: FeatureMessage) -> None:
        command = str(message.command)
        handler = self._command_handlers.get(command)
        if handler is None:
            return
        handler(str(message.sender), message)

    def _handle_reset_command(self, sender_name: str, _message: FeatureMessage) -> None:
        self.life_cells = set(self.DEFAULT_SEED)
        self._publish_state(sender_name)

    def _handle_next_command(self, sender_name: str, _message: FeatureMessage) -> None:
        self.life_cells = self.next_life_cycle(self.life_cells)
        self._publish_state(sender_name)

    def _handle_toggle_cell_command(self, sender_name: str, message: FeatureMessage) -> None:
        cell = message.get("cell")
        if isinstance(cell, tuple) and len(cell) == 2:
            normalized_cell = (int(cell[0]), int(cell[1]))
            if normalized_cell in self.life_cells:
                self.life_cells.remove(normalized_cell)
            else:
                self.life_cells.add(normalized_cell)
            self._publish_state(sender_name)

    def _handle_snapshot_command(self, sender_name: str, _message: FeatureMessage) -> None:
        self._publish_state(sender_name)

    def _publish_state(self, target_feature_name: str) -> None:
        self.send_message(
            target_feature_name,
            {
                _KEY_TOPIC: _LIFE_LOGIC_TOPIC,
                _KEY_EVENT: _LIFE_EVENT_STATE,
                _KEY_LIFE_CELLS: set(self.life_cells),
            },
        )


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
        self.demo = None  # Will be set during build_window
        self.window = None
        self.menu_bar = None
        self.canvas = None
        self.reset_button = None
        self.toggle = None
        self.zoom_slider = None

    def on_register(self, host) -> None:
        """Auto-register the companion logic feature when this feature is registered."""
        register_companion_logic_features(
            self._feature_manager,
            host,
            [LifeSimulationLogicFeature()],
        )

    def build(self, host) -> None:
        """Build the Life feature UI using the new presenter/controller pattern."""
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_LifeWindowPresenter,
            spec=_LIFE_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        """Bind scheduler/runtime services required after scene construction."""
        self.scheduler = setup_routed_feature_runtime(
            self,
            host,
            scene_name="main",
            scheduler_dispatch_limit=512,
            logic_bindings=_LIFE_LOGIC_BINDINGS,
        )
        self._send_life_logic_command("snapshot")

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        """Assign accessibility metadata and tab order for Life controls."""
        return apply_accessibility_sequence_from_attrs(
            self,
            _LIFE_ACCESSIBILITY_SPECS,
            tab_index_start,
        )

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


class _LifeWindowPresenter(WindowPresenter):
    """Window presenter for the Conway's Game of Life window."""

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.canvas = None
        self.reset_button = None
        self.toggle = None
        self.zoom_slider = None

    def on_create(self):
        content_rect = self.window.content_rect()
        padded = inset_rect(content_rect, padding_x=_LIFE_PAD, padding_y=_LIFE_PAD)
        left = padded.left
        top = padded.top
        width = padded.width
        height = padded.height

        ctrl_y = top + height - _LIFE_CTRL_H
        canvas_h = max(1, ctrl_y - _LIFE_CTRL_GAP - top)
        canvas_rect = Rect(left, top, width, canvas_h)
        self.canvas = CanvasControl("life_canvas", canvas_rect, max_events=256)
        self.add_control(self.canvas)
        self.feature.canvas = self.canvas

        slots = centered_horizontal_strip_layout(
            left=left, width=width, y=ctrl_y, item_count=4, item_height=_LIFE_CTRL_H, spacing=_LIFE_CTRL_SPACING,
        )
        life_reset_rect, life_toggle_rect, zoom_slider_slot_1, zoom_slider_slot_2 = slots

        self.reset_button = ButtonControl(
            "life_reset", life_reset_rect, "Reset", self.feature.life_reset, style="angle"
        )
        self.add_control(self.reset_button)
        self.feature.reset_button = self.reset_button

        self.toggle = ToggleControl(
            "life_toggle", life_toggle_rect, "Stop", "Start", pushed=False, style="round",
        )
        self.add_control(self.toggle)
        self.feature.toggle = self.toggle

        slider_left, slider_right = split_slot_bounds([zoom_slider_slot_1, zoom_slider_slot_2])
        slider_height = 20
        slider_y = ctrl_y + max(0, (_LIFE_CTRL_H - slider_height) // 2)
        self.zoom_slider = SliderControl(
            "life_zoom",
            Rect(slider_left, slider_y, max(80, slider_right - slider_left), slider_height),
            LayoutAxis.HORIZONTAL, 0.0, 11.0, 5.0, on_change=self.feature.on_life_zoom_slider_changed,
        )
        self.add_control(self.zoom_slider)
        self.feature.zoom_slider = self.zoom_slider

        self.feature.demo = self.host
        self.feature.window = self.window
        self.feature.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
        self.feature.life_cell_size = 12
        self.feature.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.feature.life_dragging = False
        self.feature._send_life_logic_command("snapshot")
        self.window.visible = False

    def handle_event(self, event):
        return self._event_handler_impl(event)

    def before_update(self, dt_seconds: float):
        _ = dt_seconds
        self._preamble_impl()

    def after_update(self, dt_seconds: float):
        _ = dt_seconds
        self._postamble_impl()

    def _event_handler_impl(self, event):
        demo = self.host
        canvas = self.canvas
        window = self.window

        if event.is_mouse_down(3) and event.collides(canvas.rect):
            pos = event.pos
            if pos is not None:
                self.feature.life_dragging = True
                demo.app.set_cursor("hand")
                demo.app.set_lock_point(canvas, pos)
                return True

        if event.is_mouse_up(3):
            if self.feature.life_dragging:
                self.feature.life_dragging = False
                demo.app.set_cursor("normal")
                demo.app.set_lock_point(None)
                return True

        if event.is_mouse_motion() and self.feature.life_dragging:
            delta = demo.app.get_lock_point_motion_delta(event)
            if delta is None:
                rel = event.rel
                delta = (rel[0], rel[1]) if isinstance(rel, tuple) and len(rel) == 2 else (0, 0)
            self.feature.life_origin[0] -= delta[0]
            self.feature.life_origin[1] -= delta[1]
            return True

        if event.is_mouse_wheel():
            locked = getattr(demo.app, "mouse_point_locked", False)
            lock_pos = getattr(demo.app, "lock_point_pos", None)
            pointer_pos = lock_pos if locked and lock_pos is not None else event.pos
            if pointer_pos is not None and canvas.rect.collidepoint(pointer_pos):
                if locked and lock_pos is not None:
                    lp = demo.app.convert_to_window(lock_pos, window)
                    anchor_local = (lp[0] - (canvas.rect.left - window.rect.left), lp[1] - (canvas.rect.top - window.rect.top))
                else:
                    anchor_local = (pointer_pos[0] - canvas.rect.left, pointer_pos[1] - canvas.rect.top)
                self.feature.zoom_life_view_about(anchor_local, self.feature.life_cell_size - (event.wheel_delta * 2))
                return True

        return False

    def _preamble_impl(self):
        slider_value = max(0, min(11, int(round(self.zoom_slider.value))))
        self.feature.sync_life_zoom_from_slider(slider_value)

    def _postamble_impl(self):
        self._update_life()

    def _update_life(self):
        self.feature._update_life_frame_core(self.host, self.canvas, self.toggle)
