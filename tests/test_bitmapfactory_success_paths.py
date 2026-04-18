import unittest
from unittest.mock import patch

import pygame
from pygame import Rect

from gui.utility.bitmapfactory import WidgetGraphicsFactory


class _FakeSurface:
    def __init__(self, size, *_args, **_kwargs):
        self._size = size
        self.blit_calls = []

    def convert(self):
        return self

    def convert_alpha(self):
        return self

    def get_rect(self):
        return Rect(0, 0, self._size[0], self._size[1])

    def blit(self, bitmap, pos, *_args, **_kwargs):
        self.blit_calls.append((bitmap, pos))

    def lock(self):
        return None

    def unlock(self):
        return None

    def set_at(self, _pos, _colour):
        return None


class WidgetGraphicsFactoryRoiBatch3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_draw_arrow_state_bitmaps_success(self) -> None:
        states = [_FakeSurface((10, 10)), _FakeSurface((10, 10)), _FakeSurface((10, 10))]

        with patch.object(self.factory, "draw_frame_bitmaps", return_value=tuple(states)), patch(
            "gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)
        ), patch("gui.utility.bitmapfactory.polygon", return_value=None), patch(
            "gui.utility.bitmapfactory.rotate", side_effect=lambda surf, _deg: surf
        ), patch("gui.utility.bitmapfactory.smoothscale", side_effect=lambda _surf, size: _FakeSurface(size)):
            rendered = self.factory.draw_arrow_state_bitmaps(Rect(0, 0, 12, 8), 45)

        self.assertEqual(len(rendered), 3)
        for surface in rendered:
            self.assertEqual(len(surface.blit_calls), 1)

    def test_draw_radio_bitmap_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch(
            "gui.utility.bitmapfactory.polygon", return_value=None
        ), patch("gui.utility.bitmapfactory.smoothscale", side_effect=lambda _surf, size: _FakeSurface(size)):
            out = self.factory.draw_radio_bitmap(14, (1, 2, 3), (4, 5, 6))

        self.assertEqual(out.get_rect().size, (14, 14))

    def test_draw_window_lower_widget_bitmap_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory, "_draw_box_bitmaps", return_value=None
        ), patch("gui.utility.bitmapfactory.rect", return_value=None):
            out = self.factory.draw_window_lower_widget_bitmap(16, (1, 2, 3), (4, 5, 6))

        self.assertEqual(out.get_rect().size, (16, 16))

    def test_draw_angle_state_explicit_branches(self) -> None:
        with patch.object(self.factory, "_draw_angle_style_bitmap", return_value=_FakeSurface((8, 8))) as drawer:
            self.factory._draw_angle_state((8, 8), "idle")
            self.factory._draw_angle_state((8, 8), "hover")
            self.factory._draw_angle_state((8, 8), "armed")

        self.assertEqual(drawer.call_count, 3)

    def test_draw_angle_style_bitmap_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch(
            "gui.utility.bitmapfactory.polygon", return_value=None
        ), patch("gui.utility.bitmapfactory.smoothscale", side_effect=lambda _surf, size: _FakeSurface(size)):
            out = self.factory._draw_angle_style_bitmap((15, 11), (1, 2, 3), (4, 5, 6))

        self.assertEqual(out.get_rect().size, (15, 11))

    def test_draw_box_style_bitmaps_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory, "render_text", side_effect=[pygame.Surface((8, 4)), pygame.Surface((9, 4))]
        ), patch.object(self.factory, "_draw_box_bitmaps", return_value=None):
            out, rect = self.factory._draw_box_style_bitmaps("text", Rect(1, 2, 20, 10))

        self.assertEqual(len(out), 3)
        self.assertEqual(rect, Rect(1, 2, 20, 10))

    def test_draw_check_bitmap_success_states(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory, "_draw_box_bitmaps", return_value=None
        ), patch("gui.utility.bitmapfactory.polygon", return_value=None), patch(
            "gui.utility.bitmapfactory.smoothscale", side_effect=lambda _surf, size: _FakeSurface(size)
        ):
            idle = self.factory._draw_check_bitmap(0, 12)
            hover = self.factory._draw_check_bitmap(1, 12)
            armed = self.factory._draw_check_bitmap(2, 12)

        self.assertEqual(idle.get_rect().size, (12, 12))
        self.assertEqual(hover.get_rect().size, (12, 12))
        self.assertEqual(armed.get_rect().size, (12, 12))

    def test_draw_check_and_radio_style_bitmap_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory, "render_text", return_value=pygame.Surface((10, 8))
        ), patch.object(self.factory, "_draw_check_bitmap", return_value=_FakeSurface((8, 8))), patch.object(
            self.factory, "draw_radio_bitmap", return_value=_FakeSurface((8, 8))
        ):
            _, check_rect = self.factory._draw_check_style_bitmap(Rect(0, 0, 60, 20), 1, "x")
            _, radio_rect = self.factory._draw_radio_style_bitmap(Rect(0, 0, 60, 20), "x", (1, 2, 3), (4, 5, 6))

        self.assertGreater(check_rect.width, 0)
        self.assertGreater(radio_rect.width, 0)

    def test_draw_rounded_style_bitmaps_success(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory, "render_text", side_effect=[pygame.Surface((7, 4)), pygame.Surface((8, 4))]
        ), patch.object(self.factory, "_draw_rounded_state", return_value=None):
            out, rect = self.factory._draw_rounded_style_bitmaps("text", Rect(0, 0, 18, 10))

        self.assertEqual(len(out), 3)
        self.assertEqual(rect, Rect(0, 0, 18, 10))

    def test_draw_window_title_bar_bitmap_success(self) -> None:
        class FakeFrame:
            def __init__(self, *_args, **_kwargs) -> None:
                self.state = None
                self.surface = None

            def draw(self) -> None:
                return None

        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch(
            "gui.widgets.frame.Frame", FakeFrame
        ), patch.object(self.factory, "set_font", return_value=None), patch.object(
            self.factory, "set_last_font", return_value=None
        ), patch.object(self.factory, "render_text", return_value=pygame.Surface((8, 5))):
            out = self.factory._draw_window_title_bar_bitmap(object(), "title", 80, 14)

        self.assertEqual(out.get_rect().size, (80, 14))


if __name__ == "__main__":
    unittest.main()
