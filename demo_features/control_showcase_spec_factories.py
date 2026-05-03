"""Factory helpers for declarative control showcase placement specs."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    AnimatedImageControl,
    BreadcrumbControl,
    BreadcrumbItem,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    ChipInputControl,
    DockPane,
    DockTabs,
    DockWorkspace,
    DockWorkspacePanel,
    FrameAnimation,
    CellCaretLayout,
    LabelControl,
    LayoutManager,
    ListItem,
    ListViewControl,
    PropertyInspectorModel,
    PropertyInspectorPanel,
    ProgressBarControl,
    ScrollViewControl,
    SpriteSheet,
    ColorPickerControl,
    ContextMenuItem,
    DataGridControl,
    DatePickerControl,
    DropdownControl,
    DropdownOption,
    ExpanderControl,
    FixedPatternFormatter,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LayoutAxis,
    MenuBarControl,
    MenuEntry,
    NotificationPanelControl,
    OverlayPanelControl,
    NumericFormatter,
    PanelControl,
    PatternFormatter,
    RangeSliderControl,
    RichLabelControl,
    ScrollbarControl,
    SliderControl,
    SpinnerControl,
    SplitButtonControl,
    SplitButtonOption,
    SplitterControl,
    StatusBarControl,
    StatusSlot,
    TabControl,
    TabItem,
    TextAreaControl,
    TextInputControl,
    TimePickerControl,
    ToggleControl,
    ToolbarControl,
    ToolbarItem,
    TreeControl,
    TreeNode,
)
from gui_do import ControlDefinition, build_specs_from_column_section
from gui_do.features.feature_lifecycle import ControlPlacementSpec


def build_intro_specs(
    *,
    col0_x: int,
    col0_y: int,
    column_width: int,
    inner_gap: int,
    label_height: int,
    label_gap: int,
    row_gap: int,
    arrow_control_size: int,
    group_column_specs: tuple[tuple[str, str], ...],
    group_row_specs: tuple[tuple[int, bool], ...],
    button_trio_specs: tuple[tuple[str, str, str, str], ...],
    toggle_trio_specs: tuple[tuple[str, str, str, str], ...],
) -> tuple[LabelControl, tuple[ControlPlacementSpec, ...]]:
    arrow_left_half_w = column_width // 2
    arrow_cell_w = max(20, (arrow_left_half_w - inner_gap) // 2)
    arrow_cell_h = arrow_control_size
    arrow_row0_y = col0_y + label_height + label_gap
    arrow_second_row_y = arrow_row0_y + arrow_cell_h + row_gap

    arrow_header_label = LabelControl(
        "controls_showcase_group_label_arrowboxes",
        Rect(col0_x, col0_y, arrow_left_half_w, label_height),
        "ArrowBoxes",
        align="left",
    )

    arrow_specs = (
        ("arrow_up", "control_arrow_up", 90, col0_x, arrow_row0_y, "Arrow up", 0),
        ("arrow_down", "control_arrow_down", 270, col0_x + arrow_cell_w + inner_gap, arrow_row0_y, "Arrow down", 1),
        ("arrow_left", "control_arrow_left", 180, col0_x, arrow_second_row_y, "Arrow left", 2),
        ("arrow_right", "control_arrow_right", 0, col0_x + arrow_cell_w + inner_gap, arrow_second_row_y, "Arrow right", 3),
    )
    intro_specs: list[ControlPlacementSpec] = []
    for name, control_id, degrees, x, y, accessibility_label, row_index in arrow_specs:
        intro_specs.append(
            ControlPlacementSpec(
                name=name,
                labeled=False,
                control=ArrowBoxControl(control_id, Rect(0, 0, 1, 1), degrees),
                control_rect=Rect(x, y, arrow_cell_w, arrow_cell_h),
                focusable=True,
                accessibility_role="button",
                accessibility_label=accessibility_label,
                column_index=0,
                row_index=row_index,
            )
        )

    for col_index, _ in enumerate(group_column_specs):
        button_name, button_label_text, button_control_id, button_accessibility_label = button_trio_specs[col_index]
        intro_specs.append(
            ControlPlacementSpec(
                name=button_name,
                label_text=button_label_text,
                control=ButtonControl(button_control_id, Rect(0, 0, 1, 1), "Button"),
                control_rect=Rect(0, 0, 1, 1),
                focusable=True,
                accessibility_role="button",
                accessibility_label=button_accessibility_label,
                column_index=2,
                row_index=col_index,
            )
        )

    for col_index, _ in enumerate(group_column_specs):
        toggle_name, toggle_label_text, toggle_control_id, toggle_accessibility_label = toggle_trio_specs[col_index]
        intro_specs.append(
            ControlPlacementSpec(
                name=toggle_name,
                label_text=toggle_label_text,
                control=ToggleControl(toggle_control_id, Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
                control_rect=Rect(0, 0, 1, 1),
                focusable=True,
                accessibility_role="toggle",
                accessibility_label=toggle_accessibility_label,
                column_index=2,
                row_index=3 + col_index,
            )
        )

    for col_index, (group_key, group_letter) in enumerate(group_column_specs):
        for option_index, with_label in group_row_specs:
            control_name = f"button_group_{group_key}{option_index}"
            control = ButtonGroupControl(
                f"control_button_group_{group_key}{option_index}",
                Rect(0, 0, 1, 1),
                f"controls_showcase_{group_key}",
                f"{group_letter}{option_index}",
                selected=False,
            )
            row_index = 6 + (col_index * 3) + (option_index - 1)
            intro_specs.append(
                ControlPlacementSpec(
                    name=control_name,
                    label_text=f"Group {group_letter}" if with_label else None,
                    labeled=with_label,
                    control=control,
                    control_rect=Rect(0, 0, 1, 1),
                    focusable=True,
                    accessibility_role="button",
                    accessibility_label=f"Group {group_letter} option {option_index}",
                    column_index=2,
                    row_index=row_index,
                )
            )

    return arrow_header_label, tuple(intro_specs)


def build_list_scroll_specs(
    *,
    new_row_col_w: int,
    new_row_x0: int,
    new_row_x1: int,
    col0_y: int,
    col1_y: int,
    list_slot_h: int,
    scroll_slot_h: int,
    row_gap: int,
) -> tuple[LabelControl, LabelControl, tuple[ControlPlacementSpec, ...]]:
    list_selection_label = LabelControl(
        "lv_selected_label",
        Rect(new_row_x0, col0_y + list_slot_h + row_gap, new_row_col_w, 22),
        "Selected: Item 1",
        align="left",
    )

    scroll_items = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet"]
    scroll_content_h = 24 * len(scroll_items)
    scroll_control = ScrollViewControl(
        "control_scroll_view",
        Rect(0, 0, new_row_col_w, 120),
        content_width=new_row_col_w - 20,
        content_height=scroll_content_h,
        scroll_y=True,
    )
    scroll_selection_label = LabelControl(
        "sv_selected_label",
        Rect(new_row_x1, col1_y + scroll_slot_h + row_gap, new_row_col_w, 22),
        "Selected: Alpha",
        align="left",
    )
    scroll_select_list = ListViewControl(
        "sv_select_list",
        Rect(0, 0, new_row_col_w - 20, scroll_content_h),
        [ListItem(label=item, value=item) for item in scroll_items],
        row_height=24,
        show_scrollbar=False,
        on_select=lambda _idx, item: setattr(scroll_selection_label, "text", f"Selected: {item.label}"),
    )
    scroll_select_list.set_tab_index(-1)
    scroll_select_list.set_accessibility(role="listbox", label="Scroll view list")
    scroll_control.add(scroll_select_list, content_x=4, content_y=0)
    scroll_control.set_content_size(new_row_col_w - 20, scroll_content_h)

    specs = (
        ControlPlacementSpec(
            name="list_view",
            label_text="List View",
            control=ListViewControl(
                "control_list_view",
                Rect(0, 0, 1, 1),
                [ListItem(label=f"Item {index + 1}", value=index) for index in range(10)],
                row_height=24,
                selected_index=0,
                on_select=lambda _idx, item: setattr(list_selection_label, "text", f"Selected: {item.label}"),
            ),
            control_rect=Rect(new_row_x0, col0_y, new_row_col_w, list_slot_h),
            focusable=True,
            accessibility_role="listbox",
            accessibility_label="List view",
            column_index=2,
            row_index=60,
        ),
        ControlPlacementSpec(
            name="scroll_view",
            label_text="Scroll View",
            control=scroll_control,
            control_rect=Rect(new_row_x1, col1_y, new_row_col_w, scroll_slot_h),
            focusable=True,
            accessibility_role="group",
            accessibility_label="Scroll view",
            column_index=3,
            row_index=70,
        ),
    )
    return list_selection_label, scroll_selection_label, specs


def build_core_showcase_specs(
    *,
    tab_labels: dict[str, object],
    tab_specs: tuple[tuple[str, str], ...],
    image_path: str,
    notification_center,
    scrollbar_content_size: int,
    scrollbar_viewport_size: int,
    scrollbar_default_offset: int,
    scrollbar_step: int,
    slider_minimum: float,
    slider_maximum: float,
    slider_default_value: float,
) -> tuple[ControlPlacementSpec, ...]:
    return (
        ControlPlacementSpec(
            name="text_input",
            label_text="Text Input",
            control=TextInputControl("control_text_input", Rect(0, 0, 1, 1), placeholder="Type here"),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Text input",
            column_index=0,
            row_index=4,
        ),
        ControlPlacementSpec(
            name="text_area",
            label_text="Text Area",
            control=TextAreaControl(
                "control_text_area",
                Rect(0, 0, 1, 1),
                value="Heading: Notes\n- First line\n- Second line",
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Text area",
            column_index=0,
            row_index=5,
        ),
        ControlPlacementSpec(
            name="data_grid",
            label_text="Data Grid",
            control=DataGridControl(
                "control_data_grid",
                Rect(0, 0, 1, 1),
                [
                    GridColumn(key="name", title="Name", width=90),
                    GridColumn(key="value", title="Value", width=70),
                ],
                [
                    GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                    GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                    GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                    GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
                ],
                row_height=24,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="table",
            accessibility_label="Data grid",
            column_index=2,
            row_index=20,
        ),
        ControlPlacementSpec(
            name="tab",
            labeled=False,
            control=TabControl(
                "control_tab",
                Rect(0, 0, 1, 1),
                items=[
                    TabItem(tab_key, tab_title, tab_labels[tab_key])
                    for tab_key, tab_title in tab_specs
                ],
                selected_key="one",
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="tablist",
            accessibility_label="Tab control",
            column_index=3,
            row_index=30,
        ),
        ControlPlacementSpec(
            name="image",
            labeled=False,
            control=ImageControl(
                "control_image",
                Rect(0, 0, 1, 1),
                str(Path(__file__).parent.parent / image_path),
                scale=True,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=False,
            column_index=4,
            row_index=40,
        ),
        ControlPlacementSpec(
            name="notification_panel",
            label_text="Notification Panel",
            control=NotificationPanelControl(
                "control_notification_panel",
                Rect(0, 0, 1, 1),
                notification_center,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=False,
            column_index=5,
            row_index=41,
        ),
        ControlPlacementSpec(
            name="horizontal_scrollbar",
            label_text="Horizontal Scrollbar",
            control=ScrollbarControl(
                "control_horizontal_scrollbar",
                Rect(0, 0, 1, 1),
                LayoutAxis.HORIZONTAL,
                scrollbar_content_size,
                scrollbar_viewport_size,
                offset=scrollbar_default_offset,
                step=scrollbar_step,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="scrollbar",
            accessibility_label="Horizontal scrollbar",
            column_index=0,
            row_index=6,
        ),
        ControlPlacementSpec(
            name="horizontal_slider",
            label_text="Horizontal Slider",
            control=SliderControl(
                "control_horizontal_slider",
                Rect(0, 0, 1, 1),
                LayoutAxis.HORIZONTAL,
                slider_minimum,
                slider_maximum,
                slider_default_value,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="slider",
            accessibility_label="Horizontal slider",
            column_index=0,
            row_index=7,
        ),
        ControlPlacementSpec(
            name="vertical_scrollbar",
            labeled=False,
            control=ScrollbarControl(
                "control_vertical_scrollbar",
                Rect(0, 0, 1, 1),
                LayoutAxis.VERTICAL,
                scrollbar_content_size,
                scrollbar_viewport_size,
                offset=scrollbar_default_offset,
                step=scrollbar_step,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="scrollbar",
            accessibility_label="Vertical scrollbar",
            column_index=1,
            row_index=0,
        ),
        ControlPlacementSpec(
            name="vertical_slider",
            labeled=False,
            control=SliderControl(
                "control_vertical_slider",
                Rect(0, 0, 1, 1),
                LayoutAxis.VERTICAL,
                slider_minimum,
                slider_maximum,
                slider_default_value,
            ),
            control_rect=Rect(0, 0, 1, 1),
            focusable=True,
            accessibility_role="slider",
            accessibility_label="Vertical slider",
            column_index=1,
            row_index=1,
        ),
    )


def build_data_advanced_specs(
    *,
    new_col_x: int,
    col4_y: int,
    menu_slot_h: int,
    row_gap: int,
    new_col_w: int,
    tree_slot_h: int,
    new_row_x2: int,
    dropdown_y: int,
    new_row_col_w: int,
    dropdown_slot_h: int,
    splitter_y: int,
    splitter_slot_h: int,
    col2_y: int,
    rich_slot_h: int,
    g0x: int,
    g0y: int,
    cell_w: int,
    top_slot_h: int,
    g1x: int,
    cell_w2: int,
    g1y: int,
    panel_slot_h: int,
) -> tuple[ControlPlacementSpec, ...]:
    return (
        ControlPlacementSpec(
            name="tree",
            label_text="Tree",
            control=TreeControl(
                "control_tree",
                Rect(0, 0, 1, 1),
                [
                    TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                    TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")]),
                ],
            ),
            control_rect=Rect(new_col_x, col4_y + menu_slot_h + row_gap, new_col_w, tree_slot_h),
            focusable=True,
            accessibility_role="tree",
            accessibility_label="Tree control",
            column_index=4,
            row_index=91,
        ),
        ControlPlacementSpec(
            name="dropdown",
            label_text="Dropdown",
            control=DropdownControl(
                "control_dropdown",
                Rect(0, 0, 1, 1),
                [DropdownOption(label=f"Option {index + 1}", value=index) for index in range(4)],
                placeholder="Choose",
            ),
            control_rect=Rect(new_row_x2, dropdown_y, new_row_col_w, dropdown_slot_h),
            focusable=True,
            accessibility_role="combobox",
            accessibility_label="Dropdown",
            column_index=4,
            row_index=81,
        ),
        ControlPlacementSpec(
            name="splitter",
            label_text="Splitter",
            control=SplitterControl(
                "control_splitter",
                Rect(0, 0, 1, 1),
                axis=LayoutAxis.HORIZONTAL,
                ratio=0.5,
                min_pane_size=16,
            ),
            control_rect=Rect(new_row_x2, splitter_y, new_row_col_w, splitter_slot_h),
            focusable=True,
            accessibility_role="separator",
            accessibility_label="Splitter",
            column_index=4,
            row_index=82,
        ),
        ControlPlacementSpec(
            name="menu_bar",
            label_text="Menu Bar",
            control=MenuBarControl(
                "control_menu_bar",
                Rect(0, 0, 1, 1),
                [
                    MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Save")]),
                    MenuEntry("Tools", [ContextMenuItem("Run"), ContextMenuItem("Reset")]),
                ],
            ),
            control_rect=Rect(new_col_x, col4_y, new_col_w, menu_slot_h),
            focusable=False,
            accessibility_role="menubar",
            accessibility_label="Menu bar",
            column_index=4,
            row_index=90,
        ),
        ControlPlacementSpec(
            name="rich_label",
            label_text="Rich Label",
            control=RichLabelControl(
                "control_rich_label",
                Rect(0, 0, 1, 1),
                text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, run `deploy --env staging`, and **_ship_** after QA.",
            ),
            control_rect=Rect(new_row_x2, col2_y, new_row_col_w, rich_slot_h),
            focusable=False,
            column_index=4,
            row_index=80,
        ),
        ControlPlacementSpec(
            name="canvas",
            label_text="Canvas",
            control=CanvasControl("control_canvas", Rect(0, 0, 1, 1), max_events=64),
            control_rect=Rect(g0x, g0y, cell_w, top_slot_h),
            focusable=False,
            column_index=5,
            row_index=83,
        ),
        ControlPlacementSpec(
            name="frame",
            label_text="Frame",
            control=FrameControl("control_frame", Rect(0, 0, 1, 1), border_width=2),
            control_rect=Rect(g1x, g0y, cell_w2, top_slot_h),
            focusable=False,
            column_index=5,
            row_index=84,
        ),
        ControlPlacementSpec(
            name="panel",
            label_text="Panel",
            control=PanelControl("control_panel", Rect(0, 0, 1, 1), draw_background=True),
            control_rect=Rect(g0x, g1y, new_row_col_w, panel_slot_h),
            focusable=False,
            column_index=5,
            row_index=85,
        ),
    )


def build_data_tab_specs_bundle(
    *,
    anchors: tuple[Rect, ...],
    row_gap: int,
    inner_gap: int,
    label_height: int,
    label_gap: int,
    slot_height_for: Callable[[int], int],
) -> tuple[
    LabelControl,
    LabelControl,
    tuple[ControlPlacementSpec, ...],
    tuple[ControlPlacementSpec, ...],
    Rect,
    Rect,
]:
    if len(anchors) < 7:
        raise ValueError("build_data_tab_specs_bundle requires at least 7 anchors")

    col0_anchor, col1_anchor, col2_anchor, col3_anchor, col4_anchor, col5_anchor, col6_anchor = anchors[:7]
    new_row_col_w = min(200, col0_anchor.width)
    new_row_x0 = col0_anchor.left
    new_row_x1 = col1_anchor.left
    new_row_x2 = col2_anchor.left
    new_row_x3 = col3_anchor.left
    col0_y = col0_anchor.top
    col1_y = col1_anchor.top
    col2_y = col2_anchor.top
    col3_y = col3_anchor.top

    list_slot_h = slot_height_for(120)
    scroll_slot_h = slot_height_for(120)
    list_selection_label, scroll_selection_label, list_scroll_specs = build_list_scroll_specs(
        new_row_col_w=new_row_col_w,
        new_row_x0=new_row_x0,
        new_row_x1=new_row_x1,
        col0_y=col0_y,
        col1_y=col1_y,
        list_slot_h=list_slot_h,
        scroll_slot_h=scroll_slot_h,
        row_gap=row_gap,
    )

    new_col_x = col4_anchor.left
    new_col_w = min(220, col4_anchor.width)
    col4_y = col4_anchor.top
    menu_slot_h = slot_height_for(28)
    tree_slot_h = slot_height_for(150)

    rich_slot_h = slot_height_for(90)
    dropdown_slot_h = slot_height_for(30)
    dropdown_y = col2_y + rich_slot_h + row_gap
    splitter_y = dropdown_y + dropdown_slot_h + row_gap
    splitter_slot_h = slot_height_for(52)

    cell_w = max(1, (new_row_col_w - inner_gap) // 2)
    cell_w2 = max(1, new_row_col_w - inner_gap - cell_w)
    g0x = new_row_x3
    g1x = new_row_x3 + cell_w + inner_gap
    g0y = col3_y
    top_slot_h = cell_w + label_height + label_gap
    g1y = g0y + top_slot_h + row_gap
    data_advanced_specs = build_data_advanced_specs(
        new_col_x=new_col_x,
        col4_y=col4_y,
        menu_slot_h=menu_slot_h,
        row_gap=row_gap,
        new_col_w=new_col_w,
        tree_slot_h=tree_slot_h,
        new_row_x2=new_row_x2,
        dropdown_y=dropdown_y,
        new_row_col_w=new_row_col_w,
        dropdown_slot_h=dropdown_slot_h,
        splitter_y=splitter_y,
        splitter_slot_h=splitter_slot_h,
        col2_y=col2_y,
        rich_slot_h=rich_slot_h,
        g0x=g0x,
        g0y=g0y,
        cell_w=cell_w,
        top_slot_h=top_slot_h,
        g1x=g1x,
        cell_w2=cell_w2,
        g1y=g1y,
        panel_slot_h=slot_height_for(68),
    )
    return (
        list_selection_label,
        scroll_selection_label,
        list_scroll_specs,
        data_advanced_specs,
        col5_anchor,
        col6_anchor,
    )


def formatted_input_definitions(col_w: int) -> tuple[ControlDefinition, ...]:
    _raw_defs = (
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
    return tuple(
        ControlDefinition(
            name=name,
            label_text=label_text,
            control_height=30,
            row_index=row_index,
            control_factory=(
                lambda f=formatter, cid=control_id, rv=raw_value, ph=placeholder:
                f.create_text_input(str(cid), Rect(0, 0, int(col_w), 30), raw_value=str(rv), placeholder=str(ph))
            ),
            column_index=7,
            focusable=True,
            accessibility_role="textbox",
            accessibility_label=accessibility_label,
        )
        for name, label_text, formatter, control_id, raw_value, placeholder, accessibility_label, row_index in _raw_defs
    )


def col6_control_definitions(col6_w: int) -> tuple[ControlDefinition, ...]:
    return (
        ControlDefinition(
            name="spinner",
            label_text="Spinner",
            control_height=30,
            row_index=100,
            control_factory=lambda: SpinnerControl(
                "control_spinner",
                Rect(0, 0, col6_w, 30),
                value=25,
                min_value=0,
                max_value=100,
                step=1,
                decimals=0,
                on_change=lambda v, _r: None,
            ),
        ),
        ControlDefinition(
            name="range_slider",
            label_text="Range Slider",
            control_height=24,
            row_index=101,
            control_factory=lambda: RangeSliderControl(
                "control_range_slider",
                Rect(0, 0, col6_w, 24),
                min_value=0,
                max_value=100,
                low_value=20,
                high_value=80,
                on_change=lambda lo, hi, _r: None,
            ),
        ),
        ControlDefinition(
            name="color_picker",
            label_text="Color Picker",
            control_height=180,
            row_index=102,
            control_factory=lambda: ColorPickerControl(
                "control_color_picker",
                Rect(0, 0, col6_w, 180),
                color=(64, 128, 255),
                on_change=lambda c: None,
            ),
        ),
    )


def build_col6_section_specs(
    *,
    stack: CellCaretLayout,
    col_x: int,
    col_y: int,
    col_w: int,
    slot_height_for: Callable[[int], int],
    overflow_gap: int,
    column_index: int = 5,
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    defs = tuple(
        ControlDefinition(
            name=d.name,
            label_text=d.label_text,
            control_height=d.control_height,
            row_index=d.row_index,
            control_factory=d.control_factory,
            column_index=column_index,
        )
        for d in col6_control_definitions(col_w)
    )
    return build_specs_from_column_section(defs, stack=stack, slot_height_for=slot_height_for, overflow_gap=overflow_gap)


def build_formatted_input_section_specs(
    *,
    stack: CellCaretLayout,
    col_x: int,
    col_y: int,
    col_w: int,
    slot_height_for: Callable[[int], int],
    overflow_gap: int,
    column_index: int = 7,
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    defs = tuple(
        ControlDefinition(
            name=d.name,
            label_text=d.label_text,
            control_height=d.control_height,
            row_index=d.row_index,
            control_factory=d.control_factory,
            column_index=column_index,
            focusable=d.focusable,
            accessibility_role=d.accessibility_role,
            accessibility_label=d.accessibility_label,
        )
        for d in formatted_input_definitions(col_w)
    )
    return build_specs_from_column_section(defs, stack=stack, slot_height_for=slot_height_for, overflow_gap=overflow_gap)


def nc_control_definitions(nc_w: int) -> tuple[ControlDefinition, ...]:
    return (
        ControlDefinition(
            name="toolbar",
            label_text="Toolbar",
            control_height=36,
            row_index=150,
            column_index=11,
            focusable=True,
            accessibility_role="toolbar",
            accessibility_label="Toolbar",
            control_factory=lambda: ToolbarControl(
                "control_toolbar",
                Rect(0, 0, nc_w, 36),
                items=[
                    ToolbarItem(label="Cut", action_id="cut"),
                    ToolbarItem(label="Copy", action_id="copy"),
                    ToolbarItem(separator=True),
                    ToolbarItem(label="Paste", action_id="paste"),
                ],
            ),
        ),
        ControlDefinition(
            name="status_bar",
            label_text="Status Bar",
            control_height=24,
            row_index=151,
            column_index=11,
            focusable=False,
            accessibility_role="status",
            accessibility_label="Status bar",
            control_factory=lambda: StatusBarControl(
                "control_status_bar",
                Rect(0, 0, nc_w, 24),
                slots=[
                    StatusSlot("status", "Ready", width=80),
                    StatusSlot("line", "Ln 1", width=50, separator_after=True),
                    StatusSlot("col", "Col 1", width=50),
                ],
            ),
        ),
        ControlDefinition(
            name="expander",
            label_text="Expander",
            control_height=80,
            row_index=152,
            column_index=12,
            focusable=True,
            accessibility_role="group",
            accessibility_label="Expander",
            control_factory=lambda: ExpanderControl(
                "control_expander",
                Rect(0, 0, nc_w, 80),
                title="Details",
                body_height=50,
            ),
        ),
        ControlDefinition(
            name="breadcrumb",
            label_text="Breadcrumb",
            control_height=28,
            row_index=153,
            column_index=13,
            focusable=True,
            accessibility_role="navigation",
            accessibility_label="Breadcrumb navigation",
            control_factory=lambda: BreadcrumbControl(
                "control_breadcrumb",
                Rect(0, 0, nc_w, 28),
                items=[
                    BreadcrumbItem(label="Home", value="home"),
                    BreadcrumbItem(label="Files", value="files"),
                    BreadcrumbItem(label="Documents", value="documents"),
                ],
            ),
        ),
        ControlDefinition(
            name="split_button",
            label_text="Split Button",
            control_height=32,
            row_index=154,
            column_index=13,
            focusable=True,
            accessibility_role="button",
            accessibility_label="Split button",
            control_factory=lambda: SplitButtonControl(
                "control_split_button",
                Rect(0, 0, nc_w, 32),
                label="Save",
                options=[
                    SplitButtonOption(label="Save As...", on_click=lambda: None),
                    SplitButtonOption(label="Save All", on_click=lambda: None),
                ],
            ),
        ),
        ControlDefinition(
            name="chip_input",
            label_text="Chip Input",
            control_height=36,
            row_index=155,
            column_index=14,
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Chip input",
            control_factory=lambda: ChipInputControl(
                "control_chip_input",
                Rect(0, 0, nc_w, 36),
                placeholder="Add tag...",
                values=["Python", "GUI"],
            ),
        ),
        ControlDefinition(
            name="time_picker",
            label_text="Time Picker",
            control_height=32,
            row_index=156,
            column_index=14,
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Time picker",
            control_factory=lambda: TimePickerControl(
                "control_time_picker",
                Rect(0, 0, nc_w, 32),
                hour=9,
                minute=30,
            ),
        ),
        ControlDefinition(
            name="date_picker",
            label_text="Date Picker",
            control_height=32,
            row_index=157,
            column_index=14,
            focusable=True,
            accessibility_role="textbox",
            accessibility_label="Date picker",
            control_factory=lambda: DatePickerControl(
                "control_date_picker",
                Rect(0, 0, nc_w, 32),
            ),
        ),
    )


def build_new_controls_section_specs(
    *,
    bounds: Rect,
    content_bottom: int,
    row_gap: int,
    col_gap: int,
    overall_rows: int,
    overall_columns: int,
    slot_height_for: Callable[[int], int],
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    flow = LayoutManager()
    flow.set_column_flow_properties(
        bounds=Rect(bounds),
        overall_rows=overall_rows,
        overall_columns=overall_columns,
        column_spacing=col_gap,
        row_spacing=row_gap,
    )
    anchors = list(flow.column_flow_anchors(4))
    nc_w = min(220, anchors[0].width)

    def _make_stack(anchor):
        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=anchor,
            content_bottom=content_bottom,
            preferred_width=nc_w,
            item_gap_y=row_gap,
        )
        return stack

    nc0_stack = _make_stack(anchors[0])
    nc1_stack = _make_stack(anchors[1])
    nc2_stack = _make_stack(anchors[2])
    nc3_stack = _make_stack(anchors[3])

    nc_defs = nc_control_definitions(nc_w)
    # Definitions are distributed across four columns.
    column_groups = (
        (nc0_stack, (nc_defs[0], nc_defs[1])),
        (nc1_stack, (nc_defs[2],)),
        (nc2_stack, (nc_defs[3], nc_defs[4])),
        (nc3_stack, (nc_defs[5], nc_defs[6], nc_defs[7])),
    )

    all_specs: list[ControlPlacementSpec] = []
    for stack, group in column_groups:
        group_specs, _ = build_specs_from_column_section(
            group, stack=stack, slot_height_for=slot_height_for, overflow_gap=row_gap
        )
        all_specs.extend(group_specs)

    return tuple(all_specs), nc_w


def build_overlay_panel_spec(
    *,
    col_x: int,
    col_y: int,
    col_w: int,
    slot_h: int,
    label_height: int,
    label_gap: int,
) -> ControlPlacementSpec:
    overlay_inner_h = 90
    overlay_control_top = col_y + label_height + label_gap
    overlay_panel = OverlayPanelControl(
        "control_overlay_panel",
        Rect(col_x, overlay_control_top, col_w, overlay_inner_h),
        draw_background=True,
    )
    for index, item_text in enumerate(("Overlay Item A", "Overlay Item B", "Overlay Item C")):
        child_label = LabelControl(
            f"overlay_child_{index}",
            Rect(0, 0, col_w - 16, 22),
            item_text,
            align="left",
        )
        overlay_panel.add_at(child_label, rel_x=8, rel_y=6 + index * 26)

    return ControlPlacementSpec(
        name="overlay_panel",
        label_text="Overlay Panel",
        control=overlay_panel,
        control_rect=Rect(col_x, col_y, col_w, slot_h),
        focusable=False,
        column_index=6,
        row_index=110,
    )


def build_dock_inspector_specs(
    *,
    col_x: int,
    col_w: int,
    dock_slot_rect: Rect,
    prop_slot_rect: Rect,
    label_height: int,
    label_gap: int,
    prop_inner_h: int,
    inspectable,
    include_property_inspector: bool = True,
) -> tuple[ControlPlacementSpec, ...]:
    dock_workspace = DockWorkspace(
        DockTabs(
            "sc_dock_tabs",
            panes=[
                DockPane("editor", "Editor"),
                DockPane("preview", "Preview"),
                DockPane("console", "Console"),
            ],
        )
    )
    dock_spec = ControlPlacementSpec(
        name="dock_workspace_panel",
        label_text="Dock Workspace",
        control=DockWorkspacePanel(
            "control_dock_workspace_panel",
            Rect(0, 0, col_w, 36),
            dock_workspace,
        ),
        control_rect=Rect(dock_slot_rect),
        focusable=True,
        accessibility_role="tablist",
        accessibility_label="Dock workspace panel",
        column_index=9,
        row_index=130,
    )
    if not include_property_inspector:
        return (dock_spec,)

    prop_control_top = prop_slot_rect.top + label_height + label_gap
    prop_inspector = PropertyInspectorPanel(
        "control_property_inspector",
        Rect(col_x, prop_control_top, col_w, prop_inner_h),
        PropertyInspectorModel(inspectable),
    )

    return (
        dock_spec,
        ControlPlacementSpec(
            name="property_inspector",
            label_text="Property Inspector",
            control=prop_inspector,
            control_rect=Rect(prop_slot_rect),
            focusable=False,
            column_index=9,
            row_index=131,
        ),
    )


def build_dock_inspector_column_specs(
    *,
    stack: CellCaretLayout,
    col_x: int,
    col_w: int,
    slot_height_for: Callable[[int], int],
    row_gap: int,
    label_height: int,
    label_gap: int,
    inspectable,
    prop_inner_h: int = 160,
    include_property_inspector: bool = True,
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    dock_slot_h_desired = slot_height_for(36)
    prop_slot_h_desired = slot_height_for(prop_inner_h)

    dock_slot_rect = stack.add_slot_or_overflow(dock_slot_h_desired, overflow_gap=row_gap)
    prop_slot_rect = stack.add_slot_or_overflow(prop_slot_h_desired, overflow_gap=row_gap)

    specs = build_dock_inspector_specs(
        col_x=col_x,
        col_w=col_w,
        dock_slot_rect=dock_slot_rect,
        prop_slot_rect=prop_slot_rect,
        label_height=label_height,
        label_gap=label_gap,
        prop_inner_h=max(1, min(prop_inner_h, prop_slot_rect.height - label_height - label_gap)),
        inspectable=inspectable,
        include_property_inspector=include_property_inspector,
    )
    bottom = prop_slot_rect.bottom if include_property_inspector else dock_slot_rect.bottom
    return specs, int(bottom)


def build_progress_animation_specs(
    *,
    col_w: int,
    progress_h: int,
    progress_slot_rect: Rect,
    indeterminate_h: int,
    indeterminate_slot_rect: Rect,
    anim_slot_rect: Rect,
) -> tuple[ProgressBarControl, AnimatedImageControl, tuple[ControlPlacementSpec, ...]]:
    indeterminate_bar = ProgressBarControl(
        "control_progress_bar_indeterminate",
        Rect(0, 0, col_w, indeterminate_h),
        indeterminate=True,
    )

    import pygame as _pygame

    frame_w, frame_h = 32, 32
    atlas = _pygame.Surface((frame_w * 4, frame_h), flags=_pygame.SRCALPHA)
    for frame_index, color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
        atlas.fill(color, Rect(frame_index * frame_w, 0, frame_w, frame_h))
    sheet = SpriteSheet(atlas, frame_w=frame_w, frame_h=frame_h)
    animation = FrameAnimation(sheet, frames=list(range(4)), fps=1, loop=True)
    anim_ctrl = AnimatedImageControl(
        "control_animated_image",
        Rect(0, 0, col_w, 48),
        animation=animation,
        scale=True,
    )

    specs = (
        ControlPlacementSpec(
            name="progress_bar",
            label_text="Progress Bar",
            control=ProgressBarControl(
                "control_progress_bar",
                Rect(0, 0, col_w, progress_h),
                value=0.65,
            ),
            control_rect=Rect(progress_slot_rect),
            focusable=False,
            column_index=10,
            row_index=140,
        ),
        ControlPlacementSpec(
            name="progress_bar_indeterminate",
            label_text="Progress (Marquee)",
            control=indeterminate_bar,
            control_rect=Rect(indeterminate_slot_rect),
            focusable=False,
            column_index=10,
            row_index=141,
        ),
        ControlPlacementSpec(
            name="animated_image",
            label_text="Animated Image",
            control=anim_ctrl,
            control_rect=Rect(anim_slot_rect),
            focusable=False,
            column_index=10,
            row_index=142,
        ),
    )
    return indeterminate_bar, anim_ctrl, specs


def build_progress_column_specs(
    *,
    stack: CellCaretLayout,
    col_w: int,
    slot_height_for: Callable[[int], int],
    overflow_gap: int,
) -> tuple[ProgressBarControl, AnimatedImageControl, tuple[ControlPlacementSpec, ...], int]:
    progress_h = 20
    progress_slot_rect = stack.add_slot_or_overflow(
        slot_height_for(progress_h),
        overflow_gap=overflow_gap,
    )

    indeterminate_h = 20
    indeterminate_slot_rect = stack.add_slot_or_overflow(
        slot_height_for(indeterminate_h),
        overflow_gap=overflow_gap,
    )
    anim_slot_rect = stack.add_slot_or_overflow(
        slot_height_for(48),
        overflow_gap=overflow_gap,
    )

    indeterminate_bar, anim_ctrl, specs = build_progress_animation_specs(
        col_w=col_w,
        progress_h=progress_h,
        progress_slot_rect=progress_slot_rect,
        indeterminate_h=indeterminate_h,
        indeterminate_slot_rect=indeterminate_slot_rect,
        anim_slot_rect=anim_slot_rect,
    )
    return indeterminate_bar, anim_ctrl, specs, int(anim_slot_rect.bottom)
