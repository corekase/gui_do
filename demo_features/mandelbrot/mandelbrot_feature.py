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
    ButtonControl,
    CanvasControl,
    centered_horizontal_strip_layout,
    inset_rect,
    LabelControl,
    partition_rects,
    RoutedFeature,
    WindowControl,
)
from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    bind_routed_feature_lifecycle,
    create_feature_presented_window,
    ensure_scene_scheduler,
    EventSubscriptionSpec,
    LogicBindingSpec,
    register_routed_feature_companions,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    shutdown_routed_feature_lifecycle,
)

from .mandelbrot_logic import MandelbrotLogicFeature
from .mandelbrot_status_event import MandelStatusEvent
from .mandelbrot_specs import (
    _BTN_H, _BTN_GAP, _CANVAS_H, _CANVAS_W, _NUM_BTNS, _PAD, _ROW_PAD, _STATUS_H, _WINDOW_SIZE,
    MANDEL_STATUS_TOPIC, MANDEL_STATUS_SCOPE,
    MANDEL_KIND_CLEARED, MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED,
    MANDEL_KIND_IDLE, MANDEL_KIND_RUNNING_FOUR_SPLIT, MANDEL_KIND_RUNNING_ITERATIVE,
    MANDEL_KIND_RUNNING_ONE_SPLIT, MANDEL_KIND_RUNNING_RECURSIVE, MANDEL_KIND_STATUS,
    _STATUS_TEXT,
)

# ---------------------------------------------------------------------------
# Logic provider names and canvas split keys
# ---------------------------------------------------------------------------
_LOGIC_PRIMARY = "mandelbrot_logic_primary"
_LOGIC_SPLITS = (
    "mandelbrot_logic_can1",
    "mandelbrot_logic_can2",
    "mandelbrot_logic_can3",
    "mandelbrot_logic_can4",
)
_SPLIT_KEYS = ("can1", "can2", "can3", "can4")
_ALL_TASK_IDS = ("iter", "recu", "1", "2", "3", "4") + _SPLIT_KEYS

# ---------------------------------------------------------------------------
# Lifecycle and runtime specs (module-level singletons)
# ---------------------------------------------------------------------------
_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="mandelbrot_window",
    title="Mandelbrot",
    size=_WINDOW_SIZE,
    anchor="top_left",
    margin=(28, 92),
    use_frame_backdrop=True,
)

_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    companion_providers=(
        lambda: MandelbrotLogicFeature(_LOGIC_PRIMARY),
        lambda: MandelbrotLogicFeature(_LOGIC_SPLITS[0]),
        lambda: MandelbrotLogicFeature(_LOGIC_SPLITS[1]),
        lambda: MandelbrotLogicFeature(_LOGIC_SPLITS[2]),
        lambda: MandelbrotLogicFeature(_LOGIC_SPLITS[3]),
    ),
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host),
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)

_LOGIC_BINDINGS = (
    LogicBindingSpec(alias="primary", provider_name=_LOGIC_PRIMARY),
    LogicBindingSpec(alias="can1",    provider_name=_LOGIC_SPLITS[0]),
    LogicBindingSpec(alias="can2",    provider_name=_LOGIC_SPLITS[1]),
    LogicBindingSpec(alias="can3",    provider_name=_LOGIC_SPLITS[2]),
    LogicBindingSpec(alias="can4",    provider_name=_LOGIC_SPLITS[3]),
)


