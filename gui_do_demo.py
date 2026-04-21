import math
import time
from random import randint
from typing import Optional, Set, Tuple

import pygame
from pygame import Rect

from gui import (
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    FrameControl,
    GuiApplication,
    ImageControl,
    LabelControl,
    LayoutAxis,
    PanelControl,
    ScrollbarControl,
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
        self.root = self.app.add(PanelControl("root", Rect(0, 0, self.screen_rect.width, self.screen_rect.height)))

        self.ticks = 0
        self.arrow_hits = 0
        self.life_cells: Set[Tuple[int, int]] = set()
        self.life_origin = [0, 0]
        self.mandel_task_ids: Set[str] = set()
        self.max_iter = 96

        self._build_shell()
        self._build_widget_showcase_window()
        self._build_life_window()
        self._build_mandelbrot_window()
        self._bind_runtime()

        self.app.update = self._update

    def _set_title(self, label: LabelControl, size: int = 22) -> LabelControl:
        label.title = True
        label.text_size = size
        return label

    def _set_text(self, label: LabelControl, size: int = 16) -> LabelControl:
        label.title = False
        label.text_size = size
        return label

    def _build_shell(self) -> None:
        self._set_title(
            self.root.add(LabelControl("header", Rect(28, 20, 900, 30), "gui_do legacy widget showcase (rebased OOP demo)")),
            24,
        )
        self._set_text(
            self.root.add(
                LabelControl(
                    "sub_header",
                    Rect(28, 52, 1300, 22),
                    "old demo behaviors: style showcase, life, mandelbrot, task panel, and window layering/drag",
                )
            ),
            16,
        )

        self.root.add(ImageControl("realize", Rect(self.screen_rect.width - 156, 14, 140, 72), "data/images/realize.png", scale=True))

        self.panel_toggle = self.root.add(
            ToggleControl("panel_toggle", Rect(self.screen_rect.width - 570, 18, 180, 32), "Panel On", "Panel Off", pushed=True)
        )
        self.clock_toggle = self.root.add(
            ToggleControl("clock_toggle", Rect(self.screen_rect.width - 380, 18, 170, 32), "Clock On", "Clock Off", pushed=True)
        )
        self.clock_label = self._set_text(
            self.root.add(LabelControl("clock", Rect(self.screen_rect.width - 200, 26, 180, 20), "Clock: 0")),
            16,
        )

        self.task_panel = self.app.add(
            TaskPanelControl(
                "task_panel",
                Rect(0, self.screen_rect.height - 50, self.screen_rect.width, 50),
                auto_hide=True,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
            )
        )
        self._set_text(
            self.task_panel.add(LabelControl("task_label", Rect(16, self.screen_rect.height - 36, 110, 20), "Task panel")),
            16,
        )
        self.status_label = self._set_text(
            self.task_panel.add(LabelControl("task_status", Rect(130, self.screen_rect.height - 36, 640, 20), "Status: ready")),
            16,
        )

        self.task_panel.add(ButtonControl("show_showcase", Rect(640, self.screen_rect.height - 40, 140, 30), "Show Showcase", self._show_showcase))
        self.task_panel.add(ButtonControl("show_life", Rect(790, self.screen_rect.height - 40, 120, 30), "Show Life", self._show_life))
        self.task_panel.add(ButtonControl("show_mandel", Rect(920, self.screen_rect.height - 40, 150, 30), "Show Mandelbrot", self._show_mandel))
        self.task_panel.add(ButtonControl("run_worker", Rect(1080, self.screen_rect.height - 40, 120, 30), "Run Worker", self._run_worker))
        self.task_panel.add(ButtonControl("exit", Rect(self.screen_rect.width - 132, self.screen_rect.height - 40, 120, 30), "Exit", self._exit_app))

    def _build_widget_showcase_window(self) -> None:
        self.showcase_window = self.root.add(WindowControl("showcase_window", Rect(28, 92, 910, 940), "Widget Showcase"))

        self._set_text(
            self.showcase_window.add(
                LabelControl("show_help", Rect(46, 124, 820, 20), "Legacy-equivalent widgets: buttons, toggles, groups, sliders, scrollbars, arrows, canvas, image")
            )
        )

        self.showcase_window.add(FrameControl("style_frame", Rect(46, 152, 820, 214), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("style_title", Rect(58, 160, 420, 22), "Styles (box/round/angle/radio/check)")), 18)

        styles = ("box", "round", "angle", "radio", "check")
        for idx, style in enumerate(styles):
            x = 58 + (idx * 154)
            self.showcase_window.add(ButtonControl(f"btn_{style}", Rect(x, 196, 140, 30), f"{style.title()} Btn", style=style))
            self.showcase_window.add(
                ToggleControl(
                    f"tog_{style}",
                    Rect(x, 234, 140, 30),
                    f"{style.title()} On",
                    f"{style.title()} Off",
                    pushed=False,
                    style=style,
                )
            )

        self.showcase_window.add(ButtonGroupControl("bg_a", Rect(58, 274, 140, 30), "legacy_group", "Group A", selected=True))
        self.showcase_window.add(ButtonGroupControl("bg_b", Rect(212, 274, 140, 30), "legacy_group", "Group B", selected=False))
        self.showcase_window.add(ButtonGroupControl("bg_c", Rect(366, 274, 140, 30), "legacy_group", "Group C", selected=False))

        self.showcase_window.add(FrameControl("axis_frame", Rect(46, 378, 820, 214), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("axis_title", Rect(58, 386, 400, 22), "Sliders and Scrollbars")), 18)

        self.slider_h = self.showcase_window.add(
            SliderControl("slider_h", Rect(58, 428, 420, 30), LayoutAxis.HORIZONTAL, 0.0, 100.0, 42.0)
        )
        self.slider_h_label = self._set_text(self.showcase_window.add(LabelControl("slider_h_label", Rect(488, 434, 150, 20), "H: 42.00")))

        self.slider_v = self.showcase_window.add(
            SliderControl("slider_v", Rect(640, 426, 30, 140), LayoutAxis.VERTICAL, 0.0, 10.0, 5.0)
        )
        self.slider_v_label = self._set_text(self.showcase_window.add(LabelControl("slider_v_label", Rect(676, 484, 170, 20), "V: 5.00")))

        self.scroll_h = self.showcase_window.add(
            ScrollbarControl(
                "scroll_h",
                Rect(58, 470, 420, 24),
                LayoutAxis.HORIZONTAL,
                content_size=3000,
                viewport_size=640,
                offset=320,
                step=64,
            )
        )
        self.scroll_h_label = self._set_text(self.showcase_window.add(LabelControl("scroll_h_label", Rect(488, 472, 170, 20), "SH: 320")))

        self.scroll_v = self.showcase_window.add(
            ScrollbarControl(
                "scroll_v",
                Rect(710, 426, 24, 140),
                LayoutAxis.VERTICAL,
                content_size=2200,
                viewport_size=480,
                offset=220,
                step=48,
            )
        )
        self.scroll_v_label = self._set_text(self.showcase_window.add(LabelControl("scroll_v_label", Rect(740, 484, 120, 20), "SV: 220")))

        self.showcase_window.add(FrameControl("arrow_canvas_frame", Rect(46, 604, 820, 268), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("arrow_title", Rect(58, 612, 300, 22), "Arrow Boxes and Canvas")), 18)

        self.arrow_hits_label = self._set_text(self.showcase_window.add(LabelControl("arrow_hits", Rect(58, 646, 180, 20), "Arrow hits: 0")))
        self.showcase_window.add(ArrowBoxControl("arrow_left", Rect(58, 676, 36, 36), 180, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_right", Rect(102, 676, 36, 36), 0, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_up", Rect(146, 676, 36, 36), 270, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_down", Rect(190, 676, 36, 36), 90, on_activate=self._arrow_hit))

        self.canvas_status_label = self._set_text(
            self.showcase_window.add(LabelControl("canvas_status", Rect(256, 646, 590, 20), "Canvas: left click draws, right click clears"))
        )
        self.showcase_canvas = self.showcase_window.add(CanvasControl("showcase_canvas", Rect(256, 676, 594, 184), max_events=128))
        self.showcase_canvas.canvas.fill((0, 72, 72))
        self.showcase_canvas.set_overflow_mode("drop_oldest")
        self.showcase_canvas.set_overflow_handler(self._on_showcase_canvas_overflow)

        self.showcase_window.add(ImageControl("icon_img", Rect(58, 724, 150, 124), "data/images/realize.png", scale=True))
        self.showcase_window.add(ButtonControl("hide_showcase", Rect(730, 900, 120, 30), "Hide Window", self._hide_showcase))

    def _build_life_window(self) -> None:
        self.life_window = self.root.add(WindowControl("life_window", Rect(960, 92, 932, 460), "Conway's Game of Life"))
        self._set_text(
            self.life_window.add(LabelControl("life_help", Rect(978, 124, 500, 20), "Left click to toggle cells, Start for continuous update"))
        )

        self.life_canvas = self.life_window.add(CanvasControl("life_canvas", Rect(978, 150, 896, 330), max_events=256))
        self.life_toggle = self.life_window.add(ToggleControl("life_toggle", Rect(978, 490, 120, 30), "Stop", "Start", pushed=False))
        self.life_reset_button = self.life_window.add(ButtonControl("life_reset", Rect(1108, 490, 110, 30), "Reset", self._life_reset))
        self.life_step_button = self.life_window.add(ButtonControl("life_step", Rect(1228, 490, 110, 30), "Step", self._life_step))
        self.life_zoom_slider = self.life_window.add(
            SliderControl("life_zoom", Rect(1352, 488, 360, 32), LayoutAxis.HORIZONTAL, 2.0, 24.0, 12.0)
        )
        self.life_zoom_label = self._set_text(self.life_window.add(LabelControl("life_zoom_label", Rect(1720, 494, 120, 20), "Zoom: 12")))
        self.life_window.add(ButtonControl("hide_life", Rect(1750, 490, 124, 30), "Hide Window", self._hide_life))

        self.life_origin = [self.life_canvas.rect.width // 2, self.life_canvas.rect.height // 2]
        self._life_reset()
        self.life_window.visible = False

    def _build_mandelbrot_window(self) -> None:
        self.mandel_window = self.root.add(WindowControl("mandel_window", Rect(960, 572, 932, 460), "Mandelbrot"))
        self._set_text(
            self.mandel_window.add(LabelControl("mandel_help", Rect(978, 604, 540, 20), "Iterative and recursive renders run as scheduler tasks"))
        )
        self.mandel_canvas = self.mandel_window.add(CanvasControl("mandel_canvas", Rect(978, 630, 896, 330), max_events=128))
        self.mandel_iter_button = self.mandel_window.add(ButtonControl("mandel_iter", Rect(978, 970, 120, 30), "Iterative", self._launch_mandel_iterative))
        self.mandel_recur_button = self.mandel_window.add(ButtonControl("mandel_recur", Rect(1108, 970, 120, 30), "Recursive", self._launch_mandel_recursive))
        self.mandel_reset_button = self.mandel_window.add(ButtonControl("mandel_reset", Rect(1238, 970, 110, 30), "Reset", self._clear_mandel))
        self.mandel_status = self._set_text(
            self.mandel_window.add(LabelControl("mandel_status", Rect(1360, 976, 380, 20), "Mandelbrot: idle"))
        )
        self.mandel_window.add(ButtonControl("hide_mandel", Rect(1750, 970, 124, 30), "Hide Window", self._hide_mandel))

        self._clear_mandel()
        self.mandel_window.visible = False

    def _bind_runtime(self) -> None:
        self.app.timers.add_timer("demo.clock", 1.0, self._on_clock_tick)

    def _on_clock_tick(self) -> None:
        if self.clock_toggle.pushed:
            self.ticks += 1
            self.clock_label.text = f"Clock: {self.ticks}"

    def _show_showcase(self) -> None:
        self.showcase_window.visible = True
        self.status_label.text = "Status: showcase visible"

    def _hide_showcase(self) -> None:
        self.showcase_window.visible = False

    def _show_life(self) -> None:
        self.life_window.visible = True
        self.status_label.text = "Status: life window visible"

    def _hide_life(self) -> None:
        self.life_window.visible = False

    def _show_mandel(self) -> None:
        self.mandel_window.visible = True
        self.status_label.text = "Status: mandelbrot window visible"

    def _hide_mandel(self) -> None:
        self.mandel_window.visible = False

    def _run_worker(self) -> None:
        self.status_label.text = "Status: async worker started"

        def worker_logic(task_id, params):
            total = int(params.get("total", 18))
            for step in range(1, total + 1):
                time.sleep(0.05)
                self.app.scheduler.send_message(task_id, {"step": step, "total": total})
            return {"ok": True}

        task_id = f"worker-{time.time_ns()}"

        def on_worker(payload: dict) -> None:
            self.status_label.text = f"Status: worker {payload['step']}/{payload['total']}"

        self.app.scheduler.add_task(task_id, worker_logic, parameters={"total": 18}, message_method=on_worker)

    def _exit_app(self) -> None:
        self.app.running = False

    def _arrow_hit(self) -> None:
        self.arrow_hits += 1
        self.arrow_hits_label.text = f"Arrow hits: {self.arrow_hits}"

    def _on_showcase_canvas_overflow(self, dropped: int, queued: int) -> None:
        self.canvas_status_label.text = f"Canvas overflow: dropped {dropped}, queued {queued}"

    def _life_reset(self) -> None:
        self.life_cells.clear()
        self.life_cells.update({(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)})
        self.life_zoom_slider.value = 12.0
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

    def _mandel_col(self, k: int) -> Tuple[int, int, int]:
        if k >= self.max_iter - 1:
            return (0, 0, 0)
        return self.mandel_cols[k % len(self.mandel_cols)]

    def _mandel_pixel(self, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(self.max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return self.max_iter - 1

    def _clear_mandel(self) -> None:
        self.mandel_canvas.canvas.fill((0, 100, 100))
        self.mandel_status.text = "Mandelbrot: cleared"

    def _mandel_iterative_task(self, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [self._mandel_pixel(x, y, width, height, center, scale) for x in range(width)]
            self.app.scheduler.send_message(task_id, (y, row))
        return {"mode": "iterative"}

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
            self.app.scheduler.send_message(task_id, (x, y, w, h, values))
            return
        if tl == tr == bl == br:
            self.app.scheduler.send_message(task_id, (x, y, w, h, tl))
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
        self._recursive_fill(task_id, 0, 0, width, height, width, height, center, scale)
        return {"mode": "recursive"}

    def _launch_mandel(self, mode: str) -> None:
        if self.mandel_task_ids:
            return
        self._clear_mandel()
        width, height = self.mandel_canvas.canvas.get_size()
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        task_id = f"mandel-{mode}-{time.time_ns()}"
        self.mandel_task_ids.add(task_id)
        self.mandel_status.text = f"Mandelbrot: running {mode}"

        if mode == "iterative":
            def on_iter(payload):
                y, row = payload
                for x, value in enumerate(row):
                    self.mandel_canvas.canvas.set_at((x, y), self._mandel_col(value))

            self.app.scheduler.add_task(
                task_id,
                self._mandel_iterative_task,
                parameters={"size": (width, height), "center": center, "scale": scale},
                message_method=on_iter,
            )
            return

        def on_recur(payload):
            x, y, w, h, values = payload
            if isinstance(values, int):
                self.mandel_canvas.canvas.fill(self._mandel_col(values), Rect(x, y, w, h))
                return
            idx = 0
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.mandel_canvas.canvas.set_at((xx, yy), self._mandel_col(values[idx]))
                    idx += 1

        self.app.scheduler.add_task(
            task_id,
            self._mandel_recursive_task,
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=on_recur,
        )

    def _launch_mandel_iterative(self) -> None:
        self._launch_mandel("iterative")

    def _launch_mandel_recursive(self) -> None:
        self._launch_mandel("recursive")

    def _update_widget_showcase(self) -> None:
        self.slider_h_label.text = f"H: {self.slider_h.value:.2f}"
        self.slider_v_label.text = f"V: {self.slider_v.value:.2f}"
        self.scroll_h_label.text = f"SH: {self.scroll_h.offset}"
        self.scroll_v_label.text = f"SV: {self.scroll_v.offset}"

        while True:
            packet = self.showcase_canvas.read_event()
            if packet is None:
                break
            if packet.pos is None:
                continue
            if packet.event_type == pygame.MOUSEBUTTONDOWN and packet.button == 1:
                local_x = packet.pos[0] - self.showcase_canvas.rect.left
                local_y = packet.pos[1] - self.showcase_canvas.rect.top
                radius = randint(6, 18)
                col = (randint(100, 255), randint(100, 255), randint(100, 255))
                pygame.draw.circle(self.showcase_canvas.canvas, col, (local_x, local_y), radius)
                self.canvas_status_label.text = f"Canvas: drew at ({local_x}, {local_y})"
            elif packet.event_type == pygame.MOUSEBUTTONDOWN and packet.button == 3:
                self.showcase_canvas.canvas.fill((0, 72, 72))
                self.canvas_status_label.text = "Canvas: cleared"

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
            cell_size = max(2, int(round(self.life_zoom_slider.value)))
            cell_x = math.floor((local_x - self.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - self.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if cell in self.life_cells:
                self.life_cells.remove(cell)
            else:
                self.life_cells.add(cell)

        if self.life_toggle.pushed:
            self._life_step()

        cell_size = max(2, int(round(self.life_zoom_slider.value)))
        self.life_zoom_label.text = f"Zoom: {cell_size}"
        self.life_canvas.canvas.fill((0, 70, 70))
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.life_cells:
            px = int(self.life_origin[0] + (cx * cell_size))
            py = int(self.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= self.life_canvas.rect.width and -cell_size <= py <= self.life_canvas.rect.height:
                self.life_canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))

    def _update_mandel_events(self) -> None:
        finished = self.app.scheduler.get_finished_events()
        failed = self.app.scheduler.get_failed_events()

        for event in finished:
            if event.task_id in self.mandel_task_ids:
                self.mandel_task_ids.remove(event.task_id)
        for event in failed:
            if event.task_id in self.mandel_task_ids:
                self.mandel_task_ids.remove(event.task_id)
                self.mandel_status.text = f"Mandelbrot failed: {event.error}"

        self.app.scheduler.clear_events()
        if not self.mandel_task_ids and self.mandel_status.text.startswith("Mandelbrot: running"):
            self.mandel_status.text = "Mandelbrot: complete"

    def _update(self, dt_seconds: float) -> None:
        self.task_panel.set_visible(self.panel_toggle.pushed)
        GuiApplication.update(self.app, dt_seconds)

        self._update_widget_showcase()
        self._update_life()
        self._update_mandel_events()

    def run(self) -> None:
        UiEngine(self.app, target_fps=120).run()
        pygame.quit()


def main() -> None:
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
