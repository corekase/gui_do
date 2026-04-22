"""Life simulation feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import math
from typing import Set, Tuple

from pygame import Rect


class LifeSimulationFeature:
    """Build and run the Conway's Game of Life feature window and interactions."""

    name = "life_simulation"

    def build(self, demo) -> None:
        self.build_window(
            demo,
            window_control_cls=demo._window_control_cls,
            canvas_control_cls=demo._canvas_control_cls,
            button_control_cls=demo._button_control_cls,
            toggle_control_cls=demo._toggle_control_cls,
            slider_control_cls=demo._slider_control_cls,
            label_control_cls=demo._label_control_cls,
            layout_axis_cls=demo._layout_axis_cls,
        )

    def bind_runtime(self, demo) -> None:
        demo.life_scheduler.set_message_dispatch_limit(256)

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
        controls = [
            demo.life_reset_button,
            demo.life_toggle,
            demo.life_zoom_slider,
        ]
        roles = [
            ("button", "Reset life board"),
            ("toggle", "Run life simulation"),
            ("slider", "Life zoom"),
        ]
        next_index = int(tab_index_start)
        for control, (role, label) in zip(controls, roles):
            control.set_tab_index(next_index)
            control.set_accessibility(role=role, label=label)
            next_index += 1
        return next_index

    def on_post_frame(self, demo) -> None:
        return None

    @staticmethod
    def build_window(
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
        life_rect = demo.app.layout.anchored((640, 640), anchor="top_right", margin=(28, 92), use_rect=True)
        demo.life_window = demo.root.add(
            window_control_cls(
                "life_window",
                life_rect,
                "Conway's Game of Life",
                preamble=demo._life_window_preamble,
                event_handler=demo._life_window_event_handler,
                postamble=demo._life_window_postamble,
            )
        )
        content_rect = demo.life_window.content_rect()
        left = content_rect.left
        top = content_rect.top
        width = content_rect.width
        height = content_rect.height
        widget_height = 28
        padding = 10

        demo.life_canvas = demo.life_window.add(
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

        demo.life_reset_button = demo.life_window.add(
            button_control_cls("life_reset", life_reset_rect, "Reset", demo._life_reset, style="angle")
        )
        demo.life_toggle = demo.life_window.add(
            toggle_control_cls(
                "life_toggle",
                life_toggle_rect,
                "Stop",
                "Start",
                pushed=False,
                style="round",
            )
        )

        slider_left = zoom_slider_slot_1.left
        slider_right = zoom_slider_slot_2.right
        demo.life_zoom_slider = demo.life_window.add(
            slider_control_cls(
                "life_zoom",
                Rect(slider_left, controls_y, max(80, slider_right - slider_left), widget_height),
                layout_axis_cls.HORIZONTAL,
                0.0,
                11.0,
                5.0,
                on_change=demo._on_life_zoom_slider_changed,
            )
        )
        demo._life_zoom_slider_last_value = int(round(demo.life_zoom_slider.value))
        zoom_label_rect = Rect(zoom_label_slot.left + 24, controls_y + 6, 76, 20)
        demo.life_zoom_label = demo._set_text(
            demo.life_window.add(label_control_cls("life_zoom_label", zoom_label_rect, "Zoom 12"))
        )

        demo.life_origin = [demo.life_canvas.rect.width // 2, demo.life_canvas.rect.height // 2]
        LifeSimulationFeature.life_reset(demo)
        demo.life_window.visible = False

    @staticmethod
    def set_life_zoom_label(demo) -> None:
        zoom_level = max(2, int(round(demo.life_cell_size)))
        demo.life_zoom_label.text = f"Zoom {zoom_level}"

    @staticmethod
    def life_reset(demo) -> None:
        demo.life_cells.clear()
        demo.life_cells.update({(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)})
        demo.life_origin = [demo.life_canvas.rect.width / 2.0, demo.life_canvas.rect.height / 2.0]
        demo.life_cell_size = 12
        demo.life_zoom_slider.value = 5.0
        demo._life_zoom_slider_last_value = int(round(demo.life_zoom_slider.value))
        LifeSimulationFeature.set_life_zoom_label(demo)
        demo.life_toggle.pushed = False

    @staticmethod
    def life_population(demo, cell: Tuple[int, int]) -> int:
        count = 0
        for dx, dy in demo.neighbours:
            if (cell[0] + dx, cell[1] + dy) in demo.life_cells:
                count += 1
        return count

    @staticmethod
    def life_step(demo) -> None:
        new_life: Set[Tuple[int, int]] = set()
        for cell in demo.life_cells:
            pop = LifeSimulationFeature.life_population(demo, cell)
            if pop in (2, 3):
                new_life.add(cell)
            for dx, dy in demo.neighbours:
                n_cell = (cell[0] + dx, cell[1] + dy)
                if LifeSimulationFeature.life_population(demo, n_cell) == 3:
                    new_life.add(n_cell)
        demo.life_cells = new_life

    @staticmethod
    def zoom_life_view_about(demo, anchor_local: Tuple[float, float], new_size: int) -> None:
        old_size = max(2, int(round(demo.life_cell_size)))
        clamped_size = max(2, min(24, int(new_size)))
        if clamped_size == old_size:
            return
        anchor_x, anchor_y = anchor_local
        demo.life_origin[0] = anchor_x - ((anchor_x - demo.life_origin[0]) / old_size) * clamped_size
        demo.life_origin[1] = anchor_y - ((anchor_y - demo.life_origin[1]) / old_size) * clamped_size
        demo.life_cell_size = clamped_size
        slider_value = max(0, min(11, (clamped_size // 2) - 1))
        demo.life_zoom_slider.value = float(slider_value)
        demo._life_zoom_slider_last_value = int(slider_value)
        LifeSimulationFeature.set_life_zoom_label(demo)

    @staticmethod
    def life_window_preamble(demo) -> None:
        slider_value = max(0, min(11, int(round(demo.life_zoom_slider.value))))
        LifeSimulationFeature.sync_life_zoom_from_slider(demo, slider_value)

    @staticmethod
    def on_life_zoom_slider_changed(demo, value: float) -> None:
        LifeSimulationFeature.sync_life_zoom_from_slider(demo, int(round(value)))

    @staticmethod
    def sync_life_zoom_from_slider(demo, slider_value: int) -> None:
        if slider_value == demo._life_zoom_slider_last_value:
            return
        old_size = max(2, int(round(demo.life_cell_size)))
        new_size = (slider_value + 1) * 2
        if new_size == old_size:
            demo._life_zoom_slider_last_value = slider_value
            return
        demo._life_zoom_slider_last_value = slider_value
        center_local = (demo.life_canvas.rect.width / 2.0, demo.life_canvas.rect.height / 2.0)
        LifeSimulationFeature.zoom_life_view_about(demo, center_local, new_size)

    @staticmethod
    def life_window_event_handler(demo, event) -> bool:
        if event.is_mouse_down(3) and event.collides(demo.life_canvas.rect):
            pos = event.pos
            if pos is not None:
                demo.life_dragging = True
                demo.app.set_cursor("hand")
                demo.app.set_lock_point(demo.life_canvas, pos)
                return True

        if event.is_mouse_up(3):
            if demo.life_dragging:
                demo.life_dragging = False
                demo.app.set_cursor("normal")
                demo.app.set_lock_point(None)
                return True

        if event.is_mouse_motion() and demo.life_dragging:
            delta = demo.app.get_lock_point_motion_delta(event)
            if delta is None:
                rel = event.rel
                if isinstance(rel, tuple) and len(rel) == 2:
                    delta = (rel[0], rel[1])
                else:
                    delta = (0, 0)
            demo.life_origin[0] -= delta[0]
            demo.life_origin[1] -= delta[1]
            return True

        if event.is_mouse_down(4) or event.is_mouse_down(5):
            pos = event.pos
            if pos is not None and demo.life_canvas.rect.collidepoint(pos):
                wheel_step = 1 if event.button == 4 else -1
                anchor_local = (pos[0] - demo.life_canvas.rect.left, pos[1] - demo.life_canvas.rect.top)
                LifeSimulationFeature.zoom_life_view_about(demo, anchor_local, demo.life_cell_size + (wheel_step * 2))
                return True

        if event.is_mouse_wheel():
            pointer_pos = demo.app.lock_point_pos if demo.app.mouse_point_locked and demo.app.lock_point_pos is not None else event.pos
            if pointer_pos is not None and demo.life_canvas.rect.collidepoint(pointer_pos):
                if demo.app.mouse_point_locked and demo.app.lock_point_pos is not None:
                    lock_window_pos = demo.app.convert_to_window(demo.app.lock_point_pos, demo.life_window)
                    canvas_window_left = demo.life_canvas.rect.left - demo.life_window.rect.left
                    canvas_window_top = demo.life_canvas.rect.top - demo.life_window.rect.top
                    anchor_local = (lock_window_pos[0] - canvas_window_left, lock_window_pos[1] - canvas_window_top)
                else:
                    anchor_local = (pointer_pos[0] - demo.life_canvas.rect.left, pointer_pos[1] - demo.life_canvas.rect.top)
                LifeSimulationFeature.zoom_life_view_about(demo, anchor_local, demo.life_cell_size + (event.wheel_delta * 2))
                return True

        return False

    @staticmethod
    def life_window_postamble(demo) -> None:
        LifeSimulationFeature.update_life(demo)

    @staticmethod
    def update_life(demo) -> None:
        while True:
            packet = demo.life_canvas.read_event()
            if packet is None:
                break
            if not packet.is_mouse_down(1):
                continue
            if packet.local_pos is not None:
                local_x, local_y = packet.local_pos
            elif packet.pos is not None:
                local_x = packet.pos[0] - demo.life_canvas.rect.left
                local_y = packet.pos[1] - demo.life_canvas.rect.top
            else:
                continue
            cell_size = max(2, int(round(demo.life_cell_size)))
            cell_x = math.floor((local_x - demo.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - demo.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if cell in demo.life_cells:
                demo.life_cells.remove(cell)
            else:
                demo.life_cells.add(cell)

        if demo.life_toggle.pushed:
            LifeSimulationFeature.life_step(demo)

        cell_size = max(2, int(round(demo.life_cell_size)))
        demo.life_canvas.canvas.fill(demo.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in demo.life_cells:
            px = int(demo.life_origin[0] + (cx * cell_size))
            py = int(demo.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= demo.life_canvas.rect.width and -cell_size <= py <= demo.life_canvas.rect.height:
                demo.life_canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))
