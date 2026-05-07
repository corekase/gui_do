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
    build_notification_center,
    build_specs_from_column_section,
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
# Category routing
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
# Popup-promotion helpers
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
        c for c in controls
        if c in children and c.visible and c.enabled and control_has_open_popup(c)
    ]
    if not open_controls:
        return False
    changed = False
    for c in open_controls:
        idx = children.index(c)
        if idx != len(children) - 1:
            children.append(children.pop(idx))
            changed = True
    if changed:
        root.invalidate()
    return changed


# ---------------------------------------------------------------------------
# Category visibility
# ---------------------------------------------------------------------------

def apply_category_visibility(
    *,
    active_key: str,
    placed_controls: list,
    control_labels: list,
) -> None:
    """Show controls belonging to *active_key* and hide all others."""
    active_label_set: set = set()
    for placed in placed_controls:
        show = category_for_row(int(placed.row_index)) == active_key
        placed.control.visible = show
        placed.control.enabled = show
        if placed.label is not None:
            placed.label.visible = show
            placed.label.enabled = show
            if show:
                active_label_set.add(placed.label)
    for label in control_labels:
        if label not in active_label_set:
            label.visible = False
            label.enabled = False


# ---------------------------------------------------------------------------
# Grid placement helper
# ---------------------------------------------------------------------------

