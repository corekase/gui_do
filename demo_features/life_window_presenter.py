from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.controls.chrome.window_control import WindowControl
from gui_do import (
    CanvasControl, ButtonControl, ToggleControl, SliderControl, LayoutAxis, centered_horizontal_strip_layout, inset_rect, partition_rects
)
from pygame import Rect

class LifeWindowPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        # These will be set in on_create and also assigned to feature for correct wiring
        self.canvas = None
        self.reset_button = None
        self.toggle = None
        self.zoom_slider = None


    def on_create(self):
        content_rect = self.window.content_rect()
        padded_content_rect = inset_rect(content_rect, padding_x=10, padding_y=10)
        left = padded_content_rect.left
        top = padded_content_rect.top
        width = padded_content_rect.width
        height = padded_content_rect.height
        control_height = 28
        controls_gap = 10
        control_spacing = 12
        grid_gap = 6
        controls_y = top + height - control_height - 10
        padded_rect = Rect(left, top, width, max(1, controls_y - controls_gap - top))
        [canvas_rect] = partition_rects(
            padded_rect,
            rows=1,
            cols=1,
            gap=grid_gap,
            bottom_padding=0,
            controls_and_status_height=0,
        )
        self.canvas = CanvasControl("life_canvas", canvas_rect, max_events=256)
        self.window.add(self.canvas)
        self.feature.canvas = self.canvas

        # Controls row at the bottom
        slots = centered_horizontal_strip_layout(
            left=left,
            width=width,
            y=controls_y,
            item_count=4,
            item_height=control_height,
            spacing=control_spacing,
        )
        life_reset_rect, life_toggle_rect, zoom_slider_slot_1, zoom_slider_slot_2 = slots

        self.reset_button = ButtonControl(
            "life_reset", life_reset_rect, "Reset", self.feature.life_reset, style="angle", font_role=self.feature.font_role("control")
        )
        self.window.add(self.reset_button)
        self.feature.reset_button = self.reset_button

        self.toggle = ToggleControl(
            "life_toggle",
            life_toggle_rect,
            "Stop",
            "Start",
            pushed=False,
            style="round",
            font_role=self.feature.font_role("control"),
        )
        self.window.add(self.toggle)
        self.feature.toggle = self.toggle

        from gui_do import split_slot_bounds
        slider_left, slider_right = split_slot_bounds([zoom_slider_slot_1, zoom_slider_slot_2])
        slider_height = 20
        slider_y = controls_y + max(0, (control_height - slider_height) // 2)
        self.zoom_slider = SliderControl(
            "life_zoom",
            Rect(slider_left, slider_y, max(80, slider_right - slider_left), slider_height),
            LayoutAxis.HORIZONTAL,
            0.0,
            11.0,
            5.0,
            on_change=self.feature.on_life_zoom_slider_changed,
        )
        self.window.add(self.zoom_slider)
        self.feature.zoom_slider = self.zoom_slider

        # Restore feature state for correct initialization
        self.feature.demo = self.host
        self.feature.window = self.window
        self.feature.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
        self.feature.life_cell_size = 12
        self.feature.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
        self.feature.life_dragging = False
        # Request initial cell state from logic (so cells appear at start)
        self.feature._send_life_logic_command("snapshot")
        self.window.visible = False

        # Attach event handler and post-render hooks for canvas interaction and drawing
        self.window._event_handler = self.life_window_event_handler
        self.window._preamble = self.life_window_preamble
        self.window._postamble = self.life_window_postamble

    def life_window_event_handler(self, event):
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
                if isinstance(rel, tuple) and len(rel) == 2:
                    delta = (rel[0], rel[1])
                else:
                    delta = (0, 0)
            self.feature.life_origin[0] -= delta[0]
            self.feature.life_origin[1] -= delta[1]
            return True

        if event.is_mouse_wheel():
            pointer_pos = demo.app.lock_point_pos if getattr(demo.app, "mouse_point_locked", False) and getattr(demo.app, "lock_point_pos", None) is not None else event.pos
            if pointer_pos is not None and canvas.rect.collidepoint(pointer_pos):
                if getattr(demo.app, "mouse_point_locked", False) and getattr(demo.app, "lock_point_pos", None) is not None:
                    lock_window_pos = demo.app.convert_to_window(demo.app.lock_point_pos, window)
                    canvas_window_left = canvas.rect.left - window.rect.left
                    canvas_window_top = canvas.rect.top - window.rect.top
                    anchor_local = (lock_window_pos[0] - canvas_window_left, lock_window_pos[1] - canvas_window_top)
                else:
                    anchor_local = (pointer_pos[0] - canvas.rect.left, pointer_pos[1] - canvas.rect.top)
                self.feature.zoom_life_view_about(anchor_local, self.feature.life_cell_size - (event.wheel_delta * 2))
                return True

        return False

    def life_window_preamble(self):
        slider_value = max(0, min(11, int(round(self.zoom_slider.value))))
        self.feature.sync_life_zoom_from_slider(slider_value)

    def life_window_postamble(self):
        self.update_life()

    def update_life(self):
        import math
        demo = self.host
        canvas = self.canvas
        toggle = self.toggle
        while True:
            packet = canvas.read_event()
            if packet is None:
                break
            if not packet.is_mouse_down(1):
                continue
            if packet.local_pos is not None:
                local_x, local_y = packet.local_pos
            elif packet.pos is not None:
                local_x = packet.pos[0] - canvas.rect.left
                local_y = packet.pos[1] - canvas.rect.top
            else:
                continue
            cell_size = max(2, int(round(self.feature.life_cell_size)))
            cell_x = math.floor((local_x - self.feature.life_origin[0]) / cell_size)
            cell_y = math.floor((local_y - self.feature.life_origin[1]) / cell_size)
            cell = (cell_x, cell_y)
            if not self.feature._send_life_logic_command("toggle_cell", cell=cell):
                if cell in self.feature.life_cells:
                    self.feature.life_cells.remove(cell)
                else:
                    self.feature.life_cells.add(cell)

        if toggle.pushed:
            if not self.feature._send_life_logic_command("next"):
                from demo_features.life_demo_feature import LifeSimulationLogicFeature
                self.feature.life_cells = LifeSimulationLogicFeature.next_life_cycle(self.feature.life_cells)

        cell_size = max(2, int(round(self.feature.life_cell_size)))
        canvas.canvas.fill(demo.app.theme.medium)
        trim = 0 if cell_size <= 2 else 1
        for cx, cy in self.feature.life_cells:
            px = int(self.feature.life_origin[0] + (cx * cell_size))
            py = int(self.feature.life_origin[1] + (cy * cell_size))
            if -cell_size <= px <= canvas.rect.width and -cell_size <= py <= canvas.rect.height:
                canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))

    def handle_event(self, event):
        # Optionally handle window-level events
        return False

    def update(self, dt_seconds: float):
        # Optionally update window state
        pass
