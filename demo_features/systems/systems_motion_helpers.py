"""Motion workflow helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import AnimationSequence, ButtonControl, LabelControl, PanelControl, SceneTimeline

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_motion_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_motion_panel", Rect(rect), draw_background=False)
    if feature._motion_animation_state_machine.current_state is None:
        feature._motion_animation_state_machine.set_state("idle")
    feature.motion_intro_label = LabelControl(
        "systems_motion_intro",
        Rect(0, 0, rect.width, 28),
        "SceneTimeline, TweenManager, and AnimationSequence demo motion workflows.",
        align="left",
    )
    feature._place_vertical_grid_sequence(
        panel,
        Rect(feature.LABEL_INSET_X, 0, max(1, rect.width - feature.LABEL_INSET_X), 28),
        [(feature.motion_intro_label, 28, 0)],
    )

    motion_buttons_top = 44
    motion_labels_anchor_top = feature._add_button_rows(
        panel,
        rect,
        motion_buttons_top,
        [
            ButtonControl(
                "systems_motion_timeline",
                Rect(0, 0, 160, 32),
                "Play Timeline",
                feature._play_motion_timeline,
                style="round",
            ),
            ButtonControl(
                "systems_motion_tween",
                Rect(0, 0, 156, 32),
                "Run Tween",
                feature._run_motion_tween,
                style="round",
            ),
            ButtonControl(
                "systems_motion_sequence",
                Rect(0, 0, 176, 32),
                "Run Animation Sequence",
                feature._run_motion_sequence,
                style="round",
            ),
            ButtonControl(
                "systems_motion_transition",
                Rect(0, 0, 170, 32),
                "Toggle Transition",
                feature._toggle_motion_transition,
                style="round",
            ),
            ButtonControl(
                "systems_motion_asm",
                Rect(0, 0, 170, 32),
                "Cycle Anim State",
                feature._cycle_motion_animation_state,
                style="round",
            ),
        ],
        per_row=3,
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )

    motion_labels_top = motion_labels_anchor_top + 8
    feature.scheduling_timeline_label = LabelControl(
        "systems_motion_timeline_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.scheduling_tween_label = LabelControl(
        "systems_motion_tween_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.scheduling_sequence_label = LabelControl(
        "systems_motion_sequence_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            motion_labels_top,
            max(1, rect.width - feature.LABEL_INSET_X),
            100,
        ),
        [
            feature.scheduling_timeline_label,
            feature.scheduling_tween_label,
            feature.scheduling_sequence_label,
        ],
        gap=8,
    )
    feature._refresh_motion_labels()
    return panel


def refresh_motion_labels(feature: SystemsFeature) -> None:
    feature._refresh_scheduling_labels()
    if feature.motion_intro_label is not None:
        feature.motion_intro_label.text = (
            "SceneTimeline, TweenManager, AnimationSequence, TransitionManager, "
            "and AnimationStateMachine demo motion workflows."
        )


def play_motion_timeline(feature: SystemsFeature) -> None:
    timeline = SceneTimeline(duration=1.6)
    timeline.at(0.0, lambda: feature._set_motion_timeline_stage("Queued"))
    timeline.at(0.5, lambda: feature._set_motion_timeline_stage("Running"))
    timeline.at(1.0, lambda: feature._set_motion_timeline_stage("Settling"))
    timeline.on_complete(lambda: feature._set_motion_timeline_stage("Complete"))
    feature._motion_timeline_stage = "Queued"
    feature._motion_timeline_cycles += 1
    feature._motion_timeline = timeline
    feature._motion_timeline.play()
    feature._refresh_scheduling_labels()


def set_motion_timeline_stage(feature: SystemsFeature, stage: str) -> None:
    feature._motion_timeline_stage = str(stage)
    feature._refresh_scheduling_labels()


def run_motion_tween(feature: SystemsFeature) -> None:
    feature._motion_tweens.cancel_all()
    feature._motion_tween_value = 0.0
    feature._motion_sequence_stage = "Tween running"
    feature._motion_tweens.tween(
        feature,
        "_motion_tween_value",
        1.0,
        0.8,
        on_complete=lambda: feature._set_motion_sequence_stage("Tween complete"),
    )
    feature._refresh_scheduling_labels()


def run_motion_sequence(feature: SystemsFeature) -> None:
    feature._motion_tweens.cancel_all()
    feature._motion_tween_value = 0.0
    feature._motion_sequence_runs += 1
    sequence = AnimationSequence(feature._motion_tweens)
    sequence.then(
        target=feature,
        attr="_motion_tween_value",
        end_value=1.0,
        duration_seconds=0.4,
    ).wait(0.1).then(
        target=feature,
        attr="_motion_tween_value",
        end_value=0.25,
        duration_seconds=0.45,
    ).on_done(lambda: feature._set_motion_sequence_stage("Sequence complete"))
    feature._motion_sequence_stage = "Sequence running"
    sequence.start()
    feature._refresh_scheduling_labels()


def toggle_motion_transition(feature: SystemsFeature) -> None:
    if feature._motion_transition_value >= 0.5:
        feature._motion_transition_phase = "Hide"
        feature._transition_manager.on_hide(feature)
    else:
        feature._motion_transition_phase = "Show"
        feature._transition_manager.on_show(feature)
    feature._refresh_scheduling_labels()


def on_motion_animation_state_changed(feature: SystemsFeature, state_name: str) -> None:
    feature._motion_animation_state = str(state_name)
    feature._refresh_scheduling_labels()


def cycle_motion_animation_state(feature: SystemsFeature) -> None:
    feature._motion_animation_state_index = (feature._motion_animation_state_index + 1) % len(
        feature._motion_animation_states
    )
    next_state = feature._motion_animation_states[feature._motion_animation_state_index]
    feature._motion_animation_state_machine.set_state(next_state)
    feature._refresh_scheduling_labels()


def set_motion_sequence_stage(feature: SystemsFeature, stage: str) -> None:
    feature._motion_sequence_stage = str(stage)
    feature._refresh_scheduling_labels()


__all__ = [
    "build_motion_panel",
    "cycle_motion_animation_state",
    "on_motion_animation_state_changed",
    "play_motion_timeline",
    "refresh_motion_labels",
    "run_motion_sequence",
    "run_motion_tween",
    "set_motion_sequence_stage",
    "set_motion_timeline_stage",
    "toggle_motion_transition",
]
