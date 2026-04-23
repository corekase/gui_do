"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import math
from typing import Set, Tuple

from pygame import Rect
from shared.part_lifecycle import Part


class LifeSimulationFeature(Part):
    """Build and run the Conway's Game of Life feature window and interactions."""

    def __init__(self) -> None:
        super().__init__("life_simulation")
        self.neighbours = (
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        )
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
        self.zoom_label = None
        self.last_mandel_status = None

    def build(self, demo) -> None:
        """Build the Life feature UI using the application's configured UI types."""
        ui = demo.app.read_part_ui_types()
        self.register_font_roles(
            demo,
            {
                "window_title": {"size": 14, "file_path": "data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 16, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "annotation": {"size": 16, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="main",
        )
        self.build_window(
            demo,
            window_control_cls=ui.window_control_cls,
            canvas_control_cls=ui.canvas_control_cls,
            button_control_cls=ui.button_control_cls,
            toggle_control_cls=ui.toggle_control_cls,
            slider_control_cls=ui.slider_control_cls,
            label_control_cls=ui.label_control_cls,
            layout_axis_cls=ui.layout_axis_cls,
        )

    def bind_runtime(self, demo) -> None:
        """Bind scheduler/runtime services required after scene construction."""
        if self.scheduler is None:
            self.scheduler = demo.app.get_scene_scheduler("main")
        self.scheduler.set_message_dispatch_limit(256)

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
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

    def on_post_frame(self, demo) -> None:
        """Consume cross-part status messages published by the Mandelbrot feature."""
        latest_status = None
        while self.has_messages():
            payload = self.pop_message()
            if not isinstance(payload, dict):
                continue
            if payload.get("topic") != "mandelbrot_status":
                continue
            if "status" in payload:
                latest_status = str(payload["status"])
        if latest_status is not None:
            self.last_mandel_status = latest_status

    def on_update(self, host) -> None:
        """Part lifecycle on_update hook delegated from the host application."""
        self.on_post_frame(host)

    def build_window(
        self,
        demo,
        *,
        window_control_cls,
        canvas_control_cls,
        button_control_cls,
        toggle_control_cls,
        slider_control_cls,
        label_control_cls,
        layout_axis_cls,
    ) -> None:
        """Create the Life window, canvas, and interaction controls."""
        self.demo = demo  # Store demo reference for use in callback methods
        life_rect = demo.app.layout.anchored((640, 640), anchor="top_right", margin=(28, 92), use_rect=True)
        self.window = demo.root.add(
            window_control_cls(
                "life_window",
                life_rect,
                "Conway's Game of Life",
                title_font_role=self.font_role("window_title"),
                preamble=self.life_window_preamble,
                event_handler=self.life_window_event_handler,
                postamble=self.life_window_postamble,
            )
        )
        content_rect = self.window.content_rect()
        left = content_rect.left
        top = content_rect.top
        width = content_rect.width
        height = content_rect.height
        widget_height = 28
        padding = 10

        self.canvas = self.window.add(
            canvas_control_cls("life_canvas", Rect(left + padding, top + padding, width - (padding * 2), height - (widget_height * 2)), max_events=256)
        )

        controls_y = top + height - widget_height - padding

        demo.app.layout.set_linear_properties(
            anchor=(left + padding, controls_y),
            item_width=100,
            item_height=widget_height,
            spacing=12,
            horizontal=True,
        )
        life_reset_rect = demo.app.layout.next_linear()
        life_toggle_rect = demo.app.layout.next_linear()
        zoom_slider_slot_1 = demo.app.layout.next_linear()
        zoom_slider_slot_2 = demo.app.layout.next_linear()
        zoom_label_slot = demo.app.layout.next_linear()

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
        zoom_label_rect = Rect(zoom_label_slot.left + 24, controls_y + 6, 76, 20)
        self.zoom_label = demo.app.style_label(
            self.window.add(label_control_cls("life_zoom_label", zoom_label_rect, "Zoom 12")),
            role=self.font_role("annotation"),
        )
        self.life_reset()
        self.window.visible = False

    def set_life_zoom_label(self) -> None:
        """Refresh the Life zoom label text from the effective cell size."""
        zoom_level = max(2, int(round(self.life_cell_size)))
        self.zoom_label.text = f"Zoom {zoom_level}"

    def life_reset(self) -> None:
        """Reset simulation state, viewport origin, zoom level, and run toggle."""
        self.life_cells.clear()
        self.life_cells.update({(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)})
        self.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
        self.life_cell_size = 12
        self.zoom_slider.value = 5.0
        self.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.set_life_zoom_label()
        self.toggle.pushed = False

    def life_population(self, cell: Tuple[int, int]) -> int:
        """Return the number of alive neighbours surrounding one cell."""
        count = 0
        for dx, dy in self.neighbours:
            if (cell[0] + dx, cell[1] + dy) in self.life_cells:
                count += 1
        return count

    def life_step(self, demo) -> None:
        """Advance the simulation by one generation using Conway rules."""
        new_life: Set[Tuple[int, int]] = set()
        for cell in self.life_cells:
            pop = self.life_population(cell)
            if pop in (2, 3):
                new_life.add(cell)
            for dx, dy in self.neighbours:
                n_cell = (cell[0] + dx, cell[1] + dy)
                if self.life_population(n_cell) == 3:
                    new_life.add(n_cell)
        self.life_cells = new_life

    def zoom_life_view_about(self, demo, anchor_local: Tuple[float, float], new_size: int) -> None:
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
        self.set_life_zoom_label()

    def life_window_preamble(self) -> None:
        """Window preamble hook that reconciles zoom changes from slider position."""
        slider_value = max(0, min(11, int(round(self.zoom_slider.value))))
        self.sync_life_zoom_from_slider(slider_value)

    def on_life_zoom_slider_changed(self, value: float) -> None:
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
        self.zoom_life_view_about(self.demo, center_local, new_size)

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

        if event.is_mouse_down(4) or event.is_mouse_down(5):
            pos = event.pos
            if pos is not None and canvas.rect.collidepoint(pos):
                wheel_step = 1 if event.button == 4 else -1
                anchor_local = (pos[0] - canvas.rect.left, pos[1] - canvas.rect.top)
                self.zoom_life_view_about(demo, anchor_local, self.life_cell_size + (wheel_step * 2))
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
                self.zoom_life_view_about(demo, anchor_local, self.life_cell_size + (event.wheel_delta * 2))
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
            if cell in self.life_cells:
                self.life_cells.remove(cell)
            else:
                self.life_cells.add(cell)

        if toggle.pushed:
            self.life_step(demo)

        cell_size = max(2, int(round(self.life_cell_size)))
        canvas.canvas.fill(demo.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.life_cells:
            px = int(self.life_origin[0] + (cx * cell_size))
            py = int(self.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= canvas.rect.width and -cell_size <= py <= canvas.rect.height:
                canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))
