"""Controls showcase feature — tabbed gallery of all gui_do controls."""

from __future__ import annotations

from pathlib import Path

import pygame
from pygame import Rect

from gui_do import (
    AnimatedImageControl,
    ArrowBoxControl,
    BreadcrumbControl,
    BreadcrumbItem,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    CellCaretLayout,
    ChipInputControl,
    ColorPickerControl,
    ContextMenuItem,
    ControlDefinition,
    ControlRegistry,
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
    FrameControl,
    FrameTimer,
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
    RowCellSpec,
    SceneMenuStripControl,
    SceneTaskPanelSpec,
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
    TaskPanelLinearLayoutSpec,
    TaskPanelSceneNavButtonSpec,
    TaskPanelWindowToggleGroupSpec,
    TextAreaControl,
    TextInputControl,
    TimePickerControl,
    ToastSeverity,
    ToggleControl,
    ToolbarControl,
    ToolbarItem,
    TreeControl,
    TreeNode,
    add_scene_task_panel_items,
    apply_category_visibility,
    build_horizontal_row_specs,
    build_multi_column_grid_specs,
    build_notification_center,
    create_task_panel_linear_layout,
    draw_controls_prewarm,
    ensure_scene_task_panel,
    make_labeled_slot_height_fn,
)
from gui_do.features.data_driven_runtime import (
    SceneMenuStripSpec,
    add_scene_menu_strip_from_spec,
    build_tab_builder_specs,
    create_tab_control_from_specs,
    setup_routed_runtime,
)
from gui_do.features.feature_lifecycle import ControlPlacementSpec
from .showcase_inspectable import ShowcaseInspectable
from .showcase_specs import _CONTROLS_RUNTIME_SPEC


# ---------------------------------------------------------------------------
# Category routing  (showcase-specific — not a general gui_do helper)
# ---------------------------------------------------------------------------

def category_for_row(row_index: int) -> str:
    """Return the category key for the given placement row index."""
    if row_index < 60:
        return "basics"
    if row_index < 100:
        return "data"
    if row_index < 140:
        return "advanced"
    return "extended"


# ---------------------------------------------------------------------------
# ShowcaseFeature
# ---------------------------------------------------------------------------

