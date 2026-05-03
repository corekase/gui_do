"""Mandelbrot feature part extracted from the gui_do demo entrypoint."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

import pygame
from dataclasses import dataclass
from typing import Optional, Tuple

from pygame import Rect
from gui_do import (
    ButtonControl,
    CanvasControl,
    centered_horizontal_strip_layout,
    inset_rect,
    LabelControl,
    LogicFeature,
    RoutedFeature,
    WindowControl,
)
from gui_do.controls.chrome.window_presenter import WindowPresenter
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
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_MandelbrotWindowPresenter,
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


class _MandelbrotWindowPresenter(WindowPresenter):
    """Window presenter for the Mandelbrot demo window."""

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
        padded = inset_rect(content_rect, padding_x=_MANDEL_PAD, padding_y=_MANDEL_PAD)

        canvas_area = Rect(padded.left, padded.top, _MANDEL_CANVAS_W, _MANDEL_CANVAS_H)

        self.primary_canvas = self._add_control(
            CanvasControl(
                str(_MANDEL_PRIMARY_CANVAS_SPEC["control_id"]),
                Rect(canvas_area),
                max_events=int(_MANDEL_PRIMARY_CANVAS_SPEC["max_events"]),
            )
        )
        self.feature.primary_canvas = self.primary_canvas

        self.split_canvases = self._build_split_canvases(canvas_area, partition_rects)
        self._register_split_canvases(self.split_canvases)
        self.feature.split_canvases = self.split_canvases

        controls_y = padded.top + _MANDEL_CANVAS_H + _MANDEL_CTRL_GAP
        slots = centered_horizontal_strip_layout(
            left=padded.left + _MANDEL_ROW_STRIP_PAD,
            width=max(1, _MANDEL_CANVAS_W - 2 * _MANDEL_ROW_STRIP_PAD),
            y=controls_y, item_count=_MANDEL_BTN_COUNT, item_height=_MANDEL_CTRL_H, spacing=_MANDEL_BTN_SPACING,
        )
        reset_slot = slots[int(_MANDEL_RESET_BUTTON_SPEC["slot_index"])]
        self.reset_button = self._add_button_control(
            str(_MANDEL_RESET_BUTTON_SPEC["control_id"]),
            reset_slot,
            str(_MANDEL_RESET_BUTTON_SPEC["label"]),
            lambda: self.feature.clear(self.host),
            style=str(_MANDEL_RESET_BUTTON_SPEC["style"]),
        )
        self.reset_button.set_accessibility(
            role=str(_MANDEL_RESET_BUTTON_SPEC["accessibility_role"]),
            label=str(_MANDEL_RESET_BUTTON_SPEC["accessibility_label"]),
        )
        self.feature.reset_button = self.reset_button

        task_buttons = self._build_task_buttons(slots[1:])

        (
            self.mandel_iter_button,
            self.mandel_recur_button,
            self.mandel_one_split_button,
            self.mandel_four_split_button,
        ) = tuple(task_buttons)
        self.feature.task_buttons = tuple(task_buttons)

        status_y = controls_y + _MANDEL_CTRL_H + _MANDEL_STATUS_GAP
        self.status_label = self._add_label_control(
            str(_MANDEL_STATUS_LABEL_SPEC["control_id"]),
            Rect(padded.left, status_y, _MANDEL_CANVAS_W, _MANDEL_STATUS_H),
            self.feature.status_text,
        )
        self.feature.status_label = self.status_label

        self.feature.demo = self.host
        self.feature.window = self.window
        self.feature.menu_bar = None
        self.feature.set_task_buttons_disabled(self.host, False)
        self.feature.clear(self.host)
        self.window.visible = False

    def _build_split_canvases(self, canvas_area: Rect, partition_rects):
        """Build the four split Mandelbrot canvases mapped by declarative keys."""
        canvas_rects = partition_rects(canvas_area, rows=2, cols=2, gap=6)
        return {
            canvas_key: CanvasControl(canvas_key, canvas_rects[index], max_events=max_events)
            for index, (canvas_key, max_events) in enumerate(_MANDEL_SPLIT_CANVAS_SPECS)
        }

    def _register_split_canvases(self, split_canvases) -> None:
        """Register split canvases as hidden controls until split mode is activated."""
        for canvas in split_canvases.values():
            canvas.visible = False
            self.add_control(canvas)

    def _add_control(self, control):
        """Add a presenter-managed control and return it."""
        self.add_control(control)
        return control

    def _add_button_control(self, control_id: str, rect: Rect, text: str, on_click, *, style: str):
        """Create and register a ButtonControl in one call."""
        return self._add_control(ButtonControl(control_id, Rect(rect), text, on_click, style=style))

    def _add_label_control(self, control_id: str, rect: Rect, text: str):
        """Create and register a LabelControl in one call."""
        return self._add_control(LabelControl(control_id, Rect(rect), text))

    def _build_task_buttons(self, task_slots):
        """Build task launch buttons from declarative specs."""
        task_buttons = []
        for slot_rect, (control_id, label, launch_method_name, style, accessibility_label) in zip(
            task_slots,
            _MANDEL_TASK_BUTTON_SPECS,
        ):
            launch_method = getattr(self.feature, launch_method_name)
            button = self._add_button_control(
                control_id,
                slot_rect,
                label,
                lambda _method=launch_method: _method(self.host),
                style=style,
            )
            button.set_accessibility(role="button", label=accessibility_label)
            task_buttons.append(button)
        return tuple(task_buttons)
