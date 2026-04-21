import math
from typing import Set, Tuple

import pygame
from pygame import Rect

from gui import (
    ButtonControl,
    CanvasControl,
    GuiApplication,
    LabelControl,
    LayoutAxis,
    PanelControl,
    SliderControl,
    TaskPanelControl,
    ToggleControl,
    UiEngine,
    WindowControl,
)


class GuiDoDemo:
    neighbours = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )

    mandel_cols = (
        (66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
        (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
        (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
        (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
    )

    def __init__(self) -> None:
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

        self._build_main_scene()
        self.app.set_pristine("backdrop.jpg", scene_name="main")
        self._bind_runtime()
        self.app.set_screen_lifecycle(
            preamble=self._screen_preamble,
            event_handler=self._screen_event_handler,
            postamble=self._screen_postamble,
        )

        self.app.update = self._update

    def _build_main_scene(self) -> None:
        self.root = self.app.add(
            PanelControl("main_root", Rect(0, 0, self.screen_rect.width, self.screen_rect.height), draw_background=False),
            scene_name="main",
        )
        self._build_life_window()
        self._build_mandelbrot_window()
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
                "Mandlebrot",
                "Mandlebrot",
                pushed=True,
                on_toggle=self._toggle_mandel_window,
                style="round",
            )
        )
        self._tile_visible_windows()

    def _set_text(self, label: LabelControl, size: int = 16) -> LabelControl:
        label.title = False
        label.text_size = size
        return label

    def _build_life_window(self) -> None:
        life_rect = self.app.layout.anchored((640, 640), anchor="top_right", margin=(28, 92), use_rect=True)
        self.life_window = self.root.add(
            WindowControl(
                "life_window",
                life_rect,
                "Conway's Game of Life",
                preamble=self._life_window_preamble,
                event_handler=self._life_window_event_handler,
                postamble=self._life_window_postamble,
            )
        )
        content_rect = self.life_window.content_rect()
        left = content_rect.left
        top = content_rect.top
        width = content_rect.width
        height = content_rect.height
        widget_height = 28
        padding = 10

        self.life_canvas = self.life_window.add(
            CanvasControl("life_canvas", Rect(left + padding, top + padding, width - (padding * 2), height - (widget_height * 2)), max_events=256)
        )

        controls_y = top + height - widget_height - padding
        self.life_reset_button = self.life_window.add(
            ButtonControl("life_reset", Rect(left + padding, controls_y, 100, widget_height), "Reset", self._life_reset, style="angle")
        )
        self.life_toggle = self.life_window.add(
            ToggleControl(
                "life_toggle",
                Rect(left + padding + 102, controls_y, 100, widget_height),
                "Stop",
                "Start",
                pushed=False,
                style="round",
            )
        )

        zoom_label_width = 60
        zoom_label_x = self.life_canvas.rect.right - zoom_label_width
        slider_left = self.life_toggle.rect.right + 12
        slider_right = zoom_label_x - 8
        self.life_zoom_slider = self.life_window.add(
            SliderControl(
                "life_zoom",
                Rect(slider_left, controls_y, max(80, slider_right - slider_left), widget_height),
                LayoutAxis.HORIZONTAL,
                0.0,
                11.0,
                5.0,
            )
        )
        self._life_zoom_slider_last_value = int(round(self.life_zoom_slider.value))
        self.life_zoom_label = self._set_text(
            self.life_window.add(LabelControl("life_zoom_label", Rect(zoom_label_x, controls_y + 6, zoom_label_width, 20), "Zoom"))
        )

        self.life_origin = [self.life_canvas.rect.width // 2, self.life_canvas.rect.height // 2]
        self._life_reset()
        self.life_window.visible = False

    def _build_mandelbrot_window(self) -> None:
        mandel_rect = self.app.layout.anchored((640, 724), anchor="top_right", margin=(28, 92), use_rect=True)
        self.mandel_window = self.root.add(WindowControl("mandel_window", mandel_rect, "Mandelbrot"))
        left = mandel_rect.left
        top = mandel_rect.top
        canvas_size = 580
        canvas_x = left + 20
        canvas_y = top + 54
        split_gap = 6
        split_size = (canvas_size - split_gap) // 2
        controls_y = canvas_y + canvas_size + 12
        status_y = controls_y + 38

        self._set_text(
            self.mandel_window.add(
                LabelControl(
                    "mandel_help",
                    Rect(left + 20, top + 30, 590, 20),
                    "Render modes: Iterative, Recursive, 1M 4Tasks, and 4M 4Tasks",
                )
            )
        )
        self.mandel_canvas = self.mandel_window.add(CanvasControl("mandel_canvas", Rect(canvas_x, canvas_y, canvas_size, canvas_size), max_events=128))
        self.mandel_canvas_rect = Rect(canvas_x, canvas_y, canvas_size, canvas_size)
        self.canvas1 = self.mandel_window.add(CanvasControl("can1", Rect(canvas_x, canvas_y, split_size, split_size), max_events=32))
        self.canvas2 = self.mandel_window.add(CanvasControl("can2", Rect(canvas_x + split_size + split_gap, canvas_y, split_size, split_size), max_events=32))
        self.canvas3 = self.mandel_window.add(CanvasControl("can3", Rect(canvas_x, canvas_y + split_size + split_gap, split_size, split_size), max_events=32))
        self.canvas4 = self.mandel_window.add(
            CanvasControl("can4", Rect(canvas_x + split_size + split_gap, canvas_y + split_size + split_gap, split_size, split_size), max_events=32)
        )

        self.mandel_reset_button = self.mandel_window.add(
            ButtonControl("mandel_reset", Rect(left + 20, controls_y, 112, 30), "Reset", self._clear_mandel, style="angle")
        )
        self.mandel_iter_button = self.mandel_window.add(
            ButtonControl("mandel_iter", Rect(left + 140, controls_y, 112, 30), "Iterative", self._launch_mandel_iterative, style="round")
        )
        self.mandel_recur_button = self.mandel_window.add(
            ButtonControl("mandel_recur", Rect(left + 260, controls_y, 112, 30), "Recursive", self._launch_mandel_recursive, style="round")
        )
        self.mandel_one_split_button = self.mandel_window.add(
            ButtonControl("mandel_one_split", Rect(left + 380, controls_y, 112, 30), "1M 4Tasks", self._launch_mandel_one_split, style="round")
        )
        self.mandel_four_split_button = self.mandel_window.add(
            ButtonControl("mandel_four_split", Rect(left + 500, controls_y, 112, 30), "4M 4Tasks", self._launch_mandel_four_split, style="round")
        )
        self.mandel_task_buttons = (
            self.mandel_iter_button,
            self.mandel_recur_button,
            self.mandel_one_split_button,
            self.mandel_four_split_button,
        )

        self.mandel_status = self._set_text(
            self.mandel_window.add(LabelControl("mandel_status", Rect(left + 20, status_y, 590, 20), "Mandelbrot: idle"))
        )

        self.canvas1.visible = False
        self.canvas2.visible = False
        self.canvas3.visible = False
        self.canvas4.visible = False
        self._set_mandel_task_buttons_disabled(False)
        self._clear_mandel()
        self.mandel_window.visible = False

    def _bind_runtime(self) -> None:
        self.life_scheduler.set_message_dispatch_limit(256)
        self.mandel_scheduler.set_message_dispatch_limit(256)

    def _toggle_life_window(self, pushed: bool) -> None:
        self.life_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.life_window])
        else:
            self._tile_visible_windows()

    def _toggle_mandel_window(self, pushed: bool) -> None:
        self.mandel_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.mandel_window])
        else:
            self._tile_visible_windows()

    def _visible_windows_for_tiling(self):
        windows = []
        for name in ("life_window", "mandel_window"):
            window = getattr(self, name, None)
            if window is not None and window.visible:
                windows.append(window)
        return windows

    def _tile_visible_windows(self, newly_visible=None) -> None:
        if not self.app.read_window_tiling_settings().get("enabled", False):
            return
        if newly_visible is None:
            newly_visible = self._visible_windows_for_tiling()
        self.app.tile_windows(newly_visible=newly_visible)

    def _exit_app(self) -> None:
        self.app.running = False

    def _life_reset(self) -> None:
        self.life_cells.clear()
        self.life_cells.update({(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)})
        self.life_origin = [self.life_canvas.rect.width / 2.0, self.life_canvas.rect.height / 2.0]
        self.life_cell_size = 12
        self.life_zoom_slider.value = 5.0
        self._life_zoom_slider_last_value = int(round(self.life_zoom_slider.value))
        self.life_toggle.pushed = False

    def _life_population(self, cell: Tuple[int, int]) -> int:
        count = 0
        for dx, dy in self.neighbours:
            if (cell[0] + dx, cell[1] + dy) in self.life_cells:
                count += 1
        return count

    def _life_step(self) -> None:
        new_life: Set[Tuple[int, int]] = set()
        for cell in self.life_cells:
            pop = self._life_population(cell)
            if pop in (2, 3):
                new_life.add(cell)
            for dx, dy in self.neighbours:
                n_cell = (cell[0] + dx, cell[1] + dy)
                if self._life_population(n_cell) == 3:
                    new_life.add(n_cell)
        self.life_cells = new_life

    def _zoom_life_view_about(self, anchor_local: Tuple[float, float], new_size: int) -> None:
        old_size = max(2, int(round(self.life_cell_size)))
        clamped_size = max(2, min(24, int(new_size)))
        if clamped_size == old_size:
            return
        anchor_x, anchor_y = anchor_local
        self.life_origin[0] = anchor_x - ((anchor_x - self.life_origin[0]) / old_size) * clamped_size
        self.life_origin[1] = anchor_y - ((anchor_y - self.life_origin[1]) / old_size) * clamped_size
        self.life_cell_size = clamped_size
        slider_value = max(0, min(11, (clamped_size // 2) - 1))
        self.life_zoom_slider.value = float(slider_value)
        self._life_zoom_slider_last_value = int(slider_value)

    def _life_window_preamble(self) -> None:
        slider_value = max(0, min(11, int(round(self.life_zoom_slider.value))))
        if slider_value == self._life_zoom_slider_last_value:
            return
        old_size = max(2, int(round(self.life_cell_size)))
        new_size = (slider_value + 1) * 2
        if new_size == old_size:
            self._life_zoom_slider_last_value = slider_value
            return
        self._life_zoom_slider_last_value = slider_value
        center_local = (self.life_canvas.rect.width / 2.0, self.life_canvas.rect.height / 2.0)
        self._zoom_life_view_about(center_local, new_size)

    def _life_window_event_handler(self, event) -> bool:
        if event.is_mouse_down(3) and event.collides(self.life_canvas.rect):
            pos = event.pos
            if pos is not None:
                self.life_dragging = True
                self.app.set_cursor("hand")
                self.app.set_lock_point(self.life_canvas, pos)
                return True

        if event.is_mouse_up(3):
            if self.life_dragging:
                self.life_dragging = False
                self.app.set_cursor("normal")
                self.app.set_lock_point(None)
                return True

        if event.is_mouse_motion() and self.life_dragging:
            delta = self.app.get_lock_point_motion_delta(event)
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
            if pos is not None and self.life_canvas.rect.collidepoint(pos):
                wheel_step = 1 if event.button == 4 else -1
                anchor_local = (pos[0] - self.life_canvas.rect.left, pos[1] - self.life_canvas.rect.top)
                self._zoom_life_view_about(anchor_local, self.life_cell_size + (wheel_step * 2))
                return True

        if event.is_mouse_wheel():
            pointer_pos = self.app.lock_point_pos if self.app.mouse_point_locked and self.app.lock_point_pos is not None else event.pos
            if pointer_pos is not None and self.life_canvas.rect.collidepoint(pointer_pos):
                if self.app.mouse_point_locked and self.app.lock_point_pos is not None:
                    lock_window_pos = self.app.convert_to_window(self.app.lock_point_pos, self.life_window)
                    canvas_window_left = self.life_canvas.rect.left - self.life_window.rect.left
                    canvas_window_top = self.life_canvas.rect.top - self.life_window.rect.top
                    anchor_local = (lock_window_pos[0] - canvas_window_left, lock_window_pos[1] - canvas_window_top)
                else:
                    anchor_local = (pointer_pos[0] - self.life_canvas.rect.left, pointer_pos[1] - self.life_canvas.rect.top)
                self._zoom_life_view_about(anchor_local, self.life_cell_size + (event.wheel_delta * 2))
                return True

        return False

    def _life_window_postamble(self) -> None:
        self._update_life()

    def _mandel_col(self, k: int) -> Tuple[int, int, int]:
        if k >= self.max_iter - 1:
            return (0, 0, 0)
        return self.mandel_cols[k % len(self.mandel_cols)]

    def _mandel_viewport(self, width: int, height: int) -> Tuple[complex, float]:
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        return center, scale

    def _mandel_pixel(self, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(self.max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return self.max_iter - 1

    def _clear_mandel_surfaces(self) -> None:
        self.mandel_canvas.canvas.fill(self.app.theme.medium)
        self.canvas1.canvas.fill(self.app.theme.medium)
        self.canvas2.canvas.fill(self.app.theme.medium)
        self.canvas3.canvas.fill(self.app.theme.medium)
        self.canvas4.canvas.fill(self.app.theme.medium)

    def _set_mandel_task_buttons_disabled(self, disabled: bool) -> None:
        for button in self.mandel_task_buttons:
            button.enabled = not disabled

    def _show_single_mandel_canvas(self) -> None:
        self.mandel_canvas.visible = True
        self.canvas1.visible = False
        self.canvas2.visible = False
        self.canvas3.visible = False
        self.canvas4.visible = False
        self._clear_mandel_surfaces()

    def _prepare_mandel_single_canvas_run(self) -> None:
        self._set_mandel_task_buttons_disabled(True)
        self._show_single_mandel_canvas()

    def _prepare_mandel_split_canvas_run(self) -> None:
        self._set_mandel_task_buttons_disabled(True)
        self.mandel_canvas.visible = False
        self.canvas1.visible = True
        self.canvas2.visible = True
        self.canvas3.visible = True
        self.canvas4.visible = True
        self._clear_mandel_surfaces()

    def _mandel_canvas_for_task(self, task_id: str):
        canvas_by_task = {
            "iter": self.mandel_canvas.canvas,
            "recu": self.mandel_canvas.canvas,
            "1": self.mandel_canvas.canvas,
            "2": self.mandel_canvas.canvas,
            "3": self.mandel_canvas.canvas,
            "4": self.mandel_canvas.canvas,
            "can1": self.canvas1.canvas,
            "can2": self.canvas2.canvas,
            "can3": self.canvas3.canvas,
            "can4": self.canvas4.canvas,
        }
        return canvas_by_task.get(task_id)

    def _make_mandel_progress_handler(self, task_id: str):
        def handler(payload):
            self._apply_mandel_result(task_id, payload)

        return handler

    def _apply_mandel_result(self, task_id: str, payload) -> None:
        canvas = self._mandel_canvas_for_task(task_id)
        if canvas is None:
            return

        if task_id == "iter":
            y_pos, row = payload
            if y_pos < 0 or y_pos >= canvas.get_height():
                return
            for x_pos, value in enumerate(row):
                if 0 <= x_pos < canvas.get_width():
                    canvas.set_at((x_pos, y_pos), self._mandel_col(value))
            return

        x_pos, y_pos, width, height, values = payload
        x0 = max(0, x_pos)
        y0 = max(0, y_pos)
        x1 = min(canvas.get_width(), x_pos + width)
        y1 = min(canvas.get_height(), y_pos + height)
        if x1 <= x0 or y1 <= y0:
            return

        if isinstance(values, int):
            canvas.fill(self._mandel_col(values), Rect(x0, y0, x1 - x0, y1 - y0))
            return

        src_w = max(1, width)
        if (x0, y0, x1, y1) != (x_pos, y_pos, x_pos + width, y_pos + height):
            clipped_values = []
            for row_index in range(y0 - y_pos, y1 - y_pos):
                start = row_index * src_w + (x0 - x_pos)
                end = start + (x1 - x0)
                clipped_values.extend(values[start:end])
            values = clipped_values
            x_pos, y_pos, width, height = x0, y0, x1 - x0, y1 - y0

        idx = 0
        for yy in range(y_pos, y_pos + height):
            for xx in range(x_pos, x_pos + width):
                canvas.set_at((xx, yy), self._mandel_col(values[idx]))
                idx += 1

    def _clear_mandel(self) -> None:
        self.mandel_scheduler.remove_tasks(*self.mandel_task_id_pool)
        self.mandel_task_ids.clear()
        self._show_single_mandel_canvas()
        self._set_mandel_task_buttons_disabled(False)
        self.mandel_status.text = "Mandelbrot: cleared"

    def _mandel_iterative_task(self, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [self._mandel_pixel(x, y, width, height, center, scale) for x in range(width)]
            self.mandel_scheduler.send_message(task_id, (y, row))
        return None

    def _recursive_fill(self, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
        if w <= 0 or h <= 0:
            return
        tl = self._mandel_pixel(x, y, width, height, center, scale)
        tr = self._mandel_pixel(x + w - 1, y, width, height, center, scale)
        bl = self._mandel_pixel(x, y + h - 1, width, height, center, scale)
        br = self._mandel_pixel(x + w - 1, y + h - 1, width, height, center, scale)
        if w <= 4 or h <= 4:
            values = []
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    values.append(self._mandel_pixel(xx, yy, width, height, center, scale))
            self.mandel_scheduler.send_message(task_id, (x, y, w, h, values))
            return
        if tl == tr == bl == br:
            self.mandel_scheduler.send_message(task_id, (x, y, w, h, tl))
            return
        hw = w // 2
        hh = h // 2
        self._recursive_fill(task_id, x, y, hw, hh, width, height, center, scale)
        self._recursive_fill(task_id, x + hw, y, w - hw, hh, width, height, center, scale)
        self._recursive_fill(task_id, x, y + hh, hw, h - hh, width, height, center, scale)
        self._recursive_fill(task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

    def _mandel_recursive_task(self, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        rect = Rect(params.get("rect", Rect(0, 0, width, height)))
        self._recursive_fill(task_id, rect.x, rect.y, rect.width, rect.height, width, height, center, scale)
        return None

    def _queue_mandel_recursive_task(self, task_id: str, rect: Rect, size: Tuple[int, int], center: complex, scale: float) -> None:
        self.mandel_scheduler.add_task(
            task_id,
            self._mandel_recursive_task,
            parameters={"size": size, "center": center, "scale": scale, "rect": Rect(rect)},
            message_method=self._make_mandel_progress_handler(task_id),
        )
        self.mandel_task_ids.add(task_id)

    def _launch_mandel_iterative(self) -> None:
        if self.mandel_scheduler.tasks_busy_match_any(*self.mandel_task_id_pool):
            return
        self._prepare_mandel_single_canvas_run()
        width, height = self.mandel_canvas.canvas.get_size()
        center, scale = self._mandel_viewport(width, height)
        self.mandel_scheduler.add_task(
            "iter",
            self._mandel_iterative_task,
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=self._make_mandel_progress_handler("iter"),
        )
        self.mandel_task_ids.add("iter")
        self.mandel_status.text = "Mandelbrot: running iterative"

    def _launch_mandel_recursive(self) -> None:
        if self.mandel_scheduler.tasks_busy_match_any(*self.mandel_task_id_pool):
            return
        self._prepare_mandel_single_canvas_run()
        width, height = self.mandel_canvas.canvas.get_size()
        center, scale = self._mandel_viewport(width, height)
        self._queue_mandel_recursive_task("recu", Rect(0, 0, width, height), (width, height), center, scale)
        self.mandel_status.text = "Mandelbrot: running recursive"

    def _launch_mandel_one_split(self) -> None:
        if self.mandel_scheduler.tasks_busy_match_any(*self.mandel_task_id_pool):
            return
        self._prepare_mandel_single_canvas_run()
        width, height = self.mandel_canvas.canvas.get_size()
        center, scale = self._mandel_viewport(width, height)
        left_w, top_h = width // 2, height // 2
        right_w, bottom_h = width - left_w, height - top_h
        self._queue_mandel_recursive_task("1", Rect(0, 0, left_w, top_h), (width, height), center, scale)
        self._queue_mandel_recursive_task("2", Rect(left_w, 0, right_w, top_h), (width, height), center, scale)
        self._queue_mandel_recursive_task("3", Rect(0, top_h, left_w, bottom_h), (width, height), center, scale)
        self._queue_mandel_recursive_task("4", Rect(left_w, top_h, right_w, bottom_h), (width, height), center, scale)
        self.mandel_status.text = "Mandelbrot: running 1M 4Tasks"

    def _launch_mandel_four_split(self) -> None:
        if self.mandel_scheduler.tasks_busy_match_any(*self.mandel_task_id_pool):
            return
        self._prepare_mandel_split_canvas_run()
        width, height = self.canvas1.canvas.get_size()
        center, scale = self._mandel_viewport(width, height)
        for task_id in ("can1", "can2", "can3", "can4"):
            self._queue_mandel_recursive_task(task_id, Rect(0, 0, width, height), (width, height), center, scale)
        self.mandel_status.text = "Mandelbrot: running 4M 4Tasks"

    def _update_life(self) -> None:
        while True:
            packet = self.life_canvas.read_event()
            if packet is None:
                break
            if packet.pos is None or packet.button != 1:
                continue
            if packet.event_type != pygame.MOUSEBUTTONDOWN:
                continue
            local_x = packet.pos[0] - self.life_canvas.rect.left
            local_y = packet.pos[1] - self.life_canvas.rect.top
            cell_size = max(2, int(round(self.life_cell_size)))
            cell_x = math.floor((local_x - self.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - self.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if cell in self.life_cells:
                self.life_cells.remove(cell)
            else:
                self.life_cells.add(cell)

        if self.life_toggle.pushed:
            self._life_step()

        cell_size = max(2, int(round(self.life_cell_size)))
        self.life_canvas.canvas.fill(self.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.life_cells:
            px = int(self.life_origin[0] + (cx * cell_size))
            py = int(self.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= self.life_canvas.rect.width and -cell_size <= py <= self.life_canvas.rect.height:
                self.life_canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))

    def _update_mandel_events(self) -> None:
        finished = self.mandel_scheduler.get_finished_events()
        failed = self.mandel_scheduler.get_failed_events()

        for event in finished:
            if event.task_id in self.mandel_task_ids:
                self.mandel_task_ids.remove(event.task_id)
                self.mandel_scheduler.pop_result(event.task_id, None)
        for event in failed:
            if event.task_id in self.mandel_task_ids:
                self.mandel_task_ids.remove(event.task_id)
                self.mandel_status.text = f"Mandelbrot failed: {event.error}"

        busy = self.mandel_scheduler.tasks_busy_match_any(*self.mandel_task_id_pool)
        self._set_mandel_task_buttons_disabled(busy)
        self.mandel_scheduler.clear_events()
        if not busy and self.mandel_status.text.startswith("Mandelbrot: running"):
            self.mandel_status.text = "Mandelbrot: complete"

    def _update(self, dt_seconds: float) -> None:
        GuiApplication.update(self.app, dt_seconds)

    def _screen_preamble(self) -> None:
        return None

    def _screen_event_handler(self, event) -> bool:
        if event.is_key_down(pygame.K_ESCAPE):
            self._exit_app()
            return True
        return False

    def _screen_postamble(self) -> None:
        self._update_mandel_events()

    def run(self) -> None:
        UiEngine(self.app, target_fps=120).run()
        pygame.quit()


def main() -> None:
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
