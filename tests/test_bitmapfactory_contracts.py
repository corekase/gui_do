import unittest
from unittest.mock import patch

import pygame

from gui.utility.bitmapfactory import WidgetGraphicsFactory
from gui.utility.constants import GuiError


class FontStub:
    def __init__(self, linesize: int = 10) -> None:
        self.linesize = linesize

    def get_linesize(self) -> int:
        return self.linesize

    def render(self, text, _aa, _colour, _bg=None):
        width = max(1, len(text))
        return pygame.Surface((width, self.linesize))


class WidgetGraphicsFactoryContractsBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_get_cursor_rejects_unknown_name(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.get_cursor("missing")

    def test_get_styled_bitmaps_rejects_unknown_style(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.get_styled_bitmaps("bad-style", "text", pygame.Rect(0, 0, 10, 10))  # type: ignore[arg-type]

    def test_set_font_and_set_last_font_roundtrip(self) -> None:
        self.factory._fonts["a"] = FontStub(10)
        self.factory._fonts["b"] = FontStub(12)

        self.factory.set_font("a")
        self.assertEqual(self.factory.get_current_font_name(), "a")

        self.factory.set_font("b")
        self.assertEqual(self.factory.get_current_font_name(), "b")

        self.factory.set_last_font()
        self.assertEqual(self.factory.get_current_font_name(), "a")

    def test_set_last_font_rejects_missing_previous_font(self) -> None:
        self.factory._last_font_name = "missing"

        with self.assertRaises(GuiError):
            self.factory.set_last_font()

    def test_get_font_height_and_titlebar_height_validation(self) -> None:
        self.factory._fonts["titlebar"] = FontStub(11)

        self.assertEqual(self.factory.get_font_height("titlebar"), 11)
        self.assertEqual(self.factory.get_font_height("titlebar", shadow=True), 12)
        self.assertEqual(self.factory.get_titlebar_height(padding=6), 18)

        with self.assertRaises(GuiError):
            self.factory.get_font_height("missing")
        with self.assertRaises(GuiError):
            self.factory.get_titlebar_height(padding=-1)

    def test_render_text_requires_active_font(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.render_text("hello")

    def test_render_text_shadow_expands_surface(self) -> None:
        self.factory._font = FontStub(7)

        plain = self.factory.render_text("abc", shadow=False)
        shadow = self.factory.render_text("abc", shadow=True)

        self.assertEqual(plain.get_size(), (3, 7))
        self.assertEqual(shadow.get_size(), (4, 8))

    def test_centre_returns_expected_offset(self) -> None:
        self.assertEqual(self.factory.centre(100, 20), 40)

    def test_register_cursor_validates_inputs(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.register_cursor(name="cursor", filename="file.cur", hotspot=(1,))  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            self.factory.register_cursor(name="", filename="file.cur", hotspot=(0, 0))
        with self.assertRaises(GuiError):
            self.factory.register_cursor(name="cursor", filename="", hotspot=(0, 0))

    def test_register_cursor_populates_cache_via_image_alpha(self) -> None:
        surface = pygame.Surface((2, 2))

        with patch.object(self.factory, "image_alpha", return_value=surface):
            self.factory.register_cursor(name="cursor", filename="cursor.png", hotspot=(1, 2))

        cursor = self.factory.get_cursor("cursor")
        self.assertEqual(cursor.name, "cursor")
        self.assertIs(cursor.image, surface)
        self.assertEqual(cursor.hotspot, (1, 2))
        self.assertTrue(cursor.source_path.endswith("cursor.png"))

    def test_load_font_wraps_loader_error_with_guierror(self) -> None:
        with patch("pygame.font.Font", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                self.factory.load_font("main", "missing.ttf", 12)

        self.assertIn("failed to load font", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
