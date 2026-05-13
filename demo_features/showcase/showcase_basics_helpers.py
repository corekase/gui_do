"""Basics-category builders for the controls showcase feature."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    DataGridControl,
    DropdownControl,
    DropdownOption,
    FlexLayout,
    FrameControl,
    GridColumn,
    GridLayout,
    GridPlacement,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    ListItem,
    NotificationPanelControl,
    PanelControl,
    RichLabelControl,
    ScrollbarControl,
    SliderControl,
    TabControl,
    TabItem,
    TextAreaControl,
    TextInputControl,
    ToggleControl,
    build_horizontal_row_specs,
)
from gui_do.features.control_spec import RowCellSpec
from gui_do.features.feature_lifecycle import ControlPlacementSpec
from gui_do.features.layout_geometry import column_stack_from_anchor

if TYPE_CHECKING:
    from .showcase_feature import ShowcaseFeature


def build_basics_specs(feature: ShowcaseFeature, bounds: Rect) -> tuple[ControlPlacementSpec, ...]:
    image_path = str(Path(__file__).parent.parent / feature.IMAGE_PATH)
    nc = feature._showcase_notification_center
    label_h = int(feature.LABEL_HEIGHT)
    label_gap = int(feature.LABEL_GAP)
    row_gap = int(feature.ROW_GAP)
    inner_gap = int(feature.BASICS_INNER_GAP)

    stack, _, _, _ = column_stack_from_anchor(
        anchor=bounds,
        content_bottom=bounds.bottom,
        preferred_width=bounds.width,
        item_gap_y=row_gap,
    )

    def make_arrow_boxes(w: int, h: int):
        panel = PanelControl("control_arrow_boxes_cell", Rect(0, 0, w, h), draw_background=False)
        area_w, area_h = min(60, w), min(60, h)
        area = Rect((w - area_w) // 2, (h - area_h) // 2, area_w, area_h)
        cell_w = max(10, (area_w - inner_gap) // 2)
        cell_h = max(10, (area_h - inner_gap) // 2)
        arrows = [
            ArrowBoxControl("control_arrow_up", Rect(0, 0, cell_w, cell_h), 90),
            ArrowBoxControl("control_arrow_down", Rect(0, 0, cell_w, cell_h), 270),
            ArrowBoxControl("control_arrow_left", Rect(0, 0, cell_w, cell_h), 180),
            ArrowBoxControl("control_arrow_right", Rect(0, 0, cell_w, cell_h), 0),
        ]
        layout = GridLayout(
            row_tracks=[cell_h, cell_h],
            col_tracks=[cell_w, cell_w],
            gap=inner_gap,
            padding=0,
        )
        layout.place(arrows[0], GridPlacement(row=0, col=0))
        layout.place(arrows[1], GridPlacement(row=0, col=1))
        layout.place(arrows[2], GridPlacement(row=1, col=0))
        layout.place(arrows[3], GridPlacement(row=1, col=1))
        layout.apply(area)
        for control in arrows:
            panel.add_at(control, control.rect.left, control.rect.top)
        return panel

    def make_vertical_buttons(w: int, h: int):
        panel = PanelControl("control_button_cell", Rect(0, 0, w, h), draw_background=False)
        btn_w = min(100, w)
        btn_h = max(20, (h - inner_gap * 2) // 3)
        controls: list[ButtonControl] = []
        for ctrl_id, label in [
            ("control_button", "Button A"),
            ("control_button_2", "Button B"),
            ("control_button_3", "Button C"),
        ]:
            controls.append(ButtonControl(ctrl_id, Rect(0, 0, btn_w, btn_h), label))
        layout = FlexLayout(direction="column", gap=inner_gap, padding=0)
        for control in controls:
            layout.add(control, grow=0, basis=btn_h)
        layout.apply(Rect(0, 0, btn_w, h))
        for control in controls:
            panel.add_at(control, control.rect.left, control.rect.top)
        return panel

    def make_button_group(group_id: str, group_name: str, items: list):
        def _factory(w: int, h: int) -> PanelControl:
            panel = PanelControl(group_id, Rect(0, 0, w, h), draw_background=False)
            btn_w = min(100, w)
            btn_h = max(20, (h - inner_gap * 2) // 3)
            controls: list[ButtonGroupControl] = []
            for ctrl_id, label in items:
                controls.append(
                    ButtonGroupControl(
                        ctrl_id,
                        Rect(0, 0, btn_w, btn_h),
                        f"controls_showcase_{group_name}",
                        label,
                        selected=False,
                    )
                )
            layout = FlexLayout(direction="column", gap=inner_gap, padding=0)
            for control in controls:
                layout.add(control, grow=0, basis=btn_h)
            layout.apply(Rect(0, 0, btn_w, h))
            for control in controls:
                panel.add_at(control, control.rect.left, control.rect.top)
            return panel

        return _factory

    def make_toggle_group(group_id: str, items: list[tuple[str, str]]):
        def _factory(w: int, h: int) -> PanelControl:
            panel = PanelControl(group_id, Rect(0, 0, w, h), draw_background=False)
            btn_w = min(100, w)
            btn_h = max(20, (h - inner_gap * 2) // 3)
            controls: list[ToggleControl] = []
            for ctrl_id, suffix in items:
                controls.append(
                    ToggleControl(
                        ctrl_id,
                        Rect(0, 0, btn_w, btn_h),
                        text_on=f"Pressed {suffix}",
                        text_off=f"Raised {suffix}",
                        pushed=False,
                    )
                )
            layout = FlexLayout(direction="column", gap=inner_gap, padding=0)
            for control in controls:
                layout.add(control, grow=0, basis=btn_h)
            layout.apply(Rect(0, 0, btn_w, h))
            for control in controls:
                panel.add_at(control, control.rect.left, control.rect.top)
            return panel

        return _factory

    def make_horiz_pair(w: int, h: int):
        panel = PanelControl("control_horizontal_pair_cell", Rect(0, 0, w, h), draw_background=False)
        scrollbar = ScrollbarControl(
            "control_horizontal_scrollbar",
            Rect(0, 0, max(1, w), 24),
            LayoutAxis.HORIZONTAL,
            feature.SCROLLBAR_CONTENT_SIZE,
            feature.SCROLLBAR_VIEWPORT_SIZE,
            offset=feature.SCROLLBAR_DEFAULT_OFFSET,
            step=feature.SCROLLBAR_STEP,
        )
        slider = SliderControl(
            "control_horizontal_slider",
            Rect(0, 0, max(1, w), 24),
            LayoutAxis.HORIZONTAL,
            feature.SLIDER_MINIMUM,
            feature.SLIDER_MAXIMUM,
            feature.SLIDER_DEFAULT_VALUE,
        )
        layout = GridLayout(
            row_tracks=[24, 24],
            col_tracks=["1fr"],
            gap=row_gap,
            padding=0,
        )
        layout.place(scrollbar, GridPlacement(row=0, col=0))
        layout.place(slider, GridPlacement(row=1, col=0))
        layout.apply(Rect(0, 0, max(1, w), max(1, h)))
        panel.add_at(scrollbar, scrollbar.rect.left, scrollbar.rect.top)
        panel.add_at(slider, slider.rect.left, slider.rect.top)
        return panel

    def make_vert_pair(w: int, h: int):
        panel = PanelControl("control_vertical_pair_cell", Rect(0, 0, w, h), draw_background=False)
        track_w, gap_x = 24, 12
        track_h = max(80, h)
        y = max(0, (h - track_h) // 2)
        scrollbar = ScrollbarControl(
            "control_vertical_scrollbar",
            Rect(0, 0, track_w, track_h),
            LayoutAxis.VERTICAL,
            feature.SCROLLBAR_CONTENT_SIZE,
            feature.SCROLLBAR_VIEWPORT_SIZE,
            offset=feature.SCROLLBAR_DEFAULT_OFFSET,
            step=feature.SCROLLBAR_STEP,
        )
        slider = SliderControl(
            "control_vertical_slider",
            Rect(0, 0, track_w, track_h),
            LayoutAxis.VERTICAL,
            feature.SLIDER_MINIMUM,
            feature.SLIDER_MAXIMUM,
            feature.SLIDER_DEFAULT_VALUE,
        )
        layout = GridLayout(
            row_tracks=[track_h],
            col_tracks=[track_w, track_w],
            gap=gap_x,
            padding=0,
        )
        layout.place(scrollbar, GridPlacement(row=0, col=0))
        layout.place(slider, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, y, (track_w * 2) + gap_x, track_h))
        panel.add_at(scrollbar, scrollbar.rect.left, scrollbar.rect.top)
        panel.add_at(slider, slider.rect.left, slider.rect.top)
        return panel

    def make_text_area_with_input(w: int, h: int):
        panel = PanelControl("control_text_area_cell", Rect(0, 0, w, h), draw_background=False)
        ta_h, ti_h, gap = 96, 32, 8
        text_area = TextAreaControl(
            "control_text_area",
            Rect(0, 0, w, ta_h),
            value="Release Notes\nWrap keeps spaces with the text they separate.\nEdit this sample to check caret placement.",
        )
        text_label = LabelControl(
            "label_control_text_input_inline",
            Rect(0, 0, w, label_h),
            "Text Input",
            align="left",
        )
        text_input = TextInputControl(
            "control_text_input",
            Rect(0, 0, w, ti_h),
            placeholder="Type here",
        )
        layout = GridLayout(
            row_tracks=[ta_h, gap, label_h, label_gap, ti_h],
            col_tracks=["1fr"],
            gap=0,
            padding=0,
        )
        layout.place(text_area, GridPlacement(row=0, col=0))
        layout.place(text_label, GridPlacement(row=2, col=0))
        layout.place(text_input, GridPlacement(row=4, col=0))
        layout.apply(Rect(0, 0, max(1, w), ta_h + gap + label_h + label_gap + ti_h))
        panel.add_at(text_area, text_area.rect.left, text_area.rect.top)
        panel.add_at(text_label, text_label.rect.left, text_label.rect.top)
        panel.add_at(text_input, text_input.rect.left, text_input.rect.top)
        return panel

    def make_tab_control(w: int, h: int):
        panel = PanelControl("control_tab_cell", Rect(0, 0, w, h), draw_background=False)
        tab = TabControl(
            "control_tab",
            Rect(0, 0, w, h),
            items=[
                TabItem("one", "One", LabelControl("ctrl_tab_lbl_one", Rect(0, 0, 1, 30), "One", align="left")),
                TabItem("two", "Two", LabelControl("ctrl_tab_lbl_two", Rect(0, 0, 1, 30), "Two", align="left")),
                TabItem("three", "Three", LabelControl("ctrl_tab_lbl_three", Rect(0, 0, 1, 30), "Three", align="left")),
            ],
            selected_key="one",
        )
        layout = GridLayout(
            row_tracks=[max(1, h)],
            col_tracks=["1fr"],
            gap=0,
            padding=0,
        )
        layout.place(tab, GridPlacement(row=0, col=0))
        layout.apply(Rect(0, 0, max(1, w), max(1, h)))
        panel.add_at(tab, tab.rect.left, tab.rect.top)
        return panel

    def make_data_grid(w: int, h: int):
        panel = PanelControl("control_data_grid_cell", Rect(0, 0, w, h), draw_background=False)
        dg = DataGridControl(
            "control_data_grid",
            Rect(0, 0, w, h),
            [GridColumn(key="name", title="Name", width=90), GridColumn(key="value", title="Value", width=70)],
            [
                GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
            ],
            row_height=24,
        )
        layout = GridLayout(
            row_tracks=[max(1, h)],
            col_tracks=["1fr"],
            gap=0,
            padding=0,
        )
        layout.place(dg, GridPlacement(row=0, col=0))
        layout.apply(Rect(0, 0, max(1, w), max(1, h)))
        panel.add_at(dg, dg.rect.left, dg.rect.top)
        return panel

    kw = dict(stack=stack, label_height=label_h, label_gap=label_gap, overflow_gap=row_gap)

    row1 = build_horizontal_row_specs(
        [
            RowCellSpec("arrow_boxes", "Arrow Boxes", 80, 0, make_arrow_boxes, natural_width=110),
            RowCellSpec("buttons_cell", "Buttons", 80, 1, make_vertical_buttons, natural_width=100),
            RowCellSpec(
                "button_group_a_cell",
                "Group A",
                80,
                2,
                make_button_group(
                    "control_button_group_a_cell",
                    "a",
                    [
                        ("control_button_group_a1", "A1"),
                        ("control_button_group_a2", "A2"),
                        ("control_button_group_a3", "A3"),
                    ],
                ),
                natural_width=100,
            ),
            RowCellSpec(
                "button_group_b_cell",
                "Group B",
                80,
                3,
                make_button_group(
                    "control_button_group_b_cell",
                    "b",
                    [
                        ("control_button_group_b1", "B1"),
                        ("control_button_group_b2", "B2"),
                        ("control_button_group_b3", "B3"),
                    ],
                ),
                natural_width=100,
            ),
            RowCellSpec(
                "button_group_c_cell",
                "Group C",
                80,
                4,
                make_button_group(
                    "control_button_group_c_cell",
                    "c",
                    [
                        ("control_button_group_c1", "C1"),
                        ("control_button_group_c2", "C2"),
                        ("control_button_group_c3", "C3"),
                    ],
                ),
                natural_width=100,
            ),
            RowCellSpec(
                "toggle_group",
                "Toggles",
                80,
                12,
                make_toggle_group(
                    "control_toggle_group_cell",
                    [
                        ("control_toggle_a", "A"),
                        ("control_toggle_b", "B"),
                        ("control_toggle_c", "C"),
                    ],
                ),
                natural_width=100,
                accessibility_role="group",
                accessibility_label="Toggle group",
            ),
        ],
        col_gap=6,
        **kw,
    )

    row2 = build_horizontal_row_specs(
        [
            RowCellSpec(
                "text_area",
                "Text Area",
                160,
                5,
                make_text_area_with_input,
                accessibility_role="textbox",
                accessibility_label="Text area",
            ),
            RowCellSpec(
                "tab",
                "Tab",
                160,
                6,
                make_tab_control,
                accessibility_role="tablist",
                accessibility_label="Tab control",
            ),
            RowCellSpec(
                "data_grid",
                "Data Grid",
                120,
                7,
                make_data_grid,
                accessibility_role="table",
                accessibility_label="Data grid",
            ),
        ],
        col_gap=feature.BASICS_COL_GAP,
        **kw,
    )

    row3 = build_horizontal_row_specs(
        [
            RowCellSpec("horizontal_pair", "Horizontal Scrollbar and Slider", 56, 8, make_horiz_pair),
            RowCellSpec("vertical_pair", "Vertical Scrollbar and Slider", 140, 9, make_vert_pair),
        ],
        col_gap=16,
        **kw,
    )

    row4 = build_horizontal_row_specs(
        [
            RowCellSpec(
                "notification_panel",
                "Notification Panel",
                160,
                10,
                lambda w, h: NotificationPanelControl("control_notification_panel", Rect(0, 0, w, h), nc),
            ),
            RowCellSpec(
                "image",
                "Image",
                160,
                11,
                lambda w, h: ImageControl("control_image", Rect(0, 0, h, h), image_path, scale=True),
                target_width=160,
                target_align="left",
            ),
        ],
        col_gap=6,
        **kw,
    )

    return row1 + row2 + row3 + row4


__all__ = ["build_basics_specs"]
