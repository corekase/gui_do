import unittest
from unittest.mock import patch

import pygame

from gui.utility.bitmapfactory import WidgetGraphicsFactory
from gui.utility.constants import ButtonStyle, GuiError


class WidgetGraphicsFactoryDispatchBatch2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_get_styled_bitmaps_dispatches_to_each_style_handler(self) -> None:
        rect = pygame.Rect(0, 0, 10, 10)
        sentinel = ((object(), object(), object()), rect)

        with patch.object(self.factory, "_draw_box_style_bitmaps", return_value=sentinel) as box:
            self.assertIs(self.factory.get_styled_bitmaps(ButtonStyle.Box, "x", rect), sentinel)
            box.assert_called_once_with("x", rect)

        with patch.object(self.factory, "_draw_rounded_style_bitmaps", return_value=sentinel) as round_style:
            self.assertIs(self.factory.get_styled_bitmaps(ButtonStyle.Round, "x", rect), sentinel)
            round_style.assert_called_once_with("x", rect)

        with patch.object(self.factory, "_draw_angle_style_bitmaps", return_value=sentinel) as angle:
            self.assertIs(self.factory.get_styled_bitmaps(ButtonStyle.Angle, "x", rect), sentinel)
            angle.assert_called_once_with("x", rect)

        with patch.object(self.factory, "_draw_radio_style_bitmaps", return_value=sentinel) as radio:
            self.assertIs(self.factory.get_styled_bitmaps(ButtonStyle.Radio, "x", rect), sentinel)
            radio.assert_called_once_with("x", rect)

        with patch.object(self.factory, "_draw_check_style_bitmaps", return_value=sentinel) as check:
            self.assertIs(self.factory.get_styled_bitmaps(ButtonStyle.Check, "x", rect), sentinel)
            check.assert_called_once_with("x", rect)

    def test_draw_angle_state_falls_back_to_idle_palette_for_unknown_state(self) -> None:
        sentinel = pygame.Surface((1, 1), pygame.SRCALPHA)
        with patch.object(self.factory, "_draw_angle_style_bitmap", return_value=sentinel) as drawer:
            out = self.factory._draw_angle_state((8, 8), "unexpected")

        self.assertIs(out, sentinel)
        drawer.assert_called_once()

    def test_load_font_rejects_bad_resource_component_types(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.load_font("main", "", 12)

    def test_image_alpha_wraps_loader_failure(self) -> None:
        with patch("pygame.image.load", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.image_alpha("images", "missing.png")

        self.assertIn("failed to load image resource", str(ctx.exception))

    def test_set_font_rejects_unknown_name(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.set_font("missing")


if __name__ == "__main__":
    unittest.main()
