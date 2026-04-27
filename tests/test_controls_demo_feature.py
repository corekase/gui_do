import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_features.controls_demo_feature import ControlsShowcaseFeature
from gui_do import (
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    ColorPickerControl,
    DataGridControl,
    DropdownControl,
    FrameControl,
    GuiApplication,
    ImageControl,
    ListViewControl,
    MenuBarControl,
    NotificationPanelControl,
    PanelControl,
    RangeSliderControl,
    RichLabelControl,
    ScrollbarControl,
    ScrollViewControl,
    SliderControl,
    SpinnerControl,
    SplitterControl,
    TabControl,
    TextAreaControl,
    TextInputControl,
    TreeControl,
    ToggleControl,
)


class ControlsShowcaseFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((1280, 720))

    def tearDown(self) -> None:
        pygame.quit()

    def _build_feature(self, width: int = 1280, height: int = 720):
        app = GuiApplication(self.surface)
        app.create_scene("main")
        app.create_scene("control_showcase")
        root = app.add(
            PanelControl("control_showcase_root", pygame.Rect(0, 0, width, height), draw_background=False),
            scene_name="control_showcase",
        )
        host = SimpleNamespace(
            app=app,
            control_showcase_root=root,
            screen_rect=pygame.Rect(0, 0, width, height),
            TASK_PANEL_CONTROL_FONT_ROLE="screen.main.task_panel.control",
        )
        feature = ControlsShowcaseFeature(pygame.Rect(24, 60, width - 48, height - 120))
        feature.build(host)
        return app, host, feature

    def test_build_includes_all_showcase_controls_except_task_panel_and_window(self) -> None:
        _app, _host, feature = self._build_feature()

        expected_types = {
            ArrowBoxControl,
            ButtonControl,
            ButtonGroupControl,
            CanvasControl,
            ColorPickerControl,
            DataGridControl,
            DropdownControl,
            FrameControl,
            ImageControl,
            ListViewControl,
            MenuBarControl,
            NotificationPanelControl,
            PanelControl,
            RangeSliderControl,
            RichLabelControl,
            ScrollbarControl,
            ScrollViewControl,
            SliderControl,
            SpinnerControl,
            SplitterControl,
            TabControl,
            TextAreaControl,
            TextInputControl,
            TreeControl,
            ToggleControl,
        }
        self.assertEqual({type(control) for control in feature.controls}, expected_types)

    def test_arrow_box_shows_all_directions(self) -> None:
        _app, _host, feature = self._build_feature()

        arrow_controls = [control for control in feature.controls if isinstance(control, ArrowBoxControl)]
        self.assertEqual(len(arrow_controls), 4)
        self.assertEqual({control.direction for control in arrow_controls}, {0, 90, 180, 270})

    def test_showcase_does_not_include_standalone_label_control(self) -> None:
        _app, _host, feature = self._build_feature()
        self.assertNotIn("label", {placed.name for placed in feature.placed_controls})

    def test_all_showcase_controls_are_enabled_by_default(self) -> None:
        _app, _host, feature = self._build_feature()
        self.assertTrue(feature.controls)
        self.assertTrue(all(control.enabled for control in feature.controls))

    def test_each_control_has_left_aligned_label_above_it(self) -> None:
        _app, _host, feature = self._build_feature()

        self.assertLess(len(feature.control_labels), len(feature.controls))
        for placed in feature.placed_controls:
            if placed.label is None:
                continue
            self.assertEqual(placed.label.align, "left")
            self.assertEqual(placed.label.rect.left, placed.control.rect.left)
            self.assertEqual(placed.control.rect.top, placed.label.rect.bottom + feature.LABEL_GAP)

    def test_arrow_boxes_are_grouped_under_single_label_without_individual_labels(self) -> None:
        _app, _host, feature = self._build_feature()

        arrow_placed = [placed for placed in feature.placed_controls if placed.name.startswith("arrow_")]
        self.assertEqual(len(arrow_placed), 4)
        self.assertTrue(all(placed.label is None for placed in arrow_placed))
        group_texts = {label.text for label in feature.control_labels}
        self.assertIn("ArrowBoxes", group_texts)

    def test_vertical_pair_uses_single_group_label(self) -> None:
        _app, _host, feature = self._build_feature()

        vertical_placed = [
            placed
            for placed in feature.placed_controls
            if placed.name in {"vertical_scrollbar", "vertical_slider"}
        ]
        self.assertEqual(len(vertical_placed), 2)
        self.assertTrue(all(placed.label is None for placed in vertical_placed))
        group_texts = {label.text for label in feature.control_labels}
        self.assertIn("V.", group_texts)

    def test_horizontal_control_labels_use_short_names(self) -> None:
        _app, _host, feature = self._build_feature()
        labels_by_name = {placed.name: placed.label.text for placed in feature.placed_controls if placed.label is not None}
        self.assertEqual(labels_by_name["horizontal_scrollbar"], "H. Scrollbar")
        self.assertEqual(labels_by_name["horizontal_slider"], "H. Slider")

    def test_button_toggle_and_group_rows_expand_to_requested_matrix(self) -> None:
        _app, _host, feature = self._build_feature()

        button_names = [placed.name for placed in feature.placed_controls if placed.name in {"button", "button_2", "button_3"}]
        toggle_names = [placed.name for placed in feature.placed_controls if placed.name in {"toggle", "toggle_2", "toggle_3"}]
        group_controls = [placed for placed in feature.placed_controls if placed.name.startswith("button_group_")]

        self.assertEqual(len(button_names), 3)
        self.assertEqual(len(toggle_names), 3)
        self.assertEqual(len(group_controls), 9)

        labeled_group_controls = [placed for placed in group_controls if placed.label is not None]
        self.assertEqual({placed.name for placed in labeled_group_controls}, {"button_group_a1", "button_group_b1", "button_group_c1"})
        self.assertEqual({placed.label.text for placed in labeled_group_controls}, {"Group A", "Group B", "Group C"})

        unlabeled_group_controls = [placed for placed in group_controls if placed.label is None]
        self.assertEqual(len(unlabeled_group_controls), 6)

    def test_tab_control_is_square_column_with_three_named_label_tabs(self) -> None:
        _app, _host, feature = self._build_feature()

        tab_placed = next(placed for placed in feature.placed_controls if placed.name == "tab")
        self.assertIsInstance(tab_placed.control, TabControl)

        ctrl = tab_placed.control
        self.assertEqual(ctrl.rect.width, ctrl.rect.height, "Tab column must be square (width == height)")

        items = ctrl.items()
        self.assertEqual([item.key for item in items], ["one", "two", "three"])
        self.assertEqual([item.label for item in items], ["One", "Two", "Three"])
        self.assertTrue(all(item.content is not None for item in items))
        for item in items:
            self.assertTrue(hasattr(item.content, "text"), f"Tab '{item.key}' content must have .text")
            self.assertEqual(item.content.text, item.label)

    def test_image_control_is_square_column_after_tab(self) -> None:
        _app, _host, feature = self._build_feature()

        tab_placed = next(placed for placed in feature.placed_controls if placed.name == "tab")
        img_placed = next(placed for placed in feature.placed_controls if placed.name == "image")

        img = img_placed.control
        self.assertEqual(img.rect.width, img.rect.height, "Image column must be square (width == height)")
        self.assertEqual(img.rect.width, tab_placed.control.rect.width, "Image and tab columns must be the same square size")
        self.assertGreater(img.rect.left, tab_placed.control.rect.right - 1, "Image column must be to the right of tab column")


    def test_new_row_starts_below_data_grid_with_list_view_then_dropdown(self) -> None:
        _app, _host, feature = self._build_feature()

        by_name = {placed.name: placed for placed in feature.placed_controls}
        dg = by_name["data_grid"]
        lv = by_name["list_view"]
        dd = by_name["dropdown"]
        splitter = by_name["splitter"]

        # ListView and Dropdown must be below the data grid slot bottom
        self.assertGreater(lv.control.rect.top, dg.control.rect.bottom,
                           "ListView must start below data grid")

        # New row starts from the left edge of the content area.
        self.assertEqual(
            lv.control.rect.left,
            feature.rect.left + feature.CONTENT_PADDING_X,
            "ListView column must restart from left content edge",
        )

        # ListView and Dropdown share the same left edge (col 0 of new row)
        self.assertEqual(lv.control.rect.left, dd.control.rect.left,
                         "ListView and Dropdown must share column left edge")
        self.assertEqual(lv.control.rect.left, splitter.control.rect.left,
                         "Splitter must share the first-column left edge")

        # ListView and Dropdown are both 200px wide
        self.assertEqual(lv.control.rect.width, 200)
        self.assertEqual(dd.control.rect.width, 200)
        self.assertEqual(splitter.control.rect.width, 200)

        # Dropdown top must be below ListView bottom
        self.assertGreater(dd.control.rect.top, lv.control.rect.bottom,
                           "Dropdown must be below ListView")
        self.assertGreater(splitter.control.rect.top, dd.control.rect.bottom,
                           "Splitter must be below Dropdown")

    def test_canvas_frame_top_row_and_panel_spans_next_row(self) -> None:
        _app, _host, feature = self._build_feature()
        by_name = {placed.name: placed for placed in feature.placed_controls}

        canvas = by_name["canvas"].control
        frame = by_name["frame"].control
        panel = by_name["panel"].control

        self.assertEqual(canvas.rect.top, frame.rect.top)
        self.assertLess(canvas.rect.left, frame.rect.left)
        self.assertGreater(panel.rect.top, canvas.rect.bottom)
        self.assertEqual(panel.rect.left, canvas.rect.left)
        self.assertEqual(panel.rect.right, frame.rect.right)

    def test_panel_label_does_not_overlap_canvas_control(self) -> None:
        _app, _host, feature = self._build_feature()
        by_name = {placed.name: placed for placed in feature.placed_controls}

        canvas_placed = by_name["canvas"]
        panel_placed = by_name["panel"]
        self.assertIsNotNone(panel_placed.label)
        self.assertGreaterEqual(panel_placed.label.rect.top, canvas_placed.control.rect.bottom)

    def test_splitter_next_tab_wraps_to_arrow_box_without_hidden_task_panel_hops(self) -> None:
        app, host, feature = self._build_feature()
        app.switch_scene("control_showcase")
        feature.configure_accessibility(host, tab_index_start=0)

        by_name = {placed.name: placed for placed in feature.placed_controls}
        splitter = by_name["splitter"].control
        arrow_ids = {
            by_name["arrow_up"].control.control_id,
            by_name["arrow_down"].control.control_id,
            by_name["arrow_left"].control.control_id,
            by_name["arrow_right"].control.control_id,
        }

        app.focus.set_focus(splitter, via_keyboard=True)
        # First Tab only arms traversal hint; second Tab advances.
        app.focus.cycle_focus(app.scene, forward=True)
        app.focus.cycle_focus(app.scene, forward=True)
        self.assertIsNotNone(app.focus.focused_node)
        self.assertIn(app.focus.focused_node.control_id, arrow_ids | {"control_tree"})

    def test_columns_wrap_to_new_row_of_columns_from_left(self) -> None:
        _app, _host, feature = self._build_feature(width=900, height=720)

        widths = {placed.control.rect.width for placed in feature.placed_controls}
        heights = {placed.control.rect.height for placed in feature.placed_controls}
        self.assertGreater(len(widths), 3)
        self.assertGreater(len(heights), 4)

    def test_slider_scrollbar_special_column_sequence(self) -> None:
        _app, _host, feature = self._build_feature()

        by_name = {placed.name: placed for placed in feature.placed_controls}
        h_slider = by_name["horizontal_slider"]
        h_scrollbar = by_name["horizontal_scrollbar"]
        v_slider = by_name["vertical_slider"]
        v_scrollbar = by_name["vertical_scrollbar"]

        self.assertEqual(h_slider.column_index, h_scrollbar.column_index)
        self.assertEqual(h_slider.row_index, h_scrollbar.row_index + 1)

        self.assertEqual(v_slider.column_index, h_slider.column_index + 1)
        self.assertEqual(v_scrollbar.column_index, v_slider.column_index)
        self.assertEqual(v_slider.row_index, v_scrollbar.row_index + 1)

        controls_in_vertical_column = [
            placed.name
            for placed in feature.placed_controls
            if placed.column_index == v_slider.column_index
        ]
        self.assertEqual(set(controls_in_vertical_column), {"vertical_slider", "vertical_scrollbar"})

    def test_rich_label_uses_multiline_rich_text_content(self) -> None:
        _app, _host, feature = self._build_feature()

        rich = next(placed.control for placed in feature.placed_controls if placed.name == "rich_label")
        self.assertIsInstance(rich, RichLabelControl)
        self.assertIn("\n", rich.text)
        self.assertIn("**", rich.text)
        self.assertIn("_", rich.text)
        self.assertIn("`", rich.text)

    def test_accessibility_tab_order_matches_control_addition_order(self) -> None:
        _app, host, feature = self._build_feature()

        next_index = feature.configure_accessibility(host, tab_index_start=5)
        self.assertTrue(feature._focus_controls)

        for offset, control in enumerate(feature._focus_controls):
            self.assertEqual(control.tab_index, 5 + offset)
        self.assertEqual(next_index, 5 + len(feature._focus_controls))

    def test_task_panel_return_button_exists_and_action_is_wired(self) -> None:
        app, _host, feature = self._build_feature()

        self.assertIsNotNone(feature.task_panel)
        self.assertTrue(feature.task_panel.auto_hide)
        self.assertEqual(feature.showcase_return_button.style, "angle")

        app.switch_scene("control_showcase")
        feature.showcase_return_button._invoke_click()
        self.assertEqual(app.active_scene_name, "main")

    def test_on_update_sets_initial_focus_to_first_focusable_control(self) -> None:
        app, host, feature = self._build_feature()
        feature.configure_accessibility(host, tab_index_start=0)
        app.switch_scene("control_showcase")

        self.assertIsNone(app.focus.focused_node)
        feature.on_update(host)

        self.assertIsNotNone(feature._initial_focus_control)
        self.assertIs(app.focus.focused_node, feature._initial_focus_control)


if __name__ == "__main__":
    unittest.main()
