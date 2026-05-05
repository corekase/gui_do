"""Controls showcase feature with grouped, varied-span layout."""

from __future__ import annotations

from pygame import Rect
import pygame

from gui_do import (
    AnimatedImageControl,
    ArrowBoxControl,
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
    SceneReturnButtonSpec,
    SceneTaskPanelSpec,
    SceneMenuStripControl,
    CellCaretLayout,
    ControlRegistry,
    ColorPickerControl,
    ContextMenuItem,
    DataGridControl,
    DatePickerControl,
    DropdownControl,
    DropdownOption,
    ExpanderControl,
    Feature,
    FixedPatternFormatter,
    FrameControl,
    FrameTimer,
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
    NotificationSpec,
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
    ToastSeverity,
    TreeControl,
    TreeNode,
    add_scene_return_button,
    build_notification_center,
    draw_controls_prewarm,
    ensure_scene_task_panel,
    make_labeled_slot_height_fn,
    ui_property,
    ControlDefinition,
    build_specs_from_column_section,
)
from gui_do.features.data_driven_runtime import (
    SceneMenuStripSpec,
    add_scene_menu_strip_from_spec,
    build_tab_builder_specs,
    create_tab_control_from_specs,
    setup_routed_runtime,
)
from gui_do.features.feature_lifecycle import ControlPlacementSpec
from demo_features.showcase.control_gallery_layout_manager import ControlGalleryLayoutManager
from .showcase_inspectable import ShowcaseInspectable
from .showcase_specs import _CONTROLS_RUNTIME_SPEC, BASICS_SUPPRESSED_LABEL_NAMES


def category_for_row(row_index: int) -> str:
    if row_index < 60:
        return "basics"
    if row_index < 100:
        return "data"
    if row_index < 140:
        return "advanced"
    return "extended"


def _relayout_category(
    *,
    category_key: str,
    category_content_bounds: Rect,
    placed_controls: list,
    gallery_layout,
    ensure_basics_aux_label,
) -> None:
    from collections.abc import Callable
    bounds = Rect(category_content_bounds)
    if bounds.width <= 0 or bounds.height <= 0:
        return
    items = [
        placed
        for placed in placed_controls
        if category_for_row(int(placed.row_index)) == category_key
    ]
    if not items:
        return
    if category_key == "basics":
        gallery_layout.relayout_basics(Rect(bounds), items, ensure_aux_label=ensure_basics_aux_label)
        return
    gallery_layout.relayout_grid_items(category_key, Rect(bounds), items)


def apply_category_visibility(
    *,
    active_key: str,
    category_content_bounds: Rect,
    placed_controls: list,
    control_labels: list,
    basics_aux_labels: dict,
    gallery_layout,
    ensure_basics_aux_label,
    basics_suppressed_label_names: frozenset,
) -> None:
    _relayout_category(
        category_key=active_key,
        category_content_bounds=Rect(category_content_bounds),
        placed_controls=placed_controls,
        gallery_layout=gallery_layout,
        ensure_basics_aux_label=ensure_basics_aux_label,
    )
    matched_labels = {placed.label for placed in placed_controls if placed.label is not None}
    if active_key == "basics":
        matched_labels.update(basics_aux_labels.values())
    for placed in placed_controls:
        show = category_for_row(int(placed.row_index)) == active_key
        placed.control.visible = show
        placed.control.enabled = show
        if placed.label is not None:
            show_label = show and not (
                active_key == "basics"
                and str(placed.name) in basics_suppressed_label_names
            )
            placed.label.visible = show_label
            placed.label.enabled = show_label
    for label in control_labels:
        if label not in matched_labels:
            label.visible = False
            label.enabled = False


def ensure_basics_aux_label(
    *,
    name: str,
    basics_aux_labels: dict,
    root,
    control_labels: list,
) -> LabelControl | None:
    label = basics_aux_labels.get(name)
    if label is not None:
        return label
    text_map = {
        "vertical_scrollbar": "Vertical scrollbar",
        "vertical_slider": "Vertical slider",
    }
    text = text_map.get(name)
    if text is None or root is None:
        return None
    label = LabelControl(
        f"controls_showcase_aux_label_{name}",
        Rect(0, 0, 1, 1),
        text,
        align="left",
    )
    root.add(label)
    control_labels.append(label)
    basics_aux_labels[name] = label
    return label


# ---------------------------------------------------------------------------
# Runtime helpers (inlined from control_showcase_runtime)
# ---------------------------------------------------------------------------

def control_has_open_popup(control) -> bool:
    if bool(getattr(control, "_open", False)):
        return True
    if bool(getattr(control, "_dropdown_open", False)):
        return True
    if bool(getattr(control, "_is_open", False)):
        return True
    open_index = getattr(control, "_open_index", -1)
    return isinstance(open_index, int) and open_index >= 0


def promote_open_popup_controls(root, controls: list) -> bool:
    if root is None:
        return False
    children = getattr(root, "children", None)
    if not isinstance(children, list) or not children:
        return False
    open_controls = [
        control
        for control in controls
        if control in children and control.visible and control.enabled and control_has_open_popup(control)
    ]
    if not open_controls:
        return False
    changed = False
    for control in open_controls:
        idx = children.index(control)
        if idx != len(children) - 1:
            children.append(children.pop(idx))
            changed = True
    if changed:
        root.invalidate()
    return changed


# ---------------------------------------------------------------------------
# Control spec factories (inlined from control_showcase_spec_factories)
# ---------------------------------------------------------------------------

