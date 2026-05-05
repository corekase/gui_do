"""Mandelbrot feature part extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from typing import Optional, Tuple

from pygame import Rect
from gui_do import inset_rect, RoutedFeature, WindowControl
from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    bind_routed_feature_lifecycle,
    EventSubscriptionSpec,
    LogicBindingSpec,
    create_feature_presented_window,
    ensure_scene_scheduler,
    register_routed_feature_companions,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    shutdown_routed_feature_lifecycle,
)
from .mandelbrot_status_event import MandelStatusEvent
from .mandelbrot_logic import MandelbrotLogicFeature


# ---------------------------------------------------------------------------
# Mandelbrot window layout constants — single source of truth for sizing and layout
# ---------------------------------------------------------------------------
_MANDEL_PAD = 10            # Uniform padding inside the window body on all four sides
_MANDEL_CTRL_GAP = 8        # Gap between canvas bottom edge and the button strip
_MANDEL_STATUS_GAP = 6      # Gap between button strip and status label
_MANDEL_CTRL_H = 30         # Button strip height
_MANDEL_STATUS_H = 20       # Status label height
_MANDEL_CANVAS_H = 560      # Canvas height
_MANDEL_TITLEBAR_H = 24     # Estimated titlebar height (matches size-14 title font)

# Button strip sizing — canvas width is derived so buttons always fit exactly
_MANDEL_BTN_COUNT = 5
_MANDEL_BTN_W = 120         # Per-button width (change this to resize all buttons)
_MANDEL_BTN_SPACING = 8     # Gap between adjacent buttons
_MANDEL_ROW_STRIP_PAD = 12  # Padding on each side of the button row
_MANDEL_CANVAS_W = (
    _MANDEL_BTN_COUNT * _MANDEL_BTN_W
    + (_MANDEL_BTN_COUNT - 1) * _MANDEL_BTN_SPACING
    + 2 * _MANDEL_ROW_STRIP_PAD
)

_MANDEL_BODY_W = _MANDEL_PAD + _MANDEL_CANVAS_W + _MANDEL_PAD
_MANDEL_BODY_H = (
    _MANDEL_PAD + _MANDEL_CANVAS_H
    + _MANDEL_CTRL_GAP + _MANDEL_CTRL_H
    + _MANDEL_STATUS_GAP + _MANDEL_STATUS_H
    + _MANDEL_PAD
)
_MANDEL_WINDOW_SIZE = (_MANDEL_BODY_W, _MANDEL_TITLEBAR_H + _MANDEL_BODY_H)
# ---------------------------------------------------------------------------

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

_MANDEL_SPLIT_CANVAS_SPECS = (
    ("can1", 32),
    ("can2", 32),
    ("can3", 32),
    ("can4", 32),
)
_MANDEL_SPLIT_CANVAS_KEYS = tuple(canvas_key for canvas_key, _ in _MANDEL_SPLIT_CANVAS_SPECS)
_MANDEL_ONE_SPLIT_TASK_IDS = ("1", "2", "3", "4")
_MANDEL_TASK_BUTTON_SPECS = (
    ("mandel_iter", "Iterative", "launch_iterative", "round", "Run Mandelbrot iterative"),
    ("mandel_recur", "Recursive", "launch_recursive", "round", "Run Mandelbrot recursive"),
    ("mandel_one_split", "1M 4Tasks", "launch_one_split", "round", "Run Mandelbrot one canvas split"),
    ("mandel_four_split", "4M 4Tasks", "launch_four_split", "round", "Run Mandelbrot four canvases split"),
)
_MANDEL_PRIMARY_CANVAS_SPEC = {
    "control_id": "mandel_canvas",
    "max_events": 128,
}
_MANDEL_RESET_BUTTON_SPEC = {
    "control_id": "mandel_reset",
    "label": "Reset",
    "style": "angle",
    "slot_index": 0,
    "accessibility_role": "button",
    "accessibility_label": "Clear Mandelbrot surfaces",
}
_MANDEL_STATUS_LABEL_SPEC = {
    "control_id": "mandel_status",
}
_MANDEL_LAUNCH_MODE_SPECS = {
    "iterative": {
        "busy_profile": "iterative",
        "split_canvas": False,
        "running_mode": "running iterative",
        "event_kind": MANDEL_KIND_RUNNING_ITERATIVE,
    },
    "recursive": {
        "busy_profile": "default",
        "split_canvas": False,
        "running_mode": "running recursive",
        "event_kind": MANDEL_KIND_RUNNING_RECURSIVE,
    },
    "one_split": {
        "busy_profile": "default",
        "split_canvas": False,
        "running_mode": "running 1M 4Tasks",
        "event_kind": MANDEL_KIND_RUNNING_ONE_SPLIT,
    },
    "four_split": {
        "busy_profile": "default",
        "split_canvas": True,
        "running_mode": "running 4M 4Tasks",
        "event_kind": MANDEL_KIND_RUNNING_FOUR_SPLIT,
    },
}
_MANDEL_TASK_CANVAS_KEY_BY_TASK_ID = {
    "iter": "primary",
    "recu": "primary",
    "1": "primary",
    "2": "primary",
    "3": "primary",
    "4": "primary",
    "can1": "can1",
    "can2": "can2",
    "can3": "can3",
    "can4": "can4",
}

_MANDEL_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="mandelbrot_window",
    title="Mandelbrot Demo",
    size=_MANDEL_WINDOW_SIZE,
    anchor="top_left",
    margin=(28, 92),
    use_frame_backdrop=True,
)

_MANDEL_LOGIC_BINDINGS = (
    LogicBindingSpec(alias="primary", provider_name=_MANDEL_LOGIC_PRIMARY),
    LogicBindingSpec(alias="can1", provider_name=_MANDEL_LOGIC_CAN1),
    LogicBindingSpec(alias="can2", provider_name=_MANDEL_LOGIC_CAN2),
    LogicBindingSpec(alias="can3", provider_name=_MANDEL_LOGIC_CAN3),
    LogicBindingSpec(alias="can4", provider_name=_MANDEL_LOGIC_CAN4),
)

_MANDEL_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    companion_providers=(
        lambda: MandelbrotLogicFeature(_MANDEL_LOGIC_PRIMARY),
        lambda: MandelbrotLogicFeature(_MANDEL_LOGIC_CAN1),
        lambda: MandelbrotLogicFeature(_MANDEL_LOGIC_CAN2),
        lambda: MandelbrotLogicFeature(_MANDEL_LOGIC_CAN3),
        lambda: MandelbrotLogicFeature(_MANDEL_LOGIC_CAN4),
    ),
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host),
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)
class MandelbrotFeature(RoutedFeature):
    """Build and run the Mandelbrot demo windows, tasks, and status plumbing."""


    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    LOGIC_ALIAS_PRIMARY = "primary"
    LOGIC_ALIAS_CAN1 = "can1"
    LOGIC_ALIAS_CAN2 = "can2"
    LOGIC_ALIAS_CAN3 = "can3"
    LOGIC_ALIAS_CAN4 = "can4"
    DEFAULT_MESSAGE_DISPATCH_LIMIT = 512
    BUSY_STARTUP_MESSAGE_DISPATCH_LIMIT = 32
    BUSY_MESSAGE_DISPATCH_LIMIT = 96
    DEFAULT_MESSAGE_INGEST_LIMIT = 512
    BUSY_MESSAGE_INGEST_LIMIT = 96
    DEFAULT_MAX_QUEUED_MESSAGES_PER_TASK = 1024
    BUSY_MAX_QUEUED_MESSAGES_PER_TASK = 192
    BUSY_STARTUP_FRAMES = 6
    ITERATIVE_BUSY_STARTUP_MESSAGE_DISPATCH_LIMIT = 16
    ITERATIVE_BUSY_MESSAGE_DISPATCH_LIMIT = 72
    ITERATIVE_BUSY_MESSAGE_INGEST_LIMIT = 64
    ITERATIVE_BUSY_MAX_QUEUED_MESSAGES_PER_TASK = 128
    ITERATIVE_BUSY_STARTUP_FRAMES = 10




    def __init__(self) -> None:
        super().__init__("mandelbrot", scene_name="main")
        self.task_ids = set()
        self.task_id_pool = ("iter", "recu", "1", "2", "3", "4", "can1", "can2", "can3", "can4")
        self.running_mode = None
        self.scheduler = None
        self.demo = None  # Will be set during build_window
        self.window = None
        self.menu_bar = None
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
        self._busy_startup_frames_remaining = 0
        self._busy_profile_name = "default"
        self._task_logic_alias = {
            "can1": self.LOGIC_ALIAS_CAN1,
            "can2": self.LOGIC_ALIAS_CAN2,
            "can3": self.LOGIC_ALIAS_CAN3,
            "can4": self.LOGIC_ALIAS_CAN4,
        }
        self._runtime_spec: RoutedRuntimeSpec | None = None

    def on_register(self, host) -> None:
        """Auto-register all companion logic features when this feature is registered."""
        register_routed_feature_companions(self, host, _MANDEL_LIFECYCLE_SPEC)

    def build(self, host) -> None:
        """Build the Mandelbrot feature UI using the new presenter/controller pattern."""
        from .mandelbrot_presenter import MandelbrotPresenter

        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=MandelbrotPresenter,
            spec=_MANDEL_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        """Bind scheduler, keyboard shortcuts, and event-bus subscription hooks."""
        self.demo = host  # Store host reference
        self.scheduler = bind_routed_feature_lifecycle(self, host, _MANDEL_LIFECYCLE_SPEC)
        self._set_busy_dispatch_mode(False)
        self.status_bus_ready = True

    def _build_runtime_spec(self, host) -> RoutedRuntimeSpec:
        return RoutedRuntimeSpec(
            scene_name="main",
            logic_bindings=_MANDEL_LOGIC_BINDINGS,
            event_subscriptions=(
                EventSubscriptionSpec(
                    attr_name="status_subscription",
                    topic=self.status_topic,
                    handler=lambda payload: self.on_status_event(host, payload),
                    scope=self.status_scope,
                ),
            ),
        )

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
        shutdown_routed_feature_lifecycle(self, host, _MANDEL_LIFECYCLE_SPEC)
        self.status_bus_ready = False
        self._busy_profile_name = "default"
        self._set_busy_dispatch_mode(False)

    def _set_busy_profile(self, profile_name: str) -> None:
        if str(profile_name) == "iterative":
            self._busy_profile_name = "iterative"
        else:
            self._busy_profile_name = "default"

    def _active_busy_scheduler_profile(self) -> tuple[int, int, int, int, int]:
        if self._busy_profile_name == "iterative":
            return (
                self.ITERATIVE_BUSY_STARTUP_MESSAGE_DISPATCH_LIMIT,
                self.ITERATIVE_BUSY_MESSAGE_DISPATCH_LIMIT,
                self.ITERATIVE_BUSY_MESSAGE_INGEST_LIMIT,
                self.ITERATIVE_BUSY_MAX_QUEUED_MESSAGES_PER_TASK,
                self.ITERATIVE_BUSY_STARTUP_FRAMES,
            )
        return (
            self.BUSY_STARTUP_MESSAGE_DISPATCH_LIMIT,
            self.BUSY_MESSAGE_DISPATCH_LIMIT,
            self.BUSY_MESSAGE_INGEST_LIMIT,
            self.BUSY_MAX_QUEUED_MESSAGES_PER_TASK,
            self.BUSY_STARTUP_FRAMES,
        )

    def _set_busy_dispatch_mode(self, busy: bool) -> None:
        scheduler = self.scheduler
        if scheduler is None:
            return
        target_busy = bool(busy)
        if target_busy == self._busy_dispatch_mode:
            return
        if target_busy:
            startup_dispatch_limit, _steady_dispatch_limit, busy_ingest_limit, busy_max_queued_messages, startup_frames = self._active_busy_scheduler_profile()
            self._busy_startup_frames_remaining = startup_frames
            self._configure_scheduler_limits(
                scheduler,
                dispatch_limit=startup_dispatch_limit,
                ingest_limit=busy_ingest_limit,
                max_queued_messages_per_task=busy_max_queued_messages,
            )
        else:
            self._busy_startup_frames_remaining = 0
            self._busy_profile_name = "default"
            self._configure_scheduler_limits(
                scheduler,
                dispatch_limit=self.DEFAULT_MESSAGE_DISPATCH_LIMIT,
                ingest_limit=self.DEFAULT_MESSAGE_INGEST_LIMIT,
                max_queued_messages_per_task=self.DEFAULT_MAX_QUEUED_MESSAGES_PER_TASK,
            )
        self._busy_dispatch_mode = target_busy

    @staticmethod
    def _configure_scheduler_limits(
        scheduler,
        *,
        dispatch_limit: int,
        ingest_limit: int,
        max_queued_messages_per_task: int,
    ) -> None:
        # Test doubles for scheduler may expose only a subset of configuration APIs.
        if hasattr(scheduler, "set_message_dispatch_limit"):
            scheduler.set_message_dispatch_limit(dispatch_limit)
        if hasattr(scheduler, "set_message_ingest_limit"):
            scheduler.set_message_ingest_limit(ingest_limit)
        if hasattr(scheduler, "set_max_queued_messages_per_task"):
            scheduler.set_max_queued_messages_per_task(max_queued_messages_per_task)

    def _tick_busy_scheduler_startup(self) -> None:
        scheduler = self.scheduler
        if scheduler is None:
            return
        if not self._busy_dispatch_mode:
            return
        if self._busy_startup_frames_remaining <= 0:
            return
        self._busy_startup_frames_remaining -= 1
        _startup_dispatch_limit, steady_dispatch_limit, _busy_ingest_limit, _busy_max_queued_messages, _startup_frames = self._active_busy_scheduler_profile()
        if self._busy_startup_frames_remaining == 0 and hasattr(scheduler, "set_message_dispatch_limit"):
            scheduler.set_message_dispatch_limit(steady_dispatch_limit)

    def _get_scheduler(self, host):
        """Resolve and memoize the scene scheduler used by render tasks."""
        scheduler = ensure_scene_scheduler(self, host, scene_name="main")
        if scheduler is None:
            raise AttributeError("Mandelbrot scheduler is not available")
        self.scheduler = scheduler
        return scheduler

    def on_update(self, _host) -> None:
        """Publish post-frame status updates for Mandelbrot state."""
        self.update_events()



    def _set_status_text(self, text: str) -> None:
        """Set canonical status text and keep status label in sync."""
        normalized = str(text)
        self.status_text = normalized
        self.status_label.text = normalized


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
        if not self.task_ids:
            return
        mode = self.running_mode if self.running_mode is not None else "running"
        task_count = len(self.task_ids)
        task_word = "task" if task_count == 1 else "tasks"
        detail = f"Mandelbrot: {mode} ({task_count} {task_word})"
        if self.status_text == detail:
            return
        self.publish_event(MANDEL_KIND_STATUS, detail)


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
        """Clear all Mandelbrot canvases and the padded content area to the theme medium background color."""
        # Fill the padded content area (including gaps between canvases)
        if hasattr(self.window, "content_rect"):
            padded_content_rect = inset_rect(self.window.content_rect(), padding_x=0, padding_y=0)
            surface = self.window.surface if hasattr(self.window, "surface") else None
            if surface is not None:
                import pygame
                pygame.draw.rect(surface, host.app.theme.medium, padded_content_rect)

        self.primary_canvas.canvas.fill(host.app.theme.medium)
        for canvas_key in _MANDEL_SPLIT_CANVAS_KEYS:
            canvas = self.split_canvases.get(canvas_key)
            if canvas is not None:
                canvas.canvas.fill(host.app.theme.medium)

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
        self._set_split_canvas_visibility(False)
        self.clear_surfaces(host)

    def prepare_single_canvas_run(self, host) -> None:
        """Prepare UI for single-canvas rendering modes."""
        self.set_task_buttons_disabled(host, True)
        self.show_single_canvas(host)

    def prepare_split_canvas_run(self, host) -> None:
        """Prepare UI for split-canvas rendering mode."""
        self.set_task_buttons_disabled(host, True)
        self.primary_canvas.visible = False
        self._set_split_canvas_visibility(True)
        self.clear_surfaces(host)

    def _set_split_canvas_visibility(self, visible: bool) -> None:
        state = bool(visible)
        for canvas_key in _MANDEL_SPLIT_CANVAS_KEYS:
            canvas = self.split_canvases.get(canvas_key)
            if canvas is not None:
                canvas.visible = state

    def canvas_for_task(self, host, task_id: str):
        """Resolve target canvas surface for a given scheduler task id."""
        canvas_key = _MANDEL_TASK_CANVAS_KEY_BY_TASK_ID.get(str(task_id))
        if canvas_key == "primary":
            return self.primary_canvas.canvas
        if canvas_key is None:
            return None
        split_canvas = self.split_canvases.get(canvas_key)
        if split_canvas is None:
            return None
        return split_canvas.canvas

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
        self._busy_profile_name = "default"
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

    def _begin_launch(self, host, *, busy_profile: str, split_canvas: bool):
        """Run shared launch preflight and return scheduler when launch may proceed."""
        scheduler = self._get_scheduler(host)
        if scheduler.tasks_busy_match_any(*self.task_id_pool):
            return None
        self._set_busy_profile(busy_profile)
        self._set_busy_dispatch_mode(True)
        if split_canvas:
            self.prepare_split_canvas_run(host)
        else:
            self.prepare_single_canvas_run(host)
        return scheduler

    def _finalize_launch(self, *, running_mode: str, event_kind: str) -> None:
        """Apply shared launch completion state and publish running status."""
        self.running_mode = str(running_mode)
        self.publish_event(str(event_kind))
        self.publish_running_status()

    def _launch_mode(self, host, mode_key: str) -> None:
        """Launch one Mandelbrot mode from declarative metadata and queue strategy."""
        spec = _MANDEL_LAUNCH_MODE_SPECS.get(str(mode_key))
        if spec is None:
            raise ValueError(f"Unsupported Mandelbrot launch mode: {mode_key}")
        scheduler = self._begin_launch(
            host,
            busy_profile=str(spec["busy_profile"]),
            split_canvas=bool(spec["split_canvas"]),
        )
        if scheduler is None:
            return
        queue_builders = {
            "iterative": self._queue_iterative_mode,
            "recursive": self._queue_recursive_mode,
            "one_split": self._queue_one_split_mode,
            "four_split": self._queue_four_split_mode,
        }
        queue_builder = queue_builders[str(mode_key)]
        queue_builder(host, scheduler)
        self._finalize_launch(
            running_mode=str(spec["running_mode"]),
            event_kind=str(spec["event_kind"]),
        )

    def _queue_iterative_mode(self, host, scheduler) -> None:
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        scheduler.add_task(
            "iter",
            lambda task_id, params: self.iterative_task(host, task_id, params),
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=self.make_progress_handler(host, "iter"),
        )
        self.task_ids.add("iter")

    def _queue_recursive_mode(self, host, _scheduler) -> None:
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

    def _queue_one_split_mode(self, host, _scheduler) -> None:
        width, height = self.primary_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        left_w, top_h = width // 2, height // 2
        right_w, bottom_h = width - left_w, height - top_h
        quadrants = (
            Rect(0, 0, left_w, top_h),
            Rect(left_w, 0, right_w, top_h),
            Rect(0, top_h, left_w, bottom_h),
            Rect(left_w, top_h, right_w, bottom_h),
        )
        for task_id, rect in zip(_MANDEL_ONE_SPLIT_TASK_IDS, quadrants):
            self.queue_recursive_task(
                host,
                task_id,
                rect,
                (width, height),
                center,
                scale,
                logic_alias=self.LOGIC_ALIAS_PRIMARY,
            )

    def _queue_four_split_mode(self, host, _scheduler) -> None:
        first_split_canvas = self.split_canvases.get(_MANDEL_SPLIT_CANVAS_KEYS[0])
        if first_split_canvas is None:
            return
        width, height = first_split_canvas.canvas.get_size()
        center, scale = self.mandel_viewport(host, width, height)
        for task_id in _MANDEL_SPLIT_CANVAS_KEYS:
            self.queue_recursive_task(
                host,
                task_id,
                Rect(0, 0, width, height),
                (width, height),
                center,
                scale,
                logic_alias=self._task_logic_alias[task_id],
            )

    def launch_iterative(self, host) -> None:
        """Launch iterative render mode when no Mandelbrot task is already running."""
        self._launch_mode(host, "iterative")

    def launch_recursive(self, host) -> None:
        """Launch single-task recursive render mode."""
        self._launch_mode(host, "recursive")

    def launch_one_split(self, host) -> None:
        """Launch four recursive tasks that render quadrants into one canvas."""
        self._launch_mode(host, "one_split")

    def launch_four_split(self, host) -> None:
        """Launch four recursive tasks across four independent split canvases."""
        self._launch_mode(host, "four_split")


    def update_events(self) -> None:
        """Drain scheduler event streams and synchronize UI/task status state. Also sends a toast when a Mandelbrot task completes."""
        demo = self.demo
        if demo is None:
            return
        scheduler = self._get_scheduler(demo)
        finished = scheduler.get_finished_events()
        failed = scheduler.get_failed_events()
        failed_details = []

        # Send a toast for each completed task
        for event in finished:
            if event.task_id in self.task_ids:
                # Send toast notification
                demo.app.events.publish(
                    "toast",
                    {
                        "message": f"Mandelbrot task '{event.task_id}' completed.",
                        "title": "Mandelbrot",
                        "severity": "SUCCESS",
                    },
                )
                self.task_ids.remove(event.task_id)
                scheduler.pop_result(event.task_id, None)

        for event in failed:
            if event.task_id in self.task_ids:
                self.task_ids.remove(event.task_id)
                failed_details.append((str(event.task_id), str(event.error)))

        if failed_details:
            failed_details.sort(key=lambda item: (item[0], item[1]))
            # Simple summary: just join all failures for demo simplicity
            summary = "; ".join(f"{tid}: {err}" for tid, err in failed_details)
            self.publish_event(MANDEL_KIND_FAILED, summary)

        busy = scheduler.tasks_busy_match_any(*self.task_id_pool)
        self._set_busy_dispatch_mode(busy)
        if busy:
            self._tick_busy_scheduler_startup()
        self.set_task_buttons_disabled(demo, busy)
        if busy:
            self.publish_running_status()
        scheduler.clear_events()
        if not busy and self.status_text.startswith("Mandelbrot: running"):
            self.running_mode = None
            self.publish_event(MANDEL_KIND_COMPLETE)
