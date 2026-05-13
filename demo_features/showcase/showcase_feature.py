"""Controls showcase feature — tabbed gallery of all gui_do controls."""
from __future__ import annotations

import pygame
from gui_do import *
from pygame import Rect
from gui_do.features.data_driven_runtime import (
    SceneMenuStripSpec,
    TaskPanelSlotLayoutSpec,
    add_scene_menu_strip_from_spec,
    build_tab_builder_specs,
    create_task_panel_slot_layout,
    create_tab_control_from_specs,
    shutdown_routed_runtime,
    setup_routed_runtime,
)
from gui_do.features.control_spec import ControlDefinition
from gui_do.features.feature_lifecycle import ControlPlacementSpec
from .showcase_advanced_helpers import advanced_defs as advanced_defs_helper
from .showcase_basics_helpers import build_basics_specs as build_basics_specs_helper
from .showcase_data_helpers import data_defs as data_defs_helper
from .showcase_extended_helpers import extended_defs as extended_defs_helper
from .showcase_runtime_helpers import (
    apply_active_category_visibility as apply_active_category_visibility_helper,
    build_scene_task_panel as build_scene_task_panel_helper,
    col_width as col_width_helper,
    default_rect as default_rect_helper,
    on_update as on_update_helper,
    prewarm as prewarm_helper,
    set_active_category as set_active_category_helper,
)
from .showcase_specs import (
    _CONTROLS_RUNTIME_SPEC,
    SHOWCASE_ADVANCED_COLUMNS,
    SHOWCASE_BASICS_COL_GAP,
    SHOWCASE_BASICS_COLUMNS,
    SHOWCASE_BASICS_INNER_GAP,
    SHOWCASE_CATEGORY_TAB_STRIP_GAP,
    SHOWCASE_CATEGORY_TAB_STRIP_HEIGHT,
    SHOWCASE_CATEGORY_TABS as SHOWCASE_CATEGORY_TABS_SPEC,
    SHOWCASE_CONTENT_PADDING_X,
    SHOWCASE_CONTENT_PADDING_Y,
    SHOWCASE_DATA_COLUMNS,
    SHOWCASE_EXTENDED_COLUMNS,
    SHOWCASE_IMAGE_PATH,
    SHOWCASE_LABEL_GAP,
    SHOWCASE_LABEL_HEIGHT,
    SHOWCASE_MENU_BAR_HEIGHT,
    SHOWCASE_MENU_TOOLS_EXCLUDE_LABELS,
    SHOWCASE_ROOT_MARGIN_BOTTOM,
    SHOWCASE_ROOT_MARGIN_TOP,
    SHOWCASE_ROOT_MARGIN_X,
    SHOWCASE_ROW_GAP,
    SHOWCASE_SCROLLBAR_CONTENT_SIZE,
    SHOWCASE_SCROLLBAR_DEFAULT_OFFSET,
    SHOWCASE_SCROLLBAR_STEP,
    SHOWCASE_SCROLLBAR_VIEWPORT_SIZE,
    SHOWCASE_SLIDER_DEFAULT_VALUE,
    SHOWCASE_SLIDER_MAXIMUM,
    SHOWCASE_SLIDER_MINIMUM,
    SHOWCASE_TASK_PANEL_ANIMATION_STEP_PX,
    SHOWCASE_TASK_PANEL_BUTTON_HEIGHT,
    SHOWCASE_TASK_PANEL_BUTTON_LEFT,
    SHOWCASE_TASK_PANEL_BUTTON_TOP_OFFSET,
    SHOWCASE_TASK_PANEL_BUTTON_WIDTH,
    SHOWCASE_TASK_PANEL_HEIGHT,
    SHOWCASE_TASK_PANEL_HIDDEN_PEEK_PIXELS,
    SHOWCASE_TASK_PANEL_SLOT_SPACING,
)


# ---------------------------------------------------------------------------
# ShowcaseFeature
# ---------------------------------------------------------------------------

