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

    def _find_background_point(self, demo: GuiDoDemo) -> tuple[int, int]:
        rect = demo.screen_rect
        for y in range(8, rect.height, 24):
            for x in range(8, rect.width, 24):
                point = (x, y)
                if demo.app.overlay.point_in_any_overlay(point):
                    continue
                window_hit, focus_target = demo.app.scene.pointer_context_at(point)
                if not window_hit and focus_target is None:
                    return point
        self.fail("Could not find background point in scene")

    def test_right_click_background_opens_command_palette(self) -> None:
        demo = GuiDoDemo()
        point = self._find_background_point(demo)

        self.assertFalse(demo.app.overlay.has_overlay("__command_palette__"))
        consumed = demo.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": point, "button": 3})
        )

        self.assertTrue(consumed)
        self.assertTrue(demo.app.overlay.has_overlay("__command_palette__"))

    def test_right_click_on_control_does_not_open_command_palette(self) -> None:
        demo = GuiDoDemo()
        target = demo.exit_button.rect.center

        self.assertFalse(demo.app.overlay.has_overlay("__command_palette__"))
        demo.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": target, "button": 3})
        )

        self.assertFalse(demo.app.overlay.has_overlay("__command_palette__"))


if __name__ == "__main__":
    unittest.main()
