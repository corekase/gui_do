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
    DropdownControl,
    FrameControl,
    GuiApplication,
    ImageControl,
    LabelControl,
    ListViewControl,
    PanelControl,
    ScrollbarControl,
    SliderControl,
    TextInputControl,
    ToggleControl,
)


class ControlsShowcaseFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((1280, 720))

    def tearDown(self) -> None:
        pygame.quit()

    def _build_part(self):
        app = GuiApplication(self.surface)
        app.create_scene("control_showcase")
        root = app.add(
            PanelControl("control_showcase_root", pygame.Rect(0, 0, 1280, 720), draw_background=False),
            scene_name="control_showcase",
        )
        host = SimpleNamespace(app=app, control_showcase_root=root)
        feature = ControlsShowcaseFeature(pygame.Rect(24, 140, 1232, 500))
        feature.build(host)
        return app, host, feature

    def test_build_creates_enabled_and_disabled_control_catalogs(self) -> None:
        _app, _host, feature = self._build_part()

        self.assertEqual(len(feature.enabled_controls), 27)
        self.assertEqual(len(feature.disabled_controls), 27)
        self.assertIsNotNone(feature.enabled_title)
        self.assertIsNotNone(feature.disabled_title)

        expected_types = {
            ButtonControl,
            LabelControl,
            ToggleControl,
            ArrowBoxControl,
            ButtonGroupControl,
            ImageControl,
            CanvasControl,
            SliderControl,
            ScrollbarControl,
            PanelControl,
            TextInputControl,
            ListViewControl,
            DropdownControl,
        }
        self.assertEqual({type(control) for control in feature.enabled_controls}, expected_types)

    def test_mirrored_layout_pairs_disabled_counterparts(self) -> None:
        _app, _host, feature = self._build_part()

        allowed_enabled_ids = {"canvas_label_disabled", "panel_label_disabled"}
        self.assertEqual(len(feature.enabled_controls), len(feature.disabled_controls))
        for enabled_control, disabled_control in zip(feature.enabled_controls, feature.disabled_controls):
            self.assertIs(type(enabled_control), type(disabled_control))
            if disabled_control.control_id in allowed_enabled_ids:
                self.assertTrue(disabled_control.enabled)
            else:
                self.assertFalse(disabled_control.enabled)
            self.assertTrue(enabled_control.enabled)

    def test_block_labels_are_enabled_in_disabled_section(self) -> None:
        """Verify that block labels in disabled section are enabled state."""
        _app, _host, feature = self._build_part()

        # All block labels should be enabled (not inherited disabled state)
        for block_label in feature.disabled_control_labels:
            self.assertTrue(block_label.enabled, f"Block label {block_label.control_id} should be enabled")

    def test_block_structure_created(self) -> None:
        """Verify that blocks are created with correct structure."""
        _app, _host, feature = self._build_part()

        # Should have blocks for both enabled and disabled
        self.assertEqual(len(feature.enabled_blocks), 10)
        self.assertEqual(len(feature.disabled_blocks), 10)

        # Block names should match definitions
        expected_block_names = [
            "arrow_cluster",
            "button_groups",
            "buttons_and_indicators",
            "horizontal_sliders",
            "vertical_sliders",
            "image_block",
            "canvas_panel_block",
            "text_input_block",
            "list_view_block",
            "dropdown_block",
        ]
        enabled_block_names = [block["name"] for block in feature.enabled_blocks]
        disabled_block_names = [block["name"] for block in feature.disabled_blocks]
        self.assertEqual(enabled_block_names, expected_block_names)
        self.assertEqual(disabled_block_names, expected_block_names)

    def test_control_distribution_across_blocks(self) -> None:
        """Verify controls are properly distributed across blocks."""
        _app, _host, feature = self._build_part()

        # Verify control counts per block
        # arrow_cluster: 4 arrows in TL, TR, BL, BR order
        self.assertEqual(len(feature.enabled_blocks[0]["controls"]), 4)
        self.assertTrue(all(isinstance(c, ArrowBoxControl) for c in feature.enabled_blocks[0]["controls"]))
        arrow_directions = [c.direction for c in feature.enabled_blocks[0]["controls"]]
        self.assertEqual(arrow_directions, [90, 270, 180, 0])

        # button_groups: 3x3 grid — 3 independent groups (columns) x 3 buttons (rows)
        # Controls stored in column-major order: A1,A2,A3, B1,B2,B3, C1,C2,C3
        self.assertEqual(len(feature.enabled_blocks[1]["controls"]), 9)
        self.assertTrue(all(isinstance(c, ButtonGroupControl) for c in feature.enabled_blocks[1]["controls"]))
        # First button in each group (A1=idx 0, B1=idx 3, C1=idx 6) auto-armed
        for grp_start in (0, 3, 6):
            self.assertTrue(feature.enabled_blocks[1]["controls"][grp_start].pushed,
                            f"Button at index {grp_start} should be auto-armed (first of its group)")
            self.assertFalse(feature.enabled_blocks[1]["controls"][grp_start + 1].pushed)
            self.assertFalse(feature.enabled_blocks[1]["controls"][grp_start + 2].pushed)
        # Disabled section: same pattern
        for grp_start in (0, 3, 6):
            self.assertTrue(feature.disabled_blocks[1]["controls"][grp_start].pushed,
                            f"Disabled button at index {grp_start} should be auto-armed")

        # buttons_and_indicators: button, toggle (2)
        self.assertEqual(len(feature.enabled_blocks[2]["controls"]), 2)
        self.assertIsInstance(feature.enabled_blocks[2]["controls"][0], ButtonControl)
        self.assertIsInstance(feature.enabled_blocks[2]["controls"][1], ToggleControl)

        # horizontal_sliders: h_slider, h_scrollbar (2)
        self.assertEqual(len(feature.enabled_blocks[3]["controls"]), 2)
        self.assertIsInstance(feature.enabled_blocks[3]["controls"][0], SliderControl)
        self.assertIsInstance(feature.enabled_blocks[3]["controls"][1], ScrollbarControl)

        # vertical_sliders: v_slider, v_scrollbar (2) — in its own dedicated layout column
        self.assertEqual(len(feature.enabled_blocks[4]["controls"]), 2)
        self.assertIsInstance(feature.enabled_blocks[4]["controls"][0], SliderControl)
        self.assertIsInstance(feature.enabled_blocks[4]["controls"][1], ScrollbarControl)

        # image_block: image (1)
        self.assertEqual(len(feature.enabled_blocks[5]["controls"]), 1)
        self.assertIsInstance(feature.enabled_blocks[5]["controls"][0], ImageControl)

        # canvas_panel_block: canvas_label, canvas, panel_label, panel (4)
        self.assertEqual(len(feature.enabled_blocks[6]["controls"]), 4)
        self.assertIsInstance(feature.enabled_blocks[6]["controls"][0], LabelControl)
        self.assertIsInstance(feature.enabled_blocks[6]["controls"][1], CanvasControl)
        self.assertIsInstance(feature.enabled_blocks[6]["controls"][2], LabelControl)
        self.assertIsInstance(feature.enabled_blocks[6]["controls"][3], PanelControl)

    def test_all_controls_mirrored_between_sections(self) -> None:
        """Verify all controls exist in both enabled and disabled sections."""
        _app, _host, feature = self._build_part()

        # Flatten all controls from blocks
        enabled_types = [type(control) for block in feature.enabled_blocks for control in block["controls"]]
        disabled_types = [type(control) for block in feature.disabled_blocks for control in block["controls"]]

        # Both should have same types
        self.assertEqual(set(enabled_types), set(disabled_types))
        self.assertEqual(len(enabled_types), 27)
        self.assertEqual(len(disabled_types), 27)

    def test_configure_accessibility_assigns_enabled_focus_order_in_creation_sequence(self) -> None:
        _app, host, feature = self._build_part()

        next_index = feature.configure_accessibility(host, tab_index_start=7)

        focus_controls = list(feature._accessibility_focus_controls)

        self.assertTrue(focus_controls)
        self.assertEqual(focus_controls[0].control_id, "arrow_up_enabled")
        self.assertEqual(focus_controls[-1].control_id, "dropdown_enabled")
        expected_ids = [
            "arrow_up_enabled",
            "arrow_down_enabled",
            "arrow_left_enabled",
            "arrow_right_enabled",
            "button_enabled",
            "toggle_enabled",
            "btn_grp_a1_enabled",
            "btn_grp_a2_enabled",
            "btn_grp_a3_enabled",
            "btn_grp_b1_enabled",
            "btn_grp_b2_enabled",
            "btn_grp_b3_enabled",
            "btn_grp_c1_enabled",
            "btn_grp_c2_enabled",
            "btn_grp_c3_enabled",
            "slider_enabled",
            "scrollbar_enabled",
            "v_slider_enabled",
            "v_scrollbar_enabled",
            "text_input_enabled",
            "list_view_enabled",
            "dropdown_enabled",
        ]
        self.assertEqual([control.control_id for control in focus_controls], expected_ids)
        allowed_types = {"ArrowBoxControl", "ButtonControl", "ToggleControl", "ButtonGroupControl", "SliderControl", "ScrollbarControl", "TextInputControl", "ListViewControl", "DropdownControl"}
        self.assertEqual({control.__class__.__name__ for control in focus_controls}, allowed_types)
        self.assertEqual(next_index, 7 + len(focus_controls))
        for offset, control in enumerate(focus_controls):
            self.assertEqual(control.tab_index, 7 + offset)

        self.assertEqual(feature.enabled_blocks[0]["controls"][0].accessibility_role, "button")
        self.assertEqual(feature.enabled_blocks[0]["controls"][0].accessibility_label, "Arrow up")
        self.assertEqual(feature.enabled_blocks[1]["controls"][0].accessibility_role, "button")
        self.assertEqual(feature.enabled_blocks[1]["controls"][0].accessibility_label, "Group A option 1")
        self.assertEqual(feature.enabled_blocks[2]["controls"][0].accessibility_role, "button")
        self.assertEqual(feature.enabled_blocks[2]["controls"][0].accessibility_label, "Showcase button")
        self.assertEqual(feature.enabled_blocks[2]["controls"][1].accessibility_role, "toggle")
        self.assertEqual(feature.enabled_blocks[2]["controls"][1].accessibility_label, "Showcase toggle")
        self.assertEqual(feature.enabled_blocks[3]["controls"][0].accessibility_role, "slider")
        self.assertEqual(feature.enabled_blocks[3]["controls"][0].accessibility_label, "Horizontal slider")
        self.assertEqual(feature.enabled_blocks[3]["controls"][1].accessibility_role, "scrollbar")
        self.assertEqual(feature.enabled_blocks[3]["controls"][1].accessibility_label, "Horizontal scrollbar")
        self.assertEqual(feature.enabled_blocks[4]["controls"][0].accessibility_role, "slider")
        self.assertEqual(feature.enabled_blocks[4]["controls"][0].accessibility_label, "Vertical slider")
        self.assertEqual(feature.enabled_blocks[4]["controls"][1].accessibility_role, "scrollbar")
        self.assertEqual(feature.enabled_blocks[4]["controls"][1].accessibility_label, "Vertical scrollbar")

        explicit_types = (ArrowBoxControl, ButtonControl, ButtonGroupControl, ToggleControl, SliderControl, ScrollbarControl)
        non_registered_focusables = [
            control
            for control in feature.enabled_controls
            if isinstance(control, explicit_types)
            and control not in focus_controls
        ]
        self.assertFalse(non_registered_focusables)

    def test_on_update_sets_initial_focus_to_first_created_enabled_focus_control(self) -> None:
        app, host, feature = self._build_part()
        feature.configure_accessibility(host, tab_index_start=0)
        app.switch_scene("control_showcase")

        self.assertIsNone(app.focus.focused_node)
        feature.on_update(host)

        self.assertIsNotNone(feature._initial_focus_control)
        self.assertIs(app.focus.focused_node, feature._initial_focus_control)
        self.assertEqual(app.focus.focused_node.control_id, "arrow_up_enabled")

    def test_canvas_panel_and_image_are_not_focus_accessible(self) -> None:
        _app, _host, feature = self._build_part()

        blocked_types = {CanvasControl, PanelControl, ImageControl}
        blocked = [control for control in feature.enabled_controls if type(control) in blocked_types]
        self.assertTrue(blocked)
        for control in blocked:
            self.assertEqual(control.tab_index, -1)
            self.assertNotIn(control, feature._accessibility_focus_controls)


if __name__ == "__main__":
    unittest.main()
