import math
import time
from random import randint
from typing import Set, Tuple

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
    LayoutManager,
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
        self.app.layout.set_anchor_bounds(self.screen_rect)
        self.app.create_scene("main")
        self.app.switch_scene("main")
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False)
        self.app.set_window_tiling_enabled(True, relayout=False)
        self.scene_scheduler = self.app.get_scene_scheduler("main")
        self.life_scheduler = self.scene_scheduler
        self.mandel_scheduler = self.scene_scheduler

        self.ticks = 0
        self.arrow_hits = 0
        self._last_brand_ms = pygame.time.get_ticks()
        self.life_cells: Set[Tuple[int, int]] = set()
        self.life_origin = [0, 0]
        self.life_cell_size = 12
        self.life_dragging = False
        self._life_zoom_slider_last_value = 5
        self.mandel_task_ids: Set[str] = set()
        self.mandel_task_id_pool = ("iter", "recu", "1", "2", "3", "4", "can1", "can2", "can3", "can4")
        self.max_iter = 96
        self.circles = []
        self._last_panel_visible = True
        self._frame_dt_seconds = 0.0

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
        self.quit_button = self.task_panel.add(
            ButtonControl(
                "quit",
                Rect(16, self.screen_rect.height - 40, 120, 30),
                "Quit",
                self._exit_app,
                style="angle",
            )
        )
        self.life_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_life",
                Rect(146, self.screen_rect.height - 40, 140, 30),
                "Life On",
                "Life Off",
                pushed=True,
                on_toggle=self._toggle_life_window,
            )
        )
        self.mandel_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_mandel",
                Rect(296, self.screen_rect.height - 40, 170, 30),
                "Mandelbrot On",
                "Mandelbrot Off",
                pushed=True,
                on_toggle=self._toggle_mandel_window,
            )
        )
        self._tile_visible_windows()

    def _set_title(self, label: LabelControl, size: int = 22) -> LabelControl:
        label.title = True
        label.text_size = size
        return label

    def _set_text(self, label: LabelControl, size: int = 16) -> LabelControl:
        label.title = False
        label.text_size = size
        return label

    def _build_shell(self) -> None:
        self.bg_canvas = self.root.add(CanvasControl("bg_canvas", Rect(0, 0, self.screen_rect.width, self.screen_rect.height), max_events=1))
        self.bg_canvas.enabled = False
        self.bg_canvas.canvas.fill((0, 0, 0, 0))

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
        self.gui_do_label = self._set_title(
            self.root.add(LabelControl("gui_do_label", Rect(48, 76, 280, 56), "gui_do")),
            54,
        )
        self.gui_do_pos_x = float(self.gui_do_label.rect.x)
        self.gui_do_pos_y = float(self.gui_do_label.rect.y)
        self.gui_do_speed = 250.0
        self.gui_do_angle = math.radians(35.0)

        for _ in range(64):
            size = randint(6, 12)
            self.circles.append(
                {
                    "x": float(randint(size, self.screen_rect.width - (size * 2))),
                    "y": float(randint(size, self.screen_rect.height - (size * 2))),
                    "dx": float(randint(-80, 80) or 40),
                    "dy": float(randint(-80, 80) or -50),
                    "size": size,
                    "col": (0, 200, 200) if randint(0, 1) == 0 else (0, 150, 150),
                }
            )

        self.root.add(ImageControl("realize", Rect(self.screen_rect.width - 156, 14, 140, 72), "data/images/realize.png", scale=True))

        self.app.layout.set_grid_properties(anchor=(self.screen_rect.width - 760, 18), width=180, height=32, spacing=10)
        self.circles_toggle = self.root.add(ToggleControl("circles_toggle", self.app.layout.gridded(0, 0), "Circles On", "Circles Off", pushed=True))
        self.panel_toggle = self.root.add(ToggleControl("panel_toggle", self.app.layout.gridded(1, 0), "Panel On", "Panel Off", pushed=True))
        self.clock_toggle = self.root.add(ToggleControl("clock_toggle", self.app.layout.gridded(2, 0), "Clock On", "Clock Off", pushed=True))
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

        self.app.layout.set_linear_properties(
            anchor=(590, self.screen_rect.height - 40),
            item_width=120,
            item_height=30,
            spacing=10,
            horizontal=True,
        )
        self.showcase_toggle = self.task_panel.add(
            ToggleControl("show_showcase", self.app.layout.linear(0), "Showcase On", "Showcase Off", pushed=True, on_toggle=self._toggle_showcase)
        )
        self.life_toggle_window = self.task_panel.add(
            ToggleControl("show_life", self.app.layout.linear(1), "Life On", "Life Off", pushed=False, on_toggle=self._toggle_life_window)
        )
        self.mandel_toggle_window = self.task_panel.add(
            ToggleControl("show_mandel", self.app.layout.linear(2), "Mandel On", "Mandel Off", pushed=False, on_toggle=self._toggle_mandel_window)
        )
        self.tile_toggle = self.task_panel.add(
            ToggleControl(
                "tile_windows",
                self.app.layout.linear(3),
                "Tile On",
                "Tile Off",
                pushed=True,
                on_toggle=self._on_tile_toggle,
            )
        )
        self.task_panel.add(ButtonControl("tile_now", self.app.layout.linear(4), "Tile Now", self._tile_visible_windows))
        self.task_panel.add(ButtonControl("run_worker", self.app.layout.linear(5), "Run Worker", self._run_worker))
        self.task_panel.add(ButtonControl("exit", Rect(self.screen_rect.width - 132, self.screen_rect.height - 40, 120, 30), "Exit", self._exit_app))

    def _build_widget_showcase_window(self) -> None:
        showcase_rect = self.app.layout.anchored((910, 940), anchor="top_left", margin=(28, 92), use_rect=True)
        self.showcase_window = self.root.add(WindowControl("showcase_window", showcase_rect, "Widget Showcase"))
        left = showcase_rect.left
        top = showcase_rect.top
        showcase_layout = LayoutManager()

        def abs_rect(offset_x: int, offset_y: int, width: int, height: int) -> Rect:
            return Rect(left + offset_x, top + offset_y, width, height)

        self._set_text(
            self.showcase_window.add(
                LabelControl(
                    "show_help",
                    abs_rect(18, 32, 820, 20),
                    "Legacy-equivalent widgets: buttons, toggles, groups, sliders, scrollbars, arrows, canvas, image",
                )
            )
        )

        self.showcase_window.add(FrameControl("style_frame", abs_rect(18, 60, 820, 214), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("style_title", abs_rect(30, 68, 420, 22), "Styles (box/round/angle/radio/check)")), 18)

        styles = ("box", "round", "angle", "radio", "check")
        showcase_layout.set_linear_properties(anchor=(left + 30, top + 104), item_width=140, item_height=30, spacing=14, horizontal=True)
        for idx, style in enumerate(styles):
            self.showcase_window.add(ButtonControl(f"btn_{style}", showcase_layout.linear_item(idx), f"{style.title()} Btn", style=style))

        showcase_layout.set_linear_properties(anchor=(left + 30, top + 142), item_width=140, item_height=30, spacing=14, horizontal=True)
        for idx, style in enumerate(styles):
            self.showcase_window.add(
                ToggleControl(
                    f"tog_{style}",
                    showcase_layout.linear_item(idx),
                    f"{style.title()} On",
                    f"{style.title()} Off",
                    pushed=False,
                    style=style,
                )
            )

        group_labels = ("Group A", "Group B", "Group C", "Group D", "Group E")
        showcase_layout.set_linear_properties(anchor=(left + 30, top + 182), item_width=140, item_height=30, spacing=14, horizontal=True)
        for idx, style in enumerate(styles):
            self.showcase_window.add(
                ButtonGroupControl(
                    f"bg_{chr(ord('a') + idx)}",
                    showcase_layout.linear_item(idx),
                    "legacy_group",
                    group_labels[idx],
                    selected=(idx == 0),
                    style=style,
                )
            )

        self.showcase_window.add(FrameControl("axis_frame", abs_rect(18, 286, 820, 214), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("axis_title", abs_rect(30, 294, 400, 22), "Sliders and Scrollbars")), 18)

        self.slider_h = self.showcase_window.add(
            SliderControl("slider_h", abs_rect(30, 336, 420, 30), LayoutAxis.HORIZONTAL, 0.0, 100.0, 42.0)
        )
        self.slider_h_label = self._set_text(self.showcase_window.add(LabelControl("slider_h_label", abs_rect(460, 342, 150, 20), "H: 42.00")))

        self.slider_v = self.showcase_window.add(
            SliderControl("slider_v", abs_rect(612, 334, 30, 140), LayoutAxis.VERTICAL, 0.0, 10.0, 5.0)
        )
        self.slider_v_label = self._set_text(self.showcase_window.add(LabelControl("slider_v_label", abs_rect(648, 392, 170, 20), "V: 5.00")))

        self.scroll_h = self.showcase_window.add(
            ScrollbarControl(
                "scroll_h",
                abs_rect(30, 378, 420, 24),
                LayoutAxis.HORIZONTAL,
                content_size=3000,
                viewport_size=640,
                offset=320,
                step=64,
            )
        )
        self.scroll_h_label = self._set_text(self.showcase_window.add(LabelControl("scroll_h_label", abs_rect(460, 380, 170, 20), "SH: 320")))

        self.scroll_v = self.showcase_window.add(
            ScrollbarControl(
                "scroll_v",
                abs_rect(682, 334, 24, 140),
                LayoutAxis.VERTICAL,
                content_size=2200,
                viewport_size=480,
                offset=220,
                step=48,
            )
        )
        self.scroll_v_label = self._set_text(self.showcase_window.add(LabelControl("scroll_v_label", abs_rect(712, 392, 120, 20), "SV: 220")))

        self.showcase_window.add(FrameControl("arrow_canvas_frame", abs_rect(18, 512, 820, 268), border_width=2))
        self._set_title(self.showcase_window.add(LabelControl("arrow_title", abs_rect(30, 520, 300, 22), "Arrow Boxes and Canvas")), 18)

        self.arrow_hits_label = self._set_text(self.showcase_window.add(LabelControl("arrow_hits", abs_rect(30, 554, 180, 20), "Arrow hits: 0")))
        showcase_layout.set_linear_properties(anchor=(left + 30, top + 584), item_width=36, item_height=36, spacing=8, horizontal=True)
        self.showcase_window.add(ArrowBoxControl("arrow_left", showcase_layout.linear_item(0), 180, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_right", showcase_layout.linear_item(1), 0, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_up", showcase_layout.linear_item(2), 270, on_activate=self._arrow_hit))
        self.showcase_window.add(ArrowBoxControl("arrow_down", showcase_layout.linear_item(3), 90, on_activate=self._arrow_hit))

        self.canvas_status_label = self._set_text(
            self.showcase_window.add(LabelControl("canvas_status", abs_rect(228, 554, 590, 20), "Canvas: left click draws, right click clears"))
        )
        self.showcase_canvas = self.showcase_window.add(CanvasControl("showcase_canvas", abs_rect(228, 584, 594, 184), max_events=128))
        self.showcase_canvas.canvas.fill((0, 72, 72))
        self.showcase_canvas.set_overflow_mode("drop_oldest")
        self.showcase_canvas.set_overflow_handler(self._on_showcase_canvas_overflow)

        self.showcase_window.add(ImageControl("icon_img", abs_rect(30, 632, 150, 124), "data/images/realize.png", scale=True))

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

    def _on_clock_tick(self) -> None:
        return None

    def _update_brand_and_circles(self, dt_seconds: float) -> None:
        self.bg_canvas.visible = self.circles_toggle.pushed
        if self.circles_toggle.pushed:
            self.bg_canvas.canvas.fill((0, 0, 0, 0))
            for item in self.circles:
                item["x"] += item["dx"] * dt_seconds
                item["y"] += item["dy"] * dt_seconds
                size = item["size"]
                if item["x"] <= size or item["x"] >= self.screen_rect.width - (size + 1):
                    item["dx"] *= -1.0
                if item["y"] <= size or item["y"] >= self.screen_rect.height - (size + 1):
                    item["dy"] *= -1.0
                pygame.draw.circle(self.bg_canvas.canvas, item["col"], (int(item["x"]), int(item["y"])), size)

        now_ms = pygame.time.get_ticks()
        elapsed_ms = max(1, now_ms - self._last_brand_ms)
        self._last_brand_ms = now_ms
        delta = elapsed_ms / 1000.0

        dx = math.cos(self.gui_do_angle) * self.gui_do_speed * delta
        dy = math.sin(self.gui_do_angle) * self.gui_do_speed * delta
        self.gui_do_pos_x += dx
        self.gui_do_pos_y += dy

        label_rect = self.gui_do_label.rect
        max_x = self.screen_rect.width - label_rect.width - 16
        min_x = 16
        max_y = self.screen_rect.height - label_rect.height - 80
        min_y = 76

        if self.gui_do_pos_x <= min_x or self.gui_do_pos_x >= max_x:
            self.gui_do_angle = math.pi - self.gui_do_angle
            self.gui_do_pos_x = max(min_x, min(max_x, self.gui_do_pos_x))
        if self.gui_do_pos_y <= min_y or self.gui_do_pos_y >= max_y:
            self.gui_do_angle = -self.gui_do_angle
            self.gui_do_pos_y = max(min_y, min(max_y, self.gui_do_pos_y))

        self.gui_do_label.rect.topleft = (int(self.gui_do_pos_x), int(self.gui_do_pos_y))

    def _toggle_showcase(self, pushed: bool) -> None:
        self.showcase_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.showcase_window])
            self.status_label.text = "Status: showcase visible"
        else:
            self.status_label.text = "Status: showcase hidden"

    def _toggle_life_window(self, pushed: bool) -> None:
        self.life_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.life_window])
        else:
            self._tile_visible_windows()

    def _on_tile_toggle(self, pushed: bool) -> None:
        self.app.set_window_tiling_enabled(bool(pushed), relayout=True)
        if pushed:
            self._tile_visible_windows()

    def _toggle_mandel_window(self, pushed: bool) -> None:
        self.mandel_window.visible = bool(pushed)
        if pushed:
            self._tile_visible_windows(newly_visible=[self.mandel_window])
        else:
            self._tile_visible_windows()

    def _visible_windows_for_tiling(self):
        windows = []
        for name in ("showcase_window", "life_window", "mandel_window"):
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

    def _run_worker(self) -> None:
        self.status_label.text = "Status: async worker started"

        def worker_logic(task_id, params):
            total = int(params.get("total", 18))
            for step in range(1, total + 1):
                time.sleep(0.05)
                self.life_scheduler.send_message(task_id, {"step": step, "total": total})
            return {"ok": True}

        task_id = f"worker-{time.time_ns()}"

        def on_worker(payload: dict) -> None:
            self.status_label.text = f"Status: worker {payload['step']}/{payload['total']}"

        self.life_scheduler.add_task(task_id, worker_logic, parameters={"total": 18}, message_method=on_worker)

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
        event_type = getattr(event, "type", None)
        button = getattr(event, "button", None)
        pos = getattr(event, "pos", None)

        if event_type == pygame.MOUSEBUTTONDOWN and button == 3:
            if isinstance(pos, tuple) and len(pos) == 2 and self.life_canvas.rect.collidepoint(pos):
                self.life_dragging = True
                self.app.set_cursor("hand")
                self.app.set_lock_point(self.life_canvas, pos)
                return True

        if event_type == pygame.MOUSEBUTTONUP and button == 3:
            if self.life_dragging:
                self.life_dragging = False
                self.app.set_cursor("normal")
                self.app.set_lock_point(None)
                return True

        if event_type == pygame.MOUSEMOTION and self.life_dragging:
            delta = self.app.get_lock_point_motion_delta(event)
            if delta is None:
                rel = getattr(event, "rel", None)
                if isinstance(rel, tuple) and len(rel) == 2:
                    delta = (rel[0], rel[1])
                else:
                    delta = (0, 0)
            self.life_origin[0] -= delta[0]
            self.life_origin[1] -= delta[1]
            return True

        if event_type == pygame.MOUSEBUTTONDOWN and button in (4, 5):
            if isinstance(pos, tuple) and len(pos) == 2 and self.life_canvas.rect.collidepoint(pos):
                wheel_step = 1 if button == 4 else -1
                anchor_local = (pos[0] - self.life_canvas.rect.left, pos[1] - self.life_canvas.rect.top)
                self._zoom_life_view_about(anchor_local, self.life_cell_size + (wheel_step * 2))
                return True

        if event_type == pygame.MOUSEWHEEL:
            pointer_pos = self.app.lock_point_pos if self.app.mouse_point_locked and self.app.lock_point_pos is not None else pygame.mouse.get_pos()
            if self.life_canvas.rect.collidepoint(pointer_pos):
                if self.app.mouse_point_locked and self.app.lock_point_pos is not None:
                    lock_window_pos = self.app.convert_to_window(self.app.lock_point_pos, self.life_window)
                    canvas_window_left = self.life_canvas.rect.left - self.life_window.rect.left
                    canvas_window_top = self.life_canvas.rect.top - self.life_window.rect.top
                    anchor_local = (lock_window_pos[0] - canvas_window_left, lock_window_pos[1] - canvas_window_top)
                else:
                    anchor_local = (pointer_pos[0] - self.life_canvas.rect.left, pointer_pos[1] - self.life_canvas.rect.top)
                self._zoom_life_view_about(anchor_local, self.life_cell_size + (getattr(event, "y", 0) * 2))
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
        self._frame_dt_seconds = dt_seconds
        GuiApplication.update(self.app, dt_seconds)

    def _screen_preamble(self) -> None:
        return None

    def _screen_event_handler(self, event) -> bool:
        if getattr(event, "type", None) == pygame.KEYDOWN and getattr(event, "key", None) == pygame.K_ESCAPE:
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
