"""Mandelbrot demo feature.

Illustrates async task scheduling by rendering the Mandelbrot set with four strategies:

  Iterative   – one task, row-by-row scanline pass on the primary canvas.
  Recursive   – one task, recursive quad-subdivision on the primary canvas.
  1M 4Tasks   – four tasks each rendering a quadrant of the primary canvas.
  4M 4Tasks   – four tasks, each with its own canvas and independent logic provider.

The window contains a large canvas area, a row of buttons (Reset + four launch
buttons), and a status label.  Background tasks paint pixels via scheduler messages;
the feature drains those messages each frame and updates the canvas in-place.
"""

from __future__ import annotations

from typing import Optional

from pygame import Rect

from gui_do import (
    RoutedFeature,
    WindowControl,
)
from gui_do.features.data_driven_runtime import (
    bind_routed_feature_lifecycle,
    create_feature_presented_window,
    EventSubscriptionSpec,
    register_routed_feature_companions,
    RoutedRuntimeSpec,
    shutdown_routed_feature_lifecycle,
)

from .mandelbrot_logic_feature import MandelbrotLogicFeature
from .mandelbrot_canvas_helpers import (
    apply_result as apply_result_helper,
    canvas_for_task as canvas_for_task_helper,
    color_for_iteration as color_for_iteration_helper,
    logic as logic_helper,
    mapped_colors_for_canvas as mapped_colors_for_canvas_helper,
    refresh_color_table as refresh_color_table_helper,
    viewport as viewport_helper,
)
from .mandelbrot_presenter import MandelbrotPresenter
from .mandelbrot_runtime_helpers import (
    begin_launch as begin_launch_helper,
    clear_canvases as clear_canvases_helper,
    drain_pending_launches as drain_pending_launches_helper,
    drain_scheduler_events as drain_scheduler_events_helper,
    get_scheduler as get_scheduler_helper,
    on_status_event as on_status_event_helper,
    publish_status as publish_status_helper,
    queue_staged_tasks as queue_staged_tasks_helper,
    set_busy as set_busy_helper,
    set_buttons_enabled as set_buttons_enabled_helper,
    show_primary as show_primary_helper,
    show_split as show_split_helper,
)
from .mandelbrot_scheduling_helpers import queue_task as queue_task_helper
from .mandelbrot_specs import (
    _CANVAS_H,
    _CANVAS_W,
    MANDEL_ALL_TASK_IDS,
    MANDEL_KIND_CLEARED, MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED,
    MANDEL_LOGIC_BINDINGS,
    MANDEL_SPLIT_KEYS,
    MANDEL_STATUS_SCOPE,
    MANDEL_STATUS_TOPIC,
    MANDEL_TASK_IDS_QUADRANTS,
    MANDEL_TASK_ID_ITERATIVE,
    MANDEL_TASK_ID_RECURSIVE,
    MANDEL_WINDOW_SPEC,
    MANDEL_KIND_RUNNING_FOUR_SPLIT, MANDEL_KIND_RUNNING_ITERATIVE,
    MANDEL_KIND_RUNNING_ONE_SPLIT, MANDEL_KIND_RUNNING_RECURSIVE,
    build_mandel_lifecycle_spec,
)

_LIFECYCLE_SPEC = build_mandel_lifecycle_spec(
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host)
)


