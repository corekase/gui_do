"""Runtime/status helpers for the Mandelbrot demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gui_do.features.data_driven_runtime import ensure_scene_scheduler

from .mandelbrot_specs import (
    MANDEL_ALL_TASK_IDS,
    MANDEL_KIND_COMPLETE,
    MANDEL_KIND_FAILED,
    MANDEL_KIND_STATUS,
    MANDEL_STATUS_SCOPE,
    MANDEL_STATUS_TOPIC,
    _STATUS_TEXT,
)
from .mandelbrot_status_event import MandelStatusEvent

if TYPE_CHECKING:
    from .mandelbrot_feature import MandelbrotFeature


def set_busy(feature: MandelbrotFeature, busy: bool) -> None:
    sched = feature.scheduler
    if sched is None or bool(busy) == feature._busy:
        return
    feature._busy = bool(busy)
    limit = feature._idle_dispatch_limit
    ingest_limit = feature._idle_ingest_limit
    if busy:
        if isinstance(limit, int):
            limit = max(48, min(limit, 192))
        if isinstance(ingest_limit, int):
            ingest_limit = max(256, min(ingest_limit, 1024))
    if hasattr(sched, "set_message_dispatch_limit"):
        sched.set_message_dispatch_limit(limit)
    if hasattr(sched, "set_message_ingest_limit"):
        sched.set_message_ingest_limit(ingest_limit)


def publish_status(feature: MandelbrotFeature, kind: str, detail: str | None = None) -> None:
    if kind == MANDEL_KIND_FAILED:
        text = f"Mandelbrot failed: {detail}" if detail else "Mandelbrot failed"
    elif kind == MANDEL_KIND_STATUS:
        text = detail or "Mandelbrot: idle"
    else:
        text = _STATUS_TEXT.get(kind, detail or f"Mandelbrot: {kind}")

    feature.status_text = text
    if feature.status_label is not None:
        feature.status_label.text = text

    demo = feature.demo
    if demo is not None:
        event = MandelStatusEvent(kind=kind, detail=detail)
        demo.app.events.publish(MANDEL_STATUS_TOPIC, event.to_payload(), scope=MANDEL_STATUS_SCOPE)


def on_status_event(feature: MandelbrotFeature, payload) -> None:
    event = MandelStatusEvent.from_payload(payload)
    text = _STATUS_TEXT.get(event.kind, event.detail or f"Mandelbrot: {event.kind}")
    feature.status_text = text
    if feature.status_label is not None:
        feature.status_label.text = text


def get_scheduler(feature: MandelbrotFeature, host):
    sched = ensure_scene_scheduler(feature, host, scene_name="main")
    if sched is None:
        raise AttributeError("Mandelbrot scheduler not available")
    feature.scheduler = sched
    return sched


def queue_staged_tasks(feature: MandelbrotFeature, host, tasks: list[tuple[str, str, str, dict]]) -> None:
    if not tasks:
        return
    first_task = tasks[0]
    feature._queue_task(host, *first_task)
    if len(tasks) > 1:
        feature._pending_launches.extend(tasks[1:])


def drain_pending_launches(feature: MandelbrotFeature) -> None:
    demo = feature.demo
    if demo is None or not feature._pending_launches:
        return
    launches = max(1, int(feature._launches_per_update))
    count = 0
    while feature._pending_launches and count < launches:
        task_id, logic_alias, runnable, params = feature._pending_launches.pop(0)
        feature._queue_task(demo, task_id, logic_alias, runnable, params)
        count += 1


def set_buttons_enabled(feature: MandelbrotFeature, host, enabled: bool) -> None:
    for btn in feature.task_buttons:
        btn.enabled = enabled
    if not enabled:
        focused = host.app.focus.focused_node
        if focused in feature.task_buttons:
            reset = feature.reset_button
            if reset and reset.visible and reset.enabled and reset.accepts_focus():
                host.app.focus.set_focus(reset)
            else:
                host.app.focus.revalidate_focus(host.app.scene)


def show_primary(feature: MandelbrotFeature) -> None:
    if feature.primary_canvas:
        feature.primary_canvas.visible = True
    for c in feature.split_canvases.values():
        c.visible = False


def show_split(feature: MandelbrotFeature) -> None:
    if feature.primary_canvas:
        feature.primary_canvas.visible = False
    for c in feature.split_canvases.values():
        c.visible = True


def clear_canvases(feature: MandelbrotFeature, host) -> None:
    bg = host.app.theme.medium
    if feature.primary_canvas:
        feature.primary_canvas.canvas.fill(bg)
    for c in feature.split_canvases.values():
        c.canvas.fill(bg)


def drain_scheduler_events(feature: MandelbrotFeature) -> None:
    demo = feature.demo
    if demo is None:
        return
    sched = feature._get_scheduler(demo)

    for event in sched.get_finished_events():
        if event.task_id in feature.task_ids:
            demo.app.events.publish("toast", {
                "message": f"Mandelbrot task '{event.task_id}' completed.",
                "title": "Mandelbrot",
                "severity": "SUCCESS",
            })
            feature.task_ids.discard(event.task_id)
            sched.pop_result(event.task_id, None)

    failed = []
    for event in sched.get_failed_events():
        if event.task_id in feature.task_ids:
            feature.task_ids.discard(event.task_id)
            failed.append(f"{event.task_id}: {event.error}")
    if failed:
        feature._publish_status(MANDEL_KIND_FAILED, "; ".join(sorted(failed)))

    busy = bool(feature._pending_launches) or sched.tasks_busy_match_any(*MANDEL_ALL_TASK_IDS)
    feature._set_busy(busy)
    feature._set_buttons_enabled(demo, not busy)

    if busy:
        n = len(feature.task_ids) + len(feature._pending_launches)
        word = "task" if n == 1 else "tasks"
        status_text = f"Mandelbrot: running ({n} {word})"
        if feature.status_text != status_text:
            feature._publish_status(MANDEL_KIND_STATUS, status_text)
    elif feature.status_text.startswith("Mandelbrot: running"):
        feature._publish_status(MANDEL_KIND_COMPLETE)

    sched.clear_events()


def begin_launch(feature: MandelbrotFeature, host, *, split: bool = False):
    sched = feature._get_scheduler(host)
    if sched.tasks_busy_match_any(*MANDEL_ALL_TASK_IDS):
        return None
    feature._pending_launches.clear()
    feature._refresh_color_table()
    feature._set_busy(True)
    feature._set_buttons_enabled(host, False)
    if split:
        feature._show_split()
    else:
        feature._show_primary()
    feature._clear_canvases(host)
    return sched


__all__ = [
    "begin_launch",
    "clear_canvases",
    "drain_pending_launches",
    "drain_scheduler_events",
    "get_scheduler",
    "on_status_event",
    "publish_status",
    "queue_staged_tasks",
    "set_busy",
    "set_buttons_enabled",
    "show_primary",
    "show_split",
]