def _build_list_scroll_specs(
    *,
    new_row_col_w: int,
    new_row_x0: int,
    new_row_x1: int,
    col0_y: int,
    col1_y: int,
    list_slot_h: int,
    scroll_slot_h: int,
    row_gap: int,
):
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
    group_column_specs: tuple,
    group_row_specs: tuple,
    button_trio_specs: tuple,
    toggle_trio_specs: tuple,
):
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
        intro_specs.append(ControlPlacementSpec(
            name=name, labeled=False,
            control=ArrowBoxControl(control_id, Rect(0, 0, 1, 1), degrees),
            control_rect=Rect(x, y, arrow_cell_w, arrow_cell_h),
            focusable=True, accessibility_role="button", accessibility_label=accessibility_label,
            column_index=0, row_index=row_index,
        ))
    for col_index, _ in enumerate(group_column_specs):
        button_name, button_label_text, button_control_id, button_accessibility_label = button_trio_specs[col_index]
        intro_specs.append(ControlPlacementSpec(
            name=button_name, label_text=button_label_text,
            control=ButtonControl(button_control_id, Rect(0, 0, 1, 1), "Button"),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="button",
            accessibility_label=button_accessibility_label, column_index=2, row_index=col_index,
        ))
    for col_index, _ in enumerate(group_column_specs):
        toggle_name, toggle_label_text, toggle_control_id, toggle_accessibility_label = toggle_trio_specs[col_index]
        intro_specs.append(ControlPlacementSpec(
            name=toggle_name, label_text=toggle_label_text,
            control=ToggleControl(toggle_control_id, Rect(0, 0, 1, 1), "On", "Off", pushed=False, style="round"),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="toggle",
            accessibility_label=toggle_accessibility_label, column_index=2, row_index=3 + col_index,
        ))
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
            intro_specs.append(ControlPlacementSpec(
                name=control_name, label_text=f"Group {group_letter}" if with_label else None, labeled=with_label,
                control=control, control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="button",
                accessibility_label=f"Group {group_letter} option {option_index}",
                column_index=2, row_index=row_index,
            ))
    return arrow_header_label, tuple(intro_specs)


