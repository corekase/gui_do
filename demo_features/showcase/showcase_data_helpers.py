"""Data-category builders for the controls showcase feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    CanvasControl,
    CanvasViewport,
    DropdownControl,
    DropdownOption,
    FrameControl,
    GridLayout,
    GridPlacement,
    LabelControl,
    LayoutAxis,
    ListItem,
    ListViewControl,
    PanelControl,
    ScrollViewControl,
    SplitterControl,
    TreeControl,
    TreeNode,
)
from gui_do.features.control_spec import ControlDefinition

if TYPE_CHECKING:
    from .showcase_feature import ShowcaseFeature


def data_defs(feature: ShowcaseFeature, col_w: int) -> list[ControlDefinition]:
    scroll_items = [
        "Alpha",
        "Bravo",
        "Charlie",
        "Delta",
        "Echo",
        "Foxtrot",
        "Golf",
        "Hotel",
        "India",
        "Juliet",
    ]

    def _make_scroll_view():
        content_w = col_w - 20
        content_h = 24 * len(scroll_items)
        sv = ScrollViewControl(
            "control_scroll_view",
            Rect(0, 0, col_w, 140),
            content_width=content_w,
            content_height=content_h,
            scroll_y=True,
        )
        inner = ListViewControl(
            "sv_select_list",
            Rect(0, 0, content_w, content_h),
            [ListItem(label=item, value=item) for item in scroll_items],
            row_height=24,
            show_scrollbar=False,
        )
        inner.set_tab_index(-1)
        inner.set_accessibility(role="listbox", label="Scroll view list")
        sv.add(inner, content_x=4, content_y=0)
        sv.set_content_size(content_w, content_h)
        return sv

    def _make_canvas_viewport_panel():
        panel = PanelControl("control_canvas_viewport_cell", Rect(0, 0, col_w, 112), draw_background=False)
        viewport = CanvasViewport(
            content_size=(2048, 1024),
            initial_offset=(192.0, 128.0),
            initial_scale=1.25,
            min_scale=0.5,
            max_scale=4.0,
        )
        canvas = CanvasControl("control_canvas_viewport_canvas", Rect(0, 0, col_w, 72), max_events=64)
        world_sample = viewport.to_canvas((96, 32))
        screen_sample = viewport.to_screen((320, 240))
        offset_x, offset_y = viewport.offset
        info = LabelControl(
            "control_canvas_viewport_info",
            Rect(0, 0, col_w, 34),
            (
                f"CanvasViewport offset ({int(offset_x)}, {int(offset_y)}) "
                f"scale {viewport.scale:.2f} | screen(96,32)->world({int(world_sample[0])},{int(world_sample[1])}) "
                f"| world(320,240)->screen({int(screen_sample[0])},{int(screen_sample[1])})"
            ),
            align="left",
        )
        layout = GridLayout(
            row_tracks=[72, 6, 34],
            col_tracks=["1fr"],
            gap=0,
            padding=0,
        )
        layout.place(canvas, GridPlacement(row=0, col=0))
        layout.place(info, GridPlacement(row=2, col=0))
        layout.apply(Rect(0, 0, max(1, col_w), 112))
        panel.add_at(canvas, canvas.rect.left, canvas.rect.top)
        panel.add_at(info, info.rect.left, info.rect.top)
        return panel

    return [
        ControlDefinition(
            "list_view",
            "List View",
            140,
            60,
            lambda: ListViewControl(
                "control_list_view",
                Rect(0, 0, col_w, 140),
                [ListItem(label=f"Item {i + 1}", value=i) for i in range(10)],
                row_height=24,
                selected_index=0,
            ),
            accessibility_role="listbox",
            accessibility_label="List view",
        ),
        ControlDefinition(
            "scroll_view",
            "Scroll View",
            140,
            61,
            _make_scroll_view,
            accessibility_role="group",
            accessibility_label="Scroll view",
        ),
        ControlDefinition(
            "tree",
            "Tree",
            150,
            62,
            lambda: TreeControl(
                "control_tree",
                Rect(0, 0, col_w, 150),
                [
                    TreeNode("Desktop", expanded=True, children=[TreeNode("Window A"), TreeNode("Window B")]),
                    TreeNode("Scenes", expanded=True, children=[TreeNode("Main"), TreeNode("Control Showcase")]),
                ],
            ),
            accessibility_role="tree",
            accessibility_label="Tree control",
        ),
        ControlDefinition(
            "dropdown",
            "Dropdown",
            32,
            63,
            lambda: DropdownControl(
                "control_dropdown",
                Rect(0, 0, col_w, 32),
                [DropdownOption(label=f"Option {i + 1}", value=i) for i in range(4)],
                placeholder="Choose",
            ),
            accessibility_role="combobox",
            accessibility_label="Dropdown",
        ),
        ControlDefinition(
            "splitter",
            "Splitter",
            60,
            64,
            lambda: SplitterControl(
                "control_splitter",
                Rect(0, 0, col_w, 60),
                axis=LayoutAxis.HORIZONTAL,
                ratio=0.5,
                min_pane_size=16,
            ),
            accessibility_role="separator",
            accessibility_label="Splitter",
        ),
        ControlDefinition(
            "canvas",
            "Canvas",
            100,
            67,
            lambda: CanvasControl("control_canvas", Rect(0, 0, col_w, 100), max_events=64),
        ),
        ControlDefinition(
            "frame",
            "Frame",
            60,
            68,
            lambda: FrameControl("control_frame", Rect(0, 0, col_w, 60), border_width=2),
        ),
        ControlDefinition(
            "panel",
            "Panel",
            60,
            69,
            lambda: PanelControl("control_panel", Rect(0, 0, col_w, 60), draw_background=True),
        ),
        ControlDefinition(
            "canvas_viewport",
            "Canvas Viewport",
            112,
            70,
            _make_canvas_viewport_panel,
            accessibility_role="group",
            accessibility_label="Canvas viewport transform sample",
        ),
    ]


__all__ = ["data_defs"]
