import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do_demo import GuiDoDemo


class GuiDoDemoMainSceneControlsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_main_scene_includes_all_controls_except_task_panel_and_window(self) -> None:
        demo = GuiDoDemo()

        scene_types = set()
        stack = list(demo.app.scene.nodes)
        while stack:
            node = stack.pop()
            scene_types.add(type(node).__name__)
            stack.extend(getattr(node, "children", []) or [])

        expected = {
            "ArrowBoxControl",
            "ButtonControl",
            "ButtonGroupControl",
            "CanvasControl",
            "ColorPickerControl",
            "DataGridControl",
            "DropdownControl",
            "FrameControl",
            "ImageControl",
            "LabelControl",
            "ListViewControl",
            "MenuBarControl",
            "NotificationPanelControl",
            "OverlayPanelControl",
            "PanelControl",
            "RangeSliderControl",
            "RichLabelControl",
            "ScrollbarControl",
            "ScrollViewControl",
            "SliderControl",
            "SpinnerControl",
            "SplitterControl",
            "TabControl",
            "TextAreaControl",
            "TextInputControl",
            "ToggleControl",
            "TreeControl",
        }

        self.assertTrue(expected.issubset(scene_types), sorted(expected - scene_types))

    def test_notification_preview_is_fixed_above_overlay_panel_not_scrolled_content(self) -> None:
        demo = GuiDoDemo()

        scroll = demo.main_controls_scroll
        notification_panel = demo.main_scene_notification_panel
        overlay_panel = demo.main_scene_overlay_panel

        self.assertNotIn(notification_panel, scroll.children)
        self.assertEqual(notification_panel.parent, demo.main_controls_dock)
        self.assertGreaterEqual(notification_panel.rect.top, scroll.rect.bottom)
        self.assertLessEqual(notification_panel.rect.bottom, overlay_panel.rect.top)


if __name__ == "__main__":
    unittest.main()