def build_core_showcase_specs(
    *,
    tab_labels: dict,
    tab_specs: tuple,
    image_path: str,
    notification_center,
    scrollbar_content_size: int,
    scrollbar_viewport_size: int,
    scrollbar_default_offset: int,
    scrollbar_step: int,
    slider_minimum: float,
    slider_maximum: float,
    slider_default_value: float,
):
    from pathlib import Path
    return (
        ControlPlacementSpec(
            name="text_input", label_text="Text Input",
            control=TextInputControl("control_text_input", Rect(0, 0, 1, 1), placeholder="Type here"),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="textbox",
            accessibility_label="Text input", column_index=0, row_index=4,
        ),
        ControlPlacementSpec(
            name="text_area", label_text="Text Area",
            control=TextAreaControl("control_text_area", Rect(0, 0, 1, 1), value="Heading: Notes\n- First line\n- Second line"),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="textbox",
            accessibility_label="Text area", column_index=0, row_index=5,
        ),
        ControlPlacementSpec(
            name="data_grid", label_text="Data Grid",
            control=DataGridControl(
                "control_data_grid", Rect(0, 0, 1, 1),
                [GridColumn(key="name", title="Name", width=90), GridColumn(key="value", title="Value", width=70)],
                [
                    GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                    GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                    GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                    GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
                ],
                row_height=24,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="table",
            accessibility_label="Data grid", column_index=2, row_index=20,
        ),
        ControlPlacementSpec(
            name="tab", labeled=False,
            control=TabControl(
                "control_tab", Rect(0, 0, 1, 1),
                items=[TabItem(tab_key, tab_title, tab_labels[tab_key]) for tab_key, tab_title in tab_specs],
                selected_key="one",
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="tablist",
            accessibility_label="Tab control", column_index=3, row_index=30,
        ),
        ControlPlacementSpec(
            name="image", labeled=False,
            control=ImageControl(
                "control_image", Rect(0, 0, 1, 1),
                str(Path(__file__).parent.parent / image_path),
                scale=True,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=False, column_index=4, row_index=40,
        ),
        ControlPlacementSpec(
            name="notification_panel", label_text="Notification Panel",
            control=NotificationPanelControl("control_notification_panel", Rect(0, 0, 1, 1), notification_center),
            control_rect=Rect(0, 0, 1, 1), focusable=False, column_index=5, row_index=41,
        ),
        ControlPlacementSpec(
            name="horizontal_scrollbar", label_text="Horizontal Scrollbar",
            control=ScrollbarControl(
                "control_horizontal_scrollbar", Rect(0, 0, 1, 1), LayoutAxis.HORIZONTAL,
                scrollbar_content_size, scrollbar_viewport_size,
                offset=scrollbar_default_offset, step=scrollbar_step,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="scrollbar",
            accessibility_label="Horizontal scrollbar", column_index=0, row_index=6,
        ),
        ControlPlacementSpec(
            name="horizontal_slider", label_text="Horizontal Slider",
            control=SliderControl(
                "control_horizontal_slider", Rect(0, 0, 1, 1), LayoutAxis.HORIZONTAL,
                slider_minimum, slider_maximum, slider_default_value,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="slider",
            accessibility_label="Horizontal slider", column_index=0, row_index=7,
        ),
        ControlPlacementSpec(
            name="vertical_scrollbar", labeled=False,
            control=ScrollbarControl(
                "control_vertical_scrollbar", Rect(0, 0, 1, 1), LayoutAxis.VERTICAL,
                scrollbar_content_size, scrollbar_viewport_size,
                offset=scrollbar_default_offset, step=scrollbar_step,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="scrollbar",
            accessibility_label="Vertical scrollbar", column_index=1, row_index=0,
        ),
        ControlPlacementSpec(
            name="vertical_slider", labeled=False,
            control=SliderControl(
                "control_vertical_slider", Rect(0, 0, 1, 1), LayoutAxis.VERTICAL,
                slider_minimum, slider_maximum, slider_default_value,
            ),
            control_rect=Rect(0, 0, 1, 1), focusable=True, accessibility_role="slider",
            accessibility_label="Vertical slider", column_index=1, row_index=1,
        ),
    )


def _build_data_advanced_specs(
    *,
    new_col_x, col4_y, menu_slot_h, row_gap, new_col_w, tree_slot_h,
    new_row_x2, dropdown_y, new_row_col_w, dropdown_slot_h,
    splitter_y, splitter_slot_h, col2_y, rich_slot_h,
    g0x, g0y, cell_w, top_slot_h, g1x, cell_w2, g1y, panel_slot_h,
):
    return (
        ControlPlacementSpec(
            name="tree", label_text="Tree",
            control=TreeControl(
                "control_tree", Rect(0, 0, 1, 1),
                [
                    TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                    TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")]),
                ],
            ),
            control_rect=Rect(new_col_x, col4_y + menu_slot_h + row_gap, new_col_w, tree_slot_h),
            focusable=True, accessibility_role="tree", accessibility_label="Tree control",
            column_index=4, row_index=91,
        ),
        ControlPlacementSpec(
            name="dropdown", label_text="Dropdown",
            control=DropdownControl(
                "control_dropdown", Rect(0, 0, 1, 1),
                [DropdownOption(label=f"Option {index + 1}", value=index) for index in range(4)],
                placeholder="Choose",
            ),
            control_rect=Rect(new_row_x2, dropdown_y, new_row_col_w, dropdown_slot_h),
            focusable=True, accessibility_role="combobox", accessibility_label="Dropdown",
            column_index=4, row_index=81,
        ),
        ControlPlacementSpec(
            name="splitter", label_text="Splitter",
            control=SplitterControl("control_splitter", Rect(0, 0, 1, 1), axis=LayoutAxis.HORIZONTAL, ratio=0.5, min_pane_size=16),
            control_rect=Rect(new_row_x2, splitter_y, new_row_col_w, splitter_slot_h),
            focusable=True, accessibility_role="separator", accessibility_label="Splitter",
            column_index=4, row_index=82,
        ),
        ControlPlacementSpec(
            name="menu_bar", label_text="Menu Bar",
            control=MenuBarControl(
                "control_menu_bar", Rect(0, 0, 1, 1),
                [
                    MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Save")]),
                    MenuEntry("Tools", [ContextMenuItem("Run"), ContextMenuItem("Reset")]),
                ],
            ),
            control_rect=Rect(new_col_x, col4_y, new_col_w, menu_slot_h),
            focusable=False, accessibility_role="menubar", accessibility_label="Menu bar",
            column_index=4, row_index=90,
        ),
        ControlPlacementSpec(
            name="rich_label", label_text="Rich Label",
            control=RichLabelControl(
                "control_rich_label", Rect(0, 0, 1, 1),
                text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, run `deploy --env staging`, and **_ship_** after QA.",
            ),
            control_rect=Rect(new_row_x2, col2_y, new_row_col_w, rich_slot_h),
            focusable=False, column_index=4, row_index=80,
        ),
        ControlPlacementSpec(
            name="canvas", label_text="Canvas",
            control=CanvasControl("control_canvas", Rect(0, 0, 1, 1), max_events=64),
            control_rect=Rect(g0x, g0y, cell_w, top_slot_h),
            focusable=False, column_index=5, row_index=83,
        ),
        ControlPlacementSpec(
            name="frame", label_text="Frame",
            control=FrameControl("control_frame", Rect(0, 0, 1, 1), border_width=2),
            control_rect=Rect(g1x, g0y, cell_w2, top_slot_h),
            focusable=False, column_index=5, row_index=84,
        ),
        ControlPlacementSpec(
            name="panel", label_text="Panel",
            control=PanelControl("control_panel", Rect(0, 0, 1, 1), draw_background=True),
            control_rect=Rect(g0x, g1y, new_row_col_w, panel_slot_h),
            focusable=False, column_index=5, row_index=85,
        ),
    )


def build_data_tab_specs_bundle(
    *,
    anchors: tuple,
    row_gap: int,
    inner_gap: int,
    label_height: int,
    label_gap: int,
    slot_height_for,
):
    if len(anchors) < 7:
        raise ValueError("build_data_tab_specs_bundle requires at least 7 anchors")
    col0_anchor, col1_anchor, col2_anchor, col3_anchor, col4_anchor, col5_anchor, col6_anchor = anchors[:7]
    new_row_col_w = min(200, col0_anchor.width)
    new_row_x0, new_row_x1, new_row_x2, new_row_x3 = col0_anchor.left, col1_anchor.left, col2_anchor.left, col3_anchor.left
    col0_y, col1_y, col2_y, col3_y = col0_anchor.top, col1_anchor.top, col2_anchor.top, col3_anchor.top
    list_slot_h = slot_height_for(120)
    scroll_slot_h = slot_height_for(120)
    list_selection_label, scroll_selection_label, list_scroll_specs = _build_list_scroll_specs(
        new_row_col_w=new_row_col_w, new_row_x0=new_row_x0, new_row_x1=new_row_x1,
        col0_y=col0_y, col1_y=col1_y, list_slot_h=list_slot_h, scroll_slot_h=scroll_slot_h, row_gap=row_gap,
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
    g0x, g1x = new_row_x3, new_row_x3 + cell_w + inner_gap
    g0y = col3_y
    top_slot_h = cell_w + label_height + label_gap
    g1y = g0y + top_slot_h + row_gap
    data_advanced_specs = _build_data_advanced_specs(
        new_col_x=new_col_x, col4_y=col4_y, menu_slot_h=menu_slot_h, row_gap=row_gap,
        new_col_w=new_col_w, tree_slot_h=tree_slot_h, new_row_x2=new_row_x2,
        dropdown_y=dropdown_y, new_row_col_w=new_row_col_w, dropdown_slot_h=dropdown_slot_h,
        splitter_y=splitter_y, splitter_slot_h=splitter_slot_h, col2_y=col2_y, rich_slot_h=rich_slot_h,
        g0x=g0x, g0y=g0y, cell_w=cell_w, top_slot_h=top_slot_h, g1x=g1x, cell_w2=cell_w2, g1y=g1y,
        panel_slot_h=slot_height_for(68),
    )
    return (list_selection_label, scroll_selection_label, list_scroll_specs, data_advanced_specs, col5_anchor, col6_anchor)


def _formatted_input_definitions(col_w: int):
    _raw_defs = (
        ("numeric_fmt_input", "Numeric Format", NumericFormatter(decimals=2, thousands_sep=","),
         "control_numeric_fmt_input", "12500", "0.00", "Numeric formatted text input", 120),
        ("pattern_fmt_input", "Pattern Format", PatternFormatter("###-###-####"),
         "control_pattern_fmt_input", "5551234567", "###-###-####", "Pattern formatted text input", 121),
        ("fixed_pattern_fmt_input", "Fixed Pattern Format", FixedPatternFormatter("#####-####"),
         "control_fixed_pattern_fmt_input", "941010001", "#####-####", "Fixed pattern formatted text input", 122),
    )
    return tuple(
        ControlDefinition(
            name=name, label_text=label_text, control_height=30, row_index=row_index,
            control_factory=(
                lambda f=formatter, cid=control_id, rv=raw_value, ph=placeholder:
                f.create_text_input(str(cid), Rect(0, 0, int(col_w), 30), raw_value=str(rv), placeholder=str(ph))
            ),
            column_index=7, focusable=True, accessibility_role="textbox", accessibility_label=accessibility_label,
        )
        for name, label_text, formatter, control_id, raw_value, placeholder, accessibility_label, row_index in _raw_defs
    )


def _col6_control_definitions(col6_w: int):
    return (
        ControlDefinition(
            name="spinner", label_text="Spinner", control_height=30, row_index=100,
            control_factory=lambda: SpinnerControl(
                "control_spinner", Rect(0, 0, col6_w, 30), value=25, min_value=0, max_value=100, step=1, decimals=0, on_change=lambda v, _r: None,
            ),
        ),
        ControlDefinition(
            name="range_slider", label_text="Range Slider", control_height=24, row_index=101,
            control_factory=lambda: RangeSliderControl(
                "control_range_slider", Rect(0, 0, col6_w, 24), min_value=0, max_value=100, low_value=20, high_value=80, on_change=lambda lo, hi, _r: None,
            ),
        ),
        ControlDefinition(
            name="color_picker", label_text="Color Picker", control_height=180, row_index=102,
            control_factory=lambda: ColorPickerControl(
                "control_color_picker", Rect(0, 0, col6_w, 180), color=(64, 128, 255), on_change=lambda c: None,
            ),
        ),
    )


def build_col6_section_specs(
    *,
    stack: CellCaretLayout,
    col_x: int,
    col_y: int,
    col_w: int,
    slot_height_for,
    overflow_gap: int,
    column_index: int = 5,
):
    defs = tuple(
        ControlDefinition(name=d.name, label_text=d.label_text, control_height=d.control_height,
                          row_index=d.row_index, control_factory=d.control_factory, column_index=column_index)
        for d in _col6_control_definitions(col_w)
    )
    return build_specs_from_column_section(defs, stack=stack, slot_height_for=slot_height_for, overflow_gap=overflow_gap)


def build_formatted_input_section_specs(
    *,
    stack: CellCaretLayout,
    col_x: int,
    col_y: int,
    col_w: int,
    slot_height_for,
    overflow_gap: int,
    column_index: int = 7,
):
    defs = tuple(
        ControlDefinition(
            name=d.name, label_text=d.label_text, control_height=d.control_height,
            row_index=d.row_index, control_factory=d.control_factory, column_index=column_index,
            focusable=d.focusable, accessibility_role=d.accessibility_role, accessibility_label=d.accessibility_label,
        )
        for d in _formatted_input_definitions(col_w)
    )
    return build_specs_from_column_section(defs, stack=stack, slot_height_for=slot_height_for, overflow_gap=overflow_gap)


def _nc_control_definitions(nc_w: int, app):
    return (
        ControlDefinition(
            name="toolbar", label_text="Toolbar", control_height=36, row_index=150, column_index=11,
            focusable=True, accessibility_role="toolbar", accessibility_label="Toolbar",
            control_factory=lambda: ToolbarControl(
                "control_toolbar", Rect(0, 0, nc_w, 36),
                items=[ToolbarItem(label="Cut", action_id="cut"), ToolbarItem(label="Copy", action_id="copy"),
                       ToolbarItem(separator=True), ToolbarItem(label="Paste", action_id="paste")],
            ),
        ),
        ControlDefinition(
            name="status_bar", label_text="Status Bar", control_height=24, row_index=151, column_index=11,
            focusable=False, accessibility_role="status", accessibility_label="Status bar",
            control_factory=lambda: StatusBarControl(
                "control_status_bar", Rect(0, 0, nc_w, 24),
                slots=[StatusSlot("status", "Ready", width=80), StatusSlot("line", "Ln 1", width=50, separator_after=True), StatusSlot("col", "Col 1", width=50)],
            ),
        ),
        ControlDefinition(
            name="expander", label_text="Expander", control_height=80, row_index=152, column_index=12,
            focusable=True, accessibility_role="group", accessibility_label="Expander",
            control_factory=lambda: ExpanderControl("control_expander", Rect(0, 0, nc_w, 80), title="Details", body_height=50),
        ),
        ControlDefinition(
            name="breadcrumb", label_text="Breadcrumb", control_height=28, row_index=153, column_index=13,
            focusable=True, accessibility_role="navigation", accessibility_label="Breadcrumb navigation",
            control_factory=lambda: BreadcrumbControl(
                "control_breadcrumb", Rect(0, 0, nc_w, 28),
                items=[BreadcrumbItem(label="Home", value="home"), BreadcrumbItem(label="Files", value="files"), BreadcrumbItem(label="Documents", value="documents")],
            ),
        ),
        ControlDefinition(
            name="split_button", label_text="Split Button", control_height=32, row_index=154, column_index=13,
            focusable=True, accessibility_role="button", accessibility_label="Split button",
            control_factory=lambda: SplitButtonControl(
                "control_split_button", Rect(0, 0, nc_w, 32), label="Save",
                options=[SplitButtonOption(label="Save As...", on_click=lambda: None), SplitButtonOption(label="Save All", on_click=lambda: None)],
            ),
        ),
        ControlDefinition(
            name="chip_input", label_text="Chip Input", control_height=36, row_index=155, column_index=14,
            focusable=True, accessibility_role="textbox", accessibility_label="Chip input",
            control_factory=lambda: ChipInputControl("control_chip_input", Rect(0, 0, nc_w, 36), placeholder="Add tag...", values=["Python", "GUI"]),
        ),
        ControlDefinition(
            name="time_picker", label_text="Time Picker", control_height=32, row_index=156, column_index=14,
            focusable=True, accessibility_role="textbox", accessibility_label="Time picker",
            control_factory=lambda: TimePickerControl("control_time_picker", Rect(0, 0, nc_w, 32), hour=9, minute=30),
        ),
        ControlDefinition(
            name="date_picker", label_text="Date Picker", control_height=32, row_index=157, column_index=14,
            focusable=True, accessibility_role="textbox", accessibility_label="Date picker",
            control_factory=lambda: DatePickerControl("control_date_picker", Rect(0, 0, nc_w, 32)),
        ),
        ControlDefinition(
            name="scene_menu_strip", label_text="Scene Menu Strip", control_height=30, row_index=158, column_index=14,
            focusable=False, accessibility_role="menubar", accessibility_label="Scene menu strip",
            control_factory=lambda: SceneMenuStripControl(
                "control_scene_menu_strip",
                Rect(0, 0, nc_w, 30),
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
    slot_height_for,
    app,
):
    flow = LayoutManager()
    flow.set_column_flow_properties(
        bounds=Rect(bounds), overall_rows=overall_rows, overall_columns=overall_columns,
        column_spacing=col_gap, row_spacing=row_gap,
    )
    anchors = list(flow.column_flow_anchors(4))
    nc_w = min(220, anchors[0].width)

    def _make_stack(anchor):
        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=anchor, content_bottom=content_bottom, preferred_width=nc_w, item_gap_y=row_gap,
        )
        return stack

    nc_defs = _nc_control_definitions(nc_w, app)
    column_groups = (
        (_make_stack(anchors[0]), (nc_defs[0], nc_defs[1])),
        (_make_stack(anchors[1]), (nc_defs[2],)),
        (_make_stack(anchors[2]), (nc_defs[3], nc_defs[4])),
        (_make_stack(anchors[3]), (nc_defs[5], nc_defs[6], nc_defs[7], nc_defs[8])),
    )
    all_specs: list[ControlPlacementSpec] = []
    for stack, group in column_groups:
        group_specs, _ = build_specs_from_column_section(group, stack=stack, slot_height_for=slot_height_for, overflow_gap=row_gap)
        all_specs.extend(group_specs)
    return tuple(all_specs), nc_w


def build_overlay_panel_spec(*, col_x: int, col_y: int, col_w: int, slot_h: int, label_height: int, label_gap: int):
    overlay_inner_h = 90
    overlay_control_top = col_y + label_height + label_gap
    overlay_panel = OverlayPanelControl("control_overlay_panel", Rect(col_x, overlay_control_top, col_w, overlay_inner_h), draw_background=True)
    for index, item_text in enumerate(("Overlay Item A", "Overlay Item B", "Overlay Item C")):
        child_label = LabelControl(f"overlay_child_{index}", Rect(0, 0, col_w - 16, 22), item_text, align="left")
        overlay_panel.add_at(child_label, rel_x=8, rel_y=6 + index * 26)
    return ControlPlacementSpec(
        name="overlay_panel", label_text="Overlay Panel", control=overlay_panel,
        control_rect=Rect(col_x, col_y, col_w, slot_h), focusable=False, column_index=6, row_index=110,
    )


def _build_dock_inspector_specs(
    *, col_x, col_w, dock_slot_rect, prop_slot_rect, label_height, label_gap,
    prop_inner_h, inspectable, include_property_inspector=True,
):
    dock_workspace = DockWorkspace(DockTabs("sc_dock_tabs", panes=[DockPane("editor", "Editor"), DockPane("preview", "Preview"), DockPane("console", "Console")]))
    dock_spec = ControlPlacementSpec(
        name="dock_workspace_panel", label_text="Dock Workspace",
        control=DockWorkspacePanel("control_dock_workspace_panel", Rect(0, 0, col_w, 36), dock_workspace),
        control_rect=Rect(dock_slot_rect), focusable=True, accessibility_role="tablist",
        accessibility_label="Dock workspace panel", column_index=9, row_index=130,
    )
    if not include_property_inspector:
        return (dock_spec,)
    prop_control_top = prop_slot_rect.top + label_height + label_gap
    prop_inspector = PropertyInspectorPanel(
        "control_property_inspector", Rect(col_x, prop_control_top, col_w, prop_inner_h),
        PropertyInspectorModel(inspectable),
    )
    return (dock_spec, ControlPlacementSpec(
        name="property_inspector", label_text="Property Inspector", control=prop_inspector,
        control_rect=Rect(prop_slot_rect), focusable=False, column_index=9, row_index=131,
    ))


def build_dock_inspector_column_specs(
    *, stack, col_x, col_w, slot_height_for, row_gap, label_height, label_gap,
    inspectable, prop_inner_h=160, include_property_inspector=True,
):
    dock_slot_h_desired = slot_height_for(36)
    prop_slot_h_desired = slot_height_for(prop_inner_h)
    dock_slot_rect = stack.add_slot_or_overflow(dock_slot_h_desired, overflow_gap=row_gap)
    prop_slot_rect = stack.add_slot_or_overflow(prop_slot_h_desired, overflow_gap=row_gap)
    specs = _build_dock_inspector_specs(
        col_x=col_x, col_w=col_w, dock_slot_rect=dock_slot_rect, prop_slot_rect=prop_slot_rect,
        label_height=label_height, label_gap=label_gap,
        prop_inner_h=max(1, min(prop_inner_h, prop_slot_rect.height - label_height - label_gap)),
        inspectable=inspectable, include_property_inspector=include_property_inspector,
    )
    bottom = prop_slot_rect.bottom if include_property_inspector else dock_slot_rect.bottom
    return specs, int(bottom)


def _build_progress_animation_specs(*, col_w, progress_h, progress_slot_rect, indeterminate_h, indeterminate_slot_rect, anim_slot_rect):
    indeterminate_bar = ProgressBarControl("control_progress_bar_indeterminate", Rect(0, 0, col_w, indeterminate_h), indeterminate=True)
    import pygame as _pygame
    frame_w, frame_h = 32, 32
    atlas = _pygame.Surface((frame_w * 4, frame_h), flags=_pygame.SRCALPHA)
    for frame_index, color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
        atlas.fill(color, Rect(frame_index * frame_w, 0, frame_w, frame_h))
    sheet = SpriteSheet(atlas, frame_w=frame_w, frame_h=frame_h)
    animation = FrameAnimation(sheet, frames=list(range(4)), fps=1, loop=True)
    anim_ctrl = AnimatedImageControl("control_animated_image", Rect(0, 0, col_w, 48), animation=animation, scale=True)
    specs = (
        ControlPlacementSpec(
            name="progress_bar", label_text="Progress Bar",
            control=ProgressBarControl("control_progress_bar", Rect(0, 0, col_w, progress_h), value=0.65),
            control_rect=Rect(progress_slot_rect), focusable=False, column_index=10, row_index=140,
        ),
        ControlPlacementSpec(
            name="progress_bar_indeterminate", label_text="Progress (Marquee)", control=indeterminate_bar,
            control_rect=Rect(indeterminate_slot_rect), focusable=False, column_index=10, row_index=141,
        ),
        ControlPlacementSpec(
            name="animated_image", label_text="Animated Image", control=anim_ctrl,
            control_rect=Rect(anim_slot_rect), focusable=False, column_index=10, row_index=142,
        ),
    )
    return indeterminate_bar, anim_ctrl, specs


def build_progress_column_specs(*, stack, col_w, slot_height_for, overflow_gap):
    progress_h = 20
    progress_slot_rect = stack.add_slot_or_overflow(slot_height_for(progress_h), overflow_gap=overflow_gap)
    indeterminate_h = 20
    indeterminate_slot_rect = stack.add_slot_or_overflow(slot_height_for(indeterminate_h), overflow_gap=overflow_gap)
    anim_slot_rect = stack.add_slot_or_overflow(slot_height_for(48), overflow_gap=overflow_gap)
    indeterminate_bar, anim_ctrl, specs = _build_progress_animation_specs(
        col_w=col_w, progress_h=progress_h, progress_slot_rect=progress_slot_rect,
        indeterminate_h=indeterminate_h, indeterminate_slot_rect=indeterminate_slot_rect, anim_slot_rect=anim_slot_rect,
    )
    return indeterminate_bar, anim_ctrl, specs, int(anim_slot_rect.bottom)


class ShowcaseFeature(Feature):
    """Render all controls except task panel/window in grouped, non-uniform layouts."""

    HOST_REQUIREMENTS = {
        "build": ("app", "scene_presentation", "control_showcase_root"),
        "bind_runtime": ("app",),
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

    IMAGE_PATH = "data/images/realize.png"

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

        self._registry: ControlRegistry | None = None
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
        self._gallery_layout = ControlGalleryLayoutManager(
            inner_gap=self.INNER_GAP,
            label_height=self.LABEL_HEIGHT,
            label_gap=self.LABEL_GAP,
        )

    def build(self, host) -> None:
        self._showcase_root = host.control_showcase_root
        host.control_showcase_menu_bar = add_scene_menu_strip_from_spec(
            host.control_showcase_root,
            host,
            SceneMenuStripSpec(
                control_id="control_showcase_menu_bar",
                rect=Rect(0, 0, host.control_showcase_root.rect.width, 28),
                scene_name="control_showcase",
                scenes_shown=True,
                windows_shown=True,
                tools_exclude_labels=("Open Command Palette (F5)",),
            ),
        )

        if self.rect.width <= 0 or self.rect.height <= 0:
            self.rect = self._default_rect(host)

        self._registry = ControlRegistry(host.control_showcase_root)

        root_content_rect = Rect(
            self.rect.left + self.CONTENT_PADDING_X,
            self.rect.top + self.CONTENT_PADDING_Y,
            max(1, self.rect.width - (self.CONTENT_PADDING_X * 2)),
            max(1, self.rect.height - (self.CONTENT_PADDING_Y * 2)),
        )

        # Top-level category tabs drive which control groups are visible and interactive.
        tab_strip_h = int(self.CATEGORY_TAB_STRIP_HEIGHT)
        tab_strip_gap = int(self.CATEGORY_TAB_STRIP_GAP)
        category_tab_specs = build_tab_builder_specs(
            self.SHOWCASE_CATEGORY_TABS,
            builder_prefix="",
            builder_suffix="",
        )
        category_tabs = create_tab_control_from_specs(
            "control_showcase_category_tabs",
            Rect(root_content_rect.left, root_content_rect.top, root_content_rect.width, tab_strip_h),
            category_tab_specs,
            selected_key=self._active_category_key,
            on_change=lambda key: self._set_active_category(host, key),
        )
        category_tabs.set_accessibility(role="tablist", label="Showcase categories")
        self._registry.add_control(category_tabs)
        self._category_tabs = category_tabs

        # Build nested content bounds from the base rect so downstream layout
        # can consume a composable source instead of raw arithmetic-only rects.
        content_rect = LayoutManager.as_layout_rect(root_content_rect).inset((0, tab_strip_h + tab_strip_gap, 0, 0)).resolve_layout_rect()

        slot_h = make_labeled_slot_height_fn(self.LABEL_HEIGHT, self.LABEL_GAP)

        column_width = 320
        row_gap = 8
        col_gap = 4
        arrow_control_size = 32

        # Reserve bottom space for the task panel so per-tab reflow does not
        # collide with docked task controls.
        self._category_content_bounds = LayoutManager.as_layout_rect(content_rect).inset((0, 0, 0, self.TASK_PANEL_HEIGHT + row_gap)).resolve_layout_rect()

        col0_x = content_rect.left
        col0_y = content_rect.top

        arrow_header_label, intro_specs = build_intro_specs(
            col0_x=col0_x,
            col0_y=col0_y,
            column_width=column_width,
            inner_gap=self.INNER_GAP,
            label_height=self.LABEL_HEIGHT,
            label_gap=self.LABEL_GAP,
            row_gap=row_gap,
            arrow_control_size=arrow_control_size,
            group_column_specs=self.SHOWCASE_GROUP_COLUMN_SPECS,
            group_row_specs=self.SHOWCASE_GROUP_ROW_SPECS,
            button_trio_specs=self.SHOWCASE_BUTTON_TRIO_SPECS,
            toggle_trio_specs=self.SHOWCASE_TOGGLE_TRIO_SPECS,
        )
        self._registry.add_label(arrow_header_label)

        # Compute metrics needed for data_grid_bottom (drives data-tab initial layout Y).
        button_slot_h = slot_h(34)
        group_first_slot_h = slot_h(34)
        group_other_h = 34
        lane_controls_h = (
            button_slot_h + row_gap
            + button_slot_h + row_gap
            + group_first_slot_h + row_gap
            + group_other_h + row_gap
            + group_other_h
        )
        mid_block_h = slot_h(120)
        data_grid_bottom = col0_y + lane_controls_h + row_gap + mid_block_h

        self._registry.register(intro_specs)

        # Remaining-grid items are declared as placement specs so this section
        # stays data-driven and delegates registration details to lifecycle helpers.
        tab_labels = {
            tab_key: LabelControl(
                f"ctrl_tab_lbl_{tab_key}",
                Rect(0, 0, 1, 30),
                tab_title,
                align="left",
            )
            for tab_key, tab_title in self.SHOWCASE_TAB_SPECS
        }

        self._showcase_notification_center = build_notification_center(
            (
                NotificationSpec("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS),
                NotificationSpec("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING),
            ),
            max_records=6,
        )
        placement_specs = build_core_showcase_specs(
            tab_labels=tab_labels,
            tab_specs=self.SHOWCASE_TAB_SPECS,
            image_path=self.IMAGE_PATH,
            notification_center=self._showcase_notification_center,
            scrollbar_content_size=self.SCROLLBAR_CONTENT_SIZE,
            scrollbar_viewport_size=self.SCROLLBAR_VIEWPORT_SIZE,
            scrollbar_default_offset=self.SCROLLBAR_DEFAULT_OFFSET,
            scrollbar_step=self.SCROLLBAR_STEP,
            slider_minimum=self.SLIDER_MINIMUM,
            slider_maximum=self.SLIDER_MAXIMUM,
            slider_default_value=self.SLIDER_DEFAULT_VALUE,
        )

        self._registry.register(placement_specs)

        # New row of columns starts from the left edge at data_grid bottom + 10.
        new_row_y = data_grid_bottom + 10
        anchors = LayoutManager.column_flow_anchors_for(
            Rect(content_rect.left, new_row_y, content_rect.width, max(1, content_rect.bottom - new_row_y)),
            8,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            column_spacing=col_gap,
            row_spacing=row_gap,
        )
        # Data-tab focusable controls are created in the intended traversal order:
        # list_view → scroll_view → tree → dropdown → splitter → menu_bar.
        (
            list_selection_label,
            scroll_selection_label,
            list_scroll_specs,
            data_advanced_specs,
            col5_anchor,
            col6_anchor,
        ) = build_data_tab_specs_bundle(
            anchors=anchors,
            row_gap=row_gap,
            inner_gap=self.INNER_GAP,
            label_height=self.LABEL_HEIGHT,
            label_gap=self.LABEL_GAP,
            slot_height_for=slot_h,
        )
        self._registry.add_label(list_selection_label)
        self._registry.register(list_scroll_specs)
        self._registry.add_label(scroll_selection_label)
        self._registry.register(data_advanced_specs)

        # col 5: spinner, range slider, color picker
        col6_stack, col6_x, col6_w, col6_y = CellCaretLayout.column_stack_from_anchor(
            anchor=col5_anchor,
            content_bottom=content_rect.bottom,
            preferred_width=220,
            item_gap_y=row_gap,
        )

        col6_place_specs, _ = build_col6_section_specs(
            stack=col6_stack,
            col_x=col6_x,
            col_y=col6_y,
            col_w=col6_w,
            slot_height_for=slot_h,
            overflow_gap=row_gap,
            column_index=5,
        )
        self._registry.register(col6_place_specs)

        # OverlayPanelControl
        _, col7_x, col7_w, col7_y = CellCaretLayout.column_stack_from_anchor(
            anchor=col6_anchor,
            content_bottom=content_rect.bottom,
            preferred_width=200,
            item_gap_y=row_gap,
        )
        overlay_slot_h = slot_h(90)
        overlay_spec = build_overlay_panel_spec(
            col_x=col7_x,
            col_y=col7_y,
            col_w=col7_w,
            slot_h=overlay_slot_h,
            label_height=self.LABEL_HEIGHT,
            label_gap=self.LABEL_GAP,
        )
        self._registry.register(
            (
                overlay_spec,
            ),
        )

        section_top = col6_anchor.top + col6_anchor.height + row_gap
        section_anchors = LayoutManager.column_flow_anchors_for(
            Rect(content_rect.left, section_top, content_rect.width, max(1, content_rect.bottom - section_top)),
            3,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            column_spacing=col_gap,
            row_spacing=row_gap,
        )

        # Column 0: format-aware text inputs.
        col7_anchor, col9_anchor, col10_anchor = section_anchors
        col7_stack, col7_x, col7_w, col7_y = CellCaretLayout.column_stack_from_anchor(
            anchor=col7_anchor,
            content_bottom=content_rect.bottom,
            preferred_width=220,
            item_gap_y=row_gap,
        )

        formatted_place_specs, col7_bottom = build_formatted_input_section_specs(
            stack=col7_stack,
            col_x=col7_x,
            col_y=col7_y,
            col_w=col7_w,
            slot_height_for=slot_h,
            overflow_gap=row_gap,
            column_index=7,
        )
        self._registry.register(formatted_place_specs)
        col7_y = col7_bottom

        # Column 1 in this row: Dock workspace and property inspector.
        col9_stack, col9_x, col9_w, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=col9_anchor,
            content_bottom=content_rect.bottom,
            preferred_width=260,
            item_gap_y=row_gap,
        )
        dock_specs, col9_bottom = build_dock_inspector_column_specs(
            stack=col9_stack,
            col_x=col9_x,
            col_w=col9_w,
            slot_height_for=slot_h,
            row_gap=row_gap,
            label_height=self.LABEL_HEIGHT,
            label_gap=self.LABEL_GAP,
            prop_inner_h=160,
            inspectable=ShowcaseInspectable(),
            include_property_inspector=True,
        )
        self._registry.register(dock_specs)

        # Column 2 in this row: progress controls and animated image.
        col10_stack, _, col10_w, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=col10_anchor,
            content_bottom=content_rect.bottom,
            preferred_width=220,
            item_gap_y=row_gap,
        )

        indeterminate_bar, anim_ctrl, progress_specs, col10_bottom = build_progress_column_specs(
            stack=col10_stack,
            col_w=col10_w,
            slot_height_for=slot_h,
            overflow_gap=row_gap,
        )
        self._indeterminate_bar = indeterminate_bar
        self._showcase_anim_ctrl = anim_ctrl
        self._registry.register(progress_specs)

        # ---------------------------------------------------------------
        # New controls section — placed below the tallest control column in
        # the previous section so controls never overlap.
        # ---------------------------------------------------------------
        prev_section_bottom = max(
            col7_y,
            col9_bottom,
            col10_bottom,
        )
        new_ctrl_section_top = prev_section_bottom + row_gap
        nc_bounds = Rect(
            content_rect.left,
            new_ctrl_section_top,
            content_rect.width,
            max(1, content_rect.bottom - new_ctrl_section_top),
        )
        nc_place_specs, _ = build_new_controls_section_specs(
            bounds=nc_bounds,
            content_bottom=content_rect.bottom,
            row_gap=row_gap,
            col_gap=col_gap,
            overall_rows=self.LAYOUT_OVERALL_ROWS_CONSTANT,
            overall_columns=self.LAYOUT_OVERALL_COLUMNS_CONSTANT,
            slot_height_for=slot_h,
            app=host.app,
        )
        self._registry.register(nc_place_specs)

        self._build_scene_task_panel(host)

        # Apply initial tab category visibility after all placements are registered.
        self._apply_category_visibility(host)

        self._initial_focus_control = host.control_showcase_menu_bar
        self._pending_initial_focus = True

    def bind_runtime(self, host) -> None:
        """Wire runtime hotkeys from the declarative runtime spec."""
        setup_routed_runtime(self, host, _CONTROLS_RUNTIME_SPEC)

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
        menu_strip = getattr(_host, "control_showcase_menu_bar", None)
        reg = self._registry
        tracked = ([*reg.control_labels, *reg.controls] if reg is not None else [])
        draw_controls_prewarm(surface, theme, [menu_strip, *tracked, self.task_panel, self.showcase_return_button])


    _BASICS_SUPPRESSED_LABEL_NAMES: frozenset[str] = BASICS_SUPPRESSED_LABEL_NAMES

    def _set_active_category(self, host, key: str) -> None:
        valid_keys = {k for k, _ in self.SHOWCASE_CATEGORY_TABS}
        if key not in valid_keys:
            return
        if self._active_category_key == key:
            return
        self._active_category_key = key
        self._apply_category_visibility(host)

    def _apply_category_visibility(self, host) -> None:
        reg = self._registry
        apply_category_visibility(
            active_key=self._active_category_key,
            category_content_bounds=Rect(self._category_content_bounds),
            placed_controls=(reg.placed_controls if reg is not None else []),
            control_labels=(reg.control_labels if reg is not None else []),
            basics_aux_labels=self._basics_aux_labels,
            gallery_layout=self._gallery_layout,
            ensure_basics_aux_label=self._ensure_basics_aux_label,
            basics_suppressed_label_names=self._BASICS_SUPPRESSED_LABEL_NAMES,
        )

        # If current focus became hidden, park focus on the category tab strip.
        focused = getattr(host.app.focus, "focused", None)
        if focused is not None and not getattr(focused, "visible", True):
            if self._category_tabs is not None and self._category_tabs.visible and self._category_tabs.enabled:
                host.app.focus.set_focus(self._category_tabs)

    def _ensure_basics_aux_label(self, name: str) -> LabelControl | None:
        reg = self._registry
        return ensure_basics_aux_label(
            name=name,
            basics_aux_labels=self._basics_aux_labels,
            root=self._showcase_root,
            control_labels=(reg.control_labels if reg is not None else []),
        )

    def _promote_open_popup_controls(self, host) -> None:
        root = getattr(host, "control_showcase_root", None)
        reg = self._registry
        promote_open_popup_controls(root, (reg.controls if reg is not None else []))

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


    def _build_scene_task_panel(self, host) -> None:
        self.task_panel = ensure_scene_task_panel(
            host,
            SceneTaskPanelSpec(
                scene_name=self.scene_name,
                control_id="control_showcase_task_panel",
                height=self.TASK_PANEL_HEIGHT,
                hidden_peek_pixels=self.TASK_PANEL_HIDDEN_PEEK_PIXELS,
                animation_step_px=self.TASK_PANEL_ANIMATION_STEP_PX,
                dock_bottom=True,
                auto_hide=True,
            ),
        )
        self.showcase_return_button = add_scene_return_button(
            self.task_panel,
            host,
            SceneReturnButtonSpec(
                control_id="showcase_return",
                label="Return",
                target_scene="main",
                go_to_attr="go_to_main",
                left=self.TASK_PANEL_BUTTON_LEFT,
                top_offset=self.TASK_PANEL_BUTTON_TOP_OFFSET,
                width=self.TASK_PANEL_BUTTON_WIDTH,
                height=self.TASK_PANEL_BUTTON_HEIGHT,
                style="angle",
                accessibility_role="button",
                accessibility_label="Return to main",
                # Keep showcase Tab traversal within the feature surface; task panel
                # actions remain clickable but are not part of feature focus cycling.
                tab_index=-1,
            ),
        )
