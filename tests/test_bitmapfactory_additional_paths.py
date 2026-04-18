import unittest
from unittest.mock import patch

import pygame
from pygame import Rect

from gui.utility.bitmapfactory import WidgetGraphicsFactory
from gui.utility.constants import GuiError, colours


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


class WidgetGraphicsFactoryAdditionalPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_draw_frame_bitmaps_builds_idle_hover_armed(self) -> None:
        states = []

        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory,
            "_draw_box_bitmaps",
            side_effect=lambda _surface, state: states.append(state),
        ):
            rendered = self.factory.draw_frame_bitmaps(Rect(0, 0, 9, 7))

        self.assertEqual(len(rendered), 3)
        self.assertEqual(states, ["idle", "hover", "armed"])

    def test_draw_frame_bitmaps_wraps_generic_failure(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.draw_frame_bitmaps(Rect(0, 0, 9, 7))

        self.assertIn("failed to draw frame bitmaps", str(ctx.exception))

    def test_draw_arrow_state_bitmaps_wraps_generic_failure(self) -> None:
        with patch.object(self.factory, "draw_frame_bitmaps", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.draw_arrow_state_bitmaps(Rect(0, 0, 10, 10), 45)

        self.assertIn("failed to draw arrow state bitmaps", str(ctx.exception))

    def test_draw_window_title_bar_bitmaps_aggregates_two_surfaces(self) -> None:
        first = object()
        second = object()

        with patch.object(self.factory, "_draw_window_title_bar_bitmap", side_effect=[first, second]) as drawer:
            output = self.factory.draw_window_title_bar_bitmaps(object(), "title", 120, 20)

        self.assertEqual(output, (first, second))
        self.assertEqual(drawer.call_count, 2)

    def test_draw_check_style_bitmaps_uses_first_hit_rect(self) -> None:
        r0 = Rect(1, 2, 3, 4)
        r1 = Rect(5, 6, 7, 8)
        r2 = Rect(9, 10, 11, 12)

        with patch.object(
            self.factory,
            "_draw_check_style_bitmap",
            side_effect=[(object(), r0), (object(), r1), (object(), r2)],
        ):
            bitmaps, hit_rect = self.factory._draw_check_style_bitmaps("x", Rect(0, 0, 30, 20))

        self.assertEqual(len(bitmaps), 3)
        self.assertEqual(hit_rect, r0)

    def test_draw_radio_style_bitmaps_uses_first_hit_rect(self) -> None:
        r0 = Rect(1, 2, 3, 4)
        r1 = Rect(5, 6, 7, 8)
        r2 = Rect(9, 10, 11, 12)

        with patch.object(
            self.factory,
            "_draw_radio_style_bitmap",
            side_effect=[(object(), r0), (object(), r1), (object(), r2)],
        ):
            bitmaps, hit_rect = self.factory._draw_radio_style_bitmaps("x", Rect(0, 0, 30, 20))

        self.assertEqual(len(bitmaps), 3)
        self.assertEqual(hit_rect, r0)

    def test_draw_window_lower_widget_bitmap_wraps_generic_failure(self) -> None:
        with patch.object(self.factory, "_draw_box_bitmaps", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.draw_window_lower_widget_bitmap(12, (1, 2, 3), (4, 5, 6))

        self.assertIn("failed to draw window lower widget bitmap", str(ctx.exception))

    def test_draw_radio_bitmap_wraps_generic_failure(self) -> None:
        with patch("gui.utility.bitmapfactory.polygon", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.draw_radio_bitmap(12, (1, 2, 3), (4, 5, 6))

        self.assertIn("failed to draw radio bitmap", str(ctx.exception))

    def test_load_font_reraises_guierror(self) -> None:
        with patch("pygame.font.Font", side_effect=GuiError("font-fail")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.load_font("main", "missing.ttf", 12)

        self.assertEqual(str(ctx.exception), "font-fail")

    def test_draw_angle_style_bitmaps_builds_three_states_and_returns_rect(self) -> None:
        state_calls = []

        with patch.object(
            self.factory,
            "render_text",
            side_effect=[pygame.Surface((6, 4)), pygame.Surface((7, 4))],
        ), patch.object(
            self.factory,
            "_draw_angle_state",
            side_effect=lambda _size, state: state_calls.append(state) or _FakeSurface((20, 10)),
        ):
            rendered, hit_rect = self.factory._draw_angle_style_bitmaps("ok", Rect(1, 2, 20, 10))

        self.assertEqual(len(rendered), 3)
        self.assertEqual(hit_rect, Rect(1, 2, 20, 10))
        self.assertEqual(state_calls, ["idle", "hover", "armed"])

    def test_draw_angle_style_bitmaps_wraps_generic_error(self) -> None:
        with patch.object(self.factory, "render_text", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_angle_style_bitmaps("x", Rect(0, 0, 20, 10))

        self.assertIn("failed to draw angle style bitmaps", str(ctx.exception))

    def test_draw_check_style_bitmap_computes_hit_rect(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory,
            "render_text",
            return_value=pygame.Surface((10, 8)),
        ), patch.object(
            self.factory,
            "_draw_check_bitmap",
            return_value=pygame.Surface((8, 8)),
        ):
            _, hit_rect = self.factory._draw_check_style_bitmap(Rect(5, 6, 50, 20), 1, "x")

        self.assertEqual(hit_rect, Rect(5, 12, 18, 8))

    def test_draw_radio_style_bitmap_computes_hit_rect(self) -> None:
        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch.object(
            self.factory,
            "render_text",
            return_value=pygame.Surface((9, 10)),
        ), patch.object(
            self.factory,
            "draw_radio_bitmap",
            return_value=pygame.Surface((10, 10)),
        ):
            _, hit_rect = self.factory._draw_radio_style_bitmap(Rect(2, 4, 60, 24), "x", (1, 2, 3), (4, 5, 6))

        self.assertEqual(hit_rect, Rect(3, 11, 20, 10))

    def test_draw_window_title_bar_bitmaps_wraps_generic_failure(self) -> None:
        with patch.object(self.factory, "_draw_window_title_bar_bitmap", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.draw_window_title_bar_bitmaps(object(), "title", 100, 20)

        self.assertIn("failed to draw window title bar bitmaps", str(ctx.exception))

    def test_draw_window_title_bar_bitmap_set_font_guierror_does_not_restore_last_font(self) -> None:
        with patch.object(self.factory, "set_font", side_effect=GuiError("font-fail")), patch.object(
            self.factory,
            "set_last_font",
        ) as restore_last:
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_window_title_bar_bitmap(object(), "title", 80, 16)

        self.assertEqual(str(ctx.exception), "font-fail")
        restore_last.assert_not_called()

    def test_draw_window_title_bar_bitmap_generic_failure_restores_last_font(self) -> None:
        class FakeFrame:
            def __init__(self, *_args, **_kwargs) -> None:
                self.state = None
                self.surface = None

            def draw(self) -> None:
                pass

        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch(
            "gui.widgets.frame.Frame",
            FakeFrame,
        ), patch.object(
            self.factory,
            "set_font",
            return_value=None,
        ), patch.object(
            self.factory,
            "render_text",
            side_effect=RuntimeError("boom"),
        ), patch.object(
            self.factory,
            "set_last_font",
        ) as restore_last:
            with self.assertRaises(GuiError) as ctx:
                self.factory._draw_window_title_bar_bitmap(object(), "title", 80, 16)

        self.assertIn("failed to draw window title bar bitmap", str(ctx.exception))
        restore_last.assert_called_once()

    def test_draw_window_title_bar_bitmap_uses_default_highlight_colour(self) -> None:
        class FakeFrame:
            def __init__(self, *_args, **_kwargs) -> None:
                self.state = None
                self.surface = None

            def draw(self) -> None:
                pass

        with patch("gui.utility.bitmapfactory.Surface", side_effect=lambda size, *_a, **_k: _FakeSurface(size)), patch(
            "gui.widgets.frame.Frame",
            FakeFrame,
        ), patch.object(
            self.factory,
            "set_font",
            return_value=None,
        ), patch.object(
            self.factory,
            "render_text",
            return_value=pygame.Surface((7, 6)),
        ) as render_text, patch.object(
            self.factory,
            "set_last_font",
            return_value=None,
        ):
            self.factory._draw_window_title_bar_bitmap(object(), "title", 80, 16, colour=None)

        render_text.assert_called_once_with("title", colours["highlight"], True)


if __name__ == "__main__":
    unittest.main()