def _build_grid_specs(
    definitions: list[ControlDefinition],
    *,
    bounds: Rect,
    num_cols: int,
    content_bottom: int,
    row_gap: int,
    slot_height_for,
) -> tuple[tuple, int]:
    """Place *definitions* in reading order (left-to-right, top-to-bottom) across *num_cols* columns.

    Uses CellCaretLayout and build_specs_from_column_section from the framework.
    Returns (specs_tuple, max_bottom_y).
    """
    if not definitions or num_cols < 1:
        return (), int(bounds.top)

    col_rects = CellCaretLayout.split_columns(bounds, count=num_cols, gap=row_gap, min_width=100)
    n = min(num_cols, len(col_rects))

    # Assign definitions round-robin to columns (preserves reading order within each column)
    col_defs: list[list[ControlDefinition]] = [[] for _ in range(n)]
    for i, defn in enumerate(definitions):
        col_defs[i % n].append(defn)

    # Build specs per column using the standard framework helper
    col_specs: list[tuple] = []
    max_bottom = int(bounds.top)
    for idx, col_rect in enumerate(col_rects[:n]):
        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=col_rect,
            content_bottom=content_bottom,
            preferred_width=col_rect.width,
            item_gap_y=row_gap,
        )
        specs, bottom = build_specs_from_column_section(
            col_defs[idx],
            stack=stack,
            slot_height_for=slot_height_for,
            overflow_gap=row_gap,
        )
        col_specs.append(specs)
        max_bottom = max(max_bottom, bottom)

    # Interleave specs in reading order (row-major) so focus traversal goes left-to-right
    all_specs: list = []
    max_len = max((len(s) for s in col_specs), default=0)
    for row_i in range(max_len):
        for col_i in range(n):
            if row_i < len(col_specs[col_i]):
                all_specs.append(col_specs[col_i][row_i])

    return tuple(all_specs), max_bottom


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
    ADVANCED_COLUMNS = 3
    EXTENDED_COLUMNS = 3

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
        other_col_w = self._col_width(content_rect, self.DATA_COLUMNS)

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
            (self._data_defs(other_col_w), self.DATA_COLUMNS),
            (self._advanced_defs(other_col_w, host), self.ADVANCED_COLUMNS),
            (self._extended_defs(other_col_w, host), self.EXTENDED_COLUMNS),
        ):
            specs, _ = _build_grid_specs(
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
        )
        focused = getattr(host.app.focus, "focused", None)
        if focused is not None and not getattr(focused, "visible", True):
            if self._category_tabs is not None and self._category_tabs.visible and self._category_tabs.enabled:
                host.app.focus.set_focus(self._category_tabs)

    def _promote_open_popup_controls(self, host) -> None:
        root = getattr(host, "control_showcase_root", None)
        reg = self._registry
        promote_open_popup_controls(root, reg.controls if reg is not None else [])

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
        next_row_index = 0
        specs: list[ControlPlacementSpec] = []

        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=bounds,
            content_bottom=bounds.bottom,
            preferred_width=bounds.width,
            item_gap_y=row_gap,
        )

        def slot_h(control_h: int) -> int:
            return CellCaretLayout.labeled_slot_height(
                max(1, int(control_h)),
                label_height=label_h,
                label_gap=label_gap,
            )

        def add_row(cells: list[dict], cols: int) -> None:
            nonlocal next_row_index
            row_control_h = max(int(c["control_h"]) for c in cells)
            row_slot_rect = Rect(stack.add_slot_or_overflow(slot_h(row_control_h), overflow_gap=row_gap))
            col_gap = int(cells[0].get("col_gap", self.BASICS_COL_GAP)) if cells else self.BASICS_COL_GAP
            natural_widths = [c.get("natural_width") for c in cells]
            if all(w is not None for w in natural_widths):
                x = row_slot_rect.left
                col_rects = []
                for w in natural_widths:
                    col_rects.append(Rect(x, row_slot_rect.top, int(w), row_slot_rect.height))
                    x += int(w) + col_gap
            else:
                col_rects = CellCaretLayout.split_columns(row_slot_rect, count=cols, gap=col_gap, min_width=60)
            for col_i, cell in enumerate(cells):
                col_rect = Rect(col_rects[col_i])
                desired_slot_h = slot_h(int(cell["control_h"]))
                slot_rect = Rect(col_rect.left, col_rect.top, col_rect.width, min(col_rect.height, desired_slot_h))

                target_w = cell.get("target_width")
                if isinstance(target_w, int) and 1 <= target_w < slot_rect.width:
                    target_align = str(cell.get("target_align", "center")).lower()
                    if target_align == "right":
                        slot_rect.left += slot_rect.width - target_w
                    elif target_align != "left":
                        slot_rect.left += (slot_rect.width - target_w) // 2
                    slot_rect.width = target_w

                control_h = max(1, slot_rect.height - label_h - label_gap)
                control = cell["factory"](slot_rect.width, control_h)
                specs.append(
                    ControlPlacementSpec(
                        name=str(cell["name"]),
                        control=control,
                        control_rect=slot_rect,
                        focusable=bool(cell.get("focusable", False)),
                        labeled=True,
                        label_text=str(cell["label"]),
                        accessibility_role=cell.get("accessibility_role"),
                        accessibility_label=cell.get("accessibility_label"),
                        column_index=col_i,
                        row_index=next_row_index,
                    )
                )
                next_row_index += 1

        def make_arrow_boxes_cell(control_w: int, control_h: int):
            panel = PanelControl("control_arrow_boxes_cell", Rect(0, 0, control_w, control_h), draw_background=False)
            area_w = min(60, control_w)
            area_h = min(60, control_h)
            area = Rect((control_w - area_w) // 2, (control_h - area_h) // 2, area_w, area_h)
            inner_gap = int(self.BASICS_INNER_GAP)
            col_rects = CellCaretLayout.split_columns(area, count=2, gap=inner_gap, min_width=10)
            box_h = max(10, (area_h - inner_gap) // 2)

            left_stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=col_rects[0],
                content_bottom=col_rects[0].bottom,
                preferred_width=col_rects[0].width,
                item_gap_y=inner_gap,
            )
            up_rect = Rect(left_stack.add_slot_or_overflow(box_h, overflow_gap=0))
            left_rect = Rect(left_stack.add_slot_or_overflow(box_h, overflow_gap=0))

            right_stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=col_rects[1],
                content_bottom=col_rects[1].bottom,
                preferred_width=col_rects[1].width,
                item_gap_y=inner_gap,
            )
            down_rect = Rect(right_stack.add_slot_or_overflow(box_h, overflow_gap=0))
            right_rect = Rect(right_stack.add_slot_or_overflow(box_h, overflow_gap=0))

            panel.add_at(ArrowBoxControl("control_arrow_up", Rect(0, 0, up_rect.width, up_rect.height), 90), up_rect.left, up_rect.top)
            panel.add_at(ArrowBoxControl("control_arrow_down", Rect(0, 0, down_rect.width, down_rect.height), 270), down_rect.left, down_rect.top)
            panel.add_at(ArrowBoxControl("control_arrow_left", Rect(0, 0, left_rect.width, left_rect.height), 180), left_rect.left, left_rect.top)
            panel.add_at(ArrowBoxControl("control_arrow_right", Rect(0, 0, right_rect.width, right_rect.height), 0), right_rect.left, right_rect.top)
            return panel

        def make_vertical_button_cell(cell_id: str, control_ids: tuple[str, str, str], labels: tuple[str, str, str], control_w: int, control_h: int):
            panel = PanelControl(cell_id, Rect(0, 0, control_w, control_h), draw_background=False)
            btn_w = min(100, control_w)
            col_anchor = Rect(0, 0, btn_w, control_h)
            stack_inner, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=col_anchor,
                content_bottom=col_anchor.bottom,
                preferred_width=col_anchor.width,
                item_gap_y=int(self.BASICS_INNER_GAP),
            )
            gap_y = int(self.BASICS_INNER_GAP)
            btn_h = max(20, (control_h - (gap_y * 2)) // 3)
            for idx, text in enumerate(labels):
                slot = Rect(stack_inner.add_slot_or_overflow(btn_h, overflow_gap=0))
                panel.add_at(
                    ButtonControl(control_ids[idx], Rect(0, 0, slot.width, slot.height), text),
                    slot.left,
                    slot.top,
                )
            return panel

        def make_vertical_group_cell(control_id: str, group_name: str, control_ids: tuple[str, str, str], labels: tuple[str, str, str], control_w: int, control_h: int):
            panel = PanelControl(control_id, Rect(0, 0, control_w, control_h), draw_background=False)
            btn_w = min(100, control_w)
            col_anchor = Rect(0, 0, btn_w, control_h)
            stack_inner, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=col_anchor,
                content_bottom=col_anchor.bottom,
                preferred_width=col_anchor.width,
                item_gap_y=int(self.BASICS_INNER_GAP),
            )
            gap_y = int(self.BASICS_INNER_GAP)
            btn_h = max(20, (control_h - (gap_y * 2)) // 3)
            for idx, text in enumerate(labels):
                slot = Rect(stack_inner.add_slot_or_overflow(btn_h, overflow_gap=0))
                panel.add_at(
                    ButtonGroupControl(
                        control_ids[idx],
                        Rect(0, 0, slot.width, slot.height),
                        f"controls_showcase_{group_name}",
                        text,
                        selected=False,
                    ),
                    slot.left,
                    slot.top,
                )
            return panel

        def make_horiz_pair_cell(control_w: int, control_h: int):
            panel = PanelControl("control_horizontal_pair_cell", Rect(0, 0, control_w, control_h), draw_background=False)
            stack_inner, _, _, _ = CellCaretLayout.column_stack_from_anchor(
                anchor=Rect(0, 0, control_w, control_h),
                content_bottom=control_h,
                preferred_width=control_w,
                item_gap_y=row_gap,
            )
            sb_rect = Rect(stack_inner.add_slot_or_overflow(24, overflow_gap=0))
            sl_rect = Rect(stack_inner.add_slot_or_overflow(24, overflow_gap=0))
            panel.add_at(
                ScrollbarControl(
                    "control_horizontal_scrollbar",
                    Rect(0, 0, sb_rect.width, sb_rect.height),
                    LayoutAxis.HORIZONTAL,
                    self.SCROLLBAR_CONTENT_SIZE,
                    self.SCROLLBAR_VIEWPORT_SIZE,
                    offset=self.SCROLLBAR_DEFAULT_OFFSET,
                    step=self.SCROLLBAR_STEP,
                ),
                sb_rect.left,
                sb_rect.top,
            )
            panel.add_at(
                SliderControl(
                    "control_horizontal_slider",
                    Rect(0, 0, sl_rect.width, sl_rect.height),
                    LayoutAxis.HORIZONTAL,
                    self.SLIDER_MINIMUM,
                    self.SLIDER_MAXIMUM,
                    self.SLIDER_DEFAULT_VALUE,
                ),
                sl_rect.left,
                sl_rect.top,
            )
            return panel

        def make_vert_pair_cell(control_w: int, control_h: int):
            panel = PanelControl("control_vertical_pair_cell", Rect(0, 0, control_w, control_h), draw_background=False)
            track_w = 24
            gap_x = 12
            pair_w = (track_w * 2) + gap_x
            start_x = 0
            track_h = max(80, control_h)
            y = max(0, (control_h - track_h) // 2)
            panel.add_at(
                ScrollbarControl(
                    "control_vertical_scrollbar",
                    Rect(0, 0, track_w, track_h),
                    LayoutAxis.VERTICAL,
                    self.SCROLLBAR_CONTENT_SIZE,
                    self.SCROLLBAR_VIEWPORT_SIZE,
                    offset=self.SCROLLBAR_DEFAULT_OFFSET,
                    step=self.SCROLLBAR_STEP,
                ),
                start_x,
                y,
            )
            panel.add_at(
                SliderControl(
                    "control_vertical_slider",
                    Rect(0, 0, track_w, track_h),
                    LayoutAxis.VERTICAL,
                    self.SLIDER_MINIMUM,
                    self.SLIDER_MAXIMUM,
                    self.SLIDER_DEFAULT_VALUE,
                ),
                start_x + track_w + gap_x,
                y,
            )
            return panel

        def make_single_control_cell(
            cell_id: str,
            *,
            child_id: str,
            control_w: int,
            control_h: int,
            build_child,
        ):
            panel = PanelControl(cell_id, Rect(0, 0, control_w, control_h), draw_background=False)
            child = build_child(Rect(0, 0, control_w, control_h))
            if getattr(child, "control_id", None) != child_id and hasattr(child, "control_id"):
                child.control_id = child_id
            panel.add_at(child, 0, 0)
            return panel

        # Row 1: Arrow boxes + buttons + group columns A/B/C
        add_row(
            [
                {
                    "name": "arrow_boxes",
                    "label": "Arrow Boxes",
                    "control_h": 80,
                    "factory": make_arrow_boxes_cell,
                    "focusable": False,
                    "natural_width": 110,
                    "col_gap": 6,
                },
                {
                    "name": "buttons_cell",
                    "label": "Buttons",
                    "control_h": 80,
                    "factory": lambda w, h: make_vertical_button_cell(
                        "control_button_cell",
                        ("control_button", "control_button_2", "control_button_3"),
                        ("Button A", "Button B", "Button C"),
                        w,
                        h,
                    ),
                    "focusable": False,
                    "natural_width": 100,
                    "col_gap": 6,
                },
                {
                    "name": "button_group_a_cell",
                    "label": "Group A",
                    "control_h": 80,
                    "factory": lambda w, h: make_vertical_group_cell(
                        "control_button_group_a_cell",
                        "a",
                        ("control_button_group_a1", "control_button_group_a2", "control_button_group_a3"),
                        ("A1", "A2", "A3"),
                        w,
                        h,
                    ),
                    "focusable": False,
                    "natural_width": 100,
                    "col_gap": 6,
                },
                {
                    "name": "button_group_b_cell",
                    "label": "Group B",
                    "control_h": 80,
                    "factory": lambda w, h: make_vertical_group_cell(
                        "control_button_group_b_cell",
                        "b",
                        ("control_button_group_b1", "control_button_group_b2", "control_button_group_b3"),
                        ("B1", "B2", "B3"),
                        w,
                        h,
                    ),
                    "focusable": False,
                    "natural_width": 100,
                    "col_gap": 6,
                },
                {
                    "name": "button_group_c_cell",
                    "label": "Group C",
                    "control_h": 80,
                    "factory": lambda w, h: make_vertical_group_cell(
                        "control_button_group_c_cell",
                        "c",
                        ("control_button_group_c1", "control_button_group_c2", "control_button_group_c3"),
                        ("C1", "C2", "C3"),
                        w,
                        h,
                    ),
                    "focusable": False,
                    "natural_width": 100,
                    "col_gap": 6,
                },
            ],
            cols=5,
        )

        # Row 2: text area + input stacked, tab, data grid
        def make_text_area_with_input_cell(control_w: int, control_h: int):
            panel = PanelControl("control_text_area_cell", Rect(0, 0, control_w, control_h), draw_background=False)
            ta_h = 96
            ti_h = 32
            inner_gap = 8
            input_label_y = ta_h + inner_gap
            input_y = input_label_y + label_h + label_gap
            panel.add_at(
                TextAreaControl(
                    "control_text_area",
                    Rect(0, 0, control_w, ta_h),
                    value="Heading: Notes\n- First line\n- Second line",
                ),
                0, 0,
            )
            panel.add_at(
                LabelControl(
                    "label_control_text_input_inline",
                    Rect(0, 0, control_w, label_h),
                    "Text Input",
                    align="left",
                ),
                0,
                input_label_y,
            )
            panel.add_at(
                TextInputControl(
                    "control_text_input",
                    Rect(0, 0, control_w, ti_h),
                    placeholder="Type here",
                ),
                0,
                input_y,
            )
            return panel

        add_row(
            [
                {
                    "name": "text_area",
                    "label": "Text Area",
                    "control_h": 160,
                    "factory": make_text_area_with_input_cell,
                    "focusable": False,
                    "accessibility_role": "textbox",
                    "accessibility_label": "Text area",
                    "col_gap": self.BASICS_COL_GAP,
                },
                {
                    "name": "tab",
                    "label": "Tab",
                    "control_h": 160,
                    "factory": lambda w, h: make_single_control_cell(
                        "control_tab_cell",
                        child_id="control_tab",
                        control_w=w,
                        control_h=h,
                        build_child=lambda r: TabControl(
                            "control_tab",
                            r,
                            items=[
                                TabItem("one", "One", LabelControl("ctrl_tab_lbl_one", Rect(0, 0, 1, 30), "One", align="left")),
                                TabItem("two", "Two", LabelControl("ctrl_tab_lbl_two", Rect(0, 0, 1, 30), "Two", align="left")),
                                TabItem("three", "Three", LabelControl("ctrl_tab_lbl_three", Rect(0, 0, 1, 30), "Three", align="left")),
                            ],
                            selected_key="one",
                        ),
                    ),
                    "focusable": False,
                    "accessibility_role": "tablist",
                    "accessibility_label": "Tab control",
                    "col_gap": self.BASICS_COL_GAP,
                },
                {
                    "name": "data_grid",
                    "label": "Data Grid",
                    "control_h": 120,
                    "factory": lambda w, h: make_single_control_cell(
                        "control_data_grid_cell",
                        child_id="control_data_grid",
                        control_w=w,
                        control_h=h,
                        build_child=lambda r: DataGridControl(
                            "control_data_grid",
                            r,
                            [GridColumn(key="name", title="Name", width=90), GridColumn(key="value", title="Value", width=70)],
                            [
                                GridRow(data={"name": "Alpha", "value": 10}, row_id="a"),
                                GridRow(data={"name": "Beta", "value": 20}, row_id="b"),
                                GridRow(data={"name": "Gamma", "value": 30}, row_id="c"),
                                GridRow(data={"name": "Delta", "value": 40}, row_id="d"),
                            ],
                            row_height=24,
                        ),
                    ),
                    "focusable": False,
                    "accessibility_role": "table",
                    "accessibility_label": "Data grid",
                    "col_gap": self.BASICS_COL_GAP,
                },
            ],
            cols=3,
        )

        # Row 3: horizontal pair, vertical pair
        add_row(
            [
                {
                    "name": "horizontal_pair",
                    "label": "Horizontal Scrollbar and Slider",
                    "control_h": 56,
                    "factory": make_horiz_pair_cell,
                    "focusable": False,
                    "col_gap": 16,
                },
                {
                    "name": "vertical_pair",
                    "label": "Vertical Scrollbar and Slider",
                    "control_h": 140,
                    "factory": make_vert_pair_cell,
                    "focusable": False,
                    "col_gap": 16,
                },
            ],
            cols=2,
        )

        # Row 4: notification panel then square image
        add_row(
            [
                {
                    "name": "notification_panel",
                    "label": "Notification Panel",
                    "control_h": 160,
                    "factory": lambda w, h: NotificationPanelControl(
                        "control_notification_panel",
                        Rect(0, 0, w, h),
                        nc,
                    ),
                    "focusable": False,
                    "col_gap": 6,
                },
                {
                    "name": "image",
                    "label": "Image",
                    "control_h": 160,
                    "target_width": 160,
                    "target_align": "left",
                    "factory": lambda w, h: ImageControl(
                        "control_image",
                        Rect(0, 0, h, h),
                        image_path,
                        scale=True,
                    ),
                    "focusable": False,
                    "col_gap": 6,
                },
            ],
            cols=2,
        )

        return tuple(specs)

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
                focusable=True, accessibility_role="listbox", accessibility_label="List view"),
            ControlDefinition("scroll_view", "Scroll View", 140, 61,
                _make_scroll_view,
                focusable=True, accessibility_role="group", accessibility_label="Scroll view"),
            ControlDefinition("tree", "Tree", 150, 62,
                lambda: TreeControl("control_tree", Rect(0, 0, col_w, 150),
                    [TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                     TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")])]),
                focusable=True, accessibility_role="tree", accessibility_label="Tree control"),
            ControlDefinition("dropdown", "Dropdown", 32, 63,
                lambda: DropdownControl("control_dropdown", Rect(0, 0, col_w, 32),
                    [DropdownOption(label=f"Option {i + 1}", value=i) for i in range(4)],
                    placeholder="Choose"),
                focusable=True, accessibility_role="combobox", accessibility_label="Dropdown"),
            ControlDefinition("splitter", "Splitter", 60, 64,
                lambda: SplitterControl("control_splitter", Rect(0, 0, col_w, 60),
                    axis=LayoutAxis.HORIZONTAL, ratio=0.5, min_pane_size=16),
                focusable=True, accessibility_role="separator", accessibility_label="Splitter"),
            ControlDefinition("menu_bar", "Menu Bar", 28, 65,
                lambda: MenuBarControl("control_menu_bar", Rect(0, 0, col_w, 28),
                    [MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Save")]),
                     MenuEntry("Tools", [ContextMenuItem("Run"), ContextMenuItem("Reset")])]),
                focusable=False, accessibility_role="menubar", accessibility_label="Menu bar"),
            ControlDefinition("canvas", "Canvas", 100, 67,
                lambda: CanvasControl("control_canvas", Rect(0, 0, col_w, 100), max_events=64),
                focusable=False),
            ControlDefinition("frame", "Frame", 60, 68,
                lambda: FrameControl("control_frame", Rect(0, 0, col_w, 60), border_width=2),
                focusable=False),
            ControlDefinition("panel", "Panel", 60, 69,
                lambda: PanelControl("control_panel", Rect(0, 0, col_w, 60), draw_background=True),
                focusable=False),
            ControlDefinition("rich_label", "Rich Label", 80, 66,
                lambda: RichLabelControl("control_rich_label", Rect(0, 0, col_w, 80),
                    text="Sprint Notes\n**Ready** for review, _scheduled_ for Wednesday, "
                         "run `deploy --env staging`, and **_ship_** after QA."),
                focusable=False),
        ]

    def _advanced_defs(self, col_w: int, host) -> list[ControlDefinition]:
        import pygame as _pygame

        # Build animated controls eagerly so on_update can reference them
        indeterminate_bar = ProgressBarControl(
            "control_progress_bar_indeterminate", Rect(0, 0, col_w, 20), indeterminate=True)
        self._indeterminate_bar = indeterminate_bar

        frame_w, frame_h = 32, 32
        atlas = _pygame.Surface((frame_w * 4, frame_h), flags=_pygame.SRCALPHA)
        for fi, color in enumerate([(220, 60, 60), (60, 220, 60), (60, 60, 220), (220, 220, 60)]):
            atlas.fill(color, Rect(fi * frame_w, 0, frame_w, frame_h))
        sheet = SpriteSheet(atlas, frame_w=frame_w, frame_h=frame_h)
        animation = FrameAnimation(sheet, frames=list(range(4)), fps=1, loop=True)
        anim_ctrl = AnimatedImageControl(
            "control_animated_image", Rect(0, 0, col_w, 48), animation=animation, scale=True)
        self._showcase_anim_ctrl = anim_ctrl

        def _make_overlay_panel():
            op = OverlayPanelControl("control_overlay_panel", Rect(0, 0, col_w, 90), draw_background=True)
            for i, txt in enumerate(("Overlay Item A", "Overlay Item B", "Overlay Item C")):
                op.add_at(
                    LabelControl(f"overlay_child_{i}", Rect(0, 0, col_w - 16, 22), txt, align="left"),
                    rel_x=8, rel_y=6 + i * 26)
            return op

        def _make_dock():
            ws = DockWorkspace(DockTabs("sc_dock_tabs", panes=[
                DockPane("editor", "Editor"),
                DockPane("preview", "Preview"),
                DockPane("console", "Console"),
            ]))
            return DockWorkspacePanel("control_dock_workspace_panel", Rect(0, 0, col_w, 40), ws)

        return [
            ControlDefinition("spinner", "Spinner", 30, 100,
                lambda: SpinnerControl("control_spinner", Rect(0, 0, col_w, 30),
                    value=25, min_value=0, max_value=100, step=1, decimals=0,
                    on_change=lambda v, _r: None),
                focusable=True, accessibility_role="spinbutton", accessibility_label="Spinner"),
            ControlDefinition("range_slider", "Range Slider", 24, 101,
                lambda: RangeSliderControl("control_range_slider", Rect(0, 0, col_w, 24),
                    min_value=0, max_value=100, low_value=20, high_value=80,
                    on_change=lambda lo, hi, _r: None),
                focusable=True, accessibility_role="slider", accessibility_label="Range slider"),
            ControlDefinition("color_picker", "Color Picker", 180, 102,
                lambda: ColorPickerControl("control_color_picker", Rect(0, 0, col_w, 180),
                    color=(64, 128, 255), on_change=lambda c: None),
                focusable=True, accessibility_role="group", accessibility_label="Color picker"),
            ControlDefinition("numeric_fmt_input", "Numeric Format", 30, 103,
                lambda: NumericFormatter(decimals=2, thousands_sep=",").create_text_input(
                    "control_numeric_fmt_input", Rect(0, 0, col_w, 30),
                    raw_value="12500", placeholder="0.00"),
                focusable=True, accessibility_role="textbox",
                accessibility_label="Numeric formatted text input"),
            ControlDefinition("pattern_fmt_input", "Pattern Format", 30, 104,
                lambda: PatternFormatter("###-###-####").create_text_input(
                    "control_pattern_fmt_input", Rect(0, 0, col_w, 30),
                    raw_value="5551234567", placeholder="###-###-####"),
                focusable=True, accessibility_role="textbox",
                accessibility_label="Pattern formatted text input"),
            ControlDefinition("fixed_pattern_fmt_input", "Fixed Pattern Format", 30, 105,
                lambda: FixedPatternFormatter("#####-####").create_text_input(
                    "control_fixed_pattern_fmt_input", Rect(0, 0, col_w, 30),
                    raw_value="941010001", placeholder="#####-####"),
                focusable=True, accessibility_role="textbox",
                accessibility_label="Fixed pattern formatted text input"),
            ControlDefinition("overlay_panel", "Overlay Panel", 90, 106,
                _make_overlay_panel, focusable=False),
            ControlDefinition("dock_workspace_panel", "Dock Workspace", 40, 107,
                _make_dock,
                focusable=True, accessibility_role="tablist",
                accessibility_label="Dock workspace panel"),
            ControlDefinition("property_inspector", "Property Inspector", 160, 108,
                lambda: PropertyInspectorPanel("control_property_inspector",
                    Rect(0, 0, col_w, 160), PropertyInspectorModel(ShowcaseInspectable())),
                focusable=False),
            ControlDefinition("progress_bar", "Progress Bar", 20, 109,
                lambda: ProgressBarControl("control_progress_bar", Rect(0, 0, col_w, 20), value=0.65),
                focusable=False),
            ControlDefinition("progress_bar_indeterminate", "Progress (Marquee)", 20, 110,
                lambda: indeterminate_bar, focusable=False),
            ControlDefinition("animated_image", "Animated Image", 48, 111,
                lambda: anim_ctrl, focusable=False),
        ]

    def _extended_defs(self, col_w: int, host) -> list[ControlDefinition]:
        app = host.app
        return [
            ControlDefinition("toolbar", "Toolbar", 36, 140,
                lambda: ToolbarControl("control_toolbar", Rect(0, 0, col_w, 36),
                    items=[ToolbarItem(label="Cut", action_id="cut"),
                           ToolbarItem(label="Copy", action_id="copy"),
                           ToolbarItem(separator=True),
                           ToolbarItem(label="Paste", action_id="paste")]),
                focusable=True, accessibility_role="toolbar", accessibility_label="Toolbar"),
            ControlDefinition("status_bar", "Status Bar", 24, 141,
                lambda: StatusBarControl("control_status_bar", Rect(0, 0, col_w, 24),
                    slots=[StatusSlot("status", "Ready", width=80),
                           StatusSlot("line", "Ln 1", width=50, separator_after=True),
                           StatusSlot("col", "Col 1", width=50)]),
                focusable=False, accessibility_role="status", accessibility_label="Status bar"),
            ControlDefinition("expander", "Expander", 80, 142,
                lambda: ExpanderControl("control_expander", Rect(0, 0, col_w, 80),
                    title="Details", body_height=50),
                focusable=True, accessibility_role="group", accessibility_label="Expander"),
            ControlDefinition("breadcrumb", "Breadcrumb", 28, 143,
                lambda: BreadcrumbControl("control_breadcrumb", Rect(0, 0, col_w, 28),
                    items=[BreadcrumbItem(label="Home", value="home"),
                           BreadcrumbItem(label="Files", value="files"),
                           BreadcrumbItem(label="Documents", value="documents")]),
                focusable=True, accessibility_role="navigation",
                accessibility_label="Breadcrumb navigation"),
            ControlDefinition("split_button", "Split Button", 32, 144,
                lambda: SplitButtonControl("control_split_button", Rect(0, 0, col_w, 32),
                    label="Save",
                    options=[SplitButtonOption(label="Save As...", on_click=lambda: None),
                             SplitButtonOption(label="Save All", on_click=lambda: None)]),
                focusable=True, accessibility_role="button", accessibility_label="Split button"),
            ControlDefinition("chip_input", "Chip Input", 36, 145,
                lambda: ChipInputControl("control_chip_input", Rect(0, 0, col_w, 36),
                    placeholder="Add tag...", values=["Python", "GUI"]),
                focusable=True, accessibility_role="textbox", accessibility_label="Chip input"),
            ControlDefinition("time_picker", "Time Picker", 32, 146,
                lambda: TimePickerControl("control_time_picker", Rect(0, 0, col_w, 32),
                    hour=9, minute=30),
                focusable=True, accessibility_role="textbox", accessibility_label="Time picker"),
            ControlDefinition("date_picker", "Date Picker", 32, 147,
                lambda: DatePickerControl("control_date_picker", Rect(0, 0, col_w, 32)),
                focusable=True, accessibility_role="textbox", accessibility_label="Date picker"),
            ControlDefinition("scene_menu_strip", "Scene Menu Strip", 30, 148,
                lambda: SceneMenuStripControl("control_scene_menu_strip",
                    Rect(0, 0, col_w, 30), app,
                    scenes_shown=False, windows_shown=False,
                    extra_entries_provider=lambda: [
                        MenuEntry("Demo", [
                            ContextMenuItem("Inspect", action=lambda: None),
                            ContextMenuItem("Refresh", action=lambda: None),
                        ]),
                    ]),
                focusable=False, accessibility_role="menubar",
                accessibility_label="Scene menu strip"),
        ]
