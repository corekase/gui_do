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

from pygame import PixelArray, Rect

from gui_do import (
    ButtonControl,
    CanvasControl,
    LabelControl,
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
_SPLIT_KEYS = ("Canvas 1", "Canvas 2", "Canvas 3", "Canvas 4")
_ALL_TASK_IDS = ("Iterative", "Recursive", "Task 1", "Task 2", "Task 3", "Task 4") + _SPLIT_KEYS
_TASK_ID_ITERATIVE  = _ALL_TASK_IDS[0]
_TASK_ID_RECURSIVE  = _ALL_TASK_IDS[1]
_TASK_IDS_QUADRANTS = _ALL_TASK_IDS[2:6]

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
    LogicBindingSpec(alias="primary",       provider_name=_LOGIC_PRIMARY),
    LogicBindingSpec(alias=_SPLIT_KEYS[0],  provider_name=_LOGIC_SPLITS[0]),
    LogicBindingSpec(alias=_SPLIT_KEYS[1],  provider_name=_LOGIC_SPLITS[1]),
    LogicBindingSpec(alias=_SPLIT_KEYS[2],  provider_name=_LOGIC_SPLITS[2]),
    LogicBindingSpec(alias=_SPLIT_KEYS[3],  provider_name=_LOGIC_SPLITS[3]),
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
        from gui_do import FlexLayout, GridLayout, GridPlacement
        f = self.feature
        host = self.host
        content_rect = self.window.content_rect()
        inner_rect = Rect(
            content_rect.left + _PAD,
            content_rect.top + _PAD,
            max(1, content_rect.width - _PAD * 2),
            max(1, content_rect.height - _PAD * 2),
        )

        # Primary canvas (full-size)
        primary_canvas = CanvasControl("mandel_canvas", Rect(0, 0, _CANVAS_W, _CANVAS_H), max_events=128)
        f.primary_canvas = self._add(primary_canvas)
        canvas_rect = Rect(inner_rect.left, inner_rect.top, _CANVAS_W, _CANVAS_H)
        primary_canvas.rect = Rect(canvas_rect)

        # Four split canvases in a 2x2 grid (hidden by default)
        split_gap = 6
        split_canvas_w = max(1, (_CANVAS_W - split_gap) // 2)
        split_canvas_h = max(1, (_CANVAS_H - split_gap) // 2)
        split_grid = GridLayout(
            row_tracks=[split_canvas_h, split_canvas_h],
            col_tracks=[split_canvas_w, split_canvas_w],
            gap=split_gap,
            padding=0,
        )
        f.split_canvases = {}
        for idx, key in enumerate(_SPLIT_KEYS):
            row = idx // 2
            col = idx % 2
            canvas = CanvasControl(key, Rect(0, 0, split_canvas_w, split_canvas_h), max_events=32)
            canvas.visible = False
            split_grid.place(canvas, GridPlacement(row=row, col=col))
            self.add_control(canvas)
            f.split_canvases[key] = canvas
        split_grid.apply(canvas_rect)

        # Button row using FlexLayout
        btn_row = FlexLayout(direction="row", gap=_BTN_GAP, padding=0)
        f.reset_button = self._add(ButtonControl(
            "mandel_reset", Rect(0, 0, 120, _BTN_H), "Reset", lambda: f.clear(host), style="angle",
        ))
        f.reset_button.set_accessibility(role="button", label="Clear Mandelbrot surfaces")
        btn_row.add(f.reset_button, grow=0)

        task_defs = (
            ("mandel_iter",       "Iterative",  f.launch_iterative,  "Run iterative"),
            ("mandel_recur",      "Recursive",  f.launch_recursive,  "Run recursive"),
            ("mandel_one_split",  "1M 4Tasks",  f.launch_one_split,  "Run 1-canvas 4-task split"),
            ("mandel_four_split", "4M 4Tasks",  f.launch_four_split, "Run 4-canvas 4-task split"),
        )
        f.task_buttons = tuple(
            self._make_task_btn(cid, label, method, tip, Rect(0, 0, 120, _BTN_H))
            for (cid, label, method, tip) in task_defs
        )
        for btn in f.task_buttons:
            btn_row.add(btn, grow=0)
        btn_row_rect = Rect(
            inner_rect.left + _ROW_PAD,
            canvas_rect.bottom + 9,
            max(1, _CANVAS_W - (_ROW_PAD * 2)),
            _BTN_H,
        )
        btn_row.apply(btn_row_rect)

        # Status label
        f.status_label = self._add(LabelControl(
            "mandel_status",
            Rect(0, 0, _CANVAS_W, _STATUS_H),
            f.status_text,
        ))
        f.status_label.rect = Rect(inner_rect.left, btn_row_rect.bottom + 9, _CANVAS_W, _STATUS_H)

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
            presenter_cls=_MandelbrotPresenter,
            spec=_WINDOW_SPEC,
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
        self._pending_launches.clear()
        self._set_busy(False)

    def on_update(self, _host) -> None:
        self._drain_pending_launches()
        self._drain_scheduler_events()

    # ------------------------------------------------------------------
    # Busy-mode scheduler throttle
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        sched = self.scheduler
        if sched is None or bool(busy) == self._busy:
            return
        self._busy = bool(busy)
        limit = self._idle_dispatch_limit
        ingest_limit = self._idle_ingest_limit
        if busy:
            if isinstance(limit, int):
                limit = max(48, min(limit, 192))
            if isinstance(ingest_limit, int):
                ingest_limit = max(256, min(ingest_limit, 1024))
        if hasattr(sched, "set_message_dispatch_limit"):
            sched.set_message_dispatch_limit(limit)
        if hasattr(sched, "set_message_ingest_limit"):
            sched.set_message_ingest_limit(ingest_limit)

    # ------------------------------------------------------------------
    # Canvas helpers
    # ------------------------------------------------------------------

    def _logic(self, alias: str):
        name = self.bound_logic_name(alias=alias)
        if name is None:
            return None
        provider = self._feature_manager.get(name)
        return provider if isinstance(provider, MandelbrotLogicFeature) else None

    def _refresh_color_table(self) -> None:
        logic = self._logic("primary")
        if logic is None:
            self._color_table = ((0, 0, 0),)
            self._mapped_color_tables.clear()
            return

        max_iter = max(1, int(logic.max_iter))
        palette = tuple(logic.mandel_cols)
        if not palette:
            self._color_table = tuple((0, 0, 0) for _ in range(max_iter))
            self._mapped_color_tables.clear()
            return

        terminal = max_iter - 1
        self._color_table = tuple((0, 0, 0) if i >= terminal else palette[i % len(palette)] for i in range(max_iter))
        self._mapped_color_tables.clear()

    def _color_for_iteration(self, value: int) -> tuple[int, int, int]:
        if value < 0:
            return self._color_table[0]
        if value >= len(self._color_table):
            return self._color_table[-1]
        return self._color_table[value]

    def _mapped_colors_for_canvas(self, canvas) -> tuple[int, ...]:
        key = id(canvas)
        cached = self._mapped_color_tables.get(key)
        if cached is not None:
            return cached
        mapped = tuple(canvas.map_rgb(color) for color in self._color_table)
        self._mapped_color_tables[key] = mapped
        return mapped

    def _col(self, k: int) -> tuple:
        return self._color_for_iteration(int(k))

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
        color_for_iteration = self._color_for_iteration
        mapped_colors = self._mapped_colors_for_canvas(canvas)
        mapped_count = len(mapped_colors)

        if task_id == _TASK_ID_ITERATIVE:
            # Iterative payloads:
            #   (y_row, [iteration_count, ...])
            #   (y_row, x_start, [iteration_count, ...])
            if len(payload) == 2:
                y, row = payload
                x_start = 0
            else:
                y, x_start, row = payload
            if 0 <= y < ch:
                draw_x = max(0, int(x_start))
                source_x = max(0, -int(x_start))
                limit = min(cw - draw_x, len(row) - source_x)
                if limit > 0:
                    mapped_row = []
                    append = mapped_row.append
                    default_color = mapped_colors[-1]
                    for x in range(source_x, source_x + limit):
                        value = int(row[x])
                        if 0 <= value < mapped_count:
                            append(mapped_colors[value])
                        else:
                            append(default_color)
                    pixels = PixelArray(canvas)
                    try:
                        pixels[draw_x:draw_x + limit, y] = mapped_row
                    finally:
                        del pixels
            return

        # Recursive payload: (x, y, w, h, values_or_scalar)
        x0, y0, w, h, values = payload
        if isinstance(values, int):
            rx, ry = max(0, x0), max(0, y0)
            rx1, ry1 = min(cw, x0 + w), min(ch, y0 + h)
            if rx1 > rx and ry1 > ry:
                canvas.fill(color_for_iteration(values), Rect(rx, ry, rx1 - rx, ry1 - ry))
            return

        x_start = max(0, x0)
        y_start = max(0, y0)
        x_end = min(cw, x0 + w)
        y_end = min(ch, y0 + h)
        if x_end <= x_start or y_end <= y_start:
            return

        row_span = max(0, w)
        if row_span <= 0:
            return

        pixels = PixelArray(canvas)
        try:
            default_color = mapped_colors[-1]
            for yy in range(y_start, y_end):
                idx = (yy - y0) * row_span + (x_start - x0)
                row_colors = []
                append = row_colors.append
                for _ in range(x_start, x_end):
                    value = int(values[idx])
                    if 0 <= value < mapped_count:
                        append(mapped_colors[value])
                    else:
                        append(default_color)
                    idx += 1
                pixels[x_start:x_end, yy] = row_colors
        finally:
            del pixels

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

    def _queue_staged_tasks(self, host, tasks: list[tuple[str, str, str, dict]]) -> None:
        if not tasks:
            return
        first_task = tasks[0]
        self._queue_task(host, *first_task)
        if len(tasks) > 1:
            self._pending_launches.extend(tasks[1:])

    def _drain_pending_launches(self) -> None:
        demo = self.demo
        if demo is None or not self._pending_launches:
            return
        launches = max(1, int(self._launches_per_update))
        count = 0
        while self._pending_launches and count < launches:
            task_id, logic_alias, runnable, params = self._pending_launches.pop(0)
            self._queue_task(demo, task_id, logic_alias, runnable, params)
            count += 1

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

        busy = bool(self._pending_launches) or sched.tasks_busy_match_any(*_ALL_TASK_IDS)
        self._set_busy(busy)
        self._set_buttons_enabled(demo, not busy)

        if busy:
            n = len(self.task_ids) + len(self._pending_launches)
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
        self._pending_launches.clear()
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
        self._pending_launches.clear()
        self._refresh_color_table()
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
        self._queue_task(host, _TASK_ID_ITERATIVE, "primary", "iterative_task",
                         {"size": (w, h), "center": center, "scale": scale})
        self._publish_status(MANDEL_KIND_RUNNING_ITERATIVE)

    def launch_recursive(self, host) -> None:
        """Recursive quad-subdivide render: one task on the primary canvas."""
        if self._begin_launch(host) is None:
            return
        w, h = self.primary_canvas.canvas.get_size()
        center, scale = self._viewport(w, h)
        self._queue_task(host, _TASK_ID_RECURSIVE, "primary", "recursive_task",
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
            (_TASK_IDS_QUADRANTS[0], Rect(0,   0,  lw,      th)),
            (_TASK_IDS_QUADRANTS[1], Rect(lw,  0,  w - lw,  th)),
            (_TASK_IDS_QUADRANTS[2], Rect(0,   th, lw,      h - th)),
            (_TASK_IDS_QUADRANTS[3], Rect(lw,  th, w - lw,  h - th)),
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
        first = self.split_canvases.get(_SPLIT_KEYS[0])
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
            for key in _SPLIT_KEYS
        ]
        self._queue_staged_tasks(host, tasks)
        self._publish_status(MANDEL_KIND_RUNNING_FOUR_SPLIT)


__all__ = ["MandelbrotFeature"]