# ---------------------------------------------------------------------------
# Feature
# ---------------------------------------------------------------------------
class MandelbrotFeature(RoutedFeature):
    """Mandelbrot demo: four rendering strategies driven by async scheduled tasks."""

    HOST_REQUIREMENTS = {
        "build":        ("app", "root"),
        "bind_runtime": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("mandelbrot", scene_name="main")
        self.task_ids: set[str] = set()
        self.scheduler = None
        self.demo = None
        self.window = None
        self.primary_canvas = None
        self.split_canvases: dict = {}
        self.reset_button = None
        self.task_buttons: tuple = ()
        self.status_label = None
        self.status_text = "Mandelbrot: idle"
        self._runtime_spec = None
        self._busy = False
        self._color_table: tuple[tuple[int, int, int], ...] = ((0, 0, 0),)
        self._mapped_color_tables: dict[int, tuple[int, ...]] = {}
        self._idle_dispatch_limit = None
        self._idle_ingest_limit = None
        self._pending_launches: list[tuple[str, str, str, dict]] = []
        self._launches_per_update = 1

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_register(self, host) -> None:
        register_routed_feature_companions(self, host, _LIFECYCLE_SPEC)

    def build(self, host) -> None:
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=MandelbrotPresenter,
            spec=MANDEL_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        self.demo = host
        self.scheduler = bind_routed_feature_lifecycle(self, host, _LIFECYCLE_SPEC)
        if self.scheduler is not None:
            if hasattr(self.scheduler, "get_message_dispatch_limit"):
                self._idle_dispatch_limit = self.scheduler.get_message_dispatch_limit()
            if hasattr(self.scheduler, "get_message_ingest_limit"):
                self._idle_ingest_limit = self.scheduler.get_message_ingest_limit()
        self._refresh_color_table()
        self._set_busy(False)

    def _build_runtime_spec(self, host) -> RoutedRuntimeSpec:
        return RoutedRuntimeSpec(
            scene_name="main",
            logic_bindings=MANDEL_LOGIC_BINDINGS,
            event_subscriptions=(
                EventSubscriptionSpec(
                    attr_name="status_subscription",
                    topic=MANDEL_STATUS_TOPIC,
                    handler=lambda payload: self._on_status_event(payload),
                    scope=MANDEL_STATUS_SCOPE,
                ),
            ),
        )

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, _LIFECYCLE_SPEC)
        self._pending_launches.clear()
        self._set_busy(False)

    def on_update(self, _host) -> None:
        self._drain_pending_launches()
        self._drain_scheduler_events()

    # ------------------------------------------------------------------
    # Busy-mode scheduler throttle
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        set_busy_helper(self, busy)

    # ------------------------------------------------------------------
    # Canvas helpers
    # ------------------------------------------------------------------

    def _logic(self, alias: str):
        return logic_helper(self, alias)

    def _refresh_color_table(self) -> None:
        refresh_color_table_helper(self)

    def _color_for_iteration(self, value: int) -> tuple[int, int, int]:
        return color_for_iteration_helper(self, value)

    def _mapped_colors_for_canvas(self, canvas) -> tuple[int, ...]:
        return mapped_colors_for_canvas_helper(self, canvas)

    def _viewport(self, width: int, height: int) -> tuple:
        return viewport_helper(self, width, height)

    def _canvas_for_task(self, task_id: str):
        return canvas_for_task_helper(self, task_id)

    def _apply_result(self, task_id: str, payload) -> None:
        apply_result_helper(self, task_id, payload)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _publish_status(self, kind: str, detail: Optional[str] = None) -> None:
        publish_status_helper(self, kind, detail)

    def _on_status_event(self, payload) -> None:
        on_status_event_helper(self, payload)

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------

    def _get_scheduler(self, host):
        return get_scheduler_helper(self, host)

    def _queue_task(self, host, task_id: str, logic_alias: str, runnable: str, params: dict) -> None:
        """Register one background task with the scheduler."""
        queue_task_helper(self, host, task_id, logic_alias, runnable, params)

    def _queue_staged_tasks(self, host, tasks: list[tuple[str, str, str, dict]]) -> None:
        queue_staged_tasks_helper(self, host, tasks)

    def _drain_pending_launches(self) -> None:
        drain_pending_launches_helper(self)

    def _set_buttons_enabled(self, host, enabled: bool) -> None:
        set_buttons_enabled_helper(self, host, enabled)

    def _show_primary(self) -> None:
        show_primary_helper(self)

    def _show_split(self) -> None:
        show_split_helper(self)

    def _clear_canvases(self, host) -> None:
        clear_canvases_helper(self, host)

    def _drain_scheduler_events(self) -> None:
        drain_scheduler_events_helper(self)

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def clear(self, host) -> None:
        """Cancel all running tasks, clear canvases, and reset the UI."""
        sched = self._get_scheduler(host)
        sched.remove_tasks(*MANDEL_ALL_TASK_IDS)
        self._pending_launches.clear()
        self.task_ids.clear()
        self._set_busy(False)
        self._show_primary()
        self._clear_canvases(host)
        self._set_buttons_enabled(host, True)
        self._publish_status(MANDEL_KIND_CLEARED)

    def _begin_launch(self, host, *, split: bool = False):
        return begin_launch_helper(self, host, split=split)

    def launch_iterative(self, host) -> None:
        """Row-by-row scanline render: one task on the primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        self._queue_task(host, MANDEL_TASK_ID_ITERATIVE, "primary", "iterative_task",
                         {"size": (w, h), "center": center, "scale": scale})
        self._publish_status(MANDEL_KIND_RUNNING_ITERATIVE)

    def launch_recursive(self, host) -> None:
        """Recursive quad-subdivide render: one task on the primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        self._queue_task(host, MANDEL_TASK_ID_RECURSIVE, "primary", "recursive_task",
                         {"size": (w, h), "center": center, "scale": scale, "rect": Rect(0, 0, w, h)})
        self._publish_status(MANDEL_KIND_RUNNING_RECURSIVE)

    def launch_one_split(self, host) -> None:
        """Four tasks each rendering a quadrant of the single primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        lw, th = w // 2, h // 2
        quadrants = (
            (MANDEL_TASK_IDS_QUADRANTS[0], Rect(0,   0,  lw,      th)),
            (MANDEL_TASK_IDS_QUADRANTS[1], Rect(lw,  0,  w - lw,  th)),
            (MANDEL_TASK_IDS_QUADRANTS[2], Rect(0,   th, lw,      h - th)),
            (MANDEL_TASK_IDS_QUADRANTS[3], Rect(lw,  th, w - lw,  h - th)),
        )
        tasks = [
            (
                tid,
                "primary",
                "recursive_task",
                {"size": (w, h), "center": center, "scale": scale, "rect": Rect(rect)},
            )
            for tid, rect in quadrants
        ]
        self._queue_staged_tasks(host, tasks)
        self._publish_status(MANDEL_KIND_RUNNING_ONE_SPLIT)

    def launch_four_split(self, host) -> None:
        """Four independent tasks, each with its own canvas and logic provider."""
        if self._begin_launch(host, split=True) is None:
            return
        first = self.split_canvases.get(MANDEL_SPLIT_KEYS[0])
        if first is None:
            return
        w, h = first.canvas.get_size()
        center, scale = self._viewport(w, h)
        tasks = [
            (
                key,
                key,
                "recursive_task",
                {"size": (w, h), "center": center, "scale": scale, "rect": Rect(0, 0, w, h)},
            )
            for key in MANDEL_SPLIT_KEYS
        ]
        self._queue_staged_tasks(host, tasks)
        self._publish_status(MANDEL_KIND_RUNNING_FOUR_SPLIT)


__all__ = ["MandelbrotFeature"]
