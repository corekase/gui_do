"""Controls showcase feature with grouped, varied-span layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    ContextMenuItem,
    DataGridControl,
    DropdownControl,
    DropdownOption,
    Feature,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    ListItem,
    ListViewControl,
    MenuBarControl,
    MenuEntry,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    OverlayPanelControl,
    PanelControl,
    RichLabelControl,
    ScrollbarControl,
    SliderControl,
    SplitterControl,
    TabControl,
    TabItem,
    TaskPanelControl,
    TextAreaControl,
    TextInputControl,
    ToastSeverity,
    ToggleControl,
    TreeControl,
    TreeNode,
)


@dataclass(slots=True)
class _PlacedControl:
    control: object
    label: LabelControl | None
    name: str
    column_index: int
    row_index: int


class ControlsShowcaseFeature(Feature):
    """Render all controls except task panel/window in grouped, non-uniform layouts."""

    HOST_REQUIREMENTS = {
        "build": ("app", "control_showcase_root"),
        "configure_accessibility": ("app",),
        "on_update": ("app",),
        "prewarm": ("app",),
    }

    ROOT_MARGIN_X = 24
    ROOT_MARGIN_TOP = 24
    ROOT_MARGIN_BOTTOM = 86
    CONTENT_PADDING_X = 10
    CONTENT_PADDING_Y = 12
    REGION_GAP = 14
    INNER_GAP = 10
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
    TASK_PANEL_BUTTON_GAP = 10
    TASK_PANEL_BUTTON_LEFT = 16
    TASK_PANEL_BUTTON_TOP_OFFSET = 10

    LABEL_FONT_ROLE_LOCAL = "label"
    LABEL_FONT_SIZE = 14
    LABEL_FONT_PATH = "demo_features/data/fonts/Ubuntu-B.ttf"
    LABEL_SYSTEM_FONT = "arial"

    CONTROL_FONT_ROLE_LOCAL = "control"
    CONTROL_FONT_SIZE = 15
    CONTROL_FONT_PATH = "demo_features/data/fonts/Ubuntu-B.ttf"
    CONTROL_SYSTEM_FONT = "arial"

    TASK_PANEL_CONTROL_FONT_ROLE = "screen.main.task_panel.control"

    def __init__(self, rect: Rect | None = None) -> None:
        super().__init__("controls_showcase", scene_name="control_showcase")
        self.rect = Rect(rect) if rect is not None else Rect(0, 0, 0, 0)
        self._label_font_role = "body"
        self._control_font_role = "body"

        self.controls: list = []
        self.control_labels: list[LabelControl] = []
        self.placed_controls: list[_PlacedControl] = []
        self._focus_controls: list = []
        self._initial_focus_control = None
        self._pending_initial_focus = False

        self.task_panel = None
        self.showcase_return_button = None
        self._showcase_notification_center: NotificationCenter | None = None

    def build(self, host) -> None:
        self._label_font_role = self.register_font_role(
            host,
            self.LABEL_FONT_ROLE_LOCAL,
            size=self.LABEL_FONT_SIZE,
            file_path=self.LABEL_FONT_PATH,
            system_name=self.LABEL_SYSTEM_FONT,
            scene_name=self.scene_name,
        )
        self._control_font_role = self.register_font_role(
            host,
            self.CONTROL_FONT_ROLE_LOCAL,
            size=self.CONTROL_FONT_SIZE,
            file_path=self.CONTROL_FONT_PATH,
            system_name=self.CONTROL_SYSTEM_FONT,
            scene_name=self.scene_name,
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

        column_width = 200
        row_gap = 8
        col_gap = 16
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
        self._add_group_label(host, "arrowboxes", "ArrowBoxes", Rect(col0_x, col0_y, arrow_left_half_w, arrow_group_h))
        arrow_row0_y = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP
        arrow_second_row_y = arrow_row0_y + arrow_cell_h + row_gap

        self._place_control_unlabeled(
            host,
            "arrow_up",
            ArrowBoxControl("control_arrow_up", Rect(0, 0, 1, 1), 90),
            Rect(col0_x, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow up",
            column_index=0,
            row_index=0,
        )
        self._place_control_unlabeled(
            host,
            "arrow_down",
            ArrowBoxControl("control_arrow_down", Rect(0, 0, 1, 1), 270),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_row0_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow down",
            column_index=0,
            row_index=1,
        )
        self._place_control_unlabeled(
            host,
            "arrow_left",
            ArrowBoxControl("control_arrow_left", Rect(0, 0, 1, 1), 180),
            Rect(col0_x, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow left",
            column_index=0,
            row_index=2,
        )
        self._place_control_unlabeled(
            host,
            "arrow_right",
            ArrowBoxControl("control_arrow_right", Rect(0, 0, 1, 1), 0),
            Rect(col0_x + arrow_cell_w + self.INNER_GAP, arrow_second_row_y, arrow_cell_w, arrow_cell_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Arrow right",
            column_index=0,
            row_index=3,
        )

        col0_row_y = col0_y + self.LABEL_HEIGHT + self.LABEL_GAP + arrow_group_h + row_gap
        text_input_slot_h = slot_h(text_input_control_h)
        text_area_slot_h = slot_h(text_area_control_h)
        bar_slot_h = slot_h(bar_control_h)

        self._place_control(
            host,
            "text_input",
            "Text Input",
            TextInputControl("control_text_input", Rect(0, 0, 1, 1), placeholder="Type here", font_role=self._control_font_role),
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
                font_role=self._control_font_role,
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

        self._place_control(
            host,
            "button",
            "Button 1",
            ButtonControl("control_button", Rect(0, 0, 1, 1), "Button"),
            Rect(left_lane.left, y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Showcase button 1",
            column_index=2,
            row_index=0,
        )
        self._place_control(
            host,
            "button_2",
            "Button 2",
            ButtonControl("control_button_2", Rect(0, 0, 1, 1), "Button"),
            Rect(left_lane.left + tri_w + self.INNER_GAP, y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Showcase button 2",
            column_index=2,
            row_index=1,
        )
        self._place_control(
            host,
            "button_3",
            "Button 3",
            ButtonControl("control_button_3", Rect(0, 0, 1, 1), "Button"),
            Rect(left_lane.left + ((tri_w + self.INNER_GAP) * 2), y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="button",
            accessibility_label="Showcase button 3",
            column_index=2,
            row_index=2,
        )
        y += button_slot_h + row_gap

        self._place_control(
            host,
            "toggle",
            "Toggle 1",
            ToggleControl("control_toggle", Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
            Rect(left_lane.left, y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="toggle",
            accessibility_label="Showcase toggle 1",
            column_index=2,
            row_index=3,
        )
        self._place_control(
            host,
            "toggle_2",
            "Toggle 2",
            ToggleControl("control_toggle_2", Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
            Rect(left_lane.left + tri_w + self.INNER_GAP, y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="toggle",
            accessibility_label="Showcase toggle 2",
            column_index=2,
            row_index=4,
        )
        self._place_control(
            host,
            "toggle_3",
            "Toggle 3",
            ToggleControl("control_toggle_3", Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
            Rect(left_lane.left + ((tri_w + self.INNER_GAP) * 2), y, tri_w, button_slot_h),
            focusable=True,
            accessibility_role="toggle",
            accessibility_label="Showcase toggle 3",
            column_index=2,
            row_index=5,
        )
        y += button_slot_h + row_gap

        for group_col, letter in enumerate(("A", "B", "C")):
            gx = left_lane.left + (group_col * (tri_w + self.INNER_GAP))
            first_group_y = y
            self._place_control(
                host,
                f"button_group_{letter.lower()}1",
                f"Group {letter}",
                ButtonGroupControl(
                    f"control_button_group_{letter.lower()}1",
                    Rect(0, 0, 1, 1),
                    f"controls_showcase_{letter.lower()}",
                    f"{letter}1",
                    selected=False,
                ),
                Rect(gx, first_group_y, tri_w, group_first_slot_h),
                focusable=True,
                accessibility_role="button",
                accessibility_label=f"Group {letter} option 1",
                column_index=2,
                row_index=6 + (group_col * 3),
            )
            self._place_control_unlabeled(
                host,
                f"button_group_{letter.lower()}2",
                ButtonGroupControl(
                    f"control_button_group_{letter.lower()}2",
                    Rect(0, 0, 1, 1),
                    f"controls_showcase_{letter.lower()}",
                    f"{letter}2",
                    selected=False,
                ),
                Rect(gx, first_group_y + group_first_slot_h + row_gap, tri_w, group_other_h),
                focusable=True,
                accessibility_role="button",
                accessibility_label=f"Group {letter} option 2",
                column_index=2,
                row_index=7 + (group_col * 3),
            )
            self._place_control_unlabeled(
                host,
                f"button_group_{letter.lower()}3",
                ButtonGroupControl(
                    f"control_button_group_{letter.lower()}3",
                    Rect(0, 0, 1, 1),
                    f"controls_showcase_{letter.lower()}",
                    f"{letter}3",
                    selected=False,
                ),
                Rect(gx, first_group_y + group_first_slot_h + row_gap + group_other_h + row_gap, tri_w, group_other_h),
                focusable=True,
                accessibility_role="button",
                accessibility_label=f"Group {letter} option 3",
                column_index=2,
                row_index=8 + (group_col * 3),
            )

        groups_block_h = group_first_slot_h + row_gap + group_other_h + row_gap + group_other_h
        y += groups_block_h + row_gap

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
        _tab_lbl_one = LabelControl("ctrl_tab_lbl_one", Rect(0, 0, sq_size, 30), "One", align="left")
        _tab_lbl_one.font_role = self._label_font_role
        _tab_lbl_two = LabelControl("ctrl_tab_lbl_two", Rect(0, 0, sq_size, 30), "Two", align="left")
        _tab_lbl_two.font_role = self._label_font_role
        _tab_lbl_three = LabelControl("ctrl_tab_lbl_three", Rect(0, 0, sq_size, 30), "Three", align="left")
        _tab_lbl_three.font_role = self._label_font_role
        self._place_control_unlabeled(
            host,
            "tab",
            TabControl(
                "control_tab",
                Rect(0, 0, 1, 1),
                items=[
                    TabItem("one", "One", _tab_lbl_one),
                    TabItem("two", "Two", _tab_lbl_two),
                    TabItem("three", "Three", _tab_lbl_three),
                ],
                selected_key="one",
                font_role=self._control_font_role,
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

        # New row of columns starts from the left edge at data_grid bottom + 10.
        new_row_col_w = 200
        new_row_y = data_grid_bottom + 10
        new_row_x0 = content_rect.left
        new_row_x1 = new_row_x0 + new_row_col_w + col_gap
        new_row_x2 = new_row_x1 + new_row_col_w + col_gap

        # Column 0: ListView, Dropdown, then Splitter stacked with requested spacing.
        list_slot_h = slot_h(92)
        self._place_control(
            host,
            "list_view",
            "List View",
            ListViewControl(
                "control_list_view",
                Rect(0, 0, 1, 1),
                [ListItem(label=f"Item {index + 1}", value=index) for index in range(6)],
                row_height=24,
                font_role=self._control_font_role,
            ),
            Rect(new_row_x0, new_row_y, new_row_col_w, list_slot_h),
            focusable=True,
            accessibility_role="listbox",
            accessibility_label="List view",
            column_index=2,
            row_index=60,
        )
        list_view_bottom = new_row_y + list_slot_h

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
                font_role=self._control_font_role,
            ),
            Rect(new_row_x0, list_view_bottom + 5, new_row_col_w, dropdown_slot_h),
            focusable=True,
            accessibility_role="combobox",
            accessibility_label="Dropdown",
            column_index=2,
            row_index=61,
        )
        dropdown_bottom = (list_view_bottom + 5) + dropdown_slot_h

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
            Rect(new_row_x0, dropdown_bottom + 5, new_row_col_w, splitter_slot_h),
            focusable=True,
            accessibility_role="separator",
            accessibility_label="Splitter",
            column_index=2,
            row_index=62,
        )

        # Column 1: rich text spanning full width (200px).
        rich_slot_h = slot_h(90)
        self._place_control(
            host,
            "rich_label",
            "Rich Label",
            RichLabelControl(
                "control_rich_label",
                Rect(0, 0, 1, 1),
                text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, run `deploy --env staging`, and **_ship_** after QA.",
                font_role=self._control_font_role,
            ),
            Rect(new_row_x1, new_row_y, new_row_col_w, rich_slot_h),
            focusable=False,
            column_index=3,
            row_index=70,
        )

        # Column 2: canvas and frame on top row, panel on the next row spanning full width.
        grid_gap = self.INNER_GAP
        cell_w = max(1, (new_row_col_w - grid_gap) // 2)
        cell_h = cell_w
        g0x = new_row_x2
        g1x = new_row_x2 + cell_w + grid_gap
        g0y = new_row_y
        top_slot_h = cell_h + self.LABEL_HEIGHT + self.LABEL_GAP
        g1y = g0y + top_slot_h + row_gap
        self._place_control(
            host,
            "canvas",
            "Canvas",
            CanvasControl("control_canvas", Rect(0, 0, 1, 1), max_events=64),
            Rect(g0x, g0y, cell_w, top_slot_h),
            focusable=False,
            column_index=4,
            row_index=80,
        )
        self._place_control(
            host,
            "frame",
            "Frame",
            FrameControl("control_frame", Rect(0, 0, 1, 1), border_width=2),
            Rect(g1x, g0y, cell_w, top_slot_h),
            focusable=False,
            column_index=4,
            row_index=81,
        )
        self._place_control(
            host,
            "panel",
            "Panel",
            PanelControl("control_panel", Rect(0, 0, 1, 1), draw_background=True),
            Rect(g0x, g1y, new_row_col_w, slot_h(68)),
            focusable=False,
            column_index=4,
            row_index=82,
        )

        # New rightmost columns for recently added controls.
        new_col_x = new_row_x2 + new_row_col_w + col_gap
        new_col_w = 220

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
            Rect(new_col_x, new_row_y, new_col_w, menu_slot_h),
            focusable=True,
            accessibility_role="menubar",
            accessibility_label="Menu bar",
            column_index=5,
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
            Rect(new_col_x, new_row_y + menu_slot_h + row_gap, new_col_w, tree_slot_h),
            focusable=True,
            accessibility_role="tree",
            accessibility_label="Tree control",
            column_index=5,
            row_index=91,
        )

        self._showcase_notification_center = NotificationCenter(None, max_records=6)
        self._showcase_notification_center.add(
            NotificationRecord("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS)
        )
        self._showcase_notification_center.add(
            NotificationRecord("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING)
        )
        notif_col_x = new_col_x + new_col_w + col_gap
        notif_col_w = 240
        notif_slot_h = slot_h(220)
        self._place_control(
            host,
            "notification_panel",
            "Notification Panel",
            NotificationPanelControl(
                "control_notification_panel",
                Rect(0, 0, 1, 1),
                self._showcase_notification_center,
            ),
            Rect(notif_col_x, new_row_y, notif_col_w, notif_slot_h),
            focusable=False,
            column_index=6,
            row_index=92,
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
        if not self._pending_initial_focus:
            return
        if host.app.active_scene_name != self.scene_name:
            return
        target = self._initial_focus_control
        if target is None:
            self._pending_initial_focus = False
            return
        if target not in host.app.scene._walk_nodes() or not target.visible or not target.enabled:
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
        label.font_role = self._label_font_role

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

        control.rect.topleft = actual_control_rect.topleft
        control.rect.size = actual_control_rect.size
        control.enabled = True
        if hasattr(control, "font_role"):
            try:
                control.font_role = self._control_font_role
            except Exception:
                pass

        if accessibility_role is not None and accessibility_label is not None:
            control.set_accessibility(role=accessibility_role, label=accessibility_label)

        if focusable:
            self._focus_controls.append(control)
        else:
            control.set_tab_index(-1)

        host.control_showcase_root.add(control)
        self.controls.append(control)
        self.placed_controls.append(
            _PlacedControl(
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
        label.font_role = self._label_font_role
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
        screen_rect = getattr(host, "screen_rect", None)
        if screen_rect is None:
            screen_rect = host.app.screen.get_rect()

        self.task_panel = host.app.add(
            TaskPanelControl(
                "control_showcase_task_panel",
                Rect(0, screen_rect.height - self.TASK_PANEL_HEIGHT, screen_rect.width, self.TASK_PANEL_HEIGHT),
                auto_hide=True,
                hidden_peek_pixels=self.TASK_PANEL_HIDDEN_PEEK_PIXELS,
                animation_step_px=self.TASK_PANEL_ANIMATION_STEP_PX,
                dock_bottom=True,
            ),
            scene_name=self.scene_name,
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
                (host.go_to_main if hasattr(host, "go_to_main") else (lambda: host.app.switch_scene("main"))),
                style="angle",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

        self.showcase_return_button.set_accessibility(role="button", label="Return to main")
        # Keep showcase Tab traversal within the feature surface; task panel
        # actions remain clickable but are not part of feature focus cycling.
        self.showcase_return_button.set_tab_index(-1)
