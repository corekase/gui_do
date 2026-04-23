"""Mandelbrot feature part extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import pygame
from dataclasses import dataclass
from typing import Optional, Tuple

from pygame import Rect
from shared.part_lifecycle import Part


MANDEL_STATUS_TOPIC = "demo.mandel.status"
MANDEL_STATUS_SCOPE = "main"

MANDEL_KIND_IDLE = "idle"
MANDEL_KIND_CLEARED = "cleared"
MANDEL_KIND_RUNNING_ITERATIVE = "running_iterative"
MANDEL_KIND_RUNNING_RECURSIVE = "running_recursive"
MANDEL_KIND_RUNNING_ONE_SPLIT = "running_one_split"
MANDEL_KIND_RUNNING_FOUR_SPLIT = "running_four_split"
MANDEL_KIND_FAILED = "failed"
MANDEL_KIND_COMPLETE = "complete"
MANDEL_KIND_STATUS = "status"


@dataclass(frozen=True)
class MandelStatusEvent:
    """Typed status payload used for Mandelbrot status bus publication."""

    kind: str
    detail: Optional[str] = None

    def to_payload(self) -> dict[str, str]:
        """Serialize event fields into a transport-safe dictionary payload."""
        payload = {"kind": str(self.kind)}
        if self.detail is not None:
            payload["detail"] = str(self.detail)
        return payload

    @classmethod
    def from_payload(cls, payload) -> "MandelStatusEvent":
        """Build a status event from event instance, dict payload, or raw value."""
        if isinstance(payload, MandelStatusEvent):
            return payload
        if isinstance(payload, dict):
            kind = str(payload.get("kind", MANDEL_KIND_STATUS))
            detail = payload.get("detail")
            if detail is not None:
                detail = str(detail)
            return cls(kind=kind, detail=detail)
        return cls(kind=MANDEL_KIND_STATUS, detail=str(payload))


__all__ = [
    "MANDEL_STATUS_TOPIC",
    "MANDEL_STATUS_SCOPE",
    "MANDEL_KIND_IDLE",
    "MANDEL_KIND_CLEARED",
    "MANDEL_KIND_RUNNING_ITERATIVE",
    "MANDEL_KIND_RUNNING_RECURSIVE",
    "MANDEL_KIND_RUNNING_ONE_SPLIT",
    "MANDEL_KIND_RUNNING_FOUR_SPLIT",
    "MANDEL_KIND_FAILED",
    "MANDEL_KIND_COMPLETE",
    "MANDEL_KIND_STATUS",
    "MandelStatusEvent",
]


class MandelbrotRenderFeature(Part):
    """Build and run the Mandelbrot demo windows, tasks, and status plumbing."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    FAILURE_PREVIEW_MIN = 1
    FAILURE_PREVIEW_MAX = 20

    def __init__(self) -> None:
        super().__init__("mandelbrot", scene_name="main")
        self.mandel_cols = (
            (66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
            (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
            (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
            (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
        )
        self.max_iter = 96
        self.task_ids = set()
        self.task_id_pool = ("iter", "recu", "1", "2", "3", "4", "can1", "can2", "can3", "can4")
        self.running_mode = None
        self.failure_preview_limit = 3
        self.scheduler = None
        self.demo = None  # Will be set during build_window
        self.window = None
        self.help_label = None
        self.status_label = None
        self.primary_canvas = None
        self.split_canvases = {}
        self.reset_button = None
        self.task_buttons = ()
        self.status_text = "Mandelbrot: idle"
        self.status_topic = MANDEL_STATUS_TOPIC
        self.status_scope = MANDEL_STATUS_SCOPE
        self.status_bus_ready = False
        self.status_subscription = None
        self.last_status_sent = None

    def build(self, demo) -> None:
        """Build the Mandelbrot feature UI using configured application UI types."""
        ui = demo.app.read_part_ui_types()
        self.register_font_roles(
            demo,
            {
                "window_title": {"size": 14, "file_path": "data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 16, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "caption": {"size": 14, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "status": {"size": 16, "file_path": "data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="main",
        )
        self.build_window(
            demo,
            window_control_cls=ui.window_control_cls,
            label_control_cls=ui.label_control_cls,
            canvas_control_cls=ui.canvas_control_cls,
            button_control_cls=ui.button_control_cls,
        )

    def bind_runtime(self, demo) -> None:
        """Bind scheduler, keyboard shortcuts, and event-bus subscription hooks."""
        self.demo = demo  # Store demo reference
        if self.scheduler is None:
            self.scheduler = demo.app.get_scene_scheduler("main")
        self.scheduler.set_message_dispatch_limit(256)
        demo.app.actions.register_action("mandel_failure_preview_decrease", lambda _event: self.adjust_failure_preview_limit(demo, -1))
        demo.app.actions.register_action("mandel_failure_preview_increase", lambda _event: self.adjust_failure_preview_limit(demo, 1))
        demo.app.actions.bind_key(pygame.K_LEFTBRACKET, "mandel_failure_preview_decrease", scene="main")
        demo.app.actions.bind_key(pygame.K_RIGHTBRACKET, "mandel_failure_preview_increase", scene="main")
        self.status_subscription = demo.app.events.subscribe(
            self.status_topic,
            lambda payload: self.on_status_event(demo, payload),
            scope=self.status_scope,
        )
        self.status_bus_ready = True

    def shutdown_runtime(self, demo) -> None:
        """Unsubscribe runtime resources created by bind_runtime."""
        if self.status_subscription is not None:
            demo.app.events.unsubscribe(self.status_subscription)
            self.status_subscription = None
        self.status_bus_ready = False

    def _get_scheduler(self, demo):
        """Resolve and memoize the scene scheduler used by render tasks."""
        scheduler = self.scheduler
        if scheduler is None:
            scheduler = demo.app.get_scene_scheduler("main")
        if scheduler is None:
            raise AttributeError("Mandelbrot scheduler is not available")
        self.scheduler = scheduler
        return scheduler

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
        """Assign accessibility metadata and tab order for Mandelbrot controls."""
        controls = [
            self.reset_button,
            *self.task_buttons,
        ]
        labels = [
            "Clear Mandelbrot surfaces",
            "Run Mandelbrot iterative",
            "Run Mandelbrot recursive",
            "Run Mandelbrot one canvas split",
            "Run Mandelbrot four canvases split",
        ]
        next_index = int(tab_index_start)
        for control, label in zip(controls, labels):
            if control is None:
                continue
            control.set_tab_index(next_index)
            control.set_accessibility(role="button", label=label)
            next_index += 1
        return next_index

    def on_update(self, _host) -> None:
        """Publish post-frame status updates and cross-part status messages."""
        self.update_events()
        status_text = str(self.status_text)
        if status_text == self.last_status_sent:
            return
        self.last_status_sent = status_text
        self.send_message("life_simulation", {"topic": "mandelbrot_status", "status": status_text})

    def format_help_text(self, demo) -> str:
        """Return help text showing render modes and failure-preview shortcut state."""
        return f"Modes: Iterative, Recursive, 1M 4Tasks, 4M 4Tasks | Failure preview [ ]: {self.failure_preview_limit}"

    def set_help_label(self, demo) -> None:
        """Refresh the Mandelbrot help label text."""
        self.help_label.text = self.format_help_text(demo)

    def _set_status_text(self, demo, text: str) -> None:
        """Set canonical status text and keep status label in sync."""
        normalized = str(text)
        self.status_text = normalized
        self.status_label.text = normalized

    def set_failure_preview_limit(self, demo, limit: int) -> int:
        """Set failure summary preview limit and clamp to supported range."""
        clamped = max(self.FAILURE_PREVIEW_MIN, min(self.FAILURE_PREVIEW_MAX, int(limit)))
        self.failure_preview_limit = clamped
        self.set_help_label(demo)
        return clamped

    def adjust_failure_preview_limit(self, demo, delta: int) -> bool:
        """Adjust preview limit by delta and publish immediate user feedback."""
        previous = self.failure_preview_limit
        effective = self.set_failure_preview_limit(demo, previous + int(delta))
        detail = f"Mandelbrot failure preview limit: {effective}"
        if effective == previous:
            detail = f"{detail} (at bound)"
        self.publish_event(MANDEL_KIND_STATUS, detail)
        return True

    def build_window(
        self,
        demo,
        *,
        window_control_cls,
        label_control_cls,
        canvas_control_cls,
        button_control_cls,
    ) -> None:
        """Create the Mandelbrot window, canvases, controls, and status labels."""
        self.demo = demo  # Store demo reference for callbacks
        mandel_rect = demo.app.layout.anchored((640, 724), anchor="top_right", margin=(28, 92), use_rect=True)
        self.window = demo.root.add(
            window_control_cls(
                "mandel_window",
                mandel_rect,
                "Mandelbrot",
                title_font_role=self.font_role("window_title"),
                use_frame_backdrop=True,
            )
        )
        left = mandel_rect.left
        top = mandel_rect.top
        canvas_size = 580
        canvas_x = left + 20
        canvas_y = top + 54
        split_gap = 6
        split_size = (canvas_size - split_gap) // 2
        controls_y = canvas_y + canvas_size + 12
        status_y = controls_y + 38

        self.help_label = demo.app.style_label(
            self.window.add(
                label_control_cls(
                    "mandel_help",
                    Rect(left + 20, top + 30, 590, 20),
                    self.format_help_text(demo),
                )
            ),
            size=14,
            role=self.font_role("caption"),
        )
        self.primary_canvas = self.window.add(canvas_control_cls("mandel_canvas", Rect(canvas_x, canvas_y, canvas_size, canvas_size), max_events=128))
        canvas1 = self.window.add(canvas_control_cls("can1", Rect(canvas_x, canvas_y, split_size, split_size), max_events=32))
        canvas2 = self.window.add(canvas_control_cls("can2", Rect(canvas_x + split_size + split_gap, canvas_y, split_size, split_size), max_events=32))
        canvas3 = self.window.add(canvas_control_cls("can3", Rect(canvas_x, canvas_y + split_size + split_gap, split_size, split_size), max_events=32))
        canvas4 = self.window.add(
            canvas_control_cls("can4", Rect(canvas_x + split_size + split_gap, canvas_y + split_size + split_gap, split_size, split_size), max_events=32)
        )
        self.split_canvases = {"can1": canvas1, "can2": canvas2, "can3": canvas3, "can4": canvas4}

        demo.app.layout.set_linear_properties(
            anchor=(left + 20, controls_y),
            item_width=112,
            item_height=30,
            spacing=8,
            horizontal=True,
        )
        mandel_reset_rect = demo.app.layout.next_linear()
        mandel_iter_rect = demo.app.layout.next_linear()
        mandel_recur_rect = demo.app.layout.next_linear()
        mandel_one_split_rect = demo.app.layout.next_linear()
        mandel_four_split_rect = demo.app.layout.next_linear()

        self.reset_button = self.window.add(
            button_control_cls("mandel_reset", mandel_reset_rect, "Reset", lambda: self.clear(demo), style="angle", font_role=self.font_role("control"))
        )
        mandel_iter_button = self.window.add(
            button_control_cls("mandel_iter", mandel_iter_rect, "Iterative", lambda: self.launch_iterative(demo), style="round", font_role=self.font_role("control"))
        )
        mandel_recur_button = self.window.add(
            button_control_cls("mandel_recur", mandel_recur_rect, "Recursive", lambda: self.launch_recursive(demo), style="round", font_role=self.font_role("control"))
        )
        mandel_one_split_button = self.window.add(
            button_control_cls("mandel_one_split", mandel_one_split_rect, "1M 4Tasks", lambda: self.launch_one_split(demo), style="round", font_role=self.font_role("control"))
        )
        mandel_four_split_button = self.window.add(
            button_control_cls("mandel_four_split", mandel_four_split_rect, "4M 4Tasks", lambda: self.launch_four_split(demo), style="round", font_role=self.font_role("control"))
        )
        self.task_buttons = (
            mandel_iter_button,
            mandel_recur_button,
            mandel_one_split_button,
            mandel_four_split_button,
        )

        default_status = self.status_text
        self.status_label = demo.app.style_label(
            self.window.add(
                label_control_cls("mandel_status", Rect(left + 20, status_y, 590, 20), default_status)
            ),
            role=self.font_role("status"),
        )
        self.status_text = default_status

        canvas1.visible = False
        canvas2.visible = False
        canvas3.visible = False
        canvas4.visible = False
        self.set_task_buttons_disabled(demo, False)
        self.clear(demo)
        self.window.visible = False

    @staticmethod
    def on_status_changed(demo, text: str) -> None:
        """Direct status-label setter used by tests and optional host hooks."""
        demo._mandel_part().status_label.text = text

    def on_status_event(self, demo, payload) -> None:
        """Handle status-bus events and render normalized status text."""
        self._set_status_text(demo, self.format_status(demo, MandelStatusEvent.from_payload(payload)))

    @staticmethod
    def format_status(_demo, payload) -> str:
        """Convert status payload/event values into user-facing status strings."""
        event = MandelStatusEvent.from_payload(payload)
        details = "" if event.detail is None else str(event.detail)
        mapping = {
            "idle": "Mandelbrot: idle",
            MANDEL_KIND_CLEARED: "Mandelbrot: cleared",
            MANDEL_KIND_RUNNING_ITERATIVE: "Mandelbrot: running iterative",
            MANDEL_KIND_RUNNING_RECURSIVE: "Mandelbrot: running recursive",
            MANDEL_KIND_RUNNING_ONE_SPLIT: "Mandelbrot: running 1M 4Tasks",
            MANDEL_KIND_RUNNING_FOUR_SPLIT: "Mandelbrot: running 4M 4Tasks",
            MANDEL_KIND_COMPLETE: "Mandelbrot: complete",
        }
        if event.kind in mapping:
            return mapping[event.kind]
        if event.kind == MANDEL_KIND_FAILED:
            return f"Mandelbrot failed: {details}" if details else "Mandelbrot failed"
        if event.kind == MANDEL_KIND_STATUS:
            return details if details else "Mandelbrot: idle"
        return details if details else f"Mandelbrot: {event.kind}"

    def publish_event(self, kind: str, detail: Optional[str] = None) -> None:
        """Publish status updates through the event bus and local label state."""
        demo = self.demo
        part = self
        if kind in (MANDEL_KIND_CLEARED, MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED):
            part.running_mode = None
        event = MandelStatusEvent(kind=str(kind), detail=None if detail is None else str(detail))
        payload = event.to_payload()
        formatted_status = self.format_status(demo, event)
        # Keep local status in sync before publishing so repeated frame checks do not
        # republish identical running-status events while tasks are still busy.
        self._set_status_text(demo, formatted_status)
        bus_ready = bool(self.status_bus_ready)
        if bus_ready:
            demo.app.events.publish(self.status_topic, payload, scope=self.status_scope)
            return

    def publish_running_status(self) -> None:
        """Publish running-mode telemetry with current active task count."""
        demo = self.demo
        if not self.task_ids:
            return
        mode = self.running_mode if self.running_mode is not None else "running"
        task_count = len(self.task_ids)
        task_word = "task" if task_count == 1 else "tasks"
        detail = f"Mandelbrot: {mode} ({task_count} {task_word})"
        if self.status_text == detail:
            return
        self.publish_event(MANDEL_KIND_STATUS, detail)

    def format_failure_summary(self, failed_details) -> str:
        """Format deterministic, bounded failure summaries for status display."""
        if not failed_details:
            return ""
        if len(failed_details) == 1:
            task_id, error = failed_details[0]
            return f"{task_id}: {error}"

        configured = int(self.failure_preview_limit)
        limit = max(self.FAILURE_PREVIEW_MIN, min(self.FAILURE_PREVIEW_MAX, configured))
        preview = failed_details[:limit]
        summary = "; ".join(f"{task_id}: {error}" for task_id, error in preview)
        remaining = len(failed_details) - len(preview)
        if remaining > 0:
            summary = f"{summary}; +{remaining} more"
        return f"{len(failed_details)} tasks failed - {summary}"

    def mandel_col(self, k: int) -> Tuple[int, int, int]:
        """Map an iteration count to the Mandelbrot palette color."""
        if k >= self.max_iter - 1:
            return (0, 0, 0)
        return self.mandel_cols[k % len(self.mandel_cols)]

    def mandel_viewport(self, _demo, width: int, height: int) -> Tuple[complex, float]:
        """Return viewport center and scale for the requested render dimensions."""
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        return center, scale

    def mandel_pixel(self, _demo, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        """Compute Mandelbrot iteration count for one pixel coordinate."""
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(self.max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return self.max_iter - 1

    def clear_surfaces(self, demo) -> None:
        """Clear all Mandelbrot canvases to the theme medium background color."""
        self.primary_canvas.canvas.fill(demo.app.theme.medium)
        self.split_canvases["can1"].canvas.fill(demo.app.theme.medium)
        self.split_canvases["can2"].canvas.fill(demo.app.theme.medium)
        self.split_canvases["can3"].canvas.fill(demo.app.theme.medium)
        self.split_canvases["can4"].canvas.fill(demo.app.theme.medium)

    def set_task_buttons_disabled(self, demo, disabled: bool) -> None:
        """Enable or disable launch buttons and keep focus state valid."""
        buttons = self.task_buttons
        for button in buttons:
            button.enabled = not disabled
        if not disabled:
            return
        if not buttons:
            return
        focused = demo.app.focus.focused_node
        if focused not in buttons:
            return
        if self.reset_button.visible and self.reset_button.enabled and self.reset_button.accepts_focus():
            demo.app.focus.set_focus(self.reset_button, show_hint=False)
            return
        demo.app.focus.revalidate_focus(demo.app.scene)

    def show_single_canvas(self, demo) -> None:
        """Show the primary render canvas and hide split canvases."""
        self.primary_canvas.visible = True
        self.split_canvases["can1"].visible = False
        self.split_canvases["can2"].visible = False
        self.split_canvases["can3"].visible = False
        self.split_canvases["can4"].visible = False
        self.clear_surfaces(demo)

    def prepare_single_canvas_run(self, demo) -> None:
        """Prepare UI for single-canvas rendering modes."""
        self.set_task_buttons_disabled(demo, True)
        self.show_single_canvas(demo)

    def prepare_split_canvas_run(self, demo) -> None:
        """Prepare UI for split-canvas rendering mode."""
        self.set_task_buttons_disabled(demo, True)
        self.primary_canvas.visible = False
        self.split_canvases["can1"].visible = True
        self.split_canvases["can2"].visible = True
        self.split_canvases["can3"].visible = True
        self.split_canvases["can4"].visible = True
        self.clear_surfaces(demo)

    def canvas_for_task(self, demo, task_id: str):
        """Resolve target canvas surface for a given scheduler task id."""
        canvas_by_task = {
            "iter": self.primary_canvas.canvas,
            "recu": self.primary_canvas.canvas,
            "1": self.primary_canvas.canvas,
            "2": self.primary_canvas.canvas,
            "3": self.primary_canvas.canvas,
            "4": self.primary_canvas.canvas,
            "can1": self.split_canvases["can1"].canvas,
            "can2": self.split_canvases["can2"].canvas,
            "can3": self.split_canvases["can3"].canvas,
            "can4": self.split_canvases["can4"].canvas,
        }
        return canvas_by_task.get(task_id)

    def make_progress_handler(self, demo, task_id: str):
        """Build a scheduler message callback that applies task render payloads."""
        def handler(payload):
            self.apply_result(demo, task_id, payload)

        return handler

    def apply_result(self, demo, task_id: str, payload) -> None:
        """Apply task payloads to target canvas surfaces, with bounds clipping."""
        canvas = self.canvas_for_task(demo, task_id)
        if canvas is None:
            return

        if task_id == "iter":
            y_pos, row = payload
            if y_pos < 0 or y_pos >= canvas.get_height():
                return
            for x_pos, value in enumerate(row):
                if 0 <= x_pos < canvas.get_width():
                    canvas.set_at((x_pos, y_pos), self.mandel_col(value))
            return

        x_pos, y_pos, width, height, values = payload
        x0 = max(0, x_pos)
        y0 = max(0, y_pos)
        x1 = min(canvas.get_width(), x_pos + width)
        y1 = min(canvas.get_height(), y_pos + height)
        if x1 <= x0 or y1 <= y0:
            return

        if isinstance(values, int):
            # Scalar payload means region is uniform and can be filled in one call.
            canvas.fill(self.mandel_col(values), Rect(x0, y0, x1 - x0, y1 - y0))
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
                canvas.set_at((xx, yy), self.mandel_col(values[idx]))
                idx += 1

    def clear(self, demo) -> None:
        """Cancel active tasks, reset canvases/UI state, and publish cleared status."""
        scheduler = self._get_scheduler(demo)
        scheduler.remove_tasks(*self.task_id_pool)
        self.task_ids.clear()
        self.running_mode = None
        self.show_single_canvas(demo)
        self.set_task_buttons_disabled(demo, False)
        self.publish_event(MANDEL_KIND_CLEARED)

    def iterative_task(self, demo, task_id, params):
        """Worker entrypoint for iterative full-frame scanline rendering."""
        scheduler = self._get_scheduler(demo)
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [self.mandel_pixel(demo, x, y, width, height, center, scale) for x in range(width)]
            scheduler.send_message(task_id, (y, row))
        return None

    def recursive_fill(self, demo, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
        """Recursively subdivide a rectangle and emit fill/pixel payload messages."""
        scheduler = self._get_scheduler(demo)
        if w <= 0 or h <= 0:
            return
        tl = self.mandel_pixel(demo, x, y, width, height, center, scale)
        tr = self.mandel_pixel(demo, x + w - 1, y, width, height, center, scale)
        bl = self.mandel_pixel(demo, x, y + h - 1, width, height, center, scale)
        br = self.mandel_pixel(demo, x + w - 1, y + h - 1, width, height, center, scale)
        if w <= 4 or h <= 4:
            values = []
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    values.append(self.mandel_pixel(demo, xx, yy, width, height, center, scale))
            scheduler.send_message(task_id, (x, y, w, h, values))
            return
        if tl == tr == bl == br:
            scheduler.send_message(task_id, (x, y, w, h, tl))
            return
        hw = w // 2
        hh = h // 2
        self.recursive_fill(demo, task_id, x, y, hw, hh, width, height, center, scale)
        self.recursive_fill(demo, task_id, x + hw, y, w - hw, hh, width, height, center, scale)
        self.recursive_fill(demo, task_id, x, y + hh, hw, h - hh, width, height, center, scale)
        self.recursive_fill(demo, task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

    def recursive_task(self, demo, task_id, params):
        """Worker entrypoint for recursive rendering over a requested rectangle."""
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        rect = Rect(params.get("rect", Rect(0, 0, width, height)))
        self.recursive_fill(demo, task_id, rect.x, rect.y, rect.width, rect.height, width, height, center, scale)
        return None

    def queue_recursive_task(self, demo, task_id: str, rect: Rect, size: Tuple[int, int], center: complex, scale: float) -> None:
        """Queue one recursive render task and track its task id as active."""
        scheduler = self._get_scheduler(demo)
        scheduler.add_task(
            task_id,
            lambda callback_task_id, params: self.recursive_task(demo, callback_task_id, params),
            parameters={"size": size, "center": center, "scale": scale, "rect": Rect(rect)},
            message_method=self.make_progress_handler(demo, task_id),
        )
        self.task_ids.add(task_id)

    def launch_iterative(self, demo) -> None:
        """Launch iterative render mode when no Mandelbrot task is already running."""
        scheduler = self._get_scheduler(demo)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self.prepare_single_canvas_run(demo)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(demo, width, height)
        scheduler.add_task(
            "iter",
            lambda task_id, params: self.iterative_task(demo, task_id, params),
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=self.make_progress_handler(demo, "iter"),
        )
        self.task_ids.add("iter")
        self.running_mode = "running iterative"
        self.publish_event(MANDEL_KIND_RUNNING_ITERATIVE)
        self.publish_running_status()

    def launch_recursive(self, demo) -> None:
        """Launch single-task recursive render mode."""
        scheduler = self._get_scheduler(demo)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self.prepare_single_canvas_run(demo)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(demo, width, height)
        self.queue_recursive_task(demo, "recu", Rect(0, 0, width, height), (width, height), center, scale)
        self.running_mode = "running recursive"
        self.publish_event(MANDEL_KIND_RUNNING_RECURSIVE)
        self.publish_running_status()

    def launch_one_split(self, demo) -> None:
        """Launch four recursive tasks that render quadrants into one canvas."""
        scheduler = self._get_scheduler(demo)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self.prepare_single_canvas_run(demo)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(demo, width, height)
        left_w, top_h = width // 2, height // 2
        right_w, bottom_h = width - left_w, height - top_h
        self.queue_recursive_task(demo, "1", Rect(0, 0, left_w, top_h), (width, height), center, scale)
        self.queue_recursive_task(demo, "2", Rect(left_w, 0, right_w, top_h), (width, height), center, scale)
        self.queue_recursive_task(demo, "3", Rect(0, top_h, left_w, bottom_h), (width, height), center, scale)
        self.queue_recursive_task(demo, "4", Rect(left_w, top_h, right_w, bottom_h), (width, height), center, scale)
        self.running_mode = "running 1M 4Tasks"
        self.publish_event(MANDEL_KIND_RUNNING_ONE_SPLIT)
        self.publish_running_status()

    def launch_four_split(self, demo) -> None:
        """Launch four recursive tasks across four independent split canvases."""
        scheduler = self._get_scheduler(demo)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self.prepare_split_canvas_run(demo)
        width, height = self.split_canvases["can1"].canvas.get_size()
        center, scale = self.mandel_viewport(demo, width, height)
        for task_id in ("can1", "can2", "can3", "can4"):
            self.queue_recursive_task(demo, task_id, Rect(0, 0, width, height), (width, height), center, scale)
        self.running_mode = "running 4M 4Tasks"
        self.publish_event(MANDEL_KIND_RUNNING_FOUR_SPLIT)
        self.publish_running_status()

    def update_events(self) -> None:
        """Drain scheduler event streams and synchronize UI/task status state."""
        demo = self.demo
        if demo is None:
            return
        scheduler = self._get_scheduler(demo)
        finished = scheduler.get_finished_events()
        failed = scheduler.get_failed_events()
        failed_details = []

        for event in finished:
            if event.task_id in self.task_ids:
                self.task_ids.remove(event.task_id)
                scheduler.pop_result(event.task_id, None)
        for event in failed:
            if event.task_id in self.task_ids:
                self.task_ids.remove(event.task_id)
                failed_details.append((str(event.task_id), str(event.error)))

        if failed_details:
            failed_details.sort(key=lambda item: (item[0], item[1]))
            self.publish_event(MANDEL_KIND_FAILED, self.format_failure_summary(failed_details))

        busy = scheduler.tasks_busy_match_any(*self.task_id_pool)
        self.set_task_buttons_disabled(demo, busy)
        if busy:
            self.publish_running_status()
        scheduler.clear_events()
        if not busy and self.status_text.startswith("Mandelbrot: running"):
            self.running_mode = None
            self.publish_event(MANDEL_KIND_COMPLETE)
