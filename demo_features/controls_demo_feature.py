"""Controls showcase feature with grouped, varied-span layout."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from pygame import Rect

from gui_do import (
    AnimatedImageControl,
    ButtonControl,
    CellCaretLayout,
    ControlRegistry,
    Feature,
    FrameTimer,
    LabelControl,
    LayoutManager,
    NotificationCenter,
    NotificationSpec,
    ProgressBarControl,
    TabControl,
    ToastSeverity,
    build_notification_center,
    make_labeled_slot_height_fn,
    ui_property,
)
from gui_do.features.data_driven_runtime import (
    add_standard_scene_menu_strip,
    bind_task_panel_focus_toggle,
    build_tab_builder_specs,
    create_tab_control_from_specs,
)
from gui_do.layout.control_gallery_layout_manager import ControlGalleryLayoutManager
from demo_features.control_showcase_category_visibility import (
    BASICS_SUPPRESSED_LABEL_NAMES,
    apply_category_visibility,
    ensure_basics_aux_label,
)
from demo_features.control_showcase_runtime import promote_open_popup_controls
from demo_features.control_showcase_spec_factories import (
    build_col6_section_specs,
    build_core_showcase_specs,
    build_dock_inspector_column_specs,
    build_data_tab_specs_bundle,
    build_formatted_input_section_specs,
    build_intro_specs,
    build_new_controls_section_specs,
    build_overlay_panel_spec,
    build_progress_column_specs,
)


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

    @label.setter
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

        self._registry = ControlRegistry(host.control_showcase_root)

        content_rect = Rect(
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
            Rect(content_rect.left, content_rect.top, content_rect.width, tab_strip_h),
            category_tab_specs,
            selected_key=self._active_category_key,
            on_change=lambda key: self._set_active_category(host, key),
        )
        category_tabs.set_accessibility(role="tablist", label="Showcase categories")
        self._registry.add_control(category_tabs)
        self._category_tabs = category_tabs

        content_rect = Rect(
            content_rect.left,
            content_rect.top + tab_strip_h + tab_strip_gap,
            content_rect.width,
            max(1, content_rect.height - tab_strip_h - tab_strip_gap),
        )

        slot_h = make_labeled_slot_height_fn(self.LABEL_HEIGHT, self.LABEL_GAP)

        column_width = 320
        row_gap = 8
        col_gap = 4
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
            inspectable=_ShowcaseInspectable(),
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
        )
        self._registry.register(nc_place_specs)

        self._build_scene_task_panel(host)

        # Apply initial tab category visibility after all placements are registered.
        self._apply_category_visibility(host)

        self._initial_focus_control = self._category_tabs
        self._pending_initial_focus = True

    def bind_runtime(self, host) -> None:
        """Bind scene-owned shortcuts for control showcase runtime behavior."""
        bind_task_panel_focus_toggle(
            host.app.actions,
            host.app,
            action_name="toggle_task_panel_focus_control_showcase",
            scene_name="control_showcase",
            key=__import__("pygame").K_F1,
        )

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
        for control in [menu_strip, *tracked, self.task_panel, self.showcase_return_button]:
            if control is None:
                continue
            control.draw(surface, theme)


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
