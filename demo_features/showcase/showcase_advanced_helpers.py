"""Advanced-category builders for the controls showcase feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    AnimatedImageControl,
    DockPane,
    DockTabs,
    DockWorkspace,
    DockWorkspacePanel,
    FixedPatternFormatter,
    FrameAnimation,
    GridLayout,
    GridPlacement,
    LabelControl,
    NumericFormatter,
    OverlayPanelControl,
    PanelControl,
    PatternFormatter,
    ProgressBarControl,
    PropertyInspectorModel,
    PropertyInspectorPanel,
    RangeSliderControl,
    SpinnerControl,
    SpriteSheet,
)
from gui_do.features.control_spec import ControlDefinition

from .showcase_inspectable import ShowcaseInspectable

if TYPE_CHECKING:
    from .showcase_feature import ShowcaseFeature


def advanced_defs(feature: ShowcaseFeature, col_w: int, host) -> list[ControlDefinition]:
    import pygame as _pygame

    label_h = int(feature.LABEL_HEIGHT)
    label_gap = int(feature.LABEL_GAP)
    row_gap = int(feature.ROW_GAP)

    indeterminate_bar = ProgressBarControl(
        "control_progress_bar_indeterminate", Rect(0, 0, col_w, 20), indeterminate=True
    )
    feature._indeterminate_bar = indeterminate_bar

    frame_w, frame_h = 32, 32
    atlas = _pygame.Surface((frame_w * 4, frame_h), flags=_pygame.SRCALPHA)
    for fi, color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
        atlas.fill(color, Rect(fi * frame_w, 0, frame_w, frame_h))
    sheet = SpriteSheet(atlas, frame_w=frame_w, frame_h=frame_h)
    animation = FrameAnimation(sheet, frames=list(range(4)), fps=1, loop=True)
    anim_ctrl = AnimatedImageControl(
        "control_animated_image", Rect(0, 0, col_w, 48), animation=animation, scale=True
    )
    feature._showcase_anim_ctrl = anim_ctrl

    def _add_labeled(panel: PanelControl, y: int, *, key: str, label: str, control, control_h: int) -> int:
        label_control = LabelControl(
            f"label_{key}_inline",
            Rect(0, 0, col_w, label_h),
            label,
            align="left",
        )
        content_h = max(1, int(control_h))
        layout = GridLayout(
            row_tracks=[label_h, label_gap, content_h],
            col_tracks=[max(1, int(col_w))],
            gap=0,
            padding=0,
        )
        layout.place(label_control, GridPlacement(row=0, col=0))
        layout.place(control, GridPlacement(row=2, col=0))
        layout.apply(Rect(0, int(y), max(1, int(col_w)), label_h + label_gap + content_h))
        panel.add_at(label_control, label_control.rect.left, label_control.rect.top)
        panel.add_at(control, control.rect.left, control.rect.top)
        return int(y) + label_h + label_gap + content_h + row_gap

    def _make_overlay_panel() -> OverlayPanelControl:
        op = OverlayPanelControl("control_overlay_panel", Rect(0, 0, col_w, 90), draw_background=True)
        items = ["Overlay Item A", "Overlay Item B", "Overlay Item C"]
        labels = [
            LabelControl(f"overlay_child_{i}", Rect(0, 0, col_w - 16, 22), txt, align="left")
            for i, txt in enumerate(items)
        ]
        layout = GridLayout(
            row_tracks=[22, 4, 22, 4, 22],
            col_tracks=[max(1, int(col_w - 16))],
            gap=0,
            padding=0,
        )
        layout.place(labels[0], GridPlacement(row=0, col=0))
        layout.place(labels[1], GridPlacement(row=2, col=0))
        layout.place(labels[2], GridPlacement(row=4, col=0))
        layout.apply(Rect(8, 6, max(1, int(col_w - 16)), 74))
        for label in labels:
            op.add_at(label, rel_x=label.rect.left, rel_y=label.rect.top)
        return op

    def _make_dock() -> DockWorkspacePanel:
        ws = DockWorkspace(
            DockTabs(
                "sc_dock_tabs",
                panes=[
                    DockPane("editor", "Editor"),
                    DockPane("preview", "Preview"),
                    DockPane("console", "Console"),
                ],
            )
        )
        return DockWorkspacePanel("control_dock_workspace_panel", Rect(0, 0, col_w, 40), ws)

    def _make_primary_column_panel() -> PanelControl:
        panel = PanelControl("control_adv_primary_column", Rect(0, 0, col_w, 290), draw_background=False)
        y = 0
        spinner = SpinnerControl(
            "control_spinner",
            Rect(0, 0, col_w, 30),
            value=25,
            min_value=0,
            max_value=100,
            step=1,
            decimals=0,
            on_change=lambda v, _r: None,
        )
        y = _add_labeled(panel, y, key="spinner", label="Spinner", control=spinner, control_h=30)

        range_slider = RangeSliderControl(
            "control_range_slider",
            Rect(0, 0, col_w, 24),
            min_value=0,
            max_value=100,
            low_value=20,
            high_value=80,
            on_change=lambda lo, hi, _r: None,
        )
        y = _add_labeled(panel, y, key="range_slider", label="Range Slider", control=range_slider, control_h=24)

        numeric = NumericFormatter(decimals=2, thousands_sep=",").create_text_input(
            "control_numeric_fmt_input", Rect(0, 0, col_w, 30), raw_value="12500", placeholder="0.00"
        )
        y = _add_labeled(panel, y, key="numeric_fmt_input", label="Numeric Format", control=numeric, control_h=30)

        pattern = PatternFormatter("###-###-####").create_text_input(
            "control_pattern_fmt_input", Rect(0, 0, col_w, 30), raw_value="5551234567", placeholder="###-###-####"
        )
        y = _add_labeled(panel, y, key="pattern_fmt_input", label="Pattern Format", control=pattern, control_h=30)

        fixed_pattern = FixedPatternFormatter("#####-####").create_text_input(
            "control_fixed_pattern_fmt_input", Rect(0, 0, col_w, 30), raw_value="941010001", placeholder="#####-####"
        )
        _add_labeled(
            panel,
            y,
            key="fixed_pattern_fmt_input",
            label="Fixed Pattern Format",
            control=fixed_pattern,
            control_h=30,
        )
        return panel

    def _make_secondary_column_panel() -> PanelControl:
        panel = PanelControl("control_adv_secondary_column", Rect(0, 0, col_w, 278), draw_background=False)
        y = 0
        dock = _make_dock()
        y = _add_labeled(panel, y, key="dock_workspace_panel", label="Dock Workspace", control=dock, control_h=40)

        overlay = _make_overlay_panel()
        y = _add_labeled(panel, y, key="overlay_panel", label="Overlay Panel", control=overlay, control_h=90)

        progress = ProgressBarControl("control_progress_bar", Rect(0, 0, col_w, 20), value=0.65)
        y = _add_labeled(panel, y, key="progress_bar", label="Progress Bar", control=progress, control_h=20)

        _add_labeled(
            panel,
            y,
            key="progress_bar_indeterminate",
            label="Progress (Marquee)",
            control=indeterminate_bar,
            control_h=20,
        )
        return panel

    def _make_tertiary_column_panel() -> PanelControl:
        panel = PanelControl("control_adv_tertiary_column", Rect(0, 0, col_w, 238), draw_background=False)
        y = 0
        inspector = PropertyInspectorPanel(
            "control_property_inspector", Rect(0, 0, col_w, 160), PropertyInspectorModel(ShowcaseInspectable())
        )
        y = _add_labeled(
            panel,
            y,
            key="property_inspector",
            label="Property Inspector",
            control=inspector,
            control_h=160,
        )
        _add_labeled(
            panel,
            y,
            key="animated_image",
            label="Animated Image",
            control=anim_ctrl,
            control_h=48,
        )
        return panel

    return [
        ControlDefinition(
            "advanced_primary_column",
            "",
            290,
            100,
            _make_primary_column_panel,
        ),
        ControlDefinition(
            "advanced_secondary_column",
            "",
            278,
            101,
            _make_secondary_column_panel,
        ),
        ControlDefinition(
            "advanced_tertiary_column",
            "",
            238,
            102,
            _make_tertiary_column_panel,
        ),
    ]


__all__ = ["advanced_defs"]
