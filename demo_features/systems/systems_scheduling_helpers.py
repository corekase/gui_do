"""Scheduling helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, LabelControl, PanelControl, Sleep

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_scheduling_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_scheduling_panel", Rect(rect), draw_background=False)
    timer_probe_button = ButtonControl(
        "systems_schedule_timers",
        Rect(0, 0, 176, 32),
        "Start Timer Probe",
        feature._start_timer_probe,
        style="round",
    )
    labels_top = feature._add_button_rows(
        panel,
        rect,
        0,
        [
            ButtonControl(
                "systems_schedule_background_job",
                Rect(0, 0, 180, 32),
                "Queue Artifact Build",
                feature._queue_background_job,
                style="round",
            ),
            ButtonControl(
                "systems_schedule_rollout",
                Rect(0, 0, 176, 32),
                "Start Rollout Script",
                feature._start_rollout_sequence,
                style="round",
            ),
            ButtonControl(
                "systems_schedule_rate_limit",
                Rect(0, 0, 192, 32),
                "Simulate Burst Input",
                feature._simulate_rate_limited_input,
                style="round",
            ),
        ],
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )
    labels_top = feature._add_single_column_button_row(
        panel,
        rect,
        labels_top,
        timer_probe_button,
        column_index=0,
        span_both_columns=True,
        span_from_window_left=False,
        left=feature.PANEL_PADDING_X,
        width=max(1, rect.width - (feature.PANEL_PADDING_X * 2) - feature.LEFT_SIDE_INSET_X),
    )
    feature.scheduling_task_label = LabelControl(
        "systems_scheduling_task_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.scheduling_rollout_label = LabelControl(
        "systems_scheduling_rollout_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.scheduling_timer_label = LabelControl(
        "systems_scheduling_timer_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.scheduling_rate_limiter_label = LabelControl(
        "systems_scheduling_rate_limit_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            labels_top + 8,
            max(1, rect.width - feature.LABEL_INSET_X),
            136,
        ),
        [
            feature.scheduling_task_label,
            feature.scheduling_rollout_label,
            feature.scheduling_timer_label,
            feature.scheduling_rate_limiter_label,
        ],
        gap=8,
    )
    feature._refresh_scheduling_labels()
    return panel


def rollout_sequence(feature: SystemsFeature):
    feature._rollout_phase = "Prime canary ring"
    yield Sleep(0.05)
    feature._rollout_phase = "Wait for smoke checks"
    yield Sleep(0.05)
    feature._rollout_phase = "Promote stable ring"
    yield Sleep(0.05)
    feature._rollout_phase = "Rollout complete"


def start_rollout_sequence(feature: SystemsFeature) -> None:
    if feature._rollout_handle is not None and feature._rollout_handle.is_running:
        return
    feature._rollout_handle = feature._cooperative_scheduler.start(rollout_sequence(feature))
    feature._refresh_scheduling_labels()


def queue_background_job(feature: SystemsFeature) -> None:
    feature._task_job_index += 1
    task_id = f"artifact-{feature._task_job_index:02d}"
    payload = {
        "lane": feature._settings_registry.get_value("systems", "profile"),
        "checks": int(feature._settings_registry.get_value("systems", "parallel_checks")),
    }
    feature._task_scheduler.add_task(task_id, feature._build_artifact_job, payload)
    feature._task_last_summary = f"TaskScheduler queued {task_id} for the {payload['lane']} lane."
    feature._task_last_failure = ""
    feature._refresh_scheduling_labels()


def build_artifact_job(_feature: SystemsFeature, task_id: str, payload: dict[str, object]) -> str:
    lane = str(payload.get("lane", "review"))
    checks = int(payload.get("checks", 1))
    return f"{task_id} built for {lane} with {checks} parallel checks"


def refresh_scheduling_labels(feature: SystemsFeature) -> None:
    finished = feature._task_scheduler.get_finished_tasks()
    if finished:
        latest_task = finished[-1]
        result = feature._task_scheduler.pop_result(latest_task, None)
        if result is not None:
            feature._task_last_summary = f"TaskScheduler finished {latest_task}: {result}"
        feature._task_scheduler.clear_finished_tasks()
    failures = feature._task_scheduler.get_failed_tasks()
    if failures:
        latest_task, error = failures[-1]
        feature._task_last_failure = f"TaskScheduler failed {latest_task}: {error}"
        feature._task_scheduler.clear_failed_tasks()
    if feature.scheduling_task_label is not None:
        summary = feature._task_last_failure or feature._task_last_summary
        feature.scheduling_task_label.text = (
            f"{summary} | pending={feature._task_scheduler.pending_count()} running={feature._task_scheduler.running_count()}"
        )
    if feature.scheduling_rollout_label is not None:
        feature.scheduling_rollout_label.text = (
            f"CooperativeScheduler phase: {feature._rollout_phase} | active coroutines={feature._cooperative_scheduler.coroutine_count}"
        )
    if feature.scheduling_timer_label is not None:
        feature.scheduling_timer_label.text = (
            f"Timers active={feature._timers.timer_ids()} probe_armed={feature._timer_probe_armed} last_event={feature._timer_last_event}"
        )
    if feature.scheduling_rate_limiter_label is not None:
        feature.scheduling_rate_limiter_label.text = (
            f"{feature._rate_limiter_status} | throttled_events={feature._throttle_event_count} "
            f"debounced_commits={feature._debounce_commit_count}"
        )
    if feature.scheduling_timeline_label is not None:
        feature.scheduling_timeline_label.text = (
            f"SceneTimeline stage={feature._motion_timeline_stage} cycles={feature._motion_timeline_cycles}"
        )
    if feature.scheduling_tween_label is not None:
        feature.scheduling_tween_label.text = (
            f"TweenManager value={feature._motion_tween_value:.2f} active_tweens={feature._motion_tweens.active_count}"
        )
    if feature.scheduling_sequence_label is not None:
        feature.scheduling_sequence_label.text = (
            f"AnimationSequence stage={feature._motion_sequence_stage} runs={feature._motion_sequence_runs} | "
            f"TransitionManager phase={feature._motion_transition_phase} value={feature._motion_transition_value:.2f} | "
            f"AnimationStateMachine state={feature._motion_animation_state} value={feature._motion_animation_value:.2f}"
        )


def start_timer_probe(feature: SystemsFeature) -> None:
    feature._timer_probe_armed = True
    if not feature._timers.has_timer("systems_probe_heartbeat"):
        feature._timers.add_timer("systems_probe_heartbeat", 0.4, feature._on_timer_probe_tick)
    feature._timers.remove_timer("systems_probe_complete")
    feature._timers.add_once("systems_probe_complete", 1.2, feature._on_timer_probe_complete)
    feature._refresh_scheduling_labels()


def simulate_rate_limited_input(feature: SystemsFeature) -> None:
    for index in range(12):
        value = index * 10
        feature._throttler.call(value)
        feature._debouncer.call(f"draft-{value:03d}")
    feature._rate_limiter_status = "Burst queued; waiting for throttled sample and debounced commit."
    feature._refresh_scheduling_labels()


def on_throttled_burst_input(feature: SystemsFeature, value: int) -> None:
    feature._throttle_event_count += 1
    feature._throttle_last_value = int(value)
    feature._rate_limiter_status = f"Throttler sampled value {feature._throttle_last_value}"
    feature._refresh_scheduling_labels()


def on_debounced_burst_commit(feature: SystemsFeature, value: str) -> None:
    feature._debounce_commit_count += 1
    feature._debounce_last_value = str(value)
    feature._rate_limiter_status = (
        f"Debouncer committed {feature._debounce_last_value}; last throttled value {feature._throttle_last_value}"
    )
    feature._refresh_scheduling_labels()


def on_timer_probe_tick(feature: SystemsFeature) -> None:
    feature._timer_tick_count += 1
    feature._timer_last_event = f"heartbeat #{feature._timer_tick_count}"


def on_timer_probe_complete(feature: SystemsFeature) -> None:
    feature._timer_probe_armed = False
    feature._timers.remove_timer("systems_probe_heartbeat")
    feature._timer_last_event = f"probe completed after {feature._timer_tick_count} heartbeat callbacks"


__all__ = [
    "build_scheduling_panel",
    "build_artifact_job",
    "on_debounced_burst_commit",
    "on_throttled_burst_input",
    "on_timer_probe_complete",
    "on_timer_probe_tick",
    "queue_background_job",
    "refresh_scheduling_labels",
    "simulate_rate_limited_input",
    "start_timer_probe",
    "start_rollout_sequence",
]
