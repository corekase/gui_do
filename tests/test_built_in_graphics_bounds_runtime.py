import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication


class BuiltInGraphicsBoundsRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((320, 240))
        self.app = GuiApplication(self.surface)
        self.factory = self.app.theme.graphics_factory

    def tearDown(self) -> None:
        pygame.quit()

    def test_radio_bitmap_bounds_are_normalized(self) -> None:
        size = 32
        surf = self.factory.draw_radio_bitmap(size, (255, 255, 255), (0, 0, 0))
        bounds = surf.get_bounding_rect(min_alpha=1)
        self.assertEqual(bounds, Rect(0, 0, size, size))

    def test_check_bitmap_bounds_are_normalized(self) -> None:
        size = 30
        surf = self.factory._draw_check_bitmap(1, size)
        bounds = surf.get_bounding_rect(min_alpha=1)
        self.assertEqual(bounds, Rect(0, 0, size, size))

    def test_arrow_visuals_surface_size_matches_requested_rect(self) -> None:
        rect = Rect(0, 0, 36, 28)
        visuals = self.factory.draw_arrow_visuals(rect, 90)
        self.assertEqual(visuals.idle.get_size(), rect.size)
        self.assertEqual(visuals.hover.get_size(), rect.size)
        self.assertEqual(visuals.armed.get_size(), rect.size)

    def test_arrow_visuals_disabled_differs_from_frame_only(self) -> None:
        rect = Rect(0, 0, 40, 30)
        arrow_visuals = self.factory.draw_arrow_visuals(rect, 0)
        frame_visuals = self.factory.build_frame_visuals(rect)

        arrow_disabled = pygame.image.tobytes(arrow_visuals.disabled, "RGBA")
        frame_disabled = pygame.image.tobytes(frame_visuals.disabled, "RGBA")
        self.assertNotEqual(arrow_disabled, frame_disabled)


if __name__ == "__main__":
    unittest.main()
