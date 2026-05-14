"""Extended-category builders for the controls showcase feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    BreadcrumbControl,
    BreadcrumbItem,
    ChipInputControl,
    ColorPickerControl,
    ContextMenuItem,
    DatePickerControl,
    ErrorBoundary,
    ExpanderControl,
    GridLayout,
    GridPlacement,
    LabelControl,
    MenuEntry,
    PanelControl,
    SceneMenuStripControl,
    SplitButtonControl,
    SplitButtonOption,
    StatusBarControl,
    StatusSlot,
    TimePickerControl,
    ToolbarControl,
    ToolbarItem,
)
from gui_do.features.control_spec import ControlDefinition
from gui_do.features.layout_geometry import split_columns

if TYPE_CHECKING:
    from .showcase_feature import ShowcaseFeature


def extended_defs(feature: ShowcaseFeature, col_w: int, host) -> list[ControlDefinition]:
    app = host.app
    label_h = int(feature.LABEL_HEIGHT)
    label_gap = int(feature.LABEL_GAP)
    row_gap = int(feature.ROW_GAP)

    sub_cols = split_columns(Rect(0, 0, col_w, 100), count=3, gap=row_gap, min_width=80)
    sc0_x, sc0_w = int(sub_cols[0].left), int(sub_cols[0].width)
    sc1_x, sc1_w = int(sub_cols[1].left), int(sub_cols[1].width)
    sc2_x, sc2_w = int(sub_cols[2].left), int(sub_cols[2].width)

    def _add_cell(
        panel: PanelControl,
        key: str,
        x: int,
        w: int,
        label: str,
        control,
    ) -> None:
        label_control = LabelControl(
            f"label_{key}_ext",
            Rect(0, 0, w, label_h),
            label,
            align="left",
        )
        content_h = max(1, int(control.rect.height))
        layout = GridLayout(
            row_tracks=[label_h, label_gap, content_h],
            col_tracks=[max(1, int(w))],
            gap=0,
            padding=0,
        )
        layout.place(label_control, GridPlacement(row=0, col=0))
        layout.place(control, GridPlacement(row=2, col=0))
        layout.apply(Rect(int(x), 0, max(1, int(w)), label_h + label_gap + content_h))
        panel.add_at(label_control, label_control.rect.left, label_control.rect.top)
        panel.add_at(control, control.rect.left, control.rect.top)

    row1_h = label_h + label_gap + 36

    def _make_row1_panel() -> PanelControl:
        panel = PanelControl("control_ext_row1", Rect(0, 0, col_w, row1_h), draw_background=False)
        toolbar = ToolbarControl(
            "control_toolbar",
            Rect(0, 0, sc0_w, 36),
            items=[
                ToolbarItem(label="Cut", action_id="cut"),
                ToolbarItem(label="Copy", action_id="copy"),
                ToolbarItem(separator=True),
                ToolbarItem(label="Paste", action_id="paste"),
            ],
        )
        _add_cell(panel, "toolbar", sc0_x, sc0_w, "Toolbar", toolbar)
        split_btn = SplitButtonControl(
            "control_split_button",
            Rect(0, 0, sc1_w, 32),
            label="Save",
            options=[
                SplitButtonOption(label="Save As...", on_click=lambda: None),
                SplitButtonOption(label="Save All", on_click=lambda: None),
            ],
        )
        _add_cell(panel, "split_button", sc1_x, sc1_w, "Split Button", split_btn)
        breadcrumb = BreadcrumbControl(
            "control_breadcrumb",
            Rect(0, 0, sc2_w, 28),
            items=[
                BreadcrumbItem(label="Home", value="home"),
                BreadcrumbItem(label="Files", value="files"),
                BreadcrumbItem(label="Documents", value="documents"),
            ],
        )
        _add_cell(panel, "breadcrumb", sc2_x, sc2_w, "Breadcrumb", breadcrumb)
        return panel

    row2_h = label_h + label_gap + 80

    def _make_row2_panel() -> PanelControl:
        panel = PanelControl("control_ext_row2", Rect(0, 0, col_w, row2_h), draw_background=False)
        chip = ChipInputControl("control_chip_input", Rect(0, 0, sc0_w, 36), placeholder="Add tag...", values=["Python", "GUI"])
        _add_cell(panel, "chip_input", sc0_x, sc0_w, "Chip Input", chip)
        status_bar = StatusBarControl(
            "control_status_bar",
            Rect(0, 0, sc1_w, 24),
            slots=[
                StatusSlot("status", "Ready", width=80),
                StatusSlot("line", "Ln 1", width=50, separator_after=True),
                StatusSlot("col", "Col 1", width=50),
            ],
        )
        _add_cell(panel, "status_bar", sc1_x, sc1_w, "Status Bar", status_bar)
        expander = ExpanderControl("control_expander", Rect(0, 0, sc2_w, 80), title="Details", body_height=50)
        _add_cell(panel, "expander", sc2_x, sc2_w, "Expander", expander)
        return panel

    row3_h = (label_h + label_gap + 32) + row_gap + (label_h + label_gap + 32)

    def _make_row3_panel() -> PanelControl:
        panel = PanelControl("control_ext_row3", Rect(0, 0, col_w, row3_h), draw_background=False)
        first_row_h = label_h + label_gap + 32
        scene_menu = SceneMenuStripControl(
            "control_scene_menu_strip",
            Rect(0, 0, sc0_w, 30),
            app,
            scenes_shown=False,
            windows_shown=False,
            extra_entries_provider=lambda: [
                MenuEntry(
                    "Demo",
                    [
                        ContextMenuItem("Inspect", action=lambda: None),
                        ContextMenuItem("Refresh", action=lambda: None),
                    ],
                ),
            ],
        )
        _add_cell(panel, "scene_menu_strip", sc0_x, sc0_w, "Scene Menu Strip", scene_menu)

        date_picker = DatePickerControl("control_date_picker", Rect(0, 0, sc1_w, 32))
        _add_cell(panel, "date_picker", sc1_x, sc1_w, "Date Picker", date_picker)

        time_picker = TimePickerControl("control_time_picker", Rect(0, 0, sc0_w, 32), hour=9, minute=30)
        time_label = LabelControl(
            "label_time_picker_ext_row2",
            Rect(0, 0, sc0_w, label_h),
            "Time Picker",
            align="left",
        )
        time_layout = GridLayout(
            row_tracks=[label_h, label_gap, 32],
            col_tracks=[max(1, int(sc0_w))],
            gap=0,
            padding=0,
        )
        time_layout.place(time_label, GridPlacement(row=0, col=0))
        time_layout.place(time_picker, GridPlacement(row=2, col=0))
        time_layout.apply(Rect(sc0_x, first_row_h + row_gap, sc0_w, label_h + label_gap + 32))
        panel.add_at(time_label, time_label.rect.left, time_label.rect.top)
        panel.add_at(time_picker, time_picker.rect.left, time_picker.rect.top)
        return panel

    row4_h = label_h + label_gap + 160

    def _make_row4_panel() -> PanelControl:
        panel = PanelControl("control_ext_row4", Rect(0, 0, col_w, row4_h), draw_background=False)
        # Move Error Boundary to leftmost column, align label with Time Picker
        boundary_child = PanelControl("control_error_boundary_child", Rect(0, 0, sc0_w, 90), draw_background=True)
        boundary_child.add_at(
            LabelControl(
                "control_error_boundary_label",
                Rect(0, 0, sc0_w - 16, 24),
                "Protected preview surface",
                align="left",
            ),
            8,
            8,
        )
        error_boundary = ErrorBoundary(
            boundary_child,
            error_text="Preview unavailable",
        )
        _add_cell(panel, "error_boundary", sc0_x, sc0_w, "Error Boundary", error_boundary)
        return panel

    return [
        ControlDefinition("ext_row1", "", row1_h, 140, _make_row1_panel, labeled=False),
        ControlDefinition("ext_row2", "", row2_h, 141, _make_row2_panel, labeled=False),
        ControlDefinition("ext_row3", "", row3_h, 142, _make_row3_panel, labeled=False),
        ControlDefinition("ext_row4", "", row4_h, 143, _make_row4_panel, labeled=False),
    ]


__all__ = ["extended_defs"]
