"""Scheduler helpers for Mandelbrot feature task dispatch."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mandelbrot_feature import MandelbrotFeature


def _run_logic_task(feature: MandelbrotFeature, host, logic_alias: str, runnable: str, tid, params) -> None:
    name = feature.bound_logic_name(alias=logic_alias)
    if name is not None:
        host.app.run_feature_runnable(name, runnable, feature._get_scheduler(host), str(tid), params)


def _apply_task_result(feature: MandelbrotFeature, task_id: str, payload) -> None:
    feature._apply_result(task_id, payload)


def queue_task(feature: MandelbrotFeature, host, task_id: str, logic_alias: str, runnable: str, params: dict) -> None:
    sched = feature._get_scheduler(host)
    run_method = partial(_run_logic_task, feature, host, logic_alias, runnable)
    result_method = partial(_apply_task_result, feature, task_id)
    sched.add_task(
        task_id,
        run_method,
        parameters=params,
        message_method=result_method,
    )
    feature.task_ids.add(task_id)


__all__ = [
    "queue_task",
]
