import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.styles_demo_part import StylesShowcaseFeature
from gui import GuiApplication, PanelControl
from gui_do_demo import GuiDoDemo


class _ClickEvent:
    def __init__(self, pos) -> None:
        self.pos = pos

    def is_mouse_down(self, button=None) -> bool:
        return button in (None, 1)


class StylesShowcaseFeatureTests(unittest.TestCase):
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
        demo = SimpleNamespace(app=app, control_showcase_root=root)
        part = StylesShowcaseFeature()
        part.build(demo)
        return app, demo, part

    def test_build_creates_hidden_styles_window_with_expected_grid_counts(self) -> None:
        _app, _demo, part = self._build_part()

        self.assertEqual(part.window.rect.size, (part.WINDOW_WIDTH, part.WINDOW_HEIGHT))
        self.assertFalse(part.window.visible)
        self.assertEqual(len(part.group_controls), 30)
        self.assertEqual(len(part.button_controls), 5)
        self.assertEqual(len(part.toggle_controls), 5)
        self.assertEqual(len(part.footer_labels), 6)

    def test_window_event_handler_updates_group_footer_label(self) -> None:
        _app, _demo, part = self._build_part()

        second_group_control = part.group_controls[1]
        first_footer_label = part.footer_labels[0]

        part.styles_window_event_handler(_ClickEvent(second_group_control.rect.center))

        self.assertEqual(first_footer_label.text, "Gr: G1 ID: I2")

    def test_each_group_defaults_to_first_item_selected(self) -> None:
        _app, _demo, part = self._build_part()

        self.assertEqual(len(part.group_controls), 30)
        for group_index in range(6):
            start = group_index * 5
            group_slice = part.group_controls[start:start + 5]
            self.assertEqual(len(group_slice), 5)
            self.assertTrue(group_slice[0].pushed)
            for control in group_slice[1:]:
                self.assertFalse(control.pushed)
            self.assertEqual(part.footer_labels[group_index].text, f"Gr: G{group_index + 1} ID: I1")

    def test_radio_and_check_controls_are_centered_in_grid_cells(self) -> None:
        app, _demo, part = self._build_part()
        app.switch_scene("control_showcase")
        part.window.visible = True

        content_rect = part.window.content_rect()
        heading_y = content_rect.top + part.PADDING_Y
        controls_anchor_y = heading_y + part.HEADING_HEIGHT + part.HEADING_GAP
        app.layout.set_grid_properties(
            anchor=(content_rect.left + part.PADDING_X, controls_anchor_y),
            item_width=part.COLUMN_WIDTH,
            item_height=part.CONTROL_HEIGHT,
            column_spacing=part.COLUMN_GAP,
            row_spacing=part.CONTROL_GAP,
            use_rect=True,
        )

        group_radio = next(control for control in part.group_controls if control.control_id == "styles_radio_1")
        group_check = next(control for control in part.group_controls if control.control_id == "styles_check_1")
        button_radio = next(control for control in part.button_controls if control.control_id == "styles_button_radio")
        toggle_check = next(control for control in part.toggle_controls if control.control_id == "styles_toggle_check")

        group_radio_cell = app.layout.gridded(1, 0)
        group_check_cell = app.layout.gridded(4, 0)
        button_radio_cell = app.layout.gridded(6, 1)
        toggle_check_cell = app.layout.gridded(7, 4)

        for control, cell in (
            (group_radio, group_radio_cell),
            (group_check, group_check_cell),
            (button_radio, button_radio_cell),
            (toggle_check, toggle_check_cell),
        ):
            self.assertEqual(control.rect.width, part.CENTERED_STYLE_WIDTH)
            self.assertEqual(control.rect.centerx, cell.centerx)
            self.assertEqual(control.rect.height, cell.height)

    def test_tab_order_is_column_top_to_bottom_and_wraps(self) -> None:
        app, _demo, part = self._build_part()
        app.switch_scene("control_showcase")
        part.window.visible = True

        ordered_ids = [control.control_id for control in (part.group_controls + part.button_controls + part.toggle_controls)]
        focused_ids = []

        for _ in range(len(ordered_ids)):
            moved = app.focus.cycle_focus(app.scene, forward=True, window=None)
            self.assertTrue(moved)
            focused_ids.append(app.focus.focused_node.control_id)

        self.assertEqual(focused_ids, ordered_ids)

        moved = app.focus.cycle_focus(app.scene, forward=True, window=None)
        self.assertTrue(moved)
        self.assertEqual(app.focus.focused_node.control_id, ordered_ids[0])


class ControlShowcaseSceneWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((1280, 720))

    def tearDown(self) -> None:
        pygame.quit()

    def test_build_control_showcase_scene_wires_styles_toggle(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.screen_rect = pygame.Rect(0, 0, 1280, 720)
        demo.app = GuiApplication(self.surface)
        demo.app.create_scene("main")
        demo.app.create_scene("control_showcase")
        demo._styles_feature = SimpleNamespace(window=SimpleNamespace(visible=False))

        tile_calls = []
        demo.app.tile_windows = lambda newly_visible=None: tile_calls.append(newly_visible)

        demo._register_screen_font_roles()
        demo._build_control_showcase_scene()

        self.assertFalse(demo.showcase_styles_toggle.pushed)

        demo.showcase_styles_toggle.on_toggle(True)
        self.assertTrue(demo._styles_feature.window.visible)
        self.assertEqual(tile_calls[-1], [demo._styles_feature.window])

        demo.showcase_styles_toggle.on_toggle(False)
        self.assertFalse(demo._styles_feature.window.visible)
        self.assertIsNone(tile_calls[-1])
