from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.controls.chrome.window_control import WindowControl
from gui_do import (
    CanvasControl, ButtonControl, LabelControl, centered_horizontal_strip_layout, inset_rect
)
from pygame import Rect

class MandelbrotWindowPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.primary_canvas = None
        self.split_canvases = {}
        self.reset_button = None
        self.mandel_iter_button = None
        self.mandel_recur_button = None
        self.mandel_one_split_button = None
        self.mandel_four_split_button = None
        self.status_label = None


    def on_create(self):
        from gui_do import partition_rects
        content_rect = self.window.content_rect()
        padded_content_rect = inset_rect(content_rect, padding_x=8, padding_y=8)
        left = padded_content_rect.left
        top = padded_content_rect.top
        width = padded_content_rect.width
        height = padded_content_rect.height
        control_height = 30
        status_height = 20
        controls_and_status_height = control_height + status_height + 12
        bottom_visual_padding = 5
        grid_gap = 6
        canvas_area_bottom = padded_content_rect.bottom - bottom_visual_padding - controls_and_status_height
        canvas_area_width = padded_content_rect.width

        # Main canvas (single mode)
        [primary_canvas_rect] = partition_rects(
            padded_content_rect,
            rows=1,
            cols=1,
            gap=grid_gap,
            bottom_padding=bottom_visual_padding,
            controls_and_status_height=controls_and_status_height,
        )
        self.primary_canvas = CanvasControl("mandel_canvas", primary_canvas_rect, max_events=128)
        self.window.add(self.primary_canvas)
        self.feature.primary_canvas = self.primary_canvas

        # 2x2 grid canvases (hidden by default)
        canvas_rects = partition_rects(
            padded_content_rect,
            rows=2,
            cols=2,
            gap=6,
            bottom_padding=bottom_visual_padding,
            controls_and_status_height=controls_and_status_height,
        )
        self.split_canvases = {
            "can1": CanvasControl("can1", canvas_rects[0], max_events=32),
            "can2": CanvasControl("can2", canvas_rects[1], max_events=32),
            "can3": CanvasControl("can3", canvas_rects[2], max_events=32),
            "can4": CanvasControl("can4", canvas_rects[3], max_events=32),
        }
        for c in self.split_canvases.values():
            c.visible = False
            self.window.add(c)
        self.feature.split_canvases = self.split_canvases

        # Controls row at the bottom
        controls_y = canvas_area_bottom + 6
        row_strip_padding = 12
        slots = centered_horizontal_strip_layout(
            left=padded_content_rect.left + row_strip_padding,
            width=max(1, canvas_area_width - (row_strip_padding * 2)),
            y=controls_y,
            item_count=5,
            item_height=control_height,
            spacing=8,
        )
        mandel_reset_rect, mandel_iter_rect, mandel_recur_rect, mandel_one_split_rect, mandel_four_split_rect = slots

        self.reset_button = ButtonControl(
            "mandel_reset", mandel_reset_rect, "Reset", lambda: self.feature.clear(self.host), style="angle", font_role=self.feature.font_role("control")
        )
        self.window.add(self.reset_button)
        self.feature.reset_button = self.reset_button

        self.mandel_iter_button = ButtonControl(
            "mandel_iter", mandel_iter_rect, "Iterative", lambda: self.feature.launch_iterative(self.host), style="round", font_role=self.feature.font_role("control")
        )
        self.window.add(self.mandel_iter_button)
        self.mandel_recur_button = ButtonControl(
            "mandel_recur", mandel_recur_rect, "Recursive", lambda: self.feature.launch_recursive(self.host), style="round", font_role=self.feature.font_role("control")
        )
        self.window.add(self.mandel_recur_button)
        self.mandel_one_split_button = ButtonControl(
            "mandel_one_split", mandel_one_split_rect, "1M 4Tasks", lambda: self.feature.launch_one_split(self.host), style="round", font_role=self.feature.font_role("control")
        )
        self.window.add(self.mandel_one_split_button)
        self.mandel_four_split_button = ButtonControl(
            "mandel_four_split", mandel_four_split_rect, "4M 4Tasks", lambda: self.feature.launch_four_split(self.host), style="round", font_role=self.feature.font_role("control")
        )
        self.window.add(self.mandel_four_split_button)
        self.feature.task_buttons = (
            self.mandel_iter_button,
            self.mandel_recur_button,
            self.mandel_one_split_button,
            self.mandel_four_split_button,
        )

        # Status label below controls
        status_y = controls_y + control_height + 6
        self.status_label = LabelControl(
            "mandel_status", Rect(padded_content_rect.left, status_y, canvas_area_width, status_height), self.feature.status_text
        )
        self.window.add(self.status_label)
        self.feature.status_label = self.status_label

        # Restore feature state for correct initialization
        self.feature.demo = self.host
        self.feature.window = self.window
        self.feature.menu_bar = None
        self.feature.set_task_buttons_disabled(self.host, False)
        self.feature.clear(self.host)
        self.window.visible = False

    def handle_event(self, event):
        # Optionally handle window-level events
        return False

    def update(self, dt_seconds: float):
        # Optionally update window state
        pass