class ShowcaseFeature(Feature):
    """Tabbed control gallery showcasing standalone gui_do controls.

    Window/task-panel chrome is intentionally demonstrated in the main scene,
    where host-managed window presentation and scene task panel behavior are
    exercised with realistic toggle workflows.
    """

    HOST_REQUIREMENTS = {
        "build": ("app", "scene_presentation", "control_showcase_root"),
        "bind_runtime": ("app",),
        "on_update": ("app",),
        "prewarm": ("app",),
    }

    # Layout
    ROOT_MARGIN_X = SHOWCASE_ROOT_MARGIN_X
    ROOT_MARGIN_TOP = SHOWCASE_ROOT_MARGIN_TOP
    ROOT_MARGIN_BOTTOM = SHOWCASE_ROOT_MARGIN_BOTTOM
    CONTENT_PADDING_X = SHOWCASE_CONTENT_PADDING_X
    CONTENT_PADDING_Y = SHOWCASE_CONTENT_PADDING_Y
    LABEL_HEIGHT = SHOWCASE_LABEL_HEIGHT
    LABEL_GAP = SHOWCASE_LABEL_GAP
    CATEGORY_TAB_STRIP_HEIGHT = SHOWCASE_CATEGORY_TAB_STRIP_HEIGHT
    CATEGORY_TAB_STRIP_GAP = SHOWCASE_CATEGORY_TAB_STRIP_GAP
    ROW_GAP = SHOWCASE_ROW_GAP
    BASICS_COL_GAP = SHOWCASE_BASICS_COL_GAP
    BASICS_INNER_GAP = SHOWCASE_BASICS_INNER_GAP

    # Control values
    SLIDER_MINIMUM = SHOWCASE_SLIDER_MINIMUM
    SLIDER_MAXIMUM = SHOWCASE_SLIDER_MAXIMUM
    SLIDER_DEFAULT_VALUE = SHOWCASE_SLIDER_DEFAULT_VALUE
    SCROLLBAR_CONTENT_SIZE = SHOWCASE_SCROLLBAR_CONTENT_SIZE
    SCROLLBAR_VIEWPORT_SIZE = SHOWCASE_SCROLLBAR_VIEWPORT_SIZE
    SCROLLBAR_DEFAULT_OFFSET = SHOWCASE_SCROLLBAR_DEFAULT_OFFSET
    SCROLLBAR_STEP = SHOWCASE_SCROLLBAR_STEP

    IMAGE_PATH = SHOWCASE_IMAGE_PATH

    # Task panel
    TASK_PANEL_HEIGHT = SHOWCASE_TASK_PANEL_HEIGHT
    TASK_PANEL_HIDDEN_PEEK_PIXELS = SHOWCASE_TASK_PANEL_HIDDEN_PEEK_PIXELS
    TASK_PANEL_ANIMATION_STEP_PX = SHOWCASE_TASK_PANEL_ANIMATION_STEP_PX
    TASK_PANEL_BUTTON_WIDTH = SHOWCASE_TASK_PANEL_BUTTON_WIDTH
    TASK_PANEL_BUTTON_HEIGHT = SHOWCASE_TASK_PANEL_BUTTON_HEIGHT
    TASK_PANEL_BUTTON_LEFT = SHOWCASE_TASK_PANEL_BUTTON_LEFT
    TASK_PANEL_BUTTON_TOP_OFFSET = SHOWCASE_TASK_PANEL_BUTTON_TOP_OFFSET
    TASK_PANEL_SLOT_SPACING = SHOWCASE_TASK_PANEL_SLOT_SPACING

    # Category tab definitions: (key, label)
    SHOWCASE_CATEGORY_TABS = SHOWCASE_CATEGORY_TABS_SPEC

    # Column counts per category (controls laid out left-to-right across columns)
    BASICS_COLUMNS = SHOWCASE_BASICS_COLUMNS
    DATA_COLUMNS = SHOWCASE_DATA_COLUMNS
    ADVANCED_COLUMNS = SHOWCASE_ADVANCED_COLUMNS
    EXTENDED_COLUMNS = SHOWCASE_EXTENDED_COLUMNS

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
                rect=Rect(0, 0, host.control_showcase_root.rect.width, SHOWCASE_MENU_BAR_HEIGHT),
                scene_name="control_showcase",
                scenes_shown=True,
                windows_shown=True,
                tools_exclude_labels=SHOWCASE_MENU_TOOLS_EXCLUDE_LABELS,
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

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_runtime(self, host, _CONTROLS_RUNTIME_SPEC)
        app_actions = getattr(host.app, "actions", None)
        unbind_global_key = getattr(app_actions, "unbind_global_key", None)
        if callable(unbind_global_key):
            unbind_global_key(pygame.K_ESCAPE, "exit", scene="control_showcase")

    def on_update(self, host) -> None:
        dt = self._frame_timer.tick()
        on_update_helper(self, host, dt)

    def prewarm(self, host, surface, theme) -> None:
        prewarm_helper(self, host, surface, theme)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _col_width(self, bounds: Rect, num_cols: int) -> int:
        return col_width_helper(self, bounds, num_cols)

    def _default_rect(self, host) -> Rect:
        return default_rect_helper(self, host)

    def _set_active_category(self, host, key: str) -> None:
        set_active_category_helper(self, host, key)

    def _apply_category_visibility(self, host) -> None:
        apply_active_category_visibility_helper(self, host)

    def _build_scene_task_panel(self, host) -> None:
        build_scene_task_panel_helper(self, host)

    # ------------------------------------------------------------------
    # Control definition builders (one method per category)
    # ------------------------------------------------------------------

    def _build_basics_specs(self, bounds: Rect) -> tuple[ControlPlacementSpec, ...]:
        return build_basics_specs_helper(self, bounds)


    def _data_defs(self, col_w: int) -> list[ControlDefinition]:
        return data_defs_helper(self, col_w)

    def _advanced_defs(self, col_w: int, host) -> list[ControlDefinition]:
        return advanced_defs_helper(self, col_w, host)

    def _extended_defs(self, col_w: int, host) -> list[ControlDefinition]:
        return extended_defs_helper(self, col_w, host)
