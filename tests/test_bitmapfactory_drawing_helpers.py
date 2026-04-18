import unittest

import pygame

from gui.utility.bitmapfactory import BitmapFactory
from gui.utility.constants import GuiError


class BitmapFactoryDrawingHelpersBatch3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = BitmapFactory()

    def test_draw_box_bitmap_handles_zero_sized_surface(self) -> None:
        surface = pygame.Surface((0, 0))

        self.factory._draw_box_bitmap(
            surface,
            (255, 255, 255),
            (0, 0, 0),
            (255, 255, 255),
            (0, 0, 0),
            (10, 10, 10),
        )

        self.assertEqual(surface.get_size(), (0, 0))

    def test_draw_box_bitmaps_unknown_state_is_noop(self) -> None:
        surface = pygame.Surface((5, 5))
        before = surface.copy()

        self.factory._draw_box_bitmaps(surface, "unknown")

        self.assertEqual(surface.get_buffer().raw, before.get_buffer().raw)

    def test_flood_fill_fills_connected_area(self) -> None:
        surface = pygame.Surface((4, 4))
        surface.fill((0, 0, 0))

        self.factory._flood_fill(surface, (1, 1), (255, 0, 0))

        self.assertEqual(surface.get_at((0, 0))[:3], (255, 0, 0))
        self.assertEqual(surface.get_at((3, 3))[:3], (255, 0, 0))

    def test_flood_fill_noop_when_colour_is_same(self) -> None:
        surface = pygame.Surface((3, 3))
        surface.fill((10, 20, 30))
        before = surface.copy()

        self.factory._flood_fill(surface, (1, 1), (10, 20, 30))

        self.assertEqual(surface.get_buffer().raw, before.get_buffer().raw)

    def test_flood_fill_wraps_invalid_position_error(self) -> None:
        surface = pygame.Surface((3, 3))

        with self.assertRaises(GuiError):
            self.factory._flood_fill(surface, (99, 99), (1, 2, 3))

    def test_draw_rounded_state_unknown_value_is_noop(self) -> None:
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
        before = surface.copy()

        self.factory._draw_rounded_state(surface, "unknown")

        self.assertEqual(surface.get_buffer().raw, before.get_buffer().raw)


if __name__ == "__main__":
    unittest.main()
