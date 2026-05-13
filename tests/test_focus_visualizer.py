import unittest

import pygame
from pygame import Rect

from gui_do.focus.focus_visualizer import FocusVisualizer

pygame.init()


class _StubApp:
    pass


class TestFocusVisualizerDashedRectangle(unittest.TestCase):
    def test_dashed_rectangle_stays_within_box(self):
        surface = pygame.Surface((80, 60))
        surface.fill((0, 0, 0))

        visualizer = FocusVisualizer(_StubApp())
        visualizer._draw_dashed_rectangle(surface, Rect(20, 15, 30, 20), (255, 255, 255))

        # Top and bottom border rows should not extend past the hint box.
        self.assertEqual((0, 0, 0), surface.get_at((0, 15))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((79, 15))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((0, 34))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((79, 34))[:3])

        # Left and right border columns should not extend past the hint box.
        self.assertEqual((0, 0, 0), surface.get_at((20, 0))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((20, 59))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((49, 0))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((49, 59))[:3])

        # A point on the border should be painted.
        self.assertEqual((255, 255, 255), surface.get_at((20, 15))[:3])


if __name__ == "__main__":
    unittest.main()
