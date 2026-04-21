import math
import time

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


def _set_title(label: LabelControl, size: int = 22) -> LabelControl:
    label.title = True
    label.text_size = size
    return label


def _set_text(label: LabelControl, size: int = 16) -> LabelControl:
    label.title = False
    label.text_size = size
    return label


def main() -> None:
    pygame.init()
    flags = pygame.FULLSCREEN | pygame.SCALED
    try:
        screen = pygame.display.set_mode((1920, 1080), flags=flags, vsync=1)
    except TypeError:
        screen = pygame.display.set_mode((1920, 1080), flags=flags)
    pygame.display.set_caption("gui_do demo")

    app = GuiApplication(screen)
    root = app.add(PanelControl("root", Rect(14, 14, 1892, 1052)))

    header = _set_title(root.add(LabelControl("header", Rect(34, 24, 900, 30), "gui_do: fullscreen rebased demo")), 24)
    _set_text(
        root.add(
            LabelControl(
                "sub_header",
                Rect(34, 56, 1200, 24),
                "life + mandelbrot windows restored, bottom task panel auto-hide, 1920x1080 fullscreen scaled",
            )
        ),
        16,
    )

    # Top task panel with auto-hide and scheduler actions.
    task_panel = app.add(
        TaskPanelControl(
            "task_panel",
            Rect(14, 1016, 1892, 50),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=8,
            dock_bottom=True,
        )
    )
    _set_text(task_panel.add(LabelControl("task_label", Rect(28, 1030, 130, 20), "Task panel")), 16)
    status_label = _set_text(task_panel.add(LabelControl("task_status", Rect(168, 1030, 460, 20), "Status: idle")), 16)

    # Optional watermark image from original asset set.
    root.add(ImageControl("realize", Rect(1760, 20, 128, 64), "data/images/realize.png", scale=True))

    panel_toggle = root.add(ToggleControl("panel_toggle", Rect(1320, 24, 170, 32), "Panel enabled", "Panel hidden", pushed=True))
    clock_toggle = root.add(ToggleControl("clock_toggle", Rect(1500, 24, 170, 32), "Clock on", "Clock off", pushed=True))
    clock_label = _set_text(root.add(LabelControl("clock", Rect(1680, 30, 180, 20), "Clock: 0")), 16)

    # Global control demo widgets scaled for 1080p.
    root.add(FrameControl("value_frame", Rect(34, 92, 1856, 116), border_width=2))
    slider_h = root.add(SliderControl("slider_h", Rect(52, 128, 520, 34), LayoutAxis.HORIZONTAL, 0.0, 100.0, 42.0))
    slider_h_label = _set_text(root.add(LabelControl("slider_h_label", Rect(584, 136, 220, 20), "H Slider: 42.00")), 16)
    scrollbar_h = root.add(
        ScrollbarControl(
            "scroll_h",
            Rect(860, 130, 620, 28),
            LayoutAxis.HORIZONTAL,
            content_size=3200,
            viewport_size=640,
            offset=320,
            step=64,
        )
    )
    scrollbar_h_label = _set_text(root.add(LabelControl("scroll_h_label", Rect(1496, 136, 220, 20), "H Scroll: 320")), 16)
    root.add(ButtonGroupControl("group_1", Rect(52, 168, 90, 30), "g_style", "One", selected=True))
    root.add(ButtonGroupControl("group_2", Rect(150, 168, 90, 30), "g_style", "Two", selected=False))
    root.add(ButtonGroupControl("group_3", Rect(248, 168, 90, 30), "g_style", "Three", selected=False))

    # Life window.
    life_window = root.add(WindowControl("life_window", Rect(34, 224, 914, 772), "Conway's Game of Life"))
    _set_text(life_window.add(LabelControl("life_help", Rect(56, 258, 450, 20), "Left click to toggle cells. Start to run generation loop.")), 16)
    life_canvas = life_window.add(CanvasControl("life_canvas", Rect(56, 286, 874, 630), max_events=256))
    life_toggle = life_window.add(ToggleControl("life_toggle", Rect(56, 926, 120, 30), "Stop", "Start", pushed=False))
    life_reset_button = life_window.add(ButtonControl("life_reset", Rect(186, 926, 110, 30), "Reset"))
    life_step_button = life_window.add(ButtonControl("life_step", Rect(306, 926, 110, 30), "Step"))
    life_zoom_slider = life_window.add(SliderControl("life_zoom", Rect(430, 924, 330, 32), LayoutAxis.HORIZONTAL, 2.0, 24.0, 12.0))
    life_zoom_label = _set_text(life_window.add(LabelControl("life_zoom_label", Rect(768, 930, 140, 20), "Zoom: 12")), 16)
    life_hide_button = life_window.add(ButtonControl("hide_life", Rect(810, 926, 120, 30), "Hide Window"))

    # Mandelbrot window.
    mandel_window = root.add(WindowControl("mandel_window", Rect(976, 224, 914, 772), "Mandelbrot"))
    _set_text(mandel_window.add(LabelControl("mandel_help", Rect(998, 258, 500, 20), "Iterative and recursive renders are scheduled in background tasks.")), 16)
    mandel_canvas = mandel_window.add(CanvasControl("mandel_canvas", Rect(998, 286, 874, 630), max_events=128))
    mandel_iter_button = mandel_window.add(ButtonControl("mandel_iter", Rect(998, 926, 120, 30), "Iterative"))
    mandel_recur_button = mandel_window.add(ButtonControl("mandel_recur", Rect(1128, 926, 120, 30), "Recursive"))
    mandel_reset_button = mandel_window.add(ButtonControl("mandel_reset", Rect(1258, 926, 120, 30), "Reset"))
    mandel_hide_button = mandel_window.add(ButtonControl("hide_mandel", Rect(1752, 926, 120, 30), "Hide Window"))
    mandel_status = _set_text(mandel_window.add(LabelControl("mandel_status", Rect(1390, 932, 350, 20), "Mandelbrot: idle")), 16)

    life_window.visible = False
    mandel_window.visible = False

    def show_life() -> None:
        life_window.visible = True
        status_label.text = "Status: life window visible"

    def show_mandel() -> None:
        mandel_window.visible = True
        status_label.text = "Status: mandelbrot window visible"

    def run_worker() -> None:
        status_label.text = "Status: async worker started"

        def worker_logic(task_id, params):
            total = int(params.get("total", 20))
            for step in range(1, total + 1):
                time.sleep(0.05)
                app.scheduler.send_message(task_id, {"step": step, "total": total})
            return {"ok": True}

        task_id = f"worker-{time.time_ns()}"

        def on_worker(payload: dict) -> None:
            status_label.text = f"Status: worker {payload['step']}/{payload['total']}"

        app.scheduler.add_task(task_id, worker_logic, parameters={"total": 16}, message_method=on_worker)

    task_panel.add(ButtonControl("show_life", Rect(646, 1025, 120, 30), "Show Life", show_life))
    task_panel.add(ButtonControl("show_mandel", Rect(776, 1025, 150, 30), "Show Mandelbrot", show_mandel))
    task_panel.add(ButtonControl("run_worker", Rect(936, 1025, 120, 30), "Run Worker", run_worker))

    def close_app() -> None:
        app.running = False

    task_panel.add(ButtonControl("exit", Rect(1768, 1025, 120, 30), "Exit", close_app))

    # Life state.
    life_cells = {(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)}
    life_origin = [life_canvas.rect.centerx, life_canvas.rect.centery]

    def life_reset() -> None:
        life_cells.clear()
        life_cells.update({(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)})
        life_zoom_slider.value = 12.0
        life_toggle.pushed = False

    def life_step() -> None:
        neighbours = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

        def population(cell):
            count = 0
            for dx, dy in neighbours:
                if (cell[0] + dx, cell[1] + dy) in life_cells:
                    count += 1
            return count

        new_life = set()
        for cell in life_cells:
            pop = population(cell)
            if pop in (2, 3):
                new_life.add(cell)
            for dx, dy in neighbours:
                n_cell = (cell[0] + dx, cell[1] + dy)
                if population(n_cell) == 3:
                    new_life.add(n_cell)
        life_cells.clear()
        life_cells.update(new_life)

    life_reset_button.on_click = life_reset
    life_step_button.on_click = life_step
    life_hide_button.on_click = lambda: setattr(life_window, "visible", False)

    # Mandelbrot state.
    mandel_task_ids = set()
    max_iter = 96

    def mandel_col(k: int):
        cols = (
            (66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
            (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
            (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
            (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
        )
        if k >= max_iter - 1:
            return (0, 0, 0)
        return cols[k % len(cols)]

    def mandel_pixel(px: int, py: int, width: int, height: int, center: complex, scale: float):
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return max_iter - 1

    def clear_mandel() -> None:
        mandel_canvas.canvas.fill((0, 100, 100))
        mandel_status.text = "Mandelbrot: cleared"

    def mandel_iterative_task(task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [mandel_pixel(x, y, width, height, center, scale) for x in range(width)]
            app.scheduler.send_message(task_id, (y, row))
        return {"mode": "iterative"}

    def recursive_fill(task_id, x, y, w, h, width, height, center, scale):
        if w <= 0 or h <= 0:
            return
        tl = mandel_pixel(x, y, width, height, center, scale)
        tr = mandel_pixel(x + w - 1, y, width, height, center, scale)
        bl = mandel_pixel(x, y + h - 1, width, height, center, scale)
        br = mandel_pixel(x + w - 1, y + h - 1, width, height, center, scale)
        if w <= 4 or h <= 4:
            values = []
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    values.append(mandel_pixel(xx, yy, width, height, center, scale))
            app.scheduler.send_message(task_id, (x, y, w, h, values))
            return
        if tl == tr == bl == br:
            app.scheduler.send_message(task_id, (x, y, w, h, tl))
            return
        hw = w // 2
        hh = h // 2
        recursive_fill(task_id, x, y, hw, hh, width, height, center, scale)
        recursive_fill(task_id, x + hw, y, w - hw, hh, width, height, center, scale)
        recursive_fill(task_id, x, y + hh, hw, h - hh, width, height, center, scale)
        recursive_fill(task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

    def mandel_recursive_task(task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        recursive_fill(task_id, 0, 0, width, height, width, height, center, scale)
        return {"mode": "recursive"}

    def launch_mandel(mode: str) -> None:
        if mandel_task_ids:
            return
        clear_mandel()
        width, height = mandel_canvas.canvas.get_size()
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        task_id = f"mandel-{mode}-{time.time_ns()}"
        mandel_task_ids.add(task_id)
        mandel_status.text = f"Mandelbrot: running {mode}"

        if mode == "iterative":
            def on_iter(payload):
                y, row = payload
                for x, value in enumerate(row):
                    mandel_canvas.canvas.set_at((x, y), mandel_col(value))

            app.scheduler.add_task(
                task_id,
                mandel_iterative_task,
                parameters={"size": (width, height), "center": center, "scale": scale},
                message_method=on_iter,
            )
            return

        def on_recur(payload):
            x, y, w, h, values = payload
            if isinstance(values, int):
                mandel_canvas.canvas.fill(mandel_col(values), Rect(x, y, w, h))
                return
            idx = 0
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    mandel_canvas.canvas.set_at((xx, yy), mandel_col(values[idx]))
                    idx += 1

        app.scheduler.add_task(
            task_id,
            mandel_recursive_task,
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=on_recur,
        )

    mandel_iter_button.on_click = lambda: launch_mandel("iterative")
    mandel_recur_button.on_click = lambda: launch_mandel("recursive")
    mandel_reset_button.on_click = clear_mandel
    mandel_hide_button.on_click = lambda: setattr(mandel_window, "visible", False)

    ticks = {"count": 0}

    def on_tick() -> None:
        if clock_toggle.pushed:
            ticks["count"] += 1
            clock_label.text = f"Clock: {ticks['count']}"

    app.timers.add_timer("demo.tick", 1.0, on_tick)

    base_update = app.update

    def update_demo(dt_seconds: float) -> None:
        task_panel.set_visible(panel_toggle.pushed)
        base_update(dt_seconds)
        slider_h_label.text = f"H Slider: {slider_h.value:.2f}"
        scrollbar_h_label.text = f"H Scroll: {scrollbar_h.offset}"

        # Handle life canvas events.
        while True:
            packet = life_canvas.read_event()
            if packet is None:
                break
            if packet.pos is None or packet.button != 1:
                continue
            if packet.event_type != pygame.MOUSEBUTTONDOWN:
                continue
            local_x = packet.pos[0] - life_canvas.rect.left
            local_y = packet.pos[1] - life_canvas.rect.top
            cell_size = max(2, int(round(life_zoom_slider.value)))
            cell_x = math.floor((local_x - life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if cell in life_cells:
                life_cells.remove(cell)
            else:
                life_cells.add(cell)

        if life_toggle.pushed:
            life_step()

        cell_size = max(2, int(round(life_zoom_slider.value)))
        life_zoom_label.text = f"Zoom: {cell_size}"
        life_canvas.canvas.fill((0, 70, 70))
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in life_cells:
            px = int(life_origin[0] + (cx * cell_size))
            py = int(life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= life_canvas.rect.width and -cell_size <= py <= life_canvas.rect.height:
                life_canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))

        # Handle mandelbrot task completion signals.
        for event in app.scheduler.get_finished_events():
            if event.task_id in mandel_task_ids:
                mandel_task_ids.remove(event.task_id)
        for event in app.scheduler.get_failed_events():
            if event.task_id in mandel_task_ids:
                mandel_task_ids.remove(event.task_id)
                mandel_status.text = f"Mandelbrot failed: {event.error}"
        app.scheduler.clear_events()
        if not mandel_task_ids and mandel_status.text.startswith("Mandelbrot: running"):
            mandel_status.text = "Mandelbrot: complete"

    app.update = update_demo

    header.title = True

    UiEngine(app, target_fps=120).run()
    pygame.quit()


if __name__ == "__main__":
    main()
