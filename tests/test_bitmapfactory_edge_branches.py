import unittest
from unittest.mock import patch

import pygame
from pygame import Rect

from gui.utility.bitmapfactory import BitmapFactory
from gui.utility.constants import GuiError


class _FakeSurface:
    def __init__(self, size, *_args, **_kwargs):
        self._size = size

    def convert(self):
        return self

    def convert_alpha(self):
        return self

    def get_rect(self):
        return Rect(0, 0, self._size[0], self._size[1])

    def blit(self, *_args, **_kwargs):
        return None


class _FakeFontBoom:
    def render(self, *_args, **_kwargs):
        raise RuntimeError("render boom")


class BitmapFactoryRoiBatch7Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = BitmapFactory()

    def test_set_last_font_noop_when_previous_missing(self) -> None:
        self.factory._font = object()
        self.factory._current_font_name = "current"
        self.factory._last_font_name = None

        self.factory.set_last_font()

        self.assertEqual(self.factory._current_font_name, "current")

    def test_draw_arrow_state_bitmaps_width_branch_and_guierror_reraise(self) -> None:
        states = [_FakeSurface((8, 12)) for _ in range(2)]

        with patch.object(self.factory, "draw_frame_bitmaps", return_value=tuple(states)), patch(
            "gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)
        ), patch("gui.utility.bitmapfactory.polygon", return_value=None), patch(
            "gui.utility.bitmapfactory.rotate", side_effect=lambda surf, _deg: surf
        ), patch(
            "gui.utility.bitmapfactory.smoothscale", side_effect=lambda _surf, size: _FakeSurface(size)
        ):
            rendered = self.factory.draw_arrow_state_bitmaps(Rect(0, 0, 8, 12), 45)

        self.assertEqual(len(rendered), 2)

        with patch.object(self.factory, "draw_frame_bitmaps", side_effect=GuiError("frame fail")):
            with self.assertRaises(GuiError):
                self.factory.draw_arrow_state_bitmaps(Rect(0, 0, 8, 12), 45)

    def test_draw_frame_bitmaps_reraises_guierror(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", return_value=pygame.Surface((4, 4), pygame.SRCALPHA)), patch.object(
            self.factory,
            "_draw_box_bitmaps",
            side_effect=GuiError("draw fail"),
        ):
            with self.assertRaises(GuiError):
                self.factory.draw_frame_bitmaps(Rect(0, 0, 4, 4))

    def test_reraise_paths_for_window_and_title_bar_aggregators(self) -> None:
        with patch.object(self.factory, "_draw_box_bitmaps", side_effect=GuiError("box fail")):
            with self.assertRaises(GuiError):
                self.factory.draw_window_lower_widget_bitmap(12, (1, 2, 3), (4, 5, 6))

        with patch.object(self.factory, "_draw_window_title_bar_bitmap", side_effect=GuiError("title fail")):
            with self.assertRaises(GuiError):
                self.factory.draw_window_title_bar_bitmaps(object(), "title", 100, 20)

    def test_render_text_wraps_generic_font_render_error(self) -> None:
        self.factory._font = _FakeFontBoom()

        with self.assertRaises(GuiError) as ctx:
            self.factory.render_text("hello")

        self.assertIn("failed to render text", str(ctx.exception))

    def test_file_resource_wraps_commonpath_value_error(self) -> None:
        with patch("gui.utility.bitmapfactory.os.path.commonpath", side_effect=ValueError("bad paths")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.file_resource("images", "x.png")

        self.assertIn("invalid resource path", str(ctx.exception))

    def test_image_alpha_reraises_guierror_and_register_cursor_paths(self) -> None:
        with patch("pygame.image.load", side_effect=GuiError("img fail")):
            with self.assertRaises(GuiError):
                self.factory.image_alpha("images", "missing.png")

        with patch.object(self.factory, "image_alpha", side_effect=GuiError("cursor fail")):
            with self.assertRaises(GuiError):
                self.factory.register_cursor(name="name", filename="cursor.png", hotspot=(0, 0))

        with patch.object(self.factory, "image_alpha", side_effect=RuntimeError("cursor boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.register_cursor(name="name2", filename="cursor.png", hotspot=(0, 0))

        self.assertIn("failed to load cursor", str(ctx.exception))

    def test_angle_style_bitmap_and_bitmaps_reraise_guierror(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=GuiError("surface fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_angle_style_bitmap((10, 8), (1, 2, 3), (4, 5, 6))

        with patch.object(self.factory, "render_text", side_effect=GuiError("text fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_angle_style_bitmaps("x", Rect(0, 0, 20, 10))

    def test_draw_box_bitmap_normal_and_error_paths(self) -> None:
        surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.factory._draw_box_bitmap(surface, (1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12), (13, 14, 15))

        with patch("gui.utility.bitmapfactory.line", side_effect=RuntimeError("line fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_box_bitmap(surface, (1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12), (13, 14, 15))

    def test_draw_box_bitmaps_dispatches_all_states(self) -> None:
        calls = []
        with patch.object(self.factory, "_draw_box_bitmap", side_effect=lambda *_args: calls.append(True)):
            surface = pygame.Surface((5, 5), pygame.SRCALPHA)
            self.factory._draw_box_bitmaps(surface, "idle")
            self.factory._draw_box_bitmaps(surface, "hover")
            self.factory._draw_box_bitmaps(surface, "armed")

        self.assertEqual(len(calls), 3)

    def test_check_and_radio_exception_reraise_paths(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=GuiError("surface fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_check_bitmap(2, 12)

        with patch.object(self.factory, "render_text", side_effect=GuiError("text fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_check_style_bitmap(Rect(0, 0, 20, 10), 1, "x")
            with self.assertRaises(GuiError):
                self.factory._draw_radio_style_bitmap(Rect(0, 0, 20, 10), "x", (1, 2, 3), (4, 5, 6))

        with patch.object(self.factory, "_draw_check_style_bitmap", side_effect=GuiError("check fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_check_style_bitmaps("x", Rect(0, 0, 20, 10))

        with patch.object(self.factory, "_draw_radio_style_bitmap", side_effect=GuiError("radio fail")):
            with self.assertRaises(GuiError):
                self.factory._draw_radio_style_bitmaps("x", Rect(0, 0, 20, 10))

    def test_round_and_rounded_state_branches(self) -> None:
        with patch("gui.utility.bitmapfactory.circle", return_value=None), patch(
            "gui.utility.bitmapfactory.line", return_value=None
        ), patch.object(self.factory, "_flood_fill", return_value=None) as flood_fill:
            surface = pygame.Surface((20, 20), pygame.SRCALPHA)
            self.factory._draw_round_style_bitmap(surface, (1, 2, 3), (4, 5, 6))

        flood_fill.assert_called_once()

        calls = []
        with patch.object(self.factory, "_draw_round_style_bitmap", side_effect=lambda *_args: calls.append(True)):
            surface = pygame.Surface((20, 20), pygame.SRCALPHA)
            self.factory._draw_rounded_state(surface, "idle")
            self.factory._draw_rounded_state(surface, "hover")
            self.factory._draw_rounded_state(surface, "armed")

        self.assertEqual(len(calls), 3)

    def test_flood_fill_reraises_guierror(self) -> None:
        surface = pygame.Surface((5, 5), pygame.SRCALPHA)
        with patch("gui.utility.bitmapfactory.PixelArray", side_effect=GuiError("pixel fail")):
            with self.assertRaises(GuiError):
                self.factory._flood_fill(surface, (1, 1), (1, 2, 3))


if __name__ == "__main__":
    unittest.main()
