import unittest
from unittest.mock import patch

import pygame

from gui.utility.graphics.widget_graphics_factory import WidgetGraphicsFactory
from gui.utility.events import GuiError


class WidgetGraphicsFactoryExceptionWrappingBatch4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_draw_round_style_bitmap_wraps_generic_draw_error(self) -> None:
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)

        with patch("gui.utility.graphics.widget_graphics_factory.circle", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_round_style_bitmap(surface, (1, 2, 3), (4, 5, 6))

        self.assertIn("failed to draw round style bitmap", str(ctx.exception))

    def test_draw_round_style_bitmap_reraises_guierror(self) -> None:
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)

        with patch("gui.utility.graphics.widget_graphics_factory.circle", side_effect=GuiError("round-fail")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_round_style_bitmap(surface, (1, 2, 3), (4, 5, 6))

        self.assertEqual(str(ctx.exception), "round-fail")

    def test_draw_box_style_bitmaps_wraps_generic_render_error(self) -> None:
        with patch.object(self.factory, "render_text", side_effect=RuntimeError("text-boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_box_style_bitmaps("abc", pygame.Rect(0, 0, 10, 10))

        self.assertIn("failed to draw box style bitmaps", str(ctx.exception))

    def test_draw_box_style_bitmaps_reraises_guierror(self) -> None:
        with patch.object(self.factory, "render_text", side_effect=GuiError("font-fail")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_box_style_bitmaps("abc", pygame.Rect(0, 0, 10, 10))

        self.assertEqual(str(ctx.exception), "font-fail")

    def test_draw_rounded_style_bitmaps_wraps_generic_render_error(self) -> None:
        with patch.object(self.factory, "render_text", side_effect=RuntimeError("text-boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_rounded_style_bitmaps("abc", pygame.Rect(0, 0, 10, 10))

        self.assertIn("failed to draw rounded style bitmaps", str(ctx.exception))

    def test_draw_rounded_style_bitmaps_reraises_guierror(self) -> None:
        with patch.object(self.factory, "render_text", side_effect=GuiError("font-fail")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_rounded_style_bitmaps("abc", pygame.Rect(0, 0, 10, 10))

        self.assertEqual(str(ctx.exception), "font-fail")


if __name__ == "__main__":
    unittest.main()
