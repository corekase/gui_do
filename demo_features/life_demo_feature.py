"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import math
from typing import Any, Dict, Set, Tuple

from pygame import Rect
from shared.feature_lifecycle import FeatureMessage, LogicFeature, RoutedFeature


_LIFE_LOGIC_TOPIC = "life_logic"

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
        command = message.command
        sender_name = message.sender
        if command == "reset":
            self.life_cells = set(self.DEFAULT_SEED)
            self._publish_state(sender_name)
            return
        if command == "next":
            self.life_cells = self.next_life_cycle(self.life_cells)
            self._publish_state(sender_name)
            return
        if command == "toggle_cell":
            cell = message.get("cell")
            if isinstance(cell, tuple) and len(cell) == 2:
                normalized_cell = (int(cell[0]), int(cell[1]))
                if normalized_cell in self.life_cells:
                    self.life_cells.remove(normalized_cell)
                else:
                    self.life_cells.add(normalized_cell)
                self._publish_state(sender_name)
            return
        if command == "snapshot":
            self._publish_state(sender_name)

    def _publish_state(self, target_part_name: str) -> None:
        self.send_message(
            target_part_name,
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
        self.canvas = None
        self.reset_button = None
        self.toggle = None
        self.zoom_slider = None

    def build(self, host) -> None:
        """Build the Life feature UI using the application's configured UI types."""
        ui = host.app.read_feature_ui_types()
        self.register_font_roles(
            host,
            {
                "window_title": {"size": 14, "file_path": "data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 16, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="main",
        )
        self.build_window(
            host,
            window_control_cls=ui.window_control_cls,
            canvas_control_cls=ui.canvas_control_cls,
            button_control_cls=ui.button_control_cls,
            toggle_control_cls=ui.toggle_control_cls,
            slider_control_cls=ui.slider_control_cls,
            layout_axis_cls=ui.layout_axis_cls,
        )

    def bind_runtime(self, host) -> None:
        """Bind scheduler/runtime services required after scene construction."""
        if self.scheduler is None:
            self.scheduler = host.app.get_scene_scheduler("main")
        self.scheduler.set_message_dispatch_limit(256)
        if self.bound_logic_name(alias=self.LOGIC_ALIAS) is None:
            self.bind_logic("life_simulation_logic", alias=self.LOGIC_ALIAS)
        self._send_life_logic_command("snapshot")

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        """Assign accessibility metadata and tab order for Life controls."""
        controls = [
            self.reset_button,
            self.toggle,
            self.zoom_slider,
        ]
        roles = [
            ("button", "Reset life board"),
            ("toggle", "Run life simulation"),
            ("slider", "Life zoom"),
        ]
        next_index = int(tab_index_start)
        for control, (role, label) in zip(controls, roles):
            if control is None:
                continue
            control.set_tab_index(next_index)
            control.set_accessibility(role=role, label=label)
            next_index += 1
        return next_index

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

    def build_window(
        self,
        host,
        *,
        window_control_cls,
        canvas_control_cls,
        button_control_cls,
        toggle_control_cls,
        slider_control_cls,
        layout_axis_cls,
    ) -> None:
        """Create the Life window, canvas, and interaction controls."""
        self.demo = host  # Store host reference for use in callback methods
        life_rect = host.app.layout.anchored((640, 640), anchor="top_right", margin=(28, 92), use_rect=True)
        self.window = host.root.add(
            window_control_cls(
                "life_window",
                life_rect,
                "Conway's Game of Life",
                title_font_role=self.font_role("window_title"),
                preamble=self.life_window_preamble,
                event_handler=self.life_window_event_handler,
                postamble=self.life_window_postamble,
                use_frame_backdrop=True,
            )
        )
        content_rect = self.window.content_rect()
        left = content_rect.left
        top = content_rect.top
        width = content_rect.width
        height = content_rect.height
        widget_height = 28
        padding = 10
        controls_gap = padding
        control_spacing = 12

        controls_y = top + height - widget_height - padding
        canvas_height = max(1, controls_y - controls_gap - (top + padding))

        self.canvas = self.window.add(
            canvas_control_cls("life_canvas", Rect(left + padding, top + padding, width - (padding * 2), canvas_height), max_events=256)
        )

        row_width = max(1, width - (padding * 2))
        slot_count = 4
        slot_width = max(1, (row_width - (control_spacing * (slot_count - 1))) // slot_count)
        strip_width = (slot_width * slot_count) + (control_spacing * (slot_count - 1))
        strip_left = left + padding + max(0, (row_width - strip_width) // 2)
        host.app.layout.set_linear_properties(
            anchor=(strip_left, controls_y),
            item_width=slot_width,
            item_height=widget_height,
            spacing=control_spacing,
            horizontal=True,
        )
        life_reset_rect = host.app.layout.next_linear()
        life_toggle_rect = host.app.layout.next_linear()
        zoom_slider_slot_1 = host.app.layout.next_linear()
        zoom_slider_slot_2 = host.app.layout.next_linear()

        self.reset_button = self.window.add(
            button_control_cls("life_reset", life_reset_rect, "Reset", self.life_reset, style="angle", font_role=self.font_role("control"))
        )
        self.toggle = self.window.add(
            toggle_control_cls(
                "life_toggle",
                life_toggle_rect,
                "Stop",
                "Start",
                pushed=False,
                style="round",
                font_role=self.font_role("control"),
            )
        )

        slider_left = zoom_slider_slot_1.left
        slider_right = zoom_slider_slot_2.right
        self.zoom_slider = self.window.add(
            slider_control_cls(
                "life_zoom",
                Rect(slider_left, controls_y, max(80, slider_right - slider_left), widget_height),
                layout_axis_cls.HORIZONTAL,
                0.0,
                11.0,
                5.0,
                on_change=self.on_life_zoom_slider_changed,
            )
        )
        self.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.life_reset()
        self.window.visible = False

    def life_reset(self) -> None:
        """Reset simulation state, viewport origin, zoom level, and run toggle."""
        self.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
        self.life_cell_size = 12
        self.zoom_slider.value = 5.0
        self.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.toggle.pushed = False
        if not self._send_life_logic_command("reset"):
            self.life_cells = set(LifeSimulationLogicFeature.DEFAULT_SEED)

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

    def life_window_preamble(self) -> None:
        """Window preamble hook that reconciles zoom changes from slider position."""
        slider_value = max(0, min(11, int(round(self.zoom_slider.value))))
        self.sync_life_zoom_from_slider(slider_value)

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

    def life_window_event_handler(self, event) -> bool:
        """Handle drag, click, and wheel interactions routed to the Life window."""
        demo = self.demo
        canvas = self.canvas
        window = self.window
        if event.is_mouse_down(3) and event.collides(canvas.rect):
            pos = event.pos
            if pos is not None:
                self.life_dragging = True
                demo.app.set_cursor("hand")
                demo.app.set_lock_point(canvas, pos)
                return True

        if event.is_mouse_up(3):
            if self.life_dragging:
                self.life_dragging = False
                demo.app.set_cursor("normal")
                demo.app.set_lock_point(None)
                return True

        if event.is_mouse_motion() and self.life_dragging:
            # Prefer lock-point delta to keep drag behavior stable under pointer lock.
            delta = demo.app.get_lock_point_motion_delta(event)
            if delta is None:
                rel = event.rel
                if isinstance(rel, tuple) and len(rel) == 2:
                    delta = (rel[0], rel[1])
                else:
                    delta = (0, 0)
            self.life_origin[0] -= delta[0]
            self.life_origin[1] -= delta[1]
            return True

        if event.is_mouse_wheel():
            pointer_pos = demo.app.lock_point_pos if demo.app.mouse_point_locked and demo.app.lock_point_pos is not None else event.pos
            if pointer_pos is not None and canvas.rect.collidepoint(pointer_pos):
                if demo.app.mouse_point_locked and demo.app.lock_point_pos is not None:
                    # Convert locked window-space pointer to canvas-local coordinates.
                    lock_window_pos = demo.app.convert_to_window(demo.app.lock_point_pos, window)
                    canvas_window_left = canvas.rect.left - window.rect.left
                    canvas_window_top = canvas.rect.top - window.rect.top
                    anchor_local = (lock_window_pos[0] - canvas_window_left, lock_window_pos[1] - canvas_window_top)
                else:
                    anchor_local = (pointer_pos[0] - canvas.rect.left, pointer_pos[1] - canvas.rect.top)
                self.zoom_life_view_about(anchor_local, self.life_cell_size + (event.wheel_delta * 2))
                return True

        return False

    def life_window_postamble(self) -> None:
        """Window postamble hook that drains queued events and renders the board."""
        self.update_life()

    def update_life(self) -> None:
        """Process queued canvas input, step simulation, then redraw visible cells."""
        demo = self.demo
        canvas = self.canvas
        toggle = self.toggle
        while True:
            packet = canvas.read_event()
            if packet is None:
                break
            if not packet.is_mouse_down(1):
                continue
            # Prefer canvas-local packet coordinates; fall back to global packet position.
            if packet.local_pos is not None:
                local_x, local_y = packet.local_pos
            elif packet.pos is not None:
                local_x = packet.pos[0] - canvas.rect.left
                local_y = packet.pos[1] - canvas.rect.top
            else:
                continue
            cell_size = max(2, int(round(self.life_cell_size)))
            cell_x = math.floor((local_x - self.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - self.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if not self._send_life_logic_command("toggle_cell", cell=cell):
                if cell in self.life_cells:
                    self.life_cells.remove(cell)
                else:
                    self.life_cells.add(cell)

        if toggle.pushed:
            if not self._send_life_logic_command("next"):
                self.life_cells = LifeSimulationLogicFeature.next_life_cycle(self.life_cells)

        cell_size = max(2, int(round(self.life_cell_size)))
        canvas.canvas.fill(demo.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.life_cells:
            px = int(self.life_origin[0] + (cx * cell_size))
            py = int(self.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= canvas.rect.width and -cell_size <= py <= canvas.rect.height:
                canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))