# ---------------------------------------------------------------------------
# Window presenter (private -- builds and wires all controls)
# ---------------------------------------------------------------------------
class _MandelbrotPresenter(WindowPresenter):
    """Constructs the Mandelbrot window controls and wires them to the feature."""

    def __init__(self, feature, host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        f = self.feature
        host = self.host
        area = inset_rect(self.window.content_rect(), padding_x=_PAD, padding_y=_PAD)

        # Primary canvas (full-size, used for iterative / recursive / one-split modes)
        canvas_rect = Rect(area.left, area.top, _CANVAS_W, _CANVAS_H)
        f.primary_canvas = self._add(CanvasControl("mandel_canvas", Rect(canvas_rect), max_events=128))

        # Four split canvases in a 2x2 grid (shown only for the 4M 4Tasks mode)
        f.split_canvases = {}
        for key, rect in zip(_SPLIT_KEYS, partition_rects(canvas_rect, rows=2, cols=2, gap=6)):
            canvas = CanvasControl(key, rect, max_events=32)
            canvas.visible = False
            self.add_control(canvas)
            f.split_canvases[key] = canvas

        # Button row: Reset | Iterative | Recursive | 1M 4Tasks | 4M 4Tasks
        btn_y = area.top + _CANVAS_H + 8
        slots = centered_horizontal_strip_layout(
            left=area.left + _ROW_PAD,
            width=_CANVAS_W - 2 * _ROW_PAD,
            y=btn_y,
            item_count=_NUM_BTNS,
            item_height=_BTN_H,
            spacing=_BTN_GAP,
        )
        f.reset_button = self._add(ButtonControl(
            "mandel_reset", slots[0], "Reset", lambda: f.clear(host), style="angle",
        ))
        f.reset_button.set_accessibility(role="button", label="Clear Mandelbrot surfaces")

        task_defs = (
            ("mandel_iter",       "Iterative",  f.launch_iterative,  "Run iterative"),
            ("mandel_recur",      "Recursive",  f.launch_recursive,  "Run recursive"),
            ("mandel_one_split",  "1M 4Tasks",  f.launch_one_split,  "Run 1-canvas 4-task split"),
            ("mandel_four_split", "4M 4Tasks",  f.launch_four_split, "Run 4-canvas 4-task split"),
        )
        f.task_buttons = tuple(
            self._make_task_btn(cid, label, method, tip, slot)
            for (cid, label, method, tip), slot in zip(task_defs, slots[1:])
        )

        # Status label
        status_y = btn_y + _BTN_H + 6
        f.status_label = self._add(LabelControl(
            "mandel_status",
            Rect(area.left, status_y, _CANVAS_W, _STATUS_H),
            f.status_text,
        ))

        f.window = self.window
        f.demo = host
        f.clear(host)
        self.window.visible = False

    def _add(self, control):
        self.add_control(control)
        return control

    def _make_task_btn(self, cid, label, method, tip, rect):
        btn = self._add(ButtonControl(cid, rect, label, lambda m=method: m(self.host), style="round"))
        btn.set_accessibility(role="button", label=tip)
        return btn


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

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_register(self, host) -> None:
        register_routed_feature_companions(self, host, _LIFECYCLE_SPEC)

    def build(self, host) -> None:
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_MandelbrotPresenter,
            spec=_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        self.demo = host
        self.scheduler = bind_routed_feature_lifecycle(self, host, _LIFECYCLE_SPEC)
        self._set_busy(False)

    def _build_runtime_spec(self, host) -> RoutedRuntimeSpec:
        return RoutedRuntimeSpec(
            scene_name="main",
            logic_bindings=_LOGIC_BINDINGS,
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
        self._set_busy(False)

    def on_update(self, _host) -> None:
        self._drain_scheduler_events()

    # ------------------------------------------------------------------
    # Busy-mode scheduler throttle
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        sched = self.scheduler
        if sched is None or bool(busy) == self._busy:
            return
        self._busy = bool(busy)
        limit = 48 if busy else 512
        if hasattr(sched, "set_message_dispatch_limit"):
            sched.set_message_dispatch_limit(limit)

    # ------------------------------------------------------------------
    # Canvas helpers
    # ------------------------------------------------------------------

    def _logic(self, alias: str):
        name = self.bound_logic_name(alias=alias)
        if name is None:
            return None
        provider = self._feature_manager.get(name)
        return provider if isinstance(provider, MandelbrotLogicFeature) else None

    def _col(self, k: int) -> tuple:
        logic = self._logic("primary")
        return logic.mandel_col(k) if logic else (0, 0, 0)

    def _viewport(self, width: int, height: int) -> tuple:
        logic = self._logic("primary")
        return logic.mandel_viewport(width, height) if logic else (0 + 0j, 1.0)

    def _canvas_for_task(self, task_id: str):
        if task_id in _SPLIT_KEYS:
            c = self.split_canvases.get(task_id)
            return c.canvas if c else None
        return self.primary_canvas.canvas if self.primary_canvas else None

    def _apply_result(self, task_id: str, payload) -> None:
        """Paint one scheduler message payload onto the target canvas."""
        canvas = self._canvas_for_task(task_id)
        if canvas is None:
            return
        cw, ch = canvas.get_size()

        if task_id == "iter":
            # Iterative payload: (y_row, [iteration_count, ...])
            y, row = payload
            if 0 <= y < ch:
                for x, v in enumerate(row):
                    if 0 <= x < cw:
                        canvas.set_at((x, y), self._col(v))
            return

        # Recursive payload: (x, y, w, h, values_or_scalar)
        x0, y0, w, h, values = payload
        if isinstance(values, int):
            rx, ry = max(0, x0), max(0, y0)
            rx1, ry1 = min(cw, x0 + w), min(ch, y0 + h)
            if rx1 > rx and ry1 > ry:
                canvas.fill(self._col(values), Rect(rx, ry, rx1 - rx, ry1 - ry))
            return

        idx = 0
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                if 0 <= yy < ch and 0 <= xx < cw:
                    canvas.set_at((xx, yy), self._col(values[idx]))
                idx += 1

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _publish_status(self, kind: str, detail: Optional[str] = None) -> None:
        """Update the status label and publish a status event to the event bus."""
        if kind == MANDEL_KIND_FAILED:
            text = f"Mandelbrot failed: {detail}" if detail else "Mandelbrot failed"
        elif kind == MANDEL_KIND_STATUS:
            text = detail or "Mandelbrot: idle"
        else:
            text = _STATUS_TEXT.get(kind, detail or f"Mandelbrot: {kind}")

        self.status_text = text
        if self.status_label is not None:
            self.status_label.text = text

        demo = self.demo
        if demo is not None:
            event = MandelStatusEvent(kind=kind, detail=detail)
            demo.app.events.publish(MANDEL_STATUS_TOPIC, event.to_payload(), scope=MANDEL_STATUS_SCOPE)

    def _on_status_event(self, payload) -> None:
        event = MandelStatusEvent.from_payload(payload)
        text = _STATUS_TEXT.get(event.kind, event.detail or f"Mandelbrot: {event.kind}")
        self.status_text = text
        if self.status_label is not None:
            self.status_label.text = text

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------

    def _get_scheduler(self, host):
        sched = ensure_scene_scheduler(self, host, scene_name="main")
        if sched is None:
            raise AttributeError("Mandelbrot scheduler not available")
        self.scheduler = sched
        return sched

    def _queue_task(self, host, task_id: str, logic_alias: str, runnable: str, params: dict) -> None:
        """Register one background task with the scheduler."""
        def run(tid, p):
            name = self.bound_logic_name(alias=logic_alias)
            if name is not None:
                host.app.run_feature_runnable(name, runnable, self._get_scheduler(host), str(tid), p)

        sched = self._get_scheduler(host)
        sched.add_task(
            task_id,
            run,
            parameters=params,
            message_method=lambda payload, tid=task_id: self._apply_result(tid, payload),
        )
        self.task_ids.add(task_id)

    def _set_buttons_enabled(self, host, enabled: bool) -> None:
        for btn in self.task_buttons:
            btn.enabled = enabled
        if not enabled:
            focused = host.app.focus.focused_node
            if focused in self.task_buttons:
                reset = self.reset_button
                if reset and reset.visible and reset.enabled and reset.accepts_focus():
                    host.app.focus.set_focus(reset)
                else:
                    host.app.focus.revalidate_focus(host.app.scene)

    def _show_primary(self) -> None:
        if self.primary_canvas:
            self.primary_canvas.visible = True
        for c in self.split_canvases.values():
            c.visible = False

    def _show_split(self) -> None:
        if self.primary_canvas:
            self.primary_canvas.visible = False
        for c in self.split_canvases.values():
            c.visible = True

    def _clear_canvases(self, host) -> None:
        bg = host.app.theme.medium
        if self.primary_canvas:
            self.primary_canvas.canvas.fill(bg)
        for c in self.split_canvases.values():
            c.canvas.fill(bg)

    def _drain_scheduler_events(self) -> None:
        """Process finished/failed task events; update busy state and status."""
        demo = self.demo
        if demo is None:
            return
        sched = self._get_scheduler(demo)

        for event in sched.get_finished_events():
            if event.task_id in self.task_ids:
                demo.app.events.publish("toast", {
                    "message": f"Mandelbrot task '{event.task_id}' completed.",
                    "title": "Mandelbrot",
                    "severity": "SUCCESS",
                })
                self.task_ids.discard(event.task_id)
                sched.pop_result(event.task_id, None)

        failed = []
        for event in sched.get_failed_events():
            if event.task_id in self.task_ids:
                self.task_ids.discard(event.task_id)
                failed.append(f"{event.task_id}: {event.error}")
        if failed:
            self._publish_status(MANDEL_KIND_FAILED, "; ".join(sorted(failed)))

        busy = sched.tasks_busy_match_any(*_ALL_TASK_IDS)
        self._set_busy(busy)
        self._set_buttons_enabled(demo, not busy)

        if busy:
            n = len(self.task_ids)
            word = "task" if n == 1 else "tasks"
            status_text = f"Mandelbrot: running ({n} {word})"
            if self.status_text != status_text:
                self._publish_status(MANDEL_KIND_STATUS, status_text)
        elif self.status_text.startswith("Mandelbrot: running"):
            self._publish_status(MANDEL_KIND_COMPLETE)

        sched.clear_events()

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def clear(self, host) -> None:
        """Cancel all running tasks, clear canvases, and reset the UI."""
        sched = self._get_scheduler(host)
        sched.remove_tasks(*_ALL_TASK_IDS)
        self.task_ids.clear()
        self._set_busy(False)
        self._show_primary()
        self._clear_canvases(host)
        self._set_buttons_enabled(host, True)
        self._publish_status(MANDEL_KIND_CLEARED)

    def _begin_launch(self, host, *, split: bool = False):
        """Shared launch preflight.  Returns the scheduler, or None if already busy."""
        sched = self._get_scheduler(host)
        if sched.tasks_busy_match_any(*_ALL_TASK_IDS):
            return None
        self._set_busy(True)
        self._set_buttons_enabled(host, False)
        if split:
            self._show_split()
        else:
            self._show_primary()
        self._clear_canvases(host)
        return sched

    def launch_iterative(self, host) -> None:
        """Row-by-row scanline render: one task on the primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        self._queue_task(host, "iter", "primary", "iterative_task",
                         {"size": (w, h), "center": center, "scale": scale})
        self._publish_status(MANDEL_KIND_RUNNING_ITERATIVE)

    def launch_recursive(self, host) -> None:
        """Recursive quad-subdivide render: one task on the primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        self._queue_task(host, "recu", "primary", "recursive_task",
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
            ("1", Rect(0,   0,  lw,      th)),
            ("2", Rect(lw,  0,  w - lw,  th)),
            ("3", Rect(0,   th, lw,      h - th)),
            ("4", Rect(lw,  th, w - lw,  h - th)),
        )
        for tid, rect in quadrants:
            self._queue_task(host, tid, "primary", "recursive_task",
                             {"size": (w, h), "center": center, "scale": scale, "rect": Rect(rect)})
        self._publish_status(MANDEL_KIND_RUNNING_ONE_SPLIT)

    def launch_four_split(self, host) -> None:
        """Four independent tasks, each with its own canvas and logic provider."""
        if self._begin_launch(host, split=True) is None:
            return
        first = self.split_canvases.get(_SPLIT_KEYS[0])
        if first is None:
            return
        w, h = first.canvas.get_size()
        center, scale = self._viewport(w, h)
        for key in _SPLIT_KEYS:
            self._queue_task(host, key, key, "recursive_task",
                             {"size": (w, h), "center": center, "scale": scale, "rect": Rect(0, 0, w, h)})
        self._publish_status(MANDEL_KIND_RUNNING_FOUR_SPLIT)


__all__ = ["MandelbrotFeature"]