class ShowcaseFeature(Feature):
    """Tabbed control gallery showcasing all gui_do controls."""

    HOST_REQUIREMENTS = {
        "build": ("app", "scene_presentation", "control_showcase_root"),
        "bind_runtime": ("app",),
        "on_update": ("app",),
        "prewarm": ("app",),
    }

    # Layout
    ROOT_MARGIN_X = 24
    ROOT_MARGIN_TOP = 24
    ROOT_MARGIN_BOTTOM = 86
    CONTENT_PADDING_X = 4
    CONTENT_PADDING_Y = 12
    LABEL_HEIGHT = 18
    LABEL_GAP = 4
    CATEGORY_TAB_STRIP_HEIGHT = 34
    CATEGORY_TAB_STRIP_GAP = 8
    ROW_GAP = 8
    BASICS_COL_GAP = 10
    BASICS_INNER_GAP = 6

    # Control values
    SLIDER_MINIMUM = 0.0
    SLIDER_MAXIMUM = 100.0
    SLIDER_DEFAULT_VALUE = 25.0
    SCROLLBAR_CONTENT_SIZE = 1000
    SCROLLBAR_VIEWPORT_SIZE = 240
    SCROLLBAR_DEFAULT_OFFSET = 0
    SCROLLBAR_STEP = 24

    IMAGE_PATH = "data/images/realize.png"

    # Task panel
    TASK_PANEL_HEIGHT = 50
    TASK_PANEL_HIDDEN_PEEK_PIXELS = 6
    TASK_PANEL_ANIMATION_STEP_PX = 8
    TASK_PANEL_BUTTON_WIDTH = 110
    TASK_PANEL_BUTTON_HEIGHT = 30
    TASK_PANEL_BUTTON_LEFT = 16
    TASK_PANEL_BUTTON_TOP_OFFSET = 10
    TASK_PANEL_SLOT_SPACING = 10

    # Category tab definitions: (key, label)
    SHOWCASE_CATEGORY_TABS = (
        ("basics", "Basics"),
        ("data", "Data"),
        ("advanced", "Advanced"),
        ("extended", "Extended"),
    )

    # Column counts per category (controls laid out left-to-right across columns)
    BASICS_COLUMNS = 4
    DATA_COLUMNS = 3
    ADVANCED_COLUMNS = 2
    EXTENDED_COLUMNS = 1

    def __init__(self, rect: Rect | None = None) -> None:
        super().__init__("controls_showcase", scene_name="control_showcase")
        self.rect = Rect(rect) if rect is not None else Rect(0, 0, 0, 0)

        self._registry: ControlRegistry | None = None
        self._category_tabs: TabControl | None = None
        self._active_category_key: str = "basics"
        self._showcase_root = None
        self._showcase_notification_center: NotificationCenter | None = None
        self._indeterminate_bar: ProgressBarControl | None = None
        self._showcase_anim_ctrl: AnimatedImageControl | None = None
        self._frame_timer = FrameTimer()
        self._initial_focus_control = None
        self._pending_initial_focus = False
        self.task_panel = None
        self.showcase_return_button = None

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
            max(1, self.rect.width - self.CONTENT_PADDING_X * 2),
            max(1, self.rect.height - self.CONTENT_PADDING_Y * 2),
        )

        # Category tab strip
        tab_strip_h = self.CATEGORY_TAB_STRIP_HEIGHT
        tab_strip_gap = self.CATEGORY_TAB_STRIP_GAP
        category_tabs = create_tab_control_from_specs(
            "control_showcase_category_tabs",
            Rect(root_content_rect.left, root_content_rect.top, root_content_rect.width, tab_strip_h),
            build_tab_builder_specs(self.SHOWCASE_CATEGORY_TABS, builder_prefix="", builder_suffix=""),
            selected_key=self._active_category_key,
            on_change=lambda key: self._set_active_category(host, key),
        )
        category_tabs.set_accessibility(role="tablist", label="Showcase categories")
        self._registry.add_control(category_tabs)
        self._category_tabs = category_tabs

        # Content area below the tab strip.
        # All categories occupy this same rect; only the active one is visible.
        content_rect = Rect(
            root_content_rect.left,
            root_content_rect.top + tab_strip_h + tab_strip_gap,
            root_content_rect.width,
            max(1, root_content_rect.height - tab_strip_h - tab_strip_gap),
        )

        slot_h = make_labeled_slot_height_fn(self.LABEL_HEIGHT, self.LABEL_GAP)
        row_gap = self.ROW_GAP

        # Pre-compute column widths per category so control factories get correct dimensions
        data_col_w = self._col_width(content_rect, self.DATA_COLUMNS)
        advanced_col_w = self._col_width(content_rect, self.ADVANCED_COLUMNS)
        extended_col_w = self._col_width(content_rect, self.EXTENDED_COLUMNS)

        self._showcase_notification_center = build_notification_center(
            (
                NotificationSpec("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS),
                NotificationSpec("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING),
            ),
            max_records=6,
        )

        basics_specs = self._build_basics_specs(content_rect)
        self._registry.register(basics_specs)

        for defs, num_cols in (
            (self._data_defs(data_col_w), self.DATA_COLUMNS),
            (self._advanced_defs(advanced_col_w, host), self.ADVANCED_COLUMNS),
            (self._extended_defs(extended_col_w, host), self.EXTENDED_COLUMNS),
        ):
            specs, _ = build_multi_column_grid_specs(
                defs,
                bounds=content_rect,
                num_cols=num_cols,
                content_bottom=content_rect.bottom,
                row_gap=row_gap,
                slot_height_for=slot_h,
            )
            self._registry.register(specs)

        self._build_scene_task_panel(host)
        self._apply_category_visibility(host)
        self._initial_focus_control = host.control_showcase_menu_bar
        self._pending_initial_focus = True

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(self, host, _CONTROLS_RUNTIME_SPEC)
        app_actions = getattr(host.app, "actions", None)
        bind_global_key = getattr(app_actions, "bind_global_key", None)
        if callable(bind_global_key):
            bind_global_key(pygame.K_ESCAPE, "exit", scene="control_showcase")

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

    def prewarm(self, host, surface, theme) -> None:
        menu_strip = getattr(host, "control_showcase_menu_bar", None)
        reg = self._registry
        tracked = [*reg.control_labels, *reg.controls] if reg is not None else []
        draw_controls_prewarm(surface, theme, [menu_strip, *tracked, self.task_panel, self.showcase_return_button])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _col_width(self, bounds: Rect, num_cols: int) -> int:
        cols = CellCaretLayout.split_columns(bounds, count=num_cols, gap=self.ROW_GAP, min_width=100)
        return cols[0].width if cols else bounds.width

    def _default_rect(self, host) -> Rect:
        screen_rect = getattr(host, "screen_rect", None)
        if screen_rect is None:
            screen = getattr(host, "screen", None)
            if screen is not None:
                screen_rect = screen.get_rect()
        if screen_rect is None:
            return Rect(0, 0, 1, 1)
        return Rect(
            int(self.ROOT_MARGIN_X),
            int(self.ROOT_MARGIN_TOP),
            max(1, int(screen_rect.width - self.ROOT_MARGIN_X * 2)),
            max(1, int(screen_rect.height - self.ROOT_MARGIN_TOP - self.ROOT_MARGIN_BOTTOM)),
        )

    def _set_active_category(self, host, key: str) -> None:
        valid_keys = {k for k, _ in self.SHOWCASE_CATEGORY_TABS}
        if key not in valid_keys or key == self._active_category_key:
            return
        self._active_category_key = key
        self._apply_category_visibility(host)

    def _apply_category_visibility(self, host) -> None:
        reg = self._registry
        apply_category_visibility(
            active_key=self._active_category_key,
            placed_controls=reg.placed_controls if reg is not None else [],
            control_labels=reg.control_labels if reg is not None else [],
            category_fn=category_for_row,
        )
        focused = getattr(host.app.focus, "focused", None)
        if focused is not None and not getattr(focused, "visible", True):
            if self._category_tabs is not None and self._category_tabs.visible and self._category_tabs.enabled:
                host.app.focus.set_focus(self._category_tabs)

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
        task_panel_layout = create_task_panel_linear_layout(
            self.task_panel,
            TaskPanelLinearLayoutSpec(
                left=self.TASK_PANEL_BUTTON_LEFT,
                top_offset=self.TASK_PANEL_BUTTON_TOP_OFFSET,
                item_width=self.TASK_PANEL_BUTTON_WIDTH,
                item_height=self.TASK_PANEL_BUTTON_HEIGHT,
                spacing=self.TASK_PANEL_SLOT_SPACING,
                horizontal=True,
            ),
        )
        task_panel_items = add_scene_task_panel_items(
            host,
            self.task_panel,
            task_panel_layout,
            scene_nav_button_specs=(
                TaskPanelSceneNavButtonSpec(
                    control_id="showcase_return",
                    slot_index=0,
                    label="Return",
                    target_scene="main",
                    go_to_attr="go_to_main",
                    style="angle",
                    accessibility_role="button",
                    accessibility_label="Return to main",
                    tab_index=-1,
                ),
            ),
            window_toggle_group_spec=None,
            window_presentation=getattr(host, "window_presentation", None),
            window_toggle_attr_owner=self,
            tab_sequence_start=None,
        )
        self.showcase_return_button = (
            task_panel_items.scene_nav_buttons[0] if task_panel_items.scene_nav_buttons else None
        )

    # ------------------------------------------------------------------
    # Control definition builders (one method per category)
    # ------------------------------------------------------------------

    def _build_basics_specs(self, bounds: Rect) -> tuple[ControlPlacementSpec, ...]:
        image_path = str(Path(__file__).parent.parent / self.IMAGE_PATH)
        nc = self._showcase_notification_center
        label_h = int(self.LABEL_HEIGHT)
        label_gap = int(self.LABEL_GAP)
        row_gap = int(self.ROW_GAP)
        inner_gap = int(self.BASICS_INNER_GAP)

        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=bounds,
            content_bottom=bounds.bottom,
            preferred_width=bounds.width,
            item_gap_y=row_gap,
        )

        # --- Local composite-panel factories ---

        def make_arrow_boxes(w: int, h: int):
            panel = PanelControl("control_arrow_boxes_cell", Rect(0, 0, w, h), draw_background=False)
            area_w, area_h = min(60, w), min(60, h)
            area = Rect((w - area_w) // 2, (h - area_h) // 2, area_w, area_h)
            cols = CellCaretLayout.split_columns(area, count=2, gap=inner_gap, min_width=10)
            box_h = max(10, (area_h - inner_gap) // 2)
            left_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=cols[0], content_bottom=cols[0].bottom,
                preferred_width=cols[0].width, item_gap_y=inner_gap,
            )
            up_r = Rect(left_st.add_slot_or_overflow(box_h, overflow_gap=0))
            left_r = Rect(left_st.add_slot_or_overflow(box_h, overflow_gap=0))
            right_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=cols[1], content_bottom=cols[1].bottom,
                preferred_width=cols[1].width, item_gap_y=inner_gap,
            )
            down_r = Rect(right_st.add_slot_or_overflow(box_h, overflow_gap=0))
            right_r = Rect(right_st.add_slot_or_overflow(box_h, overflow_gap=0))
            panel.add_at(ArrowBoxControl("control_arrow_up", Rect(0, 0, up_r.width, up_r.height), 90), up_r.left, up_r.top)
            panel.add_at(ArrowBoxControl("control_arrow_down", Rect(0, 0, down_r.width, down_r.height), 270), down_r.left, down_r.top)
            panel.add_at(ArrowBoxControl("control_arrow_left", Rect(0, 0, left_r.width, left_r.height), 180), left_r.left, left_r.top)
            panel.add_at(ArrowBoxControl("control_arrow_right", Rect(0, 0, right_r.width, right_r.height), 0), right_r.left, right_r.top)
            return panel

        def make_vertical_buttons(w: int, h: int):
            panel = PanelControl("control_button_cell", Rect(0, 0, w, h), draw_background=False)
            btn_w = min(100, w)
            col_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=Rect(0, 0, btn_w, h), content_bottom=h,
                preferred_width=btn_w, item_gap_y=inner_gap,
            )
            btn_h = max(20, (h - inner_gap * 2) // 3)
            for ctrl_id, label in [
                ("control_button", "Button A"),
                ("control_button_2", "Button B"),
                ("control_button_3", "Button C"),
            ]:
                slot = Rect(col_st.add_slot_or_overflow(btn_h, overflow_gap=0))
                panel.add_at(ButtonControl(ctrl_id, Rect(0, 0, slot.width, slot.height), label), slot.left, slot.top)
            return panel

        def make_button_group(group_id: str, group_name: str, items: list):
            def _factory(w: int, h: int) -> PanelControl:
                panel = PanelControl(group_id, Rect(0, 0, w, h), draw_background=False)
                btn_w = min(100, w)
                col_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                    anchor=Rect(0, 0, btn_w, h), content_bottom=h,
                    preferred_width=btn_w, item_gap_y=inner_gap,
                )
                btn_h = max(20, (h - inner_gap * 2) // 3)
                for ctrl_id, label in items:
                    slot = Rect(col_st.add_slot_or_overflow(btn_h, overflow_gap=0))
                    panel.add_at(
                        ButtonGroupControl(ctrl_id, Rect(0, 0, slot.width, slot.height),
                                           f"controls_showcase_{group_name}", label, selected=False),
                        slot.left, slot.top,
                    )
                return panel
            return _factory

        def make_toggle_group(group_id: str, items: list[tuple[str, str]]):
            def _factory(w: int, h: int) -> PanelControl:
                panel = PanelControl(group_id, Rect(0, 0, w, h), draw_background=False)
                btn_w = min(100, w)
                col_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                    anchor=Rect(0, 0, btn_w, h), content_bottom=h,
                    preferred_width=btn_w, item_gap_y=inner_gap,
                )
                btn_h = max(20, (h - inner_gap * 2) // 3)
                for ctrl_id, suffix in items:
                    slot = Rect(col_st.add_slot_or_overflow(btn_h, overflow_gap=0))
                    panel.add_at(
                        ToggleControl(
                            ctrl_id,
                            Rect(0, 0, slot.width, slot.height),
                            text_on=f"Pressed {suffix}",
                            text_off=f"Raised {suffix}",
                            pushed=False,
                        ),
                        slot.left,
                        slot.top,
                    )
                return panel

            return _factory

        def make_horiz_pair(w: int, h: int):
            panel = PanelControl("control_horizontal_pair_cell", Rect(0, 0, w, h), draw_background=False)
            col_st, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=Rect(0, 0, w, h), content_bottom=h, preferred_width=w, item_gap_y=row_gap,
            )
            sb_r = Rect(col_st.add_slot_or_overflow(24, overflow_gap=0))
            sl_r = Rect(col_st.add_slot_or_overflow(24, overflow_gap=0))
            panel.add_at(
                ScrollbarControl("control_horizontal_scrollbar", Rect(0, 0, sb_r.width, sb_r.height),
                    LayoutAxis.HORIZONTAL, self.SCROLLBAR_CONTENT_SIZE, self.SCROLLBAR_VIEWPORT_SIZE,
                    offset=self.SCROLLBAR_DEFAULT_OFFSET, step=self.SCROLLBAR_STEP),
                sb_r.left, sb_r.top,
            )
            panel.add_at(
                SliderControl("control_horizontal_slider", Rect(0, 0, sl_r.width, sl_r.height),
                    LayoutAxis.HORIZONTAL, self.SLIDER_MINIMUM, self.SLIDER_MAXIMUM, self.SLIDER_DEFAULT_VALUE),
                sl_r.left, sl_r.top,
            )
            return panel

        def make_vert_pair(w: int, h: int):
            panel = PanelControl("control_vertical_pair_cell", Rect(0, 0, w, h), draw_background=False)
            track_w, gap_x = 24, 12
            track_h = max(80, h)
            y = max(0, (h - track_h) // 2)
            panel.add_at(
                ScrollbarControl("control_vertical_scrollbar", Rect(0, 0, track_w, track_h),
                    LayoutAxis.VERTICAL, self.SCROLLBAR_CONTENT_SIZE, self.SCROLLBAR_VIEWPORT_SIZE,
                    offset=self.SCROLLBAR_DEFAULT_OFFSET, step=self.SCROLLBAR_STEP),
                0, y,
            )
            panel.add_at(
                SliderControl("control_vertical_slider", Rect(0, 0, track_w, track_h),
                    LayoutAxis.VERTICAL, self.SLIDER_MINIMUM, self.SLIDER_MAXIMUM, self.SLIDER_DEFAULT_VALUE),
                track_w + gap_x, y,
            )
            return panel

        def make_text_area_with_input(w: int, h: int):
            panel = PanelControl("control_text_area_cell", Rect(0, 0, w, h), draw_background=False)
            ta_h, ti_h, gap = 96, 32, 8
            panel.add_at(TextAreaControl("control_text_area", Rect(0, 0, w, ta_h),
                value="Release Notes\nWrap keeps spaces with the text they separate.\nEdit this sample to check caret placement."), 0, 0)
            panel.add_at(LabelControl("label_control_text_input_inline", Rect(0, 0, w, label_h),
                "Text Input", align="left"), 0, ta_h + gap)
            panel.add_at(TextInputControl("control_text_input", Rect(0, 0, w, ti_h),
                placeholder="Type here"), 0, ta_h + gap + label_h + label_gap)
            return panel

        def make_tab_control(w: int, h: int):
            panel = PanelControl("control_tab_cell", Rect(0, 0, w, h), draw_background=False)
            tab = TabControl("control_tab", Rect(0, 0, w, h),
                items=[
                    TabItem("one", "One", LabelControl("ctrl_tab_lbl_one", Rect(0, 0, 1, 30), "One", align="left")),
                    TabItem("two", "Two", LabelControl("ctrl_tab_lbl_two", Rect(0, 0, 1, 30), "Two", align="left")),
                    TabItem("three", "Three", LabelControl("ctrl_tab_lbl_three", Rect(0, 0, 1, 30), "Three", align="left")),
                ],
                selected_key="one",
            )
            panel.add_at(tab, 0, 0)
            return panel

        def make_data_grid(w: int, h: int):
            panel = PanelControl("control_data_grid_cell", Rect(0, 0, w, h), draw_background=False)
            dg = DataGridControl("control_data_grid", Rect(0, 0, w, h),
                [GridColumn(key="name", title="Name", width=90), GridColumn(key="value", title="Value", width=70)],
                [
                    GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                    GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                    GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                    GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
                ],
                row_height=24,
            )
            panel.add_at(dg, 0, 0)
            return panel

        kw = dict(stack=stack, label_height=label_h, label_gap=label_gap, overflow_gap=row_gap)

        row1 = build_horizontal_row_specs([
            RowCellSpec("arrow_boxes", "Arrow Boxes", 80, 0, make_arrow_boxes, natural_width=110),
            RowCellSpec("buttons_cell", "Buttons", 80, 1, make_vertical_buttons, natural_width=100),
            RowCellSpec("button_group_a_cell", "Group A", 80, 2,
                make_button_group("control_button_group_a_cell", "a", [
                    ("control_button_group_a1", "A1"), ("control_button_group_a2", "A2"), ("control_button_group_a3", "A3"),
                ]), natural_width=100),
            RowCellSpec("button_group_b_cell", "Group B", 80, 3,
                make_button_group("control_button_group_b_cell", "b", [
                    ("control_button_group_b1", "B1"), ("control_button_group_b2", "B2"), ("control_button_group_b3", "B3"),
                ]), natural_width=100),
            RowCellSpec("button_group_c_cell", "Group C", 80, 4,
                make_button_group("control_button_group_c_cell", "c", [
                    ("control_button_group_c1", "C1"), ("control_button_group_c2", "C2"), ("control_button_group_c3", "C3"),
                ]), natural_width=100),
            RowCellSpec("toggle_group", "Toggles", 80, 12,
                make_toggle_group("control_toggle_group_cell", [
                    ("control_toggle_a", "A"), ("control_toggle_b", "B"), ("control_toggle_c", "C"),
                ]),
                natural_width=100,
                accessibility_role="group",
                accessibility_label="Toggle group"),
        ], col_gap=6, **kw)

        row2 = build_horizontal_row_specs([
            RowCellSpec("text_area", "Text Area", 160, 5, make_text_area_with_input,
                accessibility_role="textbox", accessibility_label="Text area"),
            RowCellSpec("tab", "Tab", 160, 6, make_tab_control,
                accessibility_role="tablist", accessibility_label="Tab control"),
            RowCellSpec("data_grid", "Data Grid", 120, 7, make_data_grid,
                accessibility_role="table", accessibility_label="Data grid"),
        ], col_gap=self.BASICS_COL_GAP, **kw)

        row3 = build_horizontal_row_specs([
            RowCellSpec("horizontal_pair", "Horizontal Scrollbar and Slider", 56, 8, make_horiz_pair),
            RowCellSpec("vertical_pair", "Vertical Scrollbar and Slider", 140, 9, make_vert_pair),
        ], col_gap=16, **kw)

        row4 = build_horizontal_row_specs([
            RowCellSpec("notification_panel", "Notification Panel", 160, 10,
                lambda w, h: NotificationPanelControl("control_notification_panel", Rect(0, 0, w, h), nc)),
            RowCellSpec("image", "Image", 160, 11,
                lambda w, h: ImageControl("control_image", Rect(0, 0, h, h), image_path, scale=True),
                target_width=160, target_align="left"),
        ], col_gap=6, **kw)

        return row1 + row2 + row3 + row4


    def _data_defs(self, col_w: int) -> list[ControlDefinition]:
        scroll_items = [
            "Alpha", "Bravo", "Charlie", "Delta", "Echo",
            "Foxtrot", "Golf", "Hotel", "India", "Juliet",
        ]

        def _make_scroll_view():
            content_w = col_w - 20
            content_h = 24 * len(scroll_items)
            sv = ScrollViewControl("control_scroll_view", Rect(0, 0, col_w, 140),
                content_width=content_w, content_height=content_h, scroll_y=True)
            inner = ListViewControl("sv_select_list", Rect(0, 0, content_w, content_h),
                [ListItem(label=item, value=item) for item in scroll_items],
                row_height=24, show_scrollbar=False)
            inner.set_tab_index(-1)
            inner.set_accessibility(role="listbox", label="Scroll view list")
            sv.add(inner, content_x=4, content_y=0)
            sv.set_content_size(content_w, content_h)
            return sv

        return [
            ControlDefinition("list_view", "List View", 140, 60,
                lambda: ListViewControl("control_list_view", Rect(0, 0, col_w, 140),
                    [ListItem(label=f"Item {i + 1}", value=i) for i in range(10)],
                    row_height=24, selected_index=0),
                accessibility_role="listbox", accessibility_label="List view"),
            ControlDefinition("scroll_view", "Scroll View", 140, 61,
                _make_scroll_view,
                accessibility_role="group", accessibility_label="Scroll view"),
            ControlDefinition("tree", "Tree", 150, 62,
                lambda: TreeControl("control_tree", Rect(0, 0, col_w, 150),
                    [TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                     TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")])]),
                accessibility_role="tree", accessibility_label="Tree control"),
            ControlDefinition("dropdown", "Dropdown", 32, 63,
                lambda: DropdownControl("control_dropdown", Rect(0, 0, col_w, 32),
                    [DropdownOption(label=f"Option {i + 1}", value=i) for i in range(4)],
                    placeholder="Choose"),
                accessibility_role="combobox", accessibility_label="Dropdown"),
            ControlDefinition("splitter", "Splitter", 60, 64,
                lambda: SplitterControl("control_splitter", Rect(0, 0, col_w, 60),
                    axis=LayoutAxis.HORIZONTAL, ratio=0.5, min_pane_size=16),
                accessibility_role="separator", accessibility_label="Splitter"),
            ControlDefinition("menu_bar", "Menu Bar", 28, 65,
                lambda: MenuBarControl("control_menu_bar", Rect(0, 0, col_w, 28),
                    [MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Save")]),
                     MenuEntry("Tools", [ContextMenuItem("Run"), ContextMenuItem("Reset")])]),
                accessibility_role="menubar", accessibility_label="Menu bar"),
            ControlDefinition("canvas", "Canvas", 100, 67,
                lambda: CanvasControl("control_canvas", Rect(0, 0, col_w, 100), max_events=64),
                ),
            ControlDefinition("frame", "Frame", 60, 68,
                lambda: FrameControl("control_frame", Rect(0, 0, col_w, 60), border_width=2),
                ),
            ControlDefinition("panel", "Panel", 60, 69,
                lambda: PanelControl("control_panel", Rect(0, 0, col_w, 60), draw_background=True),
                ),
            ControlDefinition("rich_label", "Rich Label", 80, 66,
                lambda: RichLabelControl("control_rich_label", Rect(0, 0, col_w, 80),
                    text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, "
                         "run `deploy --env staging`, and **_ship_** after QA."),
                ),
        ]

    def _advanced_defs(self, col_w: int, host) -> list[ControlDefinition]:
        import pygame as _pygame

        label_h = int(self.LABEL_HEIGHT)
        label_gap = int(self.LABEL_GAP)
        row_gap = int(self.ROW_GAP)

        # Build animated controls eagerly so on_update can reference them.
        indeterminate_bar = ProgressBarControl(
            "control_progress_bar_indeterminate", Rect(0, 0, col_w, 20), indeterminate=True
        )
        self._indeterminate_bar = indeterminate_bar

        frame_w, frame_h = 32, 32
        atlas = _pygame.Surface((frame_w * 4, frame_h), flags=_pygame.SRCALPHA)
        for fi, color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
            atlas.fill(color, Rect(fi * frame_w, 0, frame_w, frame_h))
        sheet = SpriteSheet(atlas, frame_w=frame_w, frame_h=frame_h)
        animation = FrameAnimation(sheet, frames=list(range(4)), fps=1, loop=True)
        anim_ctrl = AnimatedImageControl(
            "control_animated_image", Rect(0, 0, col_w, 48), animation=animation, scale=True
        )
        self._showcase_anim_ctrl = anim_ctrl

        def _add_labeled(panel: PanelControl, y: int, *, key: str, label: str, control, control_h: int) -> int:
            panel.add_at(
                LabelControl(f"label_{key}_inline", Rect(0, 0, col_w, label_h), label, align="left"),
                0,
                y,
            )
            y += label_h + label_gap
            panel.add_at(control, 0, y)
            return y + int(control_h) + row_gap

        def _make_overlay_panel() -> OverlayPanelControl:
            op = OverlayPanelControl("control_overlay_panel", Rect(0, 0, col_w, 90), draw_background=True)
            for i, txt in enumerate(("Overlay Item A", "Overlay Item B", "Overlay Item C")):
                op.add_at(
                    LabelControl(f"overlay_child_{i}", Rect(0, 0, col_w - 16, 22), txt, align="left"),
                    rel_x=8,
                    rel_y=6 + i * 26,
                )
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
            _add_labeled(panel, y, key="fixed_pattern_fmt_input", label="Fixed Pattern Format", control=fixed_pattern, control_h=30)
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

    def _extended_defs(self, col_w: int, host) -> list[ControlDefinition]:
        # col_w is the full content width (EXTENDED_COLUMNS=1).
        # Each row is a PanelControl spanning the full width with 3 internal sub-columns,
        # ensuring all three controls in a row share the same top alignment.
        app = host.app
        label_h = int(self.LABEL_HEIGHT)
        label_gap = int(self.LABEL_GAP)
        row_gap = int(self.ROW_GAP)

        # Compute sub-column rects (relative to 0,0 of the panel)
        sub_cols = CellCaretLayout.split_columns(
            Rect(0, 0, col_w, 100), count=3, gap=row_gap, min_width=80
        )
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
            panel.add_at(
                LabelControl(f"label_{key}_ext", Rect(0, 0, w, label_h), label, align="left"),
                x, 0,
            )
            panel.add_at(control, x, label_h + label_gap)

        # Row 1: Toolbar | Split Button | Breadcrumb  (tallest = Toolbar 36px)
        row1_h = label_h + label_gap + 36

        def _make_row1_panel() -> PanelControl:
            panel = PanelControl("control_ext_row1", Rect(0, 0, col_w, row1_h), draw_background=False)
            toolbar = ToolbarControl("control_toolbar", Rect(0, 0, sc0_w, 36),
                items=[ToolbarItem(label="Cut", action_id="cut"),
                       ToolbarItem(label="Copy", action_id="copy"),
                       ToolbarItem(separator=True),
                       ToolbarItem(label="Paste", action_id="paste")])
            _add_cell(panel, "toolbar", sc0_x, sc0_w, "Toolbar", toolbar)
            split_btn = SplitButtonControl("control_split_button", Rect(0, 0, sc1_w, 32),
                label="Save",
                options=[SplitButtonOption(label="Save As...", on_click=lambda: None),
                         SplitButtonOption(label="Save All", on_click=lambda: None)])
            _add_cell(panel, "split_button", sc1_x, sc1_w, "Split Button", split_btn)
            breadcrumb = BreadcrumbControl("control_breadcrumb", Rect(0, 0, sc2_w, 28),
                items=[BreadcrumbItem(label="Home", value="home"),
                       BreadcrumbItem(label="Files", value="files"),
                       BreadcrumbItem(label="Documents", value="documents")])
            _add_cell(panel, "breadcrumb", sc2_x, sc2_w, "Breadcrumb", breadcrumb)
            return panel

        # Row 2: Chip Input | Status Bar | Expander  (tallest = Expander 80px)
        row2_h = label_h + label_gap + 80

        def _make_row2_panel() -> PanelControl:
            panel = PanelControl("control_ext_row2", Rect(0, 0, col_w, row2_h), draw_background=False)
            chip = ChipInputControl("control_chip_input", Rect(0, 0, sc0_w, 36),
                placeholder="Add tag...", values=["Python", "GUI"])
            _add_cell(panel, "chip_input", sc0_x, sc0_w, "Chip Input", chip)
            status_bar = StatusBarControl("control_status_bar", Rect(0, 0, sc1_w, 24),
                slots=[StatusSlot("status", "Ready", width=80),
                       StatusSlot("line", "Ln 1", width=50, separator_after=True),
                       StatusSlot("col", "Col 1", width=50)])
            _add_cell(panel, "status_bar", sc1_x, sc1_w, "Status Bar", status_bar)
            expander = ExpanderControl("control_expander", Rect(0, 0, sc2_w, 80),
                title="Details", body_height=50)
            _add_cell(panel, "expander", sc2_x, sc2_w, "Expander", expander)
            return panel

        # Row 3: Scene Menu Strip | Date Picker | Time Picker  (tallest = Date/Time Picker 32px)
        row3_h = label_h + label_gap + 32

        def _make_row3_panel() -> PanelControl:
            panel = PanelControl("control_ext_row3", Rect(0, 0, col_w, row3_h), draw_background=False)
            scene_menu = SceneMenuStripControl("control_scene_menu_strip",
                Rect(0, 0, sc0_w, 30), app,
                scenes_shown=False, windows_shown=False,
                extra_entries_provider=lambda: [
                    MenuEntry("Demo", [
                        ContextMenuItem("Inspect", action=lambda: None),
                        ContextMenuItem("Refresh", action=lambda: None),
                    ]),
                ])
            _add_cell(panel, "scene_menu_strip", sc0_x, sc0_w, "Scene Menu Strip", scene_menu)
            date_picker = DatePickerControl("control_date_picker", Rect(0, 0, sc1_w, 32))
            _add_cell(panel, "date_picker", sc1_x, sc1_w, "Date Picker", date_picker)
            time_picker = TimePickerControl("control_time_picker", Rect(0, 0, sc2_w, 32),
                hour=9, minute=30)
            _add_cell(panel, "time_picker", sc2_x, sc2_w, "Time Picker", time_picker)
            return panel

        # Row 4: Color Picker  (tallest = Color Picker 160px)
        row4_h = label_h + label_gap + 160

        def _make_row4_panel() -> PanelControl:
            panel = PanelControl("control_ext_row4", Rect(0, 0, col_w, row4_h), draw_background=False)
            color_picker = ColorPickerControl("control_color_picker", Rect(0, 0, sc0_w, 160))
            _add_cell(panel, "color_picker", sc0_x, sc0_w, "Color Picker", color_picker)
            return panel

        return [
            ControlDefinition("ext_row1", "", row1_h, 140, _make_row1_panel, labeled=False),
            ControlDefinition("ext_row2", "", row2_h, 141, _make_row2_panel, labeled=False),
            ControlDefinition("ext_row3", "", row3_h, 142, _make_row3_panel, labeled=False),
            ControlDefinition("ext_row4", "", row4_h, 143, _make_row4_panel, labeled=False),
        ]
