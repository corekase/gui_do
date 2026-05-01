"""Controls showcase feature with grouped, varied-span layout."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from dataclasses import dataclass
from pathlib import Path

from pygame import Rect

from gui_do import (
    AnimatedImageControl,
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CellCaretLayout,
    CanvasControl,
    ColorPickerControl,
    ContextMenuItem,
    DataGridControl,
    DockPane,
    DockTabs,
    DockWorkspace,
    DockWorkspacePanel,
    DropdownControl,
    DropdownOption,
    Feature,
    FixedPatternFormatter,
    FrameAnimation,
    FrameTimer,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    LayoutManager,
    ListItem,
    ListViewControl,
    MenuBarControl,
    MenuEntry,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    NumericFormatter,
    OverlayPanelControl,
    PanelControl,
    PatternFormatter,
    ProgressBarControl,
    PropertyInspectorModel,
    PropertyInspectorPanel,
    RangeSliderControl,
    RichLabelControl,
    ScrollbarControl,
    ScrollViewControl,
    SliderControl,
    SpinnerControl,
    SplitterControl,
    SpriteSheet,
    TabControl,
    TabItem,
    TextAreaControl,
    TextInputControl,
    ToastSeverity,
    ToggleControl,
    TreeControl,
    TreeNode,
    ui_property,
)
from demo_features.feature_abstractions import add_standard_scene_menu_strip


class _ShowcaseInspectable:
    """Simple object with @ui_property decorators for the PropertyInspectorPanel showcase."""

    def __init__(self) -> None:
        self._label: str = "Showcase"
        self._value: float = 0.5
        self._active: bool = True
        self._priority: int = 1

    @property
    @ui_property(label="Label", type="str", group="Display")
    def label(self) -> str:
        return self._label

    from gui_do import PlacedControl
    def label(self, v: str) -> None:
        self._label = str(v)

    @property
    @ui_property(label="Value", type="float", min=0.0, max=1.0, group="Display")
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = float(v)

    @property
    @ui_property(label="Active", type="bool", group="State")
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, v: bool) -> None:
        self._active = bool(v)

    @property
    @ui_property(label="Priority", type="int", min=1, max=10, group="State")
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, v: int) -> None:
        self._priority = int(v)





class ControlsShowcaseFeature(Feature):
    """Render all controls except task panel/window in grouped, non-uniform layouts."""

    HOST_REQUIREMENTS = {
        "build": ("app", "scene_presentation", "control_showcase_root"),
        "configure_accessibility": ("app",),
        "on_update": ("app",),
        "prewarm": ("app",),
    }

    ROOT_MARGIN_X = 24
    ROOT_MARGIN_TOP = 24
    ROOT_MARGIN_BOTTOM = 86
    CONTENT_PADDING_X = 4
    CONTENT_PADDING_Y = 12
    REGION_GAP = 14
    INNER_GAP = 4
    LABEL_HEIGHT = 18
    LABEL_GAP = 4

    SLIDER_MINIMUM = 0.0
    SLIDER_MAXIMUM = 100.0
    SLIDER_DEFAULT_VALUE = 25.0
    SCROLLBAR_CONTENT_SIZE = 1000
    SCROLLBAR_VIEWPORT_SIZE = 240
    SCROLLBAR_DEFAULT_OFFSET = 0
    SCROLLBAR_STEP = 24

    IMAGE_PATH = "demo_features/data/images/realize.png"

    TASK_PANEL_HEIGHT = 50
    TASK_PANEL_HIDDEN_PEEK_PIXELS = 6
    TASK_PANEL_ANIMATION_STEP_PX = 8
    TASK_PANEL_BUTTON_WIDTH = 110
    TASK_PANEL_BUTTON_HEIGHT = 30
    TASK_PANEL_BUTTON_LEFT = 16
    TASK_PANEL_BUTTON_TOP_OFFSET = 10

    LAYOUT_OVERALL_ROWS_CONSTANT = 7
    LAYOUT_OVERALL_COLUMNS_CONSTANT = 2
    SHOWCASE_TAB_SPECS = (
        ("one", "One"),
        ("two", "Two"),
        ("three", "Three"),
    )
    SHOWCASE_BUTTON_TRIO_SPECS = (
        ("button", "Button 1", "control_button", "Showcase button 1"),
        ("button_2", "Button 2", "control_button_2", "Showcase button 2"),
        ("button_3", "Button 3", "control_button_3", "Showcase button 3"),
    )
    SHOWCASE_TOGGLE_TRIO_SPECS = (
        ("toggle", "Toggle 1", "control_toggle", "Showcase toggle 1"),
        ("toggle_2", "Toggle 2", "control_toggle_2", "Showcase toggle 2"),
        ("toggle_3", "Toggle 3", "control_toggle_3", "Showcase toggle 3"),
    )
    SHOWCASE_GROUP_COLUMN_SPECS = (
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    )
    SHOWCASE_GROUP_ROW_SPECS = (
        (1, True),
        (2, False),
        (3, False),
    )

    def __init__(self, rect: Rect | None = None) -> None:
        super().__init__("controls_showcase", scene_name="control_showcase")
        self.rect = Rect(rect) if rect is not None else Rect(0, 0, 0, 0)

        self.controls: list = []
        self.control_labels: list[LabelControl] = []
        from gui_do import PlacedControl
        self.placed_controls: list[PlacedControl] = []
        self._focus_controls: list = []
        self._initial_focus_control = None
        self._pending_initial_focus = False

        self.task_panel = None
        self.showcase_return_button = None
        self._showcase_notification_center: NotificationCenter | None = None
        self._indeterminate_bar: ProgressBarControl | None = None
        self._showcase_anim_ctrl: AnimatedImageControl | None = None
        self._frame_timer = FrameTimer()

    def build(self, host) -> None:
        host.control_showcase_menu_bar = add_standard_scene_menu_strip(
            host.control_showcase_root,
            host,
            control_id="control_showcase_menu_bar",
            rect=Rect(0, 0, host.control_showcase_root.rect.width, 28),
            scene_name="control_showcase",
            scenes_shown=True,
            windows_shown=True,
            tools_exclude_labels=("Open Command Palette (F5)",),
        )

        if self.rect.width <= 0 or self.rect.height <= 0:
            self.rect = self._default_rect(host)

        self._reset_collections()

        content_rect = Rect(
            self.rect.left + self.CONTENT_PADDING_X,
            self.rect.top + self.CONTENT_PADDING_Y,
            max(1, self.rect.width - (self.CONTENT_PADDING_X * 2)),
            max(1, self.rect.height - (self.CONTENT_PADDING_Y * 2)),
        )

        def slot_h(control_height: int) -> int:
            return int(control_height) + self.LABEL_HEIGHT + self.LABEL_GAP

        column_width = 320
        row_gap = 8
        col_gap = 4
        bar_control_h = 24
        text_input_control_h = 30
        text_area_rows = 4
        text_area_row_h = 28
        text_area_control_h = text_area_rows * text_area_row_h
        arrow_control_size = 32

        col0_x = content_rect.left
        col0_y = content_rect.top

        arrow_slot_h = arrow_control_size
        arrow_left_half_w = column_width // 2
        arrow_cell_w = max(20, (arrow_left_half_w - self.INNER_GAP) // 2)
        arrow_cell_h = arrow_slot_h
        arrow_group_h = (arrow_cell_h * 2) + row_gap
        from gui_do import add_group_label, place_control, place_control_unlabeled
        add_group_label(
            host.control_showcase_root,
            "arrowboxes",
            "ArrowBoxes",
            Rect(col0_x, col0_y, arrow_left_half_w, arrow_group_h),
            control_labels=self.control_labels,
        )
        arrow_row0_y = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP
        arrow_second_row_y = arrow_row0_y + arrow_cell_h + row_gap

        place_control_unlabeled(
            host.control_showcase_root,
            "arrow_up",
            ArrowBoxControl("control_arrow_up", Rect(0, 0, 1, 1), 90),
            Rect(col0_x, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow up",
            column_index=0,
            row_index=0,
            placed_controls=self.placed_controls,
            control_labels=self.control_labels,
            focus_controls=self._focus_controls,
            controls=self.controls,
        )
        place_control_unlabeled(
            host.control_showcase_root,
            "arrow_down",
            ArrowBoxControl("control_arrow_down", Rect(0, 0, 1, 1), 270),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow down",
            column_index=0,
            row_index=1,
            placed_controls=self.placed_controls,
            control_labels=self.control_labels,
            focus_controls=self._focus_controls,
            controls=self.controls,
        )
        place_control_unlabeled(
            host.control_showcase_root,
            "arrow_left",
            ArrowBoxControl("control_arrow_left", Rect(0, 0, 1, 1), 180),
            Rect(col0_x, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow left",
            column_index=0,
            row_index=2,
            placed_controls=self.placed_controls,
            control_labels=self.control_labels,
            focus_controls=self._focus_controls,
            controls=self.controls,
        )
        place_control_unlabeled(
            host.control_showcase_root,
            "arrow_right",
            ArrowBoxControl("control_arrow_right", Rect(0, 0, 1, 1), 0),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow right",
            column_index=0,
            row_index=3,
            placed_controls=self.placed_controls,
            control_labels=self.control_labels,
            focus_controls=self._focus_controls,
            controls=self.controls,
        )

        col0_row_y = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP + arrow_group_h + row_gap
        text_input_slot_h = slot_h(text_input_control_h)
        text_area_slot_h = slot_h(text_area_control_h)
        bar_slot_h = slot_h(bar_control_h)

        self._place_control(
            host,
            "text_input",
            "Text Input",
            TextInputControl("control_text_input", Rect(0, 0, 1, 1), placeholder="Type here"),
            Rect(col0_x, col0_row_y, column_width, text_input_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Text input",
            column_index=0,
            row_index=4,
        )
        col0_row_y += text_input_slot_h + row_gap

        self._place_control(
            host,
            "text_area",
            "Text Area",
            TextAreaControl(
                "control_text_area",
                Rect(0, 0, 1, 1),
                value="Heading: Notes\n- First line\n- Second line",
            ),
            Rect(col0_x, col0_row_y, column_width, text_area_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Text area",
            column_index=0,
            row_index=5,
        )
        col0_row_y += text_area_slot_h + row_gap

        self._place_control(
            host,
            "horizontal_scrollbar",
            "H. Scrollbar",
            ScrollbarControl(
                "control_horizontal_scrollbar",
                Rect(0, 0, 1, 1),
                LayoutAxis.HORIZONTAL,
                self.SCROLLBAR_CONTENT_SIZE,
                self.SCROLLBAR_VIEWPORT_SIZE,
                offset=self.SCROLLBAR_DEFAULT_OFFSET,
                step=self.SCROLLBAR_STEP,
            ),
            Rect(col0_x, col0_row_y, column_width, bar_slot_h),
            focusable=True,
            accessibility_role="scrollbar",
            accessibility_label="Horizontal scrollbar",
            column_index=0,
            row_index=6,
        )
        col0_row_y += bar_slot_h + row_gap

        self._place_control(
            host,
            "horizontal_slider",
            "H. Slider",
            SliderControl(
                "control_horizontal_slider",
                Rect(0, 0, 1, 1),
                LayoutAxis.HORIZONTAL,
                self.SLIDER_MINIMUM,
                self.SLIDER_MAXIMUM,
                self.SLIDER_DEFAULT_VALUE,
            ),
            Rect(col0_x, col0_row_y, column_width, bar_slot_h),
            focusable=True,
            accessibility_role="slider",
            accessibility_label="Horizontal slider",
            column_index=0,
            row_index=7,
        )

        col0_total_h = (col0_row_y + bar_slot_h) - col0_y

        # Column 2: vertical scrollbar + vertical slider, each full column height and 24px wide.
        col1_x = col0_x + column_width + col_gap
        vertical_slot_h = col0_total_h
        vertical_w = 24
        self._add_group_label(host, "vertical", "V.", Rect(col1_x, col0_y, (vertical_w * 2) + self.INNER_GAP, vertical_slot_h))
        vertical_controls_top = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP
        vertical_controls_h = max(1, vertical_slot_h - self.LABEL_HEIGHT - self.LABEL_GAP)
        self._place_control_unlabeled(
            host,
            "vertical_scrollbar",
            ScrollbarControl(
                "control_vertical_scrollbar",
                Rect(0, 0, 1, 1),
                LayoutAxis.VERTICAL,
                self.SCROLLBAR_CONTENT_SIZE,
                self.SCROLLBAR_VIEWPORT_SIZE,
                offset=self.SCROLLBAR_DEFAULT_OFFSET,
                step=self.SCROLLBAR_STEP,
            ),
            Rect(col1_x, vertical_controls_top, vertical_w, vertical_controls_h),
            focusable=True,
            accessibility_role="scrollbar",
            accessibility_label="Vertical scrollbar",
            column_index=1,
            row_index=0,
        )
        self._place_control_unlabeled(
            host,
            "vertical_slider",
            SliderControl(
                "control_vertical_slider",
                Rect(0, 0, 1, 1),
                LayoutAxis.VERTICAL,
                self.SLIDER_MINIMUM,
                self.SLIDER_MAXIMUM,
                self.SLIDER_DEFAULT_VALUE,
            ),
            Rect(col1_x + vertical_w + self.INNER_GAP, vertical_controls_top, vertical_w, vertical_controls_h),
            focusable=True,
            accessibility_role="slider",
            accessibility_label="Vertical slider",
            column_index=1,
            row_index=1,
        )

        # Next columns: left_lane for buttons/toggles/groups/data_grid, then a square tab column
        # (side = col0_total_h), a square image column, then remaining controls auto-stacked.
        col2_x = col1_x + (vertical_w * 2) + self.INNER_GAP + col_gap
        sq_size = col0_total_h  # each square column has width == height == col0_total_h

        avail_w = max(260, content_rect.right - col2_x)
        left_lane_w = max(160, int(avail_w * 0.22))
        left_lane = Rect(col2_x, col0_y, left_lane_w, col0_total_h)

        y = left_lane.top
        button_slot_h = slot_h(34)
        group_first_slot_h = slot_h(34)
        group_other_h = 34
        tri_w = max(48, (left_lane.width - (self.INNER_GAP * 2)) // 3)

        lane_controls_h = (
            button_slot_h + row_gap
            + button_slot_h + row_gap
            + group_first_slot_h + row_gap
            + group_other_h + row_gap
            + group_other_h
        )
        lane_layout = CellCaretLayout(
            bounds=Rect(left_lane.left, y, left_lane.width, lane_controls_h),
            cell_width=tri_w,
            cell_height=lane_controls_h,
            columns=3,
            cell_gap_x=self.INNER_GAP,
            cell_gap_y=row_gap,
            item_gap_y=row_gap,
            flow_axis="vertical",
        )
        lane_cell_layouts = {
            col_index: LayoutManager()
            for col_index in range(3)
        }
        # Each cell can host a nested LayoutManager; this keeps per-cell composition
        # extensible without changing the outer cell-caret progression behavior.
        for col_index, cell_layout in lane_cell_layouts.items():
            lane_layout.bind_layout_manager(cell_layout, col=col_index, row=0)

        for col_index, (group_key, group_letter) in enumerate(self.SHOWCASE_GROUP_COLUMN_SPECS):
            lane_layout.move_to_cell(col_index, 0)

            button_name, button_label_text, button_control_id, button_accessibility_label = self.SHOWCASE_BUTTON_TRIO_SPECS[col_index]
            self._place_control(
                host,
                button_name,
                button_label_text,
                ButtonControl(button_control_id, Rect(0, 0, 1, 1), "Button"),
                lane_layout.add(tri_w, button_slot_h),
                focusable=True,
                accessibility_role="button",
                accessibility_label=button_accessibility_label,
                column_index=2,
                row_index=col_index,
            )

            toggle_name, toggle_label_text, toggle_control_id, toggle_accessibility_label = self.SHOWCASE_TOGGLE_TRIO_SPECS[col_index]
            self._place_control(
                host,
                toggle_name,
                toggle_label_text,
                ToggleControl(toggle_control_id, Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
                lane_layout.add(tri_w, button_slot_h),
                focusable=True,
                accessibility_role="toggle",
                accessibility_label=toggle_accessibility_label,
                column_index=2,
                row_index=3 + col_index,
            )

            for option_index, with_label in self.SHOWCASE_GROUP_ROW_SPECS:
                control_name = f"button_group_{group_key}{option_index}"
                control = ButtonGroupControl(
                    f"control_button_group_{group_key}{option_index}",
                    Rect(0, 0, 1, 1),
                    f"controls_showcase_{group_key}",
                    f"{group_letter}{option_index}",
                    selected=False,
                )
                row_index = 6 + (col_index * 3) + (option_index - 1)
                option_h = group_first_slot_h if option_index == 1 else group_other_h
                placement_rect = lane_layout.add(tri_w, option_h)
                if with_label:
                    self._place_control(
                        host,
                        control_name,
                        f"Group {group_letter}",
                        control,
                        placement_rect,
                        focusable=True,
                        accessibility_role="button",
                        accessibility_label=f"Group {group_letter} option {option_index}",
                        column_index=2,
                        row_index=row_index,
                    )
                else:
                    self._place_control_unlabeled(
                        host,
                        control_name,
                        control,
                        placement_rect,
                        focusable=True,
                        accessibility_role="button",
                        accessibility_label=f"Group {group_letter} option {option_index}",
                        column_index=2,
                        row_index=row_index,
                    )

        y += lane_controls_h + row_gap

        mid_block_h = slot_h(120)
        self._place_control(
            host,
            "data_grid",
            "Data Grid",
            DataGridControl(
                "control_data_grid",
                Rect(0, 0, 1, 1),
                [
                    GridColumn(key="name", title="Name", width=max(90, int(left_lane.width * 0.58))),
                    GridColumn(key="value", title="Value", width=max(70, int(left_lane.width * 0.36))),
                ],
                [
                    GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                    GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                    GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                    GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
                ],
                row_height=24,
            ),
            Rect(left_lane.left, y, left_lane.width, mid_block_h),
            focusable=True,
            accessibility_role="table",
            accessibility_label="Data grid",
            column_index=2,
            row_index=20,
        )
        data_grid_bottom = y + mid_block_h

        # Square tab column — width == height == col0_total_h. Three tabs each showing a label.
        tab_col_x = left_lane.right + col_gap
        tab_labels = {
            tab_key: LabelControl(
                f"ctrl_tab_lbl_{tab_key}",
                Rect(0, 0, sq_size, 30),
                tab_title,
                align="left",
            )
            for tab_key, tab_title in self.SHOWCASE_TAB_SPECS
        }
        self._place_control_unlabeled(
            host,
            "tab",
            TabControl(
                "control_tab",
                Rect(0, 0, 1, 1),
                items=[
                    TabItem(tab_key, tab_title, tab_labels[tab_key])
                    for tab_key, tab_title in self.SHOWCASE_TAB_SPECS
                ],
                selected_key="one",
            ),
            Rect(tab_col_x, col0_y, sq_size, sq_size),
            focusable=True,
            accessibility_role="tablist",
            accessibility_label="Tab control",
            column_index=3,
            row_index=30,
        )

        # Square image column — same size as tab column, image is only item.
        img_col_x = tab_col_x + sq_size + col_gap
        self._place_control_unlabeled(
            host,
            "image",
            ImageControl(
                "control_image",
                Rect(0, 0, 1, 1),
                str(Path(__file__).parent.parent / self.IMAGE_PATH),
                scale=True,
            ),
            Rect(img_col_x, col0_y, sq_size, sq_size),
            focusable=False,
            column_index=4,
            row_index=40,
        )
        image_rect = Rect(img_col_x, col0_y, sq_size, sq_size)

        # Place notification panel immediately to the right of the image control (upper-right)
        notif_col_x = image_rect.right + col_gap
        notif_col_w = max(1, content_rect.right - notif_col_x)
        notif_col_y = col0_y
        notif_control_top = notif_col_y + self.LABEL_HEIGHT + self.LABEL_GAP
        notif_control_h = max(1, image_rect.bottom - notif_control_top)
        notif_slot_h = notif_control_h + self.LABEL_HEIGHT + self.LABEL_GAP
        self._showcase_notification_center = NotificationCenter(None, max_records=6)
        self._showcase_notification_center.add(
            NotificationRecord("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS)
        )
        self._showcase_notification_center.add(
            NotificationRecord("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING)
        )
        self._place_control(
            host,
            "notification_panel",
            "Notification Panel",
            NotificationPanelControl(
                "control_notification_panel",
                Rect(0, 0, 1, 1),
                self._showcase_notification_center,
            ),
            Rect(notif_col_x, notif_col_y, notif_col_w, notif_slot_h),
            focusable=False,
            column_index=5,
            row_index=41,
        )



        # New row of columns starts from the left edge at data_grid bottom + 10.
        new_row_y = data_grid_bottom + 10
        flow_bounds = Rect(
            content_rect.left,
            new_row_y,
            content_rect.width,
            max(1, content_rect.bottom - new_row_y),
        )
        flow = LayoutManager()
        flow.set_column_flow_properties(
            bounds=flow_bounds,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            column_spacing=col_gap,
            row_spacing=row_gap,
        )
        anchors = [flow.column_flow_anchor() for _ in range(8)]
        (
            col0_anchor,
            col1_anchor,
            col2_anchor,
            col3_anchor,
            col4_anchor,
            col5_anchor,
            col6_anchor,
            col7_anchor,
        ) = anchors

        new_row_col_w = min(200, col0_anchor.width)
        new_row_x0, new_row_x1, new_row_x2, new_row_x3 = [anchor.left for anchor in anchors[:4]]
        col0_y, col1_y, col2_y, col3_y = [anchor.top for anchor in anchors[:4]]

        # Column 0: ListView with selected-item label.
        list_selection_label = LabelControl(
            "lv_selected_label",
            Rect(0, 0, new_row_col_w, 22),
            "Selected: Item 1",
            align="left",
        )
        list_slot_h = slot_h(120)
        self._place_control(
            host,
            "list_view",
            "List View",
            ListViewControl(
                "control_list_view",
                Rect(0, 0, 1, 1),
                [ListItem(label=f"Item {index + 1}", value=index) for index in range(10)],
                row_height=24,
                selected_index=0,
                on_select=lambda _idx, item: setattr(list_selection_label, "text", f"Selected: {item.label}"),
            ),
            Rect(new_row_x0, col0_y, new_row_col_w, list_slot_h),
            focusable=True,
            accessibility_role="listbox",
            accessibility_label="List view",
            column_index=2,
            row_index=60,
        )
        list_view_bottom = col0_y + list_slot_h
        list_selection_label.set_rect(Rect(new_row_x0, list_view_bottom + row_gap, new_row_col_w, 22))
        host.control_showcase_root.add(list_selection_label)
        self.control_labels.append(list_selection_label)

        # Column 1: ScrollView with nested ListView and selected-item label.
        scroll_viewport_h = 120
        scroll_items = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet"]
        scroll_content_h = 24 * len(scroll_items)
        scroll_control = ScrollViewControl(
            "control_scroll_view",
            Rect(0, 0, new_row_col_w, scroll_viewport_h),
            content_width=new_row_col_w - 20,
            content_height=scroll_content_h,
            scroll_y=True,
        )
        scroll_selection_label = LabelControl("sv_selected_label", Rect(0, 0, new_row_col_w, 22), "Selected: Alpha", align="left")
        scroll_select_list = ListViewControl(
            "sv_select_list",
            Rect(0, 0, new_row_col_w - 20, scroll_content_h),
            [ListItem(label=item, value=item) for item in scroll_items],
            row_height=24,
            show_scrollbar=False,
            on_select=lambda _idx, item: setattr(scroll_selection_label, "text", f"Selected: {item.label}"),
        )
        # Managed by configure_accessibility ordering; keep out of default tab order.
        scroll_select_list.set_tab_index(-1)
        scroll_select_list.set_accessibility(role="listbox", label="Scroll view list")
        self._focus_controls.append(scroll_select_list)
        scroll_control.add(scroll_select_list, content_x=4, content_y=0)
        scroll_control.set_content_size(new_row_col_w - 20, scroll_content_h)
        scroll_slot_h = slot_h(120)
        self._place_control(
            host,
            "scroll_view",
            "Scroll View",
            scroll_control,
            Rect(new_row_x1, col1_y, new_row_col_w, scroll_slot_h),
            focusable=False,
            column_index=3,
            row_index=70,
        )
        scroll_selection_label.set_rect(Rect(new_row_x1, col1_y + scroll_slot_h + row_gap, new_row_col_w, 22))
        host.control_showcase_root.add(scroll_selection_label)
        self.control_labels.append(scroll_selection_label)

        # Column 2: rich label, then dropdown and splitter.
        rich_slot_h = slot_h(90)
        self._place_control(
            host,
            "rich_label",
            "Rich Label",
            RichLabelControl(
                "control_rich_label",
                Rect(0, 0, 1, 1),
                text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, run `deploy --env staging`, and **_ship_** after QA.",
            ),
            Rect(new_row_x2, col2_y, new_row_col_w, rich_slot_h),
            focusable=False,
            column_index=4,
            row_index=80,
        )

        rich_col_y = col2_y + rich_slot_h + row_gap
        dropdown_slot_h = slot_h(30)
        self._place_control(
            host,
            "dropdown",
            "Dropdown",
            DropdownControl(
                "control_dropdown",
                Rect(0, 0, 1, 1),
                [DropdownOption(label=f"Option {index + 1}", value=index) for index in range(4)],
                placeholder="Choose",
            ),
            Rect(new_row_x2, rich_col_y, new_row_col_w, dropdown_slot_h),
            focusable=True,
            accessibility_role="combobox",
            accessibility_label="Dropdown",
            column_index=4,
            row_index=81,
        )
        rich_col_y += dropdown_slot_h + row_gap

        splitter_slot_h = slot_h(52)
        self._place_control(
            host,
            "splitter",
            "Splitter",
            SplitterControl(
                "control_splitter",
                Rect(0, 0, 1, 1),
                axis=LayoutAxis.HORIZONTAL,
                ratio=0.5,
                min_pane_size=16,
            ),
            Rect(new_row_x2, rich_col_y, new_row_col_w, splitter_slot_h),
            focusable=True,
            accessibility_role="separator",
            accessibility_label="Splitter",
            column_index=4,
            row_index=82,
        )

        # Column 3: canvas and frame on top row, panel on the next row spanning full width.
        grid_gap = self.INNER_GAP
        cell_w = max(1, (new_row_col_w - grid_gap) // 2)
        cell_w2 = max(1, new_row_col_w - grid_gap - cell_w)
        cell_h = cell_w
        g0x = new_row_x3
        g1x = new_row_x3 + cell_w + grid_gap
        g0y = col3_y
        top_slot_h = cell_h + self.LABEL_HEIGHT + self.LABEL_GAP
        g1y = g0y + top_slot_h + row_gap
        self._place_control(
            host,
            "canvas",
            "Canvas",
            CanvasControl("control_canvas", Rect(0, 0, 1, 1), max_events=64),
            Rect(g0x, g0y, cell_w, top_slot_h),
            focusable=False,
            column_index=5,
            row_index=83,
        )
        self._place_control(
            host,
            "frame",
            "Frame",
            FrameControl("control_frame", Rect(0, 0, 1, 1), border_width=2),
            Rect(g1x, g0y, cell_w2, top_slot_h),
            focusable=False,
            column_index=5,
            row_index=84,
        )
        self._place_control(
            host,
            "panel",
            "Panel",
            PanelControl("control_panel", Rect(0, 0, 1, 1), draw_background=True),
            Rect(g0x, g1y, new_row_col_w, slot_h(68)),
            focusable=False,
            column_index=5,
            row_index=85,
        )

        # New right-side columns for recently added controls.

        # Shift columns after tree control left by one
        new_col_x = col4_anchor.left
        new_col_w = min(220, col4_anchor.width)
        col4_y = col4_anchor.top

        menu_slot_h = slot_h(28)
        self._place_control(
            host,
            "menu_bar",
            "Menu Bar",
            MenuBarControl(
                "control_menu_bar",
                Rect(0, 0, 1, 1),
                [
                    MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Save")]),
                    MenuEntry("Tools", [ContextMenuItem("Run"), ContextMenuItem("Reset")]),
                ],
            ),
            Rect(new_col_x, col4_y, new_col_w, menu_slot_h),
            focusable=True,
            accessibility_role="menubar",
            accessibility_label="Menu bar",
            column_index=4,
            row_index=90,
        )

        tree_slot_h = slot_h(150)
        self._place_control(
            host,
            "tree",
            "Tree",
            TreeControl(
                "control_tree",
                Rect(0, 0, 1, 1),
                [
                    TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                    TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")]),
                ],
            ),
            Rect(new_col_x, col4_y + menu_slot_h + row_gap, new_col_w, tree_slot_h),
            focusable=True,
            accessibility_role="tree",
            accessibility_label="Tree control",
            column_index=4,
            row_index=91,
        )

        # Now shift all subsequent columns left by one (spinner, range_slider, color_picker, overlay_panel, etc.)
        col6_x = col5_anchor.left
        col6_w = min(220, col5_anchor.width)
        col6_y = col5_anchor.top

        spinner_slot_h = slot_h(30)
        self._place_control(
            host,
            "spinner",
            "Spinner",
            SpinnerControl(
                "control_spinner",
                Rect(0, 0, col6_w, 30),
                value=25, min_value=0, max_value=100, step=1, decimals=0,
                on_change=lambda v, _r: None,
            ),
            Rect(col6_x, col6_y, col6_w, spinner_slot_h),
            focusable=True,
            column_index=5,
            row_index=100,
        )
        col6_y += spinner_slot_h + row_gap

        range_slot_h = slot_h(24)
        self._place_control(
            host,
            "range_slider",
            "Range Slider",
            RangeSliderControl(
                "control_range_slider",
                Rect(0, 0, col6_w, 24),
                min_value=0, max_value=100, low_value=20, high_value=80,
                on_change=lambda lo, hi, _r: None,
            ),
            Rect(col6_x, col6_y, col6_w, range_slot_h),
            focusable=True,
            column_index=5,
            row_index=101,
        )
        col6_y += range_slot_h + row_gap

        color_slot_h = slot_h(180)
        self._place_control(
            host,
            "color_picker",
            "Color Picker",
            ColorPickerControl(
                "control_color_picker",
                Rect(0, 0, col6_w, 180),
                color=(64, 128, 255),
                on_change=lambda c: None,
            ),
            Rect(col6_x, col6_y, col6_w, color_slot_h),
            focusable=True,
            column_index=5,
            row_index=102,
        )
        col6_y += color_slot_h + row_gap

        # OverlayPanelControl
        col7_x = col6_anchor.left
        col7_w = min(200, col6_anchor.width)
        col7_y = col6_anchor.top
        overlay_inner_h = 90
        overlay_slot_h = slot_h(overlay_inner_h)
        overlay_control_top = col7_y + self.LABEL_HEIGHT + self.LABEL_GAP
        overlay_panel = OverlayPanelControl(
            "control_overlay_panel",
            Rect(col7_x, overlay_control_top, col7_w, overlay_inner_h),
            draw_background=True,
        )
        for i, item_text in enumerate(("Overlay Item A", "Overlay Item B", "Overlay Item C")):
            child_label = LabelControl(
                f"overlay_child_{i}",
                Rect(0, 0, col7_w - 16, 22),
                item_text,
                align="left",
            )
            overlay_panel.add_at(child_label, rel_x=8, rel_y=6 + i * 26)
        self._place_control(
            host,
            "overlay_panel",
            "Overlay Panel",
            overlay_panel,
            Rect(col7_x, col7_y, col7_w, overlay_slot_h),
            focusable=False,
            column_index=6,
            row_index=110,
        )





        # Column 8: format-aware text inputs (shifted left to fill overlay panel gap)
        col8_anchor = flow.column_flow_anchor()
        col8_x = col8_anchor.left
        col8_w = min(220, col8_anchor.width)
        col8_y = col8_anchor.top

        _num_fmt = NumericFormatter(decimals=2, thousands_sep=",")

        numeric_input_slot_h = slot_h(30)
        numeric_input = _num_fmt.create_text_input(
            "control_numeric_fmt_input",
            Rect(0, 0, col8_w, 30),
            raw_value="12500",
            placeholder="0.00",
        )
        # Shift all columns from numeric format through animated image left by one column area
        # Numeric Format
        col7_anchor = flow.column_flow_anchor()
        col7_x = col7_anchor.left
        col7_w = min(220, col7_anchor.width)
        col7_y = col7_anchor.top
        self._place_control(
            host,
            "numeric_fmt_input",
            "Numeric Format",
            numeric_input,
            Rect(col7_x, col7_y, col7_w, numeric_input_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Numeric formatted text input",
            column_index=7,
            row_index=120,
        )
        col7_y += numeric_input_slot_h + row_gap


        # Pattern Format
        _pat_fmt = PatternFormatter("###-###-####")
        pattern_input_slot_h = slot_h(30)
        pattern_input = _pat_fmt.create_text_input(
            "control_pattern_fmt_input",
            Rect(0, 0, col7_w, 30),
            raw_value="5551234567",
            placeholder="###-###-####",
        )
        self._place_control(
            host,
            "pattern_fmt_input",
            "Pattern Format",
            pattern_input,
            Rect(col7_x, col7_y, col7_w, pattern_input_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Pattern formatted text input",
            column_index=7,
            row_index=121,
        )
        col7_y += pattern_input_slot_h + row_gap


        # Fixed Pattern Format
        _fixed_pat_fmt = FixedPatternFormatter("#####-####")
        fixed_pattern_input_slot_h = slot_h(30)
        fixed_pattern_input = _fixed_pat_fmt.create_text_input(
            "control_fixed_pattern_fmt_input",
            Rect(0, 0, col7_w, 30),
            raw_value="941010001",
            placeholder="#####-####",
        )
        self._place_control(
            host,
            "fixed_pattern_fmt_input",
            "Fixed Pattern Format",
            fixed_pattern_input,
            Rect(col7_x, col7_y, col7_w, fixed_pattern_input_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Fixed pattern formatted text input",
            column_index=7,
            row_index=122,
        )
        col7_y += fixed_pattern_input_slot_h + row_gap

        # Dock Workspace Panel
        _showcase_dock = DockWorkspace(
            DockTabs(
                "sc_dock_tabs",
                panes=[
                    DockPane("editor", "Editor"),
                    DockPane("preview", "Preview"),
                    DockPane("console", "Console"),
                ],
            )
        )
        dock_slot_h = slot_h(36)
        prop_inner_h = 160
        prop_slot_h = slot_h(prop_inner_h)

        # Dock Workspace Panel
        col9_anchor = flow.column_flow_anchor()
        col9_x = col9_anchor.left
        col9_w = min(260, col9_anchor.width)
        col9_y = col9_anchor.top
        self._place_control(
            host,
            "dock_workspace_panel",
            "Dock Workspace",
            DockWorkspacePanel(
                "control_dock_workspace_panel",
                Rect(0, 0, col9_w, 36),
                _showcase_dock,
            ),
            Rect(col9_x, col9_y, col9_w, dock_slot_h),
            focusable=True,
            accessibility_role="tablist",
            accessibility_label="Dock workspace panel",
            column_index=9,
            row_index=130,
        )
        col9_y += dock_slot_h + row_gap

        # Property Inspector
        _showcase_inspectable = _ShowcaseInspectable()
        prop_control_top = col9_y + self.LABEL_HEIGHT + self.LABEL_GAP
        prop_inspector = PropertyInspectorPanel(
            "control_property_inspector",
            Rect(col9_x, prop_control_top, col9_w, prop_inner_h),
            PropertyInspectorModel(_showcase_inspectable),
        )
        self._place_control(
            host,
            "property_inspector",
            "Property Inspector",
            prop_inspector,
            Rect(col9_x, col9_y, col9_w, prop_slot_h),
            focusable=False,
            column_index=9,
            row_index=131,
        )

        # ProgressBarControl (determinate + indeterminate) and AnimatedImageControl.
        col10_anchor = flow.column_flow_anchor()
        col10_x = col10_anchor.left
        col10_w = min(220, col10_anchor.width)
        col10_y = col10_anchor.top

        progress_h = 20
        progress_slot_h = slot_h(progress_h)
        self._place_control(
            host,
            "progress_bar",
            "Progress Bar",
            ProgressBarControl(
                "control_progress_bar",
                Rect(0, 0, col10_w, progress_h),
                value=0.65,
            ),
            Rect(col10_x, col10_y, col10_w, progress_slot_h),
            focusable=False,
            column_index=10,
            row_index=140,
        )
        col10_y += progress_slot_h + row_gap

        indeterminate_h = 20
        indeterminate_slot_h = slot_h(indeterminate_h)
        indeterminate_bar = ProgressBarControl(
            "control_progress_bar_indeterminate",
            Rect(0, 0, col10_w, indeterminate_h),
            indeterminate=True,
        )
        self._indeterminate_bar = indeterminate_bar
        self._place_control(
            host,
            "progress_bar_indeterminate",
            "Progress (Marquee)",
            indeterminate_bar,
            Rect(col10_x, col10_y, col10_w, indeterminate_slot_h),
            focusable=False,
            column_index=10,
            row_index=141,
        )
        col10_y += indeterminate_slot_h + row_gap

        # AnimatedImageControl — four-frame programmatic atlas.
        import pygame as _pygame
        _FRAME_W, _FRAME_H = 32, 32
        _atlas = _pygame.Surface((_FRAME_W * 4, _FRAME_H), flags=_pygame.SRCALPHA)
        for _fi, _color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
            _atlas.fill(_color, Rect(_fi * _FRAME_W, 0, _FRAME_W, _FRAME_H))
        _sheet = SpriteSheet(_atlas, frame_w=_FRAME_W, frame_h=_FRAME_H)
        _anim = FrameAnimation(_sheet, frames=list(range(4)), fps=1, loop=True)
        anim_ctrl = AnimatedImageControl(
            "control_animated_image",
            Rect(0, 0, col10_w, 48),
            animation=_anim,
            scale=True,
        )
        self._showcase_anim_ctrl = anim_ctrl
        anim_slot_h = slot_h(48)
        self._place_control(
            host,
            "animated_image",
            "Animated Image",
            anim_ctrl,
            Rect(col10_x, col10_y, col10_w, anim_slot_h),
            focusable=False,
            column_index=10,
            row_index=142,
        )

        self._build_scene_task_panel(host)

        if self._focus_controls:
            self._initial_focus_control = self._focus_controls[0]
            self._pending_initial_focus = True

    def configure_accessibility(self, _host, tab_index_start: int) -> int:
        next_index = int(tab_index_start)
        for control in self._focus_controls:
            if not control.visible or not control.enabled:
                continue
            control.set_tab_index(next_index)
            next_index += 1
        return next_index

    def on_update(self, host) -> None:
        dt = self._frame_timer.tick()

        if self._indeterminate_bar is not None and self._indeterminate_bar.visible:
            self._indeterminate_bar.tick(dt)
        if self._showcase_anim_ctrl is not None and self._showcase_anim_ctrl.visible:
            self._showcase_anim_ctrl.animation.update(dt)
            self._showcase_anim_ctrl.invalidate()

        if not self._pending_initial_focus:
            return
        if host.app.active_scene_name != self.scene_name:
            return
        target = self._initial_focus_control
        if target is None:
            self._pending_initial_focus = False
            return
        if not host.app.scene.contains(target) or not target.visible or not target.enabled:
            self._pending_initial_focus = False
            return
        host.app.focus.set_focus(target)
        self._pending_initial_focus = False

    def prewarm(self, _host, surface, theme) -> None:
        for control in [*self.control_labels, *self.controls, self.task_panel, self.showcase_return_button]:
            if control is None:
                continue
            control.draw(surface, theme)

    def _place_control(
        self,
        host,
        name: str,
        label_text: str,
        control,
        control_rect: Rect,
        *,
        focusable: bool,
        accessibility_role: str | None = None,
        accessibility_label: str | None = None,
        column_index: int,
        row_index: int,
    ) -> None:
        # Treat incoming rect as a full slot and reserve explicit vertical space for label + control.
        label_rect = Rect(control_rect.left, control_rect.top, control_rect.width, self.LABEL_HEIGHT)
        control_top = control_rect.top + self.LABEL_HEIGHT + self.LABEL_GAP
        control_height = max(1, control_rect.height - self.LABEL_HEIGHT - self.LABEL_GAP)
        actual_control_rect = Rect(control_rect.left, control_top, control_rect.width, control_height)
        label = LabelControl(f"controls_showcase_label_{name}", label_rect, label_text, align="left")
        self._register_placed_control(
            host,
            name,
            control,
            actual_control_rect,
            label,
            focusable=focusable,
            accessibility_role=accessibility_role,
            accessibility_label=accessibility_label,
            column_index=column_index,
            row_index=row_index,
        )

    def _place_control_unlabeled(
        self,
        host,
        name: str,
        control,
        control_rect: Rect,
        *,
        focusable: bool,
        accessibility_role: str | None = None,
        accessibility_label: str | None = None,
        column_index: int,
        row_index: int,
    ) -> None:
        self._register_placed_control(
            host,
            name,
            control,
            Rect(control_rect),
            None,
            focusable=focusable,
            accessibility_role=accessibility_role,
            accessibility_label=accessibility_label,
            column_index=column_index,
            row_index=row_index,
        )

    def _register_placed_control(
        self,
        host,
        name: str,
        control,
        actual_control_rect: Rect,
        label: LabelControl | None,
        *,
        focusable: bool,
        accessibility_role: str | None,
        accessibility_label: str | None,
        column_index: int,
        row_index: int,
    ) -> None:
        if label is not None:
            host.control_showcase_root.add(label)
            self.control_labels.append(label)

        # Use control geometry APIs so controls can synchronize derived internals
        # (for example ScrollView child screen rect projections) on placement.
        control.set_rect(actual_control_rect)
        control.enabled = True

        if accessibility_role is not None and accessibility_label is not None:
            control.set_accessibility(role=accessibility_role, label=accessibility_label)

        if focusable:
            self._focus_controls.append(control)
        else:
            control.set_tab_index(-1)

        host.control_showcase_root.add(control)
        self.controls.append(control)
        from gui_do import PlacedControl
        self.placed_controls.append(
            PlacedControl(
                control=control,
                label=label,
                name=name,
                column_index=column_index,
                row_index=row_index,
            )
        )

    def _add_group_label(self, host, name: str, text: str, group_rect: Rect) -> None:
        label = LabelControl(
            f"controls_showcase_group_label_{name}",
            Rect(group_rect.left, group_rect.top, group_rect.width, self.LABEL_HEIGHT),
            text,
            align="left",
        )
        host.control_showcase_root.add(label)
        self.control_labels.append(label)

    def _default_rect(self, host) -> Rect:
        screen_rect = getattr(host, "screen_rect", None)
        if screen_rect is None:
            screen = getattr(host, "screen", None)
            if screen is not None:
                screen_rect = screen.get_rect()
        if screen_rect is None:
            return Rect(0, 0, 1, 1)

        left = int(self.ROOT_MARGIN_X)
        top = int(self.ROOT_MARGIN_TOP)
        width = max(1, int(screen_rect.width - (self.ROOT_MARGIN_X * 2)))
        height = max(1, int(screen_rect.height - self.ROOT_MARGIN_TOP - self.ROOT_MARGIN_BOTTOM))
        return Rect(left, top, width, height)

    def _reset_collections(self) -> None:
        self.controls = []
        self.control_labels = []
        self.placed_controls = []
        self._focus_controls = []

    def _build_scene_task_panel(self, host) -> None:
        self.task_panel = host.scene_presentation.ensure_scene_task_panel(
            self.scene_name,
            control_id="control_showcase_task_panel",
            height=self.TASK_PANEL_HEIGHT,
            hidden_peek_pixels=self.TASK_PANEL_HIDDEN_PEEK_PIXELS,
            animation_step_px=self.TASK_PANEL_ANIMATION_STEP_PX,
            dock_bottom=True,
            auto_hide=True,
        )

        return_rect = Rect(
            self.TASK_PANEL_BUTTON_LEFT,
            self.task_panel.rect.top + self.TASK_PANEL_BUTTON_TOP_OFFSET,
            self.TASK_PANEL_BUTTON_WIDTH,
            self.TASK_PANEL_BUTTON_HEIGHT,
        )

        self.showcase_return_button = self.task_panel.add(
            ButtonControl(
                "showcase_return",
                return_rect,
                "Return",
                (
                    host.go_to_main
                    if hasattr(host, "go_to_main")
                    else (
                        lambda: (
                            host.scene_transitions.go("main")
                            if hasattr(host, "scene_transitions")
                            else host.app.switch_scene("main")
                        )
                    )
                ),
                style="angle",
            )
        )

        self.showcase_return_button.set_accessibility(role="button", label="Return to main")
        # Keep showcase Tab traversal within the feature surface; task panel
        # actions remain clickable but are not part of feature focus cycling.
        self.showcase_return_button.set_tab_index(-1)
