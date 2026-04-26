"""Mandelbrot feature part extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import pygame
from dataclasses import dataclass
from typing import Optional, Tuple

from pygame import Rect
from gui_do import LogicFeature, RoutedFeature


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


_MANDEL_LOGIC_PRIMARY = "mandelbrot_logic_primary"
_MANDEL_LOGIC_CAN1 = "mandelbrot_logic_can1"
_MANDEL_LOGIC_CAN2 = "mandelbrot_logic_can2"
_MANDEL_LOGIC_CAN3 = "mandelbrot_logic_can3"
_MANDEL_LOGIC_CAN4 = "mandelbrot_logic_can4"


class MandelbrotLogicFeature(LogicFeature):
    """Domain logic provider for Mandelbrot pixel and algorithm calculations."""

    RECURSIVE_LEAF_SPAN = 8

    def __init__(self, name: str = _MANDEL_LOGIC_PRIMARY, *, scene_name: str = "main") -> None:
        super().__init__(name, scene_name=scene_name)
        self.mandel_cols = (
            (66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
            (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
            (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
            (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
        )
        self.max_iter = 48

    def bind_runtime(self, _host) -> None:
        self._feature_manager.register_runnable(self.name, "iterative_task", self.run_iterative_task)
        self._feature_manager.register_runnable(self.name, "recursive_task", self.run_recursive_task)

    def mandel_col(self, k: int) -> Tuple[int, int, int]:
        if k >= self.max_iter - 1:
            return (0, 0, 0)
        return self.mandel_cols[k % len(self.mandel_cols)]

    @staticmethod
    def mandel_viewport(width: int, height: int) -> Tuple[complex, float]:
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        return center, scale

    def mandel_pixel(self, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(self.max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return self.max_iter - 1

    def run_iterative_task(self, scheduler, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [self.mandel_pixel(x, y, width, height, center, scale) for x in range(width)]
            scheduler.send_message(task_id, (y, row))
        return None

    def _recursive_fill(self, scheduler, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
        if w <= 0 or h <= 0:
            return
        if w <= self.RECURSIVE_LEAF_SPAN or h <= self.RECURSIVE_LEAF_SPAN:
            values = []
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    values.append(self.mandel_pixel(xx, yy, width, height, center, scale))
            scheduler.send_message(task_id, (x, y, w, h, values))
            return
        hw = w // 2
        hh = h // 2
        self._recursive_fill(scheduler, task_id, x, y, hw, hh, width, height, center, scale)
        self._recursive_fill(scheduler, task_id, x + hw, y, w - hw, hh, width, height, center, scale)
        self._recursive_fill(scheduler, task_id, x, y + hh, hw, h - hh, width, height, center, scale)
        self._recursive_fill(scheduler, task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

    def run_recursive_task(self, scheduler, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        rect = Rect(params.get("rect", Rect(0, 0, width, height)))
        self._recursive_fill(scheduler, task_id, rect.x, rect.y, rect.width, rect.height, width, height, center, scale)
        return None


class MandelbrotRenderFeature(RoutedFeature):
    """Build and run the Mandelbrot demo windows, tasks, and status plumbing."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    FAILURE_PREVIEW_MIN = 1
    FAILURE_PREVIEW_MAX = 20
    LOGIC_ALIAS_PRIMARY = "primary"
    LOGIC_ALIAS_CAN1 = "can1"
    LOGIC_ALIAS_CAN2 = "can2"
    LOGIC_ALIAS_CAN3 = "can3"
    LOGIC_ALIAS_CAN4 = "can4"
    DEFAULT_MESSAGE_DISPATCH_LIMIT = 512
    BUSY_MESSAGE_DISPATCH_LIMIT = 128

    def __init__(self) -> None:
        super().__init__("mandelbrot", scene_name="main")
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
        self._busy_dispatch_mode = False
        self._task_logic_alias = {
            "can1": self.LOGIC_ALIAS_CAN1,
            "can2": self.LOGIC_ALIAS_CAN2,
            "can3": self.LOGIC_ALIAS_CAN3,
            "can4": self.LOGIC_ALIAS_CAN4,
        }

    def on_register(self, host) -> None:
        """Auto-register all companion logic features when this feature is registered."""
        for name in (
            _MANDEL_LOGIC_PRIMARY,
            _MANDEL_LOGIC_CAN1,
            _MANDEL_LOGIC_CAN2,
            _MANDEL_LOGIC_CAN3,
            _MANDEL_LOGIC_CAN4,
        ):
            self._feature_manager.register(MandelbrotLogicFeature(name), host)

    def build(self, host) -> None:
        """Build the Mandelbrot feature UI using configured application UI types."""
        ui = host.app.read_feature_ui_types()
        self.register_font_roles(
            host,
            {
                "window_title": {"size": 14, "file_path": "demo_features/data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 16, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "caption": {"size": 14, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "status": {"size": 16, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="main",
        )
        self.build_window(
            host,
            window_control_cls=ui.window_control_cls,
            label_control_cls=ui.label_control_cls,
            canvas_control_cls=ui.canvas_control_cls,
            button_control_cls=ui.button_control_cls,
        )

    def bind_runtime(self, host) -> None:
        """Bind scheduler, keyboard shortcuts, and event-bus subscription hooks."""
        self.demo = host  # Store host reference
        if self.scheduler is None:
            self.scheduler = host.app.get_scene_scheduler("main")
        self._bind_logic_aliases()
        self._set_busy_dispatch_mode(False)
        host.app.actions.register_action("mandel_failure_preview_decrease", lambda _event: self.adjust_failure_preview_limit(host, -1))
        host.app.actions.register_action("mandel_failure_preview_increase", lambda _event: self.adjust_failure_preview_limit(host, 1))
        host.app.actions.bind_key(pygame.K_LEFTBRACKET, "mandel_failure_preview_decrease", scene="main")
        host.app.actions.bind_key(pygame.K_RIGHTBRACKET, "mandel_failure_preview_increase", scene="main")
        self.status_subscription = host.app.events.subscribe(
            self.status_topic,
            lambda payload: self.on_status_event(host, payload),
            scope=self.status_scope,
        )
        self.status_bus_ready = True

    def _bind_logic_aliases(self) -> None:
        bindings = {
            self.LOGIC_ALIAS_PRIMARY: _MANDEL_LOGIC_PRIMARY,
            self.LOGIC_ALIAS_CAN1: _MANDEL_LOGIC_CAN1,
            self.LOGIC_ALIAS_CAN2: _MANDEL_LOGIC_CAN2,
            self.LOGIC_ALIAS_CAN3: _MANDEL_LOGIC_CAN3,
            self.LOGIC_ALIAS_CAN4: _MANDEL_LOGIC_CAN4,
        }
        for alias, provider_name in bindings.items():
            if self.bound_logic_name(alias=alias) is None:
                self.bind_logic(provider_name, alias=alias)

    def _resolve_logic(self, alias: str) -> Optional[MandelbrotLogicFeature]:
        provider_name = self.bound_logic_name(alias=alias)
        if provider_name is None:
            return None
        provider = self._feature_manager.get(provider_name)
        if isinstance(provider, MandelbrotLogicFeature):
            return provider
        return None

    def _run_logic_runnable(self, alias: str, runnable_name: str, task_id: str, params):
        demo = self.demo
        if demo is None:
            return False
        provider_name = self.bound_logic_name(alias=alias)
        if provider_name is None:
            return False
        try:
            scheduler = self._get_scheduler(demo)
            demo.app.run_feature_runnable(provider_name, runnable_name, scheduler, task_id, params)
            return True
        except KeyError:
            return False

    def shutdown_runtime(self, host) -> None:
        """Unsubscribe runtime resources created by bind_runtime."""
        if self.status_subscription is not None:
            host.app.events.unsubscribe(self.status_subscription)
            self.status_subscription = None
        self.status_bus_ready = False
        self._set_busy_dispatch_mode(False)

    def _set_busy_dispatch_mode(self, busy: bool) -> None:
        scheduler = self.scheduler
        if scheduler is None:
            return
        target_busy = bool(busy)
        if target_busy == self._busy_dispatch_mode:
            return
        if target_busy:
            scheduler.set_message_dispatch_limit(self.BUSY_MESSAGE_DISPATCH_LIMIT)
        else:
            scheduler.set_message_dispatch_limit(self.DEFAULT_MESSAGE_DISPATCH_LIMIT)
        self._busy_dispatch_mode = target_busy

    def _get_scheduler(self, host):
        """Resolve and memoize the scene scheduler used by render tasks."""
        scheduler = self.scheduler
        if scheduler is None:
            scheduler = host.app.get_scene_scheduler("main")
        if scheduler is None:
            raise AttributeError("Mandelbrot scheduler is not available")
        self.scheduler = scheduler
        return scheduler

    def configure_accessibility(self, host, tab_index_start: int) -> int:
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
        """Publish post-frame status updates for Mandelbrot state."""
        self.update_events()

    def format_help_text(self) -> str:
        """Return help text showing the available render modes."""
        return "Modes: Iterative, Recursive, 1 Mandelbrot 4 Tasks, 4 Mandelbrots 4 Tasks"

    def set_help_label(self, host) -> None:
        """Refresh the Mandelbrot help label text."""
        self.help_label.text = self.format_help_text()

    def _set_status_text(self, text: str) -> None:
        """Set canonical status text and keep status label in sync."""
        normalized = str(text)
        self.status_text = normalized
        self.status_label.text = normalized

    def set_failure_preview_limit(self, host, limit: int) -> int:
        """Set failure summary preview limit and clamp to supported range."""
        clamped = max(self.FAILURE_PREVIEW_MIN, min(self.FAILURE_PREVIEW_MAX, int(limit)))
        self.failure_preview_limit = clamped
        self.set_help_label(host)
        return clamped

    def adjust_failure_preview_limit(self, host, delta: int) -> bool:
        """Adjust preview limit by delta and publish immediate user feedback."""
        previous = self.failure_preview_limit
        effective = self.set_failure_preview_limit(host, previous + int(delta))
        detail = f"Mandelbrot failure preview limit: {effective}"
        if effective == previous:
            detail = f"{detail} (at bound)"
        self.publish_event(MANDEL_KIND_STATUS, detail)
        return True

    def build_window(
        self,
        host,
        *,
        window_control_cls,
        label_control_cls,
        canvas_control_cls,
        button_control_cls,
    ) -> None:
        """Create the Mandelbrot window, canvases, controls, and status labels."""
        self.demo = host  # Store host reference for callbacks
        mandel_rect = host.app.layout.anchored((640, 717), anchor="top_right", margin=(28, 92), use_rect=True)
        self.window = host.root.add(
            window_control_cls(
                "mandel_window",
                mandel_rect,
                "Mandelbrot",
                title_font_role=self.font_role("window_title"),
                use_frame_backdrop=True,
            )
        )
        content_rect = self.window.content_rect()
        padding = 8

        # Help label at top
        help_rect = Rect(content_rect.left + padding, content_rect.top, content_rect.width - padding * 2, 20)
        self.help_label = host.app.style_label(
            self.window.add(
                label_control_cls(
                    "mandel_help",
                    help_rect,
                    self.format_help_text(),
                )
            ),
            size=14,
            role=self.font_role("caption"),
        )

        # Bottom control and status heights
        control_height = 30
        status_height = 20
        controls_and_status_height = control_height + status_height + 12
        bottom_visual_padding = 5

        # Available space for canvases
        canvas_area_top = help_rect.bottom
        canvas_area_bottom = content_rect.bottom - bottom_visual_padding - controls_and_status_height
        canvas_area_height = canvas_area_bottom - canvas_area_top
        canvas_area_width = content_rect.width - padding * 2

        # Canvas layout
        grid_gap = 6
        split_size = (canvas_area_width - grid_gap) // 2

        # Primary canvas (full width)
        primary_canvas_rect = Rect(
            content_rect.left + padding,
            canvas_area_top,
            canvas_area_width,
            canvas_area_height
        )
        self.primary_canvas = self.window.add(
            canvas_control_cls("mandel_canvas", primary_canvas_rect, max_events=128)
        )

        # Split canvases in 2x2 grid
        canvas1_rect = Rect(
            content_rect.left + padding,
            canvas_area_top,
            split_size,
            (canvas_area_height - grid_gap) // 2
        )
        canvas2_rect = Rect(
            canvas1_rect.right + grid_gap,
            canvas_area_top,
            split_size,
            (canvas_area_height - grid_gap) // 2
        )
        canvas3_rect = Rect(
            content_rect.left + padding,
            canvas1_rect.bottom + grid_gap,
            split_size,
            (canvas_area_height - grid_gap) // 2
        )
        canvas4_rect = Rect(
            canvas1_rect.right + grid_gap,
            canvas1_rect.bottom + grid_gap,
            split_size,
            (canvas_area_height - grid_gap) // 2
        )

        canvas1 = self.window.add(canvas_control_cls("can1", canvas1_rect, max_events=32))
        canvas2 = self.window.add(canvas_control_cls("can2", canvas2_rect, max_events=32))
        canvas3 = self.window.add(canvas_control_cls("can3", canvas3_rect, max_events=32))
        canvas4 = self.window.add(canvas_control_cls("can4", canvas4_rect, max_events=32))
        self.split_canvases = {"can1": canvas1, "can2": canvas2, "can3": canvas3, "can4": canvas4}

        # Controls at bottom: evenly divide a padded strip across all controls,
        # then center each control inside its slot with extra inner spacing.
        controls_y = canvas_area_bottom + 6
        control_count = 5
        row_strip_padding = 12
        slot_inner_padding = 8
        strip_left = content_rect.left + padding + row_strip_padding
        strip_width = max(1, canvas_area_width - (row_strip_padding * 2))
        slot_width = strip_width / float(control_count)

        def control_rect_at(index: int) -> Rect:
            slot_left = strip_left + int(round(slot_width * index))
            next_slot_left = strip_left + int(round(slot_width * (index + 1)))
            slot_pixel_width = max(1, next_slot_left - slot_left)
            control_width = max(1, slot_pixel_width - (slot_inner_padding * 2))
            control_left = slot_left + ((slot_pixel_width - control_width) // 2)
            return Rect(control_left, controls_y, control_width, control_height)

        mandel_reset_rect = control_rect_at(0)
        mandel_iter_rect = control_rect_at(1)
        mandel_recur_rect = control_rect_at(2)
        mandel_one_split_rect = control_rect_at(3)
        mandel_four_split_rect = control_rect_at(4)

        self.reset_button = self.window.add(
            button_control_cls("mandel_reset", mandel_reset_rect, "Reset", lambda: self.clear(host), style="angle", font_role=self.font_role("control"))
        )
        mandel_iter_button = self.window.add(
            button_control_cls("mandel_iter", mandel_iter_rect, "Iterative", lambda: self.launch_iterative(host), style="round", font_role=self.font_role("control"))
        )
        mandel_recur_button = self.window.add(
            button_control_cls("mandel_recur", mandel_recur_rect, "Recursive", lambda: self.launch_recursive(host), style="round", font_role=self.font_role("control"))
        )
        mandel_one_split_button = self.window.add(
            button_control_cls("mandel_one_split", mandel_one_split_rect, "1M 4Tasks", lambda: self.launch_one_split(host), style="round", font_role=self.font_role("control"))
        )
        mandel_four_split_button = self.window.add(
            button_control_cls("mandel_four_split", mandel_four_split_rect, "4M 4Tasks", lambda: self.launch_four_split(host), style="round", font_role=self.font_role("control"))
        )
        self.task_buttons = (
            mandel_iter_button,
            mandel_recur_button,
            mandel_one_split_button,
            mandel_four_split_button,
        )

        # Status label below controls, aligned with left edge
        status_y = controls_y + control_height + 6
        default_status = self.status_text
        self.status_label = host.app.style_label(
            self.window.add(
                label_control_cls("mandel_status", Rect(content_rect.left + padding, status_y, canvas_area_width, status_height), default_status)
            ),
            role=self.font_role("status"),
        )
        self.status_text = default_status

        canvas1.visible = False
        canvas2.visible = False
        canvas3.visible = False
        canvas4.visible = False
        self.set_task_buttons_disabled(host, False)
        self.clear(host)
        self.window.visible = False

    def on_status_event(self, host, payload) -> None:
        """Handle status-bus events and render normalized status text."""
        self._set_status_text(self.format_status(host, MandelStatusEvent.from_payload(payload)))

    @staticmethod
    def format_status(_host, payload) -> str:
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
        self._set_status_text(formatted_status)
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
        return self._resolve_logic(self.LOGIC_ALIAS_PRIMARY).mandel_col(k)

    def mandel_viewport(self, _host, width: int, height: int) -> Tuple[complex, float]:
        """Return viewport center and scale for the requested render dimensions."""
        return self._resolve_logic(self.LOGIC_ALIAS_PRIMARY).mandel_viewport(width, height)

    def mandel_pixel(self, _host, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        """Compute Mandelbrot iteration count for one pixel coordinate."""
        return self._resolve_logic(self.LOGIC_ALIAS_PRIMARY).mandel_pixel(px, py, width, height, center, scale)

    def clear_surfaces(self, host) -> None:
        """Clear all Mandelbrot canvases to the theme medium background color."""
        self.primary_canvas.canvas.fill(host.app.theme.medium)
        self.split_canvases["can1"].canvas.fill(host.app.theme.medium)
        self.split_canvases["can2"].canvas.fill(host.app.theme.medium)
        self.split_canvases["can3"].canvas.fill(host.app.theme.medium)
        self.split_canvases["can4"].canvas.fill(host.app.theme.medium)

    def set_task_buttons_disabled(self, host, disabled: bool) -> None:
        """Enable or disable launch buttons and keep focus state valid."""
        buttons = self.task_buttons
        for button in buttons:
            button.enabled = not disabled
        if not disabled:
            return
        if not buttons:
            return
        focused = host.app.focus.focused_node
        if focused not in buttons:
            return
        if self.reset_button.visible and self.reset_button.enabled and self.reset_button.accepts_focus():
            host.app.focus.set_focus(self.reset_button)
            return
        host.app.focus.revalidate_focus(host.app.scene)

    def show_single_canvas(self, host) -> None:
        """Show the primary render canvas and hide split canvases."""
        self.primary_canvas.visible = True
        self.split_canvases["can1"].visible = False
        self.split_canvases["can2"].visible = False
        self.split_canvases["can3"].visible = False
        self.split_canvases["can4"].visible = False
        self.clear_surfaces(host)

    def prepare_single_canvas_run(self, host) -> None:
        """Prepare UI for single-canvas rendering modes."""
        self.set_task_buttons_disabled(host, True)
        self.show_single_canvas(host)

    def prepare_split_canvas_run(self, host) -> None:
        """Prepare UI for split-canvas rendering mode."""
        self.set_task_buttons_disabled(host, True)
        self.primary_canvas.visible = False
        self.split_canvases["can1"].visible = True
        self.split_canvases["can2"].visible = True
        self.split_canvases["can3"].visible = True
        self.split_canvases["can4"].visible = True
        self.clear_surfaces(host)

    def canvas_for_task(self, host, task_id: str):
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

    def make_progress_handler(self, host, task_id: str):
        """Build a scheduler message callback that applies task render payloads."""
        def handler(payload):
            self.apply_result(host, task_id, payload)

        return handler

    def apply_result(self, host, task_id: str, payload) -> None:
        """Apply task payloads to target canvas surfaces, with bounds clipping."""
        canvas = self.canvas_for_task(host, task_id)
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

    def clear(self, host) -> None:
        """Cancel active tasks, reset canvases/UI state, and publish cleared status."""
        scheduler = self._get_scheduler(host)
        scheduler.remove_tasks(*self.task_id_pool)
        self.task_ids.clear()
        self.running_mode = None
        self._set_busy_dispatch_mode(False)
        self.show_single_canvas(host)
        self.set_task_buttons_disabled(host, False)
        self.publish_event(MANDEL_KIND_CLEARED)

    def iterative_task(self, host, task_id, params):
        """Worker entrypoint for iterative full-frame scanline rendering."""
        self._run_logic_runnable(self.LOGIC_ALIAS_PRIMARY, "iterative_task", str(task_id), params)
        return None

    def queue_recursive_task(
        self,
        host,
        task_id: str,
        rect: Rect,
        size: Tuple[int, int],
        center: complex,
        scale: float,
        *,
        logic_alias: str,
    ) -> None:
        """Queue one recursive render task and track its task id as active."""
        scheduler = self._get_scheduler(host)
        scheduler.add_task(
            task_id,
            lambda callback_task_id, params: self._run_recursive_task_for_alias(host, logic_alias, callback_task_id, params),
            parameters={"size": size, "center": center, "scale": scale, "rect": Rect(rect)},
            message_method=self.make_progress_handler(host, task_id),
        )
        self.task_ids.add(task_id)

    def _run_recursive_task_for_alias(self, host, logic_alias: str, task_id, params):
        self._run_logic_runnable(logic_alias, "recursive_task", str(task_id), params)
        return None

    def launch_iterative(self, host) -> None:
        """Launch iterative render mode when no Mandelbrot task is already running."""
        scheduler = self._get_scheduler(host)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self._set_busy_dispatch_mode(True)
        self.prepare_single_canvas_run(host)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        scheduler.add_task(
            "iter",
            lambda task_id, params: self.iterative_task(host, task_id, params),
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=self.make_progress_handler(host, "iter"),
        )
        self.task_ids.add("iter")
        self.running_mode = "running iterative"
        self.publish_event(MANDEL_KIND_RUNNING_ITERATIVE)
        self.publish_running_status()

    def launch_recursive(self, host) -> None:
        """Launch single-task recursive render mode."""
        scheduler = self._get_scheduler(host)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self._set_busy_dispatch_mode(True)
        self.prepare_single_canvas_run(host)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        self.queue_recursive_task(
            host,
            "recu",
            Rect(0, 0, width, height),
            (width, height),
            center,
            scale,
            logic_alias=self.LOGIC_ALIAS_PRIMARY,
        )
        self.running_mode = "running recursive"
        self.publish_event(MANDEL_KIND_RUNNING_RECURSIVE)
        self.publish_running_status()

    def launch_one_split(self, host) -> None:
        """Launch four recursive tasks that render quadrants into one canvas."""
        scheduler = self._get_scheduler(host)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self._set_busy_dispatch_mode(True)
        self.prepare_single_canvas_run(host)
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        left_w, top_h = width // 2, height // 2
        right_w, bottom_h = width - left_w, height - top_h
        self.queue_recursive_task(
            host,
            "1",
            Rect(0, 0, left_w, top_h),
            (width, height),
            center,
            scale,
            logic_alias=self.LOGIC_ALIAS_PRIMARY,
        )
        self.queue_recursive_task(
            host,
            "2",
            Rect(left_w, 0, right_w, top_h),
            (width, height),
            center,
            scale,
            logic_alias=self.LOGIC_ALIAS_PRIMARY,
        )
        self.queue_recursive_task(
            host,
            "3",
            Rect(0, top_h, left_w, bottom_h),
            (width, height),
            center,
            scale,
            logic_alias=self.LOGIC_ALIAS_PRIMARY,
        )
        self.queue_recursive_task(
            host,
            "4",
            Rect(left_w, top_h, right_w, bottom_h),
            (width, height),
            center,
            scale,
            logic_alias=self.LOGIC_ALIAS_PRIMARY,
        )
        self.running_mode = "running 1M 4Tasks"
        self.publish_event(MANDEL_KIND_RUNNING_ONE_SPLIT)
        self.publish_running_status()

    def launch_four_split(self, host) -> None:
        """Launch four recursive tasks across four independent split canvases."""
        scheduler = self._get_scheduler(host)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return
        self._set_busy_dispatch_mode(True)
        self.prepare_split_canvas_run(host)
        width, height = self.split_canvases["can1"].canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        for task_id in ("can1", "can2", "can3", "can4"):
            self.queue_recursive_task(
                host,
                task_id,
                Rect(0, 0, width, height),
                (width, height),
                center,
                scale,
                logic_alias=self._task_logic_alias[task_id],
            )
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
        self._set_busy_dispatch_mode(busy)
        self.set_task_buttons_disabled(demo, busy)
        if busy:
            self.publish_running_status()
        scheduler.clear_events()
        if not busy and self.status_text.startswith("Mandelbrot: running"):
            self.running_mode = None
            self.publish_event(MANDEL_KIND_COMPLETE)
