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
    BreadcrumbControl,
    BreadcrumbItem,
    ButtonControl,
    ButtonGroupControl,
    CellCaretLayout,
    CanvasControl,
    ChipInputControl,
    ColorPickerControl,
    ContextMenuItem,
    DataGridControl,
    DatePickerControl,
    DockPane,
    DockTabs,
    DockWorkspace,
    DockWorkspacePanel,
    DropdownControl,
    DropdownOption,
    ExpanderControl,
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
    SplitButtonControl,
    SplitButtonOption,
    SplitterControl,
    SpriteSheet,
    TabControl,
    TabItem,
    TextAreaControl,
    TextInputControl,
    TimePickerControl,
    ToastSeverity,
    ToggleControl,
    ToolbarControl,
    ToolbarItem,
    TreeControl,
    TreeNode,
    StatusBarControl,
    StatusSlot,
    ui_property,
)
from gui_do.features.data_driven_runtime import add_standard_scene_menu_strip


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
    CATEGORY_TAB_STRIP_HEIGHT = 34
    CATEGORY_TAB_STRIP_GAP = 8

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
    SHOWCASE_CATEGORY_TABS = (
        ("basics", "Basics"),
        ("data", "Data"),
        ("advanced", "Advanced"),
        ("extended", "Extended"),
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
        self._category_tabs: TabControl | None = None
        self._active_category_key: str = "basics"
        self._category_content_bounds: Rect = Rect(0, 0, 1, 1)
        self._showcase_root = None
        self._basics_aux_labels: dict[str, LabelControl] = {}
        self._frame_timer = FrameTimer()

    def build(self, host) -> None:
        self._showcase_root = host.control_showcase_root
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

        # Top-level category tabs drive which control groups are visible and interactive.
        tab_strip_h = int(self.CATEGORY_TAB_STRIP_HEIGHT)
        tab_strip_gap = int(self.CATEGORY_TAB_STRIP_GAP)
        category_tabs = TabControl(
            "control_showcase_category_tabs",
            Rect(content_rect.left, content_rect.top, content_rect.width, tab_strip_h),
            items=[
                TabItem(key=key, label=label)
                for key, label in self.SHOWCASE_CATEGORY_TABS
            ],
            selected_key=self._active_category_key,
            on_change=lambda key: self._set_active_category(host, key),
        )
        category_tabs.set_accessibility(role="tablist", label="Showcase categories")
        host.control_showcase_root.add(category_tabs)
        self._category_tabs = category_tabs
        self.controls.append(category_tabs)
        self._focus_controls.append(category_tabs)

        content_rect = Rect(
            content_rect.left,
            content_rect.top + tab_strip_h + tab_strip_gap,
            content_rect.width,
            max(1, content_rect.height - tab_strip_h - tab_strip_gap),
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

        # Reserve bottom space for the task panel so per-tab reflow does not
        # collide with docked task controls.
        self._category_content_bounds = Rect(
            content_rect.left,
            content_rect.top,
            content_rect.width,
            max(1, content_rect.height - self.TASK_PANEL_HEIGHT - row_gap),
        )

        col0_x = content_rect.left
        col0_y = content_rect.top

        arrow_slot_h = arrow_control_size
        arrow_left_half_w = column_width // 2
        arrow_cell_w = max(20, (arrow_left_half_w - self.INNER_GAP) // 2)
        arrow_cell_h = arrow_slot_h
        arrow_group_h = (arrow_cell_h * 2) + row_gap
        _agl = LabelControl(
            "controls_showcase_group_label_arrowboxes",
            Rect(col0_x, col0_y, arrow_left_half_w, self.LABEL_HEIGHT),
            "ArrowBoxes", align="left",
        )
        host.control_showcase_root.add(_agl)
        self.control_labels.append(_agl)
        arrow_row0_y = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP
        arrow_second_row_y = arrow_row0_y + arrow_cell_h + row_gap

        self._place_control_unlabeled(
            host, "arrow_up",
            ArrowBoxControl("control_arrow_up", Rect(0, 0, 1, 1), 90),
            Rect(col0_x, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True, accessibility_role="button", accessibility_label="Arrow up",
            column_index=0, row_index=0,
        )
        self._place_control_unlabeled(
            host, "arrow_down",
            ArrowBoxControl("control_arrow_down", Rect(0, 0, 1, 1), 270),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True, accessibility_role="button", accessibility_label="Arrow down",
            column_index=0, row_index=1,
        )
        self._place_control_unlabeled(
            host, "arrow_left",
            ArrowBoxControl("control_arrow_left", Rect(0, 0, 1, 1), 180),
            Rect(col0_x, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True, accessibility_role="button", accessibility_label="Arrow left",
            column_index=0, row_index=2,
        )
        self._place_control_unlabeled(
            host, "arrow_right",
            ArrowBoxControl("control_arrow_right", Rect(0, 0, 1, 1), 0),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True, accessibility_role="button", accessibility_label="Arrow right",
            column_index=0, row_index=3,
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
            "Horizontal Scrollbar",
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
            "Horizontal Slider",
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
        _vgl = LabelControl(
            "controls_showcase_group_label_vertical",
            Rect(col1_x, col0_y, (vertical_w * 2) + self.INNER_GAP, self.LABEL_HEIGHT),
            "V.", align="left",
        )
        host.control_showcase_root.add(_vgl)
        self.control_labels.append(_vgl)
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

        section_top = col6_anchor.top + col6_anchor.height + row_gap
        section_bounds = Rect(
            content_rect.left,
            section_top,
            content_rect.width,
            max(1, content_rect.bottom - section_top),
        )
        section_flow = LayoutManager()
        section_flow.set_column_flow_properties(
            bounds=section_bounds,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            column_spacing=col_gap,
            row_spacing=row_gap,
        )

        # Column 0: format-aware text inputs.
        col7_anchor = section_flow.column_flow_anchor()
        col7_x = col7_anchor.left
        col7_w = min(220, col7_anchor.width)
        col7_y = col7_anchor.top

        formatted_input_specs = (
            (
                "numeric_fmt_input",
                "Numeric Format",
                NumericFormatter(decimals=2, thousands_sep=","),
                "control_numeric_fmt_input",
                "12500",
                "0.00",
                "Numeric formatted text input",
                120,
            ),
            (
                "pattern_fmt_input",
                "Pattern Format",
                PatternFormatter("###-###-####"),
                "control_pattern_fmt_input",
                "5551234567",
                "###-###-####",
                "Pattern formatted text input",
                121,
            ),
            (
                "fixed_pattern_fmt_input",
                "Fixed Pattern Format",
                FixedPatternFormatter("#####-####"),
                "control_fixed_pattern_fmt_input",
                "941010001",
                "#####-####",
                "Fixed pattern formatted text input",
                122,
            ),
        )
        for (
            name,
            label_text,
            formatter,
            control_id,
            raw_value,
            placeholder,
            accessibility_label,
            row_index,
        ) in formatted_input_specs:
            col7_y = self._place_formatted_text_input(
                host,
                name=name,
                label_text=label_text,
                formatter=formatter,
                control_id=control_id,
                raw_value=raw_value,
                placeholder=placeholder,
                x=col7_x,
                y=col7_y,
                width=col7_w,
                row_gap=row_gap,
                column_index=7,
                row_index=row_index,
                accessibility_label=accessibility_label,
            )

        # Column 1 in this row: Dock workspace and property inspector.
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

        col9_anchor = section_flow.column_flow_anchor()
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

        # Column 2 in this row: progress controls and animated image.
        col10_anchor = section_flow.column_flow_anchor()
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

        # ---------------------------------------------------------------
        # New controls section — placed below the tallest control column in
        # the previous section so controls never overlap.
        # ---------------------------------------------------------------
        prev_section_bottom = max(
            col7_y,
            col9_y + prop_slot_h,
            col10_y + anim_slot_h,
        )
        new_ctrl_section_top = prev_section_bottom + row_gap
        nc_bounds = Rect(
            content_rect.left,
            new_ctrl_section_top,
            content_rect.width,
            max(1, content_rect.bottom - new_ctrl_section_top),
        )
        nc_flow = LayoutManager()
        nc_flow.set_column_flow_properties(
            bounds=nc_bounds,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            column_spacing=col_gap,
            row_spacing=row_gap,
        )
        nc0 = nc_flow.column_flow_anchor()
        nc1 = nc_flow.column_flow_anchor()
        nc2 = nc_flow.column_flow_anchor()
        nc3 = nc_flow.column_flow_anchor()

        nc_w = min(220, nc0.width)
        nc_slot_h = slot_h(36)

        # Toolbar
        self._place_control(
            host,
            "toolbar",
            "Toolbar",
            ToolbarControl(
                "control_toolbar",
                Rect(0, 0, nc_w, 36),
                items=[
                    ToolbarItem(label="Cut", action_id="cut"),
                    ToolbarItem(label="Copy", action_id="copy"),
                    ToolbarItem(separator=True),
                    ToolbarItem(label="Paste", action_id="paste"),
                ],
            ),
            Rect(nc0.left, nc0.top, nc_w, nc_slot_h),
            focusable=True,
            accessibility_role="toolbar",
            accessibility_label="Toolbar",
            column_index=11,
            row_index=150,
        )

        # Status Bar
        status_bar_slot_h = slot_h(24)
        self._place_control(
            host,
            "status_bar",
            "Status Bar",
            StatusBarControl(
                "control_status_bar",
                Rect(0, 0, nc_w, 24),
                slots=[
                    StatusSlot("status", "Ready", width=80),
                    StatusSlot("line", "Ln 1", width=50, separator_after=True),
                    StatusSlot("col", "Col 1", width=50),
                ],
            ),
            Rect(nc0.left, nc0.top + nc_slot_h + row_gap, nc_w, status_bar_slot_h),
            focusable=False,
            accessibility_role="status",
            accessibility_label="Status bar",
            column_index=11,
            row_index=151,
        )

        # Expander
        expander_slot_h = slot_h(80)
        self._place_control(
            host,
            "expander",
            "Expander",
            ExpanderControl(
                "control_expander",
                Rect(0, 0, nc_w, 80),
                title="Details",
                body_height=50,
            ),
            Rect(nc1.left, nc1.top, nc_w, expander_slot_h),
            focusable=True,
            accessibility_role="group",
            accessibility_label="Expander",
            column_index=12,
            row_index=152,
        )

        # Breadcrumb
        breadcrumb_slot_h = slot_h(28)
        self._place_control(
            host,
            "breadcrumb",
            "Breadcrumb",
            BreadcrumbControl(
                "control_breadcrumb",
                Rect(0, 0, nc_w, 28),
                items=[
                    BreadcrumbItem(label="Home", value="home"),
                    BreadcrumbItem(label="Files", value="files"),
                    BreadcrumbItem(label="Documents", value="documents"),
                ],
            ),
            Rect(nc2.left, nc2.top, nc_w, breadcrumb_slot_h),
            focusable=True,
            accessibility_role="navigation",
            accessibility_label="Breadcrumb navigation",
            column_index=13,
            row_index=153,
        )

        # Split Button
        split_slot_h = slot_h(32)
        self._place_control(
            host,
            "split_button",
            "Split Button",
            SplitButtonControl(
                "control_split_button",
                Rect(0, 0, nc_w, 32),
                label="Save",
                options=[
                    SplitButtonOption(label="Save As...", on_click=lambda: None),
                    SplitButtonOption(label="Save All", on_click=lambda: None),
                ],
            ),
            Rect(nc2.left, nc2.top + breadcrumb_slot_h + row_gap, nc_w, split_slot_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Split button",
            column_index=13,
            row_index=154,
        )

        # Chip Input
        chip_slot_h = slot_h(36)
        self._place_control(
            host,
            "chip_input",
            "Chip Input",
            ChipInputControl(
                "control_chip_input",
                Rect(0, 0, nc_w, 36),
                placeholder="Add tag...",
                values=["Python", "GUI"],
            ),
            Rect(nc3.left, nc3.top, nc_w, chip_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Chip input",
            column_index=14,
            row_index=155,
        )

        # Time Picker
        time_slot_h = slot_h(32)
        self._place_control(
            host,
            "time_picker",
            "Time Picker",
            TimePickerControl(
                "control_time_picker",
                Rect(0, 0, nc_w, 32),
                hour=9, minute=30,
            ),
            Rect(nc3.left, nc3.top + chip_slot_h + row_gap, nc_w, time_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Time picker",
            column_index=14,
            row_index=156,
        )

        # Date Picker
        date_slot_h = slot_h(32)
        self._place_control(
            host,
            "date_picker",
            "Date Picker",
            DatePickerControl(
                "control_date_picker",
                Rect(0, 0, nc_w, 32),
            ),
            Rect(nc3.left, nc3.top + chip_slot_h + row_gap + time_slot_h + row_gap, nc_w, date_slot_h),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Date picker",
            column_index=14,
            row_index=157,
        )

        self._build_scene_task_panel(host)

        # Apply initial tab category visibility after all placements are registered.
        self._apply_category_visibility(host)

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

        # Popup-capable controls draw their popup in their own draw pass.
        # Keep any currently-open popup control at the end of the root child
        # list so popup visuals render on top.
        self._promote_open_popup_controls(host)

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
        slot_rect: Rect,
        *,
        focusable: bool,
        accessibility_role: str | None = None,
        accessibility_label: str | None = None,
        column_index: int,
        row_index: int,
    ) -> None:
        from gui_do import PlacedControl
        label = LabelControl(
            f"controls_showcase_label_{name}",
            Rect(slot_rect.left, slot_rect.top, slot_rect.width, self.LABEL_HEIGHT),
            label_text, align="left",
        )
        ctrl_rect = Rect(
            slot_rect.left, slot_rect.top + self.LABEL_HEIGHT + self.LABEL_GAP,
            slot_rect.width, max(1, slot_rect.height - self.LABEL_HEIGHT - self.LABEL_GAP),
        )
        control.set_rect(ctrl_rect)
        control.enabled = True
        if accessibility_role and accessibility_label:
            control.set_accessibility(role=accessibility_role, label=accessibility_label)
        if focusable:
            self._focus_controls.append(control)
        else:
            control.set_tab_index(-1)
        host.control_showcase_root.add(label)
        host.control_showcase_root.add(control)
        self.control_labels.append(label)
        self.controls.append(control)
        self.placed_controls.append(PlacedControl(
            control=control, label=label, name=name,
            column_index=column_index, row_index=row_index,
        ))

    def _place_formatted_text_input(
        self,
        host,
        *,
        name: str,
        label_text: str,
        formatter,
        control_id: str,
        raw_value: str,
        placeholder: str,
        x: int,
        y: int,
        width: int,
        row_gap: int,
        column_index: int,
        row_index: int,
        accessibility_label: str,
    ) -> int:
        control_height = 30
        input_slot_h = control_height + self.LABEL_HEIGHT + self.LABEL_GAP
        text_input = formatter.create_text_input(
            str(control_id),
            Rect(0, 0, int(width), control_height),
            raw_value=str(raw_value),
            placeholder=str(placeholder),
        )
        self._place_control(
            host, name, label_text, text_input,
            Rect(int(x), int(y), int(width), int(input_slot_h)),
            focusable=True, accessibility_role="textbox",
            accessibility_label=accessibility_label,
            column_index=column_index, row_index=row_index,
        )
        return int(y) + int(input_slot_h) + int(row_gap)

    def _place_control_unlabeled(
        self,
        host,
        name: str,
        control,
        ctrl_rect: Rect,
        *,
        focusable: bool,
        accessibility_role: str | None = None,
        accessibility_label: str | None = None,
        column_index: int,
        row_index: int,
    ) -> None:
        from gui_do import PlacedControl
        control.set_rect(Rect(ctrl_rect))
        control.enabled = True
        if accessibility_role and accessibility_label:
            control.set_accessibility(role=accessibility_role, label=accessibility_label)
        if focusable:
            self._focus_controls.append(control)
        else:
            control.set_tab_index(-1)
        host.control_showcase_root.add(control)
        self.controls.append(control)
        self.placed_controls.append(PlacedControl(
            control=control, label=None, name=name,
            column_index=column_index, row_index=row_index,
        ))

    def _category_for_row(self, row_index: int) -> str:
        if row_index < 60:
            return "basics"
        if row_index < 100:
            return "data"
        if row_index < 140:
            return "advanced"
        return "extended"

    # Labels belonging to grouped family cells that must stay hidden in the Basics tab
    # (each family shows one header label only; per-item labels are suppressed).
    _BASICS_SUPPRESSED_LABEL_NAMES: frozenset[str] = frozenset({
        "button_2", "button_3",
        "toggle_2", "toggle_3",
        "button_group_a2", "button_group_a3",
        "button_group_b2", "button_group_b3",
        "button_group_c2", "button_group_c3",
    })

    def _set_active_category(self, host, key: str) -> None:
        valid_keys = {k for k, _ in self.SHOWCASE_CATEGORY_TABS}
        if key not in valid_keys:
            return
        if self._active_category_key == key:
            return
        self._active_category_key = key
        self._apply_category_visibility(host)

    def _apply_category_visibility(self, host) -> None:
        active_key = self._active_category_key
        self._relayout_category(active_key)

        # Compute the set of labels that are legitimately owned by placed controls.
        # Aux labels (vertical scrollbar/slider) are only valid on the basics tab;
        # on other tabs they fall through to the orphan sweep and get hidden.
        matched_labels = {p.label for p in self.placed_controls if p.label is not None}
        if active_key == "basics":
            matched_labels.update(self._basics_aux_labels.values())

        for placed in self.placed_controls:
            show = self._category_for_row(int(placed.row_index)) == active_key
            placed.control.visible = show
            placed.control.enabled = show
            if placed.label is not None:
                # Suppress duplicate family-member labels in the Basics tab —
                # those cells show a single header label instead.
                show_label = show and not (
                    active_key == "basics"
                    and str(placed.name) in self._BASICS_SUPPRESSED_LABEL_NAMES
                )
                placed.label.visible = show_label
                placed.label.enabled = show_label

        # Hide any orphan labels (group headers and stale labels not matched to a visible
        # placed control). Aux labels have their visibility managed by the scroll relayout.
        for label in self.control_labels:
            if label not in matched_labels:
                label.visible = False
                label.enabled = False

        # Refresh tab-index sequence for the now-visible set.
        try:
            host.app.configure_features_accessibility(host, 0)
        except Exception:
            pass

        # If current focus became hidden, park focus on the category tab strip.
        focused = getattr(host.app.focus, "focused", None)
        if focused is not None and not getattr(focused, "visible", True):
            if self._category_tabs is not None and self._category_tabs.visible and self._category_tabs.enabled:
                host.app.focus.set_focus(self._category_tabs)

    def _relayout_category(self, category_key: str) -> None:
        bounds = Rect(self._category_content_bounds)
        if bounds.width <= 0 or bounds.height <= 0:
            return
        items = [
            p for p in self.placed_controls
            if self._category_for_row(int(p.row_index)) == category_key
        ]
        if not items:
            return
        if category_key == "basics":
            self._relayout_basics(bounds, items)
        else:
            self._relayout_grid_items(category_key, bounds, items)

    def _relayout_basics(self, bounds: Rect, items: list) -> None:
        items_by_name = {str(item.name): item for item in items}
        col_gap = 8
        row_gap = 8
        label_h = 16
        label_gap = 2

        arrow_names = ["arrow_up", "arrow_down", "arrow_left", "arrow_right"]
        horizontal_names = ["horizontal_scrollbar", "horizontal_slider"]
        vertical_names = ["vertical_scrollbar", "vertical_slider"]
        button_names = ["button", "button_2", "button_3"]
        toggle_names = ["toggle", "toggle_2", "toggle_3"]
        group_names = sorted(
            [str(item.name) for item in items if str(item.name).startswith("button_group_")],
            key=lambda name: (
                name.split("_")[-1][0] if name.split("_")[-1] else "",
                int(name.split("_")[-1][1:]) if name.split("_")[-1][1:].isdigit() else 0,
            ),
        )
        special_names = set(arrow_names + horizontal_names + vertical_names + button_names + toggle_names + group_names)

        # Top row: compact 2x2 arrow grid only.
        top_cols = 3
        top_cell_w = max(140, (bounds.width - (col_gap * (top_cols - 1))) // top_cols)
        top_y = bounds.top

        arrow_x = bounds.left

        # Arrow boxes: compact 2x2 square grid centered in first cell.
        arrow_side = max(24, min(30, (top_cell_w - col_gap) // 2))
        arrow_grid_w = (arrow_side * 2) + col_gap
        arrow_start_x = arrow_x + max(0, (top_cell_w - arrow_grid_w) // 2)
        arrow_positions = {
            "arrow_up": (arrow_start_x, top_y),
            "arrow_down": (arrow_start_x + arrow_side + col_gap, top_y),
            "arrow_left": (arrow_start_x, top_y + arrow_side + row_gap),
            "arrow_right": (arrow_start_x + arrow_side + col_gap, top_y + arrow_side + row_gap),
        }
        for name in arrow_names:
            placed = items_by_name.get(name)
            if placed is None:
                continue
            x, y = arrow_positions[name]
            placed.control.set_rect(Rect(x, y, arrow_side, arrow_side))
            if placed.label is not None:
                placed.label.visible = False
                placed.label.enabled = False

        top_block_h = (arrow_side * 2) + row_gap
        section_y = top_y + top_block_h + row_gap

        # Buttons/toggles/groups: each family shares one explicit cell.
        grouped_families: list[tuple[str, list]] = []
        button_family = [items_by_name[name] for name in button_names if name in items_by_name]
        if button_family:
            grouped_families.append(("Buttons", button_family))
        toggle_family = [items_by_name[name] for name in toggle_names if name in items_by_name]
        if toggle_family:
            grouped_families.append(("Toggles", toggle_family))

        group_families: list[tuple[str, list]] = []
        for family_key in ("a", "b", "c"):
            family_items = [
                items_by_name[name]
                for name in group_names
                if name in items_by_name and name.split("_")[-1].startswith(family_key)
            ]
            if family_items:
                group_families.append((f"Group {family_key.upper()}", family_items))

        if grouped_families:
            group_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top)))
            section_y = self._relayout_basics_group_cells(group_bounds, grouped_families, col_count=max(1, len(grouped_families)))

        if group_families:
            group_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top)))
            section_y = self._relayout_basics_group_cells(group_bounds, group_families, col_count=3)

        # Reserve the final row for horizontal/vertical scroll cells.
        scroll_section_h = 184
        flow_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top) - scroll_section_h - row_gap))

        remaining = [item for item in items if str(item.name) not in special_names]
        bottom_y = section_y
        if remaining:
            bottom_y = self._relayout_grid_items("basics", flow_bounds, remaining)

        scroll_bounds = Rect(bounds.left, bottom_y, bounds.width, scroll_section_h)
        self._relayout_basics_scroll_cells(scroll_bounds, items_by_name, horizontal_names, vertical_names)
        self._reorder_basics_focus_controls(
            items_by_name, remaining,
            arrow_names, button_names, toggle_names,
            group_names, horizontal_names, vertical_names,
        )

    def _reorder_basics_focus_controls(
        self,
        items_by_name: dict,
        remaining: list,
        arrow_names: list,
        button_names: list,
        toggle_names: list,
        group_names: list,
        horizontal_names: list,
        vertical_names: list,
    ) -> None:
        """Rebuild _focus_controls so Basics-tab focus cycles in cell-visual order:
        arrows (2x2), buttons, toggles, group A/B/C, remaining grid items
        (sorted by row then column), horizontal scroll, vertical scroll.
        Category tabs and all non-Basics controls keep their existing relative order."""
        focus_id_set = set(id(c) for c in self._focus_controls)

        def _collect(names: list) -> list:
            result = []
            for name in names:
                placed = items_by_name.get(name)
                if placed is not None and id(placed.control) in focus_id_set:
                    result.append(placed.control)
            return result

        basics_ordered = (
            _collect(arrow_names)
            + _collect(button_names)
            + _collect(toggle_names)
            + _collect(group_names)
        )
        sorted_remaining = sorted(
            remaining,
            key=lambda item: (int(item.row_index), int(item.column_index), str(item.name)),
        )
        for placed in sorted_remaining:
            if id(placed.control) in focus_id_set:
                basics_ordered.append(placed.control)
        basics_ordered += _collect(horizontal_names)
        basics_ordered += _collect(vertical_names)

        basics_id_set = set(id(c) for c in basics_ordered)
        non_basics = [c for c in self._focus_controls if id(c) not in basics_id_set]
        # non_basics[0] is the category_tabs control (first item appended); keep it leading.
        self._focus_controls[:] = non_basics[:1] + basics_ordered + non_basics[1:]

    def _relayout_basics_scroll_cells(self, bounds: Rect, items_by_name: dict, horizontal_names: list[str], vertical_names: list[str]) -> None:
        col_gap = 8
        row_gap = 8
        label_h = 16
        label_gap = 2
        cell_w = max(180, (bounds.width - col_gap) // 2)
        total_w = (cell_w * 2) + col_gap
        start_x = bounds.left + max(0, (bounds.width - total_w) // 2)
        horiz_x = start_x
        vert_x = horiz_x + cell_w + col_gap
        top_y = bounds.top

        horiz_control_h = 24
        horiz_slot_h = label_h + label_gap + horiz_control_h
        for idx, name in enumerate(horizontal_names):
            placed = items_by_name.get(name)
            if placed is None:
                continue
            y = top_y + idx * (horiz_slot_h + row_gap)
            if placed.label is not None:
                placed.label.set_rect(Rect(horiz_x, y, cell_w, label_h))
                placed.label.visible = True
                placed.label.enabled = True
                control_y = y + label_h + label_gap
            else:
                control_y = y
            placed.control.set_rect(Rect(horiz_x, control_y, cell_w, horiz_control_h))

        vert_bar_w = 22
        vert_bar_h = 146
        label_w = max(54, (cell_w // 2) - 24)
        inner_gap = 4
        per_control_w = vert_bar_w + 6 + label_w
        content_w = (per_control_w * 2) + inner_gap
        vert_start_x = vert_x + max(0, (cell_w - content_w) // 2)
        for idx, name in enumerate(vertical_names):
            placed = items_by_name.get(name)
            if placed is None:
                continue
            x = vert_start_x + idx * (per_control_w + inner_gap)
            control_y = top_y + 12
            placed.control.set_rect(Rect(x, control_y, vert_bar_w, vert_bar_h))
            label = placed.label
            if label is None:
                label = self._ensure_basics_aux_label(name)
            if label is not None:
                label_x = x + vert_bar_w + 6
                label_y = control_y + (vert_bar_h - label_h) // 2
                label.set_rect(Rect(label_x, label_y, label_w, label_h))
                label.visible = True
                label.enabled = True

    def _ensure_basics_aux_label(self, name: str) -> LabelControl | None:
        label = self._basics_aux_labels.get(name)
        if label is not None:
            return label
        root = self._showcase_root
        if root is None:
            return None
        text_map = {
            "vertical_scrollbar": "Vertical scrollbar",
            "vertical_slider": "Vertical slider",
        }
        text = text_map.get(name)
        if text is None:
            return None
        label = LabelControl(f"controls_showcase_aux_label_{name}", Rect(0, 0, 1, 1), text, align="left")
        root.add(label)
        self.control_labels.append(label)
        self._basics_aux_labels[name] = label
        return label

    def _relayout_basics_group_cells(self, bounds: Rect, families: list[tuple[str, list]], *, col_count: int) -> int:
        col_gap = 8
        row_gap = 8
        label_h = 16
        label_gap = 2
        col_count = max(1, int(col_count))
        col_w = max(140, (bounds.width - (col_gap * (col_count - 1))) // col_count)
        y = bounds.top

        # Hide all per-control labels in these families first; only one header
        # label per family cell is restored below.
        for _title, placed_items in families:
            for placed in placed_items:
                if placed.label is not None:
                    placed.label.visible = False
                    placed.label.enabled = False

        for start in range(0, len(families), col_count):
            row_families = families[start:start + col_count]
            row_h = 0
            family_metrics: list[tuple[str, list, int, int]] = []
            for title, placed_items in row_families:
                control_heights = [self._target_control_size("basics", placed, col_w)[1] for placed in placed_items]
                family_h = label_h + label_gap + sum(control_heights) + (max(0, len(control_heights) - 1) * 4)
                family_metrics.append((title, placed_items, family_h, max(control_heights) if control_heights else 0))
                row_h = max(row_h, family_h)

            for col, (title, placed_items, _family_h, _max_h) in enumerate(family_metrics):
                x = bounds.left + col * (col_w + col_gap)
                header_label = placed_items[0].label if placed_items and placed_items[0].label is not None else None
                if header_label is not None:
                    header_label.text = title
                    header_label.set_rect(Rect(x, y, col_w, label_h))
                    header_label.visible = True
                    header_label.enabled = True

                control_y = y + label_h + label_gap
                for idx, placed in enumerate(placed_items):
                    target_w, control_h = self._target_control_size("basics", placed, col_w)
                    control_x = x + max(0, (col_w - target_w) // 2)
                    placed.control.set_rect(Rect(control_x, control_y, target_w, control_h))
                    control_y += control_h + 4
            y += row_h + row_gap

        return y

    def _relayout_grid_items(self, category_key: str, bounds: Rect, items: list) -> int:
        is_basics = category_key == "basics"
        col_gap    = 6  if is_basics else max(4, self.INNER_GAP * 2)
        row_gap    = 6  if is_basics else max(6, self.INNER_GAP * 2)
        label_h    = 16 if is_basics else self.LABEL_HEIGHT
        label_gap  = 2  if is_basics else self.LABEL_GAP
        min_col_w  = 160 if is_basics else 220
        max_cols   = 5  if is_basics else 4

        items.sort(key=lambda p: (int(p.row_index), int(p.column_index), str(p.name)))
        fit_cols = max(1, (bounds.width + col_gap) // (min_col_w + col_gap))
        col_count = max(1, min(max_cols, fit_cols))
        col_w = max(140, (bounds.width - col_gap * (col_count - 1)) // col_count)

        y = bounds.top
        for start in range(0, len(items), col_count):
            row_items = items[start:start + col_count]
            slot_heights = []
            for p in row_items:
                _, ch = self._target_control_size(category_key, p, col_w)
                slot_heights.append(ch + (label_h + label_gap if p.label is not None else 0))
            row_h = max(slot_heights) if slot_heights else 0

            for col, p in enumerate(row_items):
                x = bounds.left + col * (col_w + col_gap)
                cw, ch = self._target_control_size(category_key, p, col_w)
                cx = x + max(0, (col_w - cw) // 2)
                if p.label is not None:
                    p.label.set_rect(Rect(x, y, col_w, label_h))
                    p.label.visible = True
                    p.label.enabled = True
                    p.control.set_rect(Rect(cx, y + label_h + label_gap, cw, ch))
                else:
                    p.control.set_rect(Rect(cx, y, cw, ch))
            y += row_h + row_gap

        return y

    def _target_control_size(self, category_key: str, placed, column_width: int) -> tuple[int, int]:
        control = placed.control
        name = str(getattr(placed, "name", ""))
        current_w = max(1, int(control.rect.width))
        current_h = max(1, int(control.rect.height))

        if category_key != "basics":
            return (column_width, current_h)

        compact_w = max(140, column_width)

        if name.startswith("arrow_"):
            side = max(24, min(column_width, 30))
            return (side, side)
        if name in {"vertical_scrollbar", "vertical_slider"}:
            width = max(18, min(column_width, 24))
            return (width, 84)
        if name in {"horizontal_scrollbar", "horizontal_slider"}:
            return (compact_w, 24)
        if name in {"text_input", "dropdown", "spinner", "range_slider", "split_button", "date_picker", "time_picker"}:
            return (compact_w, 32)
        if name in {"button", "button_2", "button_3", "toggle", "toggle_2", "toggle_3"} or name.startswith("button_group_"):
            return (compact_w, 30)
        if name == "text_area":
            return (compact_w, 96)
        if name == "data_grid":
            return (compact_w, 132)
        if name == "tab":
            width = max(180, min(column_width, 230))
            height = max(160, min(current_h if current_h > 0 else 180, 220))
            return (width, height)
        if name == "image":
            side = max(112, min(column_width, 144))
            return (side, side)
        if name == "notification_panel":
            return (compact_w, 168)

        return (compact_w, max(min(current_h, 144), 36))

    def _control_has_open_popup(self, control) -> bool:
        # Open-state conventions across controls in this demo:
        # - _open (date picker)
        # - _dropdown_open (split button)
        # - _is_open (dropdown control, overlay-backed)
        # - _open_index >= 0 (menu bar flyout)
        if bool(getattr(control, "_open", False)):
            return True
        if bool(getattr(control, "_dropdown_open", False)):
            return True
        if bool(getattr(control, "_is_open", False)):
            return True
        open_index = getattr(control, "_open_index", -1)
        return isinstance(open_index, int) and open_index >= 0

    def _promote_open_popup_controls(self, host) -> None:
        root = getattr(host, "control_showcase_root", None)
        if root is None:
            return
        children = getattr(root, "children", None)
        if not isinstance(children, list) or not children:
            return

        open_controls = [
            control
            for control in self.controls
            if control in children and control.visible and control.enabled and self._control_has_open_popup(control)
        ]
        if not open_controls:
            return

        changed = False
        for control in open_controls:
            idx = children.index(control)
            if idx != len(children) - 1:
                children.append(children.pop(idx))
                changed = True

        if changed:
            root.invalidate()

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
